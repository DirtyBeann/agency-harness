# Code A/B/C implementer tiers (orchestrate-only conductor)

**Job titles, not model names.** `code-c` / `code-b` / `code-a` must **not** hard-pin `model` in config so the IDE GUI can change providers anytime.

The conductor stays plan / orchestrate / UNIFY. APPLY goes to tiered implementers. Suggested spawn defaults live in docs or operator notes only, never as frozen agent pins.

## Agents (roles)

| Agent | Model | Role |
|-------|-------|------|
| conductor (e.g. `esco-conductor`) | **GUI-owned** (suggested: `[ADD_MODEL_HERE]`) | Plan / orchestrate / UNIFY |
| `code-c` | **GUI-owned** (no hard pin) | Cheap / fast APPLY |
| `code-b` | **GUI-owned** (no hard pin) | Default APPLY |
| `code-a` | **GUI-owned** (no hard pin) | Max / escalated APPLY |
| legacy `code` | **GUI-owned** | Optional deprecated alias of `code-b` |
| `plan` | optional | `.paul` helper only; not daily primary |

## Hard invariants

1. Every APPLY spawn sets **explicit agent id and model** (children must not inherit the conductor model).
2. Never spawn unpinned `general` for APPLY.
3. No swarm-by-default.
4. Close sticky Agent Manager child tabs after APPLY so session model does not stick.
5. `plan` is not the daily primary planner; conductor composes plans.
6. Tier slugs are titles; GUI owns their models.

## Suggested spawn defaults (examples only)

Replace with your providers. Do **not** bake these into agent `model` fields if you want GUI control.

- `code-c`: cheap / local-capable
- `code-b`: default mid tier
- `code-a`: strongest non-conductor pool (failover ladder in operator notes)

## Example agent stubs

See `adapters/kilo/examples/code-tiers.example.jsonc` (no `model` keys on tiers).

## Conductor model

Conductor model is also **GUI-owned** (no hard pin) when you want IDE swaps. Suggested default remains the operator hard-task model ([ADD_MODEL_HERE]). APPLY children must still get an explicit model on spawn.

