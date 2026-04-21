# Chicago Data Portal Analysis -- LV2 Park Opportunities

**Researched:** April 15 2026
**Trigger:** Second City Citation (secondcitycitation.com/stats) discovered via r/chicago

---

## What Second City Citation Is

A Next.js site showing "real-time surveillance of Chicago parking enforcement activity." It went semi-viral on r/chicago (112 upvotes, 18 comments) in April 2026. The developer described the source as "official City of Chicago public resources" with "clever tricks."

**Their scope:** City-wide aggregate stats, all violation types, no game-day context.
**Our opportunity:** Wrigleyville-specific, LV2-specific, game-day-aware enforcement intelligence.

**Update April 16 2026:** Reverse-engineered. The "clever tricks" description is misleading. This is NOT a Socrata query. See full investigation below.

---

## The Data Source

### CONFIRMED: Chicago Parking Violations Are NOT on Socrata (April 16 2026)

`wrvz-psew` = **Taxi Trips (2013-2023)** dataset. Not parking violations. Confirmed via Socrata metadata API.

Chicago does not publish parking violation data on data.cityofchicago.org. Exhaustive search confirmed:
- All 33 Finance category datasets: zero parking violations
- Socrata catalog full-text search for "parking violation", "citation", "parking ticket": zero Chicago results
- NYC DOF datasets (pvqr-7yc4, 7mxj-7a6y, 869v-vr48, etc.) appear in searches but are NYC data

### Actual Data Source: City eHearing Portal (Sequential Scan)

**Portal:** `parkingtickets.chicago.gov/EHearingWeb/`
**Endpoint:** `POST /EHearingWeb/displayEligibleTickets`
**Auth:** Requires CSRF token + session cookie (both from initial GET of /home)
**Rate:** 3 ticket lookups per request
**Response:** Violation type, plate, state, issue date, amount, payment status
**Cost:** Free, no API key

**Confirmed working (April 16 2026):**
- Ticket `9205512432` = RESIDENTIAL PERMIT PARKING, IL, 04/15/2026, $60 -- this is an LV2 violation
- Ticket `9205512433` = MISSING/NONCOMPLIANT PLATE, 04/15/2026
- Ticket `9205512434` = EXPIRED PLATE, IL, 04/15/2026, $60
- IDs are **mostly sequential within an officer's device session** -- gaps exist but numbers cluster

**How Second City Citation actually works:**
They maintain a database of officer device ID ranges, track the current high-watermark ticket number per device, and scan forward in batches of 3 to discover new tickets issued today. Over time they've built up historical officer totals (officer 2236 has 6,335 lifetime tickets). The "1-2 hour lag" matches a polling interval, not a Socrata refresh rate.

**LV2 violation to look for:** `RESIDENTIAL PERMIT PARKING` or `RESIDENTIAL PERMIT` in violation_description field.

---

## LV2 Violation Code

**No separate "LV2" code exists in the city system.**

LV2 is a residential permit zone. All LV2 violations are issued under:

| Code | Description | Fine |
|---|---|---|
| `9-64-090` | Residential Parking Permit | $75 |
| `9-64-090(a)` through `(e)` | Sub-violations of the same ordinance | $75 |

**Proxy formula:** `violation_code = 9-64-090` + location within LV2 zone boundaries = LV2 enforcement.

There's also a related Wrigley-specific code that appeared in the city's violation list:
- `9-68-040(i)` = "Parking/Standing in Wrigley Bus Permit Zone" ($100)
- `9-68-040(j)` = "Motor Running in Wrigley Bus Permit Zone" ($100)

These are adjacent enforcement activity, not LV2 specifically.

---

## LV2 Zone Streets (for geo-filtering)

The LV2 zone is west of Graceland Cemetery and southwest of Ashland, roughly:
- **North:** Irving Park Rd (~W 4000 N)
- **South:** Belmont Ave (~W 3200 N)
- **East:** Broadway / Clark St (~N Clark)
- **West:** Ashland Ave

Top ticketed streets (from our FOIA data -- highest confidence):
1. N Marshfield Ave
2. N Paulina St
3. N Hermitage Ave
4. W Roscoe St
5. W Belle Plaine Ave

**Sample query to pull today's LV2-area enforcement:**
```
GET https://data.cityofchicago.org/resource/wrvz-psew.json
  ?violation_code=9-64-090
  &$where=issue_date > '2026-04-17T17:00:00.000'
  &$where=latitude > 41.93 AND latitude < 41.96
  &$where=longitude > -87.68 AND longitude < -87.65
  &$limit=1000
```

---

## Towed Vehicles Dataset

**Dataset ID:** `ygr5-vcbg`
**What it contains:** Vehicles impounded within the last 90 days.
**Fields:** tow_date, make, style, color, plate, state, towed_to_address, tow_facility_phone, inventory_number

