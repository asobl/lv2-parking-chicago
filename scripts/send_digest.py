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
SUBSCRIBER_WARN_AT = 80    # Email adam@lobosinnovation.com when list hits this
ADAM_EMAIL         = 'adam@lobosinnovation.com'


def load_week():
    with open('data/week.json') as f:
        data = json.load(f)
    # Filter to the next 7 days only
    today = datetime.now().strftime('%Y-%m-%d')
    all_days = data.get('days', [])
    data['days'] = [d for d in all_days if d.get('date', '') >= today][:7]
    return data


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
      <div style="font-size:13px;color:#6B6B80;margin-bottom:16px;">Forward this email or send them the link before they find out the hard way.</div>
      <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
        <a href="mailto:?subject=Heads%20up%20%E2%80%94%20LV2%20parking%20near%20Wrigley&body=Hey%2C%20found%20this%20%E2%80%94%20lv2park.com%20tells%20you%20when%20LV2%20tow%20zones%20are%20active%20near%20Wrigley%20Field%20so%20you%20don%27t%20get%20towed.%20Worth%20bookmarking%20if%20you%20ever%20park%20in%20Lakeview%20or%20Wrigleyville."
           style="display:inline-block;background:#1A1A2E;color:#F5E030;font-size:13px;font-weight:700;padding:10px 16px;border-radius:8px;text-decoration:none;">
          <span style="font-size:18px;vertical-align:middle;margin-right:6px;">✉</span>Email a friend
        </a>
        <a href="https://twitter.com/intent/tweet?text=If%20you%20park%20near%20Wrigley%2C%20bookmark%20this%3A%20lv2park.com%20%E2%80%94%20tells%20you%20exactly%20when%20LV2%20tow%20zones%20are%20active%20so%20you%20don%27t%20get%20towed."
           style="display:inline-block;background:#000;color:#fff;font-size:13px;font-weight:700;padding:10px 16px;border-radius:8px;text-decoration:none;">
          <span style="font-size:18px;vertical-align:middle;margin-right:6px;">𝕏</span>Post
        </a>
        <a href="https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Flv2park.com"
           style="display:inline-block;background:#1877F2;color:#fff;font-size:13px;font-weight:700;padding:10px 16px;border-radius:8px;text-decoration:none;">
          <span style="font-size:18px;vertical-align:middle;margin-right:6px;">f</span>Facebook
        </a>
      </div>
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


def get_subscriber_count():
    """Returns subscriber count from Resend, or None on error."""
    req = urllib.request.Request(
        f'https://api.resend.com/audiences/{RESEND_AUDIENCE_ID}/contacts',
        headers={'Authorization': f'Bearer {RESEND_API_KEY}'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return len(data.get('data', []))
    except Exception as e:
        print(f'[digest] Could not fetch subscriber count: {e}')
        return None


def send_subscriber_warning(count):
    """Send a one-off alert email to Adam when list approaches the free tier limit."""
    subject = f'LV2 Park: {count} subscribers -- Resend free tier limit approaching'
    html = f'''<!DOCTYPE html>
<html><body style="font-family:system-ui,sans-serif;padding:32px;max-width:480px;">
  <h2 style="color:#D4720B;">Resend tier heads-up</h2>
  <p>The LV2 Park email list now has <strong>{count} subscribers</strong>.</p>
  <p>The Resend free tier sends a max of <strong>100 emails/day</strong>.
     When the Monday digest hits more than 100 subscribers, it will fail silently.</p>
  <p><strong>Action:</strong> Upgrade to Resend Pro ($20/mo) at
     <a href="https://resend.com/pricing">resend.com/pricing</a>
     before the list passes 100.</p>
  <p style="font-size:12px;color:#999;">Sent automatically by send_digest.py when subscriber count reached {SUBSCRIBER_WARN_AT}.</p>
</body></html>'''
    api_post('/emails', {
        'from':    FROM_EMAIL,
        'to':      [ADAM_EMAIL],
        'subject': subject,
        'html':    html,
    })
    print(f'[digest] Subscriber warning sent to {ADAM_EMAIL} ({count} subscribers)')


def main():
    if not RESEND_API_KEY:
        print('[digest] RESEND_API_KEY not set — skipping')
        sys.exit(0)
    if not RESEND_AUDIENCE_ID:
        print('[digest] RESEND_AUDIENCE_ID not set — skipping')
        sys.exit(0)

    # Check subscriber count before sending digest
    count = get_subscriber_count()
    if count is not None:
        print(f'[digest] Subscriber count: {count}')
        if count >= SUBSCRIBER_WARN_AT:
            send_subscriber_warning(count)

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
