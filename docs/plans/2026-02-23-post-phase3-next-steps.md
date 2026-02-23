# Post-Phase 3: What's Next & Potential Problems

**Date:** 2026-02-23
**Context:** Phase 3 (RL Training Infrastructure) is complete on `feature/phase3-rl-training`. All code is written, tested, and passing CI.

---

## Immediate Next Steps (Priority Order)

### 1. Merge Phase 3 to Main

**What:** Code review + merge `feature/phase3-rl-training` (20 commits) into `main`.

**Actions:**
- Run full test suite one final time (`uv run pytest -v`)
- Verify CI passes on the branch
- Create a PR, review for regressions against Phase 1/2
- Merge via squash or merge commit

**Risk:** Low. Phase 3 is additive (new `training/` module) with no changes to existing engine or UI code, except a minor fix in `game_session.py` (clearing agents list on game end).

---

### 2. Run First Training Session on GPU

**What:** Deploy Docker container to a GPU machine and run the first real training run (target: 100K-200K episodes).

**Actions:**
1. Provision a GPU machine (RTX 3080 Ti or better, 12GB+ VRAM)
2. Build Docker image: `docker build -t mahjong-train .`
3. Run initial short test (1000 episodes) to verify pipeline works end-to-end
4. Launch full training run:
   ```bash
   docker run --gpus all \
     -v ./checkpoints:/app/checkpoints \
     -v ./runs:/app/runs \
     mahjong-train --device cuda --episodes 200000
   ```
5. Monitor TensorBoard: `tensorboard --logdir runs/ --bind_all`
6. Watch for phase transition (warmup -> self-play at >50% win rate)

**Target metrics:**
- Win rate vs rule-based AI: **>80% over 1000 evaluation games**
- ELO: steady upward trajectory
- Policy loss: decreasing
- Entropy: stays above 0.5 during exploration, gradually decreases

---

### 3. Complete Phase 2 UI (Parallel with Training)

While the model trains (days/weeks), continue Phase 2 desktop UI work:

**Remaining Phase 2 tasks:**
- Wire Electron main process to spawn Python backend
- Complete WebSocket event flow (game actions -> server -> state updates)
- Fix discard flash bug (state transition race condition)
- Connect animation queue to draw/discard/meld/win events
- Fix replay viewer (backend needs to serialize GameState snapshots)
- End-to-end playable game vs rule-based AI

**Phase 2.5 polish:**
- Tile hover/click feedback (scale transforms)
- Turn indicator glow effect
- Table background gradient and shadows
- Typography hierarchy improvements
- Discard confirmation UX

---

### 4. Phase 4: Integrate Trained Model into UI

Once training converges (>80% win rate):

**Actions:**
1. Load best checkpoint (`best_elo.pt`) into the WebSocket server
2. Add model inference to `game_manager.py` (replace rule-based AI with RL agent)
3. Profile inference speed (must be <100ms per decision for real-time play)
4. Add ELO tracking for human player vs AI
5. Match history viewer in UI
6. Final polish pass
7. Windows installer (.exe via electron-builder)

---

## Potential Problems & Mitigations

### Training Problems

#### Problem 1: Model Doesn't Converge (Most Likely)

**Symptoms:** Win rate stays flat at 25-30%, loss oscillates, no ELO improvement after 50K+ episodes.

**Possible causes:**
- **Observation encoding too sparse** — 290-dim binary vector may not capture enough strategic information (e.g., tile counting, opponent hand estimation)
- **Reward too sparse** — Only rewarding at game end means the agent gets very infrequent learning signals
- **Network too small** — 650K params may be insufficient for the complexity of 16-tile mahjong
- **Action space mismatch** — 128 discrete actions may not map cleanly to all game situations

**Mitigations:**
1. Add **shaping rewards** (intermediate rewards for reducing shanten, completing melds, drawing useful tiles)
2. Increase network size (add layers, increase hidden dims to 1024)
3. Add **tile counting features** to observation (which tiles are still possible in the wall)
4. Try **LSTM/attention** instead of MLP to capture sequential dependencies
5. Increase batch size and rollout length for better gradient estimates

#### Problem 2: Action Masking Issues

**Symptoms:** Agent tries illegal moves, crashes during training, NaN losses.

