# Using with Codex CLI

Codex CLI is OpenAI's terminal coding agent. It fits this harness well because it reads `AGENTS.md` on its own, runs shell commands inside a sandbox, and can run headless with `codex exec`.

## 1. Install and sign in

Follow the official Codex CLI install guide, then:

```bash
codex login
```

Never paste an API key into a Codex chat. Use `codex login` or an environment variable.

## 2. Open the repo

```bash
git clone https://github.com/DirtyBeann/agency-harness agency-harness
cd agency-harness
python -m pip install -r requirements.txt
codex
```

Codex loads the root [`AGENTS.md`](../AGENTS.md), which tells it:

- the binder CLI is the only way to change workflow state
- `flags/PAUSE` means stop
- verdicts must validate against `contracts/`
- Security `escalate` means ask the human
- secrets never go in chat, ledger, or git

## 3. Install the skills

```bash
bash adapters/codex/install-skills.sh            # macOS / Linux
powershell -File adapters/codex/install-skills.ps1   # Windows
```

This copies `agency-advance` and `agency-replay` into `.agents/skills/`, where Codex finds them. Invoke them with `$agency-advance` or let Codex pick them when you ask about workflow state.

## 4. Config (optional)

Merge [`adapters/codex/examples/config.example.toml`](../adapters/codex/examples/config.example.toml) into `~/.codex/config.toml`. It sets `workspace-write` sandboxing, `on-request` approvals, marks the repo as trusted, and shows a separate `harness-critic` profile so your reviewer is not the same model as your builder.

## 5. Map roles to Codex

| Harness role | Codex suggestion |
|---|---|
| Conductor / builder (`code-b`) | Default profile, `workspace-write` |
| Reviewer, Security, Skeptic | `--profile harness-critic` (read-only, different model) |
| Operator | You. Codex never merges to `main`. |

Codex can also run a review pass with `codex exec review`. Treat its output as input to a ReviewVerdict, not as the verdict itself: write the verdict with `scripts/write_verdict.py` so the schema check applies.

## 6. Headless smoke test

```bash
codex exec --sandbox workspace-write "Read AGENTS.md, then run python scripts/run_failure_replay.py and python scripts/binder_smoke.py --dry-run and report pass/fail counts."
```

See [`docs/examples/codex-demo.md`](./examples/codex-demo.md) for a real run.

## What Codex does not enforce

Codex follows `AGENTS.md` and skills as instructions, so they are advisory. The enforced parts are the binder exit codes, schema validation, and failure replay. Use Codex's sandbox and approval settings as a second layer, and keep a human as the final authority.
