#!/usr/bin/env python3
"""Build a BitEye motion video page from a storyboard.json.

Usage: python3 -I build.py STORYBOARD.json --out OUT_DIR [--sidecar]

Writes, in OUT_DIR:
  <slug>.html         page to publish as an Artifact (no <!doctype>, the publisher wraps it)
  <slug>.local.html   same page as a standalone document (open in a browser, or render to MP4)
  <slug>.render.json  what render.js needs: size, duration, audio tracks to mix, render scale
  <slug>.cues.json    V3: times of each transition (start, cut, end) for the sound designer
  media/              prepared media (always; also referenced by the page in --sidecar mode)

Media paths in the storyboard are relative to the storyboard file.
Only ffmpeg/ffprobe are required (no Python packages).
"""
import argparse, base64, json, math, os, re, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'engine', 'template.html')
FORMATS = {'9:16': (1080, 1920), '16:9': (1920, 1080), '1:1': (1080, 1080), '4:5': (1080, 1350)}
EMBED_LIMIT = 14 * 1024 * 1024
# "officiel" = navy + turquoise of the BitEye eye logo (default). "v2" = forest + lime palette (site V2), on request.
THEMES = {'officiel': [('#0F1A14', '#022539'), ('#0A120D', '#011A29'), ('#C4EF4E', '#03DA9F'), ('#c4ef4e', '#03da9f'),
                       ('rgba(196,239,78', 'rgba(3,218,159'), ('#2F6A1F', '#027A5B'), ('#F2EFE8', '#EAEEF1'),
                       ('rgba(242,239,232', 'rgba(234,238,241'), ('rgba(10,18,13', 'rgba(1,26,41'), ('rgba(5,9,7', 'rgba(0,12,20')],
          'temoignage': [('#0F1A14', '#022539'), ('#0A120D', '#011A29'), ('#C4EF4E', '#EEBC5C'), ('#c4ef4e', '#eebc5c'),
                       ('rgba(196,239,78', 'rgba(238,188,92'), ('#2F6A1F', '#8A5A1E'), ('#F2EFE8', '#F6EFE3'),
                       ('rgba(242,239,232', 'rgba(246,239,227'), ('rgba(10,18,13', 'rgba(2,22,34'), ('rgba(5,9,7', 'rgba(0,10,16')]}


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
    maxw, gap = cap.get('maxWords', 12), cap.get('pause', 1.6)
    maxc = cap.get('maxChars', 62)  # ~2 lines in 9:16, ~1.5 lines in 16:9 at the default size
    out, cur = [], []
    for j, tk in enumerate(toks):
        cur.append(tk)
        nxt = toks[j + 1] if j + 1 < len(toks) else None
        if (re.search(r'[.?!؟]$', tk[0]) or len(cur) >= maxw or (nxt is not None and len(' '.join(x[0] for x in cur + [nxt])) > maxc) or nxt is None or nxt[1] - tk[2] > gap):
            out.append(cur)
            cur = []
    return out


# V3 transitions: default duration (s), share of the duration before the cut, what moves ("media" = plates and
# cut-out subject only, "scene" = the whole scene with its texts).
TR_DEFAULTS = {'zoomPunch': (8 / 30, .3, 'media'), 'whip': (8 / 30, .5, 'scene'), 'zoomThrough': (.9, .62, 'scene'),
               'maskReveal': (.8, 0., 'scene'), 'matchCut': (.6, 0., 'media')}
TR_SOUND = {'zoomPunch': 'souffle court (whoosh) de start à cut, petit impact sur cut',
            'whip': 'whoosh 0,25 s centré sur cut',
            'zoomThrough': 'montée (riser) de start à cut, impact ou souffle sur cut',
            'maskReveal': 'nappe ou scintillement qui gonfle de start à end',
            'matchCut': 'coupe sèche : accent bref (tick, kick) sur cut'}


