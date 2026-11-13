#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
/usr/bin/python3 build.py
git add -A
git commit -q -m "${1:-update}" || echo "nothing to commit"
git push "https://x-access-token:$(gh auth token)@github.com/elkushi/boi.git" main:main
echo "→ https://elkushi.github.io/boi/"
