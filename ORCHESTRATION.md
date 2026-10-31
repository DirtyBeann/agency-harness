# Orchestration rules (universal)

## Control plane

Operator (human) + binder CLI. Agents propose; binder allows or refuses.

## Roles (logical - map to your agents)

| Role | Duty | Model slot |
|---|---|---|
| **Conductor** (optional) | Brainstorm, lock plan via Plan/Architect, delegate APPLY, synthesize. Does not write `.paul/**` or product src. | `hard_task` → `[ADD_MODEL_HERE]` |
| Builder / coder | Implement (Superpowers execute craft after lock) | `default_chat` or `hard_task` |
| Plan / Architect | Write PAUL PLAN / SUMMARY under `.paul/` | `hard_task` |
| Reviewer | Correctness review verdict | `hard_task` |
| Security | Auth/secrets/exploitability verdict | `hard_task` |
| Skeptic | Challenge false passes | `hard_task` |
| UI critic | Visual/a11y bar (gauntlet) | `vision` |
| Operator | Advance state, resolve pauses | n/a |

Fill model slots in `config/models.yaml` using `[ADD_MODEL_HERE]`.

See `docs/CONDUCTOR.md` for the PAUL + Superpowers conductor pattern and B2 ACL shape.

## Illegal without binder

- Editing `*.states.json` to skip gates
- Claiming merge-ready without required verdicts
- Continuing after `flags/PAUSE`
- Logging secrets into `ledger/`
- Conductor inventing Reviewer / Security / Skeptic verdicts

## Host adapters (you provide)

- Codex CLI / OpenCode / Kilo / Grok CLI: install `skills/` and ensure `python` can run `scripts/`
- Optional MCP later: wrap the same CLI - do not fork the state machine
- Optional Kilo `conductor` agent: `adapters/kilo/README.md`
