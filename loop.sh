#!/usr/bin/env bash
# Usage: ./loop.sh [count]   — back-to-back recorded runs; updates logs/leaderboard.md after each.
set -uo pipefail; cd "$(dirname "$0")"
for i in $(seq 1 "${1:-10}"); do
  id="r$(date +%m%d-%H%M%S)"
  echo "=== $id ($i/${1:-10})"
  ./run.sh "$id" 2>&1 | grep -E "^(status|demo.mp4|PASS|FAIL|video)" || true
  ./leaderboard.py | sed -n 3,5p
done
