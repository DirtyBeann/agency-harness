# Smoke results

Re-run on any machine from this directory:

```bash
python scripts/binder_smoke.py --dry-run
python scripts/run_failure_replay.py
python -m unittest discover -s tests -v
```

Last run in this repo (2026-11-02, Windows, Python 3.14): binder_smoke pass=12 fail=0 (dry-run scratch dir auto-cleaned); failure replay 18/18; unittest 27 tests OK. The same three commands run in GitHub Actions on every push and pull_request (`.github/workflows/tests.yml`).
Treat the numbers above as historical; verify again after clone.
