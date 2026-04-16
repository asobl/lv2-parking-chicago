/**
 * LV2 Park — Cloudflare Worker
 *
 * Handles two endpoints:
 *   POST /subscribe  — add email to Resend audience + send confirmation
 *   POST /contact    — forward contact form to Adam's inbox via Resend
 *
 * Environment variables (set in Cloudflare dashboard, never in code):
 *   RESEND_API_KEY      — from resend.com
 *   RESEND_AUDIENCE_ID  — from resend.com/audiences
 *   NOTIFY_EMAIL        — where contact form submissions get forwarded
 *   TURNSTILE_SECRET    — from dash.cloudflare.com/turnstile (optional, enables captcha)
 */

const ALLOWED_ORIGIN = 'https://lv2park.com';
const FROM_EMAIL     = 'LV2 Park <hello@lv2park.com>';
const RESEND_API     = 'https://api.resend.com';

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === 'OPTIONS') {
      return corsResponse(null, 204, env);
    }

    const url = new URL(request.url);

    if (request.method === 'POST' && url.pathname === '/subscribe') {
      return handleSubscribe(request, env);
    }

    if (request.method === 'POST' && url.pathname === '/contact') {
      return handleContact(request, env);
    }

    if (request.method === 'POST' && url.pathname === '/unsubscribe') {
      return handleUnsubscribe(request, env);
    }

    return corsResponse(JSON.stringify({ error: 'not found' }), 404, env);
  }
};

// ─── SUBSCRIBE ────────────────────────────────────────
async function handleSubscribe(request, env) {
  // Capture subscriber metadata from Cloudflare request
  const cf     = request.cf || {};
  const zip    = cf.postalCode || '';
  const city   = cf.city || '';
  const region = cf.regionCode || cf.region || '';
  const ua     = request.headers.get('User-Agent') || '';
  const device = detectDevice(ua);

  let body;
  try {
    body = await request.json();
  } catch {
    return corsResponse(JSON.stringify({ error: 'invalid JSON' }), 400, env);
  }

  const email = (body.email || '').trim().toLowerCase();
  if (!email || !email.includes('@')) {
    return corsResponse(JSON.stringify({ error: 'invalid email' }), 400, env);
  }

  // Turnstile captcha — only enforced if TURNSTILE_SECRET is configured
  if (env.TURNSTILE_SECRET) {
    const token = body.cf_turnstile_response || '';
    if (!token) {
      return corsResponse(JSON.stringify({ error: 'captcha required' }), 400, env);
    }
    const valid = await verifyTurnstile(token, env.TURNSTILE_SECRET, request);
    if (!valid) {
      return corsResponse(JSON.stringify({ error: 'captcha failed' }), 400, env);
    }
  }

  // 1. Add to Resend audience
  const contactRes = await fetch(`${RESEND_API}/audiences/${env.RESEND_AUDIENCE_ID}/contacts`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, unsubscribed: false })
  });

  if (!contactRes.ok) {
    const err = await contactRes.text();
    console.error('Resend contacts error:', err);
    return corsResponse(JSON.stringify({ error: 'could not subscribe' }), 500, env);
  }

  // 2. Send welcome email to subscriber
  await fetch(`${RESEND_API}/emails`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: FROM_EMAIL,
      to: [email],
      subject: "You're in — LV2 Park will keep you posted",
      html: confirmationEmailHtml()
    })
  });

  // 3. Internal subscriber notification to Adam
  const location = [city, region, zip].filter(Boolean).join(', ') || 'unknown';
  await fetch(`${RESEND_API}/emails`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: FROM_EMAIL,
      to: [env.NOTIFY_EMAIL],
      subject: `New subscriber: ${email}`,
      html: `
        <p style="font-family:sans-serif;">
          <strong>New LV2 Park subscriber</strong><br><br>
          <strong>Email:</strong> ${escHtml(email)}<br>
          <strong>Location:</strong> ${escHtml(location)}<br>
          <strong>Device:</strong> ${escHtml(device)}<br>
        </p>
      `
    })
  }).catch(() => {}); // non-blocking — don't fail subscribe if notification fails

  return corsResponse(JSON.stringify({ ok: true }), 200, env);
}

