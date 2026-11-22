#!/usr/bin/env bash
# Usage: ./run-ui.sh <session-id>
# One Speed Bounty run on the patched OpenClaw: types the prompt into the web chat UI (where the
# speed patch shows its readout) and records the screen, then cuts the video and checks the answer.
# Everything goes in runs/<id>/: full.mp4, demo.mp4, final.png, readout.json, answer.md,
# verify.txt, window.txt, AGENTS.md (the agent instructions used).
set -euo pipefail; cd "$(dirname "$0")"; id=${1:?session id}
mkdir -p logs; exec 9>logs/.run.lock; flock -n 9 || { echo "another run is in progress"; exit 1; }
REC_IMAGE=${REC_IMAGE:-ghcr.io/openclaw/openclaw:2026.11.6-browser}   # has Playwright + Chromium
d=runs/$id; mkdir -p "$d"
cp state-patched/workspace/AGENTS.md "$d/AGENTS.md" 2>/dev/null || true
# Request rewrites the proxy applies (tpsproxy/proxy.py rewrite()), and the system prompt it swaps in.
if [ -f logs/rewrite.json ]; then
  cp logs/rewrite.json "$d/rewrite.json"
  sf=$(python3 -c 'import json;print(json.load(open("logs/rewrite.json")).get("system_file",""))' 2>/dev/null || true)
  [ -n "$sf" ] && cp "logs/$sf" "$d/" 2>/dev/null || true
fi
since=$(date +%s.%N)
OPENCLAW_GATEWAY_TOKEN=$(sed -n 's/^OPENCLAW_GATEWAY_TOKEN=//p' .env) \
docker run --rm --name "rec-$id" --network container:openclaw -u 1000:1000 -e OPENCLAW_GATEWAY_TOKEN \
  -v "$PWD/recorder:/rec:ro" -v "$PWD/$d:/out" --entrypoint node "$REC_IMAGE" \
  /rec/ui-run.mjs "$id" /out || echo "ui run failed"
echo "$since $(date +%s.%N)" > "$d/window.txt"
recorder/cut.py "$d" "$since" || echo "video cut failed"
./verify.py "$id" | tee "$d/verify.txt"
