"""Pass-through proxy to api.cerebras.ai that logs per-reply TPS.
TPS = (output tokens - 1) / (last token time - first token time), same as the bounty."""
import http.client, http.server, json, time, sys, os

UP = "api.cerebras.ai"
LOG = os.environ.get("TPS_LOG", "/logs/tps.jsonl")

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def log_message(self, *a): pass

    def _fwd(self, method):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        hdrs = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length", "accept-encoding", "connection")}
        hdrs["Accept-Encoding"] = "identity"
        c = http.client.HTTPSConnection(UP, timeout=600)
        t0 = time.time()
        c.request(method, self.path, body=body, headers=hdrs)
        r = c.getresponse()
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ("transfer-encoding", "content-length", "connection", "content-encoding"):
                self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()
        first = last = None; usage = tinfo = None; model = None
        while True:
            line = r.readline()
            if not line: break
            self.wfile.write(line); self.wfile.flush()
            if line.startswith(b"data: {"):
                try: d = json.loads(line[6:])
                except Exception: continue
                model = d.get("model", model)
                if d.get("usage"): usage, tinfo = d["usage"], d.get("time_info")
                for ch in d.get("choices", []):
                    dl = ch.get("delta", {})
                    if dl.get("content") or dl.get("reasoning") or dl.get("tool_calls"):
                        now = time.time(); first = first or now; last = now
        if usage and first and last > first:
            n = usage["completion_tokens"]
            rec = {"t": time.strftime("%H:%M:%S"), "model": model, "out": n,
                   "reasoning": usage.get("completion_tokens_details", {}).get("reasoning_tokens"),
                   "tps": round((n - 1) / (last - first), 1), "decode_s": round(last - first, 2),
                   "ttft_s": round(first - t0, 1), "queue_s": round((tinfo or {}).get("queue_time", 0), 1)}
            print(json.dumps(rec), flush=True)
            with open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")

    def do_POST(self): self._fwd("POST")
    def do_GET(self): self._fwd("GET")

http.server.ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
