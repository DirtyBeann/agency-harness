# Failure replay fixtures

Run the portable replay harness:

```bash
python scripts/run_failure_replay.py
```

Each case under `cases/` has an `input.json` and `expected.json`.
Fixtures are synthetic. Secret-shaped strings are markers for redact tests, not live credentials.

Optional: you may add a local `promptfoo/` config later for CI. It is not required in this pack.