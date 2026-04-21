# LV2 Park -- Framework Evaluation

Retroactive run through the LI Money Tree Framework. v1: April 16, 2026. v2: April 16, 2026 (updated with Monetization Mode, Revenue Unlock Path, and Portfolio Discipline).

---

## Lobos Niche Thesis Pre-Check

- [x] Passionate, non-technical, underserved audience? -- Yes. Wrigleyville/North Side residents who park near the park and get confused by LV2 enforcement rules. Not served by anything else.
- [x] Boring, critical, recurring process? -- Yes. "Is parking restricted today?" is asked every game day, every season, every year.
- [x] Simple enough they'd be silly not to try it? -- Yes. One page, one answer. Is LV2 active today? No account, no friction.
- [x] Natural share moment? -- Yes. "Don't park on Waveland tonight, check lv2park.com" is a real text message between neighbors.
- [x] Runs without Adam after launch? -- Mostly yes. GitHub Actions handles daily updates. Monthly audit email is automated. Some manual attention needed for new seasons and affiliate programs.

**Pre-check: PASS**

---

## Money Tree Score

### 1. Passivity: B
GitHub Actions runs daily. Monthly audit email is automated. Health check scripts exist. But affiliate programs need periodic attention, new season data needs refresh, and the enforcement tracker needs occasional updates. Not fully hands-off, but close.

### 2. Distribution Clarity: A
People are already searching "wrigley field parking restrictions," "lv2 parking chicago," "is lv2 parking active today." SEO is the primary channel. Nextdoor and Chicago neighborhood Facebook groups are ready day-1 distribution. No paid ads needed.

### 3. PLG Score: B
Natural share moment: neighbor texts neighbor before game day. "Check lv2park.com before you park." No built-in product loop (no accounts, no share button), but the content itself is inherently shareable among the right audience.

### 4. Time to First Dollar: C
Site has been live since mid-April 2026. Revenue is $0. FlexOffers affiliate approval is pending. SpotHero affiliate link is live but generating nothing yet. Email list has 3 subscribers. Monetization path exists but hasn't produced a dollar yet.

### 5. Recurring Potential: A
Baseball season returns every year. Game schedule changes every year. LV2 enforcement happens every game and concert. The site's value resets and repeats every season automatically. Annual recurring traffic with no churn risk.

### 6. Support Burden: A
No accounts. No user data. No forms except email signup. No payments to handle. Nothing to support. As close to zero-support as a product can get.

### 7. Moat: A
The FOIA file (9,434 LV2 tickets, 2018-2023) is a unique data asset no one else has. The enforcement tracker page built from that data is unique. Season-by-season analysis, 5 PM spike data, 2023 rule change documentation -- none of this exists anywhere else. Data moat is real.

### 8. Adam's Unique Edge: A
Chicago resident. Filed the FOIA himself. Knows the neighborhood. Knows the Cubs schedule data API. The enforcement tracker page came directly from a document he obtained through the formal FOIA process. No one else has done this work.

### 9. Big Player Risk: A
Too local, too niche, too weird. The Cubs won't build this. Google won't build this. Waze won't build this. The audience is too small and too specific for any large player to care. Niche protects.

### 10. 90-Day Math: C
Revenue model: affiliate commissions (SpotHero, SeatGeek, Ticketmaster) + email list monetization. At $2 per parking referral, would need 1,250 referrals/month to hit $2,500. Traffic is near zero right now. Realistic near-term revenue: $50-200/month if traffic grows. $2,500/month is a 12+ month target, not 90 days.

---

## Summary Scorecard

| Dimension | Grade |
|---|---|
| Passivity | B |
| Distribution Clarity | A |
| PLG Score | B |
| Time to First Dollar | C |
| Recurring Potential | A |
| Support Burden | A |
| Moat | A |
| Adam's Unique Edge | A |
| Big Player Risk | A |
| 90-Day Math | C |

**Individual Score: 7 A's, 2 B's, 2 C's, 0 F's -- B Score**

---

## Monetization Mode + Revenue Unlock Path

**Monetization Mode: Deferred**
LV2 Park earns the asset first (traffic, email list, data depth), then monetizes. Revenue is not immediate. That is by design, not by accident.

**Unlock Trigger:** 500 email subscribers
**Mechanism:** $10/season game day parking alert emails. 500 x $10 = $5,000/year (~$417/month during season).
**Deadline:** End of 2026 Cubs regular season (October 1, 2026)
**Revenue Unlock Score: B** -- trigger is specific and measurable, timeline is one season, revenue is modest but real and recurring.

**Secondary unlock:** If monthly traffic hits 5,000 unique visitors, Google AdSense + affiliate click-throughs become meaningful ($100-300/month passive). No deadline on this one -- it follows the primary.

**What happens if unlock trigger is missed by October 1:** Forced decision. Either pivot the monetization model (sponsorship from a Chicago parking app or Cubs-adjacent brand?), kill the paid tier idea and run it as a pure portfolio asset, or park it.

---

## Portfolio Context

LV2 Park is not evaluated in isolation. It is **tool #1 in the Chicago Helper portfolio.**

**Portfolio contribution score: A**
- Builds the Chicago resident email list that CPD Notifier and future tools sell into
- Establishes the Chicago Helper brand and infrastructure (GitHub Actions, Resend, Cloudflare Workers)
- Proves the model for Chicago city services tools before CPD Notifier is built
- Every future Chicago Helper product costs less to launch because of this foundation

**Does this product make other products in the portfolio more valuable?** Yes, directly. Without LV2 Park there is no Chicago Helper brand, no shared infrastructure, no email list to sell CPD Notifier to.

**True score accounting for portfolio effect: A-/B+**
The individual B becomes stronger in portfolio context. This is not a reason to carry it indefinitely -- the unlock trigger and deadline still apply. But it is a reason to build it even though the individual 90-day math is weak.

---

## Portfolio Discipline

**90-Day Review Date:** July 16, 2026
**Unlock Trigger Deadline:** October 1, 2026 (end of Cubs regular season)
**Next Forced Decision:** October 1, 2026 -- Continue (unlock hit), Pivot (change model), or Kill (park it, let domain sit)
**Maintenance Budget:** Max 2 hours/month. If it exceeds that without generating revenue or list growth, flag it.

**Current status (April 16, 2026):**
- Email list: 3 subscribers (target: 500 by October 1)
- Revenue: $0
- Affiliate approvals: pending
- Enforcement tracker: live
- Next action: drive first 50 subscribers before end of April via Nextdoor + Facebook groups post

---

## What the Full Eval Reveals

LV2 Park scores B individually but A in portfolio context. The C's on Time to First Dollar and 90-Day Math are real gaps -- monetization wasn't designed in from day one. The framework would have caught that before building and pushed for a Stripe link on launch day.

The deferred monetization model is legitimate here because:
1. The unlock trigger is specific (500 subscribers) with a real deadline (October 1)
2. The portfolio contribution is high (Chicago Helper anchor)
3. The maintenance cost is near zero (2 hours/month max)
4. There is a forced kill date if the trigger isn't hit

**Lesson carried forward to CPD Notifier:** Stripe link on launch day. Don't defer what can be immediate.
