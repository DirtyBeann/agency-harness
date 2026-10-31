# Changelog

## Unreleased

- Add Codex CLI support: root `AGENTS.md`, `adapters/codex/` (skill installers, example `config.toml`), `docs/CODEX.md`, and a sample headless run in `docs/examples/codex-demo.md`.
- Rewrite README in plain language; fill LICENSE copyright holder.
- Fix: `binder_smoke.py` now creates `tmp/` (fresh clones crashed). `gate_review.py` output is ASCII only (cp1252 consoles crashed the escalate path). Both found by the Codex demo run.

## 0.1.2 - 2026-09-11

- Add `docs/CODE-TIERS.md` and `adapters/kilo/examples/code-tiers.example.jsonc`: implementer tiers `code-c` / `code-b` / `code-a` as **job titles with GUI-owned models** (no hard-coded `model`).
- Conductor examples updated: mandatory explicit model on APPLY spawn; no conductor-model inherit; plan agent demoted to optional helper.
- Sync rule unchanged: ask before mirroring private farm; keep placeholders for real model ids.

## 0.1.0 - 2026-09-09

- Initial sanitized universal pack: contracts, example workflows, binder CLI, failure replay, L1 checks.
- AI setup prompt + adapters for Kilo, Grok Build, OpenCode.
- Private integrity reports kept out of the published tree (`docs/private/`, gitignored).

## 0.1.1 - 2026-09-09

- Add portable scripts/vi_preview.ps1 + docs/vi-preview-browser-use.md for isolated CDP VI preview.
- Document PAYG priority (DeepSeek then Z.AI/GLM) without binder hard-refuse (docs/payg-priority.md).
- Hook notes on workflows/example-ui-gauntlet.md.

