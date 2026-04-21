/* ─── LV2 PARK — app.js ──────────────────────────── */

const DATA_TODAY        = '/data/today.json';
const DATA_WEEK         = '/data/week.json';
const DATA_ENFORCEMENT  = '/data/enforcement-today.json';
const SPOTHERO_URL      = 'https://spothero.com/search?latitude=41.9484&longitude=-87.6553&utm_source=lv2park';

// ── Affiliate config ──────────────────────────────────────────────────────────
// SeatGeek: apply at impact.com → search "SeatGeek". Replace SEATGEEK_AFF_ID below.
// Ticketmaster: apply at flexoffers.com (already verified). Replace TM_AFF_ID below.
const SEATGEEK_AFF_ID   = '';   // e.g. '12345'  — Impact affiliate ID
const TM_AFF_ID         = '';   // e.g. '67890'  — FlexOffers publisher ID

function ticketUrl(ev) {
  const q = encodeURIComponent(ev.name || 'Wrigley Field');
  if (ev.type === 'game') {
    const base = 'https://seatgeek.com/chicago-cubs-tickets';
    return SEATGEEK_AFF_ID ? `${base}?aid=${SEATGEEK_AFF_ID}&utm_source=lv2park` : base;
  }
  // Concert / comedy — Ticketmaster deep search
  const base = `https://www.ticketmaster.com/search?q=${q}`;
  return TM_AFF_ID ? `${base}&track=${TM_AFF_ID}&utm_source=lv2park` : base;
}
const WORKER_URL        = 'https://lv2park-email.adam-945.workers.dev';
const TURNSTILE_SITE_KEY = '0x4AAAAAAC-Mur2UjOBs1zDs';

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
  initTurnstile();
});

let tsWidgetId = null;
let tsResolve   = null;

function initTurnstile() {
  if (!TURNSTILE_SITE_KEY) return;
  const el = document.getElementById('turnstile-widget');
  if (!el) return;
  // Poll until Turnstile script is ready
  if (typeof turnstile === 'undefined') {
    setTimeout(initTurnstile, 300);
    return;
  }
  tsWidgetId = turnstile.render(el, {
    sitekey:   TURNSTILE_SITE_KEY,
    size:      'invisible',
    execution: 'execute',
    callback: token => { if (tsResolve) { tsResolve(token); tsResolve = null; } },
    'error-callback': () => { if (tsResolve) { tsResolve(''); tsResolve = null; } },
    'expired-callback': () => { if (tsResolve) { tsResolve(''); tsResolve = null; } }
  });
}

function getTurnstileToken() {
  if (!TURNSTILE_SITE_KEY || tsWidgetId === null) return Promise.resolve('');
  return new Promise(resolve => {
    const timeout = setTimeout(() => { tsResolve = null; resolve('__timeout__'); }, 4000);
    tsResolve = token => { clearTimeout(timeout); resolve(token); };
    try { turnstile.execute(tsWidgetId); } catch { clearTimeout(timeout); resolve(''); }
  });
}

