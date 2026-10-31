---
id: payg-priority
updated: 2026-09-09
---

# PAYG priority (portable policy)

## Defaults in this pack

- **No** binder hard-refuse for PAYG pools by default.
- Soft flag `flags/payg_confirm.on` remains an optional ask-before-first-PAYG-hop.
- When PAYG is needed, prefer in order:
  1. DeepSeek PAYG pool id (example: `pool-payg-deepseek`)
  2. Z.AI / GLM PAYG pool id (example: `pool-payg-glm`)
- Other providers: set **console overage caps** in each vendor console (not a harness hard-block).

## Agent rule

If a subscription pool is dead and PAYG is next: ask the operator once, prefer DeepSeek then Z.AI/GLM, and do not invent a hard refuse that blocks intentional limited overage.