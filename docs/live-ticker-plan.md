# LV2 Live Enforcement Ticker -- Build Plan

**Status:** Pre-build. Test phase first, then production.
**Goal:** Show confirmed LV2 ticket count on lv2park.com on game days after 5 PM.
**Data source:** `parkingtickets.chicago.gov/EHearingWeb/displayEligibleTickets` (city eHearing portal)
**Approach:** Sequential ticket ID scanning + address filtering for Wrigleyville streets.

---

## How the Data Source Works

The city's eHearing portal accepts POST requests with up to 3 ticket IDs and returns:
- Violation description (e.g., "RESIDENTIAL PERMIT PARKING")
- License plate + state
- Issue date
- Fine amount
- Payment status

Ticket IDs are 10 digits, mostly sequential within an officer's device session. Example from April 15 2026:
- `9205512432` = RESIDENTIAL PERMIT PARKING, 04/15/2026
- `9205512433` = MISSING/NONCOMPLIANT PLATE, 04/15/2026
- `9205512434` = EXPIRED PLATE, 04/15/2026

LV2 violations show up as `RESIDENTIAL PERMIT PARKING` or `RESIDENTIAL PERMIT`.
No separate "LV2" violation code exists.

---

## Phase 1: Test with Historical Data

**Test date:** April 12 2026 (Cubs vs Pirates, home game, 1:20 PM. LV2 active 5-10 PM.)
**Goal:** Confirm the scanner can find LV2 tickets for a past game day and count is plausible.

### What the test validates

1. Tickets from 10+ days ago are still accessible in the portal (not purged)
2. The address filter correctly identifies Wrigleyville vs. non-Wrigleyville violations
3. Ticket count per game day is in line with our FOIA data (~10-40 tickets expected)
4. Sequential scanning works -- gaps exist but don't cause missed clusters

### Test script: `scripts/scan_tickets.py --test`

```
python scripts/scan_tickets.py --date 2026-04-12 --find-range --limit 2000
```

**What it does:**
1. Starts from a known anchor (`9205512432` = 04/15 ticket, scans backwards to find 04/12 IDs)
2. Once it finds the first 04/12 ticket, scans forward 2000 IDs from that anchor
3. Filters: violation_description contains "RESIDENTIAL PERMIT"
4. Filters: ticket_location contains any LV2 street (Marshfield, Paulina, Hermitage, Roscoe, Belle Plaine, Clark, Sheffield, Kenmore, Clifton, Waveland, Addison)
5. Prints: count, list of tickets found, any misses

### RESULTS: TEST PASSED (April 16 2026)

Scanned 3,000 IDs centered on April 12 anchor (9205503000-9205505999).

```
Tickets found (April 12 total):   51
LV2 tickets found:                17
States seen:  IL, MN, MO, KY, MA, CA, WI
```

**All violation types on April 12:**
```
17x  RESIDENTIAL PERMIT PARKING   <-- LV2 (what we want)
16x  EXPIRED PLATE OR TEMPORARY REGISTRATION
 6x  MISSING/NONCOMPLIANT FRONT AND/OR REAR PLATE
 3x  PARKING/STANDING PROHIBITED ANYTIME
 3x  PARK OR STAND IN VIADUCT/UNDERPASS
 1x  OBSTRUCT ROADWAY
 1x  DOUBLE PARKING/STANDING NON-CENTRAL BUSINESS
```

**Date distribution in same 3,000-ID window:**
```
04/10/2026:   5 tickets
04/11/2026:  12 tickets
04/12/2026:  51 tickets  <-- game day
04/13/2026:  27 tickets
04/14/2026:  46 tickets
04/15/2026: 211 tickets
```

**Key architecture finding (changes Phase 2 design):** Ticket IDs do NOT sort cleanly by date. Different officer devices have different ID ranges that overlap. April 10, 11, 12, 13, 14, 15 all land in the same 3,000-ID window. This means a "moving watermark" production design WON'T work -- you'd miss tickets from officers whose device IDs are lower than your watermark.

**Revised production approach:** Scan a fixed 15,000-ID daily window filtered by today's date. The center of the window shifts ~3,000-5,000 IDs per day. Bootstrap once to find today's center, then shift daily. See Phase 2 section below (updated).

---

## Phase 2: Production Scanner

Only build this if Phase 1 passes.

### Files

| File | Purpose |
|---|---|
| `scripts/scan_tickets.py` | Scanner (test mode + production mode) |
| `data/enforcement-today.json` | Output: count + last_checked (committed to repo) |
| `data/ticker_state.json` | State: high-watermark ticket ID (gitignored) |
| `.github/workflows/ticker.yml` | GitHub Action: runs on game days 5-10 PM CT every 30 min |

### `data/enforcement-today.json` (output schema)

```json
{
  "date": "2026-04-17",
  "lv2_tickets_today": 23,
  "last_checked": "2026-04-17T22:47:00Z",
  "scan_ok": true
}
```

