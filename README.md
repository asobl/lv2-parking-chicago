# LV2 Park

**Is there a game or event at Wrigley today?**

[lv2park.com](https://lv2park.com) tells you instantly, and whether the LV2 tow zone is active tonight.

---

## What It Does

LV2 is a Chicago parking zone surrounding Wrigley Field. On game days and event nights, parking is restricted 5-10 PM. Cars get towed fast, usually within minutes of 5:00 PM. Over 9,400 cars were ticketed in the zone between 2018 and 2023.

This site gives Lakeview and Wrigleyville residents a simple answer every day:

- Is there a game or event today?
- Is LV2 in effect tonight?
- What does the week ahead look like?
- Where can I park safely?

A Monday morning email digest goes out every week with the full week's schedule.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Leaflet.js (map) |
| Hosting | GitHub Pages (custom domain) |
| Email | [Resend](https://resend.com) — audience, broadcasts, transactional |
| Backend | Cloudflare Workers (subscribe, contact, unsubscribe) |
| Captcha | Cloudflare Turnstile (invisible) |
| Data | MLB schedule API + Ticketmaster, auto-refreshed 2x/day |
| CI | GitHub Actions (6 AM + 3 PM CT daily, Monday digest) |
| Analytics | Google Analytics |

---

## How the Data Pipeline Works

```
GitHub Actions (cron) -> scripts/fetch_data.py
  -> MLB schedule API + Ticketmaster API
  -> data/today.json + data/week.json
  -> git commit + push (updates the live site)
```

On Mondays, the workflow also runs `scripts/send_digest.py`, which sends the weekly email via Resend broadcast API.

---

## Project Structure

```
/
├── index.html              Main page
├── unsubscribe.html        Unsubscribe page with churn survey
├── style.css               All styles
├── app.js                  All frontend logic (map, schedule, email form)
├── og-image.png            Social sharing image (1200x630)
├── og-image-src.html       Source HTML to regenerate OG image
├── CNAME                   GitHub Pages custom domain
│
├── blog/
│   ├── index.html          Blog index
│   ├── lv2-data-analysis.html   FOIA data analysis post
│   └── what-is-lv2.html        LV2 explainer post
│
├── data/
│   ├── today.json          Today's game/event status
│   ├── week.json           This week's schedule
│   ├── health.json         Last successful data refresh timestamp
│   └── overrides.json      Manual event overrides
│
├── scripts/
│   ├── fetch_data.py       Data pipeline (MLB + Ticketmaster)
│   └── send_digest.py      Monday digest email sender
│
├── worker/
│   ├── index.js            Cloudflare Worker (subscribe / contact / unsubscribe)
│   └── wrangler.toml       Worker config
│
└── .github/
    └── workflows/
        └── update.yml      Daily data refresh + Monday digest
```

---

## Local Development

```bash
# Serve locally
python3 -m http.server 9001

# Open
open http://localhost:9001
```

The Worker runs separately on Cloudflare. For local form testing, set `DEV_MODE = true` in your Worker environment so CORS allows localhost.

---

## Worker Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/subscribe` | POST | Adds email to Resend audience, sends welcome email, notifies Adam |
| `/contact` | POST | Forwards contact form to adam@lobosinnovation.com |
| `/unsubscribe` | POST | Marks unsubscribed in Resend, sends churn feedback |

Worker: `https://lv2park-email.adam-945.workers.dev`

Deploy: `cd worker && npx wrangler deploy`

---

## Environment Variables

### Worker Secrets (set in Cloudflare dashboard)

| Variable | Description |
|---|---|
| `RESEND_API_KEY` | Resend API key (full access) |
| `RESEND_AUDIENCE_ID` | Resend audience ID |
| `NOTIFY_EMAIL` | Where contact + subscriber notifications go |
| `TURNSTILE_SECRET` | Cloudflare Turnstile secret key |

### GitHub Actions Secrets

| Secret | Used by |
|---|---|
| `RESEND_API_KEY` | `send_digest.py` |
| `RESEND_AUDIENCE_ID` | `send_digest.py` |
| `TICKETMASTER_API_KEY` | `fetch_data.py` |

---

## The LV2 Zone

The LV2 residential parking zone is defined in Chicago Municipal Code 9-68-023. It covers roughly:

- **North:** Irving Park Road
- **South:** Addison Street
- **East:** Racine Avenue
- **West:** Ashland Avenue

Streets inside the zone are posted with signs. On any day with a Cubs game, concert, or permitted event at Wrigley, parking is restricted 5-10 PM. Enforcement starts exactly at 5:00 PM.

FOIA data analysis: [lv2park.com/blog/lv2-data-analysis.html](https://lv2park.com/blog/lv2-data-analysis.html)

---

## Not Affiliated

Not affiliated with the Chicago Cubs, MLB, or the City of Chicago. Schedule data is pulled from public sources (MLB, Ticketmaster), the same sources the 44th Ward uses to post enforcement dates. When in doubt, check [mlb.com/cubs/schedule](https://mlb.com/cubs/schedule) or the [44th Ward site](https://www.44thward.org).

---

Built by an entrepreneur in Roscoe Village who got tired of moving his car. Inspired by a Lakeview friend who didn't want her car, or her friends' cars, towed.
