#!/usr/bin/env python3
"""Tiny CORS-enabled static server for the stills/ folder so the Grok page can
fetch a still by URL and inject it into the upload (bypasses native picker)."""
import http.server, socketserver, os
DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stills"))
PORT = 8777

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=DIR, **k)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    print(f"serving {DIR} on http://127.0.0.1:{PORT}", flush=True)
    httpd.serve_forever()
