#!/usr/bin/env python3
"""Build a BitEye motion video page from a storyboard.json.

Usage: python3 -I build.py STORYBOARD.json --out OUT_DIR [--sidecar]

Writes, in OUT_DIR:
  <slug>.html         page to publish as an Artifact (no <!doctype>, the publisher wraps it)
  <slug>.local.html   same page as a standalone document (open in a browser, or render to MP4)
  <slug>.render.json  what render.js needs: size, duration, audio tracks to mix
  media/              prepared media (always; also referenced by the page in --sidecar mode)

Media paths in the storyboard are relative to the storyboard file.
Only ffmpeg/ffprobe are required (no Python packages).
"""
import argparse, base64, json, math, os, re, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'engine', 'template.html')
FORMATS = {'9:16': (1080, 1920), '16:9': (1920, 1080), '1:1': (1080, 1080), '4:5': (1080, 1350)}
EMBED_LIMIT = 14 * 1024 * 1024


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True)


def probe_duration(path):
    out = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).stdout
    return float(out.strip())


def envelope(path, fps=30):
    """Voice loudness per frame, 0..1, used to animate the glow and the waveform."""
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    n = len(raw) // 2
    s = struct.unpack('<%dh' % n, raw[:n * 2])
    hop = 16000 // fps
    env = []
    for i in range(0, n, hop):
        c = s[i:i + hop]
        env.append(math.sqrt(sum(x * x for x in c) / max(1, len(c))) / 32768)
    m = max(env) if env and max(env) > 0 else 1
    return [round(min(1, (e / m) ** 0.6), 3) for e in env]


def load_words(path):
    data = json.load(open(path, encoding='utf-8'))
    if isinstance(data, dict):
        data = data.get('words') or (data.get('transcripts') or [{}])[0].get('words', [])
    return [w for w in data if w.get('type', 'word') == 'word']


def make_phrases(words, cap):
    """Words → caption phrases [[text, start, end], ...]. Explicit ranges win; else split on
    sentence punctuation, long pauses, or too many words."""
    rep = cap.get('replace', {})
    toks = []
    i = 0
    merges = {m[0]: m for m in cap.get('merge', [])}
    while i < len(words):
        w = words[i]
        if i in merges:
            a, b, txt = merges[i]
            toks.append([txt, words[a]['start'], words[b]['end']])
            i = b + 1
            continue
        txt = rep.get(str(i), rep.get(w['text'], w['text']))
        if txt != '':
            toks.append([txt, w['start'], w['end']])
        i += 1
    if cap.get('phrases'):
        return [toks[a:b + 1] for a, b in cap['phrases']]
    maxw, gap = cap.get('maxWords', 9), cap.get('pause', 1.6)
    out, cur = [], []
    for j, tk in enumerate(toks):
        cur.append(tk)
        nxt = toks[j + 1] if j + 1 < len(toks) else None
        if (re.search(r'[.?!؟]$', tk[0]) or len(cur) >= maxw or nxt is None or nxt[1] - tk[2] > gap):
            out.append(cur)
            cur = []
    return out


