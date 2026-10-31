# example-feature-branch

Generic example state machine for a feature landing on an integration branch.

## Branch policy (example only)
Integration: dev. Live examples: main / master.
Agents never merge to main/master. Owner tests on dev, then ships.

## Gates
- REVIEW requires ReviewVerdict/v1 + SecurityVerdict/v1 (fail-closed).
- SKEPTIC requires SkepticVerdict/v1 PASS before DEV_CANDIDATE.
- Security escalate is not allow; owner decides.
- flags/PAUSE refuses mutate transitions (exit 10).

## Nested child
Taste-risk UI may nest example-ui-gauntlet. WIN is not ship.

## How to run
python scripts/run_state.py --workflow example-feature-branch --from HOLD --to SCOPE_LOCKED --flags-dir flags --dry-run
