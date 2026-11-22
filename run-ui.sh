#!/usr/bin/env bash
# Usage: ./run-ui.sh <session-id>
# One Speed Bounty run on the patched OpenClaw: types the prompt into the web chat UI (where the
# speed patch shows its readout) and records the screen, then cuts the video and checks the answer.
# Outputs: logs/videos/<id>/{full,demo}.mp4, final.png, readout.json; logs/runs/<id>.{md,verify}
set -euo pipefail; cd "$(dirname "$0")"; id=${1:?session id}
exec 9>logs/.run.lock; flock -n 9 || { echo "another run is in progress"; exit 1; }
REC_IMAGE=${REC_IMAGE:-ghcr.io/openclaw/openclaw:2026.11.6-browser}   # has Playwright + Chromium
mkdir -p logs/runs "logs/videos/$id"
since=$(date +%s.%N)
OPENCLAW_GATEWAY_TOKEN=$(sed -n 's/^OPENCLAW_GATEWAY_TOKEN=//p' .env) \
docker run --rm --name "rec-$id" --network container:openclaw -u 1000:1000 -e OPENCLAW_GATEWAY_TOKEN \
  -v "$PWD/recorder:/rec:ro" -v "$PWD/logs/videos/$id:/out" --entrypoint node "$REC_IMAGE" \
  /rec/ui-run.mjs "$id" /out || echo "ui run failed"
echo "$since $(date +%s.%N)" > "logs/runs/$id.window"
recorder/cut.py "logs/videos/$id" "$since" || echo "video cut failed"
./verify.py "$id" | tee "logs/runs/$id.verify"
