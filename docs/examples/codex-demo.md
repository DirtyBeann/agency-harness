# Example: Codex CLI headless run

A real `codex exec` run against a fresh copy of this repo, lightly trimmed. Local paths and account details are replaced with placeholders. Codex's own inspection steps (reading the scripts, `git status`) are summarized rather than pasted in full.

## Setup

- Codex CLI v0.164.0, signed in with a ChatGPT account
- Sandbox: `workspace-write`, reasoning effort `low`, `--ephemeral`
- Working dir: a fresh copy of the repo with `git init`, no `tmp/` folder (same as a new clone)
- OS: Windows, Python 3.14

## Command

```powershell
codex exec --ephemeral --sandbox workspace-write -c model_reasoning_effort=low `
  "Read AGENTS.md. Then run python scripts/run_failure_replay.py and python scripts/binder_smoke.py --dry-run. Do not edit any files. Report: which rules from AGENTS.md apply to this task, the exact commands you ran, and the pass/fail counts from each."
```

## What Codex did

1. Read `AGENTS.md`.
2. Read `scripts/run_failure_replay.py` and `scripts/binder_smoke.py` to check for side effects before running them.
3. Checked that `flags/PAUSE` was absent and recorded `git status --short`.
4. Ran both test commands.
5. Re-checked `git status --short` (unchanged) and reported. It made no edits and did not retry.

## Codex's report (first run)

> Read `AGENTS.md` and ran both requested commands. **Neither command completed successfully.** I made no file edits or fixes and did not retry either command.
>
> | Exact command | Passed | Failed | Result |
> |---|---:|---:|---|
> | `python scripts/run_failure_replay.py` | 12 | 1 | 13 fixtures evaluated; exit code `1` |
> | `python scripts/binder_smoke.py --dry-run` | 0 completed | 0 evaluated | Aborted before any tests ran; exit code `1` |
>
> The failure replay missed **`05-security-escalate-coerced`**. It expected exit code `2`, but received `1` because `scripts/gate_review.py` raised a `UnicodeEncodeError` while printing the `U+2260` character through Windows `cp1252` encoding. The other 12 fixtures matched their expected outcomes, including expected refusals.
>
> The binder smoke test raised **`FileNotFoundError: [WinError 3]`** while trying to create its temporary fixture directory beneath the missing repository `tmp/` directory. It never emitted a pass/fail summary. This is a startup error, not a completed test run with zero failures.
>
> The applicable `AGENTS.md` rules were:
>
> - **CLI gates and no bypasses:** Report nonzero results; do not work around them by editing files or workflow state.
> - **No hand-editing workflow states:** Neither requested check authorizes modifying `workflows/*.states.json`.
> - **Kill switch:** I checked `flags/PAUSE`; it was absent.
> - **Verdict integrity:** Fixture results are test evidence, not real Reviewer, Security, Skeptic, or UI Critic verdicts.
> - **Security escalation:** `escalate` must not be treated as `allow`. The escalation fixture failed because of the encoding error described above.
> - **No secrets:** No credentials were accessed or intentionally printed.

## Why this run is useful

Codex followed the house rules: it reported the failures honestly instead of patching around them, and it found two real portability bugs that never showed up on the original machine:

1. **`binder_smoke.py` assumed `tmp/` exists.** `tmp/` is gitignored, so every fresh clone would crash. Fix: the script now creates `tmp/` first.
2. **`gate_review.py` printed a non-ASCII `≠` sign.** On consoles using `cp1252`, that crashed the escalate path, which turned an "ask the human" result (exit 2) into a generic failure (exit 1). Fix: plain ASCII `!=`.

## After the fixes

Re-run in a fresh copy with no `tmp/` and `PYTHONIOENCODING=cp1252`:

```text
python scripts/run_failure_replay.py
summary: 13 passed, 0 missed, 13 total
ok: all failure-replay fixtures matched expected outcomes

python scripts/binder_smoke.py --dry-run
RESULT  pass=11  fail=0
```