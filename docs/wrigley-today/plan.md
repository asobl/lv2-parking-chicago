# LV2 Park -- Build Plan

**Domain:** lv2park.com
**Status:** Ready to build
**Estimated build time:** 1 hour
**Last updated:** April 15 2026

---

## What It Does

A mobile-first single-page website that answers: "Is there a game or event at Wrigley today, and is LV2 in effect?"

Five sections on one page:
1. **Today** -- YES/NO, event name, time, LV2 status
2. **This Week** -- 7-day list of events and LV2 days
3. **The LV2 Map** -- zone boundaries + FOIA heat map of most-ticketed streets
4. **Parking + Getting There** -- SpotHero affiliate, CTA info, free shuttle
5. **Neighborhood Resources** -- alderman links, hotline, email signup, contact form

Works on phone and desktop. No login. No app to download. Loads in under 2 seconds.

---

## Technical Architecture

### Stack

```
GitHub Pages           Static HTML/CSS/JS served free
GitHub Actions         Daily cron at 6 AM CT -- fetches APIs, writes JSON
MLB Stats API          Free, no key -- Cubs home game schedule
Ticketmaster API       Free key -- concerts and events at Wrigley
Leaflet.js + OSM       Free map tiles -- LV2 zone + heat map
Resend                 Email -- weekly digest + signup confirmation (free: 3k/mo)
```

### How the daily update works

```
GitHub Actions cron (daily 6:00 AM CT):
  1. Call MLB Stats API
     GET statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=112
     Filter: is today's game at Wrigley Field (home)?
  2. Call Ticketmaster API
     GET discovery/v2/events.json?venueId=KovZpZAFlktA
     Filter: events in the next 7 days
  3. Merge results
  4. Write /data/today.json
  5. Write /data/week.json
  6. Commit + push to repo
  7. GitHub Pages picks up automatically

Page (index.html):
  On load: fetch('/data/today.json')
  Render YES/NO block, LV2 status, week view
  FOIA heat map = static /data/lv2-heatmap.geojson (never changes)
```

### today.json shape

```json
{
  "date": "2026-04-17",
  "updated": "2026-04-17T11:00:00Z",
  "hasEvent": true,
  "lv2Active": true,
  "events": [
    {
      "type": "game",
      "name": "Cubs vs. Mets",
      "time": "1:20 PM",
      "timeUtc": "2026-04-17T18:20:00Z"
    }
  ]
}
```

### week.json shape

```json
{
  "updated": "2026-04-17T11:00:00Z",
  "days": [
    {
      "date": "2026-04-17",
      "dayLabel": "Fri Apr 17",
      "hasEvent": true,
      "lv2Active": true,
      "events": [{ "name": "Cubs vs. Mets", "time": "1:20 PM" }]
    },
    {
      "date": "2026-04-18",
      "dayLabel": "Sat Apr 18",
      "hasEvent": false,
      "lv2Active": false,
      "events": []
    }
  ]
}
```

### MLB API fallback chain

The daily script tries three layers in order:

```
1. MLB Stats API (primary)
   GET statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=112
   Free, no key, has been stable for years.

2. ESPN Public API (fallback -- no key required)
   GET site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/16/schedule
   teamId 16 = Chicago Cubs. Also free, also widely used.

3. Keep existing data (last resort)
   If both APIs fail: do NOT overwrite today.json or week.json.
   Write health.json with { "status": "error", "source": "stale" }.
   GitHub Actions failure email alerts Adam automatically.
   Site shows previous day's data -- stale but not broken.
```

In `fetch_data.py`:
```python
def fetch_mlb_schedule():
    try:
        # Primary: MLB Stats API
        resp = requests.get(MLB_URL, timeout=10)
        resp.raise_for_status()
        return parse_mlb(resp.json()), "mlb"
    except Exception:
        pass
    try:
        # Fallback: ESPN public API
        resp = requests.get(ESPN_URL, timeout=10)
        resp.raise_for_status()
        return parse_espn(resp.json()), "espn"
    except Exception:
        return None, "error"   # Caller skips file write on None
```

