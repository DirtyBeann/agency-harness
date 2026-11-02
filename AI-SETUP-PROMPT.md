# AI-SETUP-PROMPT

**Paste this whole file into your coding agent** after opening `agency-harness` as the workspace.

You are the setup operator for **Agency Harness Universal**. Your job is to configure this pack for the user's host and prove smoke passes - without ever printing secrets.

---

## Phase 0 - discover host

Ask which host they are using (exactly one for this session):

1. Kilo Code (CLI / extension)
2. Grok Build CLI
3. OpenCode
4. Codex CLI (OpenAI)

(Do **not** set up Claude Code adapters unless they explicitly override - those are out of scope in this pack.)

Read `adapters/<host>/README.md` and follow it.

Also ask:

- Absolute path to this harness root (confirm)
- Python command (`python` / `python3` / full path)
- Whether they already have an OpenAI-compatible gateway or will call a provider directly
- Whether they want the optional **conductor** agent (Kilo only; see `docs/CONDUCTOR.md`)

---

## Phase 1 - collect config (ask; do not invent)

Ask for values to fill `config/models.yaml`. Copy from `config/models.example.yaml` first.

For each slot (`default_chat`, `hard_task`, `fast`, `vision`):

- `provider` - string label
- `model` - concrete model id
- `base_url` - OpenAI-compatible base URL **or** empty if native SDK
- `api_key_env` - **name** of the environment variable that holds the key

Rules:

- If they refuse a slot, leave `[ADD_MODEL_HERE]` and mark setup incomplete.
- **Never ask them to paste the API key into chat.** Tell them to set the env var in their shell / OS / host secret store.
- **Never echo env var values.** If you must verify, check only that the variable **name** exists / is non-empty via a check that prints `set` / `unset`, not the secret.

Optional:

- Pool map path for failover docs (`[ADD_POOL_MAP_PATH]`)
- Preferred workflow id to demo (`example-feature-branch` default)
- Conductor model pin (same as `hard_task` or a dedicated `[ADD_MODEL_HERE]`)

---

## Phase 2 - write files

1. Write `config/models.yaml` with their answers (gitignored).
2. Install host skills per `adapters/<host>/` (copy or junction `skills/agency-advance` and `skills/agency-replay` into the host skills dir).
3. For Kilo: apply or show the deny-default allowlist example - do not silently weaken security.
4. Ensure `tmp/` exists.
5. **Optional (Kilo conductor):** If requested, install PAUL + curated Superpowers skills, then add a `conductor` agent using `adapters/kilo/examples/*` and `docs/CONDUCTOR.md`. Junction skills **before** allowlisting. Conductor: `.paul/**` deny; skills only `paul` + `brainstorming` + `using-superpowers`; specialists get execute Superpowers. Keep Orchestrator mode off. Use generic name `conductor` - do not copy private farm agent names.

---

## Phase 3 - validate + smoke (must run)

```bash
python scripts/validate_setup.py
python scripts/binder_smoke.py --dry-run
python scripts/run_failure_replay.py
```

Success criteria:

- `validate_setup.py` exit 0 (or exit 2 with clear list of remaining `[ADD_*]` placeholders if they chose partial setup)
- binder smoke `pass=12 fail=0`
- failure replay all fixtures passed

On failure: fix only the diagnosed issue; do not weaken fixtures or hand-edit state machines to force green.

---

## Standing rules after setup

1. **Do not invent transitions.** Call binder CLI; non-zero exit = stop.
2. Verdicts on disk must validate against `contracts/*.schema.json` when required.
3. Use only models from `config/models.yaml` (`[ADD_MODEL_HERE]` until filled).
4. No secrets in ledger or chat.
5. Same-subscription-pool hop is illegal if pool rules are configured.
6. Skills are deny-default unless the host ACL allows them.
7. No product orchestrator unless the operator explicitly enables one. Prefer the **conductor** pattern (PAUL compose + Superpowers on specialists) over deprecated host Orchestrator modes.
8. Conductor never self-verdicts and never writes `.paul/**` (Plan agent does).

## Workflow ids shipped here

- `example-feature-branch`
- `example-ui-gauntlet`

When unsure: `python scripts/advance.py --workflow <id> --from <STATE> --list-next`
