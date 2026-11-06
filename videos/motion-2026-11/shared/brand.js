// Shared canvas helpers. Everything is a pure function of time: no clocks, no requestAnimationFrame.
const NAVY = '#0a2540', CORAL = '#e07a5f', GOLD = '#d4a853', WHITE = '#ffffff';
const SERIF = 'Gloock', SANS = '"Instrument Sans"';
const W = TL.width, H = TL.height, VERTICAL = H > W;
const beat = 60 / TL.bpm, DURATION = TL.shots.reduce((a, s) => a + s.beats, 0) * beat;
const canvas = document.getElementById('c');
canvas.width = W; canvas.height = H;
const ctx = canvas.getContext('2d', { alpha: false });
ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const easeInOut = p => .5 - .5 * Math.cos(Math.PI * clamp(p));
const easeOut = p => 1 - Math.pow(1 - clamp(p), 3);
const mix = (a, b, p) => a + (b - a) * p;

// Cut list with absolute times, from timeline.json only.
let _acc = 0;
const SHOTS = TL.shots.map(s => { const o = { ...s, start: _acc * beat, dur: s.beats * beat }; _acc += s.beats; return o; });
const shotAt = t => SHOTS.findLast(s => t >= s.start - 1e-6) || SHOTS[0];

const IMGS = {};
async function loadPhotos() {
  await Promise.all(Object.keys(TL.photos || {}).map(k => new Promise((res, rej) => {
    const i = new Image(); i.onload = () => { IMGS[k] = i; res(); };
    i.onerror = () => rej(new Error('missing photo ' + k)); i.src = 'photos/' + k + '.jpg';
  })));
}

// One camera move: from/to are {s: scale, x, y: centre as a fraction of the photo}, eased over p.
function cam(from, to, p) { const e = easeInOut(p); return { s: mix(from.s, to.s, e), x: mix(from.x, to.x, e), y: mix(from.y, to.y, e) }; }
function photo(key, c) {
  const im = IMGS[key], cover = Math.max(W / im.width, H / im.height) * c.s;
  const dw = im.width * cover, dh = im.height * cover;
  const dx = W / 2 - c.x * dw, dy = H / 2 - c.y * dh;
  // A camera path must fit inside the photo. Clamping here would squash the ease into an abrupt move.
  if (dx > .5 || dy > .5 || dx + dw < W - .5 || dy + dh < H - .5) throw new Error(`camera leaves photo ${key}: ${JSON.stringify(c)}`);
  ctx.drawImage(im, dx, dy, dw, dh);
}

function text(str, x, y, { font, size, weight = 400, color = WHITE, align = 'left', spacing = 0, alpha = 1, shadow = 0 }) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.font = `${weight} ${size}px ${font}`;
  ctx.letterSpacing = spacing + 'px';
  ctx.textAlign = align; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = color;
  if (shadow) { ctx.shadowColor = 'rgba(0,0,0,.65)'; ctx.shadowBlur = shadow; ctx.shadowOffsetY = shadow / 5; }
  ctx.fillText(str, x, y);
  ctx.restore();
}
function measure(str, { font, size, weight = 400, spacing = 0 }) {
  ctx.save(); ctx.font = `${weight} ${size}px ${font}`; ctx.letterSpacing = spacing + 'px';
  const w = ctx.measureText(str).width; ctx.restore(); return w;
}
// Entrance on a beat: fades and settles, then is exactly still.
const SETTLE = .45;
const enter = (t, t0) => ({ a: easeOut((t - t0) / SETTLE), dy: 22 * (1 - easeOut((t - t0) / SETTLE)) });

function lockup(x, y, scale = 1, alpha = 1) {
  const size = 26 * scale, sp = 7 * scale, o = { font: SANS, size, weight: 600, spacing: sp, alpha, shadow: 10 * scale };
  const a = measure('SABAN ', o), b = measure('REALTY', o);
  text('SABAN ', x, y, o); text('REALTY', x + a, y, { ...o, color: GOLD });
  ctx.save(); ctx.globalAlpha = alpha; ctx.fillStyle = GOLD;
  ctx.fillRect(x, y + 12 * scale, a + b - sp, Math.max(2, 2 * scale)); ctx.restore();
}
// The lockup on photos: a small glass chip so gold stays legible on sky, brick or leaves.
function brandBar(x, y, scale = 1.35) {
  const o = { font: SANS, size: 26 * scale, weight: 600, spacing: 7 * scale }, pad = 22;
  const w = measure('SABAN REALTY', o) - o.spacing;
  ctx.save(); ctx.beginPath(); ctx.roundRect(x - pad, y - 26 * scale - pad + 4, w + pad * 2, 26 * scale + 12 * scale + pad * 2 - 4, 14); ctx.clip();
  ctx.filter = 'blur(18px)'; ctx.drawImage(canvas, 0, 0); ctx.filter = 'none';
  ctx.fillStyle = 'rgba(10,37,64,.6)'; ctx.fillRect(0, 0, W, H); ctx.restore();
  lockup(x, y, scale);
}
// Glass Panel: dark, rounded, translucent, blurring what sits behind it. Bottom right.
function glass(x, y, w, h, alpha = 1, r = 22) {
  ctx.save(); ctx.globalAlpha = alpha;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.clip();
  ctx.filter = 'blur(26px)'; ctx.drawImage(canvas, 0, 0); ctx.filter = 'none';
  ctx.fillStyle = 'rgba(10,37,64,.68)'; ctx.fillRect(x, y, w, h);
  ctx.restore();
  ctx.save(); ctx.globalAlpha = alpha * .55; ctx.strokeStyle = GOLD; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.stroke(); ctx.restore();
}
// Editorial style: dark gradient rising from the bottom behind the text.
function rise(top, bottom = H, strength = .92) {
  const g = ctx.createLinearGradient(0, top, 0, bottom);
  g.addColorStop(0, 'rgba(10,37,64,0)'); g.addColorStop(.45, `rgba(10,37,64,${strength * .72})`); g.addColorStop(1, `rgba(10,37,64,${strength})`);
  ctx.fillStyle = g; ctx.fillRect(0, top, W, bottom - top);
}
// End card: a straight cut to lockup, site and phone, still from its first frame to the last.
function endCard() {
  ctx.fillStyle = NAVY; ctx.fillRect(0, 0, W, H);
  const cx = W / 2, cy = VERTICAL ? 860 : H / 2, sc = VERTICAL ? 2.3 : 2.6;
  const o = { font: SANS, size: 26 * sc, weight: 600, spacing: 7 * sc };
  const lw = measure('SABAN REALTY', o) - o.spacing;
  lockup(cx - lw / 2, cy - 50, sc);
  text('sabanrealty.com', cx, cy + 74, { font: SERIF, size: VERTICAL ? 76 : 72, align: 'center' });
  text('+599 416 5497', cx, cy + 156, { font: SANS, size: VERTICAL ? 54 : 50, weight: 500, align: 'center', color: GOLD, spacing: 2 });
}

window.DURATION = DURATION;
window.FPS = TL.fps;
window.READY = (async () => {
  await Promise.all([`400 64px ${SERIF}`, `400 32px ${SANS}`, `500 32px ${SANS}`, `600 32px ${SANS}`].map(f => document.fonts.load(f, 'SABAN Realty $775,000')));
  for (const f of [`64px ${SERIF}`, `32px ${SANS}`]) if (!document.fonts.check(f)) throw new Error('font missing: ' + f);
  await loadPhotos();
})();