**Why this matters:** The site's core promise is "know before you leave the house." Showing yesterday's correct data is far better than showing no data or a broken page. The disclaimer already covers imperfect sources.

---

### LV2 active logic

```
lv2Active = hasEvent AND current time < 10:00 PM CT
```
LV2 enforcement window is 5 PM to 10 PM. Site shows "LV2 ACTIVE" all day as a heads-up, then the detail says "5 PM - 10 PM."

### Monitoring

- GitHub Actions failure = GitHub emails Adam automatically
- Uptime Robot (free): pings lv2park.com every 5 min, texts/emails if down
- Page shows "Last updated: [timestamp from today.json]" -- glance and know it ran
- `/data/health.json` endpoint: returns last run time + API status

### Repo structure

```
/
├── index.html          Main page
├── style.css           All styles
├── app.js              Fetch + render logic
├── data/
│   ├── today.json      Written by Actions daily
│   ├── week.json       Written by Actions daily
│   ├── health.json     Written by Actions daily
│   └── lv2-heatmap.geojson   Static -- from FOIA data
├── .github/
│   └── workflows/
│       └── update.yml  Daily cron job
└── blog/
    └── lv2-data-analysis.html   First blog post
```

### GitHub Actions workflow (update.yml)

```yaml
name: Daily Data Update
on:
  schedule:
    - cron: '0 11 * * *'   # 11 AM UTC = 6 AM CT
  workflow_dispatch:         # Manual trigger for testing

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install requests pytz
      - run: python scripts/fetch_data.py
        env:
          TM_API_KEY: ${{ secrets.TM_API_KEY }}
      - run: |
          git config user.name "lv2park-bot"
          git config user.email "bot@lv2park.com"
          git add data/
          git diff --staged --quiet || git commit -m "Daily update $(date -u +%Y-%m-%d)"
          git push
```

---

## Page Sections (What Gets Built)

### Section 1: Today (above the fold, mobile)

Full-width card. No scrolling required to see the answer.

```
LV2 PARK

[YES]                        [NO]
Cubs vs. Mets                No game.
1:20 PM                      No events.
                             Wrigley is quiet.
LV2: ACTIVE 5-10 PM
[Book parking -- from $15]
```

- YES/NO rendered in 72px+ bold type. Unmissable.
- LV2 status: one line, bold. Red pill if active, green pill if not.
- SpotHero button: full width on mobile, fires whenever hasEvent = true.
- Card background changes by state: warm yellow tint on game days, cool white on quiet days.

### Section 2: This Week

Clean 7-row list. One row per day.

```
Fri Apr 17  Cubs vs. Mets, 1:20 PM      LV2
Sat Apr 18  --                           --
Sun Apr 19  Cubs vs. Mets, 1:20 PM      LV2
Mon Apr 20  --                           --
...
```

LV2 badge shown in orange on active days. Empty days show a dash.
Tappable rows -- tap expands to show full event details + parking link.

### Section 3: The LV2 Map

Leaflet.js map, no API key needed (OpenStreetMap tiles).

Layers:
- LV2 zone boundary (purple outline, light purple fill)
- Zone 383 boundary (blue outline)
- Game-day street closures (red dashed)
- Security perimeter (orange)
- FOIA heat map overlay (color gradient -- red = most ticketed, yellow = medium)
- Marker: Wrigley Field pin

Below map: "Since 2018, over 9,400 cars have been ticketed in the LV2 zone. The red streets above are where it happens most."

### Section 4: Parking + Getting There

Three cards, tap to expand:

1. **Book Parking** -- SpotHero affiliate link, "from $15/game"
2. **Take the Red Line** -- Addison stop, 2-min walk, no parking stress
3. **Free Cubs Shuttle** -- 4650 N. Clarendon, starts 2 hrs before first pitch

### Section 5: Neighborhood Resources

Two link cards + email signup:

