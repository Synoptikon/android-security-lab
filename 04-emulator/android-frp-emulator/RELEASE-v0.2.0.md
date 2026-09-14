# FRP Emulator v0.2.0 — Controlled Transition Audit

## Scope

This release extends the controlled FRP simulator with deterministic transition-matrix coverage and replay regression tests. It does not interact with Android devices, ADB/Fastboot, credentials, or real FRP state.

## Release gates

- Full pytest suite passes.
- Scenario `ci-001` reaches `DEVICE_READY` with the expected event sequence.
- Transition matrix coverage is 1.0 with no uncovered transitions.
- Formal audit passes with zero invariant failures.
- Reproducibility manifest passes.
- Release validation remains `controlled-simulator-only`.

## Next boundary

The next increment should focus on malformed persisted-state rejection and explicit fault-injection tests inside the simulator boundary.
