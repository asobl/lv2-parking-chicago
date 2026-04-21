# LV2 Park -- Decision Log

## Domain Decision: lv2park.com
**Decided:** April 15 2026
**Status:** REGISTERED on GoDaddy -- April 15 2026

**Why lv2park.com:**
- "lv2 park" is how people naturally type the search query
- Shortest option that still explains what it does
- "park" works as both verb (can I park?) and noun (parking)
- No trademark conflict -- LV2 is a city ordinance, public law
- No time-word conflict -- works for daily check, weekly email, FOIA history, all content types
- Passes the say-it-out-loud test: "just check lv2park.com"

**Domains to register later / redirect:**
- lv2today.com -- redirect to lv2park.com
- lv2parktoday.com -- redirect to lv2park.com
- lv2parking.com -- redirect to lv2park.com

**Domains ruled out:**
- Anything with "wrigley" or "cubs" -- trademark risk (Cubs own registered mark since 1989, aggressive enforcer)
- wrigleytoday.com, iswrigleygametoday.com -- same risk

---

## Project Status: Idea Phase Complete

**What's confirmed:**
- Domain: lv2park.com (available, ~$12/yr)
- MLB Stats API: live, free, no key required. Returns venue + game time.
- Ticketmaster venue ID: KovZpZAFlktA (confirmed for Wrigley Field)
- Ticketmaster API key: register free at developer.ticketmaster.com
- FOIA data: 9,434 LV2 tickets 2018-2023 in hand. Exclusive asset.
- GitHub Pages + Actions: free hosting, daily cron workflow, emails on failure
- Repo: public (GitHub Pages free on public repos, API keys in GitHub Secrets)

**Next steps when ready to build:**
1. Register lv2park.com on GoDaddy
2. Register at developer.ticketmaster.com for free API key
3. Create GitHub repo
4. Build GitHub Actions workflow (MLB + TM APIs → JSON)
5. Build mobile-first HTML/JS page
6. Process FOIA Excel → GeoJSON for heat map
7. Set up email collection (Resend or ConvertKit free tier)
8. Apply AdSense + SpotHero affiliate
9. Write first blog post (FOIA data analysis) -- launch on r/chicago, r/Cubs
10. File second FOIA for 2023-2026 data

**Future domain portfolio (same model, different venues):**
- Guaranteed Rate Field (White Sox)
- United Center (Bulls/Blackhawks)
- Soldier Field (Bears)
- Other cities: Fenway, Dodger Stadium, etc.

**Full idea doc:** `idea.md`
**Full research doc:** `research.md`
