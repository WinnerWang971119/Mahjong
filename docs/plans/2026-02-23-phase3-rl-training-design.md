# Phase 3: RL Training Infrastructure — Design Document

**Date:** 2026-02-23
**Status:** Approved
**Author:** Diego Wang + Claude

## Overview

Build a self-play reinforcement learning pipeline where a PPO agent learns to play Taiwan 16-tile Mahjong and beats the rule-based AI in >80% of games over 1000 games.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Hardware | RTX 3080 Ti (12GB), remote machine via SSH | Sufficient for ~1M param model |
| RL Framework | PettingZoo AEC | Standard for turn-based multi-agent, per master spec |
| PPO Implementation | CleanRL-style from scratch (PyTorch) | Full control over action masking and multi-agent quirks |
| Observation Space | Flat binary encoding (~290 features) | Simple, proven in mahjong RL literature |
| Reward Function | Sparse + score-based | Clean learning signal, no reward hacking risk |
| Neural Network | Small MLP (~650K params) | Fast training, right-sized for discrete action space |
| Architecture | Monolithic `backend/training/` package | Simple, debuggable, right-sized for single GPU |
| Scope | All milestones (3.1–3.8) in one push | Components are tightly coupled |

## File Structure

```
backend/training/
├── env.py            # PettingZoo AEC wrapper over GameSession
├── network.py        # MLP with policy + value heads
├── ppo.py            # PPO algorithm (CleanRL-style)
├── self_play.py      # League manager, opponent pool
├── observation.py    # State → flat vector encoding
├── rewards.py        # Score-based reward computation
├── checkpoints.py    # Save/load/versioning
├── metrics.py        # TensorBoard logging
├── config.py         # Hyperparameters as dataclass
└── train.py          # Entry point: warm-up → self-play loop
```

## 1. PettingZoo AEC Environment (`env.py`)

Wraps `GameSession` as a PettingZoo AEC environment.

**Agents:** `["player_0", "player_1", "player_2", "player_3"]`

### Observation Space

`Box(low=0, high=1, shape=(~290,), dtype=float32)`

| Feature Group | Dims | Encoding |
|---------------|------|----------|
| Own hand tile counts | 34 | Count/4 (normalized 0-1) |
| Own flowers | 8 | Binary |
| Each opponent's discards (×3) | 102 | Count/4 normalized |
| Each opponent's visible melds (×3) | 102 | Count/4 normalized |
| Own melds | 34 | Count/4 normalized |
| Seat wind (one-hot) | 4 | One-hot |
| Prevailing wind (one-hot) | 4 | One-hot |
| Tiles remaining in wall | 1 | Normalized by initial wall size |
| Turn number | 1 | Normalized |

### Action Space

`Discrete(~104)` with action masking.

| Action Type | Count |
|-------------|-------|
| Discard tile_i | 34 |
| Chi combo_j | ~63 |
| Pong | 1 |
| Kong (4 types) | 4 |
| Win (Hu) | 1 |
| Pass | 1 |
| **Total** | ~104 |

**Action masking:** `env.action_mask(agent)` returns binary vector. Illegal actions masked to -inf before softmax.

### Step Logic

1. Receive action from current agent
2. Translate to `GameSession.step()` call
3. Handle flower replacement automatically (not a player decision)
4. Advance to next agent's turn
5. Return observation, reward, termination, truncation, info

## 2. Neural Network Architecture (`network.py`)

Shared feature extractor with separate policy and value heads.

```
Input (290) → FC(512) → ReLU → FC(512) → ReLU → FC(256) → ReLU
                                                       ↓
                                            ┌──────────┴──────────┐
                                            ↓                     ↓
                                    Policy Head              Value Head
                                    FC(256) → ReLU           FC(256) → ReLU
                                    FC(104) → logits         FC(1) → scalar
```