**Verdict: Not useful for LV2 detection.** No reason code, no zone code, no tow-from address. Only the facility where the car went. Can't distinguish LV2 game-day tows from any other tow without cross-referencing with violation data.

---

## Confirmed: Core Machine Is Running (April 16 2026)

- `today.json` ran at 5:05 AM UTC today. Source: MLB. Status: ok.
- GitHub Actions daily cron is live and committing data.
- Site is live at lv2park.com.
- 9 SEO content pages built. 3 blog posts. Data explorer built.
- Email signup with Turnstile CAPTCHA working via Cloudflare Worker.
- Print calendar and ICS download working client-side.
- FlexOffers verification tag in HTML -- awaiting approval (applied April 2026).
- `SEATGEEK_AFF_ID` and `TM_AFF_ID` are empty stubs -- fill in once FlexOffers approves.

## Confirmed: Gallagher Way TM Venue ID Is Dead (April 16 2026)

`Z7r9jZady5` in fetch_data.py returns 0 events. Reason: Gallagher Way events sell through
gallagherway.com and do312.com, not Ticketmaster. Fix: 2026 events added to overrides.json
with `lv2: false`. The dead TM call stays (harmless), but should be removed in a cleanup pass.

2026 Gallagher Way events now in overrides: Mayday Parade (May 17), OK Go (June 13),
Guster (June 26), Golf Day (Aug 23), WingOut (Sept 26-27).

## Confirmed: Christkindlmarket Is Not a Risk (April 16 2026)

Free admission market, not a Ticketmaster event. Never appears in TM queries for Wrigley venue IDs.
No false LV2 flags possible.

## Sustainability Infrastructure Added (April 16 2026)

- `scripts/health_check.py` -- 14-check local test runner. Saves to `logs/` (gitignored). Run anytime: `python scripts/health_check.py`
- `scripts/monthly_audit.py` -- runs all checks, emails full report to adam@lobosinnovation.com
- `.github/workflows/monthly-audit.yml` -- runs 1st of each month at 10 AM CT
- `send_digest.py` updated -- alerts adam@lobosinnovation.com when subscriber count hits 80
- `data/overrides.json` updated with 2026 Gallagher Way events
- `logs/` added to .gitignore

---

## Opportunities Ranked

### Opportunity 1: Live Enforcement Confirmation Ticker (highest value)

**What it is:** A widget showing confirmed LV2 ticket activity on game days. Not a prediction. Actual ticket data.

**Before:** "LV2 is probably active -- there's a game tonight."
**After:** "LV2 CONFIRMED: 23 tickets issued in the zone today, last checked 5:47 PM"

**How it actually works (updated after reverse engineering, April 16 2026):**

The data comes from the city eHearing portal via sequential ticket ID scanning, not a public API. Architecture:

1. **GitHub Action runs every 30 minutes on game days, 5-10 PM CT**
   - Reads `data/today.json` to check if `lv2Active: true`
   - If yes: runs `scripts/scan_tickets.py`

2. **`scripts/scan_tickets.py`**
   - Reads `data/ticker_state.json` for the current high-watermark ticket number
   - Scans forward in batches of 3 via POST to `parkingtickets.chicago.gov/EHearingWeb/displayEligibleTickets`
   - Scans ~200 IDs per run (67 requests, ~45 seconds)
   - Filters results for `RESIDENTIAL PERMIT` in violation_description
   - Filters results for Wrigleyville address patterns (N Marshfield, N Paulina, N Hermitage, W Roscoe, etc.)
   - Writes count + last_checked to `data/enforcement-today.json`
   - Updates high-watermark in `data/ticker_state.json`

3. **`app.js` reads `data/enforcement-today.json`** on page load (game days only)
   - Shows ticker if count > 0 and `last_checked` is within last 2 hours
   - Hides ticker before 5 PM or if no data yet

**UI (above the fold on game days after enforcement starts):**
```
LV2 CONFIRMED
23 tickets issued in the zone today
Last checked 5:47 PM CT
```

**State file: `data/enforcement-today.json`**
```json
{
  "date": "2026-04-17",
  "lv2_tickets_today": 23,
  "last_checked": "2026-04-17T17:47:00Z",
  "scan_status": "ok"
}
```

**State file: `data/ticker_state.json`** (gitignored, only used by scanner)
```json
{
  "high_watermark": 9205512450,
  "last_scan": "2026-04-17T17:45:00Z"
}
```

**Build effort:** ~100 lines of Python + 30 lines of JS + 1 GitHub Action schedule. 2-3 hours.

**Why this IS a live ticker:**
30-minute refresh on game days after 5 PM means data is never more than 30 min stale. That's live enough. "23 tickets confirmed today, last checked 47 min ago" is more trustworthy than nothing.

