# L1 deterministic gates

L1 checks are small deterministic scripts that run before (and in addition to)
any model judgment. They are local smoke-level enforcement: run them from the
repo root, and wire them into CI or a pre-share check if you want them hard.

## em-dash / slop scan

```bash
python scripts/l1_emdash_slop_check.py --fail-on-emdash docs/ README.md
```

Fails on em dashes (U+2014) and en dashes (U+2013), plus an optional tiny list
of AI-slop phrases (`--fail-on-slop`). Stdlib only, no network.

## axe accessibility wrapper

```bash
python scripts/l1_axe_check.py <url-or-html-file>
```

Wraps `@axe-core/cli` (npx, never auto-installed with `--allow-skip`) and falls
back to a Python Playwright bridge (`axe_playwright_python`) if present. It is a
deterministic pass/fail gate for rendered pages: exit 0 means zero axe
violations, non-zero means violations or errors.

### Skip policy

Missing tooling is an error by default: the script prints `SKIP: see
docs/l1-deterministic-gates.md` with the per-attempt details and exits 2. With
`--allow-skip` the same situation exits 0 and must be recorded in the run notes
as a SKIP, then re-run where the tooling exists (for example CI with Node and a
pinned `@axe-core/cli`). Never report an unrun gate as green.
