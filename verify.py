#!/usr/bin/env python3
"""Check a Speedy Shopper run's final answer against what its tools actually returned.

Usage: ./verify.py <session-id> [final-answer.md]     (default: logs/runs/<id>.md)

For every "## Gift N" section it checks:
  url      the URL was fetched successfully with web_fetch during the run (HTTP 200, no bot wall)
  source   the URL appeared in an earlier search/fetch result (not built from memory)
  price    every $ amount in the section's Price line occurs in that fetched page
  excerpt  every "> " quoted line occurs verbatim in that fetched page
Exit code 0 only if there are 5 gifts and all checks pass.
"""
import json, os, re, subprocess, sys, tempfile

BOT = re.compile(r"robot or human|captcha|access denied|are you a human|unusual traffic", re.I)


def export(session_id):
    """Export the session trajectory from the container and return its events."""
    name = f"verify-{session_id}"
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([f"{here}/oc", "sessions", "export-trajectory",
                    "--session-key", f"agent:main:explicit:{session_id}", "--output", name],
                   check=True, capture_output=True, cwd=here)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["docker", "cp", f"openclaw:/app/.openclaw/trajectory-exports/{name}/events.jsonl", tmp],
                       check=True, capture_output=True)
        subprocess.run(["docker", "exec", "openclaw", "rm", "-rf", f"/app/.openclaw/trajectory-exports/{name}"],
                       capture_output=True)
        with open(os.path.join(tmp, "events.jsonl")) as f:
            return [json.loads(l) for l in f if l.strip()]


def db_messages(session_id):
    """The session's transcript messages, read from the agent's session database. Unlike the
    trajectory export, nothing is redacted (the export can replace a long reply or page with
    "[Malformed diagnostic JSON redacted]"). None if the session isn't there."""
    import shutil, sqlite3
    from compression import zstd
    here = os.path.dirname(os.path.abspath(__file__))
    for state in ("state-patched", "state"):
        db = f"{here}/{state}/agents/main/agent/openclaw-agent.sqlite"
        if not os.path.exists(db):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            for suffix in ("", "-wal", "-shm"):
                if os.path.exists(db + suffix):
                    shutil.copy(db + suffix, f"{tmp}/a.sqlite{suffix}")
            c = sqlite3.connect(f"{tmp}/a.sqlite")
            row = c.execute("select value_json from session_entry_snapshots where session_key=? and field='systemPromptReport'",
                            (f"agent:main:explicit:{session_id}",)).fetchone()
            if not row:
                continue
            sess = json.loads(row[0])["sessionId"]
            out = []
            for raw, z in c.execute("select event_json, event_zstd from transcript_events where session_id=? order by seq", (sess,)):
                m = json.loads(raw or zstd.decompress(z).decode()).get("message")
                if m:
                    out.append(m)
            return out
    return None


def to_events(msgs):
    """Shape raw transcript messages like trajectory-export events."""
    ev = []
    for m in msgs:
        if m.get("role") == "assistant":
            ev.append({"source": "transcript", "type": "assistant.message", "data": {"message": m}})
            for c in m.get("content", []):
                if c.get("type") == "toolCall":
                    ev.append({"source": "transcript", "type": "tool.call",
                               "data": {"toolCallId": c.get("id"), "name": c.get("name"), "arguments": c.get("arguments")}})
        elif m.get("role") == "toolResult":
            ev.append({"source": "transcript", "type": "tool.result", "data": {"message": m}})
    return ev


def tool_io(events):
    """Return [(name, args, result_text)] in the order results arrived."""
    calls, out = {}, []
    for e in events:
        if e.get("source") != "transcript":
            continue
        d = e.get("data", {})
        if e["type"] == "tool.call":
            calls[d["toolCallId"]] = (d.get("name"), d.get("arguments") or {})
        elif e["type"] == "tool.result":
            m = d.get("message", {})
            text = "".join(c.get("text", "") for c in m.get("content", []))
            name, args = calls.get(m.get("toolCallId"), (m.get("toolName"), {}))
            out.append((name, args, text))
    return out


def fetched_pages(io):
    """url -> text of all successful, non-bot-walled web_fetch results for it."""
    pages = {}
    for name, args, text in io:
        if name != "web_fetch":
            continue
        try:
            d = json.loads(text)
        except ValueError:
            continue
        body = (d.get("text") or "") + "\n" + (d.get("title") or "")  # names may come from the title field
        if d.get("status") == 200 and body and not BOT.search(body[:3000]):
            for u in {args.get("url"), d.get("finalUrl"), d.get("url")} - {None}:
                pages[u] = pages.get(u, "") + "\n" + body  # a page may be fetched more than once
    return pages


