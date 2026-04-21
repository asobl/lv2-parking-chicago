#!/usr/bin/env python3
"""
LV2 Park — Game-day recap page generator

For each past Cubs home game with LV2 enforcement, generates a static HTML page at:
  /game-recaps/YYYY-MM-DD-slug.html

Data layers per recap:
  - LV2 ticket counts + hot streets (from FOIA data or live scan logs)
  - Game result + attendance (MLB Stats API)
  - Weather (Weather.gov historical API)
  - Cubs record at that date (MLB Stats API)

Usage:
  python scripts/generate_recaps.py --season 2026       # generate all 2026 recaps so far
  python scripts/generate_recaps.py --date 2026-04-17   # single game
  python scripts/generate_recaps.py --preview           # build one page and open in browser

Run from repo root.
"""

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, date, timedelta

# SSL context — use certifi if available, otherwise fall back to unverified (local dev only)
try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = ssl._create_unverified_context()

def _open(url, timeout=15, headers=None):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': 'lv2park.com'})
    return urllib.request.urlopen(req, timeout=timeout, context=_SSL)

SITE_URL   = 'https://lv2park.com'
CUBS_TEAM  = 112        # MLB team ID for Cubs
WRIGLEY_LAT = 41.9484
WRIGLEY_LON = -87.6553

# NWS grid for Wrigley Field area
NWS_OFFICE  = 'LOT'
NWS_GRID_X  = 74
NWS_GRID_Y  = 71


# ── MLB API ──────────────────────────────────────────────────────────────────

def fetch_cubs_schedule(season):
    """Returns list of home game dicts for the season."""
    url = (f'https://statsapi.mlb.com/api/v1/schedule'
           f'?sportId=1&teamId={CUBS_TEAM}&season={season}'
           f'&gameType=R&hydrate=team,linescore,boxscore')
    with _open(url) as r:
        data = json.loads(r.read())

    games = []
    for date_entry in data.get('dates', []):
        for game in date_entry.get('games', []):
            venue = game.get('venue', {}).get('name', '')
            if 'Wrigley' not in venue:
                continue
            games.append({
                'date':         date_entry['date'],
                'game_pk':      game['gamePk'],
                'home':         game['teams']['home']['team']['name'],
                'home_team_id': game['teams']['home']['team']['id'],
                'away':         game['teams']['away']['team']['name'],
                'away_team_id': game['teams']['away']['team']['id'],
                'status':       game['status']['abstractGameState'],
                'home_score':   game['teams']['home'].get('score'),
                'away_score':   game['teams']['away'].get('score'),
                'attendance':   game.get('attendance'),
                'game_time':    game.get('gameDate', ''),
            })
    return games


def fetch_cubs_record_on_date(target_date, season):
    """Returns Cubs W-L record as of a given date."""
    url = (f'https://statsapi.mlb.com/api/v1/standings'
           f'?leagueId=103,104&season={season}&date={target_date}&hydrate=team')
    try:
        with _open(url) as r:
            data = json.loads(r.read())
        for record in data.get('records', []):
            for team_rec in record.get('teamRecords', []):
                if team_rec['team']['id'] == CUBS_TEAM:
                    w = team_rec['wins']
                    l = team_rec['losses']
                    return f'{w}–{l}'
    except Exception:
        pass
    return None


# ── Weather.gov ───────────────────────────────────────────────────────────────

def fetch_weather_for_date(target_date):
    """
    Returns weather summary for Wrigley on target_date (YYYY-MM-DD).
    Uses NWS gridpoint hourly forecast — works for past dates only via observations.
    Falls back to gridpoint daily forecast for near-future dates.
    """
    # For historical dates, use NWS observation stations
    # KMDW = Chicago Midway, closest reliable station
    try:
        obs_url = f'https://api.weather.gov/stations/KMDW/observations?start={target_date}T17:00:00Z&end={target_date}T22:00:00Z&limit=10'
        with _open(obs_url, headers={'User-Agent': 'lv2park.com weather fetch'}) as r:
            data = json.loads(r.read())

        features = data.get('features', [])
        if features:
            obs = features[0]['properties']
            temp_c = obs.get('temperature', {}).get('value')
            desc   = obs.get('textDescription', '')
            if temp_c is not None:
                temp_f = round(temp_c * 9/5 + 32)
                return {'temp_f': temp_f, 'desc': desc}
    except Exception:
        pass
    return None


