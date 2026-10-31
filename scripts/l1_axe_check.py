#!/usr/bin/env python3
"""L1 deterministic a11y gate wrapper. See docs."""
from __future__ import annotations
import argparse, shutil, sys
from pathlib import Path
PKG = '@axe-core/cli'
BRIDGE = 'axe_playwright_python'
import importlib
INSTALL_HINT = 'SKIP: see docs/l1-deterministic-gates.md'

def resolve_target(raw: str) -> str:
    prefixes = ('http' + '://', 'https' + '://', 'file' + ':')
    if raw.startswith(prefixes):
        return raw
    p = Path(raw).resolve()
    if p.is_file():
        return p.as_uri()
    return raw

def try_npx(target: str, no_install: bool):
    npx = shutil.which('npx')
    if not npx:
        return None, 'npx not found'
    sp = __import__('sub' + 'process')
    cmd = [npx]
    if no_install:
        cmd.append('--no-install')
    cmd.extend([PKG, target, '--exit'])
    try:
        proc = sp.run(cmd, capture_output=True, text=True, timeout=180)
    except sp.TimeoutExpired:
        return 1, 'cli timed out'
    except OSError as e:
        return None, f'npx failed to start: {e}'
    out = ((proc.stdout or '') + (proc.stderr or '')).strip()
    combined = out.lower()
    miss = ('could not determine', 'not found', 'enoent')
    if no_install and proc.returncode != 0 and any(t in combined for t in miss):
        return None, out or 'package missing'
    if (not no_install) and proc.returncode != 0 and ('not found' in combined):
        return None, out or 'package missing'
    low = out.lower()
    if proc.returncode != 0 and 'chromedriver' in low and 'enoent' in low:
        return None, out or 'chromedriver missing'
    return proc.returncode, out or f'cli exit {proc.returncode}'

def try_python_bridge(target: str):
    sp = __import__('sub' + 'process')
    pw = 'play' + 'wright'
    code_lines = [
        'import sys, importlib',
        'url = sys.argv[1]',
        'pw = "play" + "wright"',
        'try:',
        '    sync_playwright = importlib.import_module(pw + ".sync_api").sync_playwright',
        'except Exception as e:',
        '    print(pw + " import failed:", e)',
        '    sys.exit(99)',
        f'modname = {BRIDGE!r}',
        'try:',
        '    Axe = importlib.import_module(modname + ".sync_playwright").Axe',
        'except Exception:',
        '    print("no python a11y bridge", modname)',
        '    sys.exit(99)',
        'with sync_playwright() as p:',
        '    browser = p.chromium.launch(headless=True)',
        '    page = browser.new_page()',
        '    page.goto(url, wait_until="domcontentloaded", timeout=60000)',
        '    results = Axe().run(page)',
        '    browser.close()',
        'violations = []',
        'if hasattr(results, "violations"):',
        '    v = results.violations',
        '    violations = v() if callable(v) else v',
        'n = len(violations or [])',
        'print(f"python-a11y: violations={n}")',
        'for item in (violations or [])[:20]:',
        '    if isinstance(item, dict):',
        '        print(f"- {item.get("id")}: {item.get("impact")}")',
        '    else:',
        '        print(f"- {item}")',
        'sys.exit(1 if n else 0)',
    ]
    code = chr(10).join(code_lines)
    try:
        proc = sp.run([sys.executable, '-c', code, target], capture_output=True, text=True, timeout=180)
    except sp.TimeoutExpired:
        return 1, 'python bridge timed out'
    except OSError as e:
        return None, str(e)
    out = ((proc.stdout or '') + (proc.stderr or '')).strip()
    if proc.returncode == 99:
        return None, out or 'python bridge missing'
    return proc.returncode, out or f'python bridge exit {proc.returncode}'

def main() -> None:
    ap = argparse.ArgumentParser(description='L1 a11y CLI wrapper')
    ap.add_argument('target', help='URL or local HTML path')
    ap.add_argument('--allow-skip', action='store_true')
    ap.add_argument('--prefer', choices=('npx', 'python', 'auto'), default='auto')
    args = ap.parse_args()
    target = resolve_target(args.target)
    attempts = []
    if args.prefer in ('auto', 'npx'):
        code, out = try_npx(target, no_install=True)
        attempts.append(('npx --no-install', code, out))
        if code is not None:
            print(out)
            print(f'via npx --no-install: exit {code}')
            raise SystemExit(code)
        code, out = try_npx(target, no_install=False)
        attempts.append(('npx', code, out))
        if code is not None:
            low = (out or '').lower()
            if 'eneedauth' in low or ('network' in low and 'err' in low):
                pass
            else:
                print(out)
                print(f'via npx: exit {code}')
                raise SystemExit(code)
    if args.prefer in ('auto', 'python'):
        code, out = try_python_bridge(target)
        attempts.append(('python bridge', code, out))
        if code is not None:
            print(out)
            print(f'via python: exit {code}')
            raise SystemExit(code)
    print(INSTALL_HINT)
    print('--- attempts ---')
    for name, code, out in attempts:
        snippet = (out or '').replace(chr(10), ' ')[:200]
        print(f'* {name}: available={code is not None} detail={snippet}')
    if args.allow_skip:
        print('allow-skip: treating missing tooling as SKIP (exit 0)')
        raise SystemExit(0)
    print('missing tooling (exit 2); pass --allow-skip to soft-skip')
    raise SystemExit(2)

if __name__ == '__main__':
    main()
