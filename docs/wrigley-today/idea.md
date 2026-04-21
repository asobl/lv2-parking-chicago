# Wrigley Today -- Idea Exploration

**Origin:** Friend idea, April 15 2026
**Inspired by:** isyontefearlythisyear.com, doineedanlv2passtoday.com
**Status:** Exploring -- research complete + FOIA data in hand
**FOIA data file:** `/Users/asobol/Library/Mobile Documents/com~apple~CloudDocs/Desktop/Hobbies/FOIA_Sobol_A51907_20230828.xlsx`

---

## The Core Idea

A mobile-first website that answers one question: "Is there a game or event at Wrigley Field today?"

Clear YES or NO. What's happening. What the week looks like. LV2 status. Parking links. Email signup for a weekly digest.

Pain it solves: events aren't announced in one place. Residents, commuters, parking-hunters, delivery drivers, restaurant owners -- they all need to know BEFORE they leave the house or their car gets towed.

**Mobile-first is non-negotiable.** These users are in their cars, on the Red Line, walking out their front door. Phone in one hand. Design for that.

---

## Who Actually Needs This

- **Wrigleyville/Lakeview residents in the LV2 zone** -- their car gets IMMEDIATELY TOWED after 5 PM on any game or concert day. Highest urgency. Most likely to subscribe and share.
- **Zone 383 permit holders** (Belmont to Irving, Broadway to Ashland)
- **Red Line commuters** heading north through Addison stop
- **Delivery drivers and service workers** -- need to plan routes
- **Restaurants and bars** planning staffing -- multiple owners will bookmark this
- **Visitors from other Chicago neighborhoods** planning to drive or park
- **Cubs fans deciding whether to go**

---

## What the Site Shows

### Above the fold: Today (mobile-first)
```
WRIGLEY TODAY

[YES]                         [NO]
Cubs vs. Mets                 Nothing today.
1:20 PM                       Wrigley is quiet.

Tyler Childers
8:00 PM

LV2 IN EFFECT: YES (5-10 PM)
[Book parking -- from $15 →]
```

Big. Clear. Loads fast. One thumb. Done.

### Section 2: This Week
7-day list. Monday through Sunday. Each row: date, event name, time, LV2 yes/no.
People plan their week -- this is the reason to bookmark it.

### Section 3: The LV2 Zone Map (KEY FEATURE)
Interactive map (Leaflet + OpenStreetMap, free) showing:
- LV2 tow zone boundaries
- Zone 383 boundaries
- Street closures on game day (Waveland Clark-Sheffield, Sheffield Addison-Waveland)
- Security perimeter (Cornelia-Grace / Halsted-Racine)
- Heat map overlay from FOIA data showing the most-ticketed streets

The heat map uses the FOIA dataset Adam already has. No third party needed. Pre-processed into GeoJSON and stored as a static file in the repo.

**LV2 zone legal boundaries (Chicago Municipal Code 9-68-023):**
- Irving Park Rd (N) to Roscoe St (S), Ravenswood Ave (W) to Ashland Ave (E)
- Plus: Montrose to Irving, Ashland to Clark area
- Plus specific street extensions (Eddy St, Greenview Ave, Sunnyside Ave)
In plain English: a large chunk of Lakeview west of the stadium

### Section 4: Parking + Transportation
- SpotHero affiliate link (fires prominently when answer is YES)
- ParkWhiz as backup
- CTA Red Line note ("easiest way -- get off at Addison")
- Free Cubs remote parking: 4650 N. Clarendon Ave, free shuttle, 2 hrs before first pitch
- Rideshare designated drop zones info

### Section 5: Neighborhood Resources
- 44th Ward Alderman (Bennett Lawson) -- Wrigley-area issues, LV2 permit questions
- 46th Ward Alderman (Angela Clay) -- covers LV2 west side
- Cubs game day hotline: 866-4-CPD-TOW
- "Other Chicago neighborhood problems? Contact us" -- reply form, lead gen

### Section 6: Email Signup
"Get the week at Wrigley every Monday morning."
Free digest: what's happening, which days have LV2 in effect, major closures.
Use Resend (free tier) or ConvertKit. Build the list. Sell local sponsorships later.

---

## The FOIA Data -- Exclusive Asset

Adam obtained via FOIA request: **9,434 LV2 parking tickets from February 2018 through August 2023.**

File: `FOIA_Sobol_A51907_20230828.xlsx`
Fields: Ticket Number, Notice Number, Issue Date/Time, Violation Code, Violation Description, Location, Unit Number, Badge Number, PEA Comment

### Key findings:
| Stat | Number |
|---|---|
| Total tickets | 9,434 |
| Tagged to Cubs games (in comment) | 3,645 |
| Tagged to Wrigley concerts | 577 |
| Other/generic LV2 | 5,212 |
| Peak enforcement hour | 5 PM (3,783 tickets) |
| Tickets written by 5:05 PM on a game day | ~300+ |
| Years covered | 2018, 2019, 2021, 2022, 2023 (no 2020 -- COVID) |

