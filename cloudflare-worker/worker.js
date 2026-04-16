/**
 * lv2park.com Cloudflare Worker
 *
 * Endpoints:
 *   POST /log-search        Address checker lookups → Searches sheet
 *   POST /subscribe         Email signups → Subscribers sheet
 *   POST /log-street-lookup Data explorer street lookups → Street Lookups sheet
 *   POST /log-pageview      Page loads → Page Views sheet
 *   POST /log-click         CTA / affiliate link clicks → Link Clicks sheet
 *
 * Secret (set via: wrangler secret put GOOGLE_SA_JSON):
 *   GOOGLE_SA_JSON — full service account JSON
 */

const SPREADSHEET_ID    = '1-P5kFhUvi9JieiHoU9odhRa_HiekjkinnaAqPK27Fik';
const SHEET_SEARCHES    = 'Searches';
const SHEET_SUBSCRIBERS = 'Subscribers';
const SHEET_STREETS     = 'Street Lookups';
const SHEET_CLICKS      = 'Link Clicks';

export default {
  async fetch(request, env, ctx) {
    if (request.method === 'OPTIONS') return corsResponse('', 204);

    const url = new URL(request.url);

    if (request.method === 'POST') {
      if (url.pathname === '/log-search')        return handle(request, env, logSearch);
      if (url.pathname === '/subscribe')         return handle(request, env, subscribe);
      if (url.pathname === '/log-street-lookup') return handle(request, env, logStreetLookup);
      if (url.pathname === '/log-click')         return handle(request, env, logClick);
    }

    return new Response('Not found', { status: 404 });
  }
};

async function handle(request, env, fn) {
  try {
    const body = await request.json();
    const token = await getAccessToken(env);
    await fn(token, body);
    return corsResponse(JSON.stringify({ ok: true }), 200);
  } catch (e) {
    console.error(e.message);
    return corsResponse(JSON.stringify({ error: e.message }), 500);
  }
}

// ── Handlers ───────────────────────────────────────────────────────────────────

async function logSearch(token, b) {
  const { date, time } = getCSTDateTime();
  await appendRow(token, SHEET_SEARCHES, [
    date, time,
    b.address    || '',
    b.result     || '',
    str(b.lat), str(b.lon),
    b.page       || '',
    b.referrer   || 'direct',
    b.device     || '',
    b.sessionId  || '',
    b.resultFound !== undefined ? String(b.resultFound) : ''
  ]);
}

async function subscribe(token, b) {
  if (!b.email || !b.email.includes('@')) throw new Error('Invalid email');
  const { date, time } = getCSTDateTime();
  await appendRow(token, SHEET_SUBSCRIBERS, [
    date, time,
    b.email      || '',
    b.page       || '',
    b.referrer   || 'direct',
    b.device     || '',
    b.sessionId  || ''
  ]);
}

async function logStreetLookup(token, b) {
  const { date, time } = getCSTDateTime();
  await appendRow(token, SHEET_STREETS, [
    date, time,
    b.street     || '',
    b.risk       || '',
    str(b.tickets),
    b.page       || '',
    b.referrer   || 'direct',
    b.device     || '',
    b.sessionId  || ''
  ]);
}


async function logClick(token, b) {
  const { date, time } = getCSTDateTime();
  await appendRow(token, SHEET_CLICKS, [
    date, time,
    b.link        || '',
    b.destination || '',
    b.page        || '',
    b.referrer    || 'direct',
    b.device      || '',
    b.sessionId   || ''
  ]);
}

// ── CST datetime ──────────────────────────────────────────────────────────────

function getCSTDateTime() {
  const now = new Date();
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Chicago',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  });
  const p = Object.fromEntries(fmt.formatToParts(now).map(({ type, value }) => [type, value]));
  return {
    date: `${p.year}-${p.month}-${p.day}`,
    time: `${p.hour}:${p.minute}:${p.second}`
  };
}

function str(v) { return v !== undefined && v !== null ? String(v) : ''; }

// ── Google Auth ────────────────────────────────────────────────────────────────

async function getAccessToken(env) {
  const sa = JSON.parse(env.GOOGLE_SA_JSON);
  const now = Math.floor(Date.now() / 1000);
  const claims = {
    iss: sa.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now
  };
  const jwt = await signJWT(claims, sa.private_key);
  const resp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=${jwt}`
  });
  const data = await resp.json();
  if (!data.access_token) throw new Error('Google auth failed: ' + JSON.stringify(data));
  return data.access_token;
}

async function signJWT(claims, privateKeyPem) {
  const b64url = obj =>
    btoa(JSON.stringify(obj)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const header = { alg: 'RS256', typ: 'JWT' };
  const signingInput = `${b64url(header)}.${b64url(claims)}`;
  const pemContents = privateKeyPem
    .replace(/-----BEGIN PRIVATE KEY-----/, '')
    .replace(/-----END PRIVATE KEY-----/, '')
    .replace(/\s/g, '');
  const keyData = Uint8Array.from(atob(pemContents), c => c.charCodeAt(0));
  const key = await crypto.subtle.importKey(
    'pkcs8', keyData, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']
  );
  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(signingInput)
  );
  const sigB64 = btoa(String.fromCharCode(...new Uint8Array(signature)))
    .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  return `${signingInput}.${sigB64}`;
}

// ── Sheets API ─────────────────────────────────────────────────────────────────

async function appendRow(token, sheetName, values) {
  const range = encodeURIComponent(`${sheetName}!A1`);
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${range}:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ values: [values] })
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Sheets API ${resp.status}: ${text}`);
  }
  return resp.json();
}

// ── CORS ───────────────────────────────────────────────────────────────────────

function corsResponse(body, status) {
  return new Response(body, {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