def search_hits(io):
    """url -> result title (wrapper lines removed) for every web_search result."""
    hits = {}
    for name, _, text in io:
        if name != "web_search":
            continue
        try:
            results = json.loads(text).get("results", [])
        except ValueError:
            continue
        for r in results:
            title = re.sub(r"<<<[^>]*>>>|Source: Web Search|^\s*---\s*$", "", r.get("title") or "", flags=re.M)
            hits.setdefault(r.get("url"), title.strip())
    return hits


def norm(s):
    # The trajectory export redacts parts of URL query strings, so compare URLs without them.
    s = re.sub(r"(https?://[^\s?)]+)\?[^\s)]*", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    sid = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    msgs = db_messages(sid)
    events = to_events(msgs) if msgs else export(sid)
    path = sys.argv[2] if len(sys.argv) > 2 else f"{here}/logs/runs/{sid}.md"
    msgs = [e["data"]["message"] for e in events
            if e.get("source") == "transcript" and e["type"] == "assistant.message"]
    if os.path.exists(path):
        final = open(path).read()
    else:  # web UI runs: take the last assistant reply from the transcript
        final = "".join(c.get("text", "") for c in (msgs[-1]["content"] if msgs else []) if c.get("type") == "text")
        open(path, "w").write(final)
    # The speed patch's headline: mean over model calls of completion tokens / server decode time.
    rates = [g["outputTokens"] / (g["completionMs"] / 1000) for g in (m.get("serverGeneration") for m in msgs)
             if g and g.get("completionMs")]
    if rates:
        print(f"patch readout: {sum(rates) / len(rates):,.0f} tok/s mean over {len(rates)} calls "
              f"({', '.join(f'{r:,.0f}' for r in rates)})")
    io = tool_io(events)
    pages = fetched_pages(io)

    sections = re.split(r"(?m)^## Gift \d+\s*$", final)[1:]
    ok_all = len(sections) == 5
    print(f"{len(sections)} gift sections found" + ("" if ok_all else "  ✗ expected 5"))

    hits, seen = search_hits(io), set()
    for i, sec in enumerate(sections, 1):
        sec = sec.split("\n| Name |")[0]  # drop trailing summary table
        if not any(l.startswith(">") or l.lower().startswith("price:") for l in sec.splitlines()):
            # 2-reply format (speedrun2.md): name and URL must match one live search result exactly.
            url = (re.findall(r"https?://[^\s)\]|>]+", sec) or [None])[0]
            name = next((l[5:].strip() for l in sec.splitlines() if l.lower().startswith("name:")), "")
            checks = {"url": bool(url) and url.startswith("https://www.walmart.com/ip/") and url in hits,
                      "name": bool(name) and norm(name) == norm(hits.get(url, "")),
                      "unique": url not in seen}
            seen.add(url)
            ok_all &= all(checks.values())
            print(f"Gift {i}: " + "  ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()) + f"  {url}")
            if not checks["name"]:
                print(f"    name {name[:90]!r} vs search title {hits.get(url, '')[:90]!r}")
            continue
        urls = re.findall(r"https?://[^\s)\]|>]+", sec)
        url = urls[0] if urls else None
        page = pages.get(url, "")
        npage = norm(page)
        idx = next((k for k, (n, a, t) in enumerate(io) if n == "web_fetch" and a.get("url") == url), len(io))
        sourced = bool(url) and any(url in t for _, _, t in io[:idx])
        price_line = next((l for l in sec.splitlines() if l.lower().startswith("price:")), "")
        prices = re.findall(r"\$\s?\d[\d,]*(?:\.\d\d)?", price_line)
        price_ok = bool(prices) and all(p in page for p in prices)
        quotes = [re.sub(r"^>\s?", "", l) for l in sec.splitlines() if l.startswith(">")]
        quotes = [q for q in quotes if q.strip()]
        bad = [q for q in quotes if norm(q) not in npage]
        checks = {"url": bool(page), "source": sourced, "price": price_ok, "excerpt": bool(quotes) and not bad}
        ok = all(checks.values())
        ok_all &= ok
        marks = "  ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items())
        print(f"Gift {i}: {marks}  ({len(quotes)} quoted lines, {len(bad)} not verbatim)  {url}")
        for q in bad[:3]:
            print(f"    not in page: {q[:100]!r}")

    print("PASS" if ok_all else "FAIL")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
