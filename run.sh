#!/usr/bin/env bash
# Usage: ./run.sh <session-id>
# One Speedy Shopper run: records the live dashboard, runs the agent, cuts demo videos,
# then checks the answer with ./verify.py. Outputs:
#   logs/runs/<id>.md            final answer
#   logs/videos/<id>/full.mp4    whole run;  demo.mp4  queue waits cut out
#   logs/tps.jsonl               per-reply TPS
set -euo pipefail; cd "$(dirname "$0")"; id=${1:?session id}
# One run at a time: replies are matched to runs by time, and the dashboard shows one run.
exec 9>logs/.run.lock; flock -n 9 || { echo "another run is in progress"; exit 1; }
IMAGE=${OPENCLAW_IMAGE:-ghcr.io/openclaw/openclaw:2026.11.6-browser}
mkdir -p logs/runs "logs/videos/$id"
since=$(date +%s.%N)

docker run -d --rm --name "rec-$id" --network charger_default -u 1000:1000 \
  -v "$PWD/recorder:/rec:ro" -v "$PWD/logs/videos/$id:/out" --entrypoint node "$IMAGE" \
  /rec/record.mjs "http://tpsproxy:8080/?rec=1&since=$since&run=$id" /out >/dev/null
for _ in $(seq 1 60); do [ -f "logs/videos/$id/start.txt" ] && break; sleep 0.5; done

./oc agent --agent main --session-id "$id" --json --timeout 1700 \
  -m "Santa's Speedy Shopper: find 5 Christmas gifts that are real products currently sold on real retail websites, with direct product links." \
  > "logs/runs/$id.json" 2>&1 || true

echo "$since $(date +%s.%N)" > "logs/runs/$id.window"
docker stop -t 60 "rec-$id" >/dev/null || true
python3 - "logs/runs/$id.json" <<'PY'
import json,sys
raw=open(sys.argv[1]).read(); d=json.loads(raw[raw.find("{"):]); r=d["result"]
print("status:", d.get("status"), "duration_s:", round(r["meta"].get("durationMs",0)/1000))
open(sys.argv[1].replace(".json",".md"),"w").write(r["payloads"][0]["text"])
PY
recorder/cut.py "logs/videos/$id" "$since" || echo "video cut failed"
./verify.py "$id" | tee "logs/runs/$id.verify"