**Possible causes:**
- Edge cases in legal action computation not covered by current tests
- Rare game states where no actions are legal (shouldn't happen, but game logic bugs could cause it)

**Mitigations:**
1. Add assertions in the environment that verify action masks always have at least one legal action
2. Run 10K episodes in debug mode logging every action mask
3. Add a fallback "pass" action that's always legal

#### Problem 3: Self-Play Collapse

**Symptoms:** ELO rises quickly then plateaus or oscillates. Agent learns to exploit specific opponent weaknesses rather than developing general strategy.

**Possible causes:**
- Opponent pool not diverse enough
- Too-fast transition from warmup to self-play
- Agent overfits to its own play style

**Mitigations:**
1. Keep rule-based opponents in the pool permanently (already 10% allocation)
2. Increase pool diversity: keep more historical checkpoints
3. Add **population-based training** (multiple agents training in parallel)
4. Slow down the warmup->self-play transition threshold (raise from 50% to 60%)

#### Problem 4: Training Instability (NaN/Divergence)

**Symptoms:** Loss suddenly goes to NaN or infinity, policy outputs become all zeros.

**Possible causes:**
- Learning rate too high
- Gradient explosion despite clipping
- Numerical issues in log-probability computation with masked actions

**Mitigations:**
1. Reduce learning rate (3e-4 -> 1e-4)
2. Add gradient norm monitoring to TensorBoard
3. Use `torch.clamp` on log-probs to prevent -inf
4. Add numerical stability checks in PPO update

#### Problem 5: Slow Training Speed

**Symptoms:** Each episode takes >1 second, training 200K episodes would take weeks.

**Possible causes:**
- Python game engine is the bottleneck (pure Python, no vectorization)
- PettingZoo AEC wrapper adds overhead per step
- GPU underutilized (small batch sizes, CPU-bound environment)

**Mitigations:**
1. **Profile first** — identify whether bottleneck is env, network, or PPO update
2. Vectorize environment: run N games in parallel using `multiprocessing`
3. Pre-compute legal actions more efficiently
4. Consider Cython or C extension for hot paths (shanten calculation, win detection)
5. Increase `n_steps` per rollout to amortize PPO update cost

---

### UI/Integration Problems

#### Problem 6: Model Inference Too Slow for Real-Time

**Symptoms:** AI takes >500ms per move, making the game feel sluggish.

**Possible causes:**
- Network forward pass too slow on CPU
- Observation encoding is expensive (iterating game state)
- Model loaded on wrong device

**Mitigations:**
1. Export model to ONNX for faster CPU inference
2. Use `torch.jit.script` for JIT compilation
3. Cache observation encoding between steps (incremental updates)
4. Profile and optimize the hot path

#### Problem 7: Electron + Python Subprocess Communication

**Symptoms:** WebSocket connection drops, server crashes, state desync.

**Possible causes:**
- Python server process management in Electron is fragile
- Port conflicts on user machines
- Stdout/stderr buffering issues

**Mitigations:**
1. Add health check pings on WebSocket
2. Implement automatic server restart on crash
3. Use `--port 0` for auto port selection, communicate port back to Electron
4. Add proper process cleanup on app exit

#### Problem 8: State Serialization Mismatch

**Symptoms:** UI shows wrong tiles, actions fail, scoring incorrect.

**Possible causes:**
- JSON serialization of GameState doesn't match TypeScript interfaces
- Tile ID encoding differs between Python and TypeScript
- Meld/action types not properly mapped

**Mitigations:**
1. Add schema validation (JSON Schema or Zod on frontend)
2. Generate TypeScript types from Python dataclasses (e.g., `pydantic` -> TS)
3. Add integration tests that verify full roundtrip serialization

---

### Architectural Problems

#### Problem 9: Phase 2 and Phase 3 Were Built in Parallel

**Symptoms:** Phase 2 UI assumes rule-based AI API shape that differs from trained model inference API.

**Possible causes:**
- `game_manager.py` was designed for rule-based AI, not neural network agents
- Different action representation between rule-based and RL agent

**Mitigations:**
1. Define a common `Agent` interface that both rule-based and RL agents implement
2. The current `RuleBasedAI` already returns `Action` objects — ensure RL agent does the same
3. Add a `NeuralAgent` wrapper that loads checkpoint and exposes the same API

#### Problem 10: Scoring Edge Cases in RL

**Symptoms:** Agent learns degenerate strategies (e.g., always going for minimum-score wins, or never attempting high-value hands).

**Possible causes:**
- Reward function normalizes by max score (81 tai) — most hands score 3-5 tai, so rewards are tiny
- Agent may not learn that high-value hands exist

**Mitigations:**
1. Scale rewards differently (e.g., log scale, or tiered bonuses)
2. Add curriculum: first learn to win at all, then learn to win with higher scores
3. Track average hand value in TensorBoard to detect this early

---

## Decision Points

These are choices you'll need to make during the next phases:

| Decision | When | Options |
|----------|------|---------|
| How long to train | After first 10K episodes | Continue if improving, stop if plateaued, tune hyperparams |
| Network architecture changes | If win rate <60% after 50K episodes | Bigger MLP, LSTM, Transformer, or hybrid |
| Reward shaping | If convergence is slow | Add intermediate rewards vs keep sparse |
| Distributed training | If single GPU is too slow | Multi-process env, or distributed PPO |
| When to integrate into UI | After 80% win rate achieved | Could do earlier for testing with weaker model |
| Release format | Phase 4 completion | Electron installer, web app, or both |

---

## Recommended Timeline

| Week | Activity |
|------|----------|
| 1 | Merge Phase 3 PR. Set up GPU machine. Start first training run. |
| 1-2 | Fix Phase 2 bugs (discard flash, animations, replay viewer). Monitor training. |
| 2-3 | Complete Phase 2 UI wiring (playable game vs rule-based AI). |
| 3-4 | Phase 2.5 polish. Evaluate training progress, tune hyperparams if needed. |
| 4-8 | Continue training. If converged, begin Phase 4 integration. |
| 8-10 | Phase 4: Human vs trained AI, ELO tracking, final polish. |
| 10-12 | Windows installer, README, release prep. |

---

## Summary

The critical path is:
1. **Merge Phase 3** (this week)
2. **Start training** (this week — it runs unattended)
3. **Fix Phase 2 UI** (while training runs)
4. **Evaluate and tune** (based on TensorBoard metrics)
5. **Integrate trained model** (once >80% win rate)
6. **Ship** (Phase 4 + installer)

The biggest risk is **training convergence** — if the model doesn't learn, you'll need to iterate on observation encoding, reward shaping, or network architecture. Everything else is incremental engineering work with known solutions.
