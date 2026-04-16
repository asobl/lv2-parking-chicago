# LV2 Park — Content and Feature Opportunities

## Chicago Traffic Tracker Data

**Source datasets:**
- Historical by segment (2018–Sep 2023): data.cityofchicago.org/d/77hq-huss (older) + data.cityofchicago.org/d/4g9f-3jbs (newer, 2023–current)
- Historical by region (2018–current): data.cityofchicago.org — 29 city zones, updated every 10 min
- Current segment estimates: data.cityofchicago.org/d/n4j6-wkkf

**Why it matters for lv2park:**
Segment-level data covers Sheffield Ave, Clark St, Addison St — the exact LV2 streets in our FOIA ticket dataset. Can show speed by hour on game days vs non-game days. Combined with MLB schedule (already integrated) and FOIA ticket data, this is a three-way data story nobody else has.

---

### Stories — For the person going to the game

- "What time should I leave for a 1:20 PM game?" — day games are harder to time than night games. Data shows exactly when Clark and Sheffield slow down before first pitch.
- "How long after the final out until traffic clears?" — post-game congestion curve by inning. Extra innings vs quick games tell different stories.
- "Day game vs night game: which is worse for your drive in?" — 1:20 PM hits lunch traffic, 7:05 PM hits rush hour. Neither is clean. Data compares both.

### Interactive — For the person going to the game

- **Traffic timeline slider** — pick a game time, see average speed on Clark/Sheffield by hour from 10 AM to midnight. See when it gets bad and when it recovers.
- **Best arrival window calculator** — input game time, output the recommended leave-by window based on 5 years of data.

---

### Stories — For the person living in the neighborhood

- "Which street slows down first: Sheffield, Clark, or Addison?" — segment data shows the exact order streets lock up on game days. Sheffield goes first every time.
- "The 5 PM wall: why game days own your evening" — congestion data + LV2 enforcement start time. Two things hitting at once.
- "How many hours per year does Wrigleyville lose to game day traffic?" — 81 home games x average congestion duration. Provocative aggregate number for neighborhood readers.
- "July vs April: how the season gets worse as it goes" — warmer weather, bigger crowds, longer days. July games are measurably worse than April by traffic volume.

### Interactive — For the person living in the neighborhood

- **Your street on game day** — enter a cross street, pull the closest segment, show average speed curve on game days vs a normal Tuesday. Personal and shareable.
- **Worst days of the season** — ranked list of the 10 highest-congestion game days going back to 2018. Cardinals series always shows up.

---

### Stories — For the person driving in from the suburbs

- "Why leaving at 5:30 for a 7:05 game is the worst decision you can make" — shows the exact congestion window a suburban driver hits. Leave at 4:30 or leave at 6:45, nothing in between.
- "The real cost of driving to Wrigley: time lost in traffic, not just parking" — time-in-congestion estimate plus parking cost vs CTA.
- "Which highway exit matters: Addison vs Irving Park vs Belmont?" — segment data near each exit shows which approach stays clearest on game days.

### Interactive — For the person driving in from the suburbs

- **Drive-in vs Red Line comparison** — based on starting suburb, show estimated drive time (with game day congestion baked in) vs CTA trip time.
- **When to leave the suburb** — pick your starting area, pick game time, get the window. "Leave by 4:45 or wait until 6:50."

---

### The flagship piece (combines all three audiences + all three datasets)

**"Sheffield Ave's worst hour: 5 years of data"**

Use segment speed data AND FOIA ticket data on the same timeline. Traffic peaks. Tickets start flying at exactly 5:00 PM. The two lines cross at the worst possible moment for anyone on that block. One page, one chart, shareable, ranks for "Wrigley traffic" and "Cubs game parking."

This is the story that ties everything together and links naturally to the parking guide, SpotHero affiliate, and the LV2 explainer.

---

## Other Chicago Open Data Datasets (confirmed active as of April 2026)

### Towed Vehicles — ID: ygr5-vcbg — Updated daily
Live feed of every vehicle towed and impounded in Chicago within the last 90 days, with location.

