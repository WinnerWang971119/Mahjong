"""Tests for TensorBoard metrics logger."""
from training.metrics import MetricsLogger


def test_logger_creation(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    assert logger is not None


def test_log_training_step(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    logger.log_training(
        step=100, policy_loss=0.5, value_loss=0.3,
        entropy=1.2, clip_fraction=0.1, learning_rate=3e-4,
    )
    logger.close()
    event_files = list((tmp_path / "runs").rglob("events.out.*"))
    assert len(event_files) > 0


def test_log_evaluation(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    logger.log_evaluation(
        step=200, win_rate=0.55, avg_reward=0.3,
        avg_hand_value=3.5, draw_rate=0.15,
    )
    logger.close()


def test_log_league(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    logger.log_league(step=300, current_elo=1100.0, best_elo=1100.0, pool_size=5)
    logger.close()
