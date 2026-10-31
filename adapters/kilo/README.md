# Adapter: Kilo Code (CLI / extension)

## Enforcement level

| Mechanism | Level |
|---|---|
| Binder + schemas + smoke scripts | **Enforceable** |
| `permission.skill` deny-default + allowlist | **Partially enforceable** (if applied in Kilo settings) |
| `SKILL.md` content | **Advisory** |

## Skill install paths (typical)

Copy or junction these folders into a Kilo-visible skills directory:

- `skills/agency-advance` → e.g. `%USERPROFILE%\.config\kilo\skills\agency-advance` or `%USERPROFILE%\.kilocode\skills\…`
- `skills/agency-replay` → same parent

Also acceptable: project-local skills dir if your Kilo build scans the repo.

Verify the exact skills root in your Kilo version (names vary: `.config/kilo`, `.kilocode`, `.kilo`).

## Deny-default example (pack skills)

See [`permission.skill.example.jsonc`](./permission.skill.example.jsonc).

Merge carefully into your existing Kilo permissions. **Do not** flip global allow. Only allow:

- `agency-advance`
- `agency-replay`

…plus whatever else you already trust.

## Optional: Conductor agent (PAUL + Superpowers)

Pattern overview: [`docs/CONDUCTOR.md`](../../docs/CONDUCTOR.md).

### 1) Junction skills **before** allowlisting

**PAUL** (plan SSOT):

- Obtain the PAUL skill tree (upstream PAUL / Plan-Apply-Unify pack for your host).
- Place it so Kilo can see `paul/SKILL.md` (copy or junction into your skills SSOT, then into `%USERPROFILE%\.config\kilo\skills\paul`).

**Superpowers** (curated - do not dump the entire pack onto the conductor):

| Audience | Skills |
|---|---|
| Conductor | `brainstorming`, `using-superpowers` (+ `paul`) |
| Specialists (code/debug/frontend/general/…) | `executing-plans`, `subagent-driven-development`, `test-driven-development`, `verification-before-completion`, `systematic-debugging` |
| Optional specialist extras | `dispatching-parallel-agents`, `requesting-code-review`, `receiving-code-review`, `using-git-worktrees`, `finishing-a-development-branch` |

**Do not** allowlist `writing-plans` / `executing-plans` / `subagent-driven-development` on the **conductor** - PAUL owns plan artifacts; specialists own execute craft.

### 2) Add agent `conductor`

In your Kilo agent config (e.g. `kilo.jsonc`):

1. Copy permission shape from [`examples/conductor.permission.example.jsonc`](./examples/conductor.permission.example.jsonc).
2. Paste prompt pillars from [`examples/conductor.prompt.example.md`](./examples/conductor.prompt.example.md) into the agent `prompt` field.
3. Set `mode` to `primary` (or `all` only if `@conductor` mentions are required).
4. Pin model to your `[ADD_MODEL_HERE]` hard-task id + high reasoning variant when available.
5. Confirm built-in Orchestrator / equivalent stays **disabled**.
6. Confirm Plan (or equivalent) agent retains `.paul/**` **allow**; conductor keeps `.paul/**` **deny**.

### 3) Specialist skill allows

On implementer agents, allow the Superpowers execute skills listed above (deny-default still applies). Do not put those execute skills on the conductor.

## Setup checklist

1. Open this harness folder in Kilo.
2. Paste `AI-SETUP-PROMPT.md`.
3. Install pack skills (`agency-advance` / `agency-replay`) via copy/junction or `install-skills.ps1`.
4. Apply allowlist example (or equivalent).
5. Optional: install PAUL + curated Superpowers; add `conductor` per above.
6. `python scripts/validate_setup.py && python scripts/binder_smoke.py --dry-run`

## Windows helper

`install-skills.ps1` copies the two pack skills into `%USERPROFILE%\.kilocode\skills` (creates the dir). Edit the script if your Kilo skills path differs. It does **not** install PAUL or Superpowers - those come from their upstream packs.
