#!/usr/bin/env python3
"""L1 deterministic gate: em-dash / en-dash + short AI-slop phrase scan.

Scan text files (or stdin) for:
  - em dash U+2014
  - en dash U+2013
  - a small configurable list of AI-slop phrases (keep tiny; avoid FP hell)

Exit 0 = clean. Exit 1 = findings (when corresponding --fail-on-* is set).
Skips binary-looking files and common junk dirs (node_modules, .git, etc.).

Usage:
  python scripts/l1_emdash_slop_check.py path [path ...]
  python scripts/l1_emdash_slop_check.py --json path
  type file.txt | python scripts/l1_emdash_slop_check.py --stdin
  python scripts/l1_emdash_slop_check.py --fail-on-emdash --fail-on-slop docs/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EM = "\u2014"  # em dash
EN = "\u2013"  # en dash

# Keep this list SHORT and documented. Prefer rare multi-word tells over single
# words that appear in real product copy. "seamless" / "robust solution" are
# intentional owner-facing slop catches; tighten later if FP noise appears.
DEFAULT_SLOP = [
    "delve",
    "landscape of",
    "it's important to note",
    "In today's digital",
    "seamless",
    "robust solution",
]

SKIP_DIR_NAMES = {
    "node_modules",
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
}

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".toml", ".html", ".htm", ".css", ".scss", ".rs", ".go", ".java", ".kt",
    ".cs", ".rb", ".php", ".sh", ".ps1", ".cmd", ".bat", ".sql", ".xml",
    ".vue", ".svelte", ".astro", ".mdx", ".rst", ".ini", ".cfg", ".env.example",
}


def is_skipped_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".")


def looks_binary(sample: bytes) -> bool:
    if b"\x00" in sample:
        return True
    if not sample:
        return False
    textish = sum(1 for b in sample if b in (9, 10, 13) or 32 <= b < 127 or b >= 128)
    return (textish / len(sample)) < 0.85


def iter_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file():
            out.append(p)
            continue
        if not p.is_dir():
            continue
        for child in p.rglob("*"):
            if not child.is_file():
                continue
            if any(is_skipped_dir(part) for part in child.parts):
                continue
            out.append(child)
    return out


def scan_text(text: str, source: str, slop_phrases: list[str]) -> list[dict]:
    findings: list[dict] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        if EM in line:
            findings.append({
                "source": source,
                "line": i,
                "kind": "emdash",
                "char": "U+2014",
                "snippet": line.strip()[:160],
            })
        if EN in line:
            findings.append({
                "source": source,
                "line": i,
                "kind": "endash",
                "char": "U+2013",
                "snippet": line.strip()[:160],
            })
        lower = line.lower()
        for phrase in slop_phrases:
            if phrase.lower() in lower:
                findings.append({
                    "source": source,
                    "line": i,
                    "kind": "slop",
                    "phrase": phrase,
                    "snippet": line.strip()[:160],
                })
    return findings


def scan_file(path: Path, slop_phrases: list[str]) -> list[dict]:
    try:
        raw = path.read_bytes()
    except OSError as e:
        return [{"source": str(path), "line": 0, "kind": "error", "snippet": str(e)}]
    sample = raw[:8192]
    if looks_binary(sample):
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")
    return scan_text(text, str(path), slop_phrases)


def main() -> None:
    ap = argparse.ArgumentParser(description="L1 em-dash / en-dash / AI-slop scan")
    ap.add_argument("paths", nargs="*", help="Files or directories to scan")
    ap.add_argument("--stdin", action="store_true", help="Scan stdin as one document")
    ap.add_argument("--json", action="store_true", help="Emit JSON findings")
    ap.add_argument(
        "--fail-on-emdash",
        dest="fail_on_emdash",
        action="store_true",
        default=True,
        help="Exit 1 on em/en dash (default: true)",
    )
    ap.add_argument(
        "--no-fail-on-emdash",
        dest="fail_on_emdash",
        action="store_false",
        help="Report em/en dashes but do not fail",
    )
    ap.add_argument(
        "--fail-on-slop",
        dest="fail_on_slop",
        action="store_true",
        default=True,
        help="Exit 1 on slop phrases (default: true; list is tiny to limit FP)",
    )
    ap.add_argument(
        "--no-fail-on-slop",
        dest="fail_on_slop",
        action="store_false",
        help="Report slop but do not fail (useful while tuning the list)",
    )
    ap.add_argument(
        "--slop",
        action="append",
        default=None,
        help="Extra slop phrase (repeatable). Replaces default list if any --slop given.",
    )
    args = ap.parse_args()

    if not args.stdin and not args.paths:
        ap.error("provide paths and/or --stdin")

    slop = args.slop if args.slop is not None else list(DEFAULT_SLOP)
    findings: list[dict] = []

    if args.stdin:
        text = sys.stdin.read()
        findings.extend(scan_text(text, "<stdin>", slop))

    files = iter_files([Path(p) for p in args.paths])
    for f in files:
        findings.extend(scan_file(f, slop))

    dash_hits = [f for f in findings if f.get("kind") in ("emdash", "endash")]
    slop_hits = [f for f in findings if f.get("kind") == "slop"]
    other = [f for f in findings if f.get("kind") not in ("emdash", "endash", "slop")]

    if args.json:
        print(json.dumps({
            "findings": findings,
            "counts": {
                "emdash_endash": len(dash_hits),
                "slop": len(slop_hits),
                "other": len(other),
                "total": len(findings),
            },
            "fail_on_emdash": args.fail_on_emdash,
            "fail_on_slop": args.fail_on_slop,
        }, indent=2))
    else:
        if not findings:
            print("ok: no em/en dash or slop findings")
        else:
            for f in findings:
                loc = f"{f.get('source')}:{f.get('line')}"
                if f.get("kind") in ("emdash", "endash"):
                    print(f"[{f['kind']}] {loc} {f.get('char')} :: {f.get('snippet')}")
                elif f.get("kind") == "slop":
                    print(f"[slop] {loc} phrase={f.get('phrase')!r} :: {f.get('snippet')}")
                else:
                    print(f"[{f.get('kind')}] {loc} :: {f.get('snippet')}")
            print(
                f"summary: dashes={len(dash_hits)} slop={len(slop_hits)} "
                f"other={len(other)} total={len(findings)}"
            )

    should_fail = False
    if args.fail_on_emdash and dash_hits:
        should_fail = True
    if args.fail_on_slop and slop_hits:
        should_fail = True
    if other:
        should_fail = True
    raise SystemExit(1 if should_fail else 0)


if __name__ == "__main__":
    main()
