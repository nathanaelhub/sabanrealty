#!/usr/bin/env node
/**
 * Browser interaction tests for the Saban Realty site (headless Chrome via CDP).
 * Uses Google Chrome, else Brave / Edge / Chromium; CHROME_BIN overrides.
 * Requires a local server on :8899 (the skill/run.sh starts one), or set BASE_URL.
 *
 *   node scripts/site-test/browser-test.mjs
 *
 * Assertions are data-independent (they check filter *behavior* against each
 * card's data attributes, not hardcoded counts), so they stay valid as
 * listings are added/sold. Exit 0 = all pass.
 */
import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';

const CHROME = process.env.CHROME_BIN || [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
].find(existsSync);
if (!CHROME) { console.error("No Chrome, Brave, Edge or Chromium found; set CHROME_BIN."); process.exit(1); }
const BASE = process.env.BASE_URL || "http://localhost:8899/";
const failures = [];
const t = (name, ok, detail = "") => {
  console.log(`  ${ok ? "PASS" : "FAIL"}: ${name}${!ok && detail ? " — " + detail : ""}`);
  if (!ok) failures.push(name);
};

// One browser for the whole run; each page is a new tab. (A browser per page put a
// Dock icon per page on screen with Brave, which does not hide headless instances.)
const PORT = 9390;
let browser = null;
process.on("exit", () => browser?.kill());

async function startBrowser() {
  browser = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run",
    "--window-size=1280,1000", `--remote-debugging-port=${PORT}`, `--user-data-dir=/tmp/site-test-prof-${PORT}`,
    "about:blank"], { stdio: "ignore" });
  // Brave and a cold first launch can take well over 10s to open the debugging port.
  for (let i = 0; i < 75; i++) {
    try { if ((await fetch(`http://127.0.0.1:${PORT}/json/version`)).ok) return; } catch {}
    await new Promise(r => setTimeout(r, 400));
  }
  browser.kill();
  throw new Error(`${CHROME} did not open a debugging port`);
}

async function openPage(url) {
  if (!browser) await startBrowser();
  const target = await (await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURI(url)}`, { method: "PUT" })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 0; const pend = new Map();
  const send = (m, p = {}) => { const i = ++id; ws.send(JSON.stringify({ id: i, method: m, params: p })); return new Promise(r => pend.set(i, r)); };
  await new Promise(r => ws.addEventListener("open", r));
  ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  await send("Runtime.enable");
  const ev = async x => { const r = await send("Runtime.evaluate", { expression: x, returnByValue: true }); return r.result?.result?.value; };
  const waitFor = async (expr, tries = 25) => {
    for (let i = 0; i < tries; i++) { if (await ev(expr)) return true; await new Promise(r => setTimeout(r, 300)); }
    return false;
  };
  const realClick = async expr => {
    const rect = await ev(`(()=>{const e=${expr};if(!e)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2});})()`);
    if (!rect) return false;
    const { x, y } = JSON.parse(rect);
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
    await new Promise(r => setTimeout(r, 300));
    return true;
  };
  return { ev, waitFor, realClick, kill: () => { ws.close(); fetch(`http://127.0.0.1:${PORT}/json/close/${target.id}`).catch(() => {}); } };
}

const setSel = (id, val) => `(()=>{const s=document.getElementById('${id}');s.value='${val}';s.dispatchEvent(new Event('change',{bubbles:true}));})()`;
const visCards = "[...document.querySelectorAll('.property-grid .property-card')].filter(c=>c.style.display!=='none')";

// pick test listings from live data
const data = JSON.parse(readFileSync("data/listings.json", "utf-8"));
const galleryListing = data.properties.find(p => !p.hidden && (p.images || []).length > 3);
const availListing = data.properties.find(p => !p.hidden && p.status === "for-sale" && p.detailStatus !== "under-contract");

// ---------- BUY page filters ----------
{
  const p = await openPage(BASE + "buy/");
  await p.waitFor("document.querySelectorAll('.property-grid .property-card').length>0");
  const total = await p.ev(`${visCards}.length`);
  t("buy: grid renders cards", total > 0);
  await p.ev(setSel("propertyType", "land"));
  t("buy: land filter shows only land", await p.ev(`${visCards}.every(c=>c.dataset.type==='land') && ${visCards}.length>0`));
  await p.ev(setSel("propertyType", "all"));
  await p.ev(setSel("bedrooms", "4+"));
  t("buy: 4+ beds filter respects >=4", await p.ev(`${visCards}.every(c=>parseInt(c.dataset.bedrooms)>=4)`));
  await p.ev(setSel("bedrooms", "all"));
  await p.ev("(()=>{const s=document.getElementById('searchInput');s.value='zzz-no-match';s.dispatchEvent(new Event('input',{bubbles:true}));})()");
  t("buy: nonsense search hides all", await p.ev(`${visCards}.length===0`));
  await p.ev("(()=>{const s=document.getElementById('searchInput');s.value='';s.dispatchEvent(new Event('input',{bubbles:true}));})()");
  t("buy: reset restores all", (await p.ev(`${visCards}.length`)) === total);
  p.kill();
}

// ---------- RENT page 3+ ----------
{
  const p = await openPage(BASE + "rent/");
  await p.waitFor("document.querySelectorAll('.property-grid .property-card').length>0");
  await p.ev(setSel("bedrooms", "3+"));
  t("rent: 3+ filter respects >=3", await p.ev(`${visCards}.every(c=>parseInt(c.dataset.bedrooms)>=3)`));
  p.kill();
}

// ---------- Listing detail: gallery / lightbox / share ----------
if (galleryListing) {
  const p = await openPage(`${BASE}properties/${galleryListing.id}/`);
  await p.waitFor("!!document.getElementById('mainImage')");
  const before = await p.ev("document.getElementById('mainImage').src");
  await p.realClick("document.querySelectorAll('.gallery-thumb-item')[2]");
  t("detail: thumbnail real-click changes main image", before !== await p.ev("document.getElementById('mainImage').src"));
  t("detail: share button in gallery", await p.ev("!!document.querySelector('.gallery-main-wrap #shareBtn')"));
  await p.realClick("document.getElementById('galleryMainWrap')");
  t("detail: main image opens lightbox", await p.ev("document.getElementById('lightbox').classList.contains('open')"));
  p.kill();
}

// ---------- Available listing: viewing form + nav ----------
if (availListing) {
  const p = await openPage(`${BASE}properties/${availListing.id}/`);
  await p.waitFor("!!document.querySelector('.property-header')");
  t("detail: viewing form on available listing", await p.ev("!!document.getElementById('viewingForm')"));
  t("detail: prev/next nav present", await p.ev("!!document.querySelector('.listing-nav')"));
  p.kill();
}

// ---------- Home + blog render ----------
{
  const p = await openPage(BASE);
  await p.waitFor("document.querySelectorAll('#homePropertyGrid .property-card, .property-grid .property-card').length>0", 20);
  t("home: featured cards render", await p.ev("document.querySelectorAll('.property-card').length>0"));
  t("home: showcase present", await p.ev("!!document.querySelector('.showcase-card')"));
  p.kill();
}
{
  const p = await openPage(BASE + "blog/");
  await p.waitFor("document.querySelectorAll('.blog-card').length>0", 15);
  t("blog: post cards render", await p.ev("document.querySelectorAll('.blog-card').length>0"));
  p.kill();
}

console.log();
if (failures.length) { console.log(`RESULT: ${failures.length} FAILURE(S)`); process.exit(1); }
console.log("RESULT: ALL BROWSER TESTS PASS");
process.exit(0);
