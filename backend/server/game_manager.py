"""Game manager: orchestrates human + AI turns for one game session."""
from __future__ import annotations

from engine.game_session import GameSession, Action
from engine.state import GameState
from ai.rule_based import RuleBasedAI
from ai.shanten import shanten_number
from server.serializer import serialize_game_state

# Claim priority: higher value = higher priority.
_CLAIM_PRIORITY: dict[str, int] = {
    "win": 4,
    "open_kong": 3,
    "pong": 2,
    "chi": 1,
}


class GameManager:
    """Manages a single game: wraps GameSession, drives AI, tracks events.

    The human occupies one seat; the other three seats are played by
    :class:`RuleBasedAI`.  After every human action the manager automatically
    advances AI turns until the human must act again (or the game ends).
    """

    def __init__(self, human_seat: int = 0, mode: str = "easy") -> None:
        self.session = GameSession()
        self.human_seat = human_seat
        self.ai = RuleBasedAI()
        self.mode = mode
        self.events: list[dict] = []
        self.replay_frames: list[dict] = []
        self._turn_counter: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start a new hand and run AI turns until the human needs to act."""
        self.session.start_hand()
        self._run_ai_turns()

    def handle_human_action(
        self,
        action_type: str,
        tile: str | None = None,
        combo: list[str] | None = None,
    ) -> None:
        """Process a human player's action, then continue AI turns."""
        action = Action(
            type=action_type,
            tile=tile,
            combo=combo,
            player_idx=self.human_seat,
        )
        self.session.step(action)
        self._append_event(action_type, self.human_seat, tile)
        self._run_ai_turns()

    def get_client_state(self, reveal_all: bool = False) -> dict:
        """Return the serialized game state visible to the human player.

        In inspect mode all hands are always revealed.
        """
        effective_reveal = reveal_all or self.mode == "inspect"
        return serialize_game_state(
            self.session.state, self.human_seat, reveal_all=effective_reveal
        )

    def get_action_request(self) -> dict | None:
        """Return pending action options for the human, or ``None``.

        Returns ``None`` when the game is not in the "play" phase or the
        human has no legal actions right now.
        """
        if self.session.state.phase != "play":
            return None
        legal = self.session.get_legal_actions(self.human_seat)
        if not legal:
            return None
        return {
            "player": self.human_seat,
            "options": [
                {"type": a.type, "tile": a.tile, "combo": a.combo}
                for a in legal
            ],
            "timeout": 10,
        }

    def get_events(self) -> list[dict]:
        """Return and clear accumulated game events."""
        events = list(self.events)
        self.events.clear()
        return events

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def get_replay_frames(self) -> list[dict]:
        """Return all accumulated replay frames."""
        return list(self.replay_frames)

    def _append_event(
        self, event: str, player: int, tile: str | None = None
    ) -> None:
        event_dict = {"event": event, "player": player, "tile": tile}
        self.events.append(event_dict)
        # Also record for replay
        self._turn_counter += 1
        self.replay_frames.append({
            "turn": self._turn_counter,
            "event": event,
            "player": player,
            "tile": tile,
        })

    def _run_ai_turns(self) -> None:
        """Run AI turns until the human must act or the game ends.

        Safety cap of 500 iterations prevents infinite loops in edge cases.
        In inspect mode, all 4 seats are AI-controlled.
        """
        for _ in range(500):
            phase = self.session.state.phase
            if phase in ("win", "draw"):
                return

            if phase != "play":
                return

            if self.session._sub_phase == "claim":
                if self.mode == "inspect":
                    # In inspect mode there is no human, resolve claims fully
                    self._handle_claim_phase_inspect()
                else:
                    human_must_decide = self._handle_claim_phase()
                    if human_must_decide:
                        return  # Human has a meaningful claim option
                continue  # Claim resolved; re-evaluate loop

            # --- active_turn ---
            current = self.session.state.current_player
            if current == self.human_seat and self.mode != "inspect":
                return  # Human's turn

            legal = self.session.get_legal_actions(current)
            if not legal:
                return  # Shouldn't happen, but be safe

            # In inspect mode, emit ai_thinking with shanten data
            if self.mode == "inspect":
                self._emit_ai_thinking(current)

            ai_action = self.ai.choose_action(
                self.session.state, current, legal
            )
            self.session.step(ai_action)
            self._append_event(ai_action.type, current, ai_action.tile)

    def _handle_claim_phase(self) -> bool:
        """Drive AI decisions during the claim sub-phase.

        Returns ``True`` when the human player has a non-pass claim option
        that should be presented to the UI (i.e. we must wait for input).
        Returns ``False`` when the claim phase was fully resolved by AI
        (or the human was auto-passed because they had no real options).
        """
        # 1. Gather the best claim action from each AI seat.
        best_ai_action: Action | None = None
        best_ai_priority = -1

        for idx in range(4):
            if idx == self.human_seat:
                continue
            actions = self.session.get_legal_actions(idx)
            for a in actions:
                p = _CLAIM_PRIORITY.get(a.type, 0)
                if p > best_ai_priority:
                    best_ai_priority = p
                    best_ai_action = a

        # 2. Gather the best claim priority for the human seat.
        human_actions = self.session.get_legal_actions(self.human_seat)
        human_non_pass = [a for a in human_actions if a.type != "pass"]
        human_best_priority = max(
            (_CLAIM_PRIORITY.get(a.type, 0) for a in human_non_pass),
            default=-1,
        )

        # 3. If the human has equal-or-higher priority than best AI claim,
        #    yield control so the UI can ask the human.
        if human_non_pass and human_best_priority >= best_ai_priority:
            return True  # Wait for human input

        # 4. If an AI wants to claim and outranks the human, let the AI's
        #    choose_action pick the final action (it respects win > kong >
        #    pong > chi internally).
        if best_ai_action is not None and best_ai_priority > 0:
            claimer_idx = best_ai_action.player_idx
            assert claimer_idx is not None
            legal = self.session.get_legal_actions(claimer_idx)
            ai_action = self.ai.choose_action(
                self.session.state, claimer_idx, legal
            )
            if ai_action.type != "pass":
                # Before executing the claim, all other non-discarder
                # non-claimer players must pass first (the game session
                # tracks _passed_players).  Pass everyone except the
                # claimer and the discarder.
                self._pass_all_except(claimer_idx)
                self.session.step(ai_action)
                self._append_event(
                    ai_action.type, claimer_idx, ai_action.tile
                )
                return False

        # 5. Nobody wants to claim — pass all remaining players (including
        #    the human if they have no real options).
        self._pass_all()
        return False

    def _pass_all_except(self, exclude_idx: int) -> None:
        """Have every non-discarder (except *exclude_idx*) pass."""
        discarder = self.session._pending_discarder
        for idx in range(4):
            if idx == discarder or idx == exclude_idx:
                continue
            if idx in self.session._passed_players:
                continue
            actions = self.session.get_legal_actions(idx)
            for a in actions:
                if a.type == "pass":
                    self.session.step(a)
                    break

    def _pass_all(self) -> None:
        """Have every non-discarder who hasn't passed yet pass."""
        discarder = self.session._pending_discarder
        for idx in range(4):
            if idx == discarder:
                continue
            if idx in self.session._passed_players:
                continue
            actions = self.session.get_legal_actions(idx)
            for a in actions:
                if a.type == "pass":
                    self.session.step(a)
                    break

    def _handle_claim_phase_inspect(self) -> None:
        """Resolve claim phase entirely with AI (inspect mode, no human)."""
        best_action: Action | None = None
        best_priority = -1

        for idx in range(4):
            actions = self.session.get_legal_actions(idx)
            for a in actions:
                p = _CLAIM_PRIORITY.get(a.type, 0)
                if p > best_priority:
                    best_priority = p
                    best_action = a

        if best_action is not None and best_priority > 0:
            claimer_idx = best_action.player_idx
            assert claimer_idx is not None
            legal = self.session.get_legal_actions(claimer_idx)
            ai_action = self.ai.choose_action(
                self.session.state, claimer_idx, legal
            )
            if ai_action.type != "pass":
                self._pass_all_except(claimer_idx)
                self.session.step(ai_action)
                self._append_event(
                    ai_action.type, claimer_idx, ai_action.tile
                )
                return

        self._pass_all()

    def _emit_ai_thinking(self, player_idx: int) -> None:
        """Emit an ai_thinking event with shanten data for inspect mode."""
        ps = self.session.state.players[player_idx]
        try:
            s = shanten_number(ps.hand, ps.melds)
        except Exception:
            s = None
        self.events.append({
            "event": "ai_thinking",
            "player": player_idx,
            "tile": None,
            "shanten": s,
        })