**Stories:**
- "Where do cars actually get towed near Wrigley?" — filter to Wrigleyville zip, map the tow locations, show the hot corners
- "How many cars get towed per game?" — count records per game day date, rank by opponent/day type
- "The most expensive Cubs game to park near: the day 47 cars got towed in 2 hours"

**Interactive:**
- Live tow map for Wrigleyville — on game days, show any active tows in the LV2 zone in near real-time. "3 cars towed on your block in the last hour."
- Most towed blocks ranked — overlay with our FOIA ticket data for double confirmation

---

### CTA Ridership — L Station Daily Totals — ID: 5neh-572f — Updated March 2026
Daily ridership by L station back to 2001. Addison Red Line station is the Wrigley stop.

**Stories:**
- "How many people actually take the Red Line to Cubs games?" — Addison station spikes vs baseline non-game days. The number is probably surprising.
- "Day game vs night game: Red Line ridership tells the real story" — night games draw more rail riders. Why?
- "Red Line ridership to Wrigley over 20 years" — has it grown? Did COVID kill it? Is it back?
- "The case for the Red Line: your drive vs 40,000 people who took the train"

**Interactive:**
- Addison station ridership chart overlaid on game schedule — shows the spike on every home game day

---

### Parking Permit Zones — ID: u9xt-hiju — Updated April 15, 2026
Every street segment in Chicago designated as a residential parking zone, with zone number and type (standard vs buffer).

**Stories:**
- "Every permit zone near Wrigley, explained" — Zone 383, Zone 143, and the LV2 overlay. What's the difference and which one affects you?
- "The parking zone nobody warned you about: Zone 383 vs LV2 — two different rules, same street"

**Interactive:**
- Power the zone lookup on the existing site with real city data instead of hardcoded polygons. Enter an address, get exact zone membership from the official dataset.

---

### Special Event Parking Permits — ID: 4ixn-jz5x — Updated April 15, 2026
Permits for street parking closures tied to festivals, parades, and special events.

**Stories:**
- "The worst Cubs game days: when a game + street closures + a festival all hit at once" — identify dates where game day overlaps with nearby special event permits
- "Summer 2025: how many days did Wrigleyville have a game AND a street event?" — compound pressure on parking

---

### Traffic Crashes near Wrigley — ID: 85ca-t3if — Updated April 15, 2026
All traffic crash records on city streets with conditions, injuries, contributing factors.

**Stories:**
- "Do traffic crashes near Wrigley spike on game days?" — filter to Wrigleyville area, compare game day vs non-game day crash frequency
- "The most dangerous intersections near Wrigley after a night game" — time-filtered crash data, ranks intersections

---

### On-street Construction Permits — ID: 7wiq-4rgy — Updated April 15, 2026
Active permits for temporary road use near construction.

**Practical use:**
- Show on the week schedule if any LV2-zone streets have active construction permits on game days. "Clark St lane closed + Cubs game = avoid." Could be a real-time warning on the site.

---

### Temporary Traffic Control Permits — ID: 822f-avdk — Updated April 16, 2026
Permits for traffic control changes (lane closures, detours) around the city.

**Practical use:**
- Same as construction — flag game days where TTC permits are active near the LV2 zone.

---

## Dataset Priority Ranking for lv2park

| Dataset | Relevance | Freshness | Build effort | Priority |
|---|---|---|---|---|
| Traffic Tracker (segment) | Very high | Live | Medium | 1 |
| Towed Vehicles | Very high | Daily | Low | 2 |
| CTA Ridership (Addison) | High | Monthly | Low | 3 |
| Parking Permit Zones | High | Live | Low | 4 |
| Traffic Crashes | Medium | Daily | Medium | 5 |
| Special Event Permits | Medium | Live | Low | 6 |
| Construction/TTC Permits | Medium | Live | Low | 7 |

---

## Status
- Noted: 2026-04-16
- Decision: Thinking about it — revisit when lv2park has traffic to justify the build
- Build estimate: Data pipeline (2 days) + story page (1 day) + interactive feature (2-3 days)
- Quickest wins: Towed Vehicles data (daily, easy to filter) + CTA Addison ridership (clean, goes back 20 years)
