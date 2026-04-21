# LV2 Park -- SEO Content + Tools Strategy

Built from keyword research captured April 15, 2026.
See `seo-keywords.md` for the full keyword list.

---

## The Core Insight

Most LV2 sites are city PDF pages that no one can find or read. The opportunity is clear, practical content that ranks for real searches and sends people back to lv2park.com as the live source of truth.

Three types of assets:
1. **Tools** -- interactive, unique, hard to replicate
2. **Resource pages** -- SEO-driven, evergreen, answers specific questions
3. **Downloadables** -- email-gated, give people a reason to subscribe

---

## Tools (Interactive -- Build on Site)

### Tool 1: "Am I in the LV2 Zone?" Address Checker
**What it does:** User types their street address. JS checks it against the LV2 GeoJSON boundary polygon. Returns YES or NO with a map showing where they are relative to the zone.
**Why it's powerful:** No one else has this. It's a real question residents ask. It has a shareable result ("My address IS in the zone -- here's the map").
**Build effort:** Low. We already have the GeoJSON polygon. Leaflet + turf.js for point-in-polygon check. No server needed.
**Email capture:** After the result, show: "Get an alert the day before LV2 is active near your home. [Enter email]"
**SEO:** Ranks for "am I in the lv2 zone chicago," "lv2 parking zone chicago map," "chicago lv2 zone lookup"

### Tool 2: LV2 Alert Signup (Game Day Notifications)
**What it does:** User subscribes to get an email 24 hours before any LV2 enforcement day. "Tomorrow is an LV2 day -- Cubs vs. Mets, 1:20 PM. LV2 active 5-10 PM."
**Why it's powerful:** This is the highest-value email product. People who live in the zone want to know before they leave their car on the street. Pure utility.
**Build effort:** Low. The Monday digest already uses this infrastructure. Add a second email template: "Tomorrow's LV2 Alert" sent night before each event.
**Email capture:** This IS the email capture. The alert is the product.
**SEO:** Not an SEO play. This is a direct email list builder.

### Tool 3: Historical Ticket Heat Map (FOIA Data)
**What it does:** Interactive map. Click on any street in the LV2 zone. See how many tickets were issued there from 2018-2023, broken down by game type (day game, night game) and month.
**Why it's powerful:** We own this data. No one else can build this tool. It's a reason to link to lv2park.com. It's also a great press/media hook.
**Build effort:** Medium. FOIA data is already in hand. Needs processing into street-level GeoJSON. Leaflet hover interactions. Already have the basic heat map layer from plan.md -- this extends it.
**Email capture:** "Want to know your street's ticket risk before each game? Subscribe to LV2 Alerts."
**SEO:** "wrigley field parking tickets," "lv2 parking ticket chicago," "lv2 enforcement data"

### Tool 4: Cubs Season LV2 Calendar
**What it does:** Shows the full 2026 Cubs home schedule with LV2 days marked. Filterable by month. One-click to add to Google Calendar or download as .ics file.
**Why it's powerful:** People want to plan around game days. A .ics file with every LV2 day of the season is genuinely useful. No one else has made this.
**Build effort:** Low. We already pull the schedule. Render it as a filterable table. Generate .ics with a simple JS library (ics.js, free, 0 dependencies).
**Email capture:** To download the .ics file: "Enter your email and we'll send you the calendar + updates when games are added or rescheduled."
**SEO:** "cubs 2026 home schedule," "cubs parking schedule 2026," "lv2 parking dates 2026"

### Tool 5: Parking Cost Calculator
**What it does:** "How much will it cost to get to this game?" User picks a starting neighborhood (or enters zip code). Tool shows:
- Drive + SpotHero parking: $X + $Y = total
- CTA Red Line: $Z each way
- Rideshare estimate: ~$A each way (links to Uber/Lyft)
**Why it's powerful:** Converts comparison shoppers into SpotHero affiliate clicks. People search this exact question before a game.
**Build effort:** Low. Static estimates. No live API needed. Just a well-designed table with neighborhood rows.
**Email capture:** Optional. "Save your preferred route and get reminders before game days."
**SEO:** "wrigley field parking cost," "cubs parking cost," "wrigley parking vs cta"

---

## Resource Pages (SEO Blog/Guide Pages)

### Page 1: LV2 Parking Chicago: What It Is and How It Works
**URL:** /lv2-parking-rules
**Target keywords:** "lv2 parking chicago rules," "lv2 permit chicago," "level 2 chicago parking"
**What it covers:**
- What LV2 means (Level 2 resident permit zone)
- When it activates (Cubs and Wrigley events, 5 PM - 10 PM)
- Who is exempt (zone residents with permits)
- How to get an LV2 permit
- How to contest a ticket
- Links to the 44th Ward and city permit pages
**Email capture:** "Get notified the day before LV2 is active. [Subscribe to LV2 Alerts]"
**Unique angle:** FOIA data point -- "In 5 years, 9,434 cars were ticketed in this zone."

### Page 2: LV2 Zone Map -- Chicago (Interactive + Download)
**URL:** /lv2-parking-map
**Target keywords:** "lv2 parking map," "lv2 permit chicago map," "chicago lv2 parking zone map"
**What it covers:**
- Interactive Leaflet map (same one on the homepage)
- Street-by-street boundaries
- Neighboring zones (383, 143)
- Downloadable PDF of the zone (email gate)
**Email capture:** "Download the printable zone map. [Enter email to get the PDF]"