- 44th Ward Alderman (Bennett Lawson) -- permits, LV2 questions
- 46th Ward Alderman (Angela Clay) -- LV2 west area
- Tow inquiry: 311 or call 773-265-7605 (Auto Pound #6)
- Cubs game day hotline: 866-4-CPD-TOW

**Email signup:**
```
Get the week at Wrigley every Monday.
[your email]  [Subscribe]
```

**Contact form:**
```
Chicago neighborhood problem? We can help.
[Name] [Email] [Message]  [Send]
```

### Disclaimer (footer, always visible)

Short, honest, not scary. Placed in the footer on every page.

```
LV2 Park pulls from the MLB schedule and Ticketmaster -- the same sources
the 44th Ward uses to post LV2 enforcement dates. We cover games, concerts,
and most major events. Private and corporate events at Wrigley may not appear.
When in doubt, verify at mlb.com/cubs/schedule or the 44th Ward site.
```

Tone: matter-of-fact, not overly legal. Users appreciate honesty more than
a wall of CYA text. One short paragraph is enough.

**Why "same sources the 44th Ward uses" matters:** It's true and it's credibility.
The alderman doesn't have a secret list -- they post LV2 enforcement based on
the Cubs and Ticketmaster calendars. We're not guessing.

---

## Design System

**Named aesthetic: "Chicago Street Signal"**
Bold, clear, functional. Like a traffic sign crossed with a neighborhood bulletin board. Readable from across the street. Not corporate. Not flashy. Instantly clear.

This comes from the user's screenshots: extra-bold type + warm yellow + purple/periwinkle + white base + rounded cards. All four images share these elements.

---

### Colors

**The two states drive everything:**
- Game day / LV2 active = warm, urgent, yellow-forward
- Quiet day = calm, cool, white-forward

```
Background (60%):
  --color-bg:         #FFFFFF
  --color-bg-warm:    #FFFBF0    /* game day tint */
  --color-bg-surface: #F5F4F0    /* cards on white */

Text (30%):
  --color-text:       #1A1A2E    /* near-black, not pure black */
  --color-text-soft:  #6B6B80    /* secondary/captions */

Accents (10%):
  --color-yellow:     #F5E030    /* game day, LV2 active -- from screenshots 1 and 4 */
  --color-purple:     #6B64D4    /* CTAs, SpotHero button -- from screenshots 2 and 4 */
  --color-green:      #5B9EA0    /* quiet day, "no event" calm state */
  --color-orange:     #F0A030    /* tow warning, LV2 active pill */
  --color-red:        #E84040    /* FOIA heat map hot streets, tow alert */

Semantic:
  --color-lv2-active:  var(--color-orange)
  --color-lv2-quiet:   var(--color-green)
  --color-yes:         var(--color-yellow)
  --color-no:          var(--color-green)
```

**From the books (Galitz):** 60-30-10 rule. White dominant. Two accent colors max per screen. Color encodes state -- yellow = alert/active, green = safe/quiet. Never rely on color alone -- always pair with text label.

---

### Typography

**From screenshots:** Adam's image 4 (PunchCard Branding) shows a very heavy black-weight sans-serif. That's the dominant taste signal. Pair with a clean regular-weight body font from the same family.

```
--font-heading: 'Inter', system-ui, sans-serif  /* weights: 900 Black for hero, 700 Bold for section heads */
--font-body:    'Inter', system-ui, sans-serif  /* weight: 400 Regular */
```

**Why Inter:** Free (Google Fonts), has a true Black (900) weight that matches the PunchCard screenshot, excellent screen legibility at all sizes, wide language support.

**Type scale (Galitz minimum sizes applied):**

```css
--text-hero:    72px / 900 weight   /* YES / NO answer -- unmissable */
--text-h1:      36px / 700 weight   /* section titles */
--text-h2:      24px / 700 weight   /* card titles, event names */
--text-body:    17px / 400 weight   /* body text -- Galitz minimum for mobile */
--text-small:   14px / 400 weight   /* captions, timestamps */
--text-label:   12px / 700 weight   /* ALL CAPS labels only -- LV2, STATUS */
```

**From the books (Banga & Weinhold):** Bold typography IS hierarchy. The YES/NO answer at 72px/900 weight is not decorative -- it is the entire purpose of the screen. User should never have to look for the answer.

---

### Spacing and Radius

```css
--radius-sm:    8px    /* small badges, pills */
--radius-md:    16px   /* cards, inputs */
--radius-lg:    24px   /* hero card, main YES/NO block */

--space-xs:     4px
--space-sm:     8px
--space-md:     16px
--space-lg:     24px
--space-xl:     40px

--content-max:  640px  /* max width on desktop -- stays readable */
--content-pad:  20px   /* side padding on mobile */
```

Generous rounded corners throughout -- consistent with all four screenshot examples.

---

### Component Patterns

**The hero card (YES state):**
- Background: --color-bg-warm (#FFFBF0)
- Yellow accent bar or top border: 6px solid --color-yellow
- YES: 72px / 900 weight / --color-text
- Event name: 24px / 700
- Time: 17px / 400 / --color-text-soft
- LV2 pill: orange background, white text, --radius-sm
- SpotHero button: full width, --color-purple background, white text, --radius-md, 56px height (Fitts's Law -- Galitz minimum 44pt touch target)

**The hero card (NO state):**
- Background: white
- Green accent bar
- NO: 72px / 900 weight / --color-green
- "Wrigley is quiet." -- 17px body

**Week row:**
- Row height: 56px (comfortable touch target)
- LV2 badge: orange pill, right-aligned
- Empty day: text-soft color, no badge

**SpotHero button:** Full-width on mobile. Purple (#6B64D4). White text. 56px height. "Book parking -- from $15" with right arrow. Fires on YES days only.

---

## Monetization

### Revenue stack (in launch order)

**1. SpotHero Affiliate (day 1)**
- Apply at: spothero.com/affiliate
- Pays per completed booking, ~$3-8 per booking
- Button shown prominently whenever hasEvent = true
- Also in weekly email on game days
- Est: $100-400/mo at steady state

**2. Google AdSense (week 1)**
- Apply at: adsense.google.com
- Add one ad unit below the week view -- non-intrusive
- Est: $50-200/mo after 3-6 months SEO traction
- Note: AdSense approval requires live site with real content -- apply after launch

**3. Email list sponsorship (month 3+)**
- Once list hits 500+ local subscribers
- Target sponsors: neighborhood bars, restaurants, ride apps
- "This email presented by [Old Crow Smokehouse]" -- $100-300/send
- Weekly send = $400-1,200/mo at scale

**4. ParkWhiz as backup affiliate**
- Same model as SpotHero, different inventory
- Add as secondary link if SpotHero not available for a specific event

### Revenue projection

| Month | Source | Est. |
|---|---|---|
| 1-2 | SpotHero only | $50-150 |
| 3 | SpotHero + AdSense | $150-350 |
| 6 | All three | $300-700 |
| 12 | All three + sponsorship | $500-1,200 |

---

## Email Infrastructure

### Platform: Resend

**NOT SendGrid.** SendGrid eliminated its free tier in May 2025. Only a 60-day trial now, then $19.95/mo.

**Resend free tier:** 3,000 emails/month, 100/day, no expiry, no credit card. Full API. Works perfectly for early-stage. When list grows past ~500 active subscribers, upgrade to Resend Pro ($20/mo for 50k/mo).

Register at: resend.com

**Two email types:**

**1. Signup confirmation (transactional)**
- Triggered: immediately on form submit
- From: hello@lv2park.com
- Subject: "You're in -- here's what LV2 Park does"
- Body: quick explainer + next Monday's schedule preview
- Triggered via Cloudflare Worker on form POST

**2. Weekly digest (marketing)**
- Triggered: every Monday at 8:00 AM CT via GitHub Actions cron
- From: hello@lv2park.com
- Subject: "LV2 Park: Week of [date]"
- Body:

```
Week of April 14-20 at Wrigley

Mon Apr 14  Nothing
Tue Apr 15  Nothing
Wed Apr 16  Cubs vs. Phillies, 7:05 PM -- LV2 ACTIVE
Thu Apr 17  Cubs vs. Phillies, 1:20 PM -- LV2 ACTIVE
Fri Apr 18  Cubs vs. Mets, 1:20 PM
Sat Apr 19  Cubs vs. Mets, 1:20 PM
Sun Apr 20  Cubs vs. Mets, 1:20 PM

4 LV2 days this week. Book parking for Wednesday: [SpotHero link]

LV2 permit questions? 44th Ward: [link]
Neighborhood issue? Reply to this email.

---
lv2park.com -- Unsubscribe
```

**Email signup flow:**
1. User enters email in form on site
2. POST to a Cloudflare Worker (free tier -- 100k req/day)
3. Worker calls Resend Contacts API to add to audience
4. Worker calls Resend API to send confirmation email
5. Weekly cron (GitHub Actions) calls Resend Batch Send API to send digest to full audience

**Why Cloudflare Worker for form submit:**
GitHub Pages is static -- it can't run server-side code. The Worker is 5 lines, free, and handles the Resend API call without exposing the API key in client-side JS.

**Resend setup needed:**
- Sign up at resend.com (free, no card)
- Verify sending domain: lv2park.com (DNS TXT record in GoDaddy)
- Create Audience: "lv2park-subscribers"
- API key scoped to: full access (store in Cloudflare Worker env var -- never in code)
- Note: 100/day limit on free tier. Weekly digest to 100+ subscribers = fine. At 500+ subscribers, upgrade to Pro ($20/mo).

---

## Data Gap Solutions

Three sources MLB and Ticketmaster can't cover. Here's how to handle each.

### Gap 1: Private and corporate events at Wrigley

**The problem:** wrigleyfieldevents.com manages private bookings (corporate events, film shoots, etc.). No public calendar, no API, no scrapeable page.

**Solution: Manual override file + community flag**

Add `data/overrides.json` to the repo. Format:

```json
{
  "overrides": [
    {
      "date": "2026-05-10",
      "name": "Private event at Wrigley",
      "time": "TBD",
      "type": "private",
      "source": "manual",
      "lv2": true
    }
  ]
}
```

`fetch_data.py` merges overrides into the event list. Adam edits this file when he sees a private event announced on social media, NextDoor, or 44th Ward posts.

Add a "Report a missing event" link in the footer -- a simple mailto or contact form. Users who live in the neighborhood WILL tell you when there's an event the site missed. This is distributed community QA.

**In practice:** Private corporate events are rare. When they do happen, the 44th Ward typically posts about LV2 enforcement on their site and social. That's the signal to update the override file.

---

### Gap 2: Gallagher Way events

**The problem:** Gallagher Way is the outdoor plaza adjacent to Wrigley (not inside the stadium). It runs the Budweiser Concert Series. Separate entity from the Cubs. No confirmed Ticketmaster venue ID yet.

**Key question answered:** Gallagher Way events generally do NOT trigger LV2 enforcement. LV2 is tied to Cubs home games and major Wrigley stadium events -- not the small outdoor plaza concerts next door.

**Solution: Informational display only (no LV2 flag)**

Pull Gallagher Way events from their website (gallagherway.com/events) manually or via overrides.json. Show them as a separate line:

```
Also at Gallagher Way (next door):
OK Go -- June 13, 7:00 PM (no LV2)
```

Label clearly as "no LV2." Useful context for the neighborhood without false alarm.

If Gallagher Way grows in event frequency, revisit scraping their calendar.

---

### Gap 3: Last-minute schedule changes (postponements, rain delays)

**The problem:** The daily cron runs at 6 AM. A rain postponement could be called at 2 PM. Users checking the site after 2 PM would see wrong info.

**MLB API status values** (confirmed from API response):
- `Scheduled` -- game is on as planned
- `Pre-Game` -- within 2 hours of first pitch
- `In Progress` -- game underway
- `Delayed` -- weather delay, clock running
- `Postponed` -- rescheduled to another day
- `Cancelled` -- game will not be played
- `Suspended` -- game stopped, to be continued
- `Final` -- game complete

**Solution: Status-aware rendering + second daily run on game days**

In `fetch_data.py`:
- Check `status` field for each game
- If `Postponed` or `Cancelled`: set `hasEvent = false`, `lv2Active = false`, add `"note": "Game postponed"` to today.json
- If `Delayed`: keep `hasEvent = true`, `lv2Active = true`, add `"note": "Rain delay -- check back"`

In `update.yml`, add a second cron trigger for game days at 3 PM CT (20:00 UTC):

```yaml
on:
  schedule:
    - cron: '0 11 * * *'   # 6 AM CT daily
    - cron: '0 20 * * *'   # 3 PM CT daily (catches afternoon postponements)
  workflow_dispatch:
```

Running the workflow twice on game days adds ~4 min/month to Actions usage. Still free, still unlimited on public repos.

The `workflow_dispatch` trigger (already in the YAML) also lets Adam manually re-run the workflow from GitHub if something changes and he wants an immediate update.

---

## Build Sequence

Everything below = ~1 hour of build time.

| Step | What | Time |
|---|---|---|
| 1 | Register lv2park.com on GoDaddy | DONE |
| 2 | Create GitHub repo, enable Pages | 5 min |
| 3 | Get Ticketmaster Discovery API key (developer.ticketmaster.com) | 5 min |
| 4 | Sign up at resend.com, verify lv2park.com domain | 10 min |
| 5 | Write fetch_data.py (MLB + TM + overrides → JSON) | 15 min |
| 6 | Write update.yml (two crons: 6 AM + 3 PM CT) | 5 min |
| 7 | Build index.html + style.css + app.js | 20 min |
| 8 | Process FOIA Excel → lv2-heatmap.geojson | 10 min |
| 9 | Add Leaflet map + GeoJSON layer | 10 min |
| 10 | Set up Cloudflare Worker for email form (calls Resend) | 10 min |
| 11 | Set GitHub Secrets: TM_API_KEY, RESEND_API_KEY | 2 min |
| 12 | Set up Uptime Robot monitoring | 5 min |
| 13 | Submit sitemap to Google Search Console | 5 min |
| **Total** | | **~1.5 hrs** |

---

## Decisions Still Open

| Decision | Options | Recommendation |
|---|---|---|
| AdSense timing | Apply now vs. after 90 days of traffic | After launch -- need live content first |
| SpotHero vs. ParkWhiz | Apply to both | SpotHero primary, ParkWhiz backup |
| Blog post format | Standalone HTML page vs. simple /blog/ directory | Standalone HTML, link from footer |
| Second FOIA (2023-present) | File now vs. after launch | After launch -- gives you fresh content for Year 2 |
| Future venues | Guaranteed Rate, United Center | Park idea, revisit at 6-month mark |

---

## Open Questions (Resolved)

- Domain: lv2park.com (decided)
- Hosting: GitHub Pages (decided)
- Daily update: GitHub Actions cron (decided)
- Email: Resend, not SendGrid -- SendGrid free tier gone May 2025 (decided)
- Map: Leaflet + OpenStreetMap, free (decided)
- Repo: Public (decided -- Pages free on public repos)
- Trademark: No "Wrigley" or "Cubs" anywhere in domain or prominent branding (decided)
- LV2 active logic: hasEvent = true AND time < 10 PM CT (decided)
- Ticketmaster API to register for: Discovery API, public tier (decided)

---

## Validation Pass

Run per `.claude/rules/technical-plan-validation.md`. Completed April 15 2026.

| Component | Current? | Math? | Security? | Breaks? | Simpler? | Sources |
|---|---|---|---|---|---|---|
| GitHub Pages | Yes, free for public repos | 1GB soft limit on repo; 100GB bandwidth/mo. This site will never approach either. | All code public by design. API keys never in repo. | GitHub TOS change (low risk). | Already simplest. | [GitHub Docs](https://docs.github.com/en/actions/concepts/billing-and-usage) |
| GitHub Actions | Yes, **unlimited free minutes on public repos** (March 2026 pricing change doesn't affect standard runners on public repos) | 2 runs/day × ~2 min = ~120 min/month. Against unlimited. Zero cost. | GITHUB_TOKEN needs write permission to push data/ files. Secrets encrypted at rest. | Workflows auto-disabled after 60 days of no commits. The daily cron itself keeps the repo active. workflow_dispatch also available as backup. | Already simplest. | [GitHub Actions Billing](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions) |
| MLB Stats API | Confirmed live, no key, free. No formal SLA published. | 2 calls/day. No rate limit documented. | Read-only public API, no credentials required. | No SLA. MLB could add auth or deprecate endpoint. **Mitigated:** ESPN public API as fallback (also free, no key). If both fail: keep existing JSON, don't overwrite. Site shows stale data rather than breaking. | Already simplest. | [UNVERIFIED for SLA] |
| Ticketmaster Discovery API | Yes, free tier active. 5,000 req/day, 5 req/sec. | 2 calls/day. Limit: 5,000/day. Using 0.04% of quota. | API key in GitHub Secrets. Never in client-side code. | Venue ID (KovZpZAFlktA) could change if TM restructures their database. Verify annually. | Already simplest. | [developer.ticketmaster.com](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/) |
| Leaflet.js + OpenStreetMap | Yes, both active, free. | OSM tiles: free for low-traffic use. Heavy use requires notification to OSM. This site qualifies as low-traffic. | CDN dependency for Leaflet. Pin to a specific version to avoid surprise breaking changes (e.g. `leaflet@1.9.4`). | OSM could require tile API keys for any use (not current policy). Fallback: Stadia Maps free tier. | Already simplest. | [leafletjs.com](https://leafletjs.com), [openstreetmap.org/tile_usage_policy](https://operations.osmfoundation.org/policies/tiles/) |
| SendGrid (original plan) | **BLOCKED. Free tier eliminated May 27 2025.** Only a 60-day trial remains, then $19.95/mo. | N/A | N/A | N/A | **Replaced with Resend.** | [Twilio Changelog](https://www.twilio.com/en-us/changelog/sendgrid-free-plan) |
| Resend (replacement) | Yes, free tier active. 3,000 emails/month, 100/day, no expiry. | Weekly digest to 100 subscribers = 100 emails/week. Under daily limit. At 500+ subscribers, upgrade to Pro ($20/mo for 50k/mo). | API key in Cloudflare Worker env var. Never in client-side code or GitHub repo. | 100/day cap: a Monday send to 101+ subscribers would fail on the free tier. Upgrade path is clear and cheap. | Simpler than SendGrid setup. No legacy template system. | [resend.com/pricing](https://resend.com/pricing) |
| Cloudflare Workers | Yes, 100,000 req/day free, no expiry, no credit card. | Email signups: maybe 5-50/day at peak. 0.05% of quota. | API key stored in Worker env var. Must configure CORS headers to only accept POST from lv2park.com. | CORS misconfiguration could expose endpoint to abuse. Easy to lock down. | Could use Formspree, but Worker gives CORS control + no branding. 5 lines of code. | [developers.cloudflare.com/workers/platform/limits](https://developers.cloudflare.com/workers/platform/limits/) |

### Utopian Vision

A service that knows about every event at and around Wrigley in real time, proactively pushes notifications to subscribers the moment anything changes (postponement, rain delay, new event added), and requires zero human maintenance once deployed. The current plan is within one feature of this ideal -- the only gap is same-day schedule changes after 6 AM require waiting for the 3 PM cron run or a manual `workflow_dispatch` trigger. Everything else is essentially the utopian version.

### Validation Score: 9/10

**Deductions:**
- -1: Resend 100/day free tier limit. Not a launch blocker. Upgrade to Pro ($20/mo) when list passes 100 subscribers.

**No blockers.** MLB API risk mitigated with ESPN fallback + stale-data failsafe.

**No blockers.** Ready to build.