# ── FOIA ticket data ──────────────────────────────────────────────────────────

def load_foia_street_totals():
    """
    Load ticket counts per street from ticket-map-data.json.
    Returns dict: normalized_street -> total_count
    """
    path = 'data/ticket-map-data.json'
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)

    streets = defaultdict(int)
    for p in data.get('points', []):
        addr = p.get('addr', '')
        parts = addr.split(' ', 1)
        if len(parts) > 1:
            streets[normalize_street(parts[1])] += p['count']
    return dict(streets)


def load_scan_log_for_date(target_date):
    """
    Load live scan data for a specific game date if it exists.
    Scan logs are stored at data/scans/YYYY-MM-DD.json
    Returns dict with ticket_count, peak_minute, hot_streets or None.
    """
    path = f'data/scans/{target_date}.json'
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def normalize_street(name):
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    # Normalize abbreviations
    name = re.sub(r'\bAve\b\.?', 'Ave', name)
    name = re.sub(r'\bSt\b\.?', 'St', name)
    name = re.sub(r'\bBlvd\b\.?', 'Blvd', name)
    return name


# ── HTML generator ────────────────────────────────────────────────────────────

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def build_recap_page(game, weather, cubs_record, scan_data, foia_streets):
    game_date   = game['date']
    away_team    = game['away'].replace(' Cubs', '').replace('Chicago ', '')
    away_team_id = game.get('away_team_id', '')
    home_team_id = game.get('home_team_id', CUBS_TEAM)
    home_score   = game.get('home_score', '')
    away_score   = game.get('away_score', '')
    attendance  = game.get('attendance', '')
    status      = game.get('status', '')

    dt = datetime.strptime(game_date, '%Y-%m-%d')
    date_display = dt.strftime('%B %-d, %Y')
    day_display  = dt.strftime('%A')

    # Win/loss
    result_html = ''
    if status == 'Final' and home_score is not None and away_score is not None:
        if home_score > away_score:
            result_html = f'<span style="color:#2a9d5c;font-weight:700;">Cubs won {home_score}–{away_score}</span>'
        elif away_score > home_score:
            result_html = f'<span style="color:#e84040;font-weight:700;">Cubs lost {away_score}–{home_score}</span>'
        else:
            result_html = f'<span style="font-weight:700;">Tied {home_score}–{away_score}</span>'
    elif status == 'Final':
        result_html = '<span style="font-weight:700;">Final</span>'

    # Weather line
    weather_html = ''
    if weather:
        weather_html = f'{weather["temp_f"]}°F · {weather["desc"]}'

    # Record
    record_html = f'Cubs {cubs_record}' if cubs_record else ''

    # Attendance
    attendance_html = f'{attendance:,} fans' if attendance else ''

    # Game meta line
    meta_parts = [p for p in [weather_html, record_html, attendance_html] if p]
    meta_line = ' · '.join(meta_parts)

    # LV2 enforcement data
    if scan_data:
        ticket_count = scan_data.get('ticket_count', 0)
        peak_minute  = scan_data.get('peak_minute', '')
        hot_streets  = scan_data.get('hot_streets', [])[:5]
        enforcement_html = _build_enforcement_from_scan(ticket_count, peak_minute, hot_streets)
    else:
        # Fall back to FOIA averages with disclaimer
        enforcement_html = _build_enforcement_from_foia(foia_streets, game_date)

    # Top FOIA streets sidebar
    top_streets = sorted(foia_streets.items(), key=lambda x: -x[1])[:10]
    streets_rows = ''
    for street, count in top_streets:
        pct = min(100, round(count / top_streets[0][1] * 100))
        streets_rows += f'''
        <tr>
          <td style="padding:8px 0;font-size:13px;color:#1A1A2E;border-bottom:1px solid #F0EFF0;">{street}</td>
          <td style="padding:8px 0 8px 12px;text-align:right;font-size:13px;font-weight:700;color:#1A1A2E;border-bottom:1px solid #F0EFF0;white-space:nowrap;">{count:,}</td>
        </tr>'''

    slug = f'{game_date}-cubs-vs-{slugify(away_team)}'
    canonical = f'{SITE_URL}/game-recaps/{slug}.html'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LV2 Parking: Cubs vs. {away_team} — {date_display} | LV2 Park</title>
  <meta name="description" content="LV2 parking enforcement data for the Cubs vs. {away_team} game on {date_display} at Wrigley Field. Ticket counts, hottest streets, and game day details.">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="LV2 Enforcement: Cubs vs. {away_team} — {date_display}">
  <meta property="og:description" content="LV2 parking data for this Wrigley game day. Which streets got the most tickets and when enforcement peaked.">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="LV2 Park">
  <meta property="og:image" content="{SITE_URL}/og-image.png">
  <meta name="theme-color" content="#1A1A2E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <div class="top-bar">
    <div class="top-bar-inner">
      <a class="site-logo" href="/">LV2 <span>PARK</span></a>
      <nav class="top-nav">
        <a href="/" class="top-nav-link">Today</a>
        <a href="/resources/lv2-parking-rules/" class="top-nav-link">Rules</a>
        <a href="/resources/lv2-parking-map/" class="top-nav-link">Map</a>
        <a href="/resources/cubs-game-day-parking/" class="top-nav-link">Game Day</a>
        <a href="/resources/lv2-data-explorer/" class="top-nav-link">Data</a>
      </nav>
    </div>
  </div>

  <div class="article-wrap">

    <div class="article-hero">
      <span class="cat-tag rc-data" style="margin-bottom:16px;">Game Recap</span>

      <!-- Team matchup logos -->
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <img src="https://www.mlbstatic.com/team-logos/{away_team_id}.svg"
             alt="{away_team} logo" width="64" height="64"
             style="border-radius:50%;background:#f5f4f0;padding:4px;"
             onerror="this.style.display='none'">
        <div style="font-size:22px;font-weight:900;color:#D0CFDA;">vs</div>
        <img src="https://www.mlbstatic.com/team-logos/{home_team_id}.svg"
             alt="Cubs logo" width="64" height="64"
             style="border-radius:50%;background:#f5f4f0;padding:4px;"
             onerror="this.style.display='none'">
      </div>

      <h1 class="article-h1">{away_team} vs. Cubs — LV2 parking</h1>
      <p class="article-intro">{day_display}, {date_display}</p>
      <div class="article-meta">
        {result_html}
        {f'<span style="margin:0 8px;color:#D0CFDA;">·</span>{meta_line}' if meta_line else ''}
      </div>
    </div>

    <div class="article-body">

      {enforcement_html}

      <h2>Historically ticketed streets near Wrigley</h2>
      <p>Based on 9,434 LV2 tickets issued 2018–2023. These streets see the most enforcement activity on game days.</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:28px;">
        <thead>
          <tr>
            <th style="text-align:left;font-size:11px;font-weight:700;color:#6B6B80;text-transform:uppercase;letter-spacing:.08em;padding:0 0 8px;border-bottom:2px solid #EEEDF0;">Street</th>
            <th style="text-align:right;font-size:11px;font-weight:700;color:#6B6B80;text-transform:uppercase;letter-spacing:.08em;padding:0 0 8px 12px;border-bottom:2px solid #EEEDF0;">Total tickets (2018–23)</th>
          </tr>
        </thead>
        <tbody>{streets_rows}</tbody>
      </table>

      <div class="callout callout-info">
        <div class="callout-label">How LV2 enforcement works</div>
        <p>Officers are staged and ready before 5 PM. The moment the clock hits 5:00, they start writing.
        By 5:03 PM, 40+ tickets have already been issued on a typical game day. There is no grace period.
        <a href="/blog/what-is-lv2.html">Learn more about LV2 →</a></p>
      </div>

      <h2>Related game days</h2>
    </div>

    <div class="related-grid" style="margin-top:0;">
      <a class="related-card" href="/resources/lv2-parking-rules/">
        <span class="related-card-badge rc-rules">Rules</span>
        <div class="related-card-title">LV2 Parking Rules</div>
        <div class="related-card-desc">What LV2 is, when it's in effect, and how to avoid a tow.</div>
      </a>
      <a class="related-card" href="/resources/lv2-parking-map/">
        <span class="related-card-badge rc-map">Map</span>
        <div class="related-card-title">LV2 Zone Map</div>
        <div class="related-card-desc">Interactive map of every street in the LV2 enforcement zone.</div>
      </a>
      <a class="related-card" href="/resources/lv2-data-explorer/">
        <span class="related-card-badge rc-data">Data</span>
        <div class="related-card-title">Ticket Data Explorer</div>
        <div class="related-card-desc">Look up any street in the LV2 zone. See its full ticket history.</div>
      </a>
    </div>

  </div>

  <footer>
    <div class="footer-inner">
      <div class="footer-logo">LV2 <span>PARK</span></div>
      <p class="footer-disclaimer">LV2 Park pulls from the MLB schedule and Ticketmaster. Schedule data is updated daily. Always verify LV2 enforcement with the 44th Ward site or the signs on your block. Not affiliated with the Chicago Cubs, Wrigley Field, or the City of Chicago.</p>
      <div class="footer-nav">
        <div class="footer-col">
          <div class="footer-col-label">LV2 Zone</div>
          <a href="/">Today's Status</a>
          <a href="/resources/lv2-parking-rules/">LV2 Rules</a>
          <a href="/resources/lv2-parking-map/">Zone Map</a>
        </div>
        <div class="footer-col">
          <div class="footer-col-label">Game Day</div>
          <a href="/resources/cubs-game-day-parking/">Game Day Parking</a>
          <a href="/resources/wrigley-field-parking-guide/">Parking Guide</a>
        </div>
        <div class="footer-col">
          <div class="footer-col-label">Data</div>
          <a href="/resources/lv2-data-explorer/">Data Explorer</a>
          <a href="/blog/lv2-data-analysis.html">FOIA Analysis</a>
        </div>
      </div>
      <div class="footer-copy">&copy; 2026 LV2 Park</div>
    </div>
  </footer>