def norm_transitions(sb, fps=30):
    """Scene-level `transition` (from the previous scene) and top-level `transitions` → one normalised list
    with explicit times (at = start of the move, cut = frame where the shot changes, end)."""
    scenes = sb['scenes']
    ids = {sc['id']: i for i, sc in enumerate(scenes) if sc.get('id') is not None}
    lids = {L['id']: i for i, sc in enumerate(scenes) for L in sc.get('layers', []) if L.get('id')}
    warns = []

    def sref(x):
        if isinstance(x, int) and 0 <= x < len(scenes):
            return x
        if x in ids:
            return ids[x]
        raise SystemExit('transition : scène inconnue %r' % (x,))

    raw = []
    for i, sc in enumerate(scenes):
        tr = sc.get('transition')
        if tr:
            if i == 0 and 'scene' not in tr:
                warns.append('scène 0 : transition ignorée (pas de plan avant)')
                continue
            raw.append(dict(tr, _a=i - 1, _b=i, _cut=sc['start']))
    raw += [dict(t) for t in sb.get('transitions', [])]
    out = []
    for n, T in enumerate(raw):
        typ = T.get('type')
        if typ not in TR_DEFAULTS:
            raise SystemExit('transition : type inconnu %r (zoomPunch, zoomThrough, maskReveal, whip, matchCut)' % (typ,))
        dur0, lead, mode = TR_DEFAULTS[typ]
        dur = float(T.get('dur', dur0))
        if 'scene' in T:   # inside one scene: two lists of layer ids, or nothing (a cut inside one plate)
            si = sref(T['scene'])
            if isinstance(T.get('a'), list) or isinstance(T.get('b'), list):
                a, b, same = {'scene': si, 'layers': T.get('a') or []}, {'scene': si, 'layers': T.get('b') or []}, False
                for lid in a['layers'] + b['layers']:
                    if lid not in lids:
                        warns.append('transition %d : calque %r introuvable' % (n, lid))
            else:
                a = b = {'scene': si}
                same = True
            cut0 = T.get('_cut')
        else:
            a, b, same = {'scene': sref(T.get('a', T.get('_a')))}, {'scene': sref(T.get('b', T.get('_b')))}, False
            cut0 = T.get('_cut', scenes[b['scene']]['start'])
        at, cut = T.get('at'), T.get('cut')
        if at is None and cut is None:
            if cut0 is None:
                raise SystemExit('transition %d (%s) : donner « at » ou « cut »' % (n, typ))
            cut = cut0
        if at is None:
            at = cut - lead * dur
        if cut is None:
            cut = at + lead * dur
        end = (cut + dur) if typ == 'matchCut' else (at + dur)
        if typ in ('zoomPunch', 'whip') and not 6 <= round(dur * fps) <= 10:
            warns.append('transition %d (%s) : %d images, conseillé 6 à 10' % (n, typ, round(dur * fps)))
        if typ == 'matchCut' and not (T.get('faceA') and T.get('faceB')):
            raise SystemExit('transition %d (matchCut) : faceA et faceB {x, y, s} requis' % n)
        e = {k: v for k, v in T.items() if not k.startswith('_') and k not in ('a', 'b', 'scene')}
        e.update(type=typ, at=round(at, 4), cut=round(cut, 4), end=round(end, 4), a=a, b=b, mode=T.get('target', mode))
        if same:
            e['same'] = True
        start = at
        if typ == 'matchCut' and T['faceA']['s'] < T['faceB']['s']:
            start = cut - T.get('pre', .25)
        e['cue'] = {'start': round(start, 3), 'cut': round(cut, 3), 'end': round(end, 3), 'son': TR_SOUND[typ]}
        out.append(e)
    out.sort(key=lambda e: e['at'])
    return out, warns


