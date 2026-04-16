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

## Status
- Noted: 2026-04-16
- Decision: Thinking about it — revisit when lv2park has traffic to justify the build
- Build estimate: Data pipeline (2 days) + story page (1 day) + interactive feature (2-3 days)