/* ─── ENFORCEMENT TICKER ─────────────────────────── */
async function loadTicker() {
  try {
    const res = await fetch(DATA_ENFORCEMENT + '?v=' + Date.now());
    if (!res.ok) return;
    const d = await res.json();
    // Compare date in CT (game-day concept is always CT)
    const todayCT = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
    if (d.date !== todayCT || !d.scan_ok || d.lv2_tickets_today === 0) return;
    // Don't show stale data (> 2 hours old)
    if (Date.now() - new Date(d.last_checked).getTime() > 7200000) return;
    const checkedCT = new Date(d.last_checked).toLocaleTimeString('en-US', {
      timeZone: 'America/Chicago', hour: 'numeric', minute: '2-digit'
    });
    const el = document.getElementById('enforcement-ticker');
    if (!el) return;
    const n = d.lv2_tickets_today;
    el.innerHTML = `<div style="font-size:13px;color:var(--color-text-soft);border:1px solid #C8C6D4;border-radius:6px;padding:8px 12px;margin:8px 0 4px;line-height:1.5;">
      <strong style="color:var(--color-text);">${n} ticket${n !== 1 ? 's' : ''} confirmed</strong> in the zone today · Last checked ${checkedCT} CT
    </div>`;
  } catch {}
}

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
  const todayCT = today.toLocaleDateString('en-CA', { timeZone: 'America/Chicago' }); // 'YYYY-MM-DD'
  eyebrow.textContent = 'Today — ' + today.toLocaleDateString('en-US', { timeZone: 'America/Chicago', weekday: 'long', month: 'long', day: 'numeric' });

  // Stale data guard: today.json was written for a different calendar date (happens
  // between the last nightly run and the midnight cron). Don't show yesterday's answer.
  if (data.date && data.date !== todayCT) {
    card.className   = 'hero-card quiet';
    accent.className = 'hero-accent quiet';
    answer.textContent = '...';
    answer.className   = 'hero-answer yes';
    body.innerHTML = '<div class="hero-quiet-msg">Status refreshing — check the schedule below or visit <a href="https://mlb.com/cubs/schedule" style="color:var(--color-purple);">mlb.com</a> for today\'s game.</div>';
    if (updated) updated.textContent = 'Updated ' + formatUpdated(data.updated);
    return;
  }

  // Build events list HTML (reused in multiple branches)
  function eventsListHtml(events) {
    if (!events || !events.length) return '';
    let h = '<div class="hero-events">';
    for (const ev of events) {
      h += `<div class="hero-event-row">
        <div class="hero-event-name">${eventIcon(ev)} ${escHtml(ev.name)}</div>
        <div class="hero-event-time">${escHtml(ev.time)} CT</div>
      </div>`;
    }
    return h + '</div>';
  }

  const noteHtml = data.note
    ? `<div style="font-size:14px;color:var(--color-orange);margin-bottom:16px;font-weight:700;">${escHtml(data.note)}</div>`
    : '';

  if (data.lv2Active) {
    // LV2 is active -- answer is NO, you cannot safely park here
    card.className   = 'hero-card game-day';
    accent.className = 'hero-accent game-day';
    answer.textContent = 'NO';
    answer.className   = 'hero-answer no';

    const lv2Html = '<div class="lv2-pill active"><div class="lv2-dot"></div> LV2 Active 5–10 PM — Move your car before 5</div>';
    const dayGameNote = isDayGamePast5(data.events)
      ? '<div style="font-size:13px;color:var(--color-orange);font-weight:700;margin-bottom:12px;">⚠ Day game — LV2 is still active until 10 PM even though the game is over.</div>'
      : '';
    body.innerHTML = lv2Html + eventsListHtml(data.events) + dayGameNote + noteHtml + '<div id="enforcement-ticker"></div>';
    loadTicker();

  } else if (data.hasEvent) {
    // Event today but LV2 not active -- safe to park
    card.className   = 'hero-card quiet';
    accent.className = 'hero-accent quiet';
    answer.textContent = 'YES';
    answer.className   = 'hero-answer yes';

    const lv2Html = '<div class="lv2-pill quiet"><div class="lv2-dot"></div> LV2 Not Active Today</div>';
    body.innerHTML = eventsListHtml(data.events) + noteHtml + lv2Html;

  } else {
    // No event, no LV2 -- safe to park
    card.className   = 'hero-card quiet';
    accent.className = 'hero-accent quiet';
    answer.textContent = 'YES';
    answer.className   = 'hero-answer yes';

    const quietMsg = data.note
      ? `<div style="font-size:14px;color:var(--color-text-soft);margin-bottom:16px;">${escHtml(data.note)}</div>`
      : '<div class="hero-quiet-msg">No games or events today.<br>Park freely in the LV2 zone.</div>';

    body.innerHTML = quietMsg + '<div class="lv2-pill quiet"><div class="lv2-dot"></div> LV2 Not Active Today</div>';
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
  list.innerHTML = buildDayRows(data.days, todayStr);

  // Scroll so today is at the top — defer until after browser layout
  setTimeout(() => {
    const todayRow = list.querySelector(`[data-date="${todayStr}"]`);
    if (todayRow) list.scrollTop = todayRow.offsetTop;
  }, 0);
}

