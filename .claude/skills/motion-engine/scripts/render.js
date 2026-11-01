#!/usr/bin/env node
/* Render a page built by build.py to MP4 (frame by frame, audio mixed by ffmpeg), or to stills.
 *
 *   node render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 [--fps 30]
 *   node render.js OUT/<slug>.local.html --stills OUT/stills [--times 1.2,5,9.8]   (default: one per scene; t = 0 is always added)
 *   node render.js OUT/<slug>.local.html --tsheets OUT/transitions                   (10 consecutive frames per transition)
 *
 * Delivery rule (27/10/2026): the master is 1080 `--quality 100 --bt709` + a WhatsApp version ≤ 15 MB (make_lite.sh);
 * `--scale 2 --master` (4K) only when the requester explicitly asks for it.
 *   --bt709          1080 render with the BT.601 → BT.709 conversion and BT.709 tags (x264 crf 18, crf 16 with --quality 100)
 *   --quality N      JPEG quality of captured frames (default 92, 95 with --master; 100 for the 1080 master)
 *
 * V3 (4K, on explicit request only):
 *   --scale 2        page 1080×1920 rendered with deviceScaleFactor 2 → 2160×3840 frames (also storyboard "renderScale")
 *   --master         libx264 -preset slow -crf 14, high@5.1, yuv420p BT.709 tagged, +faststart (JPEG 95 frames)
 *   --hevc           with --master: libx265 -crf 16 (hvc1) instead of x264
 *   --deliver1080    also writes <slug>-1080.mp4: lanczos reduction of the master, x264 crf 17
 *   --maxrate 8M     caps the bitrate of the delivered file (TikTok ≈ 8 Mbit/s)
 *
 * V4 checks with --stills (results in the printed JSON; exit code 3 with --strict when one fails):
 *   image0           always: t = 0 is rendered; visible texts, contrast of the largest text, source shot present, ok
 *   hors_zone        always for 9:16 `safe` pages: DOM box of each text, logo, banner, CTA and comment sheet against the DA template
 *   taille_min       always: text < 38 px after `fit` (interface detail 34 px, captions 58 px)
 *   --contrast       contrast of every visible text against the pixels behind it (≥ 4.5:1, 3:1 from 100 px)
 *   --fonts          rendered font family of every text node (Chrome DevTools protocol) → fonts.json; exit code 2 when one is a fallback
 *   --scene-exits    3 frames per scene change (end, +0.15 s, +0.3 s): residual opacity of the old scene, overlaps; KO above 0.02 at +0.3 s
 * V4 chunk cache (MP4): --cache DIR [--chunk 5] [--workers 1]: 5 s chunks, unchanged chunks reused, concat without re-encoding, audio muxed after.
 *
 * With --stills it also writes OUT/stills/sheet.jpg, a contact sheet to look at with the Read tool.
 * Needs: playwright (global or local) + Chromium, ffmpeg.
 */
const fs = require('fs'), path = require('path'), crypto = require('crypto'), { spawn, execFileSync } = require('child_process');

function loadPlaywright() {
  for (const p of ['playwright', '/opt/node-tools/node_modules/playwright', path.join(execFileSync('npm', ['root', '-g']).toString().trim(), 'playwright')]) {
    try { return require(p); } catch (_) {}
  }
  console.error('playwright introuvable : npm i -g playwright'); process.exit(1);
}
function chromePath() {
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
  try {
    for (const d of fs.readdirSync(root).filter(d => /^chromium-\d+$/.test(d)).sort().reverse()) {
      const c = path.join(root, d, 'chrome-linux', 'chrome'); if (fs.existsSync(c)) return c;
    }
  } catch (_) {}
  return undefined;
}

