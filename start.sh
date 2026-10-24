#!/usr/bin/env bash
# Build news.json from live feeds, then serve the site at http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -q -r requirements.txt
python scripts/build_news.py --out site/news.json
python -m http.server 8000 -d site
