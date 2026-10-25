// Backend for the admin page (admin/index.html).
//
// It does these things for anyone holding the passphrase, and nothing else:
//   PUT  /upload/listings/<id>/<file>.jpg         store one photo in R2 (never overwrites)
//   PUT  /upload/thumbs/listings/<id>/<file>.jpg  store the small card copy of a photo already uploaded
//   POST /change                                  hand a listing change to GitHub Actions
//   GET  /status?request_id=...                   report how that change is going
//   GET  /health                                  say whether publishing still works (GitHub token)
//
// Once a day (cron in wrangler.toml) it also checks the GitHub token and, 14/7/3/1 days before
// it expires, asks the admin-token-reminder workflow to open an issue that emails Nathanael.
//
// It does not edit the site. The GitHub Action (scripts/admin/apply_change.py)
// validates every change again before anything is committed.

const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const MAX_THUMB_BYTES = 1024 * 1024;
const WARN_DAYS = 14;
const REMIND_ON_DAYS = [14, 7, 3, 1];
const MAX_CHANGE_BYTES = 60 * 1024; // GitHub caps client_payload at ~64 KB
const MIN_PASSPHRASE_LENGTH = 16;
const UPLOAD_PATH = /^\/upload\/((thumbs\/)?(listings\/([a-z0-9]+(?:-[a-z0-9]+)*)\/([a-z0-9-]+\.jpg)))$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export default {
  async fetch(request, env) {
    const cors = corsHeaders(request, env);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    let response;
    try {
      response = await route(request, env);
    } catch (err) {
      console.error(err);
      response = json({ error: 'Something went wrong on the server.' }, 500);
    }
    for (const [k, v] of Object.entries(cors)) response.headers.set(k, v);
    return response;
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(remindIfExpiring(env));
  },
};

function corsHeaders(request, env) {
  const origin = request.headers.get('Origin');
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim());
  if (!origin || !allowed.includes(origin)) return {};
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, PUT, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

// The page sends the passphrase URI-encoded so non-ASCII characters survive the header.
async function authorized(request, env) {
  const secret = env.ADMIN_PASSPHRASE || '';
  if (secret.length < MIN_PASSPHRASE_LENGTH) return false; // refuse to run with a weak or missing secret
  const header = request.headers.get('Authorization') || '';
  if (!header.startsWith('Bearer ')) return false;
  let given;
  try {
    given = decodeURIComponent(header.slice(7));
  } catch {
    return false;
  }
  const enc = new TextEncoder();
  const [a, b] = await Promise.all([
    crypto.subtle.digest('SHA-256', enc.encode(given)),
    crypto.subtle.digest('SHA-256', enc.encode(secret)),
  ]);
  return crypto.subtle.timingSafeEqual(a, b);
}

async function route(request, env) {
  if (!(await authorized(request, env))) return json({ error: 'Wrong passphrase.' }, 401);
  const url = new URL(request.url);
  const { method } = request;

  if (method === 'GET' && url.pathname === '/auth') return new Response(null, { status: 204 });
  if (method === 'PUT' && url.pathname.startsWith('/upload/')) return upload(request, env, url);
  if (method === 'POST' && url.pathname === '/change') return change(request, env);
  if (method === 'GET' && url.pathname === '/status') return status(env, url);
  if (method === 'GET' && url.pathname === '/health') return json(await tokenHealth(env));
  return json({ error: 'Not found.' }, 404);
}

async function upload(request, env, url) {
  const m = UPLOAD_PATH.exec(url.pathname);
  // Files must be named after their listing, so one listing can't write into another's folder name.
  if (!m || !m[5].startsWith(`${m[4]}-`)) return json({ error: 'Bad photo name.' }, 400);
  const key = m[1];
  const isThumb = Boolean(m[2]);
  const maxBytes = isThumb ? MAX_THUMB_BYTES : MAX_PHOTO_BYTES;
  const photoUrl = `${env.PUBLIC_BASE}/${key}`;

  if (Number(request.headers.get('Content-Length') || 0) > maxBytes) {
    return json({ error: 'Photo is too large.' }, 413);
  }
  // A card copy is only accepted for a photo that is already there.
  if (isThumb && !(await env.BUCKET.head(m[3]))) return json({ error: 'Upload the photo first.' }, 409);
  const body = await request.arrayBuffer();
  if (body.byteLength > maxBytes) return json({ error: 'Photo is too large.' }, 413);
  const head = new Uint8Array(body.slice(0, 3));
  if (head[0] !== 0xff || head[1] !== 0xd8 || head[2] !== 0xff) {
    return json({ error: 'Only JPEG photos are accepted.' }, 415);
  }

  // Never overwrite: photos of published listings can't be replaced from here.
  if (await env.BUCKET.head(key)) return json({ error: 'Already uploaded.', url: photoUrl }, 409);
  await env.BUCKET.put(key, body, {
    httpMetadata: { contentType: 'image/jpeg', cacheControl: 'public, max-age=31536000, immutable' },
  });
  return json({ url: photoUrl });
}