const args = process.argv.slice(2), html = path.resolve(args[0]);
const opt = k => { const i = args.indexOf(k); return i > 0 ? args[i + 1] : undefined; };
const flag = k => args.includes(k);
const fps = +(opt('--fps') || 30), mp4 = opt('--mp4'), stills = opt('--stills'), tsheets = opt('--tsheets') && path.resolve(opt('--tsheets'));   // absolu : la liste concat lit des chemins relatifs à elle-même
const renderJson = html.replace(/\.local\.html$/, '.render.json');
const plan = fs.existsSync(renderJson) ? JSON.parse(fs.readFileSync(renderJson, 'utf8')) : { tracks: [] };
const scale = +(opt('--scale') || plan.scale || 1);
const master = flag('--master'), hevc = flag('--hevc'), deliver = flag('--deliver1080'), maxrate = opt('--maxrate'), bt709 = flag('--bt709');
const quality = +(opt('--quality') || (master ? 95 : 92));
const strict = flag('--strict'), wantFonts = flag('--fonts'), wantContrast = flag('--contrast'), wantExits = flag('--scene-exits');
const cacheDir = opt('--cache'), chunkSec = +(opt('--chunk') || 5), workers = Math.max(1, +(opt('--workers') || 1));
const BT709 = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];
// Chromium JPEG = full range, BT.601 matrix → limited range BT.709 (through RGB, so the matrix really changes).
const TO709 = 'scale=in_range=pc:in_color_matrix=bt601,format=gbrp,scale=out_range=tv:out_color_matrix=bt709,format=yuv420p';

function sheet(dir, files, cols, tileW, out) {
  const list = path.join(dir, '.sheet.txt');
  fs.writeFileSync(list, files.map(f => `file '${f.replace(/'/g, "'\\''")}'`).join('\n'));
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list,
    '-vf', `scale=${tileW}:-1,tile=${cols}x${Math.ceil(files.length / cols)}:padding=8:color=0x222222`, '-frames:v', '1', out]);
  fs.unlinkSync(list);
}