### 5 PM enforcement is instant:
By 5:01 PM: 40+ tickets already written. By 5:05 PM: 60-70 per minute. If you parked at 4:58 and walked to the train, you're getting a ticket before you leave the block.

### Most ticketed streets (highlight on map):
1. N Marshfield Ave -- ~2,269 tickets
2. N Paulina St -- ~1,323 tickets
3. N Hermitage Ave -- ~901 tickets
4. W Roscoe St -- ~851 tickets
5. W Belle Plaine Ave -- 375 tickets
6. N Ravenswood Ave -- 277 tickets
7. W Cornelia Ave -- 276 tickets
8. N Southport Ave -- 245 tickets

### Uses for this data:
- Heat map overlay on the LV2 map (pre-processed GeoJSON, static file)
- Landing page stat: "Over 9,400 LV2 tickets issued near Wrigley since 2018. Know before you park."
- Blog post / shareable content: "We analyzed 9,000+ LV2 tickets. Here's what we found." -- original research, no one else has this
- Credibility signal: Adam actually got the data through FOIA. That's a story.
- Potential viral angle: show the exact minute-by-minute enforcement spike on the data page

**This is the differentiator.** Every neighborhood blog and NextDoor post will link to the map and the data. That's how you build SEO authority without buying ads.

---

## LV2 -- The Sleeper Feature

LV2 is a Chicago parking permit zone covering a large chunk of Lakeview/Wrigleyville west of Graceland Cemetery.

- Changed in 2023: now applies to ALL games (day and night), not just night games
- Enforcement: 5 PM to 10 PM, immediate tow
- Residents get free permits from the City Comptroller
- Zone 383 permits do NOT work in LV2 -- different zone

Source: Chicago Municipal Code 9-68-023, Graceland West Community Association

---

## Search Terms People Actually Use

- "wrigley game today"
- "cubs game tonight"
- "is there a game at wrigley today"
- "wrigley field event today"
- "wrigley field concert tonight"
- "is there a concert at wrigley tonight"
- "LV2 parking wrigley" / "LV2 wrigley field"
- "parking wrigley field today"
- "wrigley field schedule this week"
- "is wrigley busy today"
- "wrigley street closures today"

Zero clean answers for most of these. The LV2 queries have basically no good destination. That's the SEO gap.

---

## Data Sources (all free)

| Source | What it covers | Details |
|---|---|---|
| MLB Stats API | Cubs home/away games | Free, no key. `statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=112` |
| Ticketmaster Discovery API | Concerts, special events | Free tier, 5k req/day. Venue: KovZpZAFlktA (confirm) |
| Cubs official events page | Special non-TM events | `mlb.com/cubs/tickets/events` |
| wrigleyfieldevents.com | Corporate/private events | Separate entity; may need manual or scrape |
| gallagherway.com/events | Adjacent plaza concerts | Outdoor series next door -- add separately |

Event types to cover:
- Cubs home games
- MLB special events (HBCU Classic, All-Star, Upper Deck Golf, etc.)
- Concerts (Tyler Childers, Noah Kahan, John Mulaney -- first ever comedy show)
- Savannah Bananas / novelty sports
- Gallagher Way Budweiser Concert Series (separate outdoor stage)
- Private/corporate (manual flag -- rare but high impact)

---

## Tech Stack: GitHub Pages + GitHub Actions

**No server needed. Zero ongoing cost.**

```
GitHub Actions cron (runs daily 6 AM):
  1. Fetch MLB Stats API → Cubs schedule
  2. Fetch Ticketmaster API → Wrigley events
  3. Merge + write to /data/today.json and /data/week.json
  4. Commit + push

GitHub Pages serves static site:
  - index.html loads /data/today.json on page load
  - Renders YES/NO, LV2 status, week view
  - FOIA heat map = static GeoJSON in repo (never changes)
  - Leaflet.js for map (CDN, no build step)
```

**Why this beats GCP/cloud server:**
- Free (GitHub Actions: 2,000 min/month free)
- Monitoring built in: GitHub emails you if workflow fails
- Version history of every data update
- No servers to maintain or pay for
- Data doesn't need real-time refresh (events are known in advance)

**Built-in monitoring:**
- GitHub Actions failure = email alert automatically
- Add "Last updated: [timestamp]" to the page from today.json -- you can glance and know it ran
- Uptime Robot (free) pings the URL every 5 min as backup

**Mobile-first build requirements:**
- Single column layout
- Font size: 24px+ for the YES/NO answer
- SpotHero button: full width, 56px height
- Map: touch-friendly, no hover-only interactions
- Email signup: one field (email), big button
- Load time target: under 2 seconds on 4G