### Page 3: Cubs Game Day Parking Guide (2026)
**URL:** /cubs-game-day-parking
**Target keywords:** "cubs day game parking restrictions," "cubs parking map," "cubs parking cost"
**What it covers:**
- Where to park (SpotHero options with affiliate links)
- LV2 explained for visiting fans (not residents -- different audience)
- CTA Red Line as the best option
- Free Cubs shuttle from Clarendon
- What happens if you park in the zone without a permit
- Day game vs. night game LV2 timing differences
**Email capture:** "Get parking alerts before Cubs home games. [Subscribe]"
**Note:** Careful -- no "Cubs" or "Wrigley" in the domain. In the content, use naturally and accurately. The trademark risk is domain/brand, not fair-use editorial content.

### Page 4: Complete Wrigley Field Parking Guide
**URL:** /wrigley-field-parking-guide
**Target keywords:** "wrigley field parking map," "wrigley parking cost," "wrigley field parking lots"
**What it covers:**
- All parking options ranked (garage, lots, street, SpotHero)
- Cost comparison table (updated for 2026 season)
- The Camry Lot explained (Cubs-operated lot on Clark)
- Walking distances from each option to the gate
- Tips for arriving early vs. late
**Email capture:** "Get the parking tip of the week before each home series. [Subscribe]"

### Page 5: How to Avoid a Wrigley Parking Ticket (Data from 9,434 FOIA Records)
**URL:** /wrigley-parking-ticket-data
**Target keywords:** "wrigley parking zone," "lv2 parking ticket chicago," "cubs parking restrictions"
**What it covers:**
- The FOIA data story (what we requested, what we got)
- Which streets get the most tickets
- Which game types generate the most enforcement (day game vs. night, weekday vs. weekend)
- Month-by-month ticket distribution
- The three most common mistakes that get people ticketed
**Email capture:** "See if your street is high-risk. [Check the heat map]" (leads to Tool 3)
**Note:** This is a strong media hook. Local news (Block Club Chicago, Tribune) covers neighborhood data stories. This article is the press bait.

### Page 6: Chicago Permit Parking Zones Near Wrigley (LV2, 383, 143)
**URL:** /chicago-permit-zones-wrigley
**Target keywords:** "383 parking zone chicago," "chicago parking zone 383 map," "143 permit parking chicago"
**What it covers:**
- What zone 383 is (Lakeview)
- What zone 143 is (Lincoln Park adjacent)
- How LV2 relates to these zones (LV2 is an overlay, not a separate zone)
- Zone boundary comparison map
- Links to permit lookup by address
**Email capture:** Embedded address checker (Tool 1) on this page.

### Page 7: Wrigley Field Parking Shuttle Guide
**URL:** /wrigley-field-parking-shuttle
**Target keywords:** "wrigley field parking shuttle," "cubs parking shuttle," "wrigley parking shuttle"
**What it covers:**
- Free Cubs shuttle details (location, timing, capacity)
- Other shuttles or transit options
- When the shuttle makes sense vs. driving
**Build effort:** Very low. 300-400 words. Mostly factual.

---

## Downloadables (Email-Gated)

| Asset | Email gate | Resend trigger |
|---|---|---|
| 2026 Cubs LV2 Calendar (.ics) | Yes | Send calendar file + confirmation |
| Printable LV2 Zone Map (PDF) | Yes | Send PDF + subscribe to weekly digest |
| "Wrigley Parking Cheat Sheet" (1-page PDF) | Optional (soft gate -- show teaser, email to get full version) | Send PDF + welcome email |
| FOIA Data Summary Report | Yes (higher value -- for residents and press) | Send PDF + welcome email |

---

## Email Capture Strategy

**Three hooks, in priority order:**

1. **LV2 Alert** (highest conversion): "Get a heads-up the day before LV2 is active."
   - Used on: homepage, /lv2-parking-rules, /cubs-game-day-parking
   - Why it converts: pure utility, not a newsletter. People who live in the zone have a real reason to subscribe.

2. **Calendar Download** (medium conversion): "Download the full 2026 LV2 calendar."
   - Used on: /cubs-game-day-parking, /wrigley-field-parking-guide, Cubs Season LV2 Calendar tool
   - Why it converts: one clear deliverable. Not a vague "newsletter."

3. **Weekly Digest** (lower conversion, higher long-term value): "The week at Wrigley, every Monday."
   - Used on: homepage footer, all resource pages
   - Grows the list for sponsorship monetization.

**Do NOT gate the core tool.** The homepage YES/NO answer stays free and instant. That is the product. Gates should be on extras (calendar, map PDF, alerts). Gating the core answer = users bounce.

---

## Build Priority

| Priority | Asset | Effort | Revenue/Email impact |
|---|---|---|---|
| 1 | LV2 Alert email signup (Tool 2) | Low | Highest email conversion |
| 2 | /lv2-parking-rules page | Low | Best SEO entry point |
| 3 | /lv2-parking-map page + address checker (Tool 1) | Medium | Unique, shareable, links |
| 4 | Historical ticket heat map (Tool 3) | Medium | Press bait, backlinks |
| 5 | Cubs Season LV2 Calendar (Tool 4) | Low | Strong email gate |
| 6 | /cubs-game-day-parking page | Low | Affiliate clicks |
| 7 | /wrigley-field-parking-guide page | Low | High search volume |
| 8 | FOIA data story page | Medium | Press coverage |
| 9 | Parking cost calculator (Tool 5) | Low | Affiliate clicks |
| 10 | Zone comparison page, shuttle guide | Low | Long-tail SEO |
