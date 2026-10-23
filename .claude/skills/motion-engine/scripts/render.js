#!/usr/bin/env node
/* Render a page built by build.py to MP4 (frame by frame, audio mixed by ffmpeg), or to stills.
 *
 *   node render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 [--fps 30]
 *   node render.js OUT/<slug>.local.html --stills OUT/stills [--times 1.2,5,9.8]   (default: one per scene)
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
const fps = +(opt('--fps') || 30), mp4 = opt('--mp4'), stills = opt('--stills');
const renderJson = html.replace(/\.local\.html$/, '.render.json');
const plan = fs.existsSync(renderJson) ? JSON.parse(fs.readFileSync(renderJson, 'utf8')) : { tracks: [] };

(async () => {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ executablePath: chromePath(), args: ['--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage({ viewport: { width: plan.width || 1080, height: plan.height || 1920 } });
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

  if (stills) {
    fs.mkdirSync(stills, { recursive: true });
    for (const f of fs.readdirSync(stills)) if (/^still_.*\.jpg$/.test(f)) fs.unlinkSync(path.join(stills, f));  // no stale frames in the sheet
    const times = opt('--times') ? opt('--times').split(',').map(Number)
      : meta.scenes.map(([a, b]) => +Math.max(a + .2, Math.min(b, meta.duration) - .35).toFixed(2));  // all blocks have entered
    for (const [i, t] of times.entries()) {
      await page.evaluate(t => renderAt(t), t);
      await page.screenshot({ path: path.join(stills, `still_${String(i).padStart(2, '0')}_${t}s.jpg`), type: 'jpeg', quality: 80 });
    }
    const cols = Math.min(times.length, meta.width > meta.height ? 4 : 6), rows = Math.ceil(times.length / cols);
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-pattern_type', 'glob', '-i', path.join(stills, 'still_*.jpg'),
      '-vf', `scale=${meta.width > meta.height ? 640 : 340}:-1,tile=${cols}x${rows}:padding=8:color=0x222222`, '-frames:v', '1', path.join(stills, 'sheet.jpg')]);
    console.log(JSON.stringify({ stills: times.length, times, sheet: path.join(stills, 'sheet.jpg'), fit: meta.fit, errors }));
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
    ff.push('-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), '-t', String(D), '-movflags', '+faststart', path.resolve(mp4));
    const proc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < N; i++) {
      await page.evaluate(t => renderAt(t), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!proc.stdin.write(buf)) await new Promise(r => proc.stdin.once('drain', r));
      if (i % (fps * 2) === 0) console.log(`image ${i}/${N}`);
    }
    proc.stdin.end();
    const code = await new Promise(r => proc.on('close', r));
    console.log(JSON.stringify({ mp4: path.resolve(mp4), frames: N, seconds: Math.round((Date.now() - t0) / 1000), ffmpeg: code, errors }));
    if (code) process.exitCode = 1;
  }
  await browser.close();
})();