def prepare_media(key, path, mdir):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v'):
        # WebM VP9: the open-source Chromium used for rendering cannot decode H.264.
        dst = os.path.join(mdir, key + '.webm')
        run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-vf', "scale='if(gt(iw,ih),min(1920,iw),-2)':'if(gt(iw,ih),-2,min(1920,ih))'",
             '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '36', '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1', '-an', dst])
        return dst, 'video/webm'
    if ext in ('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.opus', '.flac', '.webm'):
        dst = os.path.join(mdir, key + '.mp3')
        run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-vn', '-c:a', 'libmp3lame', '-b:a', '192k', dst])
        return dst, 'audio/mpeg'
    if ext == '.svg':
        dst = os.path.join(mdir, key + '.svg')
        shutil.copyfile(path, dst)
        return dst, 'image/svg+xml'
    keep_alpha = ext in ('.png', '.webp')
    dst = os.path.join(mdir, key + ('.png' if keep_alpha else '.jpg'))
    run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-vf', "scale='min(2160,iw)':-2", '-frames:v', '1']
        + ([] if keep_alpha else ['-q:v', '3']) + [dst])
    return dst, 'image/png' if keep_alpha else 'image/jpeg'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('storyboard')
    ap.add_argument('--out', required=True)
    ap.add_argument('--sidecar', action='store_true', help='reference media files instead of embedding them')
    a = ap.parse_args()

    sb_path = os.path.abspath(a.storyboard)
    base = os.path.dirname(sb_path)
    sb = json.load(open(sb_path, encoding='utf-8'))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    out = os.path.abspath(a.out)
    mdir = os.path.join(out, 'media')
    os.makedirs(mdir, exist_ok=True)
    slug = sb.get('slug') or re.sub(r'[^a-z0-9]+', '-', sb.get('title', 'video').lower()).strip('-')

    if sb.get('size'):
        W, H = sb['size']
    else:
        W, H = FORMATS[sb.get('format', '9:16')]

    media_src = dict(sb.get('media', {}))
    cfg = {'width': W, 'height': H, 'scenes': sb['scenes'], 'brand': sb.get('brand', True),
           'brandSpans': sb.get('brandSpans'), 'wave': sb.get('wave', True), 'poster': sb.get('poster')}
    render = {'width': W, 'height': H, 'tracks': []}

    voice = sb.get('voice')
    if voice:
        vpath = rel(voice if isinstance(voice, str) else voice['src'])
        media_src['__voice'] = vpath
        vdur = probe_duration(vpath)
        cfg['audio'] = {'src': '__voice', 'duration': vdur}
        cfg['env'] = envelope(vpath)
        render['tracks'].append({'file': vpath, 'start': 0, 'volume': (voice.get('volume', 1.0) if isinstance(voice, dict) else 1.0)})

    cap = sb.get('captions') or {}
    if cap.get('words') and cap.get('enabled', True):
        cfg['captions'] = {'phrases': make_phrases(load_words(rel(cap['words'])), cap), 'rtl': cap.get('rtl', False)}

    for tr in sb.get('audioMix', []):
        f = rel(media_src.get(tr['src'], tr['src']))
        render['tracks'].append({'file': f, 'start': tr.get('start', 0), 'from': tr.get('from', 0),
                                 'duration': tr.get('duration'), 'volume': tr.get('volume', 1.0)})
    if sb.get('music'):
        m = sb['music']
        render['tracks'].append({'file': rel(m['src']), 'start': m.get('start', 0), 'from': m.get('from', 0),
                                 'volume': m.get('volume', 0.12), 'fadeOut': m.get('fadeOut', 2.0), 'music': True})

    dur = sb.get('duration') or round(max(s['end'] for s in sb['scenes']) + 1.0, 2)
    cfg['duration'] = dur
    render['duration'] = dur

    prepared, total = {}, 0
    for key, p in media_src.items():
        dst, mime = prepare_media(key, rel(p), mdir)
        prepared[key] = (dst, mime)
        total += os.path.getsize(dst)
    sidecar = a.sidecar or total * 4 / 3 > EMBED_LIMIT
    media = {}
    for key, (dst, mime) in prepared.items():
        if sidecar:
            media[key] = 'media/' + os.path.basename(dst)
        else:
            media[key] = 'data:%s;base64,%s' % (mime, base64.b64encode(open(dst, 'rb').read()).decode())

    js = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
    page = open(TEMPLATE, encoding='utf-8').read()
    page = page.replace('__TITLE__', sb.get('title', 'Vidéo BitEye').replace('<', '&lt;'))
    page = page.replace('/*__CONFIG__*/null', js(cfg)).replace('/*__MEDIA__*/{}', js(media))

    html = os.path.join(out, slug + '.html')
    local = os.path.join(out, slug + '.local.html')
    open(html, 'w', encoding='utf-8').write(page)
    open(local, 'w', encoding='utf-8').write(
        '<!doctype html>\n<html lang="%s"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>\n%s\n</body></html>\n'
        % (sb.get('lang', 'fr'), page))
    json.dump(render, open(os.path.join(out, slug + '.render.json'), 'w'), indent=1)
    print(json.dumps({'html': html, 'local': local, 'size_mb': round(os.path.getsize(html) / 1e6, 2),
                      'sidecar_media': sidecar, 'format': [W, H], 'duration': dur,
                      'phrases': len(cfg.get('captions', {}).get('phrases', []))}, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
