"""Training entry point: rollout collection, evaluation, and main loop."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from ai.rule_based import RuleBasedAI
from training.checkpoints import CheckpointManager
from training.config import TrainingConfig
from training.env import MahjongEnv
from training.metrics import MetricsLogger
from training.network import MahjongNetwork
from training.observation import ActionEncoder, ObservationEncoder
from training.ppo import RolloutBuffer, ppo_update
from training.self_play import LeagueManager


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _evaluate_vs_rule_based(
    network: MahjongNetwork,
    act_encoder: ActionEncoder,
    n_games: int,
    device: str,
) -> dict[str, float]:
    """Play *n_games* with RL agent at seat 0 vs rule-based at seats 1-3.

    Returns dict with keys: win_rate, avg_reward, avg_hand_value, draw_rate.
    """
    rule_ai = RuleBasedAI()
    obs_encoder = ObservationEncoder()

    wins = 0
    draws = 0
    total_reward = 0.0
    total_hand_value = 0.0
    win_count_for_avg = 0

    for _ in range(n_games):
        env = MahjongEnv()
        env.reset()

        while env.agents:
            agent = env.agent_selection
            if env.terminations[agent] or env.truncations[agent]:
                env.step(None)
                continue

            idx = int(agent.split("_")[1])
            mask = env.infos[agent]["action_mask"]

            if idx == 0:
                # RL agent
                obs = env.observe(agent)
                obs_t = torch.tensor(obs, device=device).unsqueeze(0)
                mask_t = torch.tensor(mask, device=device).unsqueeze(0)
                with torch.no_grad():
                    action_t, _, _, _ = network.get_action_and_value(
                        obs_t, mask_t
                    )
                action_int = action_t.item()
            else:
                # Rule-based opponent
                assert env._session is not None
                gs = env._session.state
                legal = env._session.get_legal_actions(idx)
                if not legal:
                    env.step(None)
                    continue
                chosen = rule_ai.choose_action(gs, idx, legal)
                action_int = act_encoder.action_to_int(chosen)

            env.step(action_int)

        # Collect results for player_0
        reward_p0 = env.rewards.get("player_0", 0.0)
        total_reward += reward_p0

        if reward_p0 > 0:
            wins += 1
            hand_value = reward_p0 * 81  # reward = tai / 81
            total_hand_value += hand_value
            win_count_for_avg += 1
        elif reward_p0 == -0.1:
            # Draw penalty
            draws += 1

    win_rate = wins / max(n_games, 1)
    avg_reward = total_reward / max(n_games, 1)
    avg_hand_value = total_hand_value / max(win_count_for_avg, 1)
    draw_rate = draws / max(n_games, 1)

    return {
        "win_rate": win_rate,
        "avg_reward": avg_reward,
        "avg_hand_value": avg_hand_value,
        "draw_rate": draw_rate,
    }


# ---------------------------------------------------------------------------
# Rollout collection
# ---------------------------------------------------------------------------


def _collect_rollout(
    env: MahjongEnv,
    network: MahjongNetwork,
    buffer: RolloutBuffer,
    act_encoder: ActionEncoder,
    rule_ai: RuleBasedAI,
    n_steps: int,
    device: str,
) -> tuple[int, int]:
    """Collect *n_steps* transitions for player_0 into *buffer*.

    Other players use rule-based AI. Returns (episodes_completed, total_episode_length).
    """
    episodes_completed = 0
    total_episode_length = 0
    steps_collected = 0

    # Track per-episode length (all players' decision steps)
    episode_step_count = 0

    # Ensure env is ready (agents attr only exists after first reset)
    if not getattr(env, "agents", None):
        env.reset()
        episode_step_count = 0

    while steps_collected < n_steps:
        if not env.agents:
            # Episode ended -- reset
            env.reset()
            episode_step_count = 0

        agent = env.agent_selection

        if env.terminations[agent] or env.truncations[agent]:
            env.step(None)
            continue

        idx = int(agent.split("_")[1])
        mask = env.infos[agent]["action_mask"]

        if idx == 0:
            # RL agent: record transition
            obs = env.observe(agent)
            obs_t = torch.tensor(obs, device=device).unsqueeze(0)
            mask_t = torch.tensor(mask, device=device).unsqueeze(0)

            with torch.no_grad():
                action_t, log_prob_t, _, value_t = network.get_action_and_value(
                    obs_t, mask_t
                )

            action_int = action_t.item()
            log_prob = log_prob_t.item()
            value = value_t.item()

            env.step(action_int)
            episode_step_count += 1

            # Determine reward and done for this transition
            # After stepping, check if the game ended
            game_done = not env.agents or all(
                env.terminations.get(a, False) or env.truncations.get(a, False)
                for a in env.possible_agents
            )

            reward = env.rewards.get("player_0", 0.0) if game_done else 0.0
            done = game_done

            buffer.add(
                obs=obs,
                action=action_int,
                reward=reward,
                done=done,
                log_prob=log_prob,
                value=value,
                action_mask=mask,
            )
            steps_collected += 1

            if game_done:
                episodes_completed += 1
                total_episode_length += episode_step_count
                episode_step_count = 0
        else:
            # Opponent: rule-based AI
            assert env._session is not None
            gs = env._session.state
            legal = env._session.get_legal_actions(idx)

            if not legal:
                env.step(None)
                continue

            chosen = rule_ai.choose_action(gs, idx, legal)
            action_int = act_encoder.action_to_int(chosen)

            env.step(action_int)
            episode_step_count += 1

            # If game ended on opponent's turn, update the last buffer entry
            game_done = not env.agents or all(
                env.terminations.get(a, False) or env.truncations.get(a, False)
                for a in env.possible_agents
            )

            if game_done and buffer.size > 0:
                last_idx = buffer.size - 1
                buffer.rewards[last_idx] = env.rewards.get("player_0", 0.0)
                buffer.dones[last_idx] = 1.0
                episodes_completed += 1
                total_episode_length += episode_step_count
                episode_step_count = 0

    return episodes_completed, total_episode_length


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------


def run_training(cfg: TrainingConfig) -> None:
    """Run the full RL training pipeline."""
    device = cfg.device
    obs_encoder = ObservationEncoder()
    act_encoder = ActionEncoder()

    # Create network and optimizer
    network = MahjongNetwork(
        obs_size=obs_encoder.obs_size,
        action_size=act_encoder.action_size,
        cfg=cfg,
    ).to(device)

    optimizer = torch.optim.Adam(network.parameters(), lr=cfg.learning_rate)

    # Infrastructure
    ckpt_mgr = CheckpointManager(cfg)
    league = LeagueManager(cfg)
    logger = MetricsLogger(cfg.log_dir)

    # Rollout buffer
    buffer = RolloutBuffer(
        capacity=cfg.n_steps,
        obs_size=obs_encoder.obs_size,
        action_size=act_encoder.action_size,
    )

    rule_ai = RuleBasedAI()
    env = MahjongEnv()

    total_episodes = 0
    current_elo = cfg.elo_initial
    phase = "warmup"

    while total_episodes < cfg.total_episodes:
        # -- Collect rollout --------------------------------------------------
        buffer.reset()
        episodes_completed, total_ep_length = _collect_rollout(
            env=env,
            network=network,
            buffer=buffer,
            act_encoder=act_encoder,
            rule_ai=rule_ai,
            n_steps=cfg.n_steps,
            device=device,
        )

        total_episodes += episodes_completed

        # Skip PPO update if buffer is empty (shouldn't happen, but be safe)
        if buffer.size == 0:
            continue

        # -- Bootstrap value for GAE ------------------------------------------
        if env.agents and not all(
            env.terminations.get(a, False) or env.truncations.get(a, False)
            for a in env.possible_agents
        ):
            # Environment still active; compute bootstrap value if it's
            # player_0's turn.
            agent = env.agent_selection
            if agent == "player_0":
                obs = env.observe(agent)
                mask = env.infos[agent]["action_mask"]
                obs_t = torch.tensor(obs, device=device).unsqueeze(0)
                mask_t = torch.tensor(mask, device=device).unsqueeze(0)
                with torch.no_grad():
                    _, value_t = network(obs_t, mask_t)
                last_value = value_t.item()
            else:
                last_value = 0.0
        else:
            last_value = 0.0

        buffer.compute_gae(last_value, cfg.gamma, cfg.gae_lambda)

        # -- PPO update -------------------------------------------------------
        ppo_metrics = ppo_update(network, optimizer, buffer, cfg, device=device)

        # -- Learning rate decay (linear) -------------------------------------
        progress = min(total_episodes / max(cfg.total_episodes, 1), 1.0)
        lr = cfg.learning_rate * (1.0 - progress)
        lr = max(lr, 1e-7)  # floor to avoid zero LR
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr

        # -- Log training metrics ---------------------------------------------
        logger.log_training(
            step=total_episodes,
            policy_loss=ppo_metrics["policy_loss"],
            value_loss=ppo_metrics["value_loss"],
            entropy=ppo_metrics["entropy"],
            clip_fraction=ppo_metrics["clip_fraction"],
            learning_rate=lr,
        )

        # -- Periodic evaluation ----------------------------------------------
        if total_episodes % cfg.eval_interval < episodes_completed or (
            total_episodes >= cfg.total_episodes
        ):
            eval_results = _evaluate_vs_rule_based(
                network=network,
                act_encoder=act_encoder,
                n_games=cfg.eval_games,
                device=device,
            )

            logger.log_evaluation(
                step=total_episodes,
                win_rate=eval_results["win_rate"],
                avg_reward=eval_results["avg_reward"],
                avg_hand_value=eval_results["avg_hand_value"],
                draw_rate=eval_results["draw_rate"],
            )

            print(
                f"[ep {total_episodes:>6d}] "
                f"phase={phase}  "
                f"win_rate={eval_results['win_rate']:.3f}  "
                f"avg_reward={eval_results['avg_reward']:.4f}  "
                f"draw_rate={eval_results['draw_rate']:.3f}  "
                f"elo={current_elo:.1f}  "
                f"lr={lr:.2e}"
            )

            # Check warmup -> selfplay transition
            if (
                phase == "warmup"
                and total_episodes >= cfg.warmup_episodes
                and eval_results["win_rate"] >= cfg.warmup_win_rate_threshold
            ):
                phase = "selfplay"
                print(
                    f">>> Transitioning to self-play at episode {total_episodes} "
                    f"(win_rate={eval_results['win_rate']:.3f})"
                )

        # -- Periodic checkpoint ----------------------------------------------
        if total_episodes % cfg.checkpoint_interval < episodes_completed or (
            total_episodes >= cfg.total_episodes
        ):
            ckpt_path = ckpt_mgr.save(
                network=network,
                optimizer=optimizer,
                episode=total_episodes,
                elo=current_elo,
            )
            league.add_checkpoint(total_episodes, network, current_elo)

            logger.log_league(
                step=total_episodes,
                current_elo=current_elo,
                best_elo=ckpt_mgr.best_elo,
                pool_size=league.pool_size,
            )

    # -- Final save -----------------------------------------------------------
    ckpt_mgr.save(
        network=network,
        optimizer=optimizer,
        episode=total_episodes,
        elo=current_elo,
    )
    logger.close()
    print(f"Training complete. Total episodes: {total_episodes}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Mahjong RL agent")
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to train on (default: cuda if available, else cpu)",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=200_000,
        help="Total training episodes (default: 200000)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="checkpoints",
        help="Directory for saving checkpoints (default: checkpoints)",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="runs",
        help="Directory for TensorBoard logs (default: runs)",
    )

    args = parser.parse_args()

    config = TrainingConfig(
        total_episodes=args.episodes,
        device=args.device,
        checkpoint_dir=Path(args.checkpoint_dir),
        log_dir=Path(args.log_dir),
    )

    run_training(config)
