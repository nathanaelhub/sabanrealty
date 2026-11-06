#!/usr/bin/env node
// render.mjs <video dir> [--stills 1.2,3.4]   Inlines fonts, helpers and timeline into one page, then
// renders each frame deterministically in headless Chromium and pipes PNGs to ffmpeg.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, basename, join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const vid = resolve(process.argv[2]), name = basename(vid);
const stillsArg = process.argv.indexOf('--stills');
const stills = stillsArg > 0 ? process.argv[stillsArg + 1].split(',').map(Number) : null;
const WORKERS = 4;

const b64 = p => readFileSync(join(ROOT, 'node_modules/@fontsource', p)).toString('base64');
const face = (fam, file, w) => `@font-face{font-family:"${fam}";font-weight:${w};font-style:normal;src:url(data:font/woff2;base64,${b64(file)}) format("woff2")}`;
const fonts = [face('Gloock', 'gloock/files/gloock-latin-400-normal.woff2', 400),
  ...[400, 500, 600].map(w => face('Instrument Sans', `instrument-sans/files/instrument-sans-latin-${w}-normal.woff2`, w))].join('\n');
const tl = JSON.parse(readFileSync(join(vid, 'timeline.json'), 'utf8'));
const html = readFileSync(join(vid, 'video.html'), 'utf8')
  .replace('/*@fonts*/', () => fonts)
  .replace('/*@sitefonts*/', () => [
    face('Playfair Display', 'playfair-display/files/playfair-display-latin-600-normal.woff2', 600),
    face('Playfair Display', 'playfair-display/files/playfair-display-latin-700-normal.woff2', 700),
    face('Source Sans 3', 'source-sans-3/files/source-sans-3-latin-400-normal.woff2', 400),
    face('Source Sans 3', 'source-sans-3/files/source-sans-3-latin-600-normal.woff2', 600),
    face('Cormorant Garamond', 'cormorant-garamond/files/cormorant-garamond-latin-500-italic.woff2', 500).replace('font-style:normal', 'font-style:italic')].join('\n'))
  .replace('/*@gsap*/', () => readFileSync(join(ROOT, 'node_modules/gsap/dist/gsap.min.js'), 'utf8'))
  .replace('/*@timeline*/', () => `const TL = ${JSON.stringify(tl)};`)
  .replace('/*@brand*/', () => readFileSync(join(ROOT, 'shared/brand.js'), 'utf8'));
const buildDir = join(ROOT, 'build', name);
mkdirSync(buildDir, { recursive: true });
const page = join(buildDir, 'index.html');
writeFileSync(page, html);

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });  // photos load from disk; canvas stays readable
async function newPage() {
  const ctx = await browser.newContext({ viewport: { width: tl.width, height: tl.height }, deviceScaleFactor: 1, offline: true });
  const p = await ctx.newPage();
  p.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  await p.goto(pathToFileURL(page).href);
  await p.evaluate(() => window.READY);
  return p;
}
// "dom" pages are HTML animated by a paused GSAP timeline, so the frame is a screenshot, not a canvas export.
const grab = tl.dom
  ? async (p, t) => { await p.evaluate(t => renderFrame(t), t); return p.screenshot({ type: 'png' }); }
  : (p, t) => p.evaluate(t => { renderFrame(t); return document.getElementById('c').toDataURL('image/png').split(',')[1]; }, t)
    .then(s => Buffer.from(s, 'base64'));

if (stills) {
  const p = await newPage(), dir = join(buildDir, process.env.STILLS || 'stills');
  mkdirSync(dir, { recursive: true });
  for (const t of stills) writeFileSync(join(dir, `t${t.toFixed(2).padStart(6, '0')}.png`), await grab(p, t));
  console.log(`${stills.length} stills in ${dir}`);
  await browser.close();
  process.exit(0);
}

const pages = await Promise.all(Array.from({ length: WORKERS }, newPage));
const { dur, fps } = await pages[0].evaluate(() => ({ dur: DURATION, fps: FPS }));
const total = Math.round(dur * fps);
const wav = join(buildDir, 'audio.wav');
if (!existsSync(wav)) throw new Error('run audio.py first: ' + wav);
mkdirSync(join(ROOT, 'output'), { recursive: true });
const out = join(ROOT, 'output', `${name}.mp4`);
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-', '-i', wav,
  '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
  '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-t', (total / fps).toFixed(6), out], { stdio: ['pipe', 'inherit', 'inherit'] });
const closed = new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));

// Workers render out of order; frames are written strictly in order.
const done = new Map(); let next = 0, written = 0, wake = null;
await Promise.all([
  ...pages.map(async p => { while (next < total) {
    const i = next++;
    while (i - written > 24) await new Promise(r => setTimeout(r, 20));
    done.set(i, await grab(p, i / fps)); wake?.();
  } }),
  (async () => { while (written < total) {
    if (!done.has(written)) { await new Promise(r => { wake = r; setTimeout(r, 50); }); continue; }
    const buf = done.get(written); done.delete(written);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (++written % 90 === 0) console.log(`${written}/${total}`);
  } ff.stdin.end(); })(),
]);
await closed;
await browser.close();
console.log('wrote', out);
