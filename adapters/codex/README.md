# Adapter: Codex CLI (OpenAI)

## Enforcement level

| Mechanism | Level |
|---|---|
| Binder + schemas + smoke scripts | **Enforceable** |
| Codex sandbox and approval policy (`sandbox_mode`, `approval_policy`) | **Partially enforceable** (set by you in `config.toml`) |
| Root `AGENTS.md` | **Advisory** (loaded into context every session) |
| `SKILL.md` in `.agents/skills/` | **Advisory** (auto-invoke is model-gated) |

This pack does **not** ship Codex hooks or plugins. Skills and `AGENTS.md` teach; the CLI enforces.

## How Codex picks up the harness

- **`AGENTS.md`**: Codex reads `AGENTS.md` from the repo root down to your working directory. This repo ships one at the root, so opening Codex here is enough to load the rules.
- **Skills**: Codex scans `.agents/skills/` from your working directory up to the repo root, plus `~/.agents/skills/` for user-wide skills.

**Recommended for this pack:** project-local skills

```text
agency-harness-universal/.agents/skills/agency-advance/SKILL.md
agency-harness-universal/.agents/skills/agency-replay/SKILL.md
```

Run `install-skills.sh` or `install-skills.ps1` from this folder, or copy from `../../skills/`.

## Setup checklist

1. Install Codex CLI and sign in (`codex login`). Use your own account or API key; never paste a key into chat.
2. `cd` into this repo (Codex prefers a git repo; otherwise pass `--skip-git-repo-check`).
3. Install skills into `.agents/skills/`.
4. Optional: merge [`examples/config.example.toml`](./examples/config.example.toml) into `~/.codex/config.toml`.
5. Start `codex` and paste `AI-SETUP-PROMPT.md`, or just ask it to follow `AGENTS.md`.
6. Fill `config/models.yaml` without pasting keys into chat.
7. Run validate + binder smoke + failure replay.

## Non-interactive check

```bash
codex exec --sandbox workspace-write "Read AGENTS.md, then run python scripts/run_failure_replay.py and python scripts/binder_smoke.py --dry-run and report pass/fail counts."
```

A sample run is in [`docs/examples/codex-demo.md`](../../docs/examples/codex-demo.md).

## Notes

- `workspace-write` lets Codex run the scripts and write under the repo (including `tmp/`) without touching the rest of your disk.
- Keep `approval_policy` at `on-request` or stricter for real work. Do not use `--dangerously-bypass-approvals-and-sandbox` outside a throwaway container.
- New skills may need a Codex restart to appear.
- See [`docs/CODEX.md`](../../docs/CODEX.md) for the full walkthrough.
