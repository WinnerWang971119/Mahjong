"""Shared test fixtures and collection hooks."""
from __future__ import annotations

collect_ignore_glob = []

# Skip training tests when ML dependencies (torch/numpy) are not installed.
# CI installs --extra dev --extra server but NOT --extra train, so these
# imports would fail at collection time without this guard.
# Note: collect_ignore_glob uses fnmatch against absolute paths, so patterns
# must use wildcards (e.g. "*test_checkpoints.py", not "tests/test_checkpoints.py").
try:
    import torch  # noqa: F401
    import numpy  # noqa: F401
    _training_deps_available = True
except ImportError:
    _training_deps_available = False
    collect_ignore_glob.extend([
        "*test_checkpoints.py",
        "*test_env.py",
        "*test_metrics.py",
        "*test_network.py",
        "*test_observation.py",
        "*test_ppo.py",
        "*test_self_play.py",
        "*test_train.py",
    ])
