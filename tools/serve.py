"""Serve this repo locally for testing the apps (Android emulator: http://10.0.2.2:8765/v1/).

Uses HTTP/1.1 keep-alive: Python's default HTTP/1.0 server on Windows can reset the
connection before a phone has read the whole file.
Run from the repo root: python tools/serve.py
"""
import functools
import http.server
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), functools.partial(Handler, directory=str(ROOT)))
    print("Serving", ROOT, "on port 8765")
    server.serve_forever()
