/* ─── LV2 PARK — app.js ──────────────────────────── */

const DATA_TODAY   = '/data/today.json';
const DATA_WEEK    = '/data/week.json';
const SPOTHERO_URL = 'https://spothero.com/search?latitude=41.9484&longitude=-87.6553&utm_source=lv2park';
const WORKER_URL   = 'https://lv2park-email.YOUR_SUBDOMAIN.workers.dev'; // Update after Cloudflare deploy

/* ─── EVENT ICONS ────────────────────────────────── */
const ICONS = {
  game:     '⚾',
  concert:  '🎵',
  comedy:   '🎭',
  sports:   '🏟️',
  private:  '🏢',
  other:    '📅',
};

function eventIcon(ev) {
  if (!ev) return ICONS.other;
  const name = (ev.name || '').toLowerCase();
  if (ev.type === 'game')    return ICONS.game;
  if (name.includes('mulaney') || name.includes('comedy') || name.includes('stand-up')) return ICONS.comedy;
  if (name.includes('savannah bananas') || name.includes('golf') || name.includes('classic')) return ICONS.sports;
  if (ev.type === 'private') return ICONS.private;
  if (ev.type === 'concert') return ICONS.concert;
  return ICONS.other;
}

/* ─── BOOT ───────────────────────────────────────── */
let weekData = null;

document.addEventListener('DOMContentLoaded', () => {
  loadToday();
  loadWeek();
  initMap();
  initIcsModal();
});

/* ─── TODAY ──────────────────────────────────────── */
async function loadToday() {
  try {
    const res = await fetch(DATA_TODAY + '?v=' + Date.now());
    if (!res.ok) throw new Error('fetch failed');
    renderHero(await res.json());
  } catch {
    renderHeroError();
  }
}

function renderHero(data) {
  const card    = document.getElementById('hero-card');
  const accent  = document.getElementById('hero-accent');
  const eyebrow = document.getElementById('hero-eyebrow');
  const answer  = document.getElementById('hero-answer');
  const body    = document.getElementById('hero-body');
  const updated = document.getElementById('hero-updated');

  const today = new Date();
  eyebrow.textContent = 'Today — ' + today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  if (data.hasEvent) {
    card.className   = 'hero-card game-day';
    accent.className = 'hero-accent game-day';
    answer.textContent = 'YES';
    answer.className   = 'hero-answer yes';

    let eventsHtml = '<div class="hero-events">';
    for (const ev of data.events) {
      const icon = eventIcon(ev);
      eventsHtml += `
        <div class="hero-event-row">
          <div class="hero-event-name">${icon} ${escHtml(ev.name)}</div>
          <div class="hero-event-time">${escHtml(ev.time)} CT</div>
        </div>`;
    }
    eventsHtml += '</div>';

    const noteHtml = data.note
      ? `<div style="font-size:14px;color:var(--color-orange);margin-bottom:16px;font-weight:700;">${escHtml(data.note)}</div>`
      : '';

    const lv2Html = data.lv2Active
      ? '<div class="lv2-pill active"><div class="lv2-dot"></div> LV2 Active 5–10 PM</div>'
      : '<div class="lv2-pill quiet"><div class="lv2-dot"></div> LV2 Not Active Today</div>';

    const btnHtml = `<a class="btn-spothero" href="${SPOTHERO_URL}" target="_blank" rel="noopener">Book parking — from $15 <span class="arrow">→</span></a>`;
    body.innerHTML = eventsHtml + noteHtml + lv2Html + btnHtml;

  } else {
    card.className   = 'hero-card quiet';
    accent.className = 'hero-accent quiet';
    answer.textContent = 'NO';
    answer.className   = 'hero-answer no';

    const noteHtml = data.note
      ? `<div style="font-size:14px;color:var(--color-text-soft);margin-bottom:16px;">${escHtml(data.note)}</div>`
      : '<div class="hero-quiet-msg">No games. No events.<br>Wrigley is quiet today.</div>';

    body.innerHTML = noteHtml + '<div class="lv2-pill quiet"><div class="lv2-dot"></div> LV2 Not Active Today</div>';
  }

  if (updated) {
    const stale = isStale(data.updated);
    updated.className = stale ? 'hero-updated stale' : 'hero-updated';
    updated.textContent = stale
      ? 'Data may be outdated — check mlb.com for latest'
      : 'Updated ' + formatUpdated(data.updated);
  }

  const footerUpdated = document.getElementById('footer-updated');
  if (footerUpdated) footerUpdated.textContent = 'Data updated ' + formatUpdated(data.updated);
}

