#!/usr/bin/env python3
"""Rank all recorded runs the way the official speed patch scores them: the mean, over every model
call in the run, of completion tokens / server decode time (our own timing for older records that
lack the server's). Writes logs/leaderboard.md."""
import glob, json, os, re

here = os.path.dirname(os.path.abspath(__file__))
recs = [json.loads(l) for l in open(f"{here}/logs/tps.jsonl") if l.strip()]
windows = {os.path.basename(w)[:-7]: tuple(map(float, open(w).read().split()))
           for w in glob.glob(f"{here}/logs/runs/*.window")}
rate = lambda r: r.get("stps") or r["tps"]
rows = []
for rid, (a, b) in windows.items():
    # replies are matched to runs by time, so overlapping runs can't be told apart
    overlap = any(o != rid and oa < b and a < ob for o, (oa, ob) in windows.items())
    rr = [r for r in recs if a <= r.get("ts", 0) <= b]
    if not rr:
        continue
    v = f"{here}/logs/runs/{rid}.verify"
    if not os.path.exists(v):
        continue  # unfinished or unchecked run
    text = open(v).read()
    verdict = text.strip().splitlines()[-1] if text.strip() else "?"
    if overlap:
        verdict += " (overlapped)"
    m = re.search(r"patch readout: ([\d,]+)", text)   # from the transcript, when the patch is in use
    mean = sum(map(rate, rr)) / len(rr)
    vid = f"logs/videos/{rid}/demo.mp4"
    rows.append((mean, rid, verdict, m.group(1) if m else "-", len(rr), rate(rr[-1]),
                 "server" if all("stps" in r for r in rr) else "client",
                 vid if os.path.exists(f"{here}/{vid}") else "-"))
rows.sort(reverse=True)
out = ["| Mean TPS | Run | Check | Patch readout | Calls | Final reply TPS | Timing | Video |",
       "|---:|---|---|---:|---:|---:|---|---|"]
out += [f"| {t:,.0f} | {r} | {v} | {p} | {n} | {f:,.0f} | {s} | {vid} |" for t, r, v, p, n, f, s, vid in rows]
open(f"{here}/logs/leaderboard.md", "w").write("\n".join(out) + "\n")
print("\n".join(out[:12]))
