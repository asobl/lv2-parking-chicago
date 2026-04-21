#!/usr/bin/env python3
"""
content_reminder.py

Reads blog/schedule.json and checks for posts that:
  - Don't have an HTML file yet in product/web/blog/
  - Have a publish_date within the next 30 days

If any are found, sends a reminder email via Resend to NOTIFY_EMAIL.
Run by GitHub Actions on the 1st of each month.
"""

import json
import os
import datetime
import urllib.request
import urllib.parse

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
LOOKAHEAD_DAYS = 30

def main():
    if not RESEND_API_KEY or not NOTIFY_EMAIL:
        print("Missing RESEND_API_KEY or NOTIFY_EMAIL — skipping reminder.")
        return

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=LOOKAHEAD_DAYS)

    with open("product/web/blog/schedule.json") as f:
        schedule = json.load(f)

    due = []
    for post in schedule:
        slug = post["slug"]
        publish_date = datetime.date.fromisoformat(post["publish_date"])

        # Only care about future posts within the lookahead window
        if not (today <= publish_date <= cutoff):
            continue

        # Check if the HTML file has been drafted yet
        html_path = f"product/web/blog/{slug}"
        if not os.path.exists(html_path):
            days_until = (publish_date - today).days
            due.append({
                "title": post["title"],
                "slug": slug,
                "publish_date": post["publish_date"],
                "label": post.get("label", ""),
                "days_until": days_until,
            })

    if not due:
        print(f"No blog posts need drafting in the next {LOOKAHEAD_DAYS} days.")
        return

    # Build email body
    lines = [
        f"LV2 Park Blog: {len(due)} post(s) need drafting in the next {LOOKAHEAD_DAYS} days.",
        "",
    ]
    for p in sorted(due, key=lambda x: x["publish_date"]):
        lines.append(f"  [{p['label']}] {p['title']}")
        lines.append(f"  Publish: {p['publish_date']} ({p['days_until']} days from today)")
        lines.append(f"  File: product/web/blog/{p['slug']}")
        lines.append("")

    lines += [
        "To draft: open Claude Code in the lv2park project and say:",
        '  "Draft the blog post for [title]"',
        "",
        "Full content calendar: product/web/blog/schedule.json",
        "",
        "— GitHub Actions content reminder, lv2park",
    ]

    body = "\n".join(lines)
    subject = f"LV2 Park: {len(due)} blog post(s) need drafting this month"

    payload = json.dumps({
        "from": "LV2 Park <updates@lv2park.com>",
        "to": [NOTIFY_EMAIL],
        "subject": subject,
        "text": body,
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        status = resp.status
        body_resp = resp.read().decode()

    if status == 200:
        print(f"Reminder sent to {NOTIFY_EMAIL} ({len(due)} post(s)).")
    else:
        print(f"Resend returned {status}: {body_resp}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
