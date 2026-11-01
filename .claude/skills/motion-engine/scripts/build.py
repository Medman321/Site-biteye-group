#!/usr/bin/env python3
"""Build a BitEye motion video page from a storyboard.json.

Usage: python3 -I build.py STORYBOARD.json --out OUT_DIR [--sidecar]

Writes, in OUT_DIR:
  <slug>.html         page to publish as an Artifact (no <!doctype>, the publisher wraps it)
  <slug>.local.html   same page as a standalone document (open in a browser, or render to MP4)
  <slug>.render.json  what render.js needs: size, duration, audio tracks to mix, render scale
  <slug>.cues.json    V3: times of each transition (start, cut, end) for the sound designer;
                      V4: plus one line per block that can carry a sound (family, time, estimated x)
  <slug>.srt          V4: subtitles file (one entry per phrase, ≤ 7 words, ≤ 2 lines of ≤ 36 characters), when captions.words is set
  serie.<date>.json   V4: frozen copy of the series file named by `extends`
  media/              prepared media (always; also referenced by the page in --sidecar mode)

V4 also checks the commentCta blocks (refuses the build when the reply text, the 9:16 format or `safe` is missing).

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
                       ('rgba(242,239,232', 'rgba(234,238,241'), ('rgba(10,18,13', 'rgba(1,26,41'), ('rgba(5,9,7', 'rgba(0,12,20'),
                       ('#13241A', '#0A2F47')],
          'temoignage': [('#0F1A14', '#022539'), ('#0A120D', '#011A29'), ('#C4EF4E', '#EEBC5C'), ('#c4ef4e', '#eebc5c'),
                       ('rgba(196,239,78', 'rgba(238,188,92'), ('#2F6A1F', '#8A5A1E'), ('#F2EFE8', '#F6EFE3'),
                       ('rgba(242,239,232', 'rgba(246,239,227'), ('rgba(10,18,13', 'rgba(2,22,34'), ('rgba(5,9,7', 'rgba(0,10,16'),
                       ('#13241A', '#0A2F47')]}
# V4 : options d'en-tête transmises telles quelles à la page.
HEADER_KEYS = ('grain', 'handheld', 'flashes', 'safe', 'accents', 'plainBg', 'glowColor', 'capStyle', 'capPlain', 'capMoves', 'capHide',
               'brandTop', 'brandCompact', 'outDur', 'safeZone', 'safeZones', 'holdPush', 'premium')
# V4 : clés qu'une série (`extends`) peut fixer ; la valeur du storyboard gagne toujours.
SERIES_KEYS = ('theme', 'format', 'lang', 'captions', 'safe', 'safeZone', 'safeZones', 'grain', 'handheld', 'outDur', 'holdPush', 'premium',
               'accents', 'plainBg', 'glowColor', 'capStyle', 'brand', 'brandTop', 'wave', 'cta', 'motCode', 'fonts')


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


def caption_tokens(words, cap):
    """Words after `replace` and `merge` → [[text, start, end], ...]."""
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
    return toks


# V4 (B-11) : sous-titres courts. Mots « faibles » qui ne terminent jamais un bloc (français ; darija translittérée à compléter).
WEAK = set('le la les l un une des du de d au aux à a en et ou mais donc or ni car que qu qui dont où ce cet cette ces mon ma mes ton ta tes son sa ses '
           'notre nos votre vos leur leurs je j tu il elle on nous vous ils elles me m te t se s y ne n pas plus très sur sous dans par pour avec sans '
           'chez vers entre comme si est sont'.split())
WEAK_DZ = set('w f b l men m3a 3la fi li lli ana nta nti howa hiya ya wach bach kima ki ta3 dyal dial'.split())


def short_blocks(toks, cap):
    """Coupe optimale (programmation dynamique) d'une suite de mots en blocs de 1 à 3 mots, ≤ 16 signes, sans couper
    à travers une ponctuation finale ni une pause > 0,35 s ; un bloc ne finit jamais sur un mot faible ; un mot seul ou une paire
    coûtent plus qu'un bloc de trois. Idée et liste de mots faibles d'après le pack video-agent-skills (MIT), code réécrit."""
    maxw, maxc, gap = cap.get('shortWords', 3), cap.get('shortChars', 16), cap.get('shortPause', .35)
    weak = WEAK | WEAK_DZ | set(x.lower() for x in cap.get('weak', []))
    norm = lambda s: re.sub(r"[^\w’'-]", '', s.lower()).replace('’', "'").split("'")[-1] or s.lower()
    segs, cur = [], []
    for j, tk in enumerate(toks):
        cur.append(tk)
        nxt = toks[j + 1] if j + 1 < len(toks) else None
        if nxt is None or re.search(r'[.?!؟,;:…]$', tk[0]) or nxt[1] - tk[2] > gap:
            segs.append(cur)
            cur = []
    out = []
    for seg in segs:
        n = len(seg)
        best = [0.0] + [math.inf] * n
        back = [0] * (n + 1)
        for j in range(1, n + 1):
            for k in range(1, maxw + 1):
                i = j - k
                if i < 0:
                    break
                blk = seg[i:j]
                chars = len(' '.join(x[0] for x in blk))
                if chars > maxc and k > 1:
                    continue
                cost = {1: 3.0, 2: 1.2, 3: 0.0}.get(k, 0.0) + max(0, chars - maxc) * .5
                if j < n and norm(blk[-1][0]) in weak:
                    cost += 6.0
                if best[i] + cost < best[j]:
                    best[j], back[j] = best[i] + cost, i
        cuts, j = [], n
        while j > 0:
            cuts.append((back[j], j))
            j = back[j]
        out += [seg[a:b] for a, b in reversed(cuts)]
    return out


def make_phrases(words, cap):
    """Words → caption phrases [[text, start, end], ...]. Explicit ranges win; else split on
    sentence punctuation, long pauses, or too many words."""
    if cap.get('short') and not cap.get('phrases'):
        return short_blocks(caption_tokens(words, cap), cap)
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
               'maskReveal': (.8, 0., 'scene'), 'matchCut': (.6, 0., 'media'), 'morph': (.6, 0., 'scene')}
TR_SOUND = {'zoomPunch': 'souffle court (whoosh) de start à cut, petit impact sur cut',
            'whip': 'whoosh 0,25 s centré sur cut',
            'zoomThrough': 'montée (riser) de start à cut, impact ou souffle sur cut',
            'maskReveal': 'nappe ou scintillement qui gonfle de start à end',
            'matchCut': 'coupe sèche : accent bref (tick, kick) sur cut',
            'morph': 'L-cut + souffle court de start à end'}


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
            raise SystemExit('transition : type inconnu %r (zoomPunch, zoomThrough, maskReveal, whip, matchCut, morph)' % (typ,))
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


def srt_time(s):
    ms = int(round(max(0, s) * 1000))
    return '%02d:%02d:%02d,%03d' % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def srt_wrap(words, width=36):
    lines, cur = [], ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return lines + ([cur] if cur else [])


def srt_entries(phrases, maxw=7, width=36, maxlines=2):
    """V4 (B-19) : une entrée par phrase de sous-titre, ≤ 7 mots et ≤ 2 lignes de ≤ 36 signes ; sinon coupée à la ponctuation
    ou à la plus longue pause, au plus près du milieu."""
    def fits(tk):
        return len(tk) <= maxw and len(srt_wrap([x[0] for x in tk], width)) <= maxlines

    def split(tk):
        if len(tk) < 2 or fits(tk):
            return [tk]
        n, best, cut = len(tk), None, 1
        for k in range(1, n):
            score = abs(k - n / 2) - (3 if re.search(r'[.?!؟,;:…]$', tk[k - 1][0]) else 0) - min(3, (tk[k][1] - tk[k - 1][2]) * 6)
            if best is None or score < best:
                best, cut = score, k
        return split(tk[:cut]) + split(tk[cut:])
    out = []
    for ph in phrases:
        out += split(ph)
    return out


def write_srt(path, phrases):
    with open(path, 'w', encoding='utf-8') as f:
        for i, tk in enumerate(srt_entries(phrases), 1):
            f.write('%d\n%s --> %s\n%s\n\n' % (i, srt_time(tk[0][1]), srt_time(tk[-1][2]), '\n'.join(srt_wrap([x[0] for x in tk]))))


INVISIBLE = re.compile('[ ­​-‏‪-‮⁠-⁤﻿]')


def norm_comment_cta(sb, W, H):
    """V4 : bloc commentCta. Contrôles (refus du build) et minutage τ partagé avec la page (b['tl']) et cues.json."""
    out = []
    for si, sc in enumerate(sb['scenes']):
        for bi, b in enumerate(sc.get('blocks', [])):
            if b.get('type') != 'commentCta':
                continue
            where = 'commentCta (scène %d, bloc %d)' % (si, bi)
            code = b.get('code', b.get('motCode'))
            if not code or not str(code).strip():
                raise SystemExit(where + ' : « code » (mot-code du brief) obligatoire')
            code = str(code)
            if INVISIBLE.search(code) or code != code.strip():
                raise SystemExit(where + ' : le mot-code contient un caractère invisible ou des espaces en bord : il doit être recopiable tel quel')
            variant = b.get('variant', b.get('plateforme', 'instagram'))
            if variant not in ('instagram', 'tiktok', 'sheet'):
                raise SystemExit(where + ' : variant %r inconnu (instagram, tiktok, sheet)' % (variant,))
            if variant == 'instagram' and not str(b.get('reply') or '').strip():
                raise SystemExit(where + ' : « reply » obligatoire en variante instagram : texte EXACT de la réponse automatique réglée par le demandeur, jamais inventé')
            if not (H > W and abs(H / W - 16 / 9) < .02):
                raise SystemExit(where + ' : bloc réservé au 9:16 (sans objet en 4:5, 1:1 et 16:9)')
            if not sb.get('safe'):
                raise SystemExit(where + ' : « safe »: true obligatoire (zones sûres 9:16)')
            dur = float(b.get('dur', 3.0 if variant == 'tiktok' else 3.5))
            if not 3 <= dur <= 4:
                raise SystemExit(where + ' : dur = %s s hors de 3 à 4 s' % dur)
            at = float(b.get('at', sc['start']))
            type0, cps = .55, .05
            tap_pub = max(1.25, type0 + cps * (len(code) - 1) + .2)
            post = tap_pub + .05
            tl = {'dur': dur, 'tapField': .4, 'type0': type0, 'cps': cps, 'tapPub': round(tap_pub, 3), 'post': round(post, 3),
                  'heart': round(post + .2, 3), 'ban': round(post + .8, 3), 'exit': round(dur - .3, 3)}
            land = {'instagram': .4, 'tiktok': .3, 'sheet': 0}[variant]
            if tl['ban'] + land + .3 > tl['exit'] + 1e-6 and variant != 'sheet':
                raise SystemExit(where + ' : mot-code trop long (%d signes) pour %s s : raccourcir le code ou allonger dur' % (len(code), dur))
            if sc['end'] + .4 < at + dur - .05:
                raise SystemExit(where + ' : la scène se termine (%.2f s) avant la fin du bloc (%.2f s)' % (sc['end'], at + dur))
            b.update(type='commentCta', at=round(at, 3), code=code, variant=variant, tl=tl, count=int(b.get('count', 12)),
                     brand=b.get('brand', 'BitEye'), pseudo=b.get('pseudo', '@biteye_logiciels'), lang=b.get('lang', 'fr'))
            out.append((si, bi, b))
    return out


# V4 (D-14) : famille de son proposée par type de bloc (sound designer ; niveaux dans audio-studio/references/palette-evenements.md).
SFX_FAMILY = {'image': 'pose', 'polaroid': 'pose', 'cards': 'pose', 'gallery': 'pose', 'headline': 'pop', 'chip': 'pop', 'chips': 'pop',
              'badges': 'pop', 'lowerthird': 'pop', 'sticker': 'pop', 'checklist': 'cloche', 'cta': 'cloche', 'stats': 'compteur',
              'typewriter': 'saisie', 'commentCta': 'saisie', 'pointer': 'tap', 'letters': 'pop'}


def block_cues(sb, W, H):
    cues = []
    for si, sc in enumerate(sb['scenes']):
        blocks = sc.get('blocks', [])
        for bi, b in enumerate(blocks):
            if b.get('shown') and 'at' not in b:
                continue   # déjà à l'écran à t = 0 : pas de son d'entrée
            at = b.get('at', sc['start'] + .15 + bi * .2)
            x = W / 2
            if sc.get('split'):
                x = W * (.28 if bi < sc['split'] else .72)
            if isinstance(b.get('pos'), dict) and b['pos'].get('left') is not None:
                x = b['pos']['left'] + 200
            base = {'kind': 'bloc', 'bloc': b.get('id') or '%d.%d' % (si, bi), 'scene': sc.get('id', si), 'type': b.get('type'), 'x': round(x)}
            fam = SFX_FAMILY.get(b.get('type'))
            t = b.get('type')
            if t == 'commentCta':
                T, a = b['tl'], b['at']
                ev = [('tap', a + T['tapField'] + .04), ('tap', a + T['tapPub'] + .04), ('pop', a + T['post'] + .04), ('tap', a + T['heart'] + .04)]
                ev += [('tic', a + T['type0'] + i * T['cps']) for i in range(len(b['code']))]
                if b['variant'] == 'instagram':
                    ev += [('cloche', a + T['ban'] + .1), ('cloche-quinte', a + T['ban'] + .22)]
                elif b['variant'] == 'tiktok':
                    ev += [('pop', a + T['ban'] + .04)]
                for f, tt in sorted(ev, key=lambda e: e[1]):
                    cues.append(dict(base, famille=f, at=round(tt, 3), son='tic doux 0,03 s' if f == 'tic' else None))
                continue
            if t == 'pointer':
                for q in b.get('press', []):
                    tt = q if isinstance(q, (int, float)) else (q[0] if isinstance(q, list) else q.get('t'))
                    cues.append(dict(base, famille='tap', at=round(tt + .04, 3)))
                continue
            if t in ('stats',):
                for i, it in enumerate(b.get('items', [])):
                    a0 = it.get('at', at + i * .35) + .1
                    expo = (it.get('ease') or b.get('ease')) == 'outExpo'
                    d = it.get('dur', b.get('dur', .9 if expo else 1.4))
                    end = it.get('endAt', b.get('endAt', a0 + d))
                    cues.append(dict(base, famille='compteur', at=round(max(a0, end - d), 3), end=round(end, 3)))
                    if sc['end'] - end < 1:
                        cues[-1]['alerte'] = 'valeur finale tenue %.2f s (< 1 s)' % (sc['end'] - end)
                continue
            if fam:
                cues.append(dict(base, famille=fam, at=round(at, 3)))
            if t == 'app' and b.get('kpis'):
                expo = b.get('ease') == 'outExpo'
                a0 = b.get('kpisAt', at + .9) + (.02 if expo else 0)
                d = b.get('dur', .9 if expo else 1.4)
                end = b.get('endAt', a0 + d)
                cues.append(dict(base, famille='compteur', at=round(max(a0, end - d), 3), end=round(end, 3), detail='kpis'))
            for r in b.get('rows', []) if t == 'schedule' else []:
                s = r.get('statusAt') if isinstance(r, dict) else (r[4].get('statusAt') if len(r) > 4 and isinstance(r[4], dict) else None)
                if s is not None:
                    cues.append(dict(base, famille='cloche', at=round(s, 3), detail='statut'))
            for it in b.get('items', []) if t == 'phone' else []:
                if isinstance(it, dict) and it.get('statusAt') is not None:
                    cues.append(dict(base, famille='cloche', at=round(it['statusAt'], 3), detail='statut'))
    for c in cues:
        if c.get('son') is None:
            c.pop('son', None)
    return sorted(cues, key=lambda c: c['at'])


def apply_series(sb, sb_path, out):
    """V4 (B-26) : `extends: "serie.json"` : la série passe sous le storyboard (la valeur du storyboard gagne) ; copie datée figée
    `serie.<date>.json` dans le dossier de sortie (une retouche rejoue cette copie, pas la série courante)."""
    ext = sb.get('extends')
    if not ext:
        return sb, None
    p = ext if os.path.isabs(ext) else os.path.join(os.path.dirname(sb_path), ext)
    base = json.load(open(p, encoding='utf-8'))
    merged = dict(sb)
    for k in SERIES_KEYS:
        if k in base:
            if isinstance(base[k], dict) and isinstance(sb.get(k), dict):
                merged[k] = dict(base[k], **sb[k])
            elif k not in sb:
                merged[k] = base[k]
    frozen = None
    if not re.search(r'\.\d{4}-\d\d-\d\d\.json$', p):
        import datetime
        frozen = os.path.join(out, '%s.%s.json' % (os.path.splitext(os.path.basename(p))[0], datetime.date.today().isoformat()))
        shutil.copyfile(p, frozen)
    return merged, frozen


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
    sb, frozen = apply_series(sb, sb_path, out)
    slug = sb.get('slug') or re.sub(r'[^a-z0-9]+', '-', sb.get('title', 'video').lower()).strip('-')

    if sb.get('size'):
        W, H = sb['size']
    else:
        W, H = FORMATS[sb.get('format', '9:16')]
    ccta = norm_comment_cta(sb, W, H)

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
    srt = None
    if cap.get('words') and cap.get('enabled', True):
        cap.setdefault('maxChars', 52 if W > H else 62)
        words = load_words(rel(cap['words']))
        cfg['captions'] = {'phrases': make_phrases(words, cap), 'rtl': cap.get('rtl', False),
                           'short': bool(cap.get('short')), 'accents': cap.get('accents', [])}
        # V4 (B-19) : fichier .srt (à joindre à la publication), toujours tiré du découpage normal des phrases
        srt = os.path.join(out, slug + '.srt')
        write_srt(srt, make_phrases(words, dict(cap, short=False)))

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
    for k in HEADER_KEYS:
        if k in sb: cfg[k] = sb[k]
    warns = list(twarn)
    if 0 in [round(f, 3) for f in sb.get('flashes', [])]:
        warns.append('flashes contient 0 : l\'image 0 (aperçu du fil, vignette) est blanche à 85 % ; préférer un flash à 0,1 s ou plus')

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
    # cues.json : transitions (V3) puis, V4, une ligne par bloc qui peut porter un son (famille proposée, instant, abscisse estimée)
    bcues = block_cues(sb, W, H)
    if transitions or bcues:
        json.dump([dict(t['cue'], n=i, type=t['type'], kind='transition') for i, t in enumerate(transitions)] + bcues,
                  open(os.path.join(out, slug + '.cues.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    warns += [c['bloc'] + ' : ' + c['alerte'] for c in bcues if c.get('alerte')]
    print(json.dumps({'html': html, 'local': local, 'size_mb': round(os.path.getsize(html) / 1e6, 2),
                      'sidecar_media': sidecar, 'format': [W, H], 'duration': dur,
                      'phrases': len(cfg.get('captions', {}).get('phrases', [])), 'renderScale': rscale,
                      'transitions': [[t['type'], t['at'], t['cut'], t['end']] for t in transitions],
                      'commentCta': [[si, bi, b['variant'], b['at'], b['tl']['dur']] for si, bi, b in ccta],
                      'srt': srt, 'serie': frozen, 'warnings': warns},
                     ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