/* ---------- V4 : mesures dans la page (fonctions sérialisées par page.evaluate) ---------- */
// Phase 1 : textes visibles (boîte des glyphes, taille réelle après fit, opacité effective, couleur), logos, composants.
function probePage() {
  const M = window.__META, st = document.getElementById('stage'), sr = st.getBoundingClientRect(), k = sr.width / M.width;
  const effOp = e => { let o = 1; for (let n = e; n && n !== document.documentElement; n = n.parentElement) {
    const cs = getComputedStyle(n); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; if (o < .003) return 0; } return o; };
  const scaleOf = e => { let s = 1; for (let n = e; n && n !== st; n = n.parentElement) { const cs = getComputedStyle(n);
    if (cs.transform && cs.transform !== 'none') { const m = new DOMMatrix(cs.transform); s *= Math.hypot(m.a, m.b); }
    if (cs.scale && cs.scale !== 'none') s *= parseFloat(cs.scale) || 1; } return s; };
  const who = e => { const b = e.closest('[data-blk]'); if (b) return {bloc: b.dataset.blk, type: b.dataset.btype};
    if (e.closest('#cap')) return {bloc: 'sous-titres', type: 'captions'}; if (e.closest('#brand')) return {bloc: 'marque', type: 'brand'}; return {bloc: '?', type: '?'}; };
  const bx = (x0, y0, x1, y1) => ({x: +((x0 - sr.left)/k).toFixed(1), y: +((y0 - sr.top)/k).toFixed(1), w: +((x1 - x0)/k).toFixed(1), h: +((y1 - y0)/k).toFixed(1)});
  const onStage = b => b.x < M.width && b.y < M.height && b.x + b.w > 0 && b.y + b.h > 0;
  // boîte visible : intersection avec les ancêtres qui coupent leur contenu (overflow ≠ visible), sinon null
  const clipTo = (e, x0, y0, x1, y1) => { for (let n = e.parentElement; n && n !== st; n = n.parentElement) { const cs = getComputedStyle(n);
    if (cs.overflow !== 'visible' || cs.clipPath !== 'none') { const r = n.getBoundingClientRect(); x0 = Math.max(x0, r.left); y0 = Math.max(y0, r.top); x1 = Math.min(x1, r.right); y1 = Math.min(y1, r.bottom); } }
    return x1 - x0 > 1 && y1 - y0 > 1 ? [x0, y0, x1, y1] : null; };
  const texts = [], els = [];
  const tw = document.createTreeWalker(st, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    if (!n.nodeValue.trim()) continue; const e = n.parentElement; if (!e || e.closest('[data-nomeasure],[data-nozone="1"],.mock-flag,.lower .av')) continue;
    const op = effOp(e); if (op < .05) continue;
    const rg = document.createRange(); rg.selectNodeContents(n); const rs = [...rg.getClientRects()].filter(r => r.width > 1 && r.height > 1); if (!rs.length) continue;
    const cb = clipTo(e, Math.min(...rs.map(r => r.left)), Math.min(...rs.map(r => r.top)), Math.max(...rs.map(r => r.right)), Math.max(...rs.map(r => r.bottom))); if (!cb) continue;
    const b = bx(...cb);
    if (!onStage(b)) continue;
    const cs = getComputedStyle(e), fsz = parseFloat(cs.fontSize) * scaleOf(e);
    els.push(e);
    texts.push(Object.assign(who(e), {i: els.length - 1, txt: n.nodeValue.trim().slice(0, 40), op: +op.toFixed(3), fs: +fsz.toFixed(1), box: b, color: cs.color,
      family: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(), iface: !!e.closest('.app,.sched,.phone,.cmt-sheet,.cmt-ban,.chat'), cap: !!e.closest('#cap')}));
  }
  const parts = [];
  st.querySelectorAll('img.logo, svg.logo, .lower, .cta, .cmt-sheet, .cmt-ban').forEach(e => { if (e.closest('[data-nozone="1"]')) return; const op = effOp(e); if (op < .1) return;
    const r = e.getBoundingClientRect(), cb = clipTo(e, r.left, r.top, r.right, r.bottom); if (!cb) return; const b = bx(...cb); if (!onStage(b) || b.w < 2) return;
    parts.push(Object.assign(who(e), {kind: e.matches('.logo') ? 'logo' : e.className.split(' ')[0], op: +op.toFixed(3), box: b})); });
  let media = false;
  st.querySelectorAll('img, video').forEach(e => { if (media || e.matches('.logo')) return; const op = effOp(e); if (op < .5) return; const r = e.getBoundingClientRect();
    const w = Math.max(0, Math.min(r.right, sr.right) - Math.max(r.left, sr.left)), h = Math.max(0, Math.min(r.bottom, sr.bottom) - Math.max(r.top, sr.top));
    if (w*h > .2*sr.width*sr.height) media = true; });
  window.__probeEls = els;
  return {texts, parts, media};
}
// Phase 3 : statistiques du fond derrière chaque texte (capture prise texte masqué) → contraste au pire (WCAG).
async function contrastPage({ url, texts, dpr }) {
  const img = new Image(); img.src = url; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const g = c.getContext('2d', {willReadFrequently: true}); g.drawImage(img, 0, 0);
  const lin = v => { v /= 255; return v <= .04045 ? v/12.92 : Math.pow((v + .055)/1.055, 2.4); };
  const lum = (r, gg, b) => .2126*lin(r) + .7152*lin(gg) + .0722*lin(b);
  return texts.map(t => {
    const x = Math.max(0, Math.floor(t.box.x*dpr)), y = Math.max(0, Math.floor(t.box.y*dpr)), w = Math.min(c.width - x, Math.ceil(t.box.w*dpr)), h = Math.min(c.height - y, Math.ceil(t.box.h*dpr));
    if (w < 1 || h < 1) return null;
    const d = g.getImageData(x, y, w, h).data, n = w*h, step = Math.max(1, Math.floor(n / 6000)), L = [], cols = [];
    for (let i = 0; i < n; i += step) { const j = i*4; L.push(lum(d[j], d[j+1], d[j+2])); cols.push([d[j], d[j+1], d[j+2]]); }
    const ord = L.map((v, i) => i).sort((a, b) => L[a] - L[b]), q = f => ord[Math.min(ord.length - 1, Math.floor(f*(ord.length - 1)))];
    const m = /rgba?\(([^)]+)\)/.exec(t.color), cc = m ? m[1].split(',').map(Number) : [255, 255, 255], a = (cc[3] ?? 1) * t.op;
    const med = cols[q(.5)], comp = med.map((v, i) => a*cc[i] + (1 - a)*v), lt = lum(...comp), light = lt > L[q(.5)];
    const bgc = cols[q(light ? .9 : .1)], ltw = lum(...bgc.map((v, i) => a*cc[i] + (1 - a)*v)), lb = L[q(light ? .9 : .1)];
    const ratio = (Math.max(ltw, lb) + .05) / (Math.min(ltw, lb) + .05);
    return +ratio.toFixed(2);
  });
}
// Sorties de scène : opacité résiduelle maximale des blocs de la scène i, recouvrements avec les blocs de la scène i + 1.
function exitsPage(i) {
  const st = document.getElementById('stage'), sr = st.getBoundingClientRect(), k = sr.width / window.__META.width;
  const effOp = e => { let o = 1; for (let n = e; n && n !== document.documentElement; n = n.parentElement) {
    const cs = getComputedStyle(n); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; if (o < .001) return 0; } return o; };
  const of = s => [...st.querySelectorAll('[data-blk]')].filter(e => e.dataset.blk.split('.')[0] === String(s) && !e.dataset.blk.includes('L') && e.style.display !== 'none')
    .map(e => { const r = e.getBoundingClientRect(); return {bloc: e.dataset.blk, type: e.dataset.btype, op: effOp(e), r: [(r.left - sr.left)/k, (r.top - sr.top)/k, (r.right - sr.left)/k, (r.bottom - sr.top)/k]}; })
    .filter(x => x.r[2] - x.r[0] > 1);
  const A = of(i), B = of(i + 1), maxOp = Math.max(0, ...A.map(x => x.op)), over = [];
  A.filter(a => a.op > .02).forEach(a => B.filter(b => b.op > .02).forEach(b => { const w = Math.min(a.r[2], b.r[2]) - Math.max(a.r[0], b.r[0]), h = Math.min(a.r[3], b.r[3]) - Math.max(a.r[1], b.r[1]);
    if (w > 4 && h > 4) over.push({a: a.bloc, b: b.bloc, aire: Math.round(w*h), opA: +a.op.toFixed(3), opB: +b.op.toFixed(3)}); }));
  return {maxOp: +maxOp.toFixed(3), plus_visible: (A.find(x => x.op === maxOp) || {}).bloc || null, chevauchements: over};
}

