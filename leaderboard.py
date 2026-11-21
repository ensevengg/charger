#!/usr/bin/env python3
"""Rank all recorded runs by the TPS of their final answer. Writes logs/leaderboard.md."""
import glob, json, os

here = os.path.dirname(os.path.abspath(__file__))
recs = [json.loads(l) for l in open(f"{here}/logs/tps.jsonl") if l.strip()]
rows = []
for w in glob.glob(f"{here}/logs/runs/*.window"):
    rid = os.path.basename(w)[:-7]
    a, b = map(float, open(w).read().split())
    rr = [r for r in recs if a <= r.get("ts", 0) <= b]
    if not rr:
        continue
    v = f"{here}/logs/runs/{rid}.verify"
    verdict = open(v).read().strip().splitlines()[-1] if os.path.exists(v) else "?"
    final, best = rr[-1], max(rr, key=lambda r: r["tps"])
    vid = f"logs/videos/{rid}/demo.mp4"
    rows.append((final["tps"], rid, verdict, final["out"], final.get("reasoning"), best["tps"], len(rr),
                 vid if os.path.exists(f"{here}/{vid}") else "-"))
rows.sort(reverse=True)
out = ["| Final TPS | Run | Check | Final tokens | Reasoning | Best reply TPS | Replies | Video |",
       "|---:|---|---|---:|---:|---:|---:|---|"]
out += [f"| {t:,.0f} | {r} | {v} | {o:,} | {re} | {b:,.0f} | {n} | {vid} |" for t, r, v, o, re, b, n, vid in rows]
open(f"{here}/logs/leaderboard.md", "w").write("\n".join(out) + "\n")
print("\n".join(out[:12]))
