"""
fetch_data.py
Daily data pipeline for lv2park.com

Runs via GitHub Actions cron at 6 AM CT and 3 PM CT.
Writes: data/today.json, data/week.json, data/health.json

Fallback chain:
  1. MLB Stats API (primary)
  2. ESPN public API (fallback)
  3. Keep existing data if both fail
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
import pytz

# ─── LOAD .env (local development only) ───────────────
def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, val = line.partition('=')
            key = key.strip()
            val = val.strip()
            if key and val and key not in os.environ:
                os.environ[key] = val

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────
TM_API_KEY   = os.environ.get('TM_API_KEY', '')
# Venue IDs in Ticketmaster
# Wrigley Field has two separate listings -- query both
WRIGLEY_TM_VENUES = ['KovZpZAFlktA', 'ZFr9jZe1vk']
# Gallagher Way (adjacent plaza) -- events here do NOT trigger LV2
GALLAGHER_TM_VENUE = 'Z7r9jZady5'

CUBS_TEAM_ID  = 112   # MLB Stats API
ESPN_TEAM_ID  = 16    # ESPN API

CT = pytz.timezone('America/Chicago')

MLB_URL  = 'https://statsapi.mlb.com/api/v1/schedule'
ESPN_URL = f'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{ESPN_TEAM_ID}/schedule'
TM_URL   = 'https://app.ticketmaster.com/discovery/v2/events.json'

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# MLB game status values that mean the game is actually happening
ACTIVE_STATUSES  = {'Scheduled', 'Pre-Game', 'In Progress', 'Delayed', 'Warmup', 'Manager Challenge'}
GONE_STATUSES    = {'Postponed', 'Cancelled', 'Suspended', 'Final', 'Game Over', 'Not Necessary'}


# ─── DATE HELPERS ─────────────────────────────────────
def today_ct():
    return datetime.now(CT).date()

def date_range_str(days=7):
    start = today_ct()
    end   = start + timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()

def fmt_time_ct(utc_iso):
    """Convert UTC ISO string to '1:20 PM' in CT."""
    if not utc_iso:
        return 'TBD'
    try:
        dt = datetime.fromisoformat(utc_iso.replace('Z', '+00:00'))
        ct_dt = dt.astimezone(CT)
        return ct_dt.strftime('%-I:%M %p')
    except Exception:
        return utc_iso

def day_label(date_str):
    """'2026-04-17' → 'Fri Apr 17'"""
    d = datetime.strptime(date_str, '%Y-%m-%d').date()
    return d.strftime('%a %b %-d')


# ─── MLB STATS API ────────────────────────────────────
def fetch_mlb():
    start, end = date_range_str(180)
    params = {
        'sportId': 1,
        'teamId': CUBS_TEAM_ID,
        'startDate': start,
        'endDate': end,
        'hydrate': 'venue,game(content(summary)),status'
    }
    try:
        resp = requests.get(MLB_URL, params=params, timeout=10)
        resp.raise_for_status()
        return parse_mlb(resp.json()), 'mlb'
    except Exception as e:
        print(f'[MLB API] failed: {e}', file=sys.stderr)
        return None, 'error'


def parse_mlb(data):
    """Return list of game dicts from MLB Stats API response."""
    games = []
    for date_block in data.get('dates', []):
        for game in date_block.get('games', []):
            venue = game.get('venue', {}).get('name', '')
            if venue != 'Wrigley Field':
                continue  # Away game

            status = game.get('status', {}).get('detailedState', 'Scheduled')
            date_str = game.get('gameDate', '')[:10]  # '2026-04-17'
            time_utc = game.get('gameDate', '')

            # Build a human-readable name
            away = game.get('teams', {}).get('away', {}).get('team', {}).get('name', 'Away Team')
            home = game.get('teams', {}).get('home', {}).get('team', {}).get('name', 'Cubs')
            name = f'{away} vs. Cubs'

            games.append({
                'date':    date_str,
                'name':    name,
                'time':    fmt_time_ct(time_utc),
                'timeUtc': time_utc,
                'type':    'game',
                'status':  status,
                'source':  'mlb'
            })
    return games


# ─── ESPN FALLBACK ────────────────────────────────────
def fetch_espn():
    try:
        resp = requests.get(ESPN_URL, timeout=10)
        resp.raise_for_status()
        return parse_espn(resp.json()), 'espn'
    except Exception as e:
        print(f'[ESPN API] failed: {e}', file=sys.stderr)
        return None, 'error'


def parse_espn(data):
    games = []
    today = today_ct()
    cutoff = today + timedelta(days=180)

    for event in data.get('events', []):
        # Check venue
        competitions = event.get('competitions', [{}])
        if not competitions:
            continue
        comp = competitions[0]
        venue_name = comp.get('venue', {}).get('fullName', '')
        if 'Wrigley' not in venue_name:
            continue

        date_str = event.get('date', '')[:10]
        if date_str < today.isoformat() or date_str > cutoff.isoformat():
            continue

        # Opponent name
        competitors = comp.get('competitors', [])
        away_name = 'Away Team'
        for c in competitors:
            if c.get('homeAway') == 'away':
                away_name = c.get('team', {}).get('displayName', 'Away Team')

        time_utc = event.get('date', '')
        status = event.get('status', {}).get('type', {}).get('description', 'Scheduled')

        games.append({
            'date':    date_str,
            'name':    f'{away_name} vs. Cubs',
            'time':    fmt_time_ct(time_utc),
            'timeUtc': time_utc,
            'type':    'game',
            'status':  status,
            'source':  'espn'
        })
    return games


# ─── TICKETMASTER API ─────────────────────────────────
def fetch_ticketmaster():
    if not TM_API_KEY:
        print('[TM API] no key, skipping', file=sys.stderr)
        return []

    start, end = date_range_str(180)
    all_events = []

    # Query both Wrigley venue IDs
    for venue_id in WRIGLEY_TM_VENUES:
        params = {
            'apikey':        TM_API_KEY,
            'venueId':       venue_id,
            'startDateTime': f'{start}T00:00:00Z',
            'endDateTime':   f'{end}T23:59:59Z',
            'size':          50
        }
        try:
            resp = requests.get(TM_URL, params=params, timeout=10)
            resp.raise_for_status()
            all_events.extend(parse_ticketmaster(resp.json(), lv2=True))
        except Exception as e:
            print(f'[TM API] venue {venue_id} failed: {e}', file=sys.stderr)

    # Query Gallagher Way -- adjacent plaza, does NOT trigger LV2
    params_gw = {
        'apikey':        TM_API_KEY,
        'venueId':       GALLAGHER_TM_VENUE,
        'startDateTime': f'{start}T00:00:00Z',
        'endDateTime':   f'{end}T23:59:59Z',
        'size':          20
    }
    try:
        resp = requests.get(TM_URL, params=params_gw, timeout=10)
        resp.raise_for_status()
        gw_events = parse_ticketmaster(resp.json(), lv2=False, venue_label='Gallagher Way')
        all_events.extend(gw_events)
        if gw_events:
            print(f'[TM API] Gallagher Way: {len(gw_events)} events')
    except Exception as e:
        print(f'[TM API] Gallagher Way failed: {e}', file=sys.stderr)

    return dedup_tm_events(all_events)


def parse_ticketmaster(data, lv2=True, venue_label=None):
    events = []
    for ev in data.get('_embedded', {}).get('events', []):
        name = ev.get('name', 'Event at Wrigley')

        # Skip Cubs baseball games -- MLB API covers those
        name_lower = name.lower()
        if 'chicago cubs vs' in name_lower:
            continue
        if name_lower.startswith('chicago cubs'):
            continue

        # Skip platinum/VIP duplicate listings -- we keep the base event
        skip_suffixes = ['platinum', 'vip', 'meet & greet', 'meet and greet',
                         'fan package', 'presale', 'gold circle']
        if any(s in name_lower for s in skip_suffixes):
            continue

        # Date and time
        dates = ev.get('dates', {})
        start = dates.get('start', {})
        date_str = start.get('localDate', '')
        time_local = start.get('localTime', '')

        if time_local:
            h, m, *_ = time_local.split(':')
            h = int(h)
            am_pm = 'AM' if h < 12 else 'PM'
            h12 = h % 12 or 12
            time_fmt = f'{h12}:{m} {am_pm}'
        else:
            time_fmt = 'TBD'

        display_name = f'{name} (Gallagher Way)' if venue_label else name
        events.append({
            'date':    date_str,
            'name':    display_name,
            'time':    time_fmt,
            'timeUtc': start.get('dateTime', ''),
            'type':    'concert',
            'status':  'Scheduled',
            'source':  'ticketmaster',
            'lv2':     lv2
        })
    return events


def dedup_tm_events(events):
    """Remove duplicate events on the same date.
    Same concert is often listed under both Wrigley venue IDs with slightly different names.
    Key on date + first two words of name (catches 'Tyler Childers - Snipe Hunt' vs 'Tyler Childers w/ Jon Batiste').
    When there's a duplicate, keep the shorter/cleaner name (fewer hyphens and 'w/' notation).
    """
    seen = {}
    for ev in events:
        words = ev['name'].split()
        name_key = ' '.join(words[:2]).lower().strip(' -')
        key = (ev['date'], name_key)
        if key not in seen:
            seen[key] = ev
        else:
            # Prefer the cleaner name: shorter, no 'w/', no ' - '
            existing = seen[key]['name']
            candidate = ev['name']
            if len(candidate) < len(existing) and 'w/' not in candidate:
                seen[key] = ev
    return list(seen.values())


# ─── MANUAL OVERRIDES ─────────────────────────────────
def load_overrides():
    path = os.path.join(DATA_DIR, 'overrides.json')
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get('overrides', [])
    except Exception:
        return []


# ─── LV2 LOGIC ────────────────────────────────────────
def is_lv2_active(has_event, events):
    """LV2 is active on any game or major event day. Site shows heads-up all day."""
    if not has_event:
        return False
    # Private events flagged as lv2=false don't trigger it
    for ev in events:
        if ev.get('lv2') is False:
            continue
        return True
    return True


def event_note(events):
    """Return a note string if any event has a non-standard status."""
    for ev in events:
        s = ev.get('status', 'Scheduled')
        if s == 'Postponed':
            return 'Game postponed -- LV2 not in effect today'
        if s == 'Cancelled':
            return 'Game cancelled -- LV2 not in effect today'
        if s == 'Delayed':
            return 'Rain delay -- LV2 still in effect. Check back for updates.'
        if s == 'Suspended':
            return 'Game suspended -- check mlb.com for status'
    return None


def has_real_event(events):
    """True if any event is not postponed/cancelled."""
    if not events:
        return False
    for ev in events:
        if ev.get('status', 'Scheduled') not in GONE_STATUSES:
            return True
    return False


# ─── BUILD OUTPUT DICTS ───────────────────────────────
def build_day(date_str, events, now_ct=None):
    active_events = [e for e in events if e.get('status', 'Scheduled') not in GONE_STATUSES]
    has_event = bool(active_events)
    lv2 = is_lv2_active(has_event, active_events)

    # Enforcement window override: LV2 is active 5–10 PM on any game day,
    # even if the game finished early (status=Final). A day game ending at 4 PM
    # does not cancel the evening enforcement window.
    if not lv2 and now_ct and date_str == now_ct.date().isoformat() and 17 <= now_ct.hour < 22:
        enforcement_events = [
            e for e in events
            if e.get('lv2') is not False and e.get('status') not in {'Postponed', 'Cancelled', 'Not Necessary'}
        ]
        if enforcement_events:
            lv2 = True
            has_event = True
            active_events = enforcement_events  # show the game even though it's Final

    note = event_note(events)

    return {
        'date':     date_str,
        'dayLabel': day_label(date_str),
        'hasEvent': has_event,
        'lv2Active': lv2,
        'note':     note,
        'events': [
            {'name': e['name'], 'time': e['time'], 'type': e.get('type', 'game')}
            for e in active_events
        ]
    }


# ─── WRITE FILES ──────────────────────────────────────
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'[write] {path}')


def write_health(source, error=None):
    write_json(os.path.join(DATA_DIR, 'health.json'), {
        'updated': datetime.now(timezone.utc).isoformat(),
        'source':  source,
        'status':  'error' if error else 'ok',
        'error':   error
    })


# ─── MAIN ─────────────────────────────────────────────
def main():
    now_ct   = datetime.now(CT)
    today_str = now_ct.date().isoformat()
    now_utc = datetime.now(timezone.utc).isoformat()
    print(f'[run] {now_utc} — fetching data for {today_str}')

    # ── Step 1: MLB schedule (with ESPN fallback)
    games, mlb_source = fetch_mlb()
    if games is None:
        print('[fallback] trying ESPN...', file=sys.stderr)
        games, mlb_source = fetch_espn()

    if games is None:
        # Both APIs failed -- keep existing data, just update health
        print('[ERROR] both MLB and ESPN APIs failed. Keeping existing data.', file=sys.stderr)
        write_health('stale', error='Both MLB and ESPN APIs failed')
        sys.exit(1)  # Non-zero exit signals GitHub Actions to send failure email

    # ── Step 2: Ticketmaster events
    tm_events = fetch_ticketmaster()

    # ── Step 3: Manual overrides
    overrides = load_overrides()

    # ── Step 4: Merge all events by date
    all_events = games + tm_events + overrides
    by_date = {}
    for ev in all_events:
        d = ev.get('date', '')
        if not d:
            continue
        by_date.setdefault(d, []).append(ev)

    # ── Step 5: Build today.json
    today_events = by_date.get(today_str, [])
    today_day = build_day(today_str, today_events, now_ct=now_ct)
    today_json = {
        'date':      today_str,
        'updated':   now_utc,
        'source':    mlb_source,
        'hasEvent':  today_day['hasEvent'],
        'lv2Active': today_day['lv2Active'],
        'note':      today_day['note'],
        'events':    today_day['events']
    }
    write_json(os.path.join(DATA_DIR, 'today.json'), today_json)

    # ── Step 6: Load old week.json for change detection
    old_ev_map = {}  # { date_str: { event_name: event_dict } }
    old_week_path = os.path.join(DATA_DIR, 'week.json')
    if os.path.exists(old_week_path):
        try:
            with open(old_week_path) as f:
                old_week = json.load(f)
            for old_day in old_week.get('days', []):
                d_str = old_day['date']
                old_ev_map[d_str] = {ev['name']: ev for ev in old_day.get('events', [])}
        except Exception as e:
            print(f'[warn] could not load old week.json for diff: {e}')

    # ── Step 7: Build week.json (180 days, with change flags)
    today_iso = today_ct().isoformat()
    week_days = []
    for i in range(180):
        date_str = (today_ct() + timedelta(days=i)).isoformat()
        day_events = by_date.get(date_str, [])
        day = build_day(date_str, day_events)

        old_day_evs = old_ev_map.get(date_str, {})
        new_names = {ev['name'] for ev in day['events']}

        # Tag new events and time changes
        for ev in day['events']:
            old_ev = old_day_evs.get(ev['name'])
            if old_ev is None:
                if old_day_evs:  # Only flag new if we had prior data for this date
                    ev['changed'] = 'new'
            elif old_ev.get('time') and old_ev.get('time') != ev.get('time'):
                ev['changed'] = 'time'
                ev['prevTime'] = old_ev['time']

        # Re-surface recently cancelled events (were in old data, gone from new)
        for old_name, old_ev in old_day_evs.items():
            if old_name in new_names:
                continue
            changed_at = old_ev.get('changedAt', date_str)
            cutoff_date = (today_ct() - timedelta(days=3)).isoformat()
            if changed_at < cutoff_date:
                continue  # Cancelled more than 3 days ago — drop it
            cancelled = dict(old_ev)
            cancelled['changed'] = 'cancelled'
            cancelled['changedAt'] = old_ev.get('changedAt', today_iso)
            day['events'].append(cancelled)
            day['hasEvent'] = True

        week_days.append(day)

    week_json = {
        'updated': now_utc,
        'source':  mlb_source,
        'days':    week_days
    }
    write_json(os.path.join(DATA_DIR, 'week.json'), week_json)

    # ── Step 7: Health file
    write_health(mlb_source)

    print(f'[done] today: hasEvent={today_json["hasEvent"]}, lv2={today_json["lv2Active"]}')
    if today_json['events']:
        for ev in today_json['events']:
            print(f'  · {ev["name"]} at {ev["time"]}')


if __name__ == '__main__':
    main()
