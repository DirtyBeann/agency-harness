# Agency Harness Universal

Fail-closed rails for running a team of AI coding agents.

By Jason Escobar ([@DirtyBeann](https://github.com/DirtyBeann)) of [MadeByEsco](https://madebyesco.com).

Agency Harness gives your coding agents (Codex CLI, Kilo Code, Grok Build CLI, OpenCode, or anything that can run Python) a shared rulebook they cannot quietly skip. Agents propose work. A small Python "binder" CLI decides whether each step is allowed. Reviews, security checks, and skeptic passes are written as strict JSON verdicts, and anything missing, malformed, or unsafe is refused by default.

It is a sanitized, portable version of the setup I use to run my own multi-agent coding farm. No keys, IPs, private model maps, or product code are included. Every model and provider is a placeholder you fill in.

## What it does

- **Roles, not hard-coded models.** A conductor plans and delegates, tiered implementers (`code-c`, `code-b`, `code-a`) write code, and separate Reviewer, Security, Skeptic, and UI Critic roles each return a verdict. You map each role to whatever model you like in `config/models.yaml`.
- **State machines with a gate.** Workflows such as `example-feature-branch` and `example-ui-gauntlet` live in `workflows/`. The binder (`scripts/run_state.py`, `scripts/advance.py`) refuses illegal transitions with a non-zero exit code, so an agent cannot jump from "coding" to "merge ready" without the required verdicts.
- **Verdict schemas.** `contracts/` holds JSON Schemas for review, security, skeptic, governor, gauntlet, and ledger events. Invalid verdicts fail closed. Security `escalate` is treated as "ask the human", never as "allow".
- **Routing rules.** Builder and critic may not run on the same subscription pool, and pay-as-you-go hops can require a one-time human OK (`flags/payg_confirm.on`).
- **Kill switches.** Dropping a `flags/PAUSE` file halts mutating transitions.
- **Redacting ledger.** `scripts/append_ledger.py` refuses secret-shaped text before it hits the log.
- **Failure replay.** `failures/cases/` holds 13 synthetic regression cases (false skeptic pass, same-pool hop, missing verdicts, secret in ledger, and more) that must keep failing the right way.
- **Skills and adapters.** `skills/` contains host-agnostic skill files that teach an agent when to call the CLI. `adapters/` has install notes and example configs for Codex CLI, Kilo Code, Grok Build CLI, and OpenCode. A root `AGENTS.md` gives any agent the house rules.

## Requirements

- Python 3.10 or newer (tested on 3.14)
- `pip install -r requirements.txt` (only dependency: `jsonschema`)
- One of: Codex CLI, Kilo Code, Grok Build CLI, OpenCode, or any agent that can run shell commands
- Optional: PowerShell for `scripts/vi_preview.ps1` and `scripts/make_share_zip.ps1`

## Quick start

### Option A: let your AI set it up

1. Clone this repo and open it as the workspace in your coding agent.
2. Paste the contents of [`AI-SETUP-PROMPT.md`](./AI-SETUP-PROMPT.md) as the first message.
3. Answer its questions about your host, providers, and models.
4. It creates `config/models.yaml`, installs the adapter skills, and runs the smoke tests. It should never print an API key; keys stay in environment variables.

### Option B: manual

```bash
git clone https://github.com/DirtyBeann/agency-harness agency-harness
cd agency-harness
python -m pip install -r requirements.txt
cp config/models.example.yaml config/models.yaml   # Windows: copy config\models.example.yaml config\models.yaml
# edit config/models.yaml and replace every [ADD_*] placeholder
python scripts/validate_setup.py
python scripts/binder_smoke.py --dry-run
python scripts/run_failure_replay.py
```

Try a transition:

```bash
python scripts/advance.py --workflow example-feature-branch --from HOLD --list-next
python scripts/run_state.py --workflow example-feature-branch --from HOLD --to SCOPE_LOCKED --flags-dir flags --dry-run
```

Then follow the adapter for your host:

| Host | Adapter |
|---|---|
| Codex CLI | [`adapters/codex/`](./adapters/codex/) and [`docs/CODEX.md`](./docs/CODEX.md) |
| Kilo Code | [`adapters/kilo/`](./adapters/kilo/) |
| Grok Build CLI | [`adapters/grok-build/`](./adapters/grok-build/) |
| OpenCode | [`adapters/opencode/`](./adapters/opencode/) |

### Using with Codex CLI

Codex reads the root [`AGENTS.md`](./AGENTS.md) automatically, so the rules load as soon as you start `codex` in this folder. Install the skills with `adapters/codex/install-skills.sh` (or `.ps1`), optionally merge the example `config.toml`, and run the smoke tests headless:

```bash
codex exec --sandbox workspace-write "Read AGENTS.md, then run the failure replay and binder smoke tests and report results."
```

Full guide: [`docs/CODEX.md`](./docs/CODEX.md). Sample run: [`docs/examples/codex-demo.md`](./docs/examples/codex-demo.md).

Claude Code adapters are not included yet.

## What is enforced and what is advice

| Layer | Enforcement |
|---|---|
| Binder CLI (`run_state.py`, `advance.py`) | Enforced: non-zero exit means refused |
| Verdict JSON Schema validation | Enforced: invalid verdict fails closed |
| Failure replay and L1 checks | Enforced in CI or local smoke runs |
| Host skill allowlist (for example Kilo deny-default) | Partly enforced, if you apply the adapter config |
| `SKILL.md` instructions | Advice only; a model can ignore them |
| Human operator | Final authority |

Skills teach the agent when to call the CLI. The CLI is the gate.

## Layout

| Path | Purpose |
|---|---|
| `contracts/` | Verdict and ledger JSON Schemas |
| `workflows/` | Example state machines |
| `scripts/` | Binder, gates, ledger, L1 checks, failure replay, setup validation, VI preview |
| `failures/cases/` | Synthetic regression fixtures |
| `flags/` | Example kill switches |
| `skills/` | Portable skill files |
| `adapters/` | Per-host install notes and examples |
| `config/` | Model and provider placeholders |
| `docs/` | Architecture, conductor pattern, code tiers, enforcement levels, sharing |
| `ORCHESTRATION.md` | Roles and control-plane rules |
| `AI-SETUP-PROMPT.md` | Paste-into-your-AI setup guide |
| `AGENTS.md` | House rules any agent (Codex and others) loads automatically |

## Security

- `config/models.yaml`, `.env`, `ledger/*.jsonl`, and `tmp/` are gitignored. Keep it that way.
- Never paste live API keys into chat, the ledger, or git.
- Strings like `sk_live_` inside the schemas and scripts are detection patterns, not credentials.

See [`SECURITY.md`](./SECURITY.md) and [`docs/SHARING.md`](./docs/SHARING.md).

## Status

Early (v0.1.x). The core rails, schemas, and smoke tests work. Adapters are notes and examples, so expect to adjust paths for your setup.

## Author

Built and maintained by Jason Escobar ([@DirtyBeann](https://github.com/DirtyBeann)), [MadeByEsco](https://madebyesco.com), JKMK Ventures LLC. Licensed under Apache-2.0, see [LICENSE](./LICENSE).

## License

Apache-2.0. See [`LICENSE`](./LICENSE).