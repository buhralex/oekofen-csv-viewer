#!/usr/bin/env python3
"""
OekoFEN CSV Viewer — local development server with CORS proxy and optional
scheduled auto-fetch of daily logs.

Replaces: python -m http.server 8080

The OekoFEN heater does not return Access-Control-Allow-Origin headers,
so direct browser fetch() is blocked by CORS. This server proxies requests
to the heater server-side (where CORS does not apply) and returns the bytes
to the browser with Access-Control-Allow-Origin: * set.

Usage:
    python server.py
    python server.py --schedule 60   # auto-fetch log_today every 60 minutes
                                     # (requires settings.json with heater credentials)

settings.json format (same directory as server.py):
    {"ip": "10.10.30.3", "port": "4321", "password": "YOUR_PASSWORD"}
"""

import argparse
import datetime
import http.server
import json
import time
import urllib.error
import urllib.request
import urllib.parse
import webbrowser
import threading
import os

HOST = '127.0.0.1'
PORT = 8080
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(SCRIPT_DIR, 'history')


def load_schedule_settings():
    """Load heater connection settings from settings.json (same directory as server.py).
    Expected JSON: {"ip": "10.10.30.3", "port": "4321", "password": "ctT9"}
    Returns dict (empty dict if file missing or invalid).
    """
    path = os.path.join(SCRIPT_DIR, 'settings.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as exc:
        print(f'[schedule] Could not load settings.json: {exc}')
        return {}


def fetch_and_store_today(settings):
    """Fetch log_today from heater and save to ./history/YYYYMMDD.csv.
    settings: dict with keys 'ip', 'port', 'password'.
    Returns True on success, False on any error.
    """
    ip       = settings.get('ip', '')
    port     = settings.get('port', '4321')
    password = settings.get('password', '')
    if not ip or not password:
        print('[schedule] Skipping fetch — ip or password not configured in settings.json')
        return False
    date_str = datetime.date.today().strftime('%Y%m%d')
    url = f'http://{ip}:{port}/{password}/log_today'
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read()
        os.makedirs(HISTORY_DIR, exist_ok=True)
        path = os.path.join(HISTORY_DIR, f'{date_str}.csv')
        with open(path, 'wb') as f:
            f.write(data)
        print(f'[schedule] Stored {date_str}.csv ({len(data)} bytes)')
        return True
    except Exception as exc:
        print(f'[schedule] Fetch failed: {exc}')
        return False


def run_schedule(interval_minutes, settings):
    """Background thread: fetch and store log_today every interval_minutes minutes."""
    interval_secs = interval_minutes * 60
    print(f'[schedule] Auto-fetch every {interval_minutes} min — first fetch in 5 seconds')
    time.sleep(5)  # brief delay so server socket is bound before first fetch
    while True:
        fetch_and_store_today(settings)
        time.sleep(interval_secs)


class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # Block direct access to server-side files (covers curl path-normalization:
        # "curl /history/../server.py" sends GET /server.py — bypassing /history/ check).
        if parsed.path.lower().endswith(('.py', '.json', '.sh', '.bat')):
            self.send_error(404, 'Not found')
            return

        # Route: GET /history — list stored day files as JSON array of date strings
        if parsed.path == '/history':
            try:
                os.makedirs(HISTORY_DIR, exist_ok=True)
                files = [
                    f[:-4]  # strip .csv suffix → YYYYMMDD
                    for f in sorted(os.listdir(HISTORY_DIR))
                    if f.endswith('.csv') and len(f) == 12  # YYYYMMDD.csv = 12 chars
                ]
                body = json.dumps(files).encode('utf-8')
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                self.send_error(500, f'History list error: {exc}')
            return

        # Route: GET /history/YYYYMMDD.csv — serve a specific stored day.
        # Any /history/* request that is not an exact *.csv name is rejected with 404
        # to prevent path traversal (e.g. /history/../server.py) from falling through
        # to SimpleHTTPRequestHandler which would normalize the path and serve the file.
        if parsed.path.startswith('/history/'):
            if not parsed.path.endswith('.csv'):
                self.send_error(404, 'Not found')
                return
            filename = os.path.basename(parsed.path)  # YYYYMMDD.csv
            # Security: basename strips path traversal attempts; only serve from HISTORY_DIR
            filepath = os.path.join(HISTORY_DIR, filename)
            if not os.path.isfile(filepath):
                self.send_error(404, f'Not found: {filename}')
                return
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'text/plain; charset=windows-1252')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:
                self.send_error(500, f'History serve error: {exc}')
            return

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
            except urllib.error.HTTPError as exc:
                # Pass through the heater's actual status code so the browser can handle it correctly.
                self.send_error(exc.code, f'Proxy error: {exc}')
            except Exception as exc:
                self.send_error(502, f'Proxy error: {exc}')
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # Suppress per-request logs to keep terminal output clean
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OekoFEN CSV Viewer server')
    parser.add_argument(
        '--schedule', type=int, metavar='MINUTES', default=0,
        help='Auto-fetch log_today from heater every MINUTES minutes (requires settings.json)'
    )
    args = parser.parse_args()

    if args.schedule:
        sched_settings = load_schedule_settings()
        if not sched_settings.get('ip'):
            print('[schedule] ERROR: --schedule requires settings.json with {ip, port, password}')
            print('[schedule] Create settings.json in the same directory as server.py:')
            print('  {"ip": "10.10.30.3", "port": "4321", "password": "YOUR_PASSWORD"}')
        else:
            t = threading.Thread(target=run_schedule, args=(args.schedule, sched_settings), daemon=True)
            t.start()

    server = http.server.HTTPServer((HOST, PORT), Handler)
    url = f'http://localhost:{PORT}'
    print(f'OekoFEN Viewer running at {url} \u2014 Press Ctrl+C to stop')
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
