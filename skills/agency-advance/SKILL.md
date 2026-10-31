---
name: agency-advance
description: Use when advancing or checking Agency Harness workflow state. Calls the binder CLI; never hand-edits state.
---

# Agency advance

1. Identify workflow id (`example-feature-branch` or `example-ui-gauntlet` unless operator named another).
2. List legal next edges:

```bash
python scripts/advance.py --workflow <id> --from <STATE> --list-next
```

3. To attempt a transition:

```bash
python scripts/run_state.py --workflow <id> --from <STATE> --to <STATE> --flags-dir flags
```

4. Non-zero exit = refused. Report the ledger/refusal; do not retry by editing files.
5. Models: read `config/models.yaml`. If values are still `[ADD_MODEL_HERE]`, stop and ask the operator.
