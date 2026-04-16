# LV2 Park — System Architecture
*Last updated: April 16, 2026*

---

## What This Is

lv2park.com answers one question: **Is LV2 parking in effect near Wrigley today?**

It's a static site hosted on GitHub Pages with a fully automated data pipeline. No server. No database. No manual work after setup. Everything runs on GitHub Actions cron jobs.

---

## Stack

| Layer | Tool | Cost |
|---|---|---|
| Hosting | GitHub Pages | Free |
| Automation | GitHub Actions | Free (2,000 min/mo) |
| Email (subscribers + digest) | Resend | Free up to 100/day |
| Form handling / subscribe API | Cloudflare Workers | Free |
| Subscriber log | Google Sheets | Free |
| Analytics | Google Analytics 4 | Free |
| Schedule data | MLB Stats API | Free, no key |
| Event data | Ticketmaster API | Free key |
| Domain | lv2park.com | ~$12/yr |

**Total monthly cost: ~$1/mo** (domain amortized)

---

## Repo Structure

```
lv2park/
├── index.html                  # Homepage (the product)
├── style.css                   # Global styles, all pages share this
├── app.js                      # Homepage JS: map, schedule, subscribe form
│
├── data/
│   ├── today.json              # Is LV2 active today? (auto-updated)
│   ├── week.json               # 7-day schedule (auto-updated)
│   ├── health.json             # Last fetch timestamp + status
│   ├── enforcement-today.json  # Live ticker output (game days only)
│   ├── ticker_state.json       # Ticket ID watermark for live scanner
│   ├── ticket-map-data.json    # FOIA 2018-2023 ticket counts by address
│   └── lv2-streets.geojson     # Street geometry for the map
│
├── scripts/
│   ├── fetch_data.py           # Pulls MLB + Ticketmaster schedule → data/
│   ├── scan_tickets.py         # Scrapes Chicago parking portal for live LV2 tickets
│   ├── send_digest.py          # Builds + sends Monday email broadcast via Resend
│   ├── check_traffic.py        # Checks GA4 weekly, sends FlexOffers reapply alert
│   └── generate_recaps.py      # Auto-generates game recap HTML pages
│
├── worker/
│   ├── index.js                # Cloudflare Worker: /subscribe, /contact, /unsubscribe
│   └── wrangler.toml           # Worker config (name: lv2park-email)
│
├── cloudflare-worker/
│   └── worker.js               # OLD worker — Google Sheets only, NOT active
│
├── game-recaps/                # Auto-generated per-game HTML pages (SEO)
│   └── YYYY-MM-DD-cubs-vs-*.html
│
├── resources/                  # Static resource pages (rules, map, data explorer, etc.)
├── blog/                       # Blog posts (what-is-lv2, data analysis)
│
└── .github/workflows/
    └── update.yml              # The automation brain — all cron jobs
```

---

## Automated Pipeline

### GitHub Actions — update.yml

Runs 4 times daily + manual trigger.

```
6 AM CT  ─── fetch_data.py
             send_digest.py       (Mondays only)
             check_traffic.py     (Mondays only)
             scan_tickets.py      (if LV2 active today)
             generate_recaps.py   (if yesterday had a game)
             git commit + push

3 PM CT  ─── same as above (catches postponements + afternoon enforcement)

5 PM CT  ─── same (enforcement window opens at 5 PM)

8 PM CT  ─── same (mid-enforcement scan)
```

### fetch_data.py
- Calls `statsapi.mlb.com` (free, no key) for Cubs home game schedule
- Calls Ticketmaster API (`TM_API_KEY`) for non-MLB events at Wrigley
- Determines if today is a game day and if LV2 should be active (games after 3 PM → LV2 5-10 PM)
- Writes `data/today.json` and `data/week.json`

### scan_tickets.py
- Only runs when `today.json` shows `lv2Active: true`
- Scrapes `parkingtickets.chicago.gov` — public Chicago e-hearing portal
- Probes a 7,500-ticket-ID window centered on today's known range
- Filters for RESIDENTIAL PERMIT violations on LV2-area streets
- Writes `data/enforcement-today.json` with live ticket count
- Updates `data/ticker_state.json` (window center shifts ~4,000 IDs/day)

### send_digest.py
- Runs every Monday at 6 AM CT
- Reads `data/week.json`, filters to next 7 days
- Builds HTML email with week schedule, LV2 badges, SpotHero CTA
- Creates Resend broadcast → sends to all subscribers in audience
- Warns Adam if subscriber count approaches Resend free tier limit (100 emails/day)

### check_traffic.py
- Runs every Monday at 6 AM CT
- Queries GA4 Data API for sessions in last 28 days
- Emails Adam weekly traffic status with progress bar toward FlexOffers threshold (500 sessions)
- Sends "reapply now" alert when 500 sessions/28d is crossed

### generate_recaps.py
- Runs 6 AM CT the morning after any game day
- Fetches: MLB game result + attendance, Cubs record on that date, weather from NWS (KMDW station)
- Pulls FOIA street data for historical context
- Loads scan log (`data/scans/YYYY-MM-DD.json`) if live data exists
- Generates static HTML to `game-recaps/YYYY-MM-DD-cubs-vs-TEAM.html`
- Committed to repo → live on GitHub Pages → indexed by Google

