#!/usr/bin/env python3
"""
LV2 Park -- Monthly Audit
Runs all health checks and emails a full report to adam@lobosinnovation.com.

Triggered by GitHub Actions on the 1st of each month.
Also runnable locally: python scripts/monthly_audit.py

Requires: RESEND_API_KEY, RESEND_AUDIENCE_ID, TM_API_KEY in environment or .env
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

try:
    import requests as _requests
    _USE_REQUESTS = True
except ImportError:
    _USE_REQUESTS = False

# ── Load .env ─────────────────────────────────────────
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

# Must import after load_dotenv so env vars are available
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from health_check import run_all_checks, save_log

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
ALERT_TO       = 'adam@lobosinnovation.com'
FROM_EMAIL     = 'LV2 Park Monitor <hello@lv2park.com>'
SITE_URL       = 'https://lv2park.com'


# ── Email builder ─────────────────────────────────────

STATUS_COLORS = {
    'ok':   '#2D7D46',
    'warn': '#D4720B',
    'fail': '#C0392B',
}
STATUS_BG = {
    'ok':   '#EAF7EE',
    'warn': '#FFF4E5',
    'fail': '#FDEDEC',
}
STATUS_LABELS = {
    'ok':   'OK',
    'warn': 'WARN',
    'fail': 'FAIL',
}

def build_html(results, run_time):
    month_label = run_time.strftime('%B %Y')
    fails = [r for r in results if r['status'] == 'fail']
    warns = [r for r in results if r['status'] == 'warn']
    oks   = [r for r in results if r['status'] == 'ok']
    total = len(results)

    overall_status = 'fail' if fails else ('warn' if warns else 'ok')
    overall_label  = 'ACTION REQUIRED' if fails else ('HEADS UP' if warns else 'ALL GOOD')
    header_color   = STATUS_COLORS[overall_status]
    header_bg      = '#FDEDEC' if fails else ('#FFF4E5' if warns else '#EAF7EE')

    # Summary row
    summary_html = f'''
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tr>
        <td style="text-align:center;padding:16px;background:#EAF7EE;border-radius:8px;">
          <div style="font-size:28px;font-weight:900;color:#2D7D46;">{len(oks)}</div>
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#2D7D46;">OK</div>
        </td>
        <td style="width:12px;"></td>
        <td style="text-align:center;padding:16px;background:#FFF4E5;border-radius:8px;">
          <div style="font-size:28px;font-weight:900;color:#D4720B;">{len(warns)}</div>
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#D4720B;">WARN</div>
        </td>
        <td style="width:12px;"></td>
        <td style="text-align:center;padding:16px;background:#FDEDEC;border-radius:8px;">
          <div style="font-size:28px;font-weight:900;color:#C0392B;">{len(fails)}</div>
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#C0392B;">FAIL</div>
        </td>
      </tr>
    </table>'''

    # Check rows
    rows_html = ''
    for r in results:
        name   = r.get('name', '?')
        detail = r.get('detail', '')
        s      = r.get('status', 'warn')
        color  = STATUS_COLORS[s]
        bg     = STATUS_BG[s]
        label  = STATUS_LABELS[s]
        rows_html += f'''
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #F0EFF8;vertical-align:top;width:140px;">
            <span style="display:inline-block;background:{bg};color:{color};font-size:10px;font-weight:900;
                         letter-spacing:.06em;padding:3px 8px;border-radius:4px;">{label}</span>
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #F0EFF8;vertical-align:top;">
            <div style="font-size:14px;font-weight:700;color:#1A1A2E;">{name}</div>
            <div style="font-size:13px;color:#6B6B80;margin-top:2px;">{detail}</div>
          </td>
        </tr>'''

    # Action items section (fails + warns only)
    action_items = ''
    if fails or warns:
        items = ''
        for r in fails + warns:
            s = r['status']
            color = STATUS_COLORS[s]
            items += f'''
            <li style="margin-bottom:10px;color:#1A1A2E;">
              <strong style="color:{color};">[{STATUS_LABELS[s]}] {r["name"]}:</strong>
              {r["detail"]}
            </li>'''
        action_items = f'''
        <div style="margin-top:20px;padding:16px 20px;background:#FFF8E8;border-radius:10px;border-left:4px solid #F0A030;">
          <div style="font-size:13px;font-weight:700;color:#1A1A2E;margin-bottom:10px;">Action needed:</div>
          <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.7;">{items}</ul>
        </div>'''

    return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:-apple-system,'Inter',system-ui,sans-serif;background:#f5f4f0;margin:0;padding:32px 16px;">
  <div style="max-width:580px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;
              box-shadow:0 2px 20px rgba(0,0,0,0.08);">

    <div style="height:5px;background:{header_color};"></div>

    <div style="padding:24px 28px 8px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#6B6B80;margin-bottom:4px;">
        LV2 PARK MONTHLY AUDIT
      </div>
      <div style="font-size:24px;font-weight:900;color:#1A1A2E;">{overall_label}</div>
      <div style="font-size:13px;color:#6B6B80;margin-top:2px;">
        {month_label} &middot; {total} checks &middot; Run {run_time.strftime("%Y-%m-%d %H:%M UTC")}
      </div>
    </div>

    <div style="padding:16px 28px 0;">
      {summary_html}
    </div>

    <div style="padding:0 28px 8px;">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
                  color:#6B6B80;margin-bottom:8px;">All checks</div>
      <table style="width:100%;border-collapse:collapse;border:1px solid #F0EFF8;border-radius:8px;overflow:hidden;">
        {rows_html}
      </table>
    </div>

    {f'<div style="padding:0 28px 20px;">{action_items}</div>' if action_items else ''}

    <div style="margin:16px 28px 24px;padding:16px;background:#F5F4F0;border-radius:10px;">
      <div style="font-size:13px;color:#6B6B80;line-height:1.7;">
        <strong style="color:#1A1A2E;">Quick links:</strong><br>
        · <a href="{SITE_URL}" style="color:#6B64D4;">lv2park.com</a> — check the site is rendering correctly<br>
        · <a href="https://github.com" style="color:#6B64D4;">GitHub Actions</a> — check recent workflow runs<br>
        · <a href="https://resend.com" style="color:#6B64D4;">Resend dashboard</a> — subscriber count, broadcast history<br>
        · <a href="https://analytics.google.com" style="color:#6B64D4;">Google Analytics</a> — G-4FCPSHLCTX
      </div>
    </div>

    <div style="padding:16px 28px 20px;border-top:1px solid #EEEDF0;">
      <p style="font-size:11px;color:#9090a8;margin:0;line-height:1.8;">
        LV2 Park automated monthly audit &middot; hello@lv2park.com<br>
        To run manually: <code style="background:#f0eff8;padding:1px 5px;border-radius:3px;">
        python scripts/monthly_audit.py</code>
      </p>
    </div>

  </div>
</body>
</html>'''


# ── Send via Resend ───────────────────────────────────

def send_email(subject, html):
    if not RESEND_API_KEY:
        print('[audit] RESEND_API_KEY not set -- cannot send email')
        return False
    payload = {'from': FROM_EMAIL, 'to': [ALERT_TO], 'subject': subject, 'html': html}
    if _USE_REQUESTS:
        try:
            r = _requests.post(
                'https://api.resend.com/emails',
                json=payload,
                headers={'Authorization': f'Bearer {RESEND_API_KEY}'},
                timeout=15
            )
            if r.status_code in (200, 201):
                print(f'[audit] Email sent. ID: {r.json().get("id")}')
                return True
            print(f'[audit] Resend error HTTP {r.status_code}: {r.text[:200]}')
            return False
        except Exception as e:
            print(f'[audit] Send failed: {e}')
            return False
    # urllib fallback (GitHub Actions / Linux)
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails', data=data,
        headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f'[audit] Email sent. ID: {result.get("id")}')
            return True
    except urllib.error.HTTPError as e:
        print(f'[audit] Resend error HTTP {e.code}: {e.read().decode()}')
        return False


# ── Main ──────────────────────────────────────────────

def main():
    run_time = datetime.now(timezone.utc)
    month_label = run_time.strftime('%B %Y')
    print(f'[audit] Starting monthly audit for {month_label}...')

    results = run_all_checks()
    save_log(results)

    fails = [r for r in results if r['status'] == 'fail']
    warns = [r for r in results if r['status'] == 'warn']
    oks   = [r for r in results if r['status'] == 'ok']

    print(f'[audit] Results: {len(oks)} OK, {len(warns)} WARN, {len(fails)} FAIL')

    overall = 'ACTION REQUIRED' if fails else ('HEADS UP' if warns else 'ALL GOOD')
    subject = f'LV2 Park {month_label} audit: {overall} ({len(oks)}/{len(results)} checks passing)'

    html = build_html(results, run_time)
    sent = send_email(subject, html)

    if not sent:
        print('[audit] Email failed. Printing results to stdout instead:')
        for r in results:
            print(f'  [{r["status"].upper()}] {r["name"]}: {r["detail"]}')
        if fails:
            sys.exit(1)

    if fails:
        print(f'[audit] {len(fails)} FAIL(s) -- exiting with code 1 to trigger GitHub Actions alert')
        sys.exit(1)

    print('[audit] Done.')


if __name__ == '__main__':
    main()