---

## Monetization Stack

| Revenue source | Monthly estimate | Notes |
|---|---|---|
| SpotHero affiliate | $100-400 | High-intent (YES + need parking). $3-8/booking. |
| ParkWhiz affiliate | $50-150 | Backup/complement |
| Google AdSense | $50-200 | Passive, grows with traffic |
| Email list sponsorship | $100-500 | Local bars, restaurants, rideshare -- "presented by [bar] on game nights" |
| Civic/neighborhood links | $0 but authority | Backlinks from alderman site, NextDoor, neighborhood blogs |
| SMS alerts (future) | $2-5/mo/sub | "Text me when LV2 is in effect this week" |

Realistic at 2k-5k monthly visitors: **$250-700/month passive** after 3-6 months SEO.

---

## Email Product: "This Week at Wrigley"

Sent every Monday at 8 AM.

```
Subject: This week at Wrigley (April 14-20)

Mon 4/14: Nothing
Tue 4/15: Nothing
Wed 4/16: Cubs vs. Phillies, 7:05 PM -- LV2 IN EFFECT
Thu 4/17: Cubs vs. Phillies, 1:20 PM -- LV2 IN EFFECT (day game)
Fri 4/18: Cubs vs. Mets, 1:20 PM
Sat 4/19: Cubs vs. Mets, 1:20 PM
Sun 4/20: Cubs vs. Mets, 1:20 PM

Book parking for Wednesday: [SpotHero link]
Need your LV2 permit? → 44th Ward site
Neighborhood issue? Reply to this email.
```

Useful. Scannable. Sponsorable. Builds a local list with real value.

---

## Neighborhood Hub Features

Per Adam's direction -- make this a resource for Wrigleyville/Lakeview residents:

- **44th Ward Alderman** (Bennett Lawson): covers Wrigleyville, LV2 permit questions
- **46th Ward Alderman** (Angela Clay): covers LV2 west streets
- **Cubs game day hotline:** 866-4-CPD-TOW (towing/violations during games)
- **"Have a Chicago neighborhood problem? Contact us"** -- reply form, positions Adam as local helper, lead gen for future products

This earns goodwill, backlinks from city/neighborhood resources, and gives the site staying power beyond just the game-day check.

---

## Domain Options (check availability)

1. wrigleytoday.com
2. iswrigleygametoday.com
3. wrigleygametoday.com
4. iswrigleybusy.com
5. wrigleyeventtoday.com
6. lv2today.com (LV2-specific niche -- extremely targeted)

---

## 2026 Confirmed Events at Wrigley

Beyond baseball:
- John Mulaney: July 11 (first ever comedy show at Wrigley)
- Tyler Childers: July 12
- Noah Kahan x2: July 14-15
- Savannah Bananas: July 24-26
- Mumford & Sons + others (dates TBD)
- Upper Deck Golf: May 14-16 (tee off inside the stadium)
- Chicago HBCU Baseball Classic: May 2
- Gallagher Way Budweiser Concert Series: Mayday Parade May 17, OK Go June 13

---

## Build Estimate

| Phase | Work | Time |
|---|---|---|
| Domain + GitHub Pages setup | Register, DNS, repo | 30 min |
| GitHub Actions workflow | MLB API + TM API + JSON write | 2 hrs |
| Today/Week UI (mobile-first HTML) | YES/NO + 7-day list | 2 hrs |
| LV2 map (Leaflet + OpenStreetMap) | Static boundaries + FOIA heat map | 3 hrs |
| FOIA data processing | Excel → GeoJSON for heat map | 1 hr |
| Email signup | Resend/ConvertKit form | 1 hr |
| Monitoring | Uptime Robot + last-updated badge | 30 min |
| AdSense + SpotHero affiliate | Apply + embed | 1 hr |
| Neighborhood resources section | Links + contact form | 1 hr |
| **Total** | | **~12 hours** |

---

## Open Questions

1. Check domain availability for top 3 options
2. Confirm Ticketmaster venue ID for Wrigley Field (KovZpZAFlktA from Live Nation URL)
3. Does wrigleyfieldevents.com publish a calendar anywhere usable?
4. Google Keyword Planner: search volume for top queries
5. Does this model generalize? (Guaranteed Rate, United Center, Soldier Field = same stack, 3 more sites)

---

## Verdict

Real pain. Proven search intent. LV2 map with FOIA heat map data is original and owned by nobody else. Email list has local sponsorship value. GitHub Pages + Actions = zero ongoing cost. Self-sustaining once built.

Standalone: $250-700/month passive. Part of a 4-5 venue portfolio: could reach $1,500-3,500/month.

**Next step if building:** Domain check + Ticketmaster venue ID + keyword volume. Then build.