function zoneCheck(meta, pr, t) {
  const Z = meta.zone, out = [], small = [];
  for (const it of pr.texts.concat(pr.parts)) {
    if (Z && it.op > .1) {
      const b = it.box, d = {gauche: Z.left - b.x, droite: b.x + b.w - (meta.width - Z.right), haut: Z.top - b.y, bas: b.y + b.h - (meta.height - Z.bottom)};
      for (const [cote, px] of Object.entries(d)) if (px > .5) out.push({t, bloc: it.bloc, type: it.type, cote, px: Math.round(px), quoi: it.txt || it.kind});
    }
  }
  const byBloc = new Map();
  for (const x of pr.texts) { const floor = x.cap ? 58 : x.iface ? 34 : 38; if (x.fs + .05 < floor) { const k = x.bloc + '|' + floor, o = byBloc.get(k);
    if (!o || x.fs < o.px) byBloc.set(k, {t, bloc: x.bloc, type: x.type, px: x.fs, min: floor, texte: x.txt}); } }
  small.push(...byBloc.values());
  return {out, small};
}
const mergeMax = (list, key, worse) => { const m = new Map(); for (const x of list) { const k = key(x), o = m.get(k); if (!o || worse(x, o)) m.set(k, x); } return [...m.values()]; };

(async () => {
  const { chromium } = loadPlaywright();
  // --allow-file-access-from-files: maskReveal reads video frames into a canvas; without it, sidecar media (file://) taint the canvas.
  const browser = await chromium.launch({ executablePath: chromePath(), args: ['--autoplay-policy=no-user-gesture-required', '--allow-file-access-from-files'] });
  const errors = [];
  async function openPage() {
    const page = await browser.newPage({ viewport: { width: plan.width || 1080, height: plan.height || 1920 }, deviceScaleFactor: scale });
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'warning' || m.type() === 'error') errors.push(m.text()); });
    await page.goto('file://' + html + '?render=1');
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(600);
    const meta = await page.evaluate(() => window.__META);
    if (!meta) { console.error('Page sans __META : erreur JS ?', errors); process.exit(1); }
    await page.setViewportSize({ width: meta.width, height: meta.height });
    meta.fit = await page.evaluate(() => { fit(); fitScenes(); return FIT; });
    return { page, meta };
  }
  const { page, meta } = await openPage();
  const shotOf = pg => (p, type = 'jpeg') => pg.screenshot(Object.assign(type === 'png' ? { type: 'png' } : { type: 'jpeg', quality }, p ? { path: p } : {}));
  const shot = shotOf(page);
  const preheatOf = pg => async () => { await pg.evaluate(t => renderAt(t), 0.5); await pg.evaluate(t => renderAt(t), 0); await pg.waitForTimeout(400); };
  const preheat = preheatOf(page);
  let exitCode = 0;

  if (stills) {
    fs.mkdirSync(stills, { recursive: true });
    for (const f of fs.readdirSync(stills)) if (/^still_.*\.jpg$/.test(f)) fs.unlinkSync(path.join(stills, f));  // no stale frames in the sheet
    let times = opt('--times') ? opt('--times').split(',').map(Number)
      : meta.scenes.map(([a, b]) => +Math.max(a + .2, Math.min(b, meta.duration) - .35).toFixed(2));  // all blocks have entered
    if (!times.some(t => Math.abs(t) < 1e-6)) times = [0].concat(times);   // V4 : l'image 0 est toujours contrôlée (aperçu du fil, vignette)
    await preheat();
    const t0 = Date.now(), checks = { hors_zone: [], taille_min: [], contraste_faible: [] }, fontRows = [];
    let image0 = null, cdp = null;
    if (wantFonts) { cdp = await page.context().newCDPSession(page); await cdp.send('DOM.enable'); await cdp.send('CSS.enable'); await cdp.send('DOM.getDocument', { depth: 0 }); }
    for (const [i, t] of times.entries()) {
      await page.evaluate(t => renderAt(t), t);
      await shot(path.join(stills, `still_${String(i).padStart(2, '0')}_${t}s.jpg`));
      const pr = await page.evaluate(probePage);
      const zc = zoneCheck(meta, pr, t); checks.hors_zone.push(...zc.out); checks.taille_min.push(...zc.small);
      let ratios = null;
      if (wantContrast || Math.abs(t) < 1e-6) {
        // fond seul : textes rendus transparents le temps d'une capture (la mise en page ne change pas)
        await page.evaluate(() => { const s = document.createElement('style'); s.id = '__hide';
          s.textContent = '#stage *{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;-webkit-text-stroke:0!important}'; document.head.appendChild(s); });
        const bg = await page.screenshot({ type: 'png' });
        await page.evaluate(() => document.getElementById('__hide').remove());
        ratios = await page.evaluate(contrastPage, { url: 'data:image/png;base64,' + bg.toString('base64'), texts: pr.texts, dpr: scale });
        pr.texts.forEach((x, j) => { x.contraste = ratios[j]; });
        if (wantContrast) pr.texts.forEach(x => { const thr = x.fs >= 100 ? 3 : 4.5; if (x.contraste != null && x.op > .5 && x.contraste < thr) checks.contraste_faible.push({ t, bloc: x.bloc, type: x.type, texte: x.txt, ratio: x.contraste, seuil: thr }); });
      }
      if (Math.abs(t) < 1e-6) {
        const vis = pr.texts.filter(x => x.op > .9), big = vis.slice().sort((a, b) => b.fs*b.box.w - a.fs*a.box.w)[0];
        const lisible = vis.filter(x => x.contraste != null && x.contraste >= (x.fs >= 100 ? 3 : 4.5));
        const alertes = [];
        if ((meta.flashes || []).some(f => Math.abs(f) < 1e-3)) alertes.push('flashes contient 0 : image 0 blanche à 85 %');
        if (!pr.texts.length && !pr.parts.length && !pr.media) alertes.push('aucun bloc visible à t = 0');
        image0 = { textes: vis.length, plus_grand: big ? { texte: big.txt, px: big.fs, contraste: big.contraste } : null, textes_lisibles: lisible.length, media: pr.media,
          ok: lisible.length > 0 || pr.media, alertes };
      }
      if (cdp) {
        for (const x of pr.texts) {
          const { result } = await cdp.send('Runtime.evaluate', { expression: `window.__probeEls[${x.i}]` });
          if (!result.objectId) continue;
          const { nodeId } = await cdp.send('DOM.requestNode', { objectId: result.objectId });
          const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId }).catch(() => ({ fonts: [] }));
          if (!fonts.length) continue;
          const main = fonts.slice().sort((a, b) => b.glyphCount - a.glyphCount)[0];
          fontRows.push({ instant: t, noeud: x.txt, bloc: x.bloc, declaree: x.family, rendue: main.familyName, autres: fonts.filter(f => f !== main).map(f => `${f.familyName} (${f.glyphCount})`),
            ok: main.familyName.toLowerCase() === x.family.toLowerCase() });
        }
      }
    }
    const ms = Math.round((Date.now() - t0) / times.length);
    const cols = Math.min(times.length, meta.width > meta.height ? 4 : 6), rows = Math.ceil(times.length / cols);
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-pattern_type', 'glob', '-i', path.join(stills, 'still_*.jpg'),
      '-vf', `scale=${meta.width > meta.height ? 640 : 340}:-1,tile=${cols}x${rows}:padding=8:color=0x222222`, '-frames:v', '1', path.join(stills, 'sheet.jpg')]);
    const res = { stills: times.length, times, sheet: path.join(stills, 'sheet.jpg'), fit: meta.fit, scale, msPerStill: ms, transitions: meta.transitions, errors, image0,
      zone: meta.zone, hors_zone: mergeMax(checks.hors_zone, x => x.bloc + '|' + x.cote, (a, b) => a.px > b.px),
      taille_min: mergeMax(checks.taille_min, x => x.bloc + '|' + x.min, (a, b) => a.px < b.px) };
    if (wantContrast) res.contraste_faible = mergeMax(checks.contraste_faible, x => x.bloc + '|' + x.texte, (a, b) => a.ratio < b.ratio);
    if (wantFonts) {
      const ko = fontRows.filter(r => !r.ok), fj = path.join(stills, 'fonts.json');
      fs.writeFileSync(fj, JSON.stringify(fontRows, null, 1));
      res.fonts = { fichier: fj, noeuds: fontRows.length, ko: mergeMax(ko, r => r.declaree + '|' + r.rendue, () => false) };
      if (ko.length) exitCode = 2;
    }
    if (wantExits) {
      res.scene_exits = [];
      for (let i = 0; i + 1 < meta.scenes.length; i++) {
        const end = meta.scenes[i][1], row = { scene: i, fin: end, mesures: [] };
        for (const dt of [0, .15, .3]) { await page.evaluate(t => renderAt(t), end + dt); row.mesures.push(Object.assign({ dt }, await page.evaluate(exitsPage, i))); }
        row.ok = row.mesures[2].maxOp <= .02; res.scene_exits.push(row);
      }
    }
    const failed = (image0 && !image0.ok) || res.hors_zone.length || res.taille_min.length || (res.contraste_faible || []).length || (res.scene_exits || []).some(r => !r.ok);
    if (strict && failed && !exitCode) exitCode = 3;
    console.log(JSON.stringify(res));
  }

  if (tsheets) {   // V3: 10 consecutive frames around each cut (cut − 4 … cut + 5 images), for the DA and the sound designer
    fs.mkdirSync(tsheets, { recursive: true });
    await preheat();
    const out = [];
    for (const T of meta.transitions || []) {
      const dir = path.join(tsheets, `${String(T.n).padStart(2, '0')}-${T.type}`); fs.mkdirSync(dir, { recursive: true });
      const anchor = T.type === 'maskReveal' ? T.at + .35*(T.end - T.at) : T.type === 'morph' ? T.at + .5*(T.end - T.at) : T.cut;   // maskReveal, morph : milieu de la croissance
      const c = Math.round(anchor * fps), files = [];
      for (let i = 0; i < 10; i++) {
        const f = c - 4 + i, t = +(f / fps).toFixed(5), p = path.join(dir, `f${String(i).padStart(2, '0')}_${f}.jpg`);
        await page.evaluate(t => renderAt(t), t); await shot(p); files.push(p);
      }
      const s = path.join(tsheets, `${String(T.n).padStart(2, '0')}-${T.type}.jpg`);
      sheet(dir, files, 5, meta.width > meta.height ? 480 : 270, s);
      out.push({ n: T.n, type: T.type, at: T.at, cut: T.cut, end: T.end, frames: [c - 4, c + 5], sheet: s });
    }
    console.log(JSON.stringify({ tsheets: out, errors }));
  }

  if (mp4) {
    const N = Math.round(meta.duration * fps), D = meta.duration, px = meta.width * meta.height * scale * scale;
    // Son : chaque piste en flottant (aformat fltp), mix amix sans normalisation, un seul encodage AAC 192 kb/s (D-13 : une voix WAV 48 kHz 24 bits est acceptée telle quelle).
    const audioIn = [], parts = [];
    plan.tracks.forEach((tr, i) => {
      audioIn.push('-i', tr.file);
      const ch = [];
      if (tr.from || tr.duration) ch.push(`atrim=start=${tr.from || 0}${tr.duration ? `:duration=${tr.duration}` : ''}`, 'asetpts=PTS-STARTPTS');
      ch.push('aresample=48000', 'aformat=sample_fmts=fltp:channel_layouts=stereo', `volume=${tr.volume ?? 1}`);
      if (tr.music) ch.push(`afade=t=in:d=0.8`, `afade=t=out:st=${Math.max(0, D - (tr.fadeOut || 2))}:d=${tr.fadeOut || 2}`);
      if (tr.start) ch.push(`adelay=${Math.round(tr.start * 1000)}:all=1`);
      parts.push({ i, ch });
    });
    const audioArgs = off => !plan.tracks.length ? [] : ['-filter_complex', parts.map(({ i, ch }) => `[${i + off}:a]${ch.join(',')}[a${i}]`).concat(
      plan.tracks.map((_, i) => `[a${i}]`).join('') + `amix=inputs=${plan.tracks.length}:normalize=0:duration=longest,atrim=duration=${D},apad=whole_dur=${D}[mix]`).join(';'),
      '-map', '[mix]', '-c:a', 'aac', '-b:a', '192k'];
    const videoArgs = () => {
      const v = [];
      if (master && hevc) {
        v.push('-vf', TO709, '-c:v', 'libx265', '-preset', 'slow', '-crf', '16', '-tag:v', 'hvc1',
          '-x265-params', 'log-level=error:colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited', ...BT709);
      } else if (master) {
        const level = px > 2228224 ? (fps > 30 ? '5.2' : '5.1') : '4.2';
        v.push('-vf', TO709, '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-profile:v', 'high', '-level:v', level, ...BT709);
        // VBV au plafond du niveau High (5.1/5.2 : 300 Mbit/s, 4.2 : 62,5 Mbit/s) : le grain en 4K à crf 14 dépasse sinon le niveau annoncé
        if (!maxrate || deliver) v.push('-maxrate', level === '4.2' ? '50M' : '240M', '-bufsize', level === '4.2' ? '62M' : '300M');
      } else if (bt709) {   // E-0 : maître 1080 (--quality 100 --bt709)
        v.push('-vf', TO709, '-c:v', 'libx264', '-preset', 'medium', '-crf', quality >= 100 ? '16' : '18', '-profile:v', 'high', ...BT709);
      } else v.push('-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p');
      if (maxrate && !deliver) v.push('-maxrate', maxrate, '-bufsize', String(parseFloat(maxrate) * 2) + maxrate.replace(/[\d.]/g, ''));
      return v;
    };
    const t0 = Date.now();
    let code = 0, cacheLog = null;
    const encodeFrames = async (pg, from, to, outFile, withAudio) => {
      const ff = ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'];
      if (withAudio) ff.push(...audioIn, '-map', '0:v', ...audioArgs(1)); else ff.push('-map', '0:v');
      ff.push(...videoArgs(), '-r', String(fps));
      if (withAudio) ff.push('-t', String(D), '-movflags', '+faststart');
      ff.push(outFile);
      const proc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
      const sh = shotOf(pg);
      for (let i = from; i < to; i++) {
        await pg.evaluate(t => renderAt(t), i / fps);
        const buf = await sh();
        if (!proc.stdin.write(buf)) await new Promise(r => proc.stdin.once('drain', r));
        if (i % (fps * 2) === 0) console.log(`image ${i}/${N}`);
      }
      proc.stdin.end();
      return new Promise(r => proc.on('close', r));
    };
    if (!cacheDir) {
      await preheat();   // préchauffage : sinon la 1re image peut sortir sans les vidéos
      code = await encodeFrames(page, 0, N, path.resolve(mp4), true);
    } else {
      /* V4 (B-18) : rendu par tranches. Empreinte d'une tranche = scènes, transitions et phrases qui touchent la tranche ±2 s, enveloppe de voix,
         options globales, médias utilisés, template.html, build.py et render.js ; une tranche inchangée est réutilisée. */
      fs.mkdirSync(cacheDir, { recursive: true });
      const C = Math.max(1, Math.round(chunkSec * fps)), K = Math.ceil(N / C);
      const page0 = await page.evaluate(async () => { const h = async v => { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(v)); return [...new Uint8Array(b)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join(''); };
        const media = {}; for (const [k, v] of Object.entries(MEDIA)) media[k] = v.startsWith('data:') ? 'h' + await h(v) : v; return { cfg: CFG, media }; });
      const sha = s => crypto.createHash('sha256').update(s).digest('hex');
      const fileSig = f => { try { const s = fs.statSync(f); return sha(fs.readFileSync(f)).slice(0, 16) + ':' + s.size; } catch (_) { return 'absent'; } };
      const tools = ['../engine/template.html', 'build.py', 'render.js'].map(f => fileSig(path.join(__dirname, f))).join('|');
      const cfg = page0.cfg, glob = Object.assign({}, cfg); ['scenes', 'transitions', 'captions', 'env'].forEach(k => delete glob[k]);
      const mediaSig = Object.fromEntries(Object.entries(page0.media).map(([k, v]) => [k, v.startsWith('h') ? v : fileSig(path.join(path.dirname(html), v))]));
      const opts = JSON.stringify({ scale, fps, quality, master, bt709, hevc, maxrate: maxrate || null, C });
      const phrases = (cfg.captions && cfg.captions.phrases) || [], env = cfg.env || [];
      const fp = k => {
        const a = k*C/fps - 2, b = Math.min(N, (k + 1)*C)/fps + 2;
        const scenes = cfg.scenes.filter(s => s.start - .05 <= b && s.end + .5 >= a);
        const trs = (cfg.transitions || []).filter(T => (T.at <= b && T.end >= a) || (T.type === 'zoomPunch' && T.at < a));
        const ph = phrases.filter(p => p[0][1] - .3 <= b && p[p.length - 1][2] + .7 >= a);
        const blob = JSON.stringify({ scenes, trs, ph, env: env.slice(Math.max(0, Math.floor(a*30)), Math.ceil(b*30)), glob });
        const used = Object.keys(mediaSig).filter(m => m === '__logo' || blob.includes(JSON.stringify(m))).map(m => m + '=' + mediaSig[m]);
        return sha(blob + '|' + used.join(',') + '|' + tools + '|' + opts).slice(0, 16);
      };
      const jobs = [...Array(K).keys()].map(k => ({ k, from: k*C, to: Math.min(N, (k + 1)*C), file: path.join(path.resolve(cacheDir), `chunk-${String(k).padStart(3, '0')}-${fp(k)}.mp4`) }));
      const todo = jobs.filter(j => !fs.existsSync(j.file)), reused = jobs.filter(j => fs.existsSync(j.file)).map(j => j.k);
      const pages = [page];
      for (let w = 1; w < Math.min(workers, todo.length); w++) pages.push((await openPage()).page);
      await Promise.all(pages.map(async (pg, w) => { await preheatOf(pg)();
        for (const j of todo.filter((_, n) => n % pages.length === w)) {
          for (const f of fs.readdirSync(path.resolve(cacheDir))) if (f.startsWith(`chunk-${String(j.k).padStart(3, '0')}-`)) fs.unlinkSync(path.join(path.resolve(cacheDir), f));
          const tmp = j.file.replace(/\.mp4$/, '.part.mp4'), c = await encodeFrames(pg, j.from, j.to, tmp, false);
          if (c) { code = c; return; } fs.renameSync(tmp, j.file);
        } }));
      if (!code) {
        const list = path.join(path.resolve(cacheDir), 'concat.txt'), vid = path.join(path.resolve(cacheDir), 'video.mp4');
        fs.writeFileSync(list, jobs.map(j => `file '${j.file.replace(/'/g, "'\\''")}'`).join('\n'));
        execFileSync('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', vid]);
        const mux = ['-y', '-v', 'error', '-i', vid, ...audioIn, '-map', '0:v', ...audioArgs(1), '-c:v', 'copy', '-t', String(D), '-movflags', '+faststart', path.resolve(mp4)];
        try { execFileSync('ffmpeg', mux, { stdio: 'inherit' }); } catch (_) { code = 1; }
      }
      cacheLog = { tranches: K, secondes_par_tranche: chunkSec, rendues: todo.map(j => j.k), reutilisees: reused, workers: pages.length };
    }
    const secs = (Date.now() - t0) / 1000;
    const res = { mp4: path.resolve(mp4), frames: N, size: [meta.width * scale, meta.height * scale], seconds: Math.round(secs), secPerFrame: +(secs / N).toFixed(3), ffmpeg: code, errors };
    if (cacheLog) res.cache = cacheLog;
    if (!code && deliver) {   // version 1080 : réduction lanczos du maître (jamais un second rendu)
      const d = path.resolve(mp4).replace(/\.mp4$/i, '') + '-1080.mp4';
      const dv = ['-y', '-v', 'error', '-i', path.resolve(mp4), '-vf', `scale=${meta.width}:${meta.height}:flags=lanczos,format=yuv420p`,
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', ...BT709];
      if (maxrate) dv.push('-maxrate', maxrate, '-bufsize', String(parseFloat(maxrate) * 2) + maxrate.replace(/[\d.]/g, ''));
      dv.push('-c:a', 'copy', '-movflags', '+faststart', d);
      execFileSync('ffmpeg', dv, { stdio: 'inherit' });
      res.deliver1080 = d;
    }
    console.log(JSON.stringify(res));
    if (code) exitCode = 1;
  }
  await browser.close();
  process.exitCode = exitCode;
})();