function github(env, path, init = {}) {
  return fetch(`https://api.github.com/repos/${env.REPO}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'sabanrealty-admin',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    },
  });
}

async function change(request, env) {
  const text = await request.text();
  if (text.length > MAX_CHANGE_BYTES) return json({ error: 'That is too much text to publish at once.' }, 413);
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = null;
  }
  if (!body || typeof body !== 'object' || Array.isArray(body) || typeof body.action !== 'string') {
    return json({ error: 'Bad request.' }, 400);
  }
  const request_id = crypto.randomUUID();
  const payload = { ...body, request_id };

  if (env.DRY_RUN === '1') return json({ request_id, dry_run: true, change: payload });

  const res = await github(env, '/dispatches', {
    method: 'POST',
    body: JSON.stringify({ event_type: 'admin-change', client_payload: { change: payload } }),
  });
  if (res.status !== 204) {
    console.error('dispatch failed', res.status, await res.text());
    return json({ error: 'Could not reach the website publisher. Try again in a minute.' }, 502);
  }
  return json({ request_id });
}

// pending = GitHub hasn't shown the run yet; running; success; failed (with a reason when available).
async function status(env, url) {
  const id = url.searchParams.get('request_id') || '';
  if (!UUID.test(id)) return json({ error: 'Bad request.' }, 400);
  if (env.DRY_RUN === '1') return json({ state: 'success', dry_run: true });

  const res = await github(env, `/actions/workflows/${env.WORKFLOW}/runs?event=repository_dispatch&per_page=30`);
  if (!res.ok) return json({ error: 'Could not check progress.' }, 502);
  const title = `admin ${id}`;
  const run = ((await res.json()).workflow_runs || []).find((r) => r.display_title === title || r.name === title);
  if (!run) return json({ state: 'pending' });
  if (run.status !== 'completed') return json({ state: 'running' });
  if (run.conclusion === 'success') return json({ state: 'success' });
  return json({ state: 'failed', reason: await failureReason(env, run.id) });
}

// apply_change.py reports refusals as ::error:: annotations written for the person at the form.
async function failureReason(env, runId) {
  try {
    const jobs = await (await github(env, `/actions/runs/${runId}/jobs`)).json();
    for (const job of jobs.jobs || []) {
      const notes = await (await github(env, `/check-runs/${job.id}/annotations`)).json();
      const failure = Array.isArray(notes) && notes.find((n) => n.annotation_level === 'failure' && n.message);
      if (failure && !/^Process completed with exit code/.test(failure.message)) return failure.message;
    }
  } catch (err) {
    console.error(err);
  }
  return null;
}

// GitHub sends a fine-grained token's expiry on every API response.
// ok: true while the token works; daysLeft is null for a token that never expires.
async function tokenHealth(env) {
  if (env.DRY_RUN === '1') return { ok: true, daysLeft: null, dry_run: true };
  let res;
  try {
    res = await github(env, '');
  } catch {
    return { ok: null };
  }
  if (res.status === 401) return { ok: false, daysLeft: 0 };
  if (!res.ok) return { ok: null };
  const header = res.headers.get('github-authentication-token-expiration');
  const expires = parseExpiry(header);
  if (Number.isNaN(expires)) return { ok: true, daysLeft: null };
  const daysLeft = Math.max(0, Math.floor((expires - Date.now()) / 86400000));
  return { ok: true, daysLeft, warn: daysLeft <= WARN_DAYS, expires: new Date(expires).toISOString().slice(0, 10) };
}

// e.g. "2026-12-01 00:00:00 UTC" or "2026-12-01 00:00:00 -0800"
function parseExpiry(header) {
  const m = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})\s*(UTC|Z|[+-]\d{2}:?\d{2})?$/.exec((header || '').trim());
  if (!m) return NaN;
  let zone = m[3] || 'Z';
  if (zone === 'UTC') zone = 'Z';
  else if (/^[+-]\d{4}$/.test(zone)) zone = `${zone.slice(0, 3)}:${zone.slice(3)}`;
  return Date.parse(`${m[1]}T${m[2]}${zone}`);
}

async function remindIfExpiring(env) {
  const health = await tokenHealth(env);
  if (!health.ok || !REMIND_ON_DAYS.includes(health.daysLeft)) return;
  const res = await github(env, '/dispatches', {
    method: 'POST',
    body: JSON.stringify({ event_type: 'admin-token-expiring', client_payload: { days_left: health.daysLeft, expires: health.expires } }),
  });
  if (res.status !== 204) console.error('reminder dispatch failed', res.status, await res.text());
}
