#!/usr/bin/env bash
# Usage: ./run.sh <session-id>   — one Speedy Shopper run; per-reply TPS lands in logs/tps.jsonl
set -euo pipefail; cd "$(dirname "$0")"; id=${1:?session id}; mkdir -p logs/runs
./oc agent --agent main --session-id "$id" --json --timeout 1700 \
  -m "Santa's Speedy Shopper: find 5 Christmas gifts that are real products currently sold on real retail websites, with direct product links." \
  > "logs/runs/$id.json" 2>&1 || true
python3 - "logs/runs/$id.json" <<'PY'
import json,sys
raw=open(sys.argv[1]).read(); d=json.loads(raw[raw.find("{"):]); r=d["result"]
print("status:", d.get("status"), "duration_s:", round(r["meta"].get("durationMs",0)/1000))
open(sys.argv[1].replace(".json",".md"),"w").write(r["payloads"][0]["text"])
PY
