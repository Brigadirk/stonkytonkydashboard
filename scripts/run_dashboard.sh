#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
if [ ! -f web/public/data/dashboard.json ]; then
  echo "Missing dashboard snapshot: web/public/data/dashboard.json" >&2
  echo "Restore the versioned snapshot or rebuild from the retained research archive. See docs/REFRESH.md." >&2
  exit 1
fi
if [ ! -d web/node_modules ]; then
  npm ci --prefix web --no-fund --no-audit
fi
npm run build --prefix web
cd web
exec npm run preview -- "$@"
