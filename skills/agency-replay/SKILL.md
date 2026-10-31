---
name: agency-replay
description: Use when validating harness regressions via failure fixtures.
---

# Agency failure replay

```bash
python scripts/run_failure_replay.py
```

Expect all fixtures under `failures/cases/` to pass. Do not weaken fixtures to get a green run.