def generate_media(key, spec, mdir, base):
    """V3: test media generated by ffmpeg (no file in the public repo). spec = {"lavfi": graph, "duration": s,
    "alpha": bool, "image": bool}. Only lavfi sources: graphs that read files are refused."""
    graph = spec['lavfi']
    if re.search(r'(movie|file|filename|sendcmd|zmq)\s*=', graph):
        raise SystemExit('media %s : graphe lavfi qui lit un fichier refusé' % key)
    if spec.get('image'):
        dst = os.path.join(mdir, key + '.png')
        run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', graph, '-frames:v', '1', dst])
        return dst, 'image/png'
    dst = os.path.join(mdir, key + '.webm')
    alpha = spec.get('alpha', False)
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', graph, '-t', str(spec.get('duration', 4)),
         '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p' if alpha else 'yuv420p', '-b:v', '0', '-crf', str(spec.get('crf', 32)),
         '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1'] + (['-auto-alt-ref', '0'] if alpha else []) + ['-an', dst])
    return dst, 'video/webm'


def prepare_media(key, path, mdir, scale=1):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.webm':
        # V2 : WebM VP9 déjà prêt (plaque ambilight ou sujet détouré avec alpha yuva420p) : copié tel quel.
        dst = os.path.join(mdir, key + '.webm')
        shutil.copyfile(path, dst)
        return dst, 'video/webm'
    if ext in ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v'):
        # WebM VP9: the open-source Chromium used for rendering cannot decode H.264.
        # V3: with renderScale 2 (4K master) clips keep their native size up to 3840 px on the long side.
        lim = 1920 * scale
        dst = os.path.join(mdir, key + '.webm')
        run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-vf', "scale='if(gt(iw,ih),min(%d,iw),-2)':'if(gt(iw,ih),-2,min(%d,ih))'" % (lim, lim),
             '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '36' if scale < 2 else '30', '-deadline', 'realtime', '-cpu-used', '8', '-row-mt', '1', '-an', dst])
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
    run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-vf', "scale='min(%d,iw)':-2" % (2160 * scale), '-frames:v', '1']
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
    rscale = sb.get('renderScale', 1)
    render = {'width': W, 'height': H, 'tracks': [], 'scale': rscale}
    transitions, twarn = norm_transitions(sb)
    if transitions:
        cfg['transitions'] = transitions
        render['transitions'] = [t['cue'] for t in transitions]

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
        cap.setdefault('maxChars', 52 if W > H else 62)
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

    # The original BitEye eye logo is used whatever the palette (brand rule).
    theme = sb.get('theme', 'officiel')
    media_src['__logo'] = os.environ.get('BITEYE_LOGO') or os.path.join(HERE, '..', '..', 'biteye-brand', 'assets', 'logo-officiel.png')
    for k in ('grain', 'handheld', 'flashes', 'safe', 'accents', 'plainBg', 'glowColor', 'capStyle', 'capPlain', 'capMoves', 'capHide', 'brandTop', 'brandCompact'):
        if k in sb: cfg[k] = sb[k]

    prepared, total = {}, 0
    for key, p in media_src.items():
        if isinstance(p, dict) and 'lavfi' in p:
            dst, mime = generate_media(key, p, mdir, base)
        else:
            dst, mime = prepare_media(key, rel(p), mdir, max(1, int(rscale)))
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

    if theme in THEMES:
        for old, new in THEMES[theme]:
            page = page.replace(old, new)

    html = os.path.join(out, slug + '.html')
    local = os.path.join(out, slug + '.local.html')
    open(html, 'w', encoding='utf-8').write(page)
    open(local, 'w', encoding='utf-8').write(
        '<!doctype html>\n<html lang="%s"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>\n%s\n</body></html>\n'
        % (sb.get('lang', 'fr'), page))
    json.dump(render, open(os.path.join(out, slug + '.render.json'), 'w'), indent=1)
    if transitions:
        json.dump([dict(t['cue'], n=i, type=t['type']) for i, t in enumerate(transitions)],
                  open(os.path.join(out, slug + '.cues.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'html': html, 'local': local, 'size_mb': round(os.path.getsize(html) / 1e6, 2),
                      'sidecar_media': sidecar, 'format': [W, H], 'duration': dur,
                      'phrases': len(cfg.get('captions', {}).get('phrases', [])), 'renderScale': rscale,
                      'transitions': [[t['type'], t['at'], t['cut'], t['end']] for t in transitions], 'warnings': twarn},
                     ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
