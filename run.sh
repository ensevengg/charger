#!/usr/bin/env bash
# Usage: ./run.sh <session-id>
# One Speedy Shopper run: records the live dashboard, runs the agent, cuts demo videos,
# then checks the answer with ./verify.py. Everything goes in runs/<id>/:
#   answer.md  final answer        agent.json  raw agent output     verify.txt  check result
#   window.txt start/end times     AGENTS.md   agent instructions used
#   full.mp4   whole run           demo.mp4    queue waits cut out
# Per-reply TPS for all runs is in logs/tps.jsonl.
set -euo pipefail; cd "$(dirname "$0")"; id=${1:?session id}
# One run at a time: replies are matched to runs by time, and the dashboard shows one run.
mkdir -p logs; exec 9>logs/.run.lock; flock -n 9 || { echo "another run is in progress"; exit 1; }
IMAGE=${OPENCLAW_IMAGE:-ghcr.io/openclaw/openclaw:2026.11.6-browser}
d=runs/$id; mkdir -p "$d"
cp state/workspace/AGENTS.md "$d/AGENTS.md" 2>/dev/null || true
since=$(date +%s.%N)

docker run -d --rm --name "rec-$id" --network charger_default -u 1000:1000 \
  -v "$PWD/recorder:/rec:ro" -v "$PWD/$d:/out" --entrypoint node "$IMAGE" \
  /rec/record.mjs "http://tpsproxy:8080/?rec=1&since=$since&run=$id" /out >/dev/null
for _ in $(seq 1 60); do [ -f "$d/start.txt" ] && break; sleep 0.5; done

./oc agent --agent main --session-id "$id" --json --timeout 1700 \
  -m "Santa's Speedy Shopper: find 5 Christmas gifts that are real products currently sold on real retail websites, with direct product links." \
  > "$d/agent.json" 2>&1 || true

echo "$since $(date +%s.%N)" > "$d/window.txt"
docker stop -t 60 "rec-$id" >/dev/null || true
python3 - "$d" <<'PY'
import json,sys
raw=open(sys.argv[1]+"/agent.json").read(); d=json.loads(raw[raw.find("{"):]); r=d["result"]
print("status:", d.get("status"), "duration_s:", round(r["meta"].get("durationMs",0)/1000))
open(sys.argv[1]+"/answer.md","w").write(r["payloads"][0]["text"])
PY
recorder/cut.py "$d" "$since" || echo "video cut failed"
./verify.py "$id" | tee "$d/verify.txt"
