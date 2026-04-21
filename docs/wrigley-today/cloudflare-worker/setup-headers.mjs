/**
 * One-time setup: creates all lv2park tracking sheets with
 * styled frozen headers and cleared data row formatting.
 * Run: node setup-headers.mjs
 */

import { readFileSync } from 'fs';
import { createSign } from 'crypto';

const SA = JSON.parse(readFileSync('/Users/asobol/Downloads/ew-playground-42e0ee163a0d.json', 'utf8'));
const SPREADSHEET_ID = '1-P5kFhUvi9JieiHoU9odhRa_HiekjkinnaAqPK27Fik';

const SHEETS = [
  {
    name: 'Searches',
    headers: ['Date', 'Time (CST)', 'Address', 'Result', 'Lat', 'Lon', 'Page', 'Referrer', 'Device', 'Session ID', 'Result Found']
  },
  {
    name: 'Subscribers',
    headers: ['Date', 'Time (CST)', 'Email', 'Page', 'Referrer', 'Device', 'Session ID']
  },
  {
    name: 'Street Lookups',
    headers: ['Date', 'Time (CST)', 'Street', 'Risk', 'Tickets', 'Page', 'Referrer', 'Device', 'Session ID']
  },
  {
    name: 'Link Clicks',
    headers: ['Date', 'Time (CST)', 'Link', 'Destination', 'Page', 'Referrer', 'Device', 'Session ID']
  }
];

// ── JWT / Auth ──────────────────────────────────────────────────────────────

function signJWT(claims, privateKeyPem) {
  const b64url = obj => Buffer.from(JSON.stringify(obj)).toString('base64url');
  const header = { alg: 'RS256', typ: 'JWT' };
  const signingInput = `${b64url(header)}.${b64url(claims)}`;
  const sign = createSign('RSA-SHA256');
  sign.update(signingInput);
  const sig = sign.sign(privateKeyPem, 'base64url');
  return `${signingInput}.${sig}`;
}

async function getAccessToken() {
  const now = Math.floor(Date.now() / 1000);
  const claims = {
    iss: SA.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600, iat: now
  };
  const jwt = signJWT(claims, SA.private_key);
  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=${jwt}`
  });
  const data = await res.json();
  if (!data.access_token) throw new Error('Auth failed: ' + JSON.stringify(data));
  return data.access_token;
}

// ── Sheets helpers ──────────────────────────────────────────────────────────

async function sheetsRequest(token, method, path, body) {
  const base = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}`;
  const res = await fetch(base + path, {
    method,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await res.json();
  if (data.error) throw new Error(JSON.stringify(data.error));
  return data;
}

async function getExistingSheets(token) {
  const data = await sheetsRequest(token, 'GET', '');
  return data.sheets.map(s => ({ title: s.properties.title, id: s.properties.sheetId }));
}

async function createSheet(token, title) {
  const data = await sheetsRequest(token, 'POST', ':batchUpdate', {
    requests: [{ addSheet: { properties: { title } } }]
  });
  return data.replies[0].addSheet.properties.sheetId;
}

async function setValues(token, range, values) {
  return sheetsRequest(token, 'PUT',
    `/values/${encodeURIComponent(range)}?valueInputOption=USER_ENTERED`,
    { values }
  );
}

function headerFormatRequest(sheetId, numCols) {
  return {
    repeatCell: {
      range: { sheetId, startRowIndex: 0, endRowIndex: 1, startColumnIndex: 0, endColumnIndex: numCols },
      cell: {
        userEnteredFormat: {
          backgroundColor: { red: 0.918, green: 0.918, blue: 0.918 },
          textFormat: { bold: true, foregroundColor: { red: 0, green: 0, blue: 0 }, fontSize: 11 },
          verticalAlignment: 'MIDDLE'
        }
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'
    }
  };
}

function clearDataRowsRequest(sheetId, numCols) {
  return {
    repeatCell: {
      range: { sheetId, startRowIndex: 1, endRowIndex: 1000, startColumnIndex: 0, endColumnIndex: numCols },
      cell: {
        userEnteredFormat: {
          backgroundColor: { red: 1, green: 1, blue: 1 },
          textFormat: { bold: false, foregroundColor: { red: 0, green: 0, blue: 0 }, fontSize: 10 },
          horizontalAlignment: 'LEFT',
          numberFormat: { type: 'TEXT' }
        }
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,numberFormat)'
    }
  };
}

function freezeRowRequest(sheetId) {
  return {
    updateSheetProperties: {
      properties: { sheetId, gridProperties: { frozenRowCount: 1 } },
      fields: 'gridProperties.frozenRowCount'
    }
  };
}

// ── Main ────────────────────────────────────────────────────────────────────

const token = await getAccessToken();
console.log('Auth OK\n');

const existing = await getExistingSheets(token);
const existingNames = existing.map(s => s.title);
console.log('Existing sheets:', existingNames.join(', '));

const sheetIds = Object.fromEntries(existing.map(s => [s.title, s.id]));

// Create any missing sheets
for (const sheet of SHEETS) {
  if (!existingNames.includes(sheet.name)) {
    const id = await createSheet(token, sheet.name);
    sheetIds[sheet.name] = id;
    console.log(`Created sheet: "${sheet.name}" (id ${id})`);
  } else {
    console.log(`Sheet exists: "${sheet.name}" (id ${sheetIds[sheet.name]})`);
  }
}

// Write headers + apply formatting to all sheets
const formatRequests = [];
for (const sheet of SHEETS) {
  const id = sheetIds[sheet.name];
  const cols = sheet.headers.length;
  const colLetter = String.fromCharCode(64 + cols);
  await setValues(token, `${sheet.name}!A1:${colLetter}1`, [sheet.headers]);
  console.log(`Headers written: "${sheet.name}"`);
  formatRequests.push(
    headerFormatRequest(id, cols),
    clearDataRowsRequest(id, cols),
    freezeRowRequest(id)
  );
}

await sheetsRequest(token, 'POST', ':batchUpdate', { requests: formatRequests });
console.log('\nFormatting applied to all sheets.');
console.log('\nDone. All 5 sheets ready.');