function renderHeroError() {
  document.getElementById('hero-eyebrow').textContent = 'Could not load today\'s data';
  document.getElementById('hero-body').innerHTML =
    '<div style="font-size:14px;color:var(--color-text-soft);margin-top:8px;">Check <a href="https://mlb.com/cubs/schedule" style="color:var(--color-purple);">mlb.com/cubs/schedule</a> for the latest.</div>';
}

/* ─── WEEK ───────────────────────────────────────── */
async function loadWeek() {
  try {
    const res = await fetch(DATA_WEEK + '?v=' + Date.now());
    if (!res.ok) throw new Error('fetch failed');
    weekData = await res.json();
    renderWeek(weekData);
  } catch {
    document.getElementById('week-list').innerHTML =
      '<div style="padding:20px;font-size:14px;color:var(--color-text-soft);">Could not load schedule.</div>';
  }
}

function renderWeek(data) {
  const list = document.getElementById('week-list');
  const todayStr = new Date().toISOString().split('T')[0];
  let html = '';

  for (const day of data.days) {
    const isToday   = day.date === todayStr;
    const hasEvent  = day.hasEvent;

    let rowClass = 'week-row';
    if (isToday)      rowClass += ' today';
    else if (hasEvent) rowClass += ' active';
    if (hasEvent)     rowClass += ' has-event';

    const dateClass = isToday ? 'week-date today-label' : 'week-date';

    // Icons + event names
    let eventsHtml = '';
    if (hasEvent && day.events.length > 0) {
      eventsHtml = day.events.map(ev => {
        const icon = eventIcon(ev);
        return `<div class="week-event-name">${icon} ${escHtml(ev.name)}</div>
                <div class="week-event-time">${escHtml(ev.time)}</div>`;
      }).join('');
    } else {
      eventsHtml = '<div class="week-event-name empty">Nothing</div>';
    }

    const badgeHtml  = day.lv2Active ? '<span class="week-badge">LV2</span>' : '';
    const chevron    = hasEvent ? '<span class="week-chevron">›</span>' : '';
    const clickAttr  = hasEvent ? `onclick="toggleWeekRow(this, '${day.date}')"` : '';

    html += `
      <div class="${rowClass}" ${clickAttr} data-date="${day.date}">
        <div class="${dateClass}">${escHtml(day.dayLabel)}</div>
        <div class="week-events">${eventsHtml}</div>
        ${badgeHtml}
        ${chevron}
      </div>
      <div class="week-row-detail" id="detail-${day.date}">
        ${buildDetailPanel(day)}
      </div>`;
  }

  list.innerHTML = html;
}

function buildDetailPanel(day) {
  if (!day.hasEvent || !day.events.length) return '';

  let html = '';
  for (const ev of day.events) {
    const icon  = eventIcon(ev);
    const isGallagher = ev.name.includes('(Gallagher Way)');
    const lv2Html = day.lv2Active && !isGallagher
      ? '<div class="week-detail-lv2">⚠ LV2 active 5–10 PM — towing enforced</div>'
      : isGallagher
        ? '<div style="font-size:13px;color:var(--color-text-soft);">Gallagher Way — LV2 not active for this event</div>'
        : '';

    html += `
      <div class="week-detail-event">
        <div class="week-detail-name">${icon} ${escHtml(ev.name)}</div>
        <div class="week-detail-time">🕐 ${escHtml(ev.time)} CT &nbsp;·&nbsp; ${escHtml(day.dayLabel)}</div>
        ${lv2Html}
      </div>`;
  }

  const parkingLink = day.lv2Active
    ? `<a class="week-detail-link" href="${SPOTHERO_URL}" target="_blank" rel="noopener">🅿 Book parking</a>`
    : '';

  html += `<div class="week-detail-actions">${parkingLink}</div>`;
  return html;
}

function toggleWeekRow(rowEl, date) {
  const detail  = document.getElementById('detail-' + date);
  const isOpen  = detail.classList.contains('open');
  // Close all open details first
  document.querySelectorAll('.week-row-detail.open').forEach(el => el.classList.remove('open'));
  document.querySelectorAll('.week-row.expanded').forEach(el => el.classList.remove('expanded'));
  // Toggle this one
  if (!isOpen) {
    detail.classList.add('open');
    rowEl.classList.add('expanded');
  }
}

