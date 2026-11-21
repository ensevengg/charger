"""Pass-through proxy to api.cerebras.ai that measures per-reply TPS and serves a live dashboard.

TPS = (output tokens - 1) / (last token time - first token time), same formula as the bounty.

Routes:
  /v1/...     forwarded to api.cerebras.ai (OpenClaw's baseUrl points here)
  /           dashboard (index.html)
  /events     server-sent events: history, then live start/first/delta/done events
"""
import http.client, http.server, itertools, json, os, queue, threading, time

UP = "api.cerebras.ai"
LOG = os.environ.get("TPS_LOG", "/logs/tps.jsonl")
HERE = os.path.dirname(os.path.abspath(__file__))
FLUSH_S = 0.05  # batch streamed text to the dashboard every 50 ms

def _next_id_start():
    try:
        with open(LOG) as f:
            return max((json.loads(l).get("id") or 0) for l in f if l.strip()) + 1
    except (FileNotFoundError, ValueError):
        return 1


_clients, _lock, _ids = set(), threading.Lock(), itertools.count(_next_id_start())


def emit(ev):
    data = json.dumps(ev)
    with _lock:
        for q in list(_clients):
            q.put(data)


def history(limit=300):
    try:
        with open(LOG) as f:
            return [json.loads(l) for l in f.readlines()[-limit:] if l.strip()]
    except FileNotFoundError:
        return []


class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    # ---------- dashboard ----------
    def _static(self):
        with open(os.path.join(HERE, "index.html"), "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        q = queue.Queue()
        with _lock:
            _clients.add(q)
        try:
            self.wfile.write(f"data: {json.dumps({'type': 'history', 'items': history()})}\n\n".encode())
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=15)
                    self.wfile.write(f"data: {msg}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _lock:
                _clients.discard(q)

    # ---------- proxy ----------
    def _fwd(self, method):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        hdrs = {k: v for k, v in self.headers.items()
                if k.lower() not in ("host", "content-length", "accept-encoding", "connection")}
        hdrs["Accept-Encoding"] = "identity"
        is_chat = method == "POST" and self.path.endswith("/chat/completions")
        rid = next(_ids)
        sent = {}
        if is_chat:
            try:
                req = json.loads(body)
                sent = {k: req[k] for k in ("reasoning_effort", "temperature", "top_p", "max_completion_tokens", "max_tokens") if k in req}
            except ValueError:
                pass
        t0 = time.time()
        if is_chat:
            emit({"type": "start", "id": rid, "t": t0})
        c = http.client.HTTPSConnection(UP, timeout=600)
        c.request(method, self.path, body=body, headers=hdrs)
        r = c.getresponse()
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ("transfer-encoding", "content-length", "connection", "content-encoding"):
                self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()

        first = last = None
        usage = tinfo = model = None
        chunks = 0
        buf = {"reasoning": "", "content": "", "tool": ""}
        last_flush = time.time()

        def flush():
            nonlocal last_flush
            parts = {k: v for k, v in buf.items() if v}
            if parts:
                emit({"type": "delta", "id": rid, "chunks": chunks, "parts": parts, "t": time.time()})
                for k in buf:
                    buf[k] = ""
            last_flush = time.time()

        while True:
            line = r.readline()
            if not line:
                break
            self.wfile.write(line)
            self.wfile.flush()
            if not (is_chat and line.startswith(b"data: {")):
                continue
            try:
                d = json.loads(line[6:])
            except Exception:
                continue
            model = d.get("model", model)
            if d.get("usage"):
                usage, tinfo = d["usage"], d.get("time_info")
            for ch in d.get("choices", []):
                dl = ch.get("delta", {})
                got = False
                if dl.get("reasoning"):
                    buf["reasoning"] += dl["reasoning"]; got = True
                if dl.get("content"):
                    buf["content"] += dl["content"]; got = True
                for tc in dl.get("tool_calls") or []:
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        buf["tool"] += f"\n→ {fn['name']}("
                    if fn.get("arguments"):
                        buf["tool"] += fn["arguments"]
                    got = True
                if got:
                    now = time.time()
                    if first is None:
                        first = now
                        emit({"type": "first", "id": rid, "ttft_s": round(now - t0, 2), "t": now})
                    last = now
                    chunks += 1
            if time.time() - last_flush >= FLUSH_S:
                flush()
        if is_chat:
            flush()

        if is_chat and usage and first and last > first:
            n = usage["completion_tokens"]
            rec = {"id": rid, "t": time.strftime("%H:%M:%S"), "ts": t0, "model": model, "out": n,
                   "reasoning": usage.get("completion_tokens_details", {}).get("reasoning_tokens"),
                   "tps": round((n - 1) / (last - first), 1), "decode_s": round(last - first, 2),
                   "ttft_s": round(first - t0, 1), "queue_s": round((tinfo or {}).get("queue_time", 0), 1), "sent": sent}
            print(json.dumps(rec), flush=True)
            with open(LOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
            emit({"type": "done", "rec": rec})
        elif is_chat:
            emit({"type": "fail", "id": rid, "status": r.status})

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._static()
        if path == "/events":
            return self._events()
        self._fwd("GET")

    def do_POST(self):
        self._fwd("POST")


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True


Server(("0.0.0.0", 8080), H).serve_forever()
