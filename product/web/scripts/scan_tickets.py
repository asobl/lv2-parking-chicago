#!/usr/bin/env python3
"""
LV2 Park -- Ticket Scanner
Scans Chicago eHearing portal for LV2 (RESIDENTIAL PERMIT) violations
near Wrigleyville to power the live enforcement ticker.

Usage:
  python scripts/scan_tickets.py --date 2026-04-12 --find-range --limit 2000
  python scripts/scan_tickets.py --production

How it works:
  - POSTs to parkingtickets.chicago.gov with batches of 3 ticket IDs
  - Ticket IDs are mostly sequential within officer device sessions
  - Filters results for RESIDENTIAL PERMIT violations on LV2-area streets
"""

import argparse
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ── SSL context ───────────────────────────────────────────────────────────────
try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _CTX = None

# ── Constants ─────────────────────────────────────────────────────────────────
EHEARING_HOME   = 'https://parkingtickets.chicago.gov/EHearingWeb/home'
EHEARING_SEARCH = 'https://parkingtickets.chicago.gov/EHearingWeb/displayEligibleTickets'
USER_AGENT      = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
DELAY_SECS             = 0.4   # between requests -- polite rate
BATCH_SIZE             = 3     # portal max per request
PRODUCTION_WINDOW_HALF = 3750  # scan ±this many IDs from center = 7,500 total per run
DAILY_CENTER_SHIFT     = 4000  # IDs the center moves forward each day

# Streets inside the LV2 zone (from FOIA top-street analysis)
# Used to filter RESIDENTIAL PERMIT tickets to Wrigleyville only
LV2_STREETS = [
    'N MARSHFIELD', 'N PAULINA', 'N HERMITAGE',
    'W ROSCOE', 'W BELLE PLAINE', 'W SCHOOL', 'W PATTERSON',
    'W CORNELIA', 'W NEWPORT', 'W WAVELAND', 'W ADDISON',
    'N SHEFFIELD', 'N KENMORE', 'N CLIFTON', 'N SEMINARY',
    'N SOUTHPORT', 'W GRACE', 'W BYRON', 'W FLETCHER',
    'W OAKDALE', 'W BARRY', 'N GREENVIEW', 'N WOLCOTT',
]

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
STATE_FILE  = os.path.join(PROJECT_DIR, 'data', 'ticker_state.json')
OUTPUT_FILE = os.path.join(PROJECT_DIR, 'data', 'enforcement-today.json')


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def make_opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=_CTX),
    )

def get_csrf(opener):
    req = urllib.request.Request(EHEARING_HOME, headers={
        'User-Agent': USER_AGENT, 'Accept': 'text/html',
    })
    with opener.open(req, timeout=12) as r:
        body = r.read().decode('utf-8', errors='ignore')
    m = re.search(r'name="_csrf"[^>]+value="([^"]+)"', body)
    return m.group(1) if m else ''

def lookup_batch(opener, csrf, ticket_ids):
    """POST up to 3 ticket IDs. Returns raw HTML response."""
    ids = list(ticket_ids) + [''] * (BATCH_SIZE - len(ticket_ids))
    payload = urllib.parse.urlencode({
        '_csrf': csrf,
        'ticket1': ids[0],
        'ticket2': ids[1],
        'ticket3': ids[2],
    }).encode()
    req = urllib.request.Request(
        EHEARING_SEARCH,
        data=payload,
        headers={
            'User-Agent':    USER_AGENT,
            'Content-Type':  'application/x-www-form-urlencoded',
            'Referer':       EHEARING_HOME,
            'Accept':        'text/html',
        },
    )
    try:
        with opener.open(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'  [warn] request error: {e}')
        return ''

def parse_tickets(html):
    """
    Extract ticket records from the results table HTML.
    Returns list of dicts: {ticket_id, violation, plate, state, date, amount}.
    """
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    # Pattern: 10-digit ID, description (caps + spaces), plate, state (2 letters),
    #          date MM/DD/YYYY, dollar amount
    pattern = re.compile(
        r'(\d{10})\s+'
        r'((?:[A-Z0-9][A-Z0-9 /\-\(\)]{2,50}?))\s+'
        r'([A-Z0-9]{2,10})\s+'
        r'([A-Z]{2})\s+'
        r'(\d{2}/\d{2}/\d{4})\s+'
        r'\$(\d+\.\d{2})'
    )
    results = []
    for m in pattern.finditer(text):
        results.append({
            'ticket_id':  m.group(1),
            'violation':  m.group(2).strip(),
            'plate':      m.group(3),
            'state':      m.group(4),
            'date':       m.group(5),
            'amount':     m.group(6),
        })
    return results