function buildDayRows(days, todayStr) {
  let html = '';
  let lastMonth = '';

  for (const day of days) {
    // Month header when month changes
    const monthLabel = new Date(day.date + 'T12:00:00').toLocaleString('en-US', { month: 'long', year: 'numeric' });
    if (monthLabel !== lastMonth) {
      html += `<div class="week-month-header">${monthLabel}</div>`;
      lastMonth = monthLabel;
    }

    const isToday   = day.date === todayStr;
    const hasEvent  = day.hasEvent;

    let rowClass = 'week-row';
    if (isToday)       rowClass += ' today';
    else if (hasEvent) rowClass += ' active';
    if (hasEvent)      rowClass += ' has-event';

    const dateClass = isToday ? 'week-date today-label' : 'week-date';

    let eventsHtml = '';
    if (hasEvent && day.events.length > 0) {
      eventsHtml = day.events.map(ev => {
        const icon        = eventIcon(ev);
        const isCancelled = ev.changed === 'cancelled';
        const isNew       = ev.changed === 'new';
        const isTimeChg   = ev.changed === 'time';
        const nameClass   = isCancelled ? 'week-event-name ev-cancelled-name' : 'week-event-name';
        const dot         = isCancelled ? '<span class="ev-dot ev-dot-cancelled"></span>'
                          : isNew       ? '<span class="ev-dot ev-dot-new"></span>'
                          : isTimeChg   ? '<span class="ev-dot ev-dot-time"></span>'
                          : '';
        const timeExtra   = isTimeChg ? ` <span class="ev-was">was ${escHtml(ev.prevTime||'')}</span>` : '';
        const timeHtml    = `<div class="week-event-time">${escHtml(ev.time)}${timeExtra}</div>`;
        return `<div class="${nameClass}">${dot}${icon} ${escHtml(ev.name)}</div>${timeHtml}`;
      }).join('');
    } else {
      eventsHtml = '<div class="week-event-name empty">Nothing</div>';
    }

    const badgeHtml = ''; // LV2 info shown in expanded detail panel only
    const chevron   = hasEvent ? '<span class="week-chevron">›</span>' : '';
    const clickAttr = hasEvent ? `onclick="toggleWeekRow(this, '${day.date}')"` : '';

    const types = day.events.map(e => e.type).join(',');
    html += `
      <div class="${rowClass}" ${clickAttr} data-date="${day.date}" data-types="${types}" data-lv2="${day.lv2Active}">
        <div class="${dateClass}">${escHtml(day.dayLabel)}</div>
        <div class="week-events">${eventsHtml}</div>
        ${badgeHtml}
        ${chevron}
      </div>
      <div class="week-row-detail" id="detail-${day.date}">
        ${buildDetailPanel(day)}
      </div>`;
  }
  return html;
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

  // Ticket button — one per unique event type
  const ticketLinks = day.events
    .filter(ev => ev.changed !== 'cancelled')
    .map(ev => {
      const label = ev.type === 'game' ? '🎟 Buy tickets' : '🎟 Get tickets';
      const url   = ticketUrl(ev);
      return `<a class="week-detail-link tickets" href="${url}" target="_blank" rel="noopener">${label}</a>`;
    })
    .filter((v, i, a) => a.indexOf(v) === i); // dedupe identical links

  html += `<div class="week-detail-actions">${ticketLinks.join('')}</div>`;
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

/* ─── WEEK FILTER ───────────────────────────────── */
let activeWeekFilter = null;

function setWeekFilter(type) {
  const list = document.getElementById('week-list');
  activeWeekFilter = activeWeekFilter === type ? null : type;

  // Update button states
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('filter-active', btn.dataset.filter === activeWeekFilter);
  });

  // Show/hide rows
  list.querySelectorAll('.week-row').forEach(row => {
    const detail = document.getElementById('detail-' + row.dataset.date);
    let show = true;
    if (activeWeekFilter === 'game')    show = row.dataset.types?.includes('game');
    else if (activeWeekFilter === 'concert') show = row.dataset.types?.includes('concert');
    else if (activeWeekFilter === 'comedy')  show = row.dataset.types?.includes('comedy');
    else if (activeWeekFilter === 'lv2')     show = row.dataset.lv2 === 'true';
    row.style.display = show ? '' : 'none';
    if (detail) detail.style.display = 'none'; // collapse details on filter change
  });

  // Hide month headers that have no visible rows beneath them
  list.querySelectorAll('.week-month-header').forEach(header => {
    let next = header.nextElementSibling;
    let hasVisible = false;
    while (next && !next.classList.contains('week-month-header')) {
      if (next.classList.contains('week-row') && next.style.display !== 'none') {
        hasVisible = true;
        break;
      }
      next = next.nextElementSibling;
    }
    header.style.display = hasVisible ? '' : 'none';
  });
}

