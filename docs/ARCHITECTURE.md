# Architecture

Agency Harness Universal is fail-closed coding-agency rails:

1. Declarative state machines under `workflows/`
2. Strict verdict JSON Schemas under `contracts/`
3. Binder CLI (`scripts/run_state.py`) that refuses illegal transitions
4. Failure replay fixtures under `failures/` plus unittest security suite under `tests/`
5. Optional host adapters under `adapters/` (Codex CLI, Kilo, Grok Build, OpenCode)

Skills teach *when* to call the CLI. The CLI exit code is the gate.
Human operator remains final authority.

## Binder hardening (2026-11-02)

- Verdict gates on `REVIEW->SKEPTIC` and `SKEPTIC->DEV_CANDIDATE` always run;
  `--no-strict` is refused on those edges (dev-only elsewhere).
- A `SkepticVerdict` with `verdict: PASS` is rejected unless it carries
  `evidence_index` or `artifact_paths` and no open
  `unverified`/`incomplete`/`failures`/`violations` (shared rule in
  `scripts/binder_rules.py`, mirrored by an if/then in
  `contracts/skeptic_verdict.schema.json`).
- Recorded run state under `ledger/state/<run_id>.json` plus the owner approval
  artifact (`OwnerApproval/v1`) gate `LIVE_GO` / `LIVE_NOGO`; see
  `docs/ENFORCEMENT_LEVELS.md`.
- The canonical `flags/PAUSE` is always checked; `--flags-dir` only adds a
  location, it can never mask it.
- Secret-shape detection lives in one module (`scripts/binder_rules.py`) used
  by `run_state.py`, `write_verdict.py` and `run_failure_replay.py`; the
  contract schemas embed the same two patterns.