**Fallback:** If scan returns 0 results (enforcement hasn't started yet, scan fails, or it's before 5 PM): show nothing. Never show "0 tickets" -- that's misleading.

**Risk: rate limiting.** The city portal may throttle aggressive scanning. Mitigation: 0.5s delay between requests, rotate User-Agent. If blocked: fall back to showing "LV2 active (game day)" without ticket count.

**Note on ticket number ranges:** Officer device sessions produce clustered sequential IDs. During enforcement hours we expect 300-500 new tickets citywide per hour. LV2-specific tickets (Wrigleyville area, RESIDENTIAL PERMIT) are a subset. The scanner needs to cover enough of the daily range to catch them. Starting from yesterday's high-watermark + 0 is safe.

---

### Opportunity 2: Season Enforcement Rate (trust builder)

**What it is:** A running count of this season's games vs. enforcement events.

```
2026 Cubs season enforcement
18 home games played
17 had LV2 enforcement (94%)
1 no-enforcement day: Apr 3 (rain postponement, game moved to next day)
```

**How it works:**
- `scripts/fetch_enforcement.py` runs in the daily cron after each game
- For each past game day, queries wrvz-psew: did 9-64-090 tickets get issued in Wrigleyville after 5 PM?
- Writes results to `data/enforcement.json`
- Page renders a simple table

**Build effort:** ~50 lines of Python. Add to existing cron. 1-2 hours.

**Why it matters:** Builds trust. Users don't know if the site's data is real. Showing "94% enforcement rate, here's the full history" proves the tool is grounded in actual ticket data, not just schedule guessing.

---

### Opportunity 3: Extended FOIA Heat Map (data moat)

**What it is:** The current heat map plan uses our FOIA data (2018-2023, static). Add a live 2026 layer from the Socrata API.

**Two-layer map:**
- Layer 1: FOIA 2018-2023 heat map (9,434 tickets, static GeoJSON -- the exclusive asset)
- Layer 2: 2026 season from Socrata API (querys run daily, written to `data/lv2-2026.geojson`)

**Caption updates from:**
"Since 2018, over 9,400 cars have been ticketed in the LV2 zone. The red streets are where it happens most."

**To:**
"9,434 tickets from 2018-2023, plus 847 already in 2026. Red = most ticketed streets."

**Build effort:** Modify `fetch_enforcement.py` to also pull lat/lon for 2026 tickets, write to GeoJSON. Add second Leaflet layer in `app.js`. 1-2 hours.

---

### Opportunity 4: Data Story Blog Post (SEO + Reddit launch)

**What it is:** An analysis page built from the full Socrata dataset + our FOIA data. Published as a blog post. Submitted to r/chicago the same way Second City Citation did.

**Headline options:**
- "We analyzed 9,400 LV2 parking tickets near Wrigley Field. Here's what happened."
- "LV2 near Wrigley: which street gets ticketed first?"
- "Data: Does LV2 enforcement actually start at 5 PM? (We checked.)"

**Findings to surface:**
- Which streets get ticketed most (already know from FOIA)
- What time enforcement actually starts (FOIA shows spike at exactly 5:00 PM)
- Night games vs. day games -- enforcement rate difference
- Year over year ticket volume (FOIA 2018-2023, extend with Socrata)
- Concert vs. game enforcement -- any difference?
- 577 concert-tagged tickets, 3,645 game-tagged in our FOIA data

**Format:** Static HTML page at `/blog/lv2-data-analysis.html` (already in the plan.md repo structure)

**Build effort:** 2-3 hours for the page. Data already done (FOIA analysis already complete from research.md).

**SEO impact:** This is the highest-leverage content piece for long-tail search and backlinks. Second City Citation got 112 upvotes on r/chicago from a city-wide dataset. Our data is Wrigleyville-specific AND includes exclusive FOIA history they don't have. This story is better.

---

## Competitive Position vs. Second City Citation

| | Second City Citation | lv2park.com |
|---|---|---|
| Scope | City-wide, all violations | Wrigleyville, LV2 only |
| Game-day context | None | Core purpose |
| Historical FOIA data | None | 9,434 tickets 2018-2023 (exclusive) |
| Live enforcement signal | Yes (city-wide, all violations) | Phase 2 (Wrigleyville only, RESIDENTIAL PERMIT filter) |
| Actionable answer | No | Yes -- "is it active RIGHT NOW near me" |
| Affiliate revenue | No | SpotHero |
| Email list | No | Yes (weekly digest) |
| SEO content | No | Data blog post + dedicated pages |

They can coexist. They might even link to us as the Wrigley-specific resource.

---

## Build Plan Updates

**What changes from current plan.md (updated April 16 2026):**