/* ─── MAP ────────────────────────────────────────── */
function initMap() {
  const map = L.map('map-container', {
    center: [41.9490, -87.6660],
    zoom: 14,
    zoomControl: true,
    scrollWheelZoom: false
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 19
  }).addTo(map);

  // Wrigley Field marker — iconSize/iconAnchor [0,0] so origin = lat/lng point.
  // CSS positions the label + triangle pointer above and centered on that point.
  const wrigleyIcon = L.divIcon({
    html: `<div style="position:relative;width:0;height:0;">
      <div style="position:absolute;bottom:9px;left:0;transform:translateX(-50%);background:#1A1A2E;color:#F5E030;font-size:12px;font-weight:900;padding:6px 12px;border-radius:8px;white-space:nowrap;box-shadow:0 3px 14px rgba(0,0,0,0.5);border:2px solid #F5E030;letter-spacing:.05em;cursor:default;">🏟 WRIGLEY FIELD</div>
      <div style="position:absolute;bottom:0;left:0;transform:translateX(-50%);width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-top:9px solid #1A1A2E;"></div>
    </div>`,
    className: '',
    iconSize: [0, 0],
    iconAnchor: [0, 0]
  });
  L.marker([41.9484, -87.6553], { icon: wrigleyIcon }).addTo(map)
    .bindPopup('<strong>Wrigley Field</strong><br>1060 W Addison St<br>Home of the Chicago Cubs');

  // Zone 383 boundary (dashed purple)
  L.polygon([
    [41.954491, -87.669252],  // NW: Irving Park & Ashland
    [41.954491, -87.655100],  // NE: Irving Park & Broadway
    [41.947062, -87.651500],  // Addison & Broadway
    [41.939777, -87.644500],  // SE: Belmont & Broadway
    [41.939777, -87.669252],  // SW: Belmont & Ashland
  ], {
    color: '#6B64D4', weight: 2, opacity: 0.7,
    fillColor: '#6B64D4', fillOpacity: 0.08,
    dashArray: '6 4'
  }).addTo(map)
    .bindTooltip('Zone 383 — Year-round residential permit parking', { permanent: false, direction: 'center' });

  // LV2 individual streets from OSM GeoJSON
  fetch('/data/lv2-zone-streets.geojson')
    .then(r => r.ok ? r.json() : null)
    .then(geojson => {
      if (!geojson) return;
      L.geoJSON(geojson, {
        style: () => ({ color: '#C2185B', weight: 4, opacity: 0.75 }),
        onEachFeature: (f, layer) => {
          const p = f.properties;
          const section = p.section === 'north' ? 'north section' : 'west section';
          layer.bindTooltip(`<strong>${p.street}</strong><br><small>LV2 zone, ${section}</small>`, { sticky: true });
        }
      }).addTo(map);
    })
    .catch(() => {});
}

function ticketCountToColor(t) {
  if (t > 1500) return '#E84040';
  if (t > 800)  return '#F0A030';
  if (t > 300)  return '#C9A030';
  return '#5B9EA0';
}

/* ─── PRINT CALENDAR ─────────────────────────────── */
function printSchedule() {
  // Show inline choice UI next to the Print button
  const existing = document.getElementById('print-choice');
  if (existing) { existing.remove(); return; }

  const toolbar = document.querySelector('.week-toolbar');
  const choice = document.createElement('div');
  choice.id = 'print-choice';
  choice.style.cssText = 'display:flex;gap:8px;align-items:center;padding:8px 16px;background:#f5f4f0;border-top:1px solid #E0DFF0;flex-wrap:wrap;';
  choice.innerHTML = `
    <span style="font-size:12px;font-weight:700;color:var(--color-text-soft);">Print:</span>
    <button class="btn-week-action" onclick="doPrint('month')">This month</button>
    <button class="btn-week-action" onclick="doPrint('all')">Full season (1 page)</button>
    <button class="btn-week-action" onclick="document.getElementById('print-choice').remove()" style="color:#aaa;">Cancel</button>`;
  toolbar.insertAdjacentElement('afterend', choice);
}