---

## Cloudflare Worker (lv2park-email)

Deployed at: `https://lv2park-email.adam-945.workers.dev`

**Endpoints:**
- `POST /subscribe` — validates email, adds to Resend audience, sends welcome email, logs to Google Sheets, notifies Adam
- `POST /contact` — forwards contact form to Adam via Resend
- `POST /unsubscribe` — marks unsubscribed in Resend, captures reason
- `POST /download-pdf` — adds to lead magnet audience, sends PDF link email

**Secrets set in Cloudflare dashboard:**
- `RESEND_API_KEY`
- `RESEND_AUDIENCE_ID`
- `NOTIFY_EMAIL`
- `GOOGLE_SA_JSON` (service account: lv2park@ew-playground.iam.gserviceaccount.com)
- `TURNSTILE_SECRET` (optional captcha)

**Old worker** (`cloudflare-worker/worker.js`, named `lv2park-worker`) — Google Sheets only, no longer used for subscribe. Do not redeploy.

---

## GitHub Secrets

Set at: github.com/asobl/lv2-parking-chicago > Settings > Secrets > Actions

| Secret | Used by | What it is |
|---|---|---|
| `TM_API_KEY` | fetch_data.py | Ticketmaster API key |
| `RESEND_API_KEY` | send_digest.py, check_traffic.py | Resend API key |
| `RESEND_AUDIENCE_ID` | send_digest.py | Resend audience ID for LV2 subscribers |
| `GOOGLE_SA_JSON` | check_traffic.py | Full service account JSON for GA4 + Sheets |
| `GA4_PROPERTY_ID` | check_traffic.py | Numeric GA4 property ID (not G-XXXXXXXX) |
| `TICKER_STATE` | (reference only — committed to repo instead) | Initial ticker window center |

---

## Email System

### Subscribe flow
1. User submits email on lv2park.com
2. Cloudflare Turnstile validates (captcha)
3. Worker POSTs to Resend `/audiences/{id}/contacts`
4. Worker sends welcome email via Resend
5. Worker appends row to Google Sheet (Subscribers tab)
6. Worker emails Adam notification

### Monday digest flow
1. GitHub Actions cron fires 6 AM CT Monday
2. `send_digest.py` reads `data/week.json` (already fresh from 6 AM fetch)
3. Builds HTML email with 7-day schedule
4. Creates Resend broadcast + sends to full audience

### Google Sheet log
Spreadsheet ID: `1-P5kFhUvi9JieiHoU9odhRa_HiekjkinnaAqPK27Fik`
Tabs: Subscribers, Searches, Street Lookups, Link Clicks

---

## SEO Content Pipeline

### Static pages (already live)
- `/resources/lv2-parking-rules/` — LV2 zone rules
- `/resources/lv2-parking-map/` — Interactive zone map
- `/resources/lv2-data-explorer/` — Street-level ticket lookup
- `/resources/cubs-game-day-parking/` — Game day parking guide
- `/resources/wrigley-field-parking-guide/` — Wrigley parking guide
- `/resources/wrigley-field-parking-shuttle/` — Shuttle guide
- `/resources/wrigley-divvy-scooters/` — Divvy + scooters
- `/resources/chicago-permit-zones-wrigley/` — Permit zones
- `/resources/wrigley-parking-ticket-data/` — Ticket data overview
- `/blog/what-is-lv2.html` — Explainer post
- `/blog/lv2-data-analysis.html` — FOIA data analysis

### Auto-generated (compounds over the season)
- `/game-recaps/YYYY-MM-DD-cubs-vs-TEAM.html` — One page per game, auto-published morning after

---

## Monetization Status

| Channel | Status | Notes |
|---|---|---|
| SpotHero affiliate | Paused | Need FlexOffers approval first |
| FlexOffers | Rejected (traffic too low) | Reapply when GA4 shows 500+ sessions/28d. Automated alert set. |
| Google AdSense | Not yet applied | Apply once traffic established |
| Email sponsorships | Future | Local businesses, parking garages near Wrigley |

---

## Key Data Asset

**FOIA file:** `/Users/asobol/Library/Mobile Documents/com~apple~CloudDocs/Desktop/Hobbies/FOIA_Sobol_A51907_20230828.xlsx`
- 9,434 LV2 tickets issued 2018–2023
- Already processed into `data/ticket-map-data.json` (8,046 geocoded)
- Powers the heat map, data explorer, street rankings, and recap pages
- Unique competitive asset — no other site has this data

---

## Trademarks / Legal

- No use of "Cubs," "Wrigley," or MLB logos in the site name or domain
- Team logos on recap pages loaded from `mlbstatic.com` CDN (same as fan sites)
- Footer disclaimer on every page: "Not affiliated with the Chicago Cubs, Wrigley Field, or the City of Chicago"
- Site name "LV2 Park" refers to the parking zone designation, not the team

---

## What's Not Built Yet

- **SMS/text alerts** (needs Twilio + phone field on subscribe form)
- **Change alerts** (email when game time changes or LV2 status flips mid-week)
- **Street-level pages** (`/streets/n-marshfield-ave/`) — FOIA data ready, generator not built
- **Season summary page** — running ticket totals, YoY comparison
- **SpotHero + AdSense** — pending FlexOffers approval
