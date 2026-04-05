#!/usr/bin/env python3
"""
agent.py — Local pipeline agent server
Runs on your machine. Exposes HTTP endpoints so the web dashboard
can trigger main.py and stream live logs to your browser.

Run:  python agent.py
Port: 5050 (configurable via AGENT_PORT env var)

Security: Optionally set AGENT_SECRET in .env — the dashboard must
send this as the X-Agent-Secret header to trigger runs.
"""

import os
import sys
import subprocess
import threading
import time
import json
import queue
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

PORT        = int(os.getenv("AGENT_PORT", "5050"))
SECRET      = os.getenv("AGENT_SECRET", "")          # optional auth
PIPELINE_DIR = Path(__file__).parent
PYTHON       = sys.executable

# Global state
_run_lock    = threading.Lock()
_is_running  = False
_log_queues: list[queue.Queue] = []
_last_run    = None   # dict with summary info


def broadcast(line: str):
    """Send a log line to all connected SSE clients."""
    dead = []
    for q in _log_queues:
        try:
            q.put_nowait(line)
        except queue.Full:
            dead.append(q)
    for q in dead:
        try:
            _log_queues.remove(q)
        except ValueError:
            pass


def run_pipeline():
    """Run main.py as subprocess, stream output to all SSE clients."""
    global _is_running, _last_run

    with _run_lock:
        if _is_running:
            broadcast("data: [agent] Pipeline already running — skipped.\n\n")
            return
        _is_running = True

    start = time.time()
    broadcast("data: [agent] Starting pipeline...\n\n")

    try:
        proc = subprocess.Popen(
            [PYTHON, "main.py"],
            cwd=str(PIPELINE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in proc.stdout:
            line = line.rstrip()
            if line:
                broadcast(f"data: {line}\n\n")

        proc.wait()
        elapsed = int(time.time() - start)
        status = "completed" if proc.returncode == 0 else f"failed (exit {proc.returncode})"
        broadcast(f"data: [agent] Pipeline {status} in {elapsed}s.\n\n")
        broadcast("data: [agent] DONE\n\n")  # sentinel for frontend

        _last_run = {
            "status": status,
            "duration_seconds": elapsed,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        broadcast(f"data: [agent] ERROR: {e}\n\n")
        broadcast("data: [agent] DONE\n\n")
    finally:
        _is_running = False


class AgentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default access log noise

    def handle_error(self, *args):
        pass  # suppress BrokenPipeError noise in console

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Agent-Secret")

    def _check_secret(self) -> bool:
        if not SECRET:
            return True
        return self.headers.get("X-Agent-Secret", "") == SECRET

    def _send_json(self, code: int, data: dict):
        """Send a JSON response, silently ignoring broken pipe errors."""
        try:
            body = json.dumps(data).encode()
            self.send_response(code)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        try:
            self.send_response(204)
            self._cors()
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        path = urlparse(self.path).path

        # Health check
        if path == "/health":
            self._send_json(200, {
                "ok": True,
                "is_running": _is_running,
                "last_run": _last_run,
            })
            return

        # SSE log stream
        if path == "/logs":
            if not self._check_secret():
                self.send_response(401)
                self.end_headers()
                return

            q = queue.Queue(maxsize=500)
            _log_queues.append(q)

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            try:
                while True:
                    try:
                        line = q.get(timeout=20)
                        self.wfile.write(line.encode())
                        self.wfile.flush()
                        if "[agent] DONE" in line:
                            break
                    except queue.Empty:
                        # heartbeat to keep connection alive
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                try:
                    _log_queues.remove(q)
                except ValueError:
                    pass
            return

        try:
            self.send_response(404)
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        path = urlparse(self.path).path

        # Trigger pipeline run
        if path == "/run":
            if not self._check_secret():
                self._send_json(401, {"error": "unauthorized"})
                return

            if _is_running:
                self._send_json(409, {"error": "already_running"})
                return

            # Start pipeline in background thread
            t = threading.Thread(target=run_pipeline, daemon=True)
            t.start()

            self._send_json(200, {"ok": True, "message": "Pipeline started"})
            return

        try:
            self.send_response(404)
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    print(f"")
    print(f"  JobReach Local Agent")
    print(f"  ─────────────────────────────────")
    print(f"  Listening on  http://localhost:{PORT}")
    print(f"  Health check: http://localhost:{PORT}/health")
    print(f"  Trigger run:  POST http://localhost:{PORT}/run")
    print(f"  Live logs:    GET  http://localhost:{PORT}/logs  (SSE)")
    if SECRET:
        print(f"  Auth:         X-Agent-Secret header required")
    else:
        print(f"  Auth:         none (set AGENT_SECRET in .env to enable)")
    print(f"")
    print(f"  Keep this running while using the dashboard.")
    print(f"  Set AGENT_URL=http://localhost:{PORT} in dashboard settings.")
    print(f"")

    server = HTTPServer(("0.0.0.0", PORT), AgentHandler)
    # Suppress BrokenPipeError tracebacks from the server's error handler
    server.handle_error = lambda *args: None
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Agent stopped.")


if __name__ == "__main__":
    main()
