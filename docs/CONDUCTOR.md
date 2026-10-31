# Conductor pattern (optional)

A **conductor** is an in-IDE primary agent that brainstorms, locks a plan, and delegates implementation. It is **not** a product orchestrator mode and **not** a farm-wide control plane.

## Architecture (keep both layers)

| Layer | Owns | Does not own |
|---|---|---|
| **PAUL** (Plan-Apply-Unify) | Phase machine + plan SSOT under `.paul/` (PLAN / STATE / SUMMARY) | How specialists write code |
| **Superpowers** (curated skills) | Execute craft **after** plan lock (TDD, systematic-debug, verification-before-completion, executing-plans / subagent-driven-development on **specialists**) | Alternate plan format that races PAUL |
| **Binder CLI** (this pack) | Legal state transitions + on-disk verdicts | Agent chat UX |

**Rule:** PAUL decides *which phase* and *which artifact is SSOT*. Superpowers decides *how specialists execute inside APPLY*. Binder decides *whether the farm may advance*.

## Role split

| Actor | Duty |
|---|---|
| **Conductor** (primary) | Clarify → plan lock via Plan/Architect tasks → route specialists → synthesize. May brainstorm **pre-PLAN** only. |
| **Plan / Architect** | Write `.paul` PLAN / SUMMARY (conductor does **not**) |
| **Code / Debug / Frontend / …** | APPLY with Superpowers execute skills |
| **Reviewer / Security / Skeptic** | Verdicts on disk; conductor never invents PASS |
| **Operator (human)** | Approves plan lock, resolves PAUSE, owns live merge |

## B2 ACL shape (example)

See [`adapters/kilo/examples/conductor.permission.example.jsonc`](../adapters/kilo/examples/conductor.permission.example.jsonc).

Hard rules for the conductor agent:

1. **edit** deny-default; allow plan globs only (`.kilo/plans`, `.plans`, …). **Deny `.paul/**`** on the conductor - Plan agent writes PLAN/SUMMARY.
2. **skill** deny-default (`*:deny`). Allow only `paul` + curated pre-plan Superpowers (`brainstorming`, `using-superpowers`). **Deny** `writing-plans`, `executing-plans`, `subagent-driven-development` on the conductor.
3. **task** allowlist of specialists + `*:deny` (no self-task to conductor).
4. **bash** read-only inspect + binder validators; mutating advance/pause under `ask`.
5. Keep built-in **Orchestrator mode disabled** if your host still ships it (deprecated on modern Kilo).
6. No product source write; no ledger/secret/pools/host-config write; no self-verdicts.

## Skill junctions (before allowlisting)

1. Install PAUL skill into a host-visible skills root (copy or junction).
2. Copy curated Superpowers skills into your skills SSOT, then junction into the host:
   - Conductor: `brainstorming`, `using-superpowers` (+ `paul`)
   - Specialists: `executing-plans`, `subagent-driven-development`, `test-driven-development`, `verification-before-completion`, `systematic-debugging` (optional: review/worktree/finish skills)
3. Only then add skill names to `permission.skill` allowlists.

Do **not** allowlist skills that are not on disk.

## Model pin

Use `[ADD_MODEL_HERE]` for the conductor hard-task / high-effort slot in `config/models.yaml`. Prefer your strongest coding model at a high reasoning variant when available.

## Related

- `ORCHESTRATION.md` - logical roles
- `adapters/kilo/README.md` - Kilo install steps
- `AI-SETUP-PROMPT.md` - operator paste prompt (mentions optional conductor)

## Related: implementer tiers

See [CODE-TIERS.md](./CODE-TIERS.md). Conductor plans and routes to `code-c` / `code-b` / `code-a`. Those agents are **GUI-owned models** (no hard pin) so operators can swap providers without editing config. Spawns must still set an explicit model to avoid inheriting the conductor.
