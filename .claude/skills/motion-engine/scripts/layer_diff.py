#!/usr/bin/env python3
"""Deux contrôles d'images clés, chacun sur 2 ou 3 PNG de 540x960 (aucun rendu complet).

  effect : l'effet est-il visible, ni trop discret ni trop fort ?
      layer_diff.py effect SANS.png AVEC.png [--box x,y,w,h] [--thr 12] [--min 0.5] [--max 25]
      mesure le % de pixels qui changent quand on ajoute le calque (flou, anneau, parallaxe 2.5D). Échec si < --min (« invisible »,
      cas V2 : animations 2.5D rendues invisibles par les plafonds « subtil ») ou > --max (« trop marqué », cas V2 : flou).
  behind : le mot passe-t-il vraiment DERRIÈRE la tête ?
      layer_diff.py behind PLAQUE.png TEXTE.png FINAL.png --box x,y,w,h [--thr 24] [--min 0.08] [--max 0.85]
      PLAQUE = fond seul ; TEXTE = fond + texte, sujet masqué ; FINAL = tout. Rapport = pixels de texte recouverts par le sujet /
      pixels de texte dans la boîte (boîte = tête, d'après _info.json). Échec si < --min (le mot est devant ou à côté) ou > --max (mot invisible).
Code de sortie : 0 OK, 1 hors bornes, 2 mesure impossible (aucun texte dans la boîte).
Les trois PNG s'obtiennent avec render.js --stills --times T, en masquant le calque (option `--hide <kind>` du moteur, à ajouter)."""
import argparse, sys
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['effect', 'behind']); ap.add_argument('imgs', nargs='+')
ap.add_argument('--box'); ap.add_argument('--thr', type=float); ap.add_argument('--min', type=float); ap.add_argument('--max', type=float)
a = ap.parse_args()
L = lambda p: np.asarray(Image.open(p).convert('RGB'), np.int16)
imgs = [L(p) for p in a.imgs]
if len({i.shape for i in imgs}) != 1: sys.exit('images de tailles différentes')
H, W = imgs[0].shape[:2]
x, y, w, h = [int(v) for v in a.box.split(',')] if a.box else (0, 0, W, H)
crop = lambda i: i[y:y + h, x:x + w]
diff = lambda p, q, t: (np.abs(crop(p) - crop(q)).max(axis=2) > t)
if a.mode == 'effect':
    if len(imgs) != 2: sys.exit('effect : 2 images')
    thr = 12 if a.thr is None else a.thr; mn = 0.5 if a.min is None else a.min; mx = 25 if a.max is None else a.max
    pct = 100 * diff(imgs[0], imgs[1], thr).mean()
    ok = mn <= pct <= mx
    print('effect : %.2f %% des pixels changent (bornes %.2f à %.2f) -> %s' % (pct, mn, mx, 'OK' if ok else ('INVISIBLE' if pct < mn else 'TROP FORT')))
    sys.exit(0 if ok else 1)
if len(imgs) != 3: sys.exit('behind : 3 images (plaque, texte, final)')
thr = 24 if a.thr is None else a.thr; mn = 0.08 if a.min is None else a.min; mx = 0.85 if a.max is None else a.max
text = diff(imgs[0], imgs[1], thr)
if text.sum() < 50: print('behind : aucun texte dans la boîte'); sys.exit(2)
ratio = float((text & diff(imgs[1], imgs[2], thr)).sum() / text.sum())
ok = mn <= ratio <= mx
print('behind : %.0f %% du texte de la boîte est recouvert par le sujet (bornes %.0f à %.0f %%) -> %s' %
      (100 * ratio, 100 * mn, 100 * mx, 'OK' if ok else ('MOT PAS DERRIÈRE LA TÊTE' if ratio < mn else 'MOT QUASI INVISIBLE')))
sys.exit(0 if ok else 1)
