#!/usr/bin/env python3
"""
LV2 Park — Monday digest sender
Reads data/week.json and broadcasts the weekly email to all Resend subscribers.
Called from GitHub Actions every Monday at 7 AM CT.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

RESEND_API_KEY     = os.environ.get('RESEND_API_KEY', '')
RESEND_AUDIENCE_ID = os.environ.get('RESEND_AUDIENCE_ID', '')
FROM_EMAIL         = 'LV2 Park <hello@lv2park.com>'
SITE_URL           = 'https://lv2park.com'
SPOTHERO_URL       = 'https://spothero.com/search?latitude=41.9484&longitude=-87.6553&utm_source=lv2park-email'


def load_week():
    with open('data/week.json') as f:
        return json.load(f)


def event_icon(ev):
    name = (ev.get('name') or '').lower()
    if ev.get('type') == 'game':
        return '⚾'
    if 'comedy' in name or 'mulaney' in name or 'stand-up' in name:
        return '🎭'
    return '🎵'


def build_subject(data):
    today = datetime.now()
    date_str = today.strftime('%b %-d')
    game_days = [d for d in data.get('days', []) if d.get('hasEvent')]
    if not game_days:
        return f"Your week at Wrigley — {date_str} (quiet week)"
    count = len(game_days)
    if count == 1:
        return f"1 event at Wrigley this week — {date_str}"
    return f"{count} events at Wrigley this week — {date_str}"


def build_html(data):
    today = datetime.now()
    date_str = today.strftime('%B %-d, %Y')

    rows = ''
    has_any_event = False

    for day in data.get('days', []):
        has_event  = day.get('hasEvent', False)
        lv2_active = day.get('lv2Active', False)
        events     = day.get('events', [])
        label      = day.get('dayLabel', '')

        if has_event:
            has_any_event = True

        bg           = '#FFFBF0' if has_event else '#ffffff'
        left_border  = '4px solid #F5E030' if has_event else '4px solid transparent'

        event_html = ''
        if has_event and events:
            for ev in events:
                icon  = event_icon(ev)
                name  = ev.get('name', '')
                time  = ev.get('time', '')
                event_html += f'<div style="font-size:15px;font-weight:700;color:#1A1A2E;margin-bottom:2px;">{icon} {name}</div>'
                if time and time != 'TBD':
                    event_html += f'<div style="font-size:13px;color:#6B6B80;margin-bottom:4px;">{time} CT</div>'
        else:
            event_html = '<div style="font-size:14px;color:#9090a8;">No events</div>'

        lv2_badge = ''
        if lv2_active:
            lv2_badge = '<div style="margin-top:5px;"><span style="display:inline-block;background:#F0A030;color:#fff;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:3px 9px;border-radius:4px;">LV2 5–10 PM</span></div>'

        rows += f'''
        <tr>
          <td style="padding:12px 14px;background:{bg};border-left:{left_border};border-bottom:1px solid #EEEDF0;vertical-align:top;width:100px;">
            <div style="font-size:13px;font-weight:700;color:#6B6B80;white-space:nowrap;">{label}</div>
          </td>
          <td style="padding:12px 14px;background:{bg};border-bottom:1px solid #EEEDF0;vertical-align:top;">
            {event_html}
            {lv2_badge}
          </td>
        </tr>'''

    parking_cta = ''
    if has_any_event:
        parking_cta = f'''
        <div style="margin:20px 0 8px;">
          <a href="{SPOTHERO_URL}"
             style="display:inline-block;background:#6B64D4;color:#fff;font-size:15px;font-weight:700;padding:14px 24px;border-radius:10px;text-decoration:none;">
            Book parking near Wrigley →
          </a>
        </div>'''

    return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family:-apple-system,'Inter',system-ui,sans-serif;background:#f5f4f0;margin:0;padding:32px 16px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 20px rgba(0,0,0,0.08);">

    <div style="height:5px;background:#F5E030;"></div>

    <div style="padding:24px 28px 16px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#6B6B80;margin-bottom:6px;">LV2 PARK</div>
      <div style="font-size:26px;font-weight:900;color:#1A1A2E;line-height:1.15;">Your week at Wrigley</div>
      <div style="font-size:14px;color:#6B6B80;margin-top:4px;">{date_str}</div>
    </div>

    <div style="padding:0 28px 8px;">
      <table style="width:100%;border-collapse:collapse;border:1px solid #EEEDF0;border-radius:8px;overflow:hidden;">
        {rows}
      </table>
    </div>

    <div style="padding:0 28px;">
      {parking_cta}
    </div>

    <div style="margin:20px 28px 24px;padding:16px;background:#FFF8E8;border-radius:10px;border-left:4px solid #F0A030;">
      <div style="font-size:13px;font-weight:700;color:#1A1A2E;margin-bottom:4px;">When LV2 is active</div>
      <div style="font-size:13px;color:#6B6B80;line-height:1.6;">
        Tow zone enforced 5–10 PM on game and event days. Officers start writing tickets at 5:01 PM exactly.
        <a href="{SITE_URL}/blog/what-is-lv2.html" style="color:#6B64D4;font-weight:700;">What is LV2?</a>
      </div>
    </div>

    <div style="margin:0 28px 28px;padding:20px;background:#F5F4F0;border-radius:10px;text-align:center;">
      <div style="font-size:15px;font-weight:700;color:#1A1A2E;margin-bottom:6px;">Know someone in Lakeview?</div>
      <div style="font-size:13px;color:#6B6B80;margin-bottom:14px;">Forward this email. Their car will thank you after game day.</div>
      <a href="{SITE_URL}" style="display:inline-block;background:#1A1A2E;color:#F5E030;font-size:14px;font-weight:700;padding:10px 20px;border-radius:8px;text-decoration:none;">
        Share lv2park.com
      </a>
    </div>

    <div style="padding:16px 28px 20px;border-top:1px solid #EEEDF0;">
      <p style="font-size:11px;color:#9090a8;margin:0;line-height:1.8;">
        lv2park.com &middot; Not affiliated with the Chicago Cubs or MLB.<br>
        Schedule may change &mdash; check <a href="{SITE_URL}" style="color:#9090a8;">lv2park.com</a> for the latest.<br>
        <a href="{{{{unsubscribe_url}}}}" style="color:#9090a8;">Unsubscribe</a>
      </p>
    </div>

  </div>
</body>
</html>'''


def api_post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req  = urllib.request.Request(
        f'https://api.resend.com{path}',
        data=data,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type':  'application/json',
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'[digest] API error {e.code}: {body}')
        return None


def main():
    if not RESEND_API_KEY:
        print('[digest] RESEND_API_KEY not set — skipping')
        sys.exit(0)
    if not RESEND_AUDIENCE_ID:
        print('[digest] RESEND_AUDIENCE_ID not set — skipping')
        sys.exit(0)

    print('[digest] Loading week data...')
    data = load_week()

    subject = build_subject(data)
    html    = build_html(data)
    print(f'[digest] Subject: {subject}')

    print('[digest] Creating broadcast...')
    broadcast = api_post('/broadcasts', {
        'audience_id': RESEND_AUDIENCE_ID,
        'from':        FROM_EMAIL,
        'subject':     subject,
        'html':        html,
    })

    if not broadcast or 'id' not in broadcast:
        print('[digest] Failed to create broadcast:', broadcast)
        sys.exit(1)

    bid = broadcast['id']
    print(f'[digest] Broadcast created: {bid}')

    print('[digest] Sending...')
    result = api_post(f'/broadcasts/{bid}/send', {})
    print('[digest] Result:', result)
    print('[digest] Done.')


if __name__ == '__main__':
    main()
