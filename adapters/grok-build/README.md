# Adapter: Grok Build CLI (xAI)

## Enforcement level

| Mechanism | Level |
|---|---|
| Binder + schemas + smoke scripts | **Enforceable** |
| Project/user `SKILL.md` discovery | **Advisory** (auto-invoke is model-gated) |
| Slash-invocable skills | **Advisory** unless you always invoke them yourself |

This pack does **not** ship Grok hooks/plugins yet. Skills teach; CLI enforces.

## Skill install paths

Grok Build discovers:

- Project: `./.grok/skills/<name>/SKILL.md` (walks up to repo root)
- User: `~/.grok/skills/<name>/SKILL.md`
- Also reads `.agents/skills/` and `.claude/skills/` for compatibility

**Recommended for this pack:** project-local

```text
agency-harness-universal/.grok/skills/agency-advance/SKILL.md
agency-harness-universal/.grok/skills/agency-replay/SKILL.md
```

Copy from `../../skills/...` or run `install-skills.sh` / `install-skills.ps1`.

Optional: add root `AGENTS.md` pointing at `AI-SETUP-PROMPT.md` and binder rules (see `../../AGENTS.md`).

## Setup checklist

1. Open this folder in Grok Build.
2. Install skills into `.grok/skills/`.
3. Paste `AI-SETUP-PROMPT.md` (or rely on `AGENTS.md`).
4. Fill `config/models.yaml` without pasting keys into chat.
5. Run validate + binder smoke + failure replay.

## Notes

- New skills load on a **new session**.
- `user-invocable: true` skills can appear as `/agency-advance` style commands depending on Grok Build version.
