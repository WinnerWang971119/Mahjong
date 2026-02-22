"""Checkpoint save/load with retention policy and ELO tracking."""
from __future__ import annotations

import json
from pathlib import Path

import torch

from training.config import TrainingConfig
from training.network import MahjongNetwork


class CheckpointManager:
    """Manages saving, loading, and pruning of training checkpoints.

    Checkpoints are stored as:
      - ``ep_NNNNNN.pt`` -- periodic snapshots (pruned by retention policy)
      - ``latest.pt``     -- always points to the most recent save
      - ``best_elo.pt``   -- snapshot with the highest observed ELO
      - ``metadata.json`` -- cumulative ELO history and best-ELO value
    """

    def __init__(self, cfg: TrainingConfig) -> None:
        self.cfg = cfg
        self.dir = Path(cfg.checkpoint_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.best_elo: float = -float("inf")
        self._elo_history: list[dict] = []

        # Restore state from an earlier run if metadata exists
        meta_path = self.dir / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self._elo_history = meta.get("elo_history", [])
            self.best_elo = meta.get("best_elo", -float("inf"))

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(
        self,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer,
        episode: int,
        elo: float,
    ) -> Path:
        """Persist a checkpoint and update bookkeeping.

        Args:
            network:   The model whose weights to save.
            optimizer: The optimizer whose state to save.
            episode:   Current training episode number.
            elo:       Current ELO rating of the agent.

        Returns:
            Path to the periodic checkpoint file that was written.
        """
        checkpoint = {
            "model_state_dict": network.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "episode": episode,
            "elo": elo,
        }

        # Periodic checkpoint
        path = self.dir / f"ep_{episode:06d}.pt"
        torch.save(checkpoint, path)

        # Latest (always overwritten)
        torch.save(checkpoint, self.dir / "latest.pt")

        # Best ELO (overwritten only when a new high is reached)
        if elo > self.best_elo:
            self.best_elo = elo
            torch.save(checkpoint, self.dir / "best_elo.pt")

        # Bookkeeping
        self._elo_history.append({"episode": episode, "elo": elo})
        self._save_metadata()
        self._prune()
        return path

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_latest(
        self,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> dict:
        """Load the most recently saved checkpoint into *network* (and optionally *optimizer*)."""
        return self._load(self.dir / "latest.pt", network, optimizer)

    def load_best(
        self,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> dict:
        """Load the best-ELO checkpoint into *network* (and optionally *optimizer*)."""
        return self._load(self.dir / "best_elo.pt", network, optimizer)

    def _load(
        self,
        path: Path,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None,
    ) -> dict:
        """Internal helper that loads a specific checkpoint file.

        ``weights_only=False`` is used because the checkpoint contains
        optimizer state dicts with non-primitive tensor types that
        ``weights_only=True`` would reject on recent PyTorch versions.
        """
        checkpoint = torch.load(path, weights_only=False)
        network.load_state_dict(checkpoint["model_state_dict"])
        if optimizer is not None and "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        return {
            "episode": checkpoint.get("episode", 0),
            "elo": checkpoint.get("elo", self.cfg.elo_initial),
        }

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_checkpoints(self) -> list[Path]:
        """Return all periodic ``ep_*.pt`` files sorted by name (ascending)."""
        return sorted(self.dir.glob("ep_*.pt"))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prune(self) -> None:
        """Remove the oldest periodic checkpoints exceeding ``pool_max_size``."""
        periodic = self.list_checkpoints()
        if len(periodic) > self.cfg.pool_max_size:
            to_remove = periodic[: len(periodic) - self.cfg.pool_max_size]
            for p in to_remove:
                p.unlink()

    def _save_metadata(self) -> None:
        """Persist cumulative metadata to a human-readable JSON file."""
        meta = {
            "best_elo": self.best_elo,
            "elo_history": self._elo_history,
        }
        (self.dir / "metadata.json").write_text(json.dumps(meta, indent=2))
