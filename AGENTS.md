# AGENTS.md

Instructions for any coding agent working in this repo (Codex CLI reads this file automatically; Grok Build, OpenCode, and others can too).

## What this repo is

Agency Harness Universal: fail-closed rails for a team of AI coding agents. Agents propose. The binder CLI in `scripts/` allows or refuses. A human operator has final say.

## Ground rules

1. **The CLI is the gate.** Change workflow state only through `scripts/run_state.py` or `scripts/advance.py`. A non-zero exit means refused. Report the refusal; never retry by editing files.
2. **Never hand-edit** `workflows/*.states.json` to skip a gate.
3. **Kill switch.** If `flags/PAUSE` exists, stop mutating work and tell the operator. If `flags/payg_confirm.on` exists, ask once before the first pay-as-you-go hop.
4. **Verdicts, not vibes.** Review, Security, Skeptic, and UI Critic results are JSON verdicts that must validate against `contracts/*.schema.json`. Write them with `scripts/write_verdict.py` and check them with `scripts/validate_verdict.py` or `scripts/gate_review.py`. Do not invent a verdict for a role you are not playing.
5. **Security `escalate` is not `allow`.** It means stop and ask the human.
6. **No secrets.** Never print, log, or commit API keys. Keys live in environment variables. Ledger writes go through `scripts/append_ledger.py`, which refuses secret-shaped text.
7. **Branches.** Agents work on feature branches and never merge to `main` or `master`.
8. **Builder and critic** must not run on the same subscription pool.

## Roles

See `ORCHESTRATION.md`. Short version: Conductor (plans, delegates), Builder tiers `code-c` / `code-b` / `code-a` (implement), Reviewer, Security, Skeptic, UI Critic, and the human Operator. Model slots live in `config/models.yaml` (copy from `config/models.example.yaml`). If a slot still says `[ADD_MODEL_HERE]`, stop and ask.

## Useful commands

```bash
python -m pip install -r requirements.txt
python scripts/validate_setup.py            # fails until config/models.yaml is filled
python scripts/binder_smoke.py --dry-run    # binder smoke tests
python scripts/run_failure_replay.py        # 18 regression fixtures
python scripts/advance.py --workflow example-feature-branch --from HOLD --list-next
python scripts/run_state.py --workflow example-feature-branch --from HOLD --to SCOPE_LOCKED --flags-dir flags --dry-run
```

## First-time setup

If the operator asks you to set this pack up, follow `AI-SETUP-PROMPT.md`.

## Writing style

No em dashes or en dashes in prose. `scripts/l1_emdash_slop_check.py` enforces this.
