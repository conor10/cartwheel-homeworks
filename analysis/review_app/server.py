"""Run from the repository root: uv run python -m analysis.review_app.server."""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from observability.instrument import load_env
from analysis.helpers import langfuse_io, selection
from .state import Conflict, Workspace
from .traces import TraceStore
from .hw5 import HW5Review

ROOT = Path(__file__).resolve().parents[2]
UI = Path(__file__).parent / "ui"


def make_handler(store, workspace, offline_reason=""):
    hw5 = HW5Review(workspace.directory)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def local_request(self):
            if urlparse("http://" + self.headers.get("Host", "")).hostname not in ("localhost", "127.0.0.1"):
                self.send({"error": "Use the localhost review address"}, 403)
                return False
            return True

        def send(self, data, status=200, content_type="application/json"):
            body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.local_request():
                return
            try:
                path = urlparse(self.path)
                params = parse_qs(path.query)
                assets = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                          "/hw5.js": ("hw5.js", "text/javascript"),
                          "/style.css": ("style.css", "text/css")}
                if path.path in assets:
                    name, kind = assets[path.path]
                    return self.send((UI / name).read_bytes(), content_type=kind + "; charset=utf-8")
                if path.path == "/api/bootstrap":
                    return self.send({"traces": store.summaries(), "state": workspace.snapshot(),
                                      "source": "offline" if store.offline else "langfuse",
                                      "offline_reason": offline_reason, "spec": (ROOT / "SPEC.md").read_text()})
                if path.path == "/api/state":
                    return self.send(workspace.snapshot())
                if path.path == "/api/hw5":
                    return self.send(hw5.snapshot())
                if path.path == "/api/session":
                    return self.send(store.session(params.get("trace_id", [""])[0]))
                if path.path == "/api/map":
                    from .sampling import graph
                    return self.send(graph(store))
                if path.path == "/api/search":
                    query = params.get("q", [""])[0].strip()
                    if not query:
                        return self.send([])
                    bow = selection._bow(query.lower())
                    ranked = [(selection._cosine(bow, selection._bow(t["text"].lower())), t["id"])
                              for t in store.normalized()]
                    return self.send([{"trace_id": tid, "similarity": score} for score, tid in
                                      sorted(ranked, reverse=True)[:50] if score > 0])
                self.send({"error": "Not found"}, 404)
            except ValueError as exc:
                self.send({"error": str(exc)}, 400)
            except Exception as exc:
                self.send({"error": f"Live trace request failed ({type(exc).__name__}). Check Langfuse and retry; no offline data was substituted."}, 502)

        def do_POST(self):
            if not self.local_request():
                return
            # This is a local single-reviewer app. Reject cross-origin browser writes.
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + self.headers.get("Host", ""):
                return self.send({"error": "Cross-origin writes are not allowed"}, 403)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000 or not self.headers.get("Content-Type", "").startswith("application/json"):
                    raise ValueError("Expected a JSON request (maximum 2 MB)")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                path = urlparse(self.path).path
                if not path.startswith("/api/"):
                    return self.send({"error": "Not found"}, 404)
                if path == "/api/hw5-label":
                    return self.send(hw5.save(body))
                if path == "/api/hw5-disagreement":
                    return self.send(hw5.save_disagreement(body))
                result = workspace.mutate(path.removeprefix("/api/"), body, store)
                self.send(result)
            except Conflict as exc:
                self.send({"error": str(exc)}, 409)
            except (ValueError, KeyError, TypeError) as exc:
                self.send({"error": str(exc)}, 400)
            except Exception as exc:
                self.send({"error": f"Save interrupted ({type(exc).__name__}). Reload state and retry sync; local pending changes may have been retained."}, 500)
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8022)
    parser.add_argument("--state-dir", type=Path, default=ROOT / "analysis/state")
    parser.add_argument("--scenarios", type=Path, default=ROOT / "scenarios/support_scenarios.jsonl")
    parser.add_argument("--offline-export", type=Path)
    parser.add_argument("--offline-reason", default="")
    args = parser.parse_args()
    if args.offline_export and not args.offline_reason.strip():
        parser.error("Offline review requires --offline-reason; record it in interface_comparison.md too.")
    load_env()
    client = None if args.offline_export else langfuse_io._client()
    store = TraceStore(client, args.scenarios, os.getenv("LANGFUSE_HOST", "http://localhost:3000"), args.offline_export)
    workspace = Workspace(args.state_dir, client)
    server = None
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(store, workspace, args.offline_reason))
        print(f"Cartwheel review: http://localhost:{args.port} ({'offline, local only' if args.offline_export else 'live Langfuse'})", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if server:
            server.server_close()
        if client:
            client.shutdown()


if __name__ == "__main__":
    main()
