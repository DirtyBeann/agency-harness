# Architecture

Agency Harness Universal is fail-closed coding-agency rails:

1. Declarative state machines under `workflows/`
2. Strict verdict JSON Schemas under `contracts/`
3. Binder CLI (`scripts/run_state.py`) that refuses illegal transitions
4. Failure replay fixtures under `failures/`
5. Optional host adapters under `adapters/` (Codex CLI, Kilo, Grok Build, OpenCode)

Skills teach *when* to call the CLI. The CLI exit code is the gate.
Human operator remains final authority.