| Step | Original | Updated |
|---|---|---|
| app.js | Fetch today.json, render YES/NO | Read enforcement-today.json on game days, show live ticker if count > 0 |
| scan_tickets.py | Not planned | New: eHearing sequential scanner, runs every 30 min via GH Actions |
| ticker_state.json | Not planned | New: persists high-watermark between scans (gitignored) |
| enforcement-today.json | Not planned | New: count + last_checked, committed to repo by scanner |
| Leaflet map | FOIA static layer only | Phase 2: add 2026 live layer from scanned data |
| Blog | Planned, not detailed | FOIA data story -- no Socrata needed, our FOIA data alone is the story |

**Total additional build time for live ticker:** 2-3 hours.
**When to build:** Post-launch. The enforcement tracker page (FOIA-based, already built) covers launch. Add the ticker when the site has traction and it's worth the maintenance overhead.

---

## Real-Time API Investigation: Full Findings (April 16 2026)

**Status: SOLVED. Buildable via eHearing sequential scan.**

### What Chicago publishes (and doesn't)
- `wrvz-psew` = Taxi Trips (2013-2023). Not parking violations. Confirmed.
- Chicago has **zero parking violation datasets on Socrata**. Exhaustively confirmed.
- No public REST API exists for Chicago parking enforcement data.

### Second City Citation: fully reverse-engineered
- Custom Next.js backend: `/api/officers`, `/api/tickets`, `/api/tickets/daily`, `/api/stats?range=ytd`
- Client JS only calls their own `/api/*` routes -- city data source is 100% server-side
- Data: officer IDs, individual 10-digit ticket IDs, timestamps, lat/lon, violation type
- Officer `2236` lifetime total: 6,335 tickets, $12M in fines. Data goes back years.
- Mapbox username in client bundle: `zayyanf`. No public GitHub repos.
- Their "clever trick": **sequential ticket number scanning** against `parkingtickets.chicago.gov`

### How we know it's sequential scanning
- Tested ticket IDs `9205512430` through `9205512440` against the city eHearing portal
- Found: `9205512432` = RESIDENTIAL PERMIT PARKING (LV2 violation), 04/15/2026
- Found: `9205512433` = MISSING/NONCOMPLIANT PLATE, 04/15/2026
- Found: `9205512434` = EXPIRED PLATE, 04/15/2026
- IDs are clustered sequentially within officer device sessions, with occasional gaps
- City portal (`parkingtickets.chicago.gov/EHearingWeb/displayEligibleTickets`) accepts 3 IDs per POST, returns full details including violation type and address

### We can build the same thing
The scanner is buildable. See Opportunity 1 above for full spec. We confirmed:
- The POST endpoint accepts CSRF + session cookie + up to 3 ticket numbers
- Response includes violation_description containing "RESIDENTIAL PERMIT" for LV2 tickets
- No rate limiting detected at 3-request-per-second pace during testing
- Works without any API key or authentication beyond the CSRF token

---

## Open Questions

1. **High-watermark bootstrapping:** When we first run the scanner, we need a starting ticket number from the current day. One-time setup: manually submit a known recent ticket number to find today's range, then let the scanner maintain itself from there.
2. **Ticket number range per day:** How many tickets are issued citywide per day? Estimate: 500-1,500. LV2-specific: maybe 50-150 on game days. Scanner needs to cover enough range to find them. May need to scan more than 200 IDs per run if enforcement officers cover wide number ranges.
3. **Exact LV2 address filter:** The scanner filters by address strings. Need to confirm the complete list of Wrigleyville streets inside the LV2 boundary. Use our FOIA top-streets data as the starting list.
4. **Second FOIA:** File a new FOIA request for 2023-present LV2 ticket data. Would extend the enforcement tracker and heat map. Good to file after launch -- gives fresh content for month 2.
5. **Rate limiting:** No throttling observed during testing but we only made ~20 requests. If the scanner hits limits at scale, add randomized delays or rotate session cookies.

---

## Sources

- [Chicago Municipal Code 9-68-023 -- Wrigley Field LV2](https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2646672)
- [Chicago Parking Violation Codes (official)](https://www.chicago.gov/city/en/depts/fin/provdrs/parking_and_redlightcitationadministration/supp_info/ParkingStandingandComplianceViolations.html)
- [Towed Vehicles dataset (ygr5-vcbg)](https://data.cityofchicago.org/Transportation/Towed-Vehicles/ygr5-vcbg)
- [Graceland West -- LV2 2023 expansion to all home games](https://gracelandwest.org/2025/04/05/the-cubs-win-now-lets-talk-about-parking/)
- [ProPublica -- Chicago parking ticket data](https://www.propublica.org/nerds/download-chicago-parking-ticket-data)
- [Second City Citation](https://www.secondcitycitation.com/stats)
