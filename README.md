# LV2 Park

**Is there a game or event at Wrigley today?**

[lv2park.com](https://lv2park.com) tells you instantly, and whether the LV2 tow zone is active tonight.

---

## What It Does

LV2 is a Chicago parking zone surrounding Wrigley Field. On game days and event nights, parking is restricted 5-10 PM. Cars get towed fast, usually within minutes of 5:00 PM. Over 9,400 cars were ticketed in the zone between 2018 and 2023.

This site gives Lakeview and Wrigleyville residents a simple answer every day:

- Is there a game or event today?
- Is LV2 in effect tonight?
- What does the week ahead look like?
- Where can I park safely?

A Monday morning email digest goes out every week with the full week's schedule.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, Leaflet.js (map) |
| Hosting | GitHub Pages (custom domain) |
| Data | MLB schedule + Ticketmaster, auto-refreshed daily |
| CI | GitHub Actions (scheduled runs + Monday digest) |
| Analytics | Google Analytics |

---

## Project Structure

```
product/web/
├── index.html              Main page
├── unsubscribe.html        Unsubscribe page
├── style.css               All styles
├── app.js                  Frontend logic (map, schedule, email form)
├── game-banner.js          Game day banner (injected on all pages)
│
├── blog/                   Blog posts
├── game-recaps/            Auto-generated game recap pages
├── resources/              Resource and tool pages
├── data/                   Auto-updated JSON (today, week, health, overrides)
└── scripts/                Data pipeline scripts
```

---

## Local Development

```bash
cd product/web
python3 -m http.server 9001
open http://localhost:9001
```

---

## The LV2 Zone

The LV2 residential parking zone is defined in Chicago Municipal Code 9-68-023. It covers roughly:

- **North:** Irving Park Road
- **South:** Addison Street
- **East:** Racine Avenue
- **West:** Ashland Avenue

Streets inside the zone are posted with signs. On any day with a Cubs game, concert, or permitted event at Wrigley, parking is restricted 5-10 PM. Enforcement starts exactly at 5:00 PM.

FOIA data analysis: [lv2park.com/blog/lv2-data-analysis.html](https://lv2park.com/blog/lv2-data-analysis.html)

---

## Not Affiliated

Not affiliated with the Chicago Cubs, MLB, or the City of Chicago. Schedule data is pulled from public sources (MLB, Ticketmaster), the same sources the 44th Ward uses to post enforcement dates. When in doubt, check [mlb.com/cubs/schedule](https://mlb.com/cubs/schedule) or the [44th Ward site](https://www.44thward.org).
