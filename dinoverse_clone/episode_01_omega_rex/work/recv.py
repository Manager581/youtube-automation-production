#!/usr/bin/env python3
"""Tiny localhost receiver: POST /<name>.png with raw image bytes -> saved to stills/<name>.png.
Bypasses Chrome's download block. CORS-open so the ChatGPT page can POST to it."""
import http.server, socketserver, os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stills")
OUT = os.path.abspath(OUT)
PORT = 8765

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()
    def do_POST(self):
        name = os.path.basename(self.path.lstrip("/")) or "unnamed.bin"
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(data)
        sys.stderr.write(f"SAVED {name} {len(data)} bytes\n"); sys.stderr.flush()
        self.send_response(200); self._cors(); self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *a): pass

os.makedirs(OUT, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    sys.stderr.write(f"recv listening on {PORT} -> {OUT}\n"); sys.stderr.flush()
    httpd.serve_forever()