- **Shared backbone:** 3 layers (512→512→256) with ReLU
- **Policy head:** 2 layers → logits, masked before softmax
- **Value head:** 2 layers → scalar expected return
- **Parameters:** ~650K
- **Orthogonal initialization** for stable early training

## 3. PPO Algorithm (`ppo.py`)

CleanRL-style single-file PPO for multi-agent turn-based play. All 4 agents share one network (parameter sharing).

### Hyperparameters

| Parameter | Default |
|-----------|---------|
| learning_rate | 3e-4 (Adam, linear decay) |
| gamma | 0.99 |
| gae_lambda | 0.95 |
| clip_epsilon | 0.2 |
| entropy_coef | 0.01 |
| value_coef | 0.5 |
| max_grad_norm | 0.5 |
| n_steps | 2048 |
| n_epochs | 4 |
| batch_size | 256 |
| n_envs | 8 |

### Update Step

1. Collect `n_steps` transitions across `n_envs` parallel games
2. Compute GAE advantages
3. For `n_epochs`: shuffle, iterate minibatches, compute PPO loss (clipped surrogate + value + entropy)
4. Log losses to TensorBoard

## 4. Self-Play League (`self_play.py`)

### Phase A — Warm-up (Rule-based Opponents)

- 1 learning agent + 3 rule-based AIs
- Train ~10K episodes or until win rate vs rule-based >50%
- Purpose: learn basic hand completion

### Phase B — Self-play with League

- **Opponent pool:** Historical checkpoints + rule-based AI
- **Per game:** 1 learning agent + 3 sampled from pool
- **Sampling:** 70% recent checkpoints, 20% older, 10% rule-based
- **New checkpoint added:** Every 500 episodes
- **Pool cap:** Last 20 checkpoints + best ELO + rule-based (always)
- **Transition A→B:** Win rate vs rule-based >50% over 1000 games

### ELO Rating

- Initial ELO: 1000 for all agents
- Standard ELO formula, K=32
- Best ELO checkpoint always preserved

## 5. Training Metrics (`metrics.py`)

### TensorBoard Metrics

| Category | Metrics |
|----------|---------|
| Training | policy_loss, value_loss, entropy, clip_fraction, approx_kl, learning_rate |
| Performance | win_rate_vs_rule_based (every 100 eps), avg_episode_reward, avg_hand_value_on_win |
| League | current_elo, best_elo, pool_size |
| Environment | avg_episode_length, draw_rate, avg_tiles_remaining |

Evaluation: every 100 training episodes, freeze agent, play 100 games vs 3 rule-based AIs.

## 6. Checkpoint System (`checkpoints.py`)

```
backend/checkpoints/
├── latest.pt
├── best_elo.pt
├── ep_000500.pt
├── ep_001000.pt
├── ...
└── metadata.json
```

Each checkpoint: model state_dict, optimizer state_dict, episode number, ELO, config, RNG states.

**Retention:** Last 20 periodic + best ELO + latest. Older auto-deleted.

## 7. Configuration (`config.py`)

Single `TrainingConfig` dataclass with all hyperparameters and paths. Loadable from CLI args or YAML.

## 8. Docker & Remote Training

```dockerfile
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime
WORKDIR /app
COPY backend/ ./backend/
RUN pip install -e "./backend[train]"
ENTRYPOINT ["python", "-m", "backend.training.train"]
```

**Remote workflow:**
1. SSH into GPU machine
2. `docker build -t mahjong-train .`
3. `docker run --gpus all -v ./checkpoints:/app/checkpoints -v ./runs:/app/runs mahjong-train`
4. Monitor: `tensorboard --logdir runs/ --bind_all`

## Success Criteria

| Metric | Target |
|--------|--------|
| Win rate vs. rule-based | ≥80% over 1000 games |
| Policy entropy | Sufficient exploration |
| Average episode reward | Increasing trend |
| ELO rating curve | Steady improvement |
| Mean hand value on win | Increasing |
| Value + Policy loss | Decreasing, stable convergence |
