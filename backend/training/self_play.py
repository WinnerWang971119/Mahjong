"""Self-play league manager with ELO tracking and opponent sampling."""
from __future__ import annotations

import math
import random
from pathlib import Path

import torch

from training.config import TrainingConfig
from training.network import MahjongNetwork


class EloTracker:
    """Tracks ELO ratings for agents."""

    def __init__(self, initial_elo: float = 1000.0, k: float = 32.0) -> None:
        self._elo: dict[str, float] = {}
        self._initial = initial_elo
        self._k = k

    def get_elo(self, agent_id: str) -> float:
        return self._elo.get(agent_id, self._initial)

    def set_elo(self, agent_id: str, elo: float) -> None:
        self._elo[agent_id] = elo

    def update(self, winner: str, losers: list[str]) -> None:
        """Update ELO after a game. Winner beat all losers."""
        winner_elo = self.get_elo(winner)
        total_winner_delta = 0.0
        for loser in losers:
            loser_elo = self.get_elo(loser)
            expected_w = 1.0 / (1.0 + math.pow(10, (loser_elo - winner_elo) / 400))
            expected_l = 1.0 - expected_w
            total_winner_delta += self._k * (1.0 - expected_w)
            self._elo[loser] = loser_elo + self._k * (0.0 - expected_l)
        self._elo[winner] = winner_elo + total_winner_delta


class LeagueManager:
    """Manages opponent pool for self-play training."""

    def __init__(self, cfg: TrainingConfig) -> None:
        self.cfg = cfg
        self.elo_tracker = EloTracker(initial_elo=cfg.elo_initial, k=cfg.elo_k)
        self._pool: list[dict] = []

    @property
    def pool_size(self) -> int:
        return len(self._pool)

    def add_checkpoint(self, episode: int, network: MahjongNetwork, elo: float) -> None:
        entry = {
            "episode": episode,
            "state_dict": {k: v.cpu().clone() for k, v in network.state_dict().items()},
            "elo": elo,
        }
        self._pool.append(entry)
        if len(self._pool) > self.cfg.pool_max_size:
            best = max(self._pool, key=lambda e: e["elo"])
            others = [e for e in self._pool if e is not best]
            keep_count = self.cfg.pool_max_size - 1
            self._pool = [best] + others[-keep_count:]

    def sample_opponents(self, phase: str) -> list[str | int]:
        if phase == "warmup" or not self._pool:
            return ["rule_based"] * 3
        opponents: list[str | int] = []
        for _ in range(3):
            r = random.random()
            if r < self.cfg.pool_sample_rule_based:
                opponents.append("rule_based")
            elif r < self.cfg.pool_sample_rule_based + self.cfg.pool_sample_old:
                if len(self._pool) > 1:
                    mid = len(self._pool) // 2
                    entry = random.choice(self._pool[:mid])
                else:
                    entry = self._pool[0]
                opponents.append(entry["episode"])
            else:
                mid = max(len(self._pool) // 2, 1)
                entry = random.choice(self._pool[-mid:])
                opponents.append(entry["episode"])
        return opponents

    def load_opponent_network(self, opponent_id: str | int, network: MahjongNetwork) -> None:
        if opponent_id == "rule_based":
            return
        for entry in self._pool:
            if entry["episode"] == opponent_id:
                network.load_state_dict(entry["state_dict"])
                return
        raise ValueError(f"Checkpoint for episode {opponent_id} not found in pool")
