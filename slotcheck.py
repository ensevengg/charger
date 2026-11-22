#!/usr/bin/env python3
"""Check each speed-run search query the way the agent uses it, with no model tokens:
web_search -> first walmart.com/ip result -> web_fetch -> usable (title, `Current price is`, not sold out)?
Calls OpenClaw's tools directly through the gateway's /tools/invoke endpoint.
Usage: ./slotcheck.py [reps] [query ...]     (default: every query in speedrun.md, 3 reps)"""
import json, os, re, sys, urllib.request

here = os.path.dirname(os.path.abspath(__file__))
TOKEN = next(l.split("=", 1)[1].strip() for l in open(f"{here}/.env") if l.startswith("OPENCLAW_GATEWAY_TOKEN="))


def tool(name, args):
    req = urllib.request.Request("http://127.0.0.1:18789/tools/invoke", json.dumps({"tool": name, "args": args}).encode(),
                                 {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req, timeout=120))
    return json.loads(out["result"]["content"][0]["text"])


def check(q):
    urls = [r["url"] for r in tool("web_search", {"query": q}).get("results", [])
            if r["url"].startswith("https://www.walmart.com/ip/")]
    if not urls:
        return "no walmart result", None
    f = tool("web_fetch", {"url": urls[0], "maxChars": 12000})
    text = f.get("text") or ""
    if f.get("status") != 200:
        return f"HTTP {f.get('status')}", urls[0]
    if re.search(r"robot or human|captcha", text, re.I):
        return "bot wall", urls[0]
    if re.search(r"Sold out|Out of stock", text):
        return "SOLD OUT", urls[0]
    if "Current price is" not in text:
        return "no price", urls[0]
    return "ok", urls[0]


reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
queries = sys.argv[2:] or re.findall(r"`(site:walmart\.com/ip [^`]+)`", open(f"{here}/speedrun.md").read())
for q in queries:
    res = [check(q) for _ in range(reps)]
    good = sum(r == "ok" for r, _ in res)
    print(f"{good}/{reps}  {q}")
    for r, u in res:
        print(f"      {r:<16} {(u or '')[:110]}")
