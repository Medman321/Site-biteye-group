#!/usr/bin/env python3
"""Alignement sujet détouré / plaque AVANT tout rendu (remplace check_align.py, offset_scan.py, frame_map.py, align_tool.py).

Pour chaque calque `subject` d'un storyboard à calques (`scenes[].layers[]`, kinds `video` et `subject`, champs start/end/from/hold/on),
reproduit le calcul de position du moteur (index = floor((t - start) * 30)), cherche le décalage d'images (-3..+3) qui minimise
l'écart sujet/plaque sur le haut du cadre (tête), et signale :
  - le `start` corrigé si le décalage optimal n'est pas 0 (cause du « visage coupé » de la V2 : z4 détouré 1 s trop tôt) ;
  - les images dont l'écart dépasse --max-err (sur 255) ;
  - avec --info-gate : saut de `head_top` > 25 px entre deux images consécutives dans <sujet>_info.json (alpha qui perd le haut du crâne).
Code de sortie 1 si un défaut est trouvé : ne lance alors NI le rendu final NI le contrôle croisé.

Usage : align_check.py <dossier_prod_avec_storyboard.json> [--subjects z1 z2] [--max-err 3] [--zone 340] [--info-gate] [--json sortie.json]
Coût : quelques secondes, aucun jeton de modèle au-delà de la lecture de la sortie (≤ 1 ligne par sujet)."""
import argparse, json, math, subprocess, sys, os
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('prod'); ap.add_argument('--subjects', nargs='*', default=[])
ap.add_argument('--max-err', type=float, default=3.0); ap.add_argument('--zone', type=int, default=340, help='hauteur (px sur 480) de la zone comparée : la tête')
ap.add_argument('--info-gate', action='store_true'); ap.add_argument('--json')
a = ap.parse_args()
W, H = 270, 480

def dec(f, alpha=False):
    args = ['ffmpeg', '-v', 'error'] + (['-c:v', 'libvpx-vp9'] if alpha else []) + ['-i', f, '-vf', f'scale={W}:{H}', '-f', 'rawvideo',
            '-pix_fmt', 'rgba' if alpha else 'rgb24', '-']
    raw = subprocess.run(args, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 4 if alpha else 3).astype(np.float32)

sb = json.load(open(os.path.join(a.prod, 'storyboard.json'))); med = sb['media']; cache = {}; report = []; failed = False
for sc in sb['scenes']:
    lay = [l for l in sc.get('layers', []) if l['kind'] in ('video', 'subject')]
    plates = [l for l in lay if l['kind'] == 'video']
    for s in [l for l in lay if l['kind'] == 'subject' and (not a.subjects or l['src'] in a.subjects)]:
        S = dec(med[s['src']], alpha=True); best = None
        for o in range(-3, 4):
            errs = []; n0 = 0 if s.get('hold') else math.floor(s['start'] * 30) + 1
            for n in range(n0, math.floor(s['end'] * 30 + 1e-9) + 1):
                t = n / 30; j = int(math.floor((s.get('from', 0) + max(0, t - s['start'])) * 30 + 1e-9)) + o
                if not 0 <= j < len(S): continue
                act = [x for x in plates if (x.get('on', x['start']) if x.get('hold') else x['start']) - 1e-9 <= t <= x.get('end', 1e9)]
                if not act: continue
                pl = act[-1]
                F = cache[pl['src']] if pl['src'] in cache else cache.setdefault(pl['src'], dec(med[pl['src']]))
                i = min(int(math.floor((pl.get('from', 0) + max(0, t - pl['start'])) * 30 + 1e-9)), len(F) - 1)
                m = S[j, :a.zone, :, 3] > 250
                if m.any(): errs.append((round(t, 3), round(float(np.abs(F[i, :a.zone][m] - S[j, :a.zone, :, :3][m]).mean()), 2)))
            if not errs: continue
            e = np.array([x[1] for x in errs]); r = (float(np.median(e)), o, float(e.max()), errs)
            if best is None or r[0] < best[0]: best = r
        if best is None: print(s['src'], sc['id'], 'AUCUNE image comparable (plage hors sujet ou plaque absente)'); failed = True; continue
        med_, o, mx, errs = best; bad = [x for x in errs if x[1] > a.max_err]
        issues = []
        if o != 0: issues.append('décalage %+d img -> start %.4f' % (o, s['start'] - o / 30))
        if bad: issues.append('%d images > %.1f (ex. %s)' % (len(bad), a.max_err, bad[:3]))
        if a.info_gate:
            ip = med[s['src']].replace('.webm', '_info.json')
            if os.path.exists(ip):
                ht = [f['head_top'] for f in json.load(open(ip))['per_frame']]
                jumps = [k for k in range(1, len(ht)) if abs(ht[k] - ht[k - 1]) > 25]
                if jumps: issues.append('head_top saute > 25 px aux images %s' % jumps[:5])
        failed |= bool(issues)
        report.append({'subject': s['src'], 'scene': sc['id'], 'offset': o, 'median': med_, 'max': mx, 'issues': issues})
        print('%-6s %-10s écart médian %.2f max %.2f | %s' % (s['src'], sc['id'], med_, mx, ' ; '.join(issues) or 'OK'))
if a.info_gate:   # crâne plafonné : la médiane de head_top égale son minimum et se répète sur >= 3 sujets (V2 : 220 px sur z1..z4, zA..zF avant correction ; 186-202 après)
    meds = {}
    for l in [l for sc in sb['scenes'] for l in sc.get('layers', []) if l['kind'] == 'subject']:
        ip = med[l['src']].replace('.webm', '_info.json')
        if os.path.exists(ip):
            d = json.load(open(ip)); meds[l['src']] = (d['head_top_med'], d['head_top_range'][0])
    for v in {m for m, lo in meds.values() if m == lo}:
        who = sorted(k for k, (m, lo) in meds.items() if m == lo == v)
        if len(who) >= 3: print('ALERTE head_top plafonné à %d px sur %s : le haut du crâne est coupé par la zone de détourage' % (v, who)); failed = True
if a.json: json.dump(report, open(a.json, 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if failed else 0)
