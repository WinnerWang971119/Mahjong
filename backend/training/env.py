"""PettingZoo AEC environment wrapper for Taiwan 16-tile Mahjong."""
from __future__ import annotations

import functools
from typing import Any

import gymnasium
import numpy as np
from pettingzoo import AECEnv

from engine.game_session import Action, GameSession
from engine.scorer import score_hand
from engine.state import GameState, Meld
from engine.win_validator import decompose_hand, is_winning_hand
from training.observation import ActionEncoder, ObservationEncoder
from training.rewards import compute_rewards


def env(**kwargs: Any) -> MahjongEnv:
    """Create a MahjongEnv (PettingZoo convention)."""
    return MahjongEnv(**kwargs)


class MahjongEnv(AECEnv):
    """PettingZoo AEC environment for Taiwan 16-tile Mahjong.

    Wraps the game engine's GameSession as a standard AEC environment with
    four agents ("player_0" through "player_3"). Each agent observes via
    ObservationEncoder and acts via integer indices decoded by ActionEncoder.

    Legal actions are exposed through ``info["action_mask"]``.
    """

    metadata = {"render_modes": [], "name": "mahjong_v0"}

    def __init__(self) -> None:
        super().__init__()
        self.possible_agents: list[str] = [f"player_{i}" for i in range(4)]
        self._obs_encoder = ObservationEncoder()
        self._act_encoder = ActionEncoder()
        self._session: GameSession | None = None
        self._terminal_rewards: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Spaces
    # ------------------------------------------------------------------

    @functools.lru_cache(maxsize=4)
    def observation_space(self, agent: str) -> gymnasium.spaces.Box:
        """Return the observation space for *agent*."""
        return gymnasium.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(self._obs_encoder.obs_size,),
            dtype=np.float32,
        )

    @functools.lru_cache(maxsize=4)
    def action_space(self, agent: str) -> gymnasium.spaces.Discrete:
        """Return the action space for *agent*."""
        return gymnasium.spaces.Discrete(self._act_encoder.action_size)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(
        self, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> None:
        """Start a new hand."""
        self.agents = list(self.possible_agents)
        self._session = GameSession()
        self._session.start_hand()

        self.rewards: dict[str, float] = {a: 0.0 for a in self.agents}
        self._cumulative_rewards: dict[str, float] = {a: 0.0 for a in self.agents}
        self.terminations: dict[str, bool] = {a: False for a in self.agents}
        self.truncations: dict[str, bool] = {a: False for a in self.agents}
        self.infos: dict[str, dict[str, Any]] = {a: {} for a in self.agents}
        self._terminal_rewards = {}

        self.agent_selection = self.possible_agents[0]
        # Auto-advance through any non-decision states (draw, auto-pass)
        self._advance_non_decision_states()
        self._update_infos()

    # ------------------------------------------------------------------
    # Observe
    # ------------------------------------------------------------------

    def observe(self, agent: str) -> np.ndarray:
        """Return the observation vector for *agent*."""
        assert self._session is not None
        idx = self._agent_to_idx(agent)
        return self._obs_encoder.encode(self._session.state, idx)

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self, action: int | None) -> None:
        """Execute an action for the current agent."""
        assert self._session is not None
        agent = self.agent_selection

        # Handle terminated/truncated agent (PettingZoo dead-step protocol)
        if self.terminations[agent] or self.truncations[agent]:
            self._was_dead_step(action)
            # After all dead agents are removed, re-populate rewards from the
            # terminal snapshot so they remain queryable after the game ends.
            if not self.agents and self._terminal_rewards:
                self.rewards = dict(self._terminal_rewards)
            return

        # Clear per-step rewards
        self._clear_rewards()

        idx = self._agent_to_idx(agent)

        # Convert integer action to engine Action
        engine_action = self._act_encoder.int_to_action(action, player_idx=idx)

        # For claim-phase actions that need the pending discard tile
        gs = self._session.state
        if engine_action.type in ("pong", "open_kong") and gs.last_discard is not None:
            engine_action.tile = gs.last_discard
        if engine_action.type == "chi" and gs.last_discard is not None:
            # Chi combo already has the tiles from the encoder, but we set .tile
            # to the discard tile for consistency with engine expectations.
            engine_action.tile = gs.last_discard

        # Execute in the game engine
        self._session.step(engine_action)

        # Check for game end
        gs = self._session.state
        if gs.phase in ("win", "draw"):
            self._handle_game_end()
            return

        # Auto-advance through non-decision states and pick next agent
        self._advance_non_decision_states()
        self._update_infos()

        # Accumulate rewards into _cumulative_rewards (PettingZoo protocol)
        self._accumulate_rewards()

    # ------------------------------------------------------------------
    # Internals: agent indexing
    # ------------------------------------------------------------------

    @staticmethod
    def _agent_to_idx(agent: str) -> int:
        """Convert agent name to player index."""
        return int(agent.split("_")[1])

    @staticmethod
    def _idx_to_agent(idx: int) -> str:
        """Convert player index to agent name."""
        return f"player_{idx}"

    # ------------------------------------------------------------------
    # Internals: game advancement
    # ------------------------------------------------------------------

    def _advance_non_decision_states(self) -> None:
        """Auto-execute non-decision actions (draw, forced passes).

        This keeps stepping the engine forward until the current state
        requires a real decision from some player. Specifically:

        1. During active_turn, if the only legal action is "draw", execute it
           automatically (no strategic choice involved).
        2. During claim phase, if a player's only option is "pass", auto-pass
           for them so the RL agent only sees real decisions.
        3. Repeat until a player has a meaningful choice or the game ends.
        """
        assert self._session is not None

        max_auto_steps = 200  # Safety limit to prevent infinite loops
        for _ in range(max_auto_steps):
            gs = self._session.state
            if gs.phase in ("win", "draw"):
                self._handle_game_end()
                return

            if self._session._sub_phase == "active_turn":
                # Active turn: check if current player needs to draw
                current = gs.current_player
                actions = self._session.get_legal_actions(current)
                if len(actions) == 1 and actions[0].type == "draw":
                    # Auto-draw: no strategic choice
                    self._session.step(actions[0])
                    continue
                elif len(actions) > 0:
                    # Player has real choices (discard, kong, win, etc.)
                    self.agent_selection = self._idx_to_agent(current)
                    return
                else:
                    # No legal actions (shouldn't happen during active turn)
                    return

            elif self._session._sub_phase == "claim":
                # Claim phase: find a non-discarder with real claim actions
                discarder = self._session._pending_discarder
                assert discarder is not None

                found_real_claimant = False
                # Check all non-discarders in turn order for real claim actions
                for offset in range(1, 4):
                    pidx = (discarder + offset) % 4
                    actions = self._session.get_legal_actions(pidx)
                    if not actions:
                        continue  # Already passed or is the discarder

                    # Check if the player has non-pass actions
                    non_pass = [a for a in actions if a.type != "pass"]
                    if non_pass:
                        # This player has real claim options (win, pong, kong, chi)
                        self.agent_selection = self._idx_to_agent(pidx)
                        found_real_claimant = True
                        break

                if found_real_claimant:
                    # A player has real claim options; they're now agent_selection
                    return

                # All remaining players can only pass: auto-pass them all
                self._auto_pass_remaining()
                # After all pass, engine advances to next player's draw
                continue
            else:
                return

        # If we exhausted auto-steps, just set agent_selection to current player
        gs = self._session.state
        if gs.phase == "play":
            self.agent_selection = self._idx_to_agent(gs.current_player)

    def _auto_pass_remaining(self) -> None:
        """Auto-pass all non-discarders who haven't passed yet."""
        assert self._session is not None
        discarder = self._session._pending_discarder
        if discarder is None:
            return

        # Pass for each non-discarder who still has actions
        for offset in range(1, 4):
            pidx = (discarder + offset) % 4
            actions = self._session.get_legal_actions(pidx)
            if actions:
                # Find the pass action
                pass_action = next(
                    (a for a in actions if a.type == "pass"), None
                )
                if pass_action is not None:
                    self._session.step(pass_action)
                    # Check if engine advanced out of claim phase
                    if self._session._sub_phase != "claim":
                        return

    def _update_infos(self) -> None:
        """Populate action masks in self.infos for all agents."""
        assert self._session is not None
        gs = self._session.state
        zero_mask = np.zeros(self._act_encoder.action_size, dtype=np.float32)

        for agent in self.agents:
            if gs.phase in ("win", "draw") or self.terminations.get(agent, False):
                self.infos[agent] = {"action_mask": zero_mask.copy()}
                continue

            idx = self._agent_to_idx(agent)
            legal = self._session.get_legal_actions(idx)

            # Filter out "pass" for the currently selected agent
            # (pass is auto-handled if no real claim; if real claims exist,
            # the agent should also be able to pass explicitly)
            if legal:
                self.infos[agent] = {
                    "action_mask": self._act_encoder.legal_actions_to_mask(legal)
                }
            else:
                self.infos[agent] = {"action_mask": zero_mask.copy()}

    # ------------------------------------------------------------------
    # Internals: game end
    # ------------------------------------------------------------------

    def _handle_game_end(self) -> None:
        """Compute rewards and terminate all agents when the game ends."""
        assert self._session is not None
        gs = self._session.state

        winner_idx: int | None = None
        total_tai: int = 0

        if gs.phase == "win":
            winner_idx, total_tai = self._determine_winner()

        rewards = compute_rewards(winner_idx=winner_idx, total_tai=total_tai)

        for i, agent in enumerate(self.possible_agents):
            if agent in self.agents:
                self.rewards[agent] = rewards[i]
                self._cumulative_rewards[agent] = (
                    self._cumulative_rewards.get(agent, 0.0) + rewards[i]
                )
                self.terminations[agent] = True
            # Store terminal rewards for all agents (survives dead-step cleanup)
            self._terminal_rewards[agent] = rewards[i]

        # Expose terminal rewards on self.rewards so they remain accessible
        # even after the PettingZoo dead-step protocol removes agents
        self.rewards = dict(self._terminal_rewards)

        # Clear agents list to signal episode end (allows train.py loops to exit)
        self.agents = []

        # Update infos with zero masks
        self._update_infos()

    def _determine_winner(self) -> tuple[int | None, int]:
        """Find the winner and compute their tai score.

        Returns (winner_idx, total_tai). If winner cannot be determined,
        returns (None, 0) as a fallback.
        """
        assert self._session is not None
        gs = self._session.state

        # The engine sets current_player to the winner after a win action
        winner_idx = gs.current_player
        p = gs.players[winner_idx]

        # Determine win type from the sub-phase at win time.
        # gs.last_action is always "win" here (the engine overwrites it),
        # so we use _sub_phase which is NOT modified by _do_win().
        is_self_draw = self._session._sub_phase == "active_turn"
        win_type = "self_draw" if is_self_draw else "discard"

        # Determine win tile based on win type
        if is_self_draw:
            # Self-draw: winning tile is the last tile in hand
            if not p.hand:
                return None, 0
            win_tile = p.hand[-1]
            hand_without = list(p.hand[:-1])
        elif gs.last_discard is not None:
            # Discard win: winning tile is the discard
            win_tile = gs.last_discard
            hand_without = list(p.hand)
        else:
            # Fallback: try to find a valid decomposition
            for tile in set(p.hand):
                test_hand = list(p.hand)
                test_hand.remove(tile)
                result = is_winning_hand(test_hand, p.melds, p.flowers, tile)
                if result is not None:
                    total_tai = self._compute_tai(
                        gs, winner_idx, tile, test_hand, p.melds, p.flowers, win_type
                    )
                    return winner_idx, total_tai
            return None, 0

        # Verify the hand is actually winning
        result = is_winning_hand(hand_without, p.melds, p.flowers, win_tile)
        if result is not None:
            total_tai = self._compute_tai(
                gs, winner_idx, win_tile, hand_without, p.melds, p.flowers, win_type
            )
            return winner_idx, total_tai

        # Fallback: scan tiles if the above didn't work
        for tile in set(p.hand):
            test_hand = list(p.hand)
            test_hand.remove(tile)
            result = is_winning_hand(test_hand, p.melds, p.flowers, tile)
            if result is not None:
                total_tai = self._compute_tai(
                    gs, winner_idx, tile, test_hand, p.melds, p.flowers, win_type
                )
                return winner_idx, total_tai

        return None, 0

    @staticmethod
    def _compute_tai(
        gs: GameState,
        winner_idx: int,
        win_tile: str,
        hand: list[str],
        melds: list[Meld],
        flowers: list[str],
        win_type: str,
    ) -> int:
        """Score the winning hand and return total tai."""
        full_hand = hand + [win_tile]
        decomp = decompose_hand(full_hand, melds)

        try:
            result = score_hand(
                gs,
                winner_idx=winner_idx,
                win_tile=win_tile,
                win_type=win_type,
                hand=hand,
                melds=melds,
                flowers=flowers,
                decomp=decomp,
            )
            return result.total
        except Exception:
            # Fallback: minimum 1 tai for any valid win
            return 1

    # ------------------------------------------------------------------
    # Rendering (stub)
    # ------------------------------------------------------------------

    def render(self) -> None:
        """Render is not implemented (no render_modes)."""
        pass
