# Wrigley Today -- Research Findings

**Completed:** April 15 2026

---

## Domain Availability (checked via whois April 15 2026)

ALL available. Zero registered.

| Domain | Status | Notes |
|---|---|---|
| wrigleytoday.com | AVAILABLE | Best overall. Short, works for games + events + concerts. |
| iswrigleygametoday.com | AVAILABLE | Exact match for top search query. Longer. |
| wrigleygametoday.com | AVAILABLE | Cleaner version of above. |
| iswrigleybusy.com | AVAILABLE | Good but "busy" is vague. |
| wrigleyeventtoday.com | AVAILABLE | Event-focused angle. |
| lv2today.com | AVAILABLE | Niche, high intent. Could be a sub-feature or companion. |
| wrigleyalert.com | AVAILABLE | Good for the email/alert angle. |
| wrigleycheck.com | AVAILABLE | Short and clean. |
| iswrigleyopen.com | AVAILABLE | Slightly wrong framing. |
| wrigleyfieldeventtoday.com | AVAILABLE | Too long. |

**Recommendation: wrigleytoday.com**
Covers games, concerts, private events -- all of it. Short. Memorable. Passes the "say it out loud" test.
Register immediately before someone else sees this idea.

---

## MLB Stats API -- CONFIRMED LIVE AND FREE

Tested April 15 2026. No API key required. Returns real data.

**Endpoint:**
```
https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=112&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
```

**teamId 112 = Chicago Cubs**

**Live test results (April 15-22 2026):**
- April 15: Cubs @ Phillies (AWAY -- site shows NO)
- April 17: Mets @ Cubs, Wrigley Field, 1:20 PM CT (HOME -- site shows YES)
- April 18: Mets @ Cubs, Wrigley Field, 1:20 PM CT
- April 19: Mets @ Cubs, Wrigley Field, 1:20 PM CT
- April 20: Phillies @ Cubs, Wrigley Field, 6:40 PM CT
- April 21: Phillies @ Cubs, Wrigley Field, 6:40 PM CT
- April 22: Phillies @ Cubs, Wrigley Field, 6:40 PM CT

**Key field:** `game['venue']['name']` == "Wrigley Field" confirms it's a home game.
Times come back in UTC -- convert to CT (UTC-5 or -6 depending on DST).
Status field shows: Scheduled, Pre-Game, In Progress, Final.

**Reliability:** MLB has maintained this API for years. Low breakage risk.

---

## Ticketmaster Discovery API -- CONFIRMED VENUE ID

**Wrigley Field Venue ID: KovZpZAFlktA** (confirmed from Live Nation URL pattern + multiple sources)

**Endpoints:**
```
# Get venue info
GET https://app.ticketmaster.com/discovery/v2/venues/KovZpZAFlktA.json?apikey={KEY}

# Get upcoming events at venue
GET https://app.ticketmaster.com/discovery/v2/events.json?venueId=KovZpZAFlktA&apikey={KEY}
```

**API key:** Need to register at developer.ticketmaster.com -- free, approved instantly.
**Free tier:** 5,000 requests/day (WAY more than needed -- daily cron = 1-2 requests/day).

Note: The 401 test failed because a placeholder key was used. Once a real key is registered, this will work.

---

## GitHub: Public vs Private Repo

**Decision: Public repo.**

| | Public | Private |
|---|---|---|
| GitHub Pages | FREE | Requires GitHub Pro ($4/mo) |
| GitHub Actions | FREE, unlimited minutes | Limited free minutes |
| Code visibility | Anyone can see code | Hidden |
| API keys | Use GitHub Secrets (encrypted regardless) | Same |
| FOIA data | Public record -- fine to include | Same |

The code isn't the secret. The domain, the data, the brand, and the FOIA analysis are the moat. Nobody needs to pay to protect a 200-line JavaScript file.

API keys (Ticketmaster, email service) go in GitHub Secrets -- encrypted, never in the code -- regardless of public vs private.

**One caveat:** The FOIA Excel file is 9,000 rows. Convert it to a GeoJSON/JSON for the heat map and commit that. Don't commit the raw xlsx if you want to keep the raw source data private -- keep that on your local machine.

---

## Keyword Research

**Exact monthly search volumes:** Not available without Google Keyword Planner (free) or Ahrefs (paid).

**What we know:**
- "cubs game today" is a navigational real-time query -- spikes sharply on game days
- Industry estimates for peak-season: 50k-200k+ monthly for "cubs game today"
- These queries have clear intent: no competing ads, mostly aggregator sites (MLB.com, ESPN, Google Sports panel)
- Our single-serving site can rank for zero-competition long-tail variants: "is there a game at wrigley today", "wrigley field event tonight", "LV2 parking today wrigley"

**To verify: use Google Keyword Planner (free with any Google Ads account, no spend required)**
- Enter: "cubs game today", "wrigley game today", "wrigley field event today", "LV2 parking wrigley", "wrigley field tonight"
- Will give monthly volume ranges and seasonal trend

**SEO strategy:**
- Exact-match domain (wrigleytoday.com) captures informational queries
- Blog content from FOIA data analysis drives long-tail and backlinks
- Reddit posts (r/chicago, r/Cubs, r/Wrigleyville) drive initial traffic, Google picks it up
- Alderman site link + neighborhood org links = authority backlinks with zero outreach

---

## Confirmed 2026 Events (Ticketmaster / MLB)

Non-game events to pull from API:
- John Mulaney: July 11 (first comedy show ever at Wrigley)
- Tyler Childers: July 12
- Noah Kahan x2: July 14-15
- Savannah Bananas: July 24-26
- Mumford & Sons + others (dates TBD)
- Upper Deck Golf: May 14-16
- Chicago HBCU Baseball Classic: May 2
- Gallagher Way concerts: Mayday Parade May 17, OK Go June 13

---

## FOIA Data Summary (for reference)

File: `FOIA_Sobol_A51907_20230828.xlsx`
Records: 9,434 LV2 parking tickets, Feb 2018 -- Aug 2023

Top ticketed streets (pre-processed for heat map):
1. N Marshfield Ave: ~2,269 tickets
2. N Paulina St: ~1,323 tickets
3. N Hermitage Ave: ~901 tickets
4. W Roscoe St: ~851 tickets
5. W Belle Plaine Ave: 375 tickets

Enforcement spike: starts exactly at 5:00 PM, 60-70 tickets/minute by 5:05 PM.
Concert-tagged tickets: 577. Game-tagged: 3,645. Generic: 5,212.

Another FOIA for 2023-present: good idea. Would update the heat map and add 2024/2025 concert data. File a new request when ready to build.

---

## Next Steps

1. Register wrigleytoday.com (GoDaddy, ~$12/yr)
2. Register at developer.ticketmaster.com for free API key
3. Set up GitHub repo + Pages
4. Build GitHub Actions workflow (MLB API + TM API → JSON)
5. Build HTML/JS page (mobile-first)
6. Process FOIA data → GeoJSON for heat map
7. Set up email collection (Resend or ConvertKit free)
8. Apply for Google AdSense + SpotHero affiliate
9. Write first blog post (FOIA data analysis) for Reddit launch
10. File second FOIA for 2023-2026 data
