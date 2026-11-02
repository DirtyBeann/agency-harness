# Adapter: OpenCode

## Enforcement level

| Mechanism | Level |
|---|---|
| Binder + schemas + smoke scripts | **Enforceable** |
| OpenCode `skill` tool + `SKILL.md` | **Advisory** |
| Permission `deny` on skills (if configured) | **Partially enforceable** |

## Skill install paths

OpenCode loads skills from (project and global):

| Scope | Path |
|---|---|
| Project | `.opencode/skills/<name>/SKILL.md` |
| Project | `.agents/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` (compat) |
| Global | `~/.config/opencode/skills/<name>/SKILL.md` |
| Global | `~/.agents/skills/<name>/SKILL.md` |

**Recommended:** project `.opencode/skills/` inside this harness folder.

```text
agency-harness/.opencode/skills/agency-advance/SKILL.md
agency-harness/.opencode/skills/agency-replay/SKILL.md
```

Each `SKILL.md` frontmatter `name` must match the folder name (already true for shipped skills).

## Setup checklist

1. Open this folder as the OpenCode project.
2. Run `install-skills.ps1` or `install-skills.sh`.
3. Paste `AI-SETUP-PROMPT.md` into the session (or reference it from your instruction file).
4. Configure `config/models.yaml` (env var names only for keys).
5. `python scripts/validate_setup.py && python scripts/binder_smoke.py --dry-run`

## Notes

- Skills are on-demand via OpenCode's skill tool - description text matters.
- No OpenCode marketplace package is shipped here; folder copy is the install.