function doPrint(mode) {
  document.getElementById('print-choice')?.remove();
  const win = window.open('', '_blank', 'width=1200,height=900');
  if (!win) { alert('Allow pop-ups to print the calendar.'); return; }
  win.document.write(mode === 'all' ? buildAllMonthsCalendar() : buildPrintCalendar(null));
  win.document.close();
}

function buildPrintCalendar(monthKey) {
  const today    = new Date();
  const todayStr = today.toISOString().split('T')[0];
  if (!monthKey) monthKey = todayStr.slice(0, 7);
  const DOW = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

  // Event lookup from already-loaded weekData
  const evMap = {};
  if (weekData && weekData.days) {
    for (const d of weekData.days) evMap[d.date] = d;
  }

  // Build one calendar block per month
  function buildMonth(monthKey, isLast) {
    const [yr, mo] = monthKey.split('-').map(Number);
    const monthName  = new Date(yr, mo - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const firstDow   = new Date(yr, mo - 1, 1).getDay();
    const daysInMonth = new Date(yr, mo, 0).getDate();

    const cells = [];
    for (let i = 0; i < firstDow; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);
    const cellH = cells.length / 7 === 6 ? '88px' : '100px';

    let tableRows = '';
    for (let i = 0; i < cells.length; i += 7) {
      tableRows += '<tr>';
      for (let j = i; j < i + 7; j++) {
        const dayNum = cells[j];
        if (!dayNum) { tableRows += '<td class="empty"></td>'; continue; }
        const dateStr = `${yr}-${String(mo).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
        const d = evMap[dateStr];
        const isToday = dateStr === todayStr;
        let cls = 'day';
        if (isToday)         cls += ' today';
        if (d && d.hasEvent) cls += ' has-event';
        let inner = `<div class="day-num">${dayNum}</div>`;
        if (d && d.hasEvent) {
          for (const ev of d.events) {
            const icon = ev.type === 'game' ? '⚾' : (ev.name||'').toLowerCase().includes('comedy') ? '🎭' : '🎵';
            const name = ev.name.length > 22 ? ev.name.slice(0,20) + '…' : ev.name;
            inner += `<div class="ev-name">${icon} ${escHtml(name)}</div>`;
            if (ev.time && ev.time !== 'TBD') inner += `<div class="ev-time">${escHtml(ev.time)}</div>`;
          }
          if (d.lv2Active) inner += '<div class="lv2-tag">LV2 5–10 PM</div>';
        }
        tableRows += `<td class="${cls}" style="height:${cellH}">${inner}</td>`;
      }
      tableRows += '</tr>';
    }

    const pageBreak = isLast ? '' : 'style="page-break-after:always"';
    return `
    <div class="month-page" ${pageBreak}>
      <div class="cal-header">
        <div class="cal-logo">LV2 <span>PARK</span></div>
        <div class="cal-month">${monthName}</div>
        <div class="cal-url">lv2park.com</div>
      </div>
      <table>
        <thead class="cal-dow"><tr>${DOW.map(d=>`<th>${d}</th>`).join('')}</tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
      <div class="cal-footer">
        <div class="cal-legend">
          <div class="leg"><span class="leg-swatch ev"></span> Game or event day</div>
          <div class="leg"><span class="leg-swatch lv2"></span> LV2 tow zone active 5–10 PM</div>
        </div>
        <div>Schedule may change. Verify at <strong>lv2park.com</strong>. Not affiliated with the Chicago Cubs or MLB.</div>
      </div>
    </div>`;
  }

  const allMonths = buildMonth(monthKey, true);

  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Wrigley Field Schedule</title>
<style>
  @page { size: 11in 8.5in landscape; margin: 0.35in 0.4in; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system,'Inter',system-ui,sans-serif; background:#fff; color:#1A1A2E; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .cal-header { display:flex; align-items:flex-end; justify-content:space-between; padding-bottom:8px; border-bottom:3px solid #1A1A2E; margin-bottom:8px; }
  .cal-logo { font-size:22pt; font-weight:900; letter-spacing:.03em; color:#1A1A2E; }
  .cal-logo span { color:#C8AA00; }
  .cal-month { font-size:18pt; font-weight:900; }
  .cal-url { font-size:9pt; color:#6B6B80; }
  .cal-dow th { font-size:8.5pt; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:#6B6B80; padding:4px 6px; text-align:left; border-bottom:1px solid #ddd; }
  table { width:100%; border-collapse:collapse; table-layout:fixed; }
  td.day, td.empty { border:1px solid #e0dff0; vertical-align:top; padding:5px 6px 6px; }
  td.empty { background:#fafaf8; }
  .day-num { font-size:11pt; font-weight:700; color:#9090a8; margin-bottom:3px; }
  td.today .day-num { display:inline-block; background:#1A1A2E; color:#F5E030; border-radius:50%; width:22px; height:22px; line-height:22px; text-align:center; font-size:9.5pt; }
  td.has-event { background:#FFFBF0; }
  .ev-name { font-size:8pt; font-weight:700; line-height:1.35; color:#1A1A2E; margin-bottom:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .ev-time { font-size:7.5pt; color:#6B6B80; margin-bottom:3px; }
  .lv2-tag { display:inline-block; margin-top:3px; font-size:7pt; font-weight:700; text-transform:uppercase; letter-spacing:.04em; background:#F0A030; color:#fff; padding:2px 6px; border-radius:3px; }
  .cal-footer { margin-top:8px; display:flex; justify-content:space-between; align-items:center; font-size:7.5pt; color:#9090a8; border-top:1px solid #e0dff0; padding-top:6px; }
  .cal-footer strong { color:#1A1A2E; }
  .cal-legend { display:flex; gap:16px; align-items:center; }
  .leg { display:flex; align-items:center; gap:4px; }
  .leg-swatch { width:10px; height:10px; border-radius:2px; display:inline-block; }
  .leg-swatch.ev  { background:#FFFBF0; border:1px solid #e0c860; }
  .leg-swatch.lv2 { background:#F0A030; }
</style></head>
<body>
${allMonths}
<script>window.addEventListener('load',function(){setTimeout(function(){window.print();},400);});<\/script>
</body></html>`;
}

/* ─── ALL-MONTHS COMPACT PRINT ───────────────────── */
function buildAllMonthsCalendar() {
  const today    = new Date();
  const todayStr = today.toISOString().split('T')[0];
  const DOW = ['Su','Mo','Tu','We','Th','Fr','Sa'];

  const evMap = {};
  if (weekData && weekData.days) {
    for (const d of weekData.days) evMap[d.date] = d;
  }

  const monthKeys = new Set([todayStr.slice(0, 7)]);
  if (weekData && weekData.days) {
    for (const d of weekData.days) monthKeys.add(d.date.slice(0, 7));
  }
  const sortedMonths = [...monthKeys].sort();

  function miniMonth(monthKey) {
    const [yr, mo] = monthKey.split('-').map(Number);
    const monthName  = new Date(yr, mo - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const firstDow   = new Date(yr, mo - 1, 1).getDay();
    const daysInMonth = new Date(yr, mo, 0).getDate();
    const cells = [];
    for (let i = 0; i < firstDow; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);

    let rows = '';
    for (let i = 0; i < cells.length; i += 7) {
      rows += '<tr>';
      for (let j = i; j < i + 7; j++) {
        const dayNum = cells[j];
        if (!dayNum) { rows += '<td class="empty"></td>'; continue; }
        const dateStr = `${yr}-${String(mo).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
        const d = evMap[dateStr];
        const isToday = dateStr === todayStr;
        let cls = 'day';
        if (isToday)         cls += ' today';
        if (d && d.hasEvent) cls += ' has-event';
        let inner = `<div class="dn">${dayNum}</div>`;
        if (d && d.hasEvent) {
          for (const ev of d.events) {
            const icon = ev.type === 'game' ? '⚾' : ev.type === 'comedy' ? '🎭' : '🎵';
            let shortName;
            if (ev.type === 'game') {
              // "New York Mets vs. Cubs" → "Mets"
              const opp = ev.name.replace(/ vs\. Cubs.*$/i, '').trim();
              const parts = opp.split(' ');
              shortName = parts[parts.length - 1];
            } else {
              shortName = ev.name.length > 13 ? ev.name.slice(0, 12) + '…' : ev.name;
            }
            inner += `<div class="en">${icon} ${escHtml(shortName)}</div>`;
          }
          if (d.lv2Active) inner += '<div class="lt">LV2</div>';
        }
        rows += `<td class="${cls}">${inner}</td>`;
      }
      rows += '</tr>';
    }
    return `
      <div class="mini-cal">
        <div class="mini-hdr">${monthName}</div>
        <table>
          <thead><tr>${DOW.map(d=>`<th>${d}</th>`).join('')}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  // Split months into pages of 6 (3 columns × 2 rows fits landscape 11×8.5)
  const chunks = [];
  for (let i = 0; i < sortedMonths.length; i += 6) chunks.push(sortedMonths.slice(i, i + 6));

  const footer = `<div class="page-footer">
    <span>⚾ Game &nbsp; 🎵 Concert / Special &nbsp; <span style="background:#F0A030;color:#fff;padding:1px 4px;border-radius:2px;font-weight:900;">LV2</span> = tow zone active 5–10 PM</span>
    <span>Schedule may change. Verify at lv2park.com. Not affiliated with the Chicago Cubs or MLB.</span>
  </div>`;

  const pagesHtml = chunks.map((chunk, idx) => {
    const isLast = idx === chunks.length - 1;
    return `<div class="print-page"${isLast ? '' : ' style="page-break-after:always"'}>
      <div class="page-header">
        <div class="logo">LV2 <span>PARK</span></div>
        <div class="page-url">lv2park.com · Wrigley Field Schedule${chunks.length > 1 ? ` · ${idx + 1} of ${chunks.length}` : ''}</div>
      </div>
      <div class="grid">${chunk.map(k => miniMonth(k)).join('')}</div>
      ${footer}
    </div>`;
  }).join('');

  return `<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Wrigley Field Schedule</title>
<style>
  @page { size: 11in 8.5in landscape; margin: 0.3in; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:-apple-system,'Inter',system-ui,sans-serif; background:#fff; color:#1A1A2E; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .print-page { display:flex; flex-direction:column; height:100%; }
  .page-header { display:flex; justify-content:space-between; align-items:baseline; border-bottom:3px solid #1A1A2E; margin-bottom:10px; padding-bottom:6px; }
  .logo { font-size:16pt; font-weight:900; } .logo span { color:#C8AA00; }
  .page-url { font-size:8pt; color:#6B6B80; }
  .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; flex:1; }
  .mini-cal { border:1px solid #e0dff0; border-radius:6px; overflow:hidden; }
  .mini-hdr { background:#1A1A2E; color:#F5E030; font-size:8pt; font-weight:900; padding:4px 8px; letter-spacing:.04em; text-transform:uppercase; }
  table { width:100%; border-collapse:collapse; table-layout:fixed; }
  thead th { font-size:6pt; font-weight:700; text-transform:uppercase; color:#9090a8; padding:2px 3px; text-align:center; border-bottom:1px solid #e0dff0; }
  td.day, td.empty { border:1px solid #f0eff8; vertical-align:top; padding:2px 3px; height:52px; }
  td.empty { background:#fafaf8; }
  td.has-event { background:#FFFBF0; }
  td.today { outline:2px solid #1A1A2E; outline-offset:-2px; }
  .dn { font-size:7pt; font-weight:700; color:#9090a8; margin-bottom:1px; }
  td.today .dn { color:#1A1A2E; }
  .en { font-size:5.5pt; font-weight:700; color:#1A1A2E; line-height:1.3; white-space:normal; word-break:break-word; }
  .lt { display:inline-block; margin-top:1px; font-size:5pt; font-weight:900; background:#F0A030; color:#fff; padding:1px 3px; border-radius:2px; text-transform:uppercase; }
  .page-footer { margin-top:8px; font-size:6.5pt; color:#9090a8; display:flex; justify-content:space-between; }
</style></head><body>
${pagesHtml}
<script>window.addEventListener('load',function(){setTimeout(function(){window.print();},400);});<\/script>
</body></html>`;
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

  // Duplicate check via localStorage — covers the common case
  const seen = JSON.parse(localStorage.getItem('lv2_subscribed') || '[]');
  if (seen.includes(email)) {
    document.getElementById('email-form').style.display = 'none';
    const success = document.getElementById('email-success');
    success.innerHTML = `
      <div class="subscribe-success-headline">You're already on the list.</div>
      <div class="subscribe-success-sub">
        Every Monday morning — which days to move the car, which days to sleep in.<br>
        Check your inbox if you haven't seen it yet (check spam too, Chicago's tough).
      </div>`;
    success.style.display = 'block';
    return;
  }

  const btn = e.target.querySelector('button');
  btn.classList.add('loading');
  btn.disabled = true;
  const tsToken = await getTurnstileToken();
  if (tsWidgetId !== null) turnstile.reset(tsWidgetId);

  if (tsToken === '__timeout__') {
    btn.textContent = 'Subscribe';
    btn.disabled = false;
    alert('Security check timed out. Please try again.');
    return;
  }

  try {
    const res = await fetch(`${WORKER_URL}/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, cf_turnstile_response: tsToken })
    });
    if (res.ok) {
      seen.push(email);
      localStorage.setItem('lv2_subscribed', JSON.stringify(seen));
      if (typeof gtag !== 'undefined') gtag('event', 'sign_up', { method: 'email' });
      document.getElementById('email-form').style.display = 'none';
      const success = document.getElementById('email-success');
      success.innerHTML = `
        <div class="subscribe-success-headline">You're in.</div>
        <div class="subscribe-success-sub">
          Check your email — we just sent you a welcome note.<br>
          Every Monday morning you'll know which days to move the car and which days to sleep in.
        </div>
        <div class="subscribe-share-block">
          <div class="subscribe-share-label">Be that neighbor</div>
          <div class="subscribe-share-tagline">The one people text before a game day. Send them the link before they find out the hard way.</div>
          <div class="subscribe-share-buttons">
            <a class="btn-share sms"
               href="sms:?body=Hey%20%E2%80%94%20check%20out%20lv2park.com.%20It%20tells%20you%20when%20LV2%20parking%20is%20active%20near%20Wrigley%20so%20you%20don%27t%20get%20towed.%20Worth%20knowing%20if%20you%20park%20in%20Lakeview.">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              Text a friend
            </a>
            <a class="btn-share email"
               href="mailto:?subject=Heads%20up%20%E2%80%94%20LV2%20parking%20near%20Wrigley&body=Hey%2C%20found%20this%20%E2%80%94%20lv2park.com%20tells%20you%20when%20LV2%20tow%20zones%20are%20active%20near%20Wrigley%20Field%20so%20you%20don%27t%20get%20towed.%20Worth%20bookmarking%20if%20you%20ever%20park%20in%20Lakeview%20or%20Wrigleyville.">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              Email a friend
            </a>
            <a class="btn-share facebook"
               href="https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Flv2park.com"
               target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="#fff"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>
              Facebook
            </a>
            <button class="btn-share copy" onclick="copyLv2Link(this)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              Copy link
            </button>
          </div>
        </div>`;
      success.style.display = 'block';
    } else throw new Error();
  } catch {
    btn.classList.remove('loading');
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

function copyLv2Link(btn) {
  navigator.clipboard.writeText('https://lv2park.com').then(() => {
    btn.textContent = 'Copied!';
    setTimeout(() => {
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy link';
    }, 2000);
  });
}

/* ─── HELPERS ────────────────────────────────────── */

function isDayGamePast5(events) {
  // Returns true if all events today started before 5 PM and it's now past 5 PM CT
  if (!events || !events.length) return false;
  const nowCT = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' }));
  const hourCT = nowCT.getHours();
  if (hourCT < 17) return false; // not yet 5 PM, no note needed
  return events.every(ev => {
    const t = ev.time || '';
    const m = t.match(/(\d+):(\d+)\s*(AM|PM)/i);
    if (!m) return false;
    let h = parseInt(m[1]);
    const period = m[3].toUpperCase();
    if (period === 'PM' && h < 12) h += 12;
    if (period === 'AM' && h === 12) h = 0;
    return h < 17; // game started before 5 PM
  });
}
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
