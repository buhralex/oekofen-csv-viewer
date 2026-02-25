#!/usr/bin/env python3
"""
OekoFEN CSV Viewer — local development server with CORS proxy.

Replaces: python -m http.server 8080

The OekoFEN heater does not return Access-Control-Allow-Origin headers,
so direct browser fetch() is blocked by CORS. This server proxies requests
to the heater server-side (where CORS does not apply) and returns the bytes
to the browser with Access-Control-Allow-Origin: * set.

Usage:
    python server.py
"""

import http.server
import urllib.request
import urllib.parse
import webbrowser
import threading
import os

HOST = '127.0.0.1'
PORT = 8080
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/proxy':
            params = urllib.parse.parse_qs(parsed.query)
            target_url = params.get('url', [None])[0]
            if not target_url:
                self.send_error(400, 'Missing url parameter')
                return
            try:
                with urllib.request.urlopen(target_url, timeout=15) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'text/plain; charset=windows-1252')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:
                self.send_error(502, f'Proxy error: {exc}')
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # Suppress per-request logs to keep terminal output clean
        pass


if __name__ == '__main__':
    server = http.server.HTTPServer((HOST, PORT), Handler)
    url = f'http://localhost:{PORT}'
    print(f'OekoFEN Viewer running at {url} \u2014 Press Ctrl+C to stop')
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