</body>
</html>'''


def _build_enforcement_from_scan(ticket_count, peak_minute, hot_streets):
    """Build enforcement section from live scan data."""
    hot_html = ''
    for s in hot_streets:
        hot_html += f'<li>{s["street"]} — {s["count"]} tickets</li>'

    return f'''
      <div style="background:#FFFBF0;border-left:4px solid #F5E030;border-radius:0 var(--radius-sm) var(--radius-sm) 0;padding:20px 24px;margin:0 0 32px;">
        <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6B6B80;margin-bottom:12px;">LV2 Enforcement — This Game</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
          <div>
            <div style="font-size:36px;font-weight:900;color:#1A1A2E;line-height:1;">{ticket_count:,}</div>
            <div style="font-size:13px;color:#6B6B80;margin-top:4px;">tickets written</div>
          </div>
          <div>
            <div style="font-size:36px;font-weight:900;color:#1A1A2E;line-height:1;">{peak_minute}</div>
            <div style="font-size:13px;color:#6B6B80;margin-top:4px;">peak enforcement minute</div>
          </div>
        </div>
        {f'<div style="font-size:13px;color:#1A1A2E;"><strong>Hottest streets:</strong><ul style="margin:8px 0 0 16px;">{hot_html}</ul></div>' if hot_streets else ''}
      </div>'''


def _build_enforcement_from_foia(foia_streets, game_date):
    """Build enforcement section using FOIA averages when no live scan exists."""
    total = sum(foia_streets.values())
    avg_per_game = round(total / 81)  # ~81 home games/season in FOIA dataset

    return f'''
      <div style="background:#F5F4F0;border-left:4px solid #D0CFDA;border-radius:0 var(--radius-sm) var(--radius-sm) 0;padding:20px 24px;margin:0 0 32px;">
        <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6B6B80;margin-bottom:12px;">LV2 Enforcement — Historical Average</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:12px;">
          <div>
            <div style="font-size:36px;font-weight:900;color:#1A1A2E;line-height:1;">~{avg_per_game}</div>
            <div style="font-size:13px;color:#6B6B80;margin-top:4px;">avg tickets per game day</div>
          </div>
          <div>
            <div style="font-size:36px;font-weight:900;color:#1A1A2E;line-height:1;">5:01 PM</div>
            <div style="font-size:13px;color:#6B6B80;margin-top:4px;">enforcement starts</div>
          </div>
        </div>
        <div style="font-size:12px;color:#9090a8;">Live scan data not available for this date. Showing 2018–2023 FOIA averages.</div>
      </div>'''


# ── Blog post schedule (slug + publish date) ─────────────────────────────────
# Source of truth for sitemap generation. Add new posts here when scheduled.
BLOG_POSTS = [
    {'slug': 'lv2-data-analysis.html',              'publish_date': '2026-04-10'},
    {'slug': 'what-is-lv2.html',                    'publish_date': '2026-04-10'},
    {'slug': 'chicago-city-sticker-faq.html',        'publish_date': '2026-04-23'},
    {'slug': 'lv2-resident-permit-apply-online.html','publish_date': '2026-04-30'},
    {'slug': 'lv2-cubs-game-guest-pass.html',        'publish_date': '2026-05-07'},
    {'slug': 'contest-chicago-parking-ticket.html',  'publish_date': '2026-05-14'},
    {'slug': 'wrigley-field-concert-parking.html',   'publish_date': '2026-05-21'},
    {'slug': 'red-line-vs-driving-wrigley.html',     'publish_date': '2026-05-28'},
    {'slug': 'lv2-enforcement-peak-times.html',      'publish_date': '2026-06-04'},
    {'slug': 'chicago-permit-parking-explained.html','publish_date': '2026-06-11'},
    {'slug': 'lv2-history.html',                    'publish_date': '2026-06-18'},
    {'slug': 'chicago-parking-signs-guide.html',     'publish_date': '2026-06-25'},
    {'slug': 'chicago-street-sweeping-by-ward.html', 'publish_date': '2026-07-02'},
    {'slug': 'how-we-track-lv2-enforcement.html',    'publish_date': '2026-07-09'},
]

# ── Sitemap generator ─────────────────────────────────────────────────────────

def generate_sitemap(out_path='sitemap.xml', recaps_dir='game-recaps'):
    today_str = date.today().isoformat()

    static_urls = [
        # Core pages
        {'loc': '/',                                       'changefreq': 'daily',   'priority': '1.0', 'lastmod': today_str},
        {'loc': '/blog/',                                  'changefreq': 'weekly',  'priority': '0.7', 'lastmod': today_str},
        {'loc': '/resources/',                             'changefreq': 'monthly', 'priority': '0.7', 'lastmod': today_str},
        {'loc': '/about/',                                 'changefreq': 'monthly', 'priority': '0.4', 'lastmod': today_str},
        # Resource pages
        {'loc': '/resources/lv2-parking-rules/',           'changefreq': 'monthly', 'priority': '0.8', 'lastmod': today_str},
        {'loc': '/resources/lv2-parking-map/',             'changefreq': 'monthly', 'priority': '0.8', 'lastmod': today_str},
        {'loc': '/resources/chicago-permit-zones-wrigley/','changefreq': 'monthly', 'priority': '0.7', 'lastmod': today_str},
        {'loc': '/resources/cubs-game-day-parking/',       'changefreq': 'monthly', 'priority': '0.7', 'lastmod': today_str},
        {'loc': '/resources/wrigley-field-parking-guide/', 'changefreq': 'monthly', 'priority': '0.7', 'lastmod': today_str},
        {'loc': '/resources/wrigley-field-parking-shuttle/','changefreq': 'monthly','priority': '0.6', 'lastmod': today_str},
        {'loc': '/resources/wrigley-parking-ticket-data/', 'changefreq': 'monthly', 'priority': '0.7', 'lastmod': today_str},
        {'loc': '/resources/lv2-enforcement-tracker/',     'changefreq': 'daily',   'priority': '0.7', 'lastmod': today_str},
        {'loc': '/resources/lv2-data-explorer/',           'changefreq': 'monthly', 'priority': '0.6', 'lastmod': today_str},
        {'loc': '/resources/lv2-zone-explorer/',           'changefreq': 'monthly', 'priority': '0.6', 'lastmod': today_str},
        {'loc': '/resources/wrigley-divvy-scooters/',      'changefreq': 'monthly', 'priority': '0.5', 'lastmod': today_str},
    ]

    # Blog posts: only include those whose publish_date <= today
    blog_urls = [
        {'loc': f'/blog/{p["slug"]}', 'changefreq': 'monthly', 'priority': '0.8', 'lastmod': p['publish_date']}
        for p in BLOG_POSTS
        if p['publish_date'] <= today_str
    ]

    # Game recaps: scan the directory for all .html files
    recap_urls = []
    if os.path.isdir(recaps_dir):
        for fname in sorted(os.listdir(recaps_dir)):
            if not fname.endswith('.html'):
                continue
            # Derive lastmod from the date in the filename (YYYY-MM-DD-...)
            m = re.match(r'^(\d{4}-\d{2}-\d{2})', fname)
            lastmod = m.group(1) if m else today_str
            recap_urls.append({
                'loc': f'/game-recaps/{fname}',
                'changefreq': 'never',
                'priority': '0.4',
                'lastmod': lastmod,
            })

    all_urls = static_urls + blog_urls + recap_urls

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in all_urls:
        lines += [
            '  <url>',
            f'    <loc>{SITE_URL}{u["loc"]}</loc>',
            f'    <lastmod>{u["lastmod"]}</lastmod>',
            f'    <changefreq>{u["changefreq"]}</changefreq>',
            f'    <priority>{u["priority"]}</priority>',
            '  </url>',
        ]
    lines.append('</urlset>')

    with open(out_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'[sitemap] Written: {out_path} ({len(all_urls)} URLs, {len(blog_urls)} blog posts, {len(recap_urls)} recaps)')


# ── Main ─────────────────────────────────────────────────────────────────────

def generate_for_game(game, foia_streets, out_dir='game-recaps'):
    game_date  = game['date']
    away_clean = game['away'].replace(' Cubs', '').replace('Chicago ', '')
    slug       = f'{game_date}-cubs-vs-{slugify(away_clean)}'
    out_path   = f'{out_dir}/{slug}.html'

    # Fetch enrichment data
    weather     = fetch_weather_for_date(game_date)
    cubs_record = fetch_cubs_record_on_date(game_date, game_date[:4])
    scan_data   = load_scan_log_for_date(game_date)

    html = build_recap_page(game, weather, cubs_record, scan_data, foia_streets)

    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, 'w') as f:
        f.write(html)

    return out_path, slug


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', type=int, help='Generate all recaps for a season (completed games only)')
    parser.add_argument('--date',   type=str, help='Generate recap for a single date (YYYY-MM-DD)')
    parser.add_argument('--preview',action='store_true', help='Generate one page and open in browser')
    args = parser.parse_args()

    foia_streets = load_foia_street_totals()
    print(f'[recaps] Loaded {len(foia_streets)} streets from FOIA data')

    today_str = date.today().isoformat()

    if args.date or args.preview:
        target = args.date or today_str
        season = int(target[:4])
        print(f'[recaps] Fetching Cubs schedule for {season}...')
        games = fetch_cubs_schedule(season)
        game  = next((g for g in games if g['date'] == target), None)

        if not game:
            # Build a stub game for preview
            print(f'[recaps] No game found for {target} — building preview stub')
            game = {
                'date': target,
                'away': 'New York Mets',
                'away_team_id': 121,
                'home': 'Chicago Cubs',
                'home_team_id': 112,
                'status': 'Final',
                'home_score': 4,
                'away_score': 2,
                'attendance': 34218,
                'game_time': f'{target}T18:05:00Z'
            }

        path, slug = generate_for_game(game, foia_streets)
        print(f'[recaps] Generated: {path}')

        if args.preview:
            import subprocess
            subprocess.run(['open', path])
        else:
            generate_sitemap()

    elif args.season:
        print(f'[recaps] Fetching {args.season} Cubs schedule...')
        games = fetch_cubs_schedule(args.season)
        done_games = [g for g in games if g['status'] == 'Final' and g['date'] <= today_str]
        print(f'[recaps] {len(done_games)} completed home games to process')

        for game in done_games:
            path, slug = generate_for_game(game, foia_streets)
            print(f'[recaps] {game["date"]} → {path}')
            time.sleep(0.5)  # polite rate limit on weather API

        print(f'[recaps] Done. {len(done_games)} pages generated.')
        generate_sitemap()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
