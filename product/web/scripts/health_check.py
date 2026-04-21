#!/usr/bin/env python3
"""
LV2 Park -- Health Check
Run locally to verify all moving parts are working.

Usage:
    python scripts/health_check.py

Saves a timestamped report to logs/health-YYYY-MM-DD-HHMMSS.json
The logs/ directory is in .gitignore and never pushed to git.

Also imported by monthly_audit.py to send the results by email.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

try:
    import requests as _requests
    _USE_REQUESTS = True
except ImportError:
    _USE_REQUESTS = False

# ── Load .env (local development only) ───────────────
def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, _, v = line.partition('=')
            k, v = k.strip(), v.strip()
            if k and v and k not in os.environ:
                os.environ[k] = v

load_dotenv()

# ── Config ────────────────────────────────────────────
TM_API_KEY         = os.environ.get('TM_API_KEY', '')
RESEND_API_KEY     = os.environ.get('RESEND_API_KEY', '')
RESEND_AUDIENCE_ID = os.environ.get('RESEND_AUDIENCE_ID', '')
WORKER_URL         = 'https://lv2park-email.adam-945.workers.dev'
SITE_URL           = 'https://lv2park.com'
SUBSCRIBER_WARN_AT = 80

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
LOGS_DIR = os.path.join(ROOT, 'logs')


# ── HTTP helpers ──────────────────────────────────────
# Uses `requests` when available (handles macOS SSL certs correctly).
# Falls back to urllib for GitHub Actions (Linux has certs installed).

def http_get(url, params=None, headers=None, timeout=12):
    """GET returning (status_code, body_str). Never raises."""
    if _USE_REQUESTS:
        try:
            r = _requests.get(url, params=params, headers=headers, timeout=timeout, allow_redirects=True)
            return r.status_code, r.text
        except Exception as e:
            return 0, str(e)
    # urllib fallback
    if params:
        from urllib.parse import urlencode
        url = url + '?' + urlencode(params)
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return 0, str(e)


def http_head(url, timeout=10):
    """HEAD request, follows redirects. Returns final status code."""
    if _USE_REQUESTS:
        try:
            r = _requests.head(url, timeout=timeout, allow_redirects=True)
            return r.status_code
        except Exception:
            return 0
    req = urllib.request.Request(url, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# ── Check runner ─────────────────────────────────────
def run_check(name, fn):
    """Run fn(), catch any exception, return a normalised result dict."""
    try:
        result = fn()
        result['name'] = name
        return result
    except Exception as e:
        return {'name': name, 'status': 'fail', 'detail': f'Exception: {e}', 'value': None}


# ── Individual checks ─────────────────────────────────

def check_mlb_api():
    status, body = http_get(
        'https://statsapi.mlb.com/api/v1/schedule',
        params={'sportId': 1, 'teamId': 112,
                'startDate': '2026-04-01', 'endDate': '2026-09-30'}
    )
    if status != 200:
        return {'status': 'fail', 'detail': f'HTTP {status}', 'value': status}
    data = json.loads(body)
    total = data.get('totalGamesInSeries', data.get('totalGames', 0))
    dates = len(data.get('dates', []))
    return {'status': 'ok', 'detail': f'{dates} game dates returned for April-Sept', 'value': dates}


def check_espn_api():
    status, body = http_get(
        'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/16/schedule',
        timeout=10
    )
    if status != 200:
        return {'status': 'fail', 'detail': f'HTTP {status}', 'value': status}
    data = json.loads(body)
    events = data.get('events', [])
    if not events:
        return {'status': 'warn', 'detail': 'ESPN returned 0 events -- fallback may not work', 'value': 0}
    return {'status': 'ok', 'detail': f'{len(events)} events returned', 'value': len(events)}


def check_ticketmaster_wrigley():
    if not TM_API_KEY:
        return {'status': 'warn', 'detail': 'TM_API_KEY not set -- cannot test', 'value': None}
    status, body = http_get(
        'https://app.ticketmaster.com/discovery/v2/events.json',
        params={'apikey': TM_API_KEY, 'venueId': 'KovZpZAFlktA', 'size': 5}
    )
    if status != 200:
        return {'status': 'fail', 'detail': f'HTTP {status}', 'value': status}
    data = json.loads(body)
    events = data.get('_embedded', {}).get('events', [])
    count = len(events)
    if count == 0:
        return {'status': 'warn', 'detail': 'Wrigley venue KovZpZAFlktA returned 0 events -- check API key or upcoming schedule', 'value': 0}
    names = [e.get('name', '?') for e in events[:3]]
    return {'status': 'ok', 'detail': f'{count} events. Sample: {", ".join(names)}', 'value': count}


def check_ticketmaster_gallagher():
    """
    Gallagher Way TM venue ID Z7r9jZady5 is expected to return 0 --
    their events sell through gallagherway.com/do312, not Ticketmaster.
    This check confirms the ID is dead and events are handled via overrides.json.
    """
    if not TM_API_KEY:
        return {'status': 'warn', 'detail': 'TM_API_KEY not set -- skipping', 'value': None}
    status, body = http_get(
        'https://app.ticketmaster.com/discovery/v2/events.json',
        params={'apikey': TM_API_KEY, 'venueId': 'Z7r9jZady5', 'size': 5}
    )
    if status != 200:
        return {'status': 'warn', 'detail': f'HTTP {status} -- Gallagher Way TM query failed', 'value': status}
    data = json.loads(body)
    events = data.get('_embedded', {}).get('events', [])
    count = len(events)
    if count == 0:
        return {
            'status': 'ok',
            'detail': 'Confirmed: Gallagher Way venue ID Z7r9jZady5 returns 0 TM events. '
                      'Events managed via overrides.json -- this is expected.',
            'value': 0
        }
    return {
        'status': 'warn',
        'detail': f'Unexpected: Gallagher Way TM ID returned {count} events. '
                  'Review fetch_data.py -- may be duplicating overrides.',
        'value': count
    }


def check_today_json():
    path = os.path.join(DATA_DIR, 'today.json')
    if not os.path.exists(path):
        return {'status': 'fail', 'detail': 'today.json not found in data/', 'value': None}
    with open(path) as f:
        data = json.load(f)
    updated = data.get('updated')
    if not updated:
        return {'status': 'warn', 'detail': 'today.json missing "updated" field', 'value': None}
    updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
    age_h = (datetime.now(timezone.utc) - updated_dt).total_seconds() / 3600
    s = 'ok' if age_h < 25 else 'fail'
    return {
        'status': s,
        'detail': f'{age_h:.1f}h old (limit 25h). hasEvent={data.get("hasEvent")}, lv2={data.get("lv2Active")}, source={data.get("source")}',
        'value': round(age_h, 1)
    }


def check_week_json():
    path = os.path.join(DATA_DIR, 'week.json')
    if not os.path.exists(path):
        return {'status': 'fail', 'detail': 'week.json not found in data/', 'value': None}
    with open(path) as f:
        data = json.load(f)
    updated = data.get('updated')
    if not updated:
        return {'status': 'warn', 'detail': 'week.json missing "updated" field', 'value': None}
    updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
    age_h = (datetime.now(timezone.utc) - updated_dt).total_seconds() / 3600
    days = len(data.get('days', []))
    event_days = sum(1 for d in data.get('days', []) if d.get('hasEvent'))
    s = 'ok' if age_h < 25 else 'fail'
    return {
        'status': s,
        'detail': f'{age_h:.1f}h old (limit 25h). {days} days loaded, {event_days} with events',
        'value': {'age_hours': round(age_h, 1), 'days': days, 'event_days': event_days}
    }


def check_health_json():
    path = os.path.join(DATA_DIR, 'health.json')
    if not os.path.exists(path):
        return {'status': 'fail', 'detail': 'health.json not found in data/', 'value': None}
    with open(path) as f:
        data = json.load(f)
    s = data.get('status', 'unknown')
    source = data.get('source', 'unknown')
    error = data.get('error')
    if s == 'ok':
        return {'status': 'ok', 'detail': f'Last run OK. source={source}', 'value': s}
    return {'status': 'fail', 'detail': f'status={s}, error={error}, source={source}', 'value': s}


def check_overrides_json():
    path = os.path.join(DATA_DIR, 'overrides.json')
    if not os.path.exists(path):
        return {'status': 'fail', 'detail': 'overrides.json not found', 'value': None}
    with open(path) as f:
        data = json.load(f)
    overrides = data.get('overrides', [])
    # Check for stale past overrides (events > 30 days ago)
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')
    stale = [o for o in overrides if o.get('date', '9999') < cutoff]
    if stale:
        stale_names = [o.get('name', '?') for o in stale[:3]]
        return {
            'status': 'warn',
            'detail': f'{len(stale)} stale override(s) older than 30 days. Consider cleaning up: {", ".join(stale_names)}',
            'value': len(stale)
        }
    return {
        'status': 'ok',
        'detail': f'{len(overrides)} active override(s)',
        'value': len(overrides)
    }


def check_cloudflare_worker():
    status = http_head(WORKER_URL, timeout=10)
    # Worker returns 404 on HEAD of root -- that's fine, it means it's alive
    if status in (200, 204, 404, 405):
        return {'status': 'ok', 'detail': f'Worker at {WORKER_URL} responded HTTP {status} (alive)', 'value': status}
    if status == 0:
        return {'status': 'fail', 'detail': f'Worker at {WORKER_URL} unreachable (timeout or connection refused)', 'value': 0}
    return {'status': 'fail', 'detail': f'Worker returned HTTP {status}', 'value': status}


def check_site_live():
    status, body = http_get(SITE_URL, timeout=15)
    if status == 200:
        has_hero = 'hero-card' in body or 'LV2' in body
        return {
            'status': 'ok',
            'detail': f'lv2park.com returned HTTP 200. Hero card present: {has_hero}',
            'value': status
        }
    return {'status': 'fail', 'detail': f'lv2park.com returned HTTP {status}', 'value': status}


def check_spothero_link():
    url = 'https://spothero.com/search?latitude=41.9484&longitude=-87.6553&utm_source=lv2park'
    status = http_head(url)
    s = 'ok' if 0 < status < 400 else 'warn'
    return {'status': s, 'detail': f'SpotHero link returned HTTP {status}', 'value': status}


def check_affiliate_ids():
    app_js = os.path.join(ROOT, 'app.js')
    if not os.path.exists(app_js):
        return {'status': 'warn', 'detail': 'app.js not found at project root', 'value': None}
    with open(app_js) as f:
        content = f.read()
    sg_match = re.search(r"SEATGEEK_AFF_ID\s*=\s*'([^']*)'", content)
    tm_match = re.search(r"TM_AFF_ID\s*=\s*'([^']*)'", content)
    sg_id = sg_match.group(1) if sg_match else None
    tm_id = tm_match.group(1) if tm_match else None
    issues = []
    if not sg_id:
        issues.append('SEATGEEK_AFF_ID is empty (FlexOffers pending)')
    if not tm_id:
        issues.append('TM_AFF_ID is empty (FlexOffers pending)')
    if issues:
        return {
            'status': 'warn',
            'detail': ' | '.join(issues),
            'value': {'seatgeek': bool(sg_id), 'tm': bool(tm_id)}
        }
    return {
        'status': 'ok',
        'detail': 'Both SeatGeek and Ticketmaster affiliate IDs are set',
        'value': {'seatgeek': True, 'tm': True}
    }


def check_env_vars():
    missing = []
    if not RESEND_API_KEY:     missing.append('RESEND_API_KEY')
    if not RESEND_AUDIENCE_ID: missing.append('RESEND_AUDIENCE_ID')
    if not TM_API_KEY:         missing.append('TM_API_KEY')
    if missing:
        return {
            'status': 'fail',
            'detail': f'Missing env vars: {", ".join(missing)}',
            'value': missing
        }
    return {'status': 'ok', 'detail': 'All required env vars are set', 'value': None}


def check_resend_subscribers():
    """Check subscriber count. Warn at SUBSCRIBER_WARN_AT (80)."""
    if not RESEND_API_KEY or not RESEND_AUDIENCE_ID:
        return {'status': 'warn', 'detail': 'RESEND_API_KEY or RESEND_AUDIENCE_ID not set', 'value': None}
    status, body = http_get(
        f'https://api.resend.com/audiences/{RESEND_AUDIENCE_ID}/contacts',
        headers={'Authorization': f'Bearer {RESEND_API_KEY}'}
    )
    if status != 200:
        return {'status': 'fail', 'detail': f'Resend API error HTTP {status}: {body[:120]}', 'value': None}
    try:
        data = json.loads(body)
    except Exception as e:
        return {'status': 'fail', 'detail': f'Resend response parse error: {e}', 'value': None}
    contacts = data.get('data', [])
    count = len(contacts)
    if count >= SUBSCRIBER_WARN_AT:
        return {
            'status': 'warn',
            'detail': (
                f'{count} subscribers. Free tier daily limit is 100. '
                f'Upgrade to Resend Pro ($20/mo) before Monday digest fails.'
            ),
            'value': count
        }
    return {
        'status': 'ok',
        'detail': f'{count} subscribers ({SUBSCRIBER_WARN_AT - count} until Adam gets an alert, 100 until free tier limit)',
        'value': count
    }


# ── Main runner ───────────────────────────────────────

def run_all_checks():
    return [
        run_check('MLB API',                      check_mlb_api),
        run_check('ESPN API (fallback)',           check_espn_api),
        run_check('Ticketmaster -- Wrigley',      check_ticketmaster_wrigley),
        run_check('Ticketmaster -- Gallagher Way', check_ticketmaster_gallagher),
        run_check('today.json freshness',         check_today_json),
        run_check('week.json freshness',          check_week_json),
        run_check('health.json last run',         check_health_json),
        run_check('overrides.json',               check_overrides_json),
        run_check('Cloudflare Worker',            check_cloudflare_worker),
        run_check('Site live (lv2park.com)',      check_site_live),
        run_check('SpotHero link',                check_spothero_link),
        run_check('Affiliate IDs in app.js',      check_affiliate_ids),
        run_check('Environment variables',        check_env_vars),
        run_check('Resend subscriber count',      check_resend_subscribers),
    ]


def print_results(results):
    STATUS_ICONS = {'ok': '✓', 'warn': '!', 'fail': '✗'}
    fails = [r for r in results if r['status'] == 'fail']
    warns = [r for r in results if r['status'] == 'warn']
    oks   = [r for r in results if r['status'] == 'ok']

    print(f'\n{"─" * 60}')
    print(f'  LV2 Park Health Check — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'{"─" * 60}')
    for r in results:
        icon = STATUS_ICONS.get(r['status'], '?')
        print(f'  [{icon}] {r["name"]}')
        print(f'      {r["detail"]}')
    print(f'{"─" * 60}')
    print(f'  {len(oks)} OK  |  {len(warns)} WARN  |  {len(fails)} FAIL')
    print(f'{"─" * 60}\n')

    if fails or warns:
        print('  Action needed:')
        for r in fails + warns:
            print(f'  [{STATUS_ICONS[r["status"]]}] {r["name"]}: {r["detail"]}')
        print()


def save_log(results):
    os.makedirs(LOGS_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    path = os.path.join(LOGS_DIR, f'health-{ts}.json')
    payload = {
        'run_at':  datetime.now(timezone.utc).isoformat(),
        'summary': {
            'ok':   sum(1 for r in results if r['status'] == 'ok'),
            'warn': sum(1 for r in results if r['status'] == 'warn'),
            'fail': sum(1 for r in results if r['status'] == 'fail'),
        },
        'checks': results
    }
    with open(path, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f'  Log saved: {path}')
    return path


if __name__ == '__main__':
    print('Running LV2 Park health check...')
    results = run_all_checks()
    print_results(results)
    save_log(results)
    fails = [r for r in results if r['status'] == 'fail']
    sys.exit(1 if fails else 0)
