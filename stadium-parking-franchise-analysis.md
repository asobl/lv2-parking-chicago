# Stadium Parking Franchise Model -- Analysis

**Status:** Thought. Not a directive. Revisit after Chicago proves out.
**Date:** April 16, 2026

---

## The Idea

lv2park.com answers one question: "Is the parking restriction active near Wrigley today?" If that model works in Chicago, the same pattern exists near every major urban stadium in the country. One codebase, many cities, affiliate revenue scales with traffic.

---

## Is This Problem Everywhere?

Yes. Residential permit parking near dense urban stadiums is universal.

Strongest candidates (stadium + no on-site parking + dense neighborhood):
- Fenway Park (Boston) -- Kenmore/Fenway permit zones, game-day tow zones
- Citizens Bank Park (Philadelphia) -- South Philly event-day restrictions
- Nationals Park (DC) -- Navy Yard / Capitol Hill restrictions
- Oracle Park (San Francisco) -- Mission Bay restrictions
- Lambeau Field (Green Bay) -- neighborhood goes full permit on game days
- University stadiums: Michigan, Ohio State, Notre Dame -- often worse than pro stadiums

Wrigley is the most extreme case (zero on-site parking, 81+ events/year, dense on all four sides) but the pattern repeats everywhere.

---

## What Scales

- MLB, NFL, NBA, NHL schedules: free APIs or scrapers. One integration covers every team.
- Affiliate monetization: SpotHero is national. SeatGeek and Ticketmaster work everywhere. Same code, different stadium.
- Core logic: "event today = zone active" is identical everywhere. Just schedule + zone rules per city.
- Hosting: GitHub Actions + static site. Zero marginal cost per city added.

---

## What Doesn't Scale Cleanly

- **City parking data varies.** Chicago open data portal is good. Boston, Philly, DC are decent. LA and Houston are harder. Zone rules require manual research per city -- probably 2-4 hours per stadium.
- **FOIA enforcement data is Chicago-specific.** The enforcement tracker page (the differentiated content) won't exist for other cities on day one.
- **Search volume is unknown.** "LV2 parking Wrigley" is a real query. "Zone X parking Fenway" -- needs validation before building.

---

## The Smarter Build (When Ready)

Don't do 30 separate domains. One site with city subpages:

```
stadiumparking.guide (or similar)
  /chicago/wrigley
  /boston/fenway
  /philadelphia/citizens-bank
  /green-bay/lambeau
```

One codebase. One GitHub Actions workflow that loops city data files. City-specific JSON for zone rules and schedule source. Add a city in a day once the template is built.

---

## Monetization

Monetization is unclear upfront and that's fine. This is a traffic play first.

The core bet: parking search intent near stadiums is high-intent, right-now traffic. Someone searching "parking restrictions near Fenway tonight" is actively trying to solve a problem. That converts better than most traffic.

**Day-one options (no approval needed):**
- SpotHero affiliate -- already in lv2park.com code, works everywhere
- SeatGeek + Ticketmaster ticket affiliates -- already stubbed in

**Once traffic is there:**
- Display ads (Google AdSense or Carbon Ads) -- parking/event searches have decent CPMs
- Parking lot direct deals -- lots near Fenway etc. would pay for placement, higher margin than affiliate

**The worst case is fine.** GitHub Pages is free. Zero ongoing hosting cost. If monetization never clicks, the pages sit on the internet doing no harm, occasionally sending a SpotHero click. The downside is a few days of build time. The upside is a traffic network that compounds as more cities are added.

---

## Validation Before Building City 2

1. Confirm Chicago is driving real traffic (Google Search Console, 60-90 days post-launch)
2. Check search volume for "parking restrictions [stadium]" in 5 target cities
3. Confirm SpotHero has inventory in those cities
4. One city test: build Fenway version, measure traffic vs. effort

---

## Open Questions

- Is there a competitor already doing this at scale?
- Does Google just answer this with a featured snippet, killing search intent?
- What's the actual CPM or affiliate conversion on parking queries?
- Is the Chicago traffic enough to justify building the franchise infrastructure?

---

## Decision Trigger

Revisit when lv2park.com has 90 days of traffic data and at least 500 monthly visitors. If Chicago works, city 2 is a 1-day build.
