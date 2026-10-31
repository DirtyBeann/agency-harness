#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$ROOT/.opencode/skills"
mkdir -p "$DEST"
for name in agency-advance agency-replay; do
  rm -rf "$DEST/$name"
  cp -R "$ROOT/skills/$name" "$DEST/$name"
  echo "Installed $DEST/$name"
done
