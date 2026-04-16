# FOIA Request #2 -- LV2 / Zone 383 Ticket Data

## Background

**Original request:** A51907, filed August 25, 2023
**Original ask:** "Seeking ticket records of every LV2 ticket. Include at least the date, time, reason, narrative description, location (including street or cross streets), ID of person who gave the ticket out, license plate, and any other relevant information associated with such parking tickets."

**What was returned:** Ticket records covering roughly 2018–2023, but geographically limited to the western side of the LV2 / Zone 383 enforcement area. The returned data covers streets approximately 1400W–1855W (Southport, Greenview, Marshfield, Paulina, Hermitage, Wolcott, etc.). It does not include the core Wrigleyville streets immediately adjacent to Wrigley Field: Sheffield Ave (1000W), Kenmore Ave (1040W), Clifton Ave (840W), Clark St (400W), and the east-west streets Waveland Ave (3632N) and Addison St (3600N).

**What this request targets:** Two gaps from the original response.
1. The missing eastern streets in the same time period (2018–2023)
2. All new records from September 2023 through present

---

## Request Text (ready to submit)

---

**To:** Chicago Department of Finance -- Adjudication Division
*(or City Clerk / FOIA Officer as appropriate)*

**Re:** Follow-up FOIA Request -- Residential Permit Parking Tickets, Zone 383 / LV2, 2018–present

---

Pursuant to the Illinois Freedom of Information Act (5 ILCS 140), I am requesting the following public records:

**All parking ticket records issued for violation code 0964090E (Residential Permit Parking) within the geographic boundaries of Residential Permit Parking Zone 383 (also referred to as the LV2 zone), from January 1, 2018 through the date this request is processed.**

This is a follow-up to my prior request, A51907, filed August 25, 2023. The records returned in response to that request appear to cover the western portion of Zone 383 only. I am requesting the complete dataset, including tickets issued on or near the following streets that were absent from the prior response:

- N Sheffield Ave (approximately 1000 W) between Belmont Ave and Irving Park Rd
- N Kenmore Ave (approximately 1040 W) between Belmont Ave and Irving Park Rd
- N Clifton Ave (approximately 840 W) between Belmont Ave and Waveland Ave
- N Clark St (approximately 400 W) between Belmont Ave and Irving Park Rd
- W Waveland Ave (approximately 3632 N) between Clark St and Ashland Ave
- W Addison St (approximately 3600 N) between Clark St and Ashland Ave
- W Roscoe St (approximately 3400 N) between Clark St and Ashland Ave
- W School St (approximately 3300 N) between Clark St and Ashland Ave
- W Newport Ave (approximately 3542 N) between Clark St and Ashland Ave

Additionally, I am requesting all records from September 1, 2023 through the current date that were not included in the prior response.

**For each ticket, please include:**
- Date and time of issuance
- Violation code and description
- Street address or nearest cross streets where ticket was issued
- Beat or district (if available)
- Badge number or officer ID of the issuing officer
- Ticket status (paid, unpaid, contested, dismissed, in collections)
- Fine amount (original and current if different)

Please provide the records in a machine-readable format (CSV or Excel preferred).

If any portion of this request is denied, please provide a written explanation identifying the specific exemption(s) applied and the responsive records that are being withheld, as required by 5 ILCS 140/9.

---

## Where to Submit

**Online:** chicago.gov/city/en/depts/dof/provdrs/parking_and_boots/svcs/file-a-foia-request-for-parking-ticket-records.html

**Or by mail:**
City of Chicago -- Department of Finance
FOIA Officer
333 S. State Street, Suite 640
Chicago, IL 60604

**Or email:** dof.foia@cityofchicago.org

---

## What to Expect

- Legal response deadline: 5 business days (with one 5-day extension permitted)
- Common response: partial fulfillment or request for clarification on date range
- If they cite volume: accept a rolling production or ask for records in batches by year
- Reference A51907 explicitly to establish continuity and narrow their response

---

## Why This Matters for the Site

The current FOIA data (A51907) has zero tickets from Sheffield, Kenmore, Clifton, or Clark. Those streets are directly adjacent to Wrigley Field and almost certainly the highest-volume enforcement streets in the zone. Without them:

- The ticket density map shows the wrong hotspots (western streets only)
- The "by street" chart in the data explorer is fabricated estimates, not real data
- The enforcement peak times article may be accurate but can't be verified for the core zone

When the second FOIA comes back, update:
1. `scripts/geocode_tickets.py` -- merge both datasets, re-run
2. `data/ticket-map-data.json` -- regenerate from merged data
3. `resources/lv2-data-explorer/index.html` -- replace estimated `streetData` with real numbers
4. `blog/lv2-data-analysis.html` and `blog/lv2-enforcement-peak-times.html` -- update stats