def is_lv2_ticket(ticket):
    """True if this looks like an LV2 Wrigleyville residential permit violation."""
    v = ticket.get('violation', '').upper()
    return 'RESIDENTIAL PERMIT' in v


# ── Core scanner ──────────────────────────────────────────────────────────────

def scan_range(start_id, count, target_date=None, verbose=True):
    """
    Scan `count` ticket IDs starting at start_id.
    If target_date (MM/DD/YYYY), only collect tickets from that date.
    Returns (all_tickets, lv2_tickets, last_id_checked).
    """
    opener  = make_opener()
    csrf    = get_csrf(opener)
    if not csrf:
        print('[scan] ERROR: could not get CSRF token from eHearing portal')
        sys.exit(1)

    all_found  = []
    lv2_found  = []
    ids        = [str(start_id + i) for i in range(count)]
    batches    = [ids[i:i+BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
    total_reqs = len(batches)

    print(f'[scan] Scanning {count} IDs ({total_reqs} requests) '
          f'from {start_id} to {start_id + count - 1}')
    if target_date:
        print(f'[scan] Filtering for date: {target_date}')

    requests_since_refresh = 0
    for i, batch in enumerate(batches):
        # Refresh CSRF/session every 50 requests to avoid session expiry
        if requests_since_refresh >= 50:
            csrf = get_csrf(opener)
            requests_since_refresh = 0

        html = lookup_batch(opener, csrf, batch)
        tickets = parse_tickets(html)
        requests_since_refresh += 1

        for t in tickets:
            if target_date and t['date'] != target_date:
                continue
            all_found.append(t)
            if is_lv2_ticket(t):
                lv2_found.append(t)
                if verbose:
                    print(f'  [LV2] {t["ticket_id"]} | {t["violation"]} | '
                          f'{t["plate"]} {t["state"]} | {t["date"]} | ${t["amount"]}')

        if verbose and i % 20 == 0 and i > 0:
            print(f'  [{i}/{total_reqs} batches] found {len(lv2_found)} LV2 so far ...')

        time.sleep(DELAY_SECS)

    last_id = start_id + count - 1
    return all_found, lv2_found, last_id


def probe_id(opener, csrf, ticket_id):
    """Check a single ticket ID. Returns date string MM/DD/YYYY or None."""
    html = lookup_batch(opener, csrf, [str(ticket_id)])
    tickets = parse_tickets(html)
    return tickets[0]['date'] if tickets else None

def find_date_anchor(known_id, target_date_str, max_back=8000):
    """
    Binary-search backwards from known_id to find the start of target_date's tickets.
    Much faster than linear scan -- uses probe IDs to home in on the date boundary.
    Target date format: MM/DD/YYYY
    """
    print(f'[scan] Binary-searching backwards from {known_id} for {target_date_str} ...')
    opener = make_opener()
    csrf   = get_csrf(opener)

    # Phase 1: coarse jumps of 500 to find which 500-ID window contains target_date
    print(f'[scan] Phase 1: coarse scan (500-ID jumps) ...')
    low  = known_id - max_back
    high = known_id
    jump = 500

    left_edge  = None  # first ID where we see target_date tickets
    right_edge = None  # last ID where we see target_date tickets

    probe = high
    while probe >= low:
        time.sleep(DELAY_SECS)
        date_found = probe_id(opener, csrf, probe)
        print(f'  probe {probe}: {date_found or "no ticket"}')
        if date_found == target_date_str:
            right_edge = probe
            # Keep going back to find where it starts
            probe -= jump
        elif date_found is None:
            # Gap -- keep going
            probe -= jump
        else:
            # Different date -- we've gone too far or not far enough
            if right_edge is not None:
                # We passed the left edge of target_date -- stop
                left_edge = probe + jump
                break
            probe -= jump

    if right_edge is None:
        print(f'[scan] No tickets found for {target_date_str} in {max_back} IDs back.')
        return None

    # Phase 2: fine scan -- scan 100 IDs around left_edge to find earliest ticket
    start_fine = (left_edge or low) - 100
    print(f'[scan] Phase 2: fine scan from {start_fine} ...')
    found_ids = []
    requests_since_refresh = 0
    for i in range(0, 300, BATCH_SIZE):
        ids = [str(start_fine + i + j) for j in range(BATCH_SIZE)]
        if requests_since_refresh >= 50:
            csrf = get_csrf(opener)
            requests_since_refresh = 0
        html = lookup_batch(opener, csrf, ids)
        tickets = parse_tickets(html)
        requests_since_refresh += 1
        for t in tickets:
            if t['date'] == target_date_str:
                found_ids.append(int(t['ticket_id']))
        time.sleep(DELAY_SECS)

    if found_ids:
        earliest = min(found_ids)
        print(f'[scan] Earliest {target_date_str} ticket: {earliest}')
        return earliest

    # Fall back to right_edge if fine scan found nothing
    print(f'[scan] Using right_edge {right_edge} as anchor')
    return right_edge


# ── Modes ─────────────────────────────────────────────────────────────────────

def run_test(date_str, limit):
    """
    Test mode: scan for LV2 tickets on a specific historical game date.
    date_str: YYYY-MM-DD
    """
    # Convert to MM/DD/YYYY for portal comparison
    y, m, d = date_str.split('-')
    portal_date = f'{m}/{d}/{y}'

    ANCHOR = 9205512432   # confirmed April 15 2026 ticket

    print(f'=== LV2 Ticker Test: {date_str} ===')
    print(f'Anchor ticket: {ANCHOR} (confirmed 04/15/2026)')
    print()

    # Step 1: find first ticket from target date by scanning backwards
    anchor_for_date = find_date_anchor(ANCHOR, portal_date, max_back=5000)

    if anchor_for_date is None:
        # Tickets may have been purged or range is further back than expected
        # Fall back: try scanning a wide range from 3000 below anchor
        print(f'[scan] No anchor found. Trying wide scan from {ANCHOR - 3000} ...')
        anchor_for_date = ANCHOR - 3000

    # Step 2: scan forward from anchor for `limit` IDs
    print()
    all_tickets, lv2_tickets, last_id = scan_range(
        anchor_for_date, limit, target_date=portal_date, verbose=True
    )

    # Step 3: results
    print()
    print('=' * 60)
    print(f'TEST RESULTS: {date_str}')
    print('=' * 60)
    print(f'IDs scanned:        {limit}')
    print(f'Tickets found:      {len(all_tickets)} total on that date')
    print(f'LV2 tickets found:  {len(lv2_tickets)}')
    print()

    if lv2_tickets:
        print('LV2 tickets detail:')
        for t in lv2_tickets:
            print(f'  {t["ticket_id"]}  {t["violation"]:<40}  {t["plate"]} {t["state"]}  {t["date"]}  ${t["amount"]}')
        print()
        print(f'PASS -- found {len(lv2_tickets)} LV2 tickets for {date_str}')
        if len(lv2_tickets) < 5:
            print('NOTE: low count. May need wider scan (try --limit 5000).')
        elif len(lv2_tickets) > 100:
            print('NOTE: high count. Check address filter -- may include non-LV2 zones.')
    else:
        print('FAIL -- 0 LV2 tickets found.')
        print('Possible causes:')
        print('  1. Tickets older than ~2 weeks may be purged from the portal')
        print('  2. Scanner missed the ID range -- try --limit 5000')
        print('  3. April 12 enforcement was unusually light')
        print()
        print('Try a more recent game date, e.g., --date 2026-04-10 or --date 2026-04-11')

    print()
    print(f'Other violation types found on {date_str}:')
    viol_counts = {}
    for t in all_tickets:
        v = t['violation'][:40]
        viol_counts[v] = viol_counts.get(v, 0) + 1
    for v, cnt in sorted(viol_counts.items(), key=lambda x: -x[1])[:10]:
        marker = ' <-- LV2' if 'RESIDENTIAL PERMIT' in v else ''
        print(f'  {cnt:3d}x  {v}{marker}')


def run_production():
    """
    Production mode: scan a fixed 7,500-ID window centered on today's range.
    Each run is a full rescan -- count is all LV2 tickets found in that window today.
    Window center shifts ~4,000 IDs per day to track the city's issuing sequence.

    Key insight from Phase 1: ticket IDs from different dates interleave (different
    officer devices have different ID ranges). A watermark approach misses tickets
    from officers with lower device IDs. Fixed daily window + date filter is correct.
    """
    try:
        import zoneinfo
        tz_ct = zoneinfo.ZoneInfo('America/Chicago')
    except ImportError:
        import datetime as _dt
        tz_ct = _dt.timezone(_dt.timedelta(hours=-5))  # CDT fallback

    now_ct      = datetime.now(tz_ct)
    today       = now_ct.strftime('%Y-%m-%d')
    portal_date = now_ct.strftime('%m/%d/%Y')

    # Load state
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)

    center = state.get('window_center')
    if not center:
        print('[ticker] ERROR: no window_center in ticker_state.json')
        print('Run:  python scripts/scan_tickets.py --bootstrap')
        sys.exit(1)

    # New day: shift window center forward
    if state.get('window_date') != today:
        center = center + DAILY_CENTER_SHIFT
        print(f'[ticker] New day ({today}). Window center shifted to {center}')

    start = center - PRODUCTION_WINDOW_HALF
    all_t, lv2_t, _ = scan_range(
        start, PRODUCTION_WINDOW_HALF * 2, target_date=portal_date, verbose=False
    )

    # Update state
    state['window_center'] = center
    state['window_date']   = today
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

    # Write output
    output = {
        'date':              today,
        'lv2_tickets_today': len(lv2_t),
        'last_checked':      datetime.now(timezone.utc).isoformat(),
        'scan_ok':           True,
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f'[ticker] {today}: {len(lv2_t)} LV2 tickets in window. Center: {center}')


def run_bootstrap():
    """
    Seed ticker_state.json with today's window center.
    Run once on first production deploy, or after a gap of 7+ days.

    Phase 1: coarse probe in 1,000-ID jumps to find the frontier quickly.
    Phase 2: fine scan of 2,000 IDs around the latest ticket found.
    Total time: ~5-6 minutes.
    """
    ANCHOR       = 9205512432   # confirmed April 15 2026 -- permanent reference point
    COARSE_STEPS = 60           # up to 60,000 IDs forward (covers ~15 days of drift)
    COARSE_JUMP  = 1000

    print(f'[bootstrap] Phase 1: coarse probe from anchor {ANCHOR} ({COARSE_STEPS} steps × {COARSE_JUMP} IDs) ...')
    opener = make_opener()
    csrf   = get_csrf(opener)

    latest_id   = ANCHOR
    latest_date = None
    current     = ANCHOR

    for step in range(COARSE_STEPS):
        date = probe_id(opener, csrf, current)
        if date:
            print(f'  step {step+1:2d}: {current} → {date}')
            latest_id   = current
            latest_date = date
        elif step % 10 == 0:
            print(f'  step {step+1:2d}: {current} → (no ticket)')
        current += COARSE_JUMP
        time.sleep(DELAY_SECS)

    print(f'[bootstrap] Latest ticket found: {latest_id} dated {latest_date}')
    print(f'[bootstrap] Phase 2: fine scan 2,000 IDs around {latest_id} ...')

    fine_start = latest_id - 500
    requests_since_refresh = 0
    for i in range(0, 2000, BATCH_SIZE):
        if requests_since_refresh >= 50:
            csrf = get_csrf(opener)
            requests_since_refresh = 0
        ids  = [str(fine_start + i + j) for j in range(BATCH_SIZE)]
        html = lookup_batch(opener, csrf, ids)
        for t in parse_tickets(html):
            tid = int(t['ticket_id'])
            if tid > latest_id:
                latest_id   = tid
                latest_date = t['date']
                print(f'  Fine scan found {tid} dated {latest_date}')
        requests_since_refresh += 1
        time.sleep(DELAY_SECS)

    state = {
        'window_center': latest_id,
        'window_date':   datetime.now(timezone.utc).strftime('%Y-%m-%d'),
    }
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f'[bootstrap] Done. window_center={latest_id}, window_date={state["window_date"]}')
    print(f'[bootstrap] Saved to ticker_state.json. Store this as the TICKER_STATE GitHub secret.')


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LV2 Park ticket scanner')
    parser.add_argument('--date',        help='Target date YYYY-MM-DD (test mode)')
    parser.add_argument('--find-range',  action='store_true', help='Scan backwards to find date range anchor')
    parser.add_argument('--limit',       type=int, default=2000, help='IDs to scan forward (default 2000)')
    parser.add_argument('--production',  action='store_true', help='Production mode: scan from watermark')
    parser.add_argument('--bootstrap',   action='store_true', help='Set initial high-watermark')
    args = parser.parse_args()

    if args.bootstrap:
        run_bootstrap()
    elif args.production:
        run_production()
    elif args.date:
        run_test(args.date, args.limit)
    else:
        parser.print_help()
