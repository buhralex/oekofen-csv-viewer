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
import re
import sqlite3
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
STATS_DB_PATH = os.path.join(SCRIPT_DIR, 'stats.db')


def open_stats_db():
    """Open (or create) stats.db and ensure the daily_stats table exists.
    Opens a fresh connection each call for thread-safety.
    Returns the sqlite3 connection.
    """
    conn = sqlite3.connect(STATS_DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            starts INTEGER,
            runtime_minutes REAL,
            pellet_kg REAL,
            avg_outdoor_temp REAL,
            flow_return_delta REAL,
            degree_day_consumption REAL,
            row_count INTEGER,
            hours_covered REAL,
            is_partial INTEGER,
            computed_at INTEGER
        )
    ''')
    conn.commit()
    return conn


def detect_columns(headers):
    """Auto-detect meaningful column names from a CSV header list.

    Returns a dict with keys:
        'burner', 'runtime', 'pellet', 'outdoor_temp', 'flow_temp', 'return_temp'
    Each value is the full header string that matched, or None.
    """
    detected = {
        'burner': None,
        'runtime': None,       # cumulative hours counter (last - first = daily runtime h)
        'pellet': None,        # cumulative pellet counter (last - first = consumption kg)
        'pellet_level': None,  # fill-level gauge (first - last = consumption kg)
        'outdoor_temp': None,
        'flow_temp': None,
        'return_temp': None,
    }
    for h in headers:
        name_part = h.split('[')[0].strip()
        # burner: exact case-insensitive match on 'BR'
        if detected['burner'] is None and name_part.lower() == 'br':
            detected['burner'] = h
        # runtime: L_runtime (generic) or PE1 Runtime (OekoFEN PE1 unit)
        if detected['runtime'] is None and re.search(
            r'^L_runtime$|^PE1\s+Runtime', name_part, re.IGNORECASE
        ):
            detected['runtime'] = h
        # pellet cumulative counter: PE1.*cnt/verbrauch/pellet, or L_pellet
        if detected['pellet'] is None and re.search(
            r'^PE1.*(cnt|verbrauch|pellet)|^L_pellet', name_part, re.IGNORECASE
        ):
            detected['pellet'] = h
        # pellet fill-level gauge: PE1 Fuellstand (decreases as pellets burn)
        if detected['pellet_level'] is None and re.search(
            r'^PE1\s+Fuellstand', name_part, re.IGNORECASE
        ):
            detected['pellet_level'] = h
        # outdoor_temp: exact uppercase 'AT'
        if detected['outdoor_temp'] is None and name_part == 'AT':
            detected['outdoor_temp'] = h
        # flow_temp: HK1.*VL (case-insensitive)
        if detected['flow_temp'] is None and re.search(r'^HK1.*VL', name_part, re.IGNORECASE):
            detected['flow_temp'] = h
        # return_temp: HK1.*RT (case-insensitive)
        if detected['return_temp'] is None and re.search(r'^HK1.*RT', name_part, re.IGNORECASE):
            detected['return_temp'] = h
    print(f'[stats] columns detected: {detected}')
    return detected


def parse_german_float(s):
    """Parse a German-locale float string (comma as decimal separator).
    Returns float on success, None on failure.
    """
    if s is None:
        return None
    try:
        return float(str(s).replace(',', '.').strip())
    except (ValueError, TypeError):
        return None


def compute_day_stats(csv_string, date):
    """Compute per-day statistics from a CSV string (windows-1252 decoded).

    Returns a dict with all daily_stats fields, or None on fatal error.
    """
    try:
        lines = csv_string.splitlines()
        # Find first non-empty line as header
        header_line = None
        header_idx = 0
        for i, line in enumerate(lines):
            if line.strip():
                header_line = line
                header_idx = i
                break
        if header_line is None:
            print(f'[stats] {date}: no header line found')
            return None

        headers = [h.strip() for h in header_line.split(';')]
        detected = detect_columns(headers)

        # Map column names to indices
        col_idx = {}
        for col_name, col_header in detected.items():
            if col_header is not None:
                try:
                    col_idx[col_name] = headers.index(col_header)
                except ValueError:
                    col_idx[col_name] = None
            else:
                col_idx[col_name] = None

        # Parse all data rows (after header)
        data_rows = []
        for line in lines[header_idx + 1:]:
            if line.strip():
                data_rows.append(line.split(';'))

        row_count = len(data_rows)

        # Compute hours_covered from Datum/Zeit columns
        hours_covered = 0.0
        try:
            datum_idx = headers.index('Datum') if 'Datum' in headers else None
            # Try stripped version
            if datum_idx is None:
                for i, h in enumerate(headers):
                    if h.strip() == 'Datum':
                        datum_idx = i
                        break
            zeit_idx = None
            for i, h in enumerate(headers):
                if h.strip() == 'Zeit':
                    zeit_idx = i
                    break

            if datum_idx is not None and zeit_idx is not None and len(data_rows) >= 2:
                def parse_ts(row):
                    d_str = row[datum_idx].strip() if datum_idx < len(row) else ''
                    t_str = row[zeit_idx].strip() if zeit_idx < len(row) else ''
                    dt = datetime.datetime.strptime(f'{d_str} {t_str}', '%d.%m.%Y %H:%M:%S')
                    return dt.timestamp()
                first_ts = parse_ts(data_rows[0])
                last_ts = parse_ts(data_rows[-1])
                hours_covered = (last_ts - first_ts) / 3600.0
        except Exception as exc:
            print(f'[stats] {date}: hours_covered parse error: {exc}')
            hours_covered = 0.0

        is_partial = 1 if hours_covered < 20 else 0

        # Burner starts: count 0→1 transitions
        starts = None
        b_idx = col_idx.get('burner')
        if b_idx is not None:
            starts = 0
            prev_val = None
            for row in data_rows:
                if b_idx >= len(row):
                    continue
                val = parse_german_float(row[b_idx])
                if val is None:
                    prev_val = None
                    continue
                if prev_val is not None and prev_val == 0.0 and val == 1.0:
                    starts += 1
                prev_val = val

        # Runtime minutes: last - first value of runtime column
        # PE1 Runtime[h] is in hours — multiply delta by 60 to get minutes
        runtime_minutes = None
        r_idx = col_idx.get('runtime')
        r_header = detected.get('runtime', '')
        runtime_in_hours = r_header is not None and re.search(r'\[h\]', r_header or '', re.IGNORECASE)
        if r_idx is not None and data_rows:
            first_val = None
            last_val = None
            for row in data_rows:
                if r_idx < len(row):
                    v = parse_german_float(row[r_idx])
                    if v is not None:
                        if first_val is None:
                            first_val = v
                        last_val = v
            if first_val is not None and last_val is not None:
                delta = max(0.0, last_val - first_val)
                runtime_minutes = delta * 60.0 if runtime_in_hours else delta

        # Pellet kg: cumulative counter (last - first) or fill-level gauge (first - last)
        pellet_kg = None
        p_idx = col_idx.get('pellet')
        if p_idx is not None and data_rows:
            first_val = None
            last_val = None
            for row in data_rows:
                if p_idx < len(row):
                    v = parse_german_float(row[p_idx])
                    if v is not None:
                        if first_val is None:
                            first_val = v
                        last_val = v
            if first_val is not None and last_val is not None:
                pellet_kg = max(0.0, last_val - first_val)
        # Fallback: fill-level gauge (first - last = consumption)
        if pellet_kg is None:
            pl_idx = col_idx.get('pellet_level')
            if pl_idx is not None and data_rows:
                first_val = None
                last_val = None
                for row in data_rows:
                    if pl_idx < len(row):
                        v = parse_german_float(row[pl_idx])
                        if v is not None:
                            if first_val is None:
                                first_val = v
                            last_val = v
                if first_val is not None and last_val is not None:
                    pellet_kg = max(0.0, first_val - last_val)

        # Average outdoor temp
        avg_outdoor_temp = None
        o_idx = col_idx.get('outdoor_temp')
        if o_idx is not None:
            temps = []
            for row in data_rows:
                if o_idx < len(row):
                    v = parse_german_float(row[o_idx])
                    if v is not None:
                        temps.append(v)
            if temps:
                avg_outdoor_temp = sum(temps) / len(temps)

        # Flow/return delta
        flow_return_delta = None
        f_idx = col_idx.get('flow_temp')
        ret_idx = col_idx.get('return_temp')
        if f_idx is not None and ret_idx is not None:
            deltas = []
            for row in data_rows:
                if f_idx < len(row) and ret_idx < len(row):
                    fv = parse_german_float(row[f_idx])
                    rv = parse_german_float(row[ret_idx])
                    if fv is not None and rv is not None:
                        deltas.append(fv - rv)
            if deltas:
                flow_return_delta = sum(deltas) / len(deltas)

        # Degree-day consumption
        degree_day_consumption = None
        if (pellet_kg is not None and avg_outdoor_temp is not None
                and avg_outdoor_temp < 18):
            degree_day_consumption = pellet_kg / (18.0 - avg_outdoor_temp)

        return {
            'date': date,
            'starts': starts,
            'runtime_minutes': runtime_minutes,
            'pellet_kg': pellet_kg,
            'avg_outdoor_temp': avg_outdoor_temp,
            'flow_return_delta': flow_return_delta,
            'degree_day_consumption': degree_day_consumption,
            'row_count': row_count,
            'hours_covered': hours_covered,
            'is_partial': is_partial,
            'computed_at': int(time.time() * 1000),
        }
    except Exception as exc:
        print(f'[stats] Warning: compute_day_stats failed for {date}: {exc}')
        return None


def compute_and_store_stats(date):
    """Compute stats for one day's CSV and persist to stats.db.

    date: YYYYMMDD string (must match a file in HISTORY_DIR).
    Returns True on success, False if file missing or computation fails.
    Thread-safe: opens a fresh DB connection per call.
    """
    csv_path = os.path.join(HISTORY_DIR, f'{date}.csv')
    if not os.path.isfile(csv_path):
        return False
    try:
        with open(csv_path, 'rb') as f:
            raw = f.read()
        csv_string = None
        for enc in ('windows-1252', 'utf-8', 'utf-8-sig'):
            try:
                csv_string = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if csv_string is None:
            print(f'[stats] Could not decode {date}.csv (tried windows-1252, utf-8)')
            return False
    except Exception as exc:
        print(f'[stats] Could not read {date}.csv: {exc}')
        return False

    stats = compute_day_stats(csv_string, date)
    if stats is None:
        return False

    try:
        conn = open_stats_db()
        conn.execute('''
            INSERT OR REPLACE INTO daily_stats
            (date, starts, runtime_minutes, pellet_kg, avg_outdoor_temp,
             flow_return_delta, degree_day_consumption, row_count,
             hours_covered, is_partial, computed_at)
            VALUES (:date, :starts, :runtime_minutes, :pellet_kg, :avg_outdoor_temp,
                    :flow_return_delta, :degree_day_consumption, :row_count,
                    :hours_covered, :is_partial, :computed_at)
        ''', stats)
        conn.commit()
        conn.close()
        rt = stats['runtime_minutes']
        rt_str = f'{rt:.1f}' if rt is not None else 'N/A'
        print(f'[stats] Stored stats for {date}: {stats["starts"]} starts, {rt_str} min')
        return True
    except Exception as exc:
        print(f'[stats] DB write failed for {date}: {exc}')
        return False


def backfill_stats():
    """Process all ./history/*.csv files not yet in stats.db.

    Called synchronously at server startup so stats are ready before
    the first /stats request arrives.
    """
    if not os.path.isdir(HISTORY_DIR):
        print('[stats] Backfill complete — 0 new days computed (no history directory)')
        return

    csv_dates = set()
    for f in os.listdir(HISTORY_DIR):
        if f.endswith('.csv') and len(f) == 12:  # YYYYMMDD.csv
            csv_dates.add(f[:-4])

    if not csv_dates:
        print('[stats] Backfill complete — 0 new days computed (no CSV files)')
        return

    try:
        conn = open_stats_db()
        cur = conn.execute('SELECT date FROM daily_stats')
        existing_dates = {row[0] for row in cur.fetchall()}
        conn.close()
    except Exception as exc:
        print(f'[stats] Could not query existing dates: {exc}')
        existing_dates = set()

    missing = sorted(csv_dates - existing_dates)
    n = 0
    for date in missing:
        if compute_and_store_stats(date):
            n += 1
    print(f'[stats] Backfill complete — {n} new days computed')


def fetch_live_api():
    """Fetch live data from heater /all? endpoint.

    Returns dict with pellet consumption, storage levels, and avg runtime.
    All values are None when the heater is unreachable or settings missing.
    """
    settings = load_schedule_settings()
    ip       = settings.get('ip', '')
    port     = settings.get('port', '4321')
    password = settings.get('password', '')
    empty = {
        'pellets_today': None, 'pellets_yesterday': None,
        'storage_kg': None, 'storage_min': None, 'storage_max': None,
        'storage_hopper_kg': None, 'avg_runtime_min': None,
    }
    if not ip or not password:
        return empty
    url = f'http://{ip}:{port}/{password}/all?'
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode('windows-1252'))
        pe1 = data.get('pe1', {})
        def _int(key):
            v = pe1.get(key, {}).get('val')
            return int(v) if v is not None else None
        return {
            'pellets_today':    _int('L_pellets_today'),
            'pellets_yesterday':_int('L_pellets_yesterday'),
            'storage_kg':       _int('L_storage_fill'),
            'storage_min':      _int('L_storage_min'),
            'storage_max':      _int('L_storage_max'),
            'storage_hopper_kg':_int('L_storage_hopper'),
            'avg_runtime_min':  _int('L_avg_runtime'),
        }
    except Exception as exc:
        print(f'[stats] Could not fetch live API data: {exc}')
        return empty


def get_all_stats():
    """Retrieve all daily stats from stats.db and compute multi-day trend.

    Returns dict:
        { 'days': [...], 'trend': {...}, 'total_days': N, 'complete_days': M }
    """
    try:
        conn = open_stats_db()
        conn.row_factory = sqlite3.Row
        cur = conn.execute('SELECT * FROM daily_stats ORDER BY date ASC')
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
    except Exception as exc:
        print(f'[stats] get_all_stats DB error: {exc}')
        rows = []

    # Overlay live data from heater API
    live = fetch_live_api()
    today_str     = datetime.date.today().strftime('%Y%m%d')
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y%m%d')
    for row in rows:
        if row['date'] == today_str and live['pellets_today'] is not None:
            row['pellet_kg'] = live['pellets_today']
        elif row['date'] == yesterday_str and live['pellets_yesterday'] is not None:
            row['pellet_kg'] = live['pellets_yesterday']

    total_days = len(rows)
    complete_days_data = [r for r in rows if r.get('is_partial') == 0 and r.get('starts') is not None]
    complete_days = len(complete_days_data)

    # Linear regression on starts over time (complete days only)
    n = len(complete_days_data)
    if n < 3:
        trend = {'direction': None, 'slope': None, 'label': 'N/A — need 3+ complete days'}
    else:
        xs = list(range(n))
        ys = [r['starts'] for r in complete_days_data]
        sum_x = sum(xs)
        sum_y = sum(ys)
        sum_xy = sum(x * y for x, y in zip(xs, ys))
        sum_x2 = sum(x * x for x in xs)
        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denom

        if slope > 0.05:
            direction = 'up'
            label = f'\u2191 +{slope:.2f} starts/day'
        elif slope < -0.05:
            direction = 'down'
            label = f'\u2193 {slope:.2f} starts/day'
        else:
            direction = 'stable'
            label = '\u2192 stable'
        trend = {'direction': direction, 'slope': slope, 'label': label}

    # Days of fuel remaining = storage / avg daily consumption (last 7 complete days)
    days_remaining = None
    if live['storage_kg'] is not None:
        recent = [r['pellet_kg'] for r in complete_days_data[-7:]
                  if r.get('pellet_kg') is not None and r['pellet_kg'] > 0]
        if recent:
            avg_consumption = sum(recent) / len(recent)
            days_remaining = round(live['storage_kg'] / avg_consumption, 1)

    return {
        'days': rows,
        'trend': trend,
        'total_days': total_days,
        'complete_days': complete_days,
        'live': {
            'storage_kg':        live['storage_kg'],
            'storage_min':       live['storage_min'],
            'storage_max':       live['storage_max'],
            'storage_hopper_kg': live['storage_hopper_kg'],
            'avg_runtime_min':   live['avg_runtime_min'],
            'days_remaining':    days_remaining,
        },
    }


SYSTEM_PROMPT = """You are an expert OekoFEN pellet boiler technician with deep knowledge of the Pearl, P4, and Pellematic series. Analyse the provided operational statistics and heater settings to identify concrete, actionable improvements. Return ONLY valid JSON matching this schema exactly:

{
  "recommendations": [
    {
      "title": "Short action title (max 10 words)",
      "explanation": "Plain-language reason and expected benefit (2-4 sentences)",
      "setting_name": "Exact setting name as it appears in the heater menu, or null",
      "suggested_value": "Specific value to set, or null if no single setting change applies"
    }
  ],
  "maintenance_alerts": [
    {
      "title": "Alert title",
      "detail": "What was detected and why it matters"
    }
  ]
}

Expert knowledge base (apply when relevant):

BURNER STARTS:
- Normal: 2–5 starts/day for space heating; >8 starts/day indicates short-cycling
- Short-cycling causes: oversized boiler, buffer tank too small, heating curve too steep, hysteresis band too narrow
- Heating curve (Heizkurve Steilheit) typical range 0.8–1.8; steeper = more starts in mild weather
- Heizkurve Niveau shifts the entire curve up/down without changing slope

PELLET CONSUMPTION:
- Reference: 2–4 kg/day per 10 kW boiler output at 0°C outdoor temp
- Degree-day consumption (kg per degree-day) normalises for weather; compare across days
- High consumption at mild outdoor temps = heating curve too steep or room thermostat set too high
- Pellet hopper level below 20% warrants refill before next cold spell

HEATING CURVE INTERPRETATION:
- Steilheit (slope) controls sensitivity: 0.8 = shallow (mild response), 1.8 = steep (aggressive)
- Niveau (offset) raises/lowers flow temperature across all outdoor conditions
- Flow temperature > 75°C in non-condensing mode wastes energy; optimal 55–70°C for underfloor, 60–75°C for radiators
- Flow/return delta < 8°C suggests pump speed too high; > 20°C suggests pump too slow

MAINTENANCE INDICATORS:
- Fan speed (Geblaese) drifting above 85% of rated speed = ash buildup or heat exchanger fouling; schedule cleaning
- Ignition failures (starts counter rising but runtime not increasing proportionally) = worn igniter or pellet feed issue
- Return temperature consistently > 55°C = no condensate recovery possible; check system hydraulics
- Storage fill declining faster than expected for the outdoor temperature = check pellet quality (moisture, fines)

EXCLUSIONS (never recommend):
- Öko Modus / Eco Mode — known to underperform in practice; do not mention or suggest enabling it
- Settings that require heater firmware changes or physical modifications
- Any change that reduces safety margins (minimum flow temperature, minimum burner runtime)

If the data is insufficient to make a specific recommendation, set title to "Insufficient data" and explain what additional data would be needed. Return an empty array for sections where no issues are detected."""


def build_analysis_payload(stats_data, baseline_data):
    """Build a compact text context for the AI — aggregated stats + settings only.
    Raw CSV rows are NEVER included. Context size stays manageable (<4KB typical).
    """
    lines = []

    # --- Period summary ---
    days = stats_data.get('days', [])
    total = stats_data.get('total_days', 0)
    complete = stats_data.get('complete_days', 0)
    trend = stats_data.get('trend', {})
    live = stats_data.get('live', {})

    if days:
        dates = [d['date'] for d in days]
        lines.append(f"ANALYSIS PERIOD: {dates[0]} to {dates[-1]} ({total} days stored, {complete} complete)")
    else:
        lines.append("ANALYSIS PERIOD: No data stored yet.")

    # --- Start trend ---
    lines.append(f"START FREQUENCY TREND: {trend.get('label', 'N/A')}")
    if trend.get('slope') is not None:
        lines.append(f"  Regression slope: {trend['slope']:.3f} starts/day")

    # --- Per-day table (complete days only, most recent 14 days max) ---
    complete_days = [d for d in days if d.get('is_partial') == 0 and d.get('starts') is not None]
    recent = complete_days[-14:]  # cap at 14 to control context size
    if recent:
        lines.append("\nPER-DAY STATISTICS (complete days, most recent first):")
        lines.append("Date       | Starts | Runtime(min) | Pellet(kg) | AvgOutdoor(°C) | Flow-Return(°C)")
        lines.append("-" * 80)
        for d in reversed(recent):
            starts   = str(d.get('starts', 'N/A'))
            runtime  = f"{d['runtime_minutes']:.0f}" if d.get('runtime_minutes') is not None else 'N/A'
            pellet   = f"{d['pellet_kg']:.2f}" if d.get('pellet_kg') is not None else 'N/A'
            outdoor  = f"{d['avg_outdoor_temp']:.1f}" if d.get('avg_outdoor_temp') is not None else 'N/A'
            delta    = f"{d['flow_return_delta']:.1f}" if d.get('flow_return_delta') is not None else 'N/A'
            lines.append(f"{d['date']} | {starts:>6} | {runtime:>12} | {pellet:>10} | {outdoor:>14} | {delta}")

    # --- Live status ---
    if live.get('storage_kg') is not None:
        lines.append(f"\nCURRENT STORAGE: {live['storage_kg']:.0f} kg")
    if live.get('days_remaining') is not None:
        lines.append(f"ESTIMATED DAYS REMAINING: {live['days_remaining']:.1f} days")
    if live.get('avg_runtime_min') is not None:
        lines.append(f"AVG RUN DURATION (heater): {live['avg_runtime_min']:.0f} min")

    # --- Heater settings baseline ---
    if baseline_data and isinstance(baseline_data, dict):
        sections = baseline_data.get('sections', {})
        if sections:
            lines.append("\nHEATER SETTINGS BASELINE:")
            for section_name, kvs in sections.items():
                if not isinstance(kvs, dict):
                    continue
                lines.append(f"  [{section_name}]")
                for k, v in kvs.items():
                    lines.append(f"    {k}: {v}")
    else:
        lines.append("\nHEATER SETTINGS BASELINE: Not loaded.")

    return "\n".join(lines)


def parse_ai_response(text):
    """Extract JSON from AI response text. AI may include prose before/after the JSON block.
    Returns dict with keys 'recommendations' and 'maintenance_alerts' (both lists).
    Falls back to error structure if parsing fails.
    """
    # Try to extract JSON from markdown code block first
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
    if json_match:
        candidate = json_match.group(1)
    else:
        # Find the outermost { } in the response
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
        else:
            candidate = None

    if candidate:
        try:
            parsed = json.loads(candidate)
            return {
                'recommendations': parsed.get('recommendations', []),
                'maintenance_alerts': parsed.get('maintenance_alerts', []),
            }
        except json.JSONDecodeError:
            pass

    # Fallback: return the raw text as a single recommendation so nothing is silently lost
    return {
        'recommendations': [{'title': 'AI response parse error', 'explanation': text[:500], 'setting_name': None, 'suggested_value': None}],
        'maintenance_alerts': [],
    }


def call_ollama(endpoint, payload_text):
    """Send analysis request to Ollama chat API.
    endpoint: e.g. 'http://localhost:11434' (no trailing slash)
    Returns raw response text string.
    Raises RuntimeError on HTTP or network error.
    """
    endpoint = endpoint.rstrip('/')
    url = endpoint + '/api/chat'
    body = json.dumps({
        'model': 'llama3.2',   # default model; user can change via endpoint
        'stream': False,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user',   'content': payload_text},
        ],
    }).encode('utf-8')
    req = urllib.request.Request(
        url, data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        # Ollama response: { "message": { "content": "..." }, ... }
        return data['message']['content']
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Ollama returned HTTP {exc.code}: {exc.read().decode("utf-8", errors="replace")[:200]}')
    except Exception as exc:
        raise RuntimeError(f'Ollama call failed: {exc}')


def call_claude(api_key, payload_text):
    """Send analysis request to Claude API (api.anthropic.com).
    api_key: Anthropic API key string starting with 'sk-ant-...'
    Returns raw response text string.
    Raises RuntimeError on HTTP or network error.
    """
    url = 'https://api.anthropic.com/v1/messages'
    body = json.dumps({
        'model': 'claude-haiku-4-5',
        'max_tokens': 1024,
        'system': SYSTEM_PROMPT,
        'messages': [
            {'role': 'user', 'content': payload_text},
        ],
    }).encode('utf-8')
    req = urllib.request.Request(
        url, data=body,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        # Claude response: { "content": [{"type": "text", "text": "..."}], ... }
        return data['content'][0]['text']
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode('utf-8', errors='replace')[:300]
        raise RuntimeError(f'Claude API returned HTTP {exc.code}: {body_text}')
    except Exception as exc:
        raise RuntimeError(f'Claude API call failed: {exc}')


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
        compute_and_store_stats(date_str)
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


def _extract_date_from_log_url(url):
    """Extract YYYYMMDD date from a heater log URL (log_today, log0, log1, etc.).
    Returns date string or None if URL is not a recognizable log command.
    """
    path = urllib.parse.urlparse(url).path
    command = path.rstrip('/').split('/')[-1].lower()
    mapping = {
        'log_today': 0, 'log0': 0,
        'log_yesterday': 1, 'log1': 1,
        'log2': 2,
        'log3': 3,
    }
    delta = mapping.get(command)
    if delta is not None:
        return (datetime.date.today() - datetime.timedelta(days=delta)).strftime('%Y%m%d')
    return None


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

        # Route: GET /stats — return pre-computed daily stats as JSON
        if parsed.path == '/stats':
            stats = get_all_stats()
            body = json.dumps(stats, default=lambda x: None).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
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
                # Auto-save to history/ if this is a recognised log command
                log_date = _extract_date_from_log_url(target_url)
                if log_date:
                    try:
                        os.makedirs(HISTORY_DIR, exist_ok=True)
                        csv_path = os.path.join(HISTORY_DIR, f'{log_date}.csv')
                        with open(csv_path, 'wb') as f:
                            f.write(data)
                        threading.Thread(
                            target=compute_and_store_stats, args=(log_date,), daemon=True
                        ).start()
                    except Exception as save_exc:
                        print(f'[proxy] Could not save {log_date}.csv: {save_exc}')
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

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/history':
            params = urllib.parse.parse_qs(parsed.query)
            date = params.get('date', [None])[0]
            if not date or not re.match(r'^\d{8}$', date):
                self.send_error(400, 'Missing or invalid date parameter')
                return
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                os.makedirs(HISTORY_DIR, exist_ok=True)
                csv_path = os.path.join(HISTORY_DIR, f'{date}.csv')
                with open(csv_path, 'wb') as f:
                    f.write(body)
                compute_and_store_stats(date)
                self.send_response(204)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            except Exception as exc:
                self.send_error(500, f'POST /history error: {exc}')
        elif parsed.path == '/settings':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body.decode('utf-8'))
                ip       = str(payload.get('ip', '')).strip()
                port     = str(payload.get('port', '4321')).strip()
                password = str(payload.get('password', '')).strip()
                if not ip or not password:
                    self.send_error(400, 'ip and password are required')
                    return
                settings_path = os.path.join(SCRIPT_DIR, 'settings.json')
                with open(settings_path, 'w') as f:
                    json.dump({'ip': ip, 'port': port, 'password': password}, f)
                self.send_response(204)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            except Exception as exc:
                self.send_error(500, f'POST /settings error: {exc}')
        elif parsed.path == '/ai-analyze':
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            try:
                req_body = json.loads(raw.decode('utf-8'))
            except Exception:
                self.send_error(400, 'Invalid JSON body')
                return

            backend    = req_body.get('backend', 'ollama')
            credential = req_body.get('credential', '').strip()
            # baseline_data is optional — browser sends null if not loaded
            baseline_data = req_body.get('baseline_data')

            if not credential:
                self.send_error(400, 'Missing credential (endpoint URL or API key)')
                return

            # Build context payload from pre-computed stats (AICO-02: no raw CSV rows)
            try:
                stats_data = get_all_stats()
                payload_text = build_analysis_payload(stats_data, baseline_data)
            except Exception as exc:
                self.send_error(500, f'Failed to build analysis payload: {exc}')
                return

            # Dispatch to the configured backend
            try:
                if backend == 'claude':
                    ai_text = call_claude(credential, payload_text)
                else:
                    # default: ollama
                    ai_text = call_ollama(credential, payload_text)
            except RuntimeError as exc:
                self.send_error(502, str(exc))
                return

            # Parse structured response
            structured = parse_ai_response(ai_text)
            structured['days_analyzed'] = stats_data.get('total_days', 0)
            structured['analyzed_at']   = int(time.time() * 1000)

            resp_body = json.dumps(structured).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        else:
            self.send_error(405, 'Method not allowed')

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

    try:
        backfill_stats()
    except Exception as exc:
        print(f'[stats] Backfill error (non-fatal): {exc}')

    server = http.server.HTTPServer((HOST, PORT), Handler)
    url = f'http://localhost:{PORT}'
    print(f'OekoFEN Viewer running at {url} \u2014 Press Ctrl+C to stop')
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
