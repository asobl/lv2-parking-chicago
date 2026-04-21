#!/usr/bin/env python3
"""
LV2 Park — Weekly traffic monitor
Queries GA4 for sessions over the last 28 days.
Sends an email to Adam when sessions hit the FlexOffers reapply threshold.
Runs every Monday via GitHub Actions alongside send_digest.py.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

RESEND_API_KEY   = os.environ.get('RESEND_API_KEY', '')
GA4_PROPERTY_ID  = os.environ.get('GA4_PROPERTY_ID', '')   # numeric, e.g. 123456789
GOOGLE_SA_JSON   = os.environ.get('GOOGLE_SA_JSON', '')
NOTIFY_EMAIL     = os.environ.get('NOTIFY_EMAIL', '')
FROM_EMAIL       = 'LV2 Park <hello@lv2park.com>'
SITE_URL         = 'https://lv2park.com'

# Sessions/month threshold to trigger the FlexOffers reapply email
FLEXOFFERS_THRESHOLD = 500

# Once the alert fires, don't fire again until this many more sessions gained
REPEAT_BUFFER = 200


def get_ga4_sessions(property_id, sa_json_str):
    """Returns (sessions_28d, users_28d) from GA4 Data API."""
    token = get_google_token(sa_json_str, 'https://www.googleapis.com/auth/analytics.readonly')

    payload = {
        'dateRanges': [{'startDate': '28daysAgo', 'endDate': 'today'}],
        'metrics': [{'name': 'sessions'}, {'name': 'totalUsers'}]
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport',
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())

    rows = result.get('rows', [])
    if not rows:
        return 0, 0
    vals = rows[0].get('metricValues', [])
    sessions = int(vals[0]['value']) if len(vals) > 0 else 0
    users    = int(vals[1]['value']) if len(vals) > 1 else 0
    return sessions, users


def get_ga4_top_pages(property_id, sa_json_str, limit=5):
    """Returns list of (page_path, sessions) for top pages over last 28 days."""
    token = get_google_token(sa_json_str, 'https://www.googleapis.com/auth/analytics.readonly')

    payload = {
        'dateRanges': [{'startDate': '28daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'pagePath'}],
        'metrics': [{'name': 'sessions'}],
        'orderBys': [{'metric': {'metricName': 'sessions'}, 'desc': True}],
        'limit': limit
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport',
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())

    pages = []
    for row in result.get('rows', []):
        path = row['dimensionValues'][0]['value']
        sessions = int(row['metricValues'][0]['value'])
        pages.append((path, sessions))
    return pages


def get_ga4_top_sources(property_id, sa_json_str, limit=5):
    """Returns list of (source/medium, sessions) for top traffic sources over last 28 days."""
    token = get_google_token(sa_json_str, 'https://www.googleapis.com/auth/analytics.readonly')

    payload = {
        'dateRanges': [{'startDate': '28daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'sessionSourceMedium'}],
        'metrics': [{'name': 'sessions'}],
        'orderBys': [{'metric': {'metricName': 'sessions'}, 'desc': True}],
        'limit': limit
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport',
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())

    sources = []
    for row in result.get('rows', []):
        source = row['dimensionValues'][0]['value']
        sessions = int(row['metricValues'][0]['value'])
        sources.append((source, sessions))
    return sources


def send_reapply_email(sessions, users):
    subject = f'LV2 Park: {sessions} sessions this month — time to reapply to FlexOffers'
    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'Inter',system-ui,sans-serif;background:#f5f4f0;margin:0;padding:32px 16px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;">
    <div style="height:5px;background:#F5E030;"></div>
    <div style="padding:28px 28px 24px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#6B6B80;margin-bottom:8px;">LV2 PARK</div>
      <h1 style="font-size:26px;font-weight:900;color:#1A1A2E;margin:0 0 16px;">Reapply to FlexOffers.</h1>
      <p style="font-size:16px;color:#1A1A2E;line-height:1.6;margin:0 0 12px;">
        LV2 Park hit <strong>{sessions} sessions</strong> and <strong>{users} users</strong> in the last 28 days.
        That clears the threshold FlexOffers needs to see an established traffic source.
      </p>
      <p style="font-size:16px;color:#1A1A2E;line-height:1.6;margin:0 0 24px;">
        Reapply now and you should get approved this time.
      </p>
      <a href="https://publishers.flexoffers.com"
         style="display:inline-block;background:#6B64D4;color:#fff;font-size:15px;font-weight:700;padding:14px 24px;border-radius:10px;text-decoration:none;margin-bottom:20px;">
        Reapply to FlexOffers →
      </a>
      <p style="font-size:13px;color:#6B6B80;line-height:1.6;margin:0;">
        After approval, add the SpotHero affiliate link to app.js lines 10–11.<br>
        That unlocks the parking referral revenue on every game day.
      </p>
    </div>
    <div style="padding:16px 28px 20px;border-top:1px solid #EEEDF0;">
      <p style="font-size:11px;color:#9090a8;margin:0;">
        Sent automatically by check_traffic.py when sessions exceeded {FLEXOFFERS_THRESHOLD}.
      </p>
    </div>
  </div>
</body>
</html>'''

    data = json.dumps({
        'from': FROM_EMAIL,
        'to': [NOTIFY_EMAIL],
        'subject': subject,
        'html': html
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=data,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def send_weekly_status(sessions, users, top_pages=None, top_sources=None):
    """Send a simple weekly traffic status to Adam every Monday."""
    date_str = datetime.now().strftime('%b %-d')
    pct = min(100, round(sessions / FLEXOFFERS_THRESHOLD * 100))
    bar_filled = round(pct / 5)
    bar = '█' * bar_filled + '░' * (20 - bar_filled)
    remaining = max(0, FLEXOFFERS_THRESHOLD - sessions)

    # Build top pages rows
    pages_html = ''
    if top_pages:
        rows = ''.join(
            f'<tr><td style="padding:6px 0;font-size:13px;color:#1A1A2E;border-bottom:1px solid #EEEDF0;">'
            f'<a href="{SITE_URL}{path}" style="color:#6B64D4;text-decoration:none;">{path}</a></td>'
            f'<td style="padding:6px 0 6px 16px;font-size:13px;font-weight:700;color:#1A1A2E;text-align:right;border-bottom:1px solid #EEEDF0;">{s}</td></tr>'
            for path, s in top_pages
        )
        pages_html = f'''
      <div style="margin-bottom:20px;">
        <div style="font-size:12px;font-weight:700;color:#6B6B80;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">Top Pages (28d)</div>
        <table style="width:100%;border-collapse:collapse;">{rows}</table>
      </div>'''

    # Build top sources rows
    sources_html = ''
    if top_sources:
        rows = ''.join(
            f'<tr><td style="padding:6px 0;font-size:13px;color:#1A1A2E;border-bottom:1px solid #EEEDF0;">{src}</td>'
            f'<td style="padding:6px 0 6px 16px;font-size:13px;font-weight:700;color:#1A1A2E;text-align:right;border-bottom:1px solid #EEEDF0;">{s}</td></tr>'
            for src, s in top_sources
        )
        sources_html = f'''
      <div style="margin-bottom:20px;">
        <div style="font-size:12px;font-weight:700;color:#6B6B80;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">Top Sources (28d)</div>
        <table style="width:100%;border-collapse:collapse;">{rows}</table>
      </div>'''

    subject = f'LV2 Park traffic: {sessions} sessions (last 28d) -- {date_str}'
    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'Inter',system-ui,sans-serif;background:#f5f4f0;margin:0;padding:32px 16px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;">
    <div style="height:5px;background:#F5E030;"></div>
    <div style="padding:28px 28px 24px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#6B6B80;margin-bottom:8px;">LV2 PARK -- WEEKLY TRAFFIC</div>
      <h1 style="font-size:26px;font-weight:900;color:#1A1A2E;margin:0 0 20px;">{sessions} sessions · {users} users<br><span style="color:#6B6B80;font-size:16px;font-weight:400;">last 28 days</span></h1>

      <div style="background:#F5F4F0;border-radius:10px;padding:16px 20px;margin-bottom:20px;">
        <div style="font-size:12px;font-weight:700;color:#6B6B80;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">FlexOffers reapply goal: {FLEXOFFERS_THRESHOLD} sessions</div>
        <div style="font-family:monospace;font-size:14px;color:#1A1A2E;margin-bottom:6px;">{bar} {pct}%</div>
        <div style="font-size:13px;color:#6B6B80;">{f"Need {remaining} more sessions to reapply." if remaining > 0 else "Threshold reached -- reapply now."}</div>
      </div>

      {pages_html}
      {sources_html}

      <a href="https://analytics.google.com"
         style="display:inline-block;background:#1A1A2E;color:#F5E030;font-size:14px;font-weight:700;padding:10px 20px;border-radius:8px;text-decoration:none;">
        View GA4 →
      </a>
    </div>
    <div style="padding:16px 28px 20px;border-top:1px solid #EEEDF0;">
      <p style="font-size:11px;color:#9090a8;margin:0;">Sent every Monday by check_traffic.py · {SITE_URL}</p>
    </div>
  </div>
</body>
</html>'''

    data = json.dumps({
        'from': FROM_EMAIL,
        'to': [NOTIFY_EMAIL],
        'subject': subject,
        'html': html
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=data,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def get_google_token(sa_json_str, scope):
    import math, time
    sa = json.loads(sa_json_str)
    now = math.floor(time.time())
    claims = {
        'iss': sa['client_email'],
        'scope': scope,
        'aud': 'https://oauth2.googleapis.com/token',
        'exp': now + 3600,
        'iat': now
    }
    jwt = sign_jwt(claims, sa['private_key'])
    data = f'grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion={jwt}'.encode()
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    if 'access_token' not in result:
        raise Exception(f'Google auth failed: {result}')
    return result['access_token']


def sign_jwt(claims, private_key_pem):
    import base64, hashlib, hmac
    # Use subprocess + openssl since Python's ssl module isn't available without cryptography package
    import subprocess, tempfile, os

    header = base64.urlsafe_b64encode(json.dumps({'alg': 'RS256', 'typ': 'JWT'}).encode()).rstrip(b'=').decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b'=').decode()
    signing_input = f'{header}.{payload}'

    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write(private_key_pem)
        key_path = f.name

    try:
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-sign', key_path],
            input=signing_input.encode(),
            capture_output=True
        )
        if result.returncode != 0:
            raise Exception(f'openssl failed: {result.stderr.decode()}')
        sig = base64.urlsafe_b64encode(result.stdout).rstrip(b'=').decode()
    finally:
        os.unlink(key_path)

    return f'{signing_input}.{sig}'


def main():
    if not RESEND_API_KEY:
        print('[traffic] RESEND_API_KEY not set — skipping')
        sys.exit(0)
    if not GA4_PROPERTY_ID:
        print('[traffic] GA4_PROPERTY_ID not set — skipping')
        sys.exit(0)
    if not GOOGLE_SA_JSON:
        print('[traffic] GOOGLE_SA_JSON not set — skipping')
        sys.exit(0)

    print('[traffic] Querying GA4...')
    try:
        sessions, users = get_ga4_sessions(GA4_PROPERTY_ID, GOOGLE_SA_JSON)
    except Exception as e:
        print(f'[traffic] GA4 query failed: {e}')
        sys.exit(0)  # Non-fatal — don't break the Monday workflow

    print(f'[traffic] Sessions (28d): {sessions} | Users: {users}')

    # Fetch top pages and sources
    top_pages = []
    top_sources = []
    try:
        top_pages = get_ga4_top_pages(GA4_PROPERTY_ID, GOOGLE_SA_JSON)
        print(f'[traffic] Top pages: {top_pages}')
    except Exception as e:
        print(f'[traffic] Could not fetch top pages: {e}')
    try:
        top_sources = get_ga4_top_sources(GA4_PROPERTY_ID, GOOGLE_SA_JSON)
        print(f'[traffic] Top sources: {top_sources}')
    except Exception as e:
        print(f'[traffic] Could not fetch top sources: {e}')

    # Always send weekly status
    try:
        send_weekly_status(sessions, users, top_pages, top_sources)
        print('[traffic] Weekly status email sent')
    except Exception as e:
        print(f'[traffic] Could not send status email: {e}')

    # Send reapply alert if threshold crossed
    if sessions >= FLEXOFFERS_THRESHOLD:
        print(f'[traffic] Threshold reached ({sessions} >= {FLEXOFFERS_THRESHOLD}) — sending reapply alert')
        try:
            send_reapply_email(sessions, users)
            print('[traffic] Reapply alert sent')
        except Exception as e:
            print(f'[traffic] Could not send reapply alert: {e}')
    else:
        remaining = FLEXOFFERS_THRESHOLD - sessions
        print(f'[traffic] {remaining} more sessions needed before FlexOffers reapply')


if __name__ == '__main__':
    main()