### `data/ticker_state.json` (internal state, gitignored)

```json
{
  "high_watermark": 9205512490,
  "last_scan_date": "2026-04-17"
}
```

### GitHub Action: `ticker.yml`

```yaml
name: LV2 Live Ticker
on:
  schedule:
    # Every 30 min, 5-10 PM CT (10 PM - 3 AM UTC)
    - cron: '0,30 22,23,0,1,2 * * *'
  workflow_dispatch:
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check if game day
        id: check
        run: |
          LV2=$(python3 -c "import json; d=json.load(open('data/today.json')); print(d.get('lv2Active','false'))")
          echo "lv2_active=$LV2" >> $GITHUB_OUTPUT
      - name: Scan tickets
        if: steps.check.outputs.lv2_active == 'True'
        env:
          TICKER_STATE: ${{ secrets.TICKER_STATE }}
        run: python3 scripts/scan_tickets.py --production
      - name: Commit results
        if: steps.check.outputs.lv2_active == 'True'
        run: |
          git config user.name "lv2-ticker"
          git config user.email "bot@lv2park.com"
          git add data/enforcement-today.json
          git diff --staged --quiet || git commit -m "ticker: update enforcement count"
          git push
```

### `app.js` additions (~25 lines)

On page load, if `today.json` shows `lv2Active: true`:
- Fetch `data/enforcement-today.json`
- If count > 0 and `last_checked` is within 2 hours: show ticker
- If count == 0 or stale or before 5 PM CT: show nothing

```
LV2 CONFIRMED
23 tickets issued in the zone today
Last checked 5:47 PM CT
```

No street address shown ("too creepy" -- confirmed with Adam). Just count + time.

---

## Validation Pass

| Component | Current? | Math? | Security? | Breaks? | Simpler? | Notes |
|---|---|---|---|---|---|---|
| eHearing POST endpoint | Yes -- confirmed April 16 2026 | 67 requests × 0.5s = 34s per scan | None -- public government portal, no auth required | Portal outage, form field name change, CSRF token expiry | No simpler path -- this IS the simplest path to live data | Tested manually with ticket 9205512432 |
| Sequential ID scanning | Confirmed -- cluster of IDs all from 04/15 with no gaps >10 | ~200 IDs per run covers ~15-20 min of citywide enforcement | None | Large ID gaps could miss a cluster of LV2 tickets | Could scan more IDs (500) for safety | Need to validate gap size on game day |
| Address filter | Validated against FOIA top streets | False positive rate: other IL residential permits outside LV2 -- small, acceptable | None | New street not in filter list | Could use lat/lon bounds instead -- but portal doesn't return coordinates | Start with string match, refine if needed |
| GitHub Action cron | Standard GH Actions -- stable | 30-min refresh, 5-10 PM = 10 runs per game day | API keys not needed | GH Actions free tier: 2,000 min/month. 10 runs × 1 min = 10 min/game day, ~810 min/season -- well within free tier | Could run less often (hourly) | 30 min is the right balance |
| ticker_state.json secret | N/A -- gitignored, passed as env var | Simple JSON, 2 fields | High-watermark is not sensitive | State lost on first run -- bootstrap needed | Could hardcode starting ID on first deploy | First deploy: manually set high-watermark to a recent known ticket ID |

### Validation Score: 8/10

Two things to verify in Phase 1 before committing to Phase 2:
1. Historical tickets (10+ days old) are still in the portal
2. Address filtering finds the right tickets without too many false positives

### Utopian Vision

The city publishes a real-time parking enforcement API with violation code, lat/lon, timestamp, and officer ID. We query it directly. No scanning needed. CORS open, free, always current. This doesn't exist today, but if Chicago ever publishes it (they expanded open data in 2023), we swap to it with one config change. Our `enforcement-today.json` schema stays the same.

---

## Open Questions Before Building

1. **Are tickets older than 30 days still in the portal?** Phase 1 test answers this. If April 12 tickets are gone, test with April 15 (2 days ago).
2. **How wide is a typical ID gap between game-day sessions?** Need to scan a full game day to know how many IDs to cover. Start with 500/run, adjust.
3. **Bootstrap: what's today's high-watermark?** On first production deploy, manually run `python scripts/scan_tickets.py --find-today` to seed `ticker_state.json`.

---

## What We Are NOT Building

- Officer tracking or individual ticket history (that's Second City Citation's product)
- City-wide violation stats (not relevant to LV2 Park's use case)
- A database (flat JSON files are enough -- the count resets daily)
- Any scraping beyond what's needed for the count

---

## Next Step

Run Phase 1 test. Command:
```
cd collected-ideas/lv2park
python scripts/scan_tickets.py --date 2026-04-12 --find-range --limit 2000
```

(Script doesn't exist yet -- see next step: write scan_tickets.py test mode, ~80 lines of Python.)
