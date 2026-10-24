#!/usr/bin/env node
/* Render a page built by build.py to MP4 (frame by frame, audio mixed by ffmpeg), or to stills.
 *
 *   node render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 [--fps 30]
 *   node render.js OUT/<slug>.local.html --stills OUT/stills [--times 1.2,5,9.8]   (default: one per scene)
 *   node render.js OUT/<slug>.local.html --tsheets OUT/transitions                   (10 consecutive frames per transition)
 *
 * V3 (premium):
 *   --scale 2        page 1080×1920 rendered with deviceScaleFactor 2 → 2160×3840 frames (also storyboard "renderScale")
 *   --master         libx264 -preset slow -crf 14, high@5.1, yuv420p BT.709 tagged, +faststart (JPEG 95 frames)
 *   --hevc           with --master: libx265 -crf 16 (hvc1) instead of x264
 *   --deliver1080    also writes <slug>-1080.mp4: lanczos reduction of the master, x264 crf 17
 *   --maxrate 8M     caps the bitrate of the delivered file (TikTok ≈ 8 Mbit/s)
 *   --quality N      JPEG quality of captured frames (default 92, 95 with --master)
 *
 * With --stills it also writes OUT/stills/sheet.jpg, a contact sheet to look at with the Read tool.
 * Needs: playwright (global or local) + Chromium, ffmpeg.
 */
const fs = require('fs'), path = require('path'), { spawn, execFileSync } = require('child_process');

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
const fps = +(opt('--fps') || 30), mp4 = opt('--mp4'), stills = opt('--stills'), tsheets = opt('--tsheets');
const renderJson = html.replace(/\.local\.html$/, '.render.json');
const plan = fs.existsSync(renderJson) ? JSON.parse(fs.readFileSync(renderJson, 'utf8')) : { tracks: [] };
const scale = +(opt('--scale') || plan.scale || 1);
const master = flag('--master'), hevc = flag('--hevc'), deliver = flag('--deliver1080'), maxrate = opt('--maxrate');
const quality = +(opt('--quality') || (master ? 95 : 92));
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