// ─── CONTACT ──────────────────────────────────────────
async function handleContact(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return corsResponse(JSON.stringify({ error: 'invalid JSON' }), 400, env);
  }

  const { name, email, message } = body;
  if (!name || !email || !message) {
    return corsResponse(JSON.stringify({ error: 'missing fields' }), 400, env);
  }

  const res = await fetch(`${RESEND_API}/emails`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: FROM_EMAIL,
      to: [env.NOTIFY_EMAIL],
      reply_to: email,
      subject: `lv2park.com contact: ${name}`,
      html: `
        <p><strong>From:</strong> ${escHtml(name)} &lt;${escHtml(email)}&gt;</p>
        <p><strong>Message:</strong></p>
        <p>${escHtml(message).replace(/\n/g, '<br>')}</p>
      `
    })
  });

  if (!res.ok) {
    return corsResponse(JSON.stringify({ error: 'could not send' }), 500, env);
  }

  return corsResponse(JSON.stringify({ ok: true }), 200, env);
}

// ─── EMAIL TEMPLATE ───────────────────────────────────
function confirmationEmailHtml() {
  return `
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif;background:#f5f4f0;margin:0;padding:40px 20px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;">
    <div style="height:5px;background:#F5E030;"></div>
    <div style="padding:32px 32px 28px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#6B6B80;margin-bottom:8px;">LV2 PARK</div>
      <h1 style="font-size:28px;font-weight:900;color:#1A1A2E;margin:0 0 16px;">You're in.</h1>
      <p style="font-size:17px;color:#1A1A2E;line-height:1.6;margin:0 0 16px;">
        Every Monday morning you'll get a quick look at the week ahead at Wrigley — which days have games,
        which days LV2 is in effect, and anything else worth knowing.
      </p>
      <p style="font-size:17px;color:#1A1A2E;line-height:1.6;margin:0 0 28px;">
        No fluff. One useful email. That's it.
      </p>
      <a href="https://lv2park.com" style="display:inline-block;background:#6B64D4;color:#fff;font-size:16px;font-weight:700;padding:14px 24px;border-radius:12px;text-decoration:none;">
        Check this week →
      </a>
    </div>
    <div style="padding:20px 32px;border-top:1px solid #f0eff0;">
      <p style="font-size:12px;color:#6B6B80;margin:0;line-height:1.6;">
        lv2park.com · Not affiliated with the Chicago Cubs or MLB.<br>
        <a href="https://lv2park.com/unsubscribe" style="color:#6B6B80;">Unsubscribe</a>
      </p>
    </div>
  </div>
</body>
</html>`;
}

// ─── UNSUBSCRIBE ───────────────────────────────────────
async function handleUnsubscribe(request, env) {
  let body;
  try { body = await request.json(); }
  catch { return corsResponse(JSON.stringify({ error: 'invalid JSON' }), 400, env); }

  const email  = (body.email || '').trim().toLowerCase();
  const reason = (body.reason || '').trim();
  const detail = (body.detail || '').trim();

  if (!email || !email.includes('@')) {
    return corsResponse(JSON.stringify({ error: 'invalid email' }), 400, env);
  }

  // Mark unsubscribed in Resend audience
  await fetch(`${RESEND_API}/audiences/${env.RESEND_AUDIENCE_ID}/contacts`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, unsubscribed: true })
  });

  // Send churn feedback to Adam
  if (reason && env.NOTIFY_EMAIL) {
    await fetch(`${RESEND_API}/emails`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: FROM_EMAIL,
        to: [env.NOTIFY_EMAIL],
        subject: `Unsubscribe feedback: ${email}`,
        html: `
          <p><strong>Someone unsubscribed from LV2 Park</strong></p>
          <p><strong>Email:</strong> ${escHtml(email)}</p>
          <p><strong>Reason:</strong> ${escHtml(reason)}</p>
          ${detail ? `<p><strong>Details:</strong> ${escHtml(detail)}</p>` : ''}
        `
      })
    }).catch(() => {});
  }

  return corsResponse(JSON.stringify({ ok: true }), 200, env);
}

// ─── TURNSTILE ─────────────────────────────────────────
async function verifyTurnstile(token, secret, request) {
  const ip = request.headers.get('CF-Connecting-IP') || '';
  const form = new FormData();
  form.append('secret', secret);
  form.append('response', token);
  if (ip) form.append('remoteip', ip);
  const res  = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: form });
  const data = await res.json();
  return data.success === true;
}

// ─── DEVICE DETECTION ──────────────────────────────────
function detectDevice(ua) {
  if (!ua) return 'unknown';
  if (/iPad/i.test(ua)) return 'tablet';
  if (/iPhone|Android.*Mobile|Mobile/i.test(ua)) return 'mobile';
  if (/Android/i.test(ua)) return 'tablet';
  return 'desktop';
}

// ─── HELPERS ──────────────────────────────────────────
function escHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function corsResponse(body, status, env) {
  // In production, lock to lv2park.com. In dev, allow any origin.
  const origin = env.DEV_MODE ? '*' : ALLOWED_ORIGIN;
  return new Response(body, {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
