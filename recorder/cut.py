#!/usr/bin/env python3
"""Make demo videos from a run recording.

Usage: recorder/cut.py <video-dir> <run-start-ts>
Writes <video-dir>/full.mp4 (everything) and <video-dir>/demo.mp4, which keeps only
the streaming parts of each reply (queue waits cut) plus a few seconds at the end.
"""
import json, os, subprocess, sys

vdir, since = sys.argv[1], float(sys.argv[2])
here = os.path.dirname(os.path.abspath(__file__))
t0 = float(open(f"{vdir}/start.txt").read())
recs = [json.loads(l) for l in open(f"{here}/../logs/tps.jsonl") if l.strip()]
recs = [r for r in recs if r.get("ts", 0) >= since]

def run(*a):
    subprocess.run(a, check=True, capture_output=True)

run("ffmpeg", "-y", "-i", f"{vdir}/full.webm", "-c:v", "libx264", "-preset", "veryfast",
    "-crf", "20", "-pix_fmt", "yuv420p", f"{vdir}/full.mp4")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            f"{vdir}/full.mp4"], capture_output=True, text=True).stdout.strip())

# keep 1.5 s before first token to 2.5 s after the last token of each reply
segs = []
for r in recs:
    first = r["ts"] + r["ttft_s"] - t0
    segs.append([max(0, first - 1.5), min(dur, first + r["decode_s"] + 2.5)])
if segs:
    segs[-1][1] = dur  # keep the ending (final answer + table) in full
segs.sort()
merged = []
for a, b in segs:
    if merged and a <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], b)
    else:
        merged.append([a, b])
if not merged:
    sys.exit("no replies found for this run")
sel = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in merged)
run("ffmpeg", "-y", "-i", f"{vdir}/full.mp4", "-vf", f"select='{sel}',setpts=N/FRAME_RATE/TB",
    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", f"{vdir}/demo.mp4")
os.remove(f"{vdir}/full.webm")
print(f"demo.mp4: {sum(b - a for a, b in merged):.0f}s from {dur:.0f}s recording")