(async () => {
  const { chromium } = loadPlaywright();
  // --allow-file-access-from-files: maskReveal reads video frames into a canvas; without it, sidecar media (file://) taint the canvas.
  const browser = await chromium.launch({ executablePath: chromePath(), args: ['--autoplay-policy=no-user-gesture-required', '--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: plan.width || 1080, height: plan.height || 1920 }, deviceScaleFactor: scale });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'warning' || m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + html + '?render=1');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(600);
  const meta = await page.evaluate(() => window.__META);
  if (!meta) { console.error('Page sans __META : erreur JS ?', errors); process.exit(1); }
  await page.setViewportSize({ width: meta.width, height: meta.height });
  meta.fit = await page.evaluate(() => { fit(); fitScenes(); return FIT; });
  const shot = (p) => page.screenshot(Object.assign({ type: 'jpeg', quality }, p ? { path: p } : {}));
  const preheat = async () => { await page.evaluate(t => renderAt(t), 0.5); await page.evaluate(t => renderAt(t), 0); await page.waitForTimeout(400); };

  if (stills) {
    fs.mkdirSync(stills, { recursive: true });
    for (const f of fs.readdirSync(stills)) if (/^still_.*\.jpg$/.test(f)) fs.unlinkSync(path.join(stills, f));  // no stale frames in the sheet
    const times = opt('--times') ? opt('--times').split(',').map(Number)
      : meta.scenes.map(([a, b]) => +Math.max(a + .2, Math.min(b, meta.duration) - .35).toFixed(2));  // all blocks have entered
    await preheat();
    const t0 = Date.now();
    for (const [i, t] of times.entries()) {
      await page.evaluate(t => renderAt(t), t);
      await shot(path.join(stills, `still_${String(i).padStart(2, '0')}_${t}s.jpg`));
    }
    const ms = Math.round((Date.now() - t0) / times.length);
    const cols = Math.min(times.length, meta.width > meta.height ? 4 : 6), rows = Math.ceil(times.length / cols);
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-pattern_type', 'glob', '-i', path.join(stills, 'still_*.jpg'),
      '-vf', `scale=${meta.width > meta.height ? 640 : 340}:-1,tile=${cols}x${rows}:padding=8:color=0x222222`, '-frames:v', '1', path.join(stills, 'sheet.jpg')]);
    console.log(JSON.stringify({ stills: times.length, times, sheet: path.join(stills, 'sheet.jpg'), fit: meta.fit, scale, msPerStill: ms, transitions: meta.transitions, errors }));
  }

  if (tsheets) {   // V3: 10 consecutive frames around each cut (cut − 4 … cut + 5 images), for the DA and the sound designer
    fs.mkdirSync(tsheets, { recursive: true });
    await preheat();
    const out = [];
    for (const T of meta.transitions || []) {
      const dir = path.join(tsheets, `${String(T.n).padStart(2, '0')}-${T.type}`); fs.mkdirSync(dir, { recursive: true });
      const anchor = T.type === 'maskReveal' ? T.at + .35*(T.end - T.at) : T.cut;   // maskReveal : milieu de la croissance
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
    const N = Math.round(meta.duration * fps), D = meta.duration;
    const ff = ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'];
    const parts = [];
    plan.tracks.forEach((tr, i) => {
      ff.push('-i', tr.file);
      let f = `[${i + 1}:a]`;
      const ch = [];
      if (tr.from || tr.duration) ch.push(`atrim=start=${tr.from || 0}${tr.duration ? `:duration=${tr.duration}` : ''}`, 'asetpts=PTS-STARTPTS');
      ch.push('aresample=48000', 'aformat=channel_layouts=stereo', `volume=${tr.volume ?? 1}`);
      if (tr.music) ch.push(`afade=t=in:d=0.8`, `afade=t=out:st=${Math.max(0, D - (tr.fadeOut || 2))}:d=${tr.fadeOut || 2}`);
      if (tr.start) ch.push(`adelay=${Math.round(tr.start * 1000)}:all=1`);
      parts.push(`${f}${ch.join(',')}[a${i}]`);
    });
    if (plan.tracks.length) {
      const mix = plan.tracks.map((_, i) => `[a${i}]`).join('') + `amix=inputs=${plan.tracks.length}:normalize=0:duration=longest,atrim=duration=${D},apad=whole_dur=${D}[mix]`;
      ff.push('-filter_complex', parts.concat(mix).join(';'), '-map', '0:v', '-map', '[mix]', '-c:a', 'aac', '-b:a', '192k');
    } else ff.push('-map', '0:v');
    const px = meta.width * meta.height * scale * scale;
    if (master && hevc) {
      ff.push('-vf', TO709, '-c:v', 'libx265', '-preset', 'slow', '-crf', '16', '-tag:v', 'hvc1',
        '-x265-params', 'log-level=error:colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited', ...BT709);
    } else if (master) {
      const level = px > 2228224 ? (fps > 30 ? '5.2' : '5.1') : '4.2';
      ff.push('-vf', TO709, '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-profile:v', 'high', '-level:v', level, ...BT709);
      // VBV au plafond du niveau High (5.1/5.2 : 300 Mbit/s, 4.2 : 62,5 Mbit/s) : le grain en 4K à crf 14 dépasse sinon le niveau annoncé
      if (!maxrate || deliver) ff.push('-maxrate', level === '4.2' ? '50M' : '240M', '-bufsize', level === '4.2' ? '62M' : '300M');
    } else ff.push('-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p');
    if (maxrate && !deliver) ff.push('-maxrate', maxrate, '-bufsize', String(parseFloat(maxrate) * 2) + maxrate.replace(/[\d.]/g, ''));
    ff.push('-r', String(fps), '-t', String(D), '-movflags', '+faststart', path.resolve(mp4));
    const proc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    await preheat();   // préchauffage : sinon la 1re image peut sortir sans les vidéos
    for (let i = 0; i < N; i++) {
      await page.evaluate(t => renderAt(t), i / fps);
      const buf = await shot();
      if (!proc.stdin.write(buf)) await new Promise(r => proc.stdin.once('drain', r));
      if (i % (fps * 2) === 0) console.log(`image ${i}/${N}`);
    }
    proc.stdin.end();
    const code = await new Promise(r => proc.on('close', r));
    const secs = (Date.now() - t0) / 1000;
    const res = { mp4: path.resolve(mp4), frames: N, size: [meta.width * scale, meta.height * scale], seconds: Math.round(secs), secPerFrame: +(secs / N).toFixed(3), ffmpeg: code, errors };
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
    if (code) process.exitCode = 1;
  }
  await browser.close();
})();