/* ─── MAP ────────────────────────────────────────── */
function initMap() {
  const map = L.map('map-container', {
    center: [41.9490, -87.6660],
    zoom: 14,
    zoomControl: true,
    scrollWheelZoom: false
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19
  }).addTo(map);

  // Wrigley Field — proper stadium marker with pin
  const wrigleyIcon = L.divIcon({
    html: `<div style="display:flex;flex-direction:column;align-items:center;cursor:default;">
      <div style="background:#1A1A2E;color:#F5E030;font-size:12px;font-weight:900;padding:6px 12px;border-radius:8px;white-space:nowrap;box-shadow:0 3px 14px rgba(0,0,0,0.5);border:2px solid #F5E030;letter-spacing:.05em;">🏟 WRIGLEY FIELD</div>
      <div style="width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-top:9px solid #1A1A2E;margin-top:-1px;"></div>
    </div>`,
    className: '',
    iconAnchor: [74, 42]
  });
  L.marker([41.9484, -87.6553], { icon: wrigleyIcon }).addTo(map)
    .bindPopup('<strong>Wrigley Field</strong><br>1060 W Addison St<br>Home of the Chicago Cubs');

  // LV2 Zone boundary — Chicago Municipal Code 9-68-023
  // Main area: Irving Park (N) to Roscoe (S), Ravenswood (W) to Ashland (E)
  L.polygon([
    [41.9545, -87.6749],  // NW: Irving Park & Ravenswood
    [41.9545, -87.6690],  // NE: Irving Park & Ashland
    [41.9435, -87.6690],  // SE: Roscoe & Ashland
    [41.9435, -87.6749],  // SW: Roscoe & Ravenswood
  ], {
    color: '#6B64D4', weight: 2.5, opacity: 0.7,
    fillColor: '#6B64D4', fillOpacity: 0.07,
    dashArray: '6 4'
  }).addTo(map)
    .bindPopup('<strong>LV2 Zone</strong><br>Chicago Municipal Code 9-68-023<br>Tow zone active 5–10 PM on game and event days.');

  // High-enforcement streets near Wrigley (from FOIA data, 2018–2023)
  // These are the streets where tickets concentrate — shown red until full GeoJSON loads
  const hotStreets = [
    { name: 'Sheffield Ave', coords: [[41.9555, -87.6531], [41.9435, -87.6531]], tickets: 2100 },
    { name: 'Clark St',      coords: [[41.9555, -87.6553], [41.9435, -87.6553]], tickets: 1800 },
    { name: 'Addison St',    coords: [[41.9484, -87.6749], [41.9484, -87.6531]], tickets: 1400 },
    { name: 'Waveland Ave',  coords: [[41.9473, -87.6531], [41.9473, -87.6690]], tickets: 1200 },
    { name: 'Seminary Ave',  coords: [[41.9555, -87.6583], [41.9435, -87.6583]], tickets:  900 },
    { name: 'Kenmore Ave',   coords: [[41.9555, -87.6560], [41.9435, -87.6560]], tickets:  700 },
    { name: 'Racine Ave',    coords: [[41.9555, -87.6605], [41.9435, -87.6605]], tickets:  600 },
    { name: 'Roscoe St',     coords: [[41.9435, -87.6749], [41.9435, -87.6531]], tickets:  500 },
    { name: 'Irving Park Rd',coords: [[41.9545, -87.6749], [41.9545, -87.6531]], tickets:  400 },
  ];

  const staticStreetLayer = L.layerGroup();
  for (const s of hotStreets) {
    L.polyline(s.coords, {
      color: ticketCountToColor(s.tickets),
      weight: s.tickets > 1500 ? 5 : s.tickets > 900 ? 4 : 3,
      opacity: 0.82
    })
    .bindPopup(`<strong>${s.name}</strong><br>~${s.tickets.toLocaleString()} LV2 tickets (2018–2023)`)
    .addTo(staticStreetLayer);
  }
  staticStreetLayer.addTo(map);

  // Swap to real FOIA GeoJSON when available — hides static layer
  fetch('/data/lv2-heatmap.geojson')
    .then(r => r.ok ? r.json() : null)
    .then(geojson => {
      if (!geojson) return;
      staticStreetLayer.clearLayers();
      L.geoJSON(geojson, {
        style: f => ({
          color: ticketCountToColor(f.properties.tickets),
          weight: f.properties.tickets > 1000 ? 5 : f.properties.tickets > 500 ? 4 : 3,
          opacity: 0.85
        }),
        onEachFeature: (f, layer) => {
          if (f.properties) layer.bindPopup(`<strong>${f.properties.street}</strong><br>${f.properties.tickets.toLocaleString()} LV2 tickets (2018–2023)`);
        }
      }).addTo(map);
    })
    .catch(() => {});
}

