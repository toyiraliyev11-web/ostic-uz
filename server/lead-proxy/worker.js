/**
 * ostic.uz lead proxy (Cloudflare Worker).
 *
 * The site form posts the lead here as JSON; this Worker formats it and sends it to
 * Telegram. The bot token and chat id live only in the Worker's secrets (TG_TOKEN,
 * TG_CHAT), never in the page, so they cannot be read from the site's source.
 *
 * Optional: bind a Cloudflare Rate Limiting namespace as RL to cap requests per IP.
 */

const ALLOWED_ORIGINS = ['https://ostic.uz', 'https://www.ostic.uz'];
const MAX_BODY_BYTES = 8000;
const FIELD_LIMITS = {
  name: 80, company: 90, phone: 32, email: 90, location: 90,
  direction: 60, project: 2500, lang: 2
};
const LABELS = [
  ['name', 'Имя'], ['company', 'Компания'], ['phone', 'Телефон'], ['email', 'Почта'],
  ['location', 'Локация'], ['direction', 'Направление'], ['project', 'О проекте'], ['lang', 'Язык']
];

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin'
  };
}

function reply(status, origin, allowed) {
  return new Response(null, { status, headers: allowed ? corsHeaders(origin) : {} });
}

// Strip control characters (keep tab and newline) and cut to the field's limit.
function clean(value, max) {
  return String(value == null ? '' : value)
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '')
    .trim()
    .slice(0, max);
}

export function buildMessage(lead) {
  const lines = LABELS
    .map(([key, label]) => [label, clean(lead[key], FIELD_LIMITS[key])])
    .filter(([, v]) => v)
    .map(([label, v]) => label + ': ' + (label === 'Язык' ? v.toUpperCase() : v));
  return ['\u{1F4E9} Новая заявка с ostic.uz', ''].concat(lines).join('\n');
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const allowed = ALLOWED_ORIGINS.indexOf(origin) >= 0;

    if (request.method === 'OPTIONS') return reply(allowed ? 204 : 403, origin, allowed);
    if (request.method !== 'POST') return reply(405, origin, allowed);
    if (!allowed) return reply(403, origin, false);

    if (env.RL) {
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      const { success } = await env.RL.limit({ key: ip });
      if (!success) return reply(429, origin, true);
    }

    const declared = Number(request.headers.get('Content-Length') || 0);
    if (declared > MAX_BODY_BYTES) return reply(413, origin, true);
    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) return reply(413, origin, true);

    let lead;
    try { lead = JSON.parse(raw); } catch (e) { return reply(400, origin, true); }
    if (!lead || typeof lead !== 'object' || Array.isArray(lead)) return reply(400, origin, true);

    // The form requires a brief of at least 8 characters; hold the line here too.
    if (clean(lead.project, FIELD_LIMITS.project).length < 8) return reply(422, origin, true);
    if (!env.TG_TOKEN || !env.TG_CHAT) return reply(500, origin, true);

    const res = await fetch('https://api.telegram.org/bot' + env.TG_TOKEN + '/sendMessage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: env.TG_CHAT, text: buildMessage(lead), disable_web_page_preview: true })
    });
    return reply(res.ok ? 204 : 502, origin, true);
  }
};