function ticketCountToColor(t) {
  if (t > 1500) return '#E84040';
  if (t > 800)  return '#F0A030';
  if (t > 300)  return '#F5E030';
  return '#5B9EA0';
}

/* ─── PRINT CALENDAR ─────────────────────────────── */
function printSchedule() {
  const win = window.open('', '_blank', 'width=1200,height=900');
  if (!win) { alert('Allow pop-ups to print the calendar.'); return; }
  win.document.write(buildPrintCalendar());
  win.document.close();
}

function buildPrintCalendar() {
  const today    = new Date();
  const year     = today.getFullYear();
  const month    = today.getMonth();
  const monthName = today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const todayStr  = today.toISOString().split('T')[0];

  const firstDow    = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Event lookup from already-loaded weekData
  const evMap = {};
  if (weekData && weekData.days) {
    for (const d of weekData.days) evMap[d.date] = d;
  }

  // Build flat cell array: nulls for padding + day numbers
  const cells = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);

  const DOW = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

  // Build calendar rows
  let tableRows = '';
  for (let i = 0; i < cells.length; i += 7) {
    tableRows += '<tr>';
    for (let j = i; j < i + 7; j++) {
      const dayNum = cells[j];
      if (!dayNum) { tableRows += '<td class="empty"></td>'; continue; }

      const dateStr = `${year}-${String(month + 1).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
      const d       = evMap[dateStr];
      const isToday = dateStr === todayStr;

      let cls = 'day';
      if (isToday)             cls += ' today';
      if (d && d.hasEvent)     cls += ' has-event';

      let inner = `<div class="day-num">${dayNum}</div>`;

      if (d && d.hasEvent) {
        for (const ev of d.events) {
          const icon = ev.type === 'game' ? '⚾'
                     : (ev.name || '').toLowerCase().includes('comedy') ? '🎭' : '🎵';
          // Truncate long names for the cell
          const name = ev.name.length > 22 ? ev.name.slice(0, 20) + '…' : ev.name;
          inner += `<div class="ev-name">${icon} ${escHtml(name)}</div>`;
          if (ev.time && ev.time !== 'TBD') {
            inner += `<div class="ev-time">${escHtml(ev.time)}</div>`;
          }
        }
        if (d.lv2Active) inner += '<div class="lv2-tag">LV2 5–10 PM</div>';
      } else if (!d) {
        // Day is outside our data window — leave a subtle marker
        inner += '<div class="no-data"></div>';
      }

      tableRows += `<td class="${cls}">${inner}</td>`;
    }
    tableRows += '</tr>';
  }

  const numWeeks = cells.length / 7;

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Wrigley Field Schedule — ${monthName}</title>
<style>
  @page { size: 11in 8.5in landscape; margin: 0.35in 0.4in; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, 'Inter', system-ui, sans-serif;
    background: #fff;
    color: #1A1A2E;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* ── Header ── */
  .cal-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding-bottom: 8px;
    border-bottom: 3px solid #1A1A2E;
    margin-bottom: 8px;
  }
  .cal-logo { font-size: 22pt; font-weight: 900; letter-spacing: .03em; color: #1A1A2E; }
  .cal-logo span { color: #C8AA00; }
  .cal-month { font-size: 18pt; font-weight: 900; }
  .cal-url { font-size: 9pt; color: #6B6B80; }

  /* ── Day-of-week headers ── */
  .cal-dow th {
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: #6B6B80;
    padding: 4px 6px 4px;
    text-align: left;
    border-bottom: 1px solid #ddd;
  }

  /* ── Calendar grid ── */
  table { width: 100%; border-collapse: collapse; table-layout: fixed; }
  td.day, td.empty {
    border: 1px solid #e0dff0;
    vertical-align: top;
    padding: 5px 6px 6px;
    height: ${numWeeks === 6 ? '88px' : '100px'};
  }
  td.empty { background: #fafaf8; }

  .day-num {
    font-size: 11pt;
    font-weight: 700;
    color: #9090a8;
    margin-bottom: 3px;
  }
  td.today .day-num {
    display: inline-block;
    background: #1A1A2E;
    color: #F5E030;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    line-height: 22px;
    text-align: center;
    font-size: 9.5pt;
  }
  td.has-event { background: #FFFBF0; }

  .ev-name {
    font-size: 8pt;
    font-weight: 700;
    line-height: 1.35;
    color: #1A1A2E;
    margin-bottom: 1px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ev-time {
    font-size: 7.5pt;
    color: #6B6B80;
    margin-bottom: 3px;
  }
  .lv2-tag {
    display: inline-block;
    margin-top: 3px;
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .04em;
    background: #F0A030;
    color: #fff;
    padding: 2px 6px;
    border-radius: 3px;
  }
  .no-data { height: 8px; }

  /* ── Footer ── */
  .cal-footer {
    margin-top: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 7.5pt;
    color: #9090a8;
    border-top: 1px solid #e0dff0;
    padding-top: 6px;
  }
  .cal-footer strong { color: #1A1A2E; }

  /* ── Legend ── */
  .cal-legend {
    display: flex;
    gap: 16px;
    align-items: center;
  }
  .leg { display: flex; align-items: center; gap: 4px; }
  .leg-swatch {
    width: 10px; height: 10px; border-radius: 2px;
    display: inline-block;
  }
  .leg-swatch.ev   { background: #FFFBF0; border: 1px solid #e0c860; }
  .leg-swatch.lv2  { background: #F0A030; }
</style>
</head>
<body>
  <div class="cal-header">
    <div class="cal-logo">LV2 <span>PARK</span></div>
    <div class="cal-month">${monthName}</div>
    <div class="cal-url">lv2park.com</div>
  </div>

  <table>
    <thead class="cal-dow">
      <tr>${DOW.map(d => `<th>${d}</th>`).join('')}</tr>
    </thead>
    <tbody>${tableRows}</tbody>
  </table>

  <div class="cal-footer">
    <div class="cal-legend">
      <div class="leg"><span class="leg-swatch ev"></span> Game or event day</div>
      <div class="leg"><span class="leg-swatch lv2"></span> LV2 tow zone active 5–10 PM</div>
    </div>
    <div>Schedule may change. Verify at <strong>lv2park.com</strong>. Not affiliated with the Chicago Cubs or MLB.</div>
  </div>

  <script>
    window.addEventListener('load', function() {
      setTimeout(function() { window.print(); }, 400);
    });
  </script>
</body>
</html>`;
}

/* ─── ICS MODAL ──────────────────────────────────── */
function initIcsModal() {
  // Inject modal HTML once
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.id = 'ics-modal';
  modal.innerHTML = `
    <div class="modal">
      <div class="modal-accent"></div>
      <div class="modal-body">
        <div class="modal-title">Add to calendar</div>
        <div class="modal-sub">
          The Cubs schedule changes -- rain delays, postponements, new events.
          Enter your email and we'll alert you if anything on this schedule shifts.
          Or download and check back yourself.
        </div>
        <div class="modal-form" id="ics-form">
          <input class="form-input" type="email" id="ics-email" placeholder="your@email.com" autocomplete="email">
          <button class="btn-subscribe" onclick="icsSubscribeAndDownload()">Notify me of changes + Download</button>
        </div>
        <div class="modal-skip">
          <a onclick="icsDownloadOnly()">Just download, I'll check back myself</a>
        </div>
      </div>
    </div>`;

  modal.addEventListener('click', e => {
    if (e.target === modal) closeIcsModal();
  });

  document.body.appendChild(modal);
}

function openIcsModal() {
  document.getElementById('ics-modal').classList.add('open');
}

function closeIcsModal() {
  document.getElementById('ics-modal').classList.remove('open');
}

async function icsSubscribeAndDownload() {
  const email = document.getElementById('ics-email').value.trim();
  if (email && email.includes('@')) {
    // Non-blocking subscribe -- download regardless of result
    fetch(`${WORKER_URL}/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    }).catch(() => {});
  }
  icsDownloadOnly();
}

function icsDownloadOnly() {
  closeIcsModal();
  if (weekData) generateIcs(weekData);
}

function generateIcs(data) {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//LV2 Park//lv2park.com//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'X-WR-CALNAME:Wrigley Field Schedule',
    'X-WR-CALDESC:Games and events at Wrigley Field. Check lv2park.com for updates.',
    'X-WR-TIMEZONE:America/Chicago',
  ];

  const now = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

  for (const day of data.days) {
    if (!day.hasEvent) continue;
    for (const ev of day.events) {
      const uid = `${day.date}-${slugify(ev.name)}@lv2park.com`;
      const dtstart = icsDatetime(day.date, ev.time);
      const dtend   = icsDatetime(day.date, ev.time, 3); // assume 3hr duration
      const lv2note = day.lv2Active ? ' LV2 parking active 5-10 PM -- check lv2park.com.' : '';
      const icon    = icsIcon(ev);

      lines.push('BEGIN:VEVENT');
      lines.push(`UID:${uid}`);
      lines.push(`DTSTAMP:${now}`);
      lines.push(`DTSTART;TZID=America/Chicago:${dtstart}`);
      lines.push(`DTEND;TZID=America/Chicago:${dtend}`);
      lines.push(`SUMMARY:${icon} ${ev.name}`);
      lines.push(`LOCATION:Wrigley Field\\, 1060 W Addison St\\, Chicago IL 60613`);
      lines.push(foldIcsLine(`DESCRIPTION:${ev.name} at Wrigley Field.${lv2note} Schedule may change -- lv2park.com for latest.`));
      lines.push(`URL:https://lv2park.com`);
      lines.push('END:VEVENT');
    }
  }

  lines.push('END:VCALENDAR');

  const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'wrigley-schedule.ics';
  a.click();
  URL.revokeObjectURL(url);
}

function icsIcon(ev) {
  const name = (ev.name || '').toLowerCase();
  if (ev.type === 'game') return '⚾';
  if (name.includes('mulaney') || name.includes('comedy')) return '🎭';
  return '🎵';
}

function icsDatetime(dateStr, timeStr, addHours = 0) {
  // dateStr: '2026-04-17', timeStr: '1:20 PM'
  try {
    const [year, month, day] = dateStr.split('-').map(Number);
    const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
    if (!match) return dateStr.replace(/-/g, '') + 'T190000';
    let h = parseInt(match[1]);
    const m = parseInt(match[2]);
    const period = match[3].toUpperCase();
    if (period === 'PM' && h < 12) h += 12;
    if (period === 'AM' && h === 12) h = 0;
    h += addHours;
    return `${year}${String(month).padStart(2,'0')}${String(day).padStart(2,'0')}T${String(h).padStart(2,'0')}${String(m).padStart(2,'0')}00`;
  } catch {
    return dateStr.replace(/-/g, '') + 'T190000';
  }
}

function foldIcsLine(line) {
  // RFC 5545: fold lines at 75 chars
  if (line.length <= 75) return line;
  let out = '';
  while (line.length > 75) {
    out += line.substring(0, 75) + '\r\n ';
    line = line.substring(75);
  }
  return out + line;
}

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

/* ─── EMAIL FORM ─────────────────────────────────── */
async function handleEmailSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('email-input').value.trim();
  if (!email) return;
  const btn = e.target.querySelector('button');
  btn.textContent = 'Subscribing...';
  btn.disabled = true;
  try {
    const res = await fetch(`${WORKER_URL}/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (res.ok) {
      document.getElementById('email-form').style.display = 'none';
      document.getElementById('email-success').style.display = 'block';
    } else throw new Error();
  } catch {
    btn.textContent = 'Subscribe';
    btn.disabled = false;
    alert('Something went wrong. Try again or email hello@lv2park.com');
  }
}

/* ─── CONTACT FORM ───────────────────────────────── */
async function handleContactSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const btn  = form.querySelector('button');
  btn.textContent = 'Sending...';
  btn.disabled = true;
  try {
    const res = await fetch(`${WORKER_URL}/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name:    form.querySelector('[name=name]').value.trim(),
        email:   form.querySelector('[name=email]').value.trim(),
        message: form.querySelector('[name=message]').value.trim()
      })
    });
    if (res.ok) {
      form.innerHTML = '<div style="font-size:17px;color:var(--color-green);font-weight:700;padding:16px 0;">Got it. We\'ll be in touch.</div>';
    } else throw new Error();
  } catch {
    btn.textContent = 'Send';
    btn.disabled = false;
    alert('Something went wrong. Email hello@lv2park.com directly.');
  }
}

/* ─── HELPERS ────────────────────────────────────── */
function escHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function isStale(iso) {
  if (!iso) return true;
  return (Date.now() - new Date(iso).getTime()) > 30 * 60 * 60 * 1000;
}
function formatUpdated(iso) {
  if (!iso) return '';
  const diffH = Math.floor((Date.now() - new Date(iso).getTime()) / 3600000);
  if (diffH < 1)  return 'less than an hour ago';
  if (diffH < 24) return `${diffH} hours ago`;
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
