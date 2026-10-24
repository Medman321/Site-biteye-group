#!/usr/bin/env python3
"""Plans de profondeur d'une photo : personnes / AP1 (mobilier proche) / AP2 (mur, fond comblé), puis essai d'un mot inséré
avec une parallaxe 9:16 et mesure de la part cachée du mot (layer_diff.py behind + mesure directe sur les masques).

Profondeur : Depth Anything V2 Small, licence Apache-2.0, export ONNX des releases GitHub fabio-sim/Depth-Anything-ONNX
(téléchargé une fois dans ~/.cache/biteye-depth/, taille et SHA256 vérifiés ; jamais versionné). Matte : u2net_human_seg (rembg).
Comblement du fond : cv2.inpaint TELEA + reflet horizontal du mur voisin + grain mesuré. AUCUNE IA générative (photos de clients).

Usage :
  depth_layers.py PHOTO --out DOSSIER [--plan fond|personne] [--word MOT] [--color "#964D61"] [--amplitude moyenne]
                  [--exclude x,y,w,h ...] [--erase x,y,w,h ...] [--blur-poly x1,y1,x2,y2,...] [--x0 N] [--cx N --cy N]
                  [--font police.ttf] [--preview] [--compare-detourage]
  --plan fond      : mot entre AP1 et AP2 (caché par les personnes ET le mobilier) ;
  --plan personne  : mot devant AP1, derrière les personnes (quand un panneau ou un meuble est devant le mur à hauteur de tête).
  --amplitude      : faible (12 px/s) | moyenne (20 px/s, recommandée) | forte (30 px/s) | tous | nombre en px/s ; plan de --duree s (3).
  --exclude        : boîtes retirées de la matte (faux positifs : calculatrice, sac…) ; --erase : boîtes comblées dans l'image (filigrane).
  --blur-poly      : polygone d'un écran à rendre illisible (flou sigma 18 + grain) sur AP2 seulement : aucun visage flouté.
Sans --word : seulement les calques et calques.json.
Sorties : calque_personnes.png, calque_AP1.png (RGBA), calque_AP2.png (RGB comblé), profondeur16.png, profondeur_viz.jpg,
          calques.json (réglages, placement du mot, mesures, temps), apercu_<amplitude>_debut|fin.jpg, apercu_<amplitude>_3s.mp4 (--preview).
Dans le moteur : calques à la taille de la photo, placés comme la plaque (cover 9:16 : échelle 1920/H, décalage -x0*échelle) ;
mouvement : AP2 fixe, mot = facteur_mot x amplitude, personnes ET AP1 ensemble = 1 x amplitude (jamais séparés).
Code de sortie : 0 ; 1 si une mesure du mot sort des bornes 25-40 % ou si une lettre de bord est cachée à plus de 50 %."""
import argparse, hashlib, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

MODEL_URL = 'https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits_dynamic.onnx'
MODEL_SIZE = 99092268
MODEL_SHA = '46c4e8eeda3a27f34701831b6a2ec7753d7b38779b215acb5633424703deed8f'
MODEL_LICENSE = 'Depth Anything V2 Small, Apache-2.0'
CW, CH = 1080, 1920
AMPS = {'faible': 12, 'moyenne': 20, 'forte': 30}  # px/s d'écart personne/mur (seuils DA 12 à 30 px/s)
LAYER_DIFF = Path(__file__).resolve().parents[2] / 'motion-engine' / 'scripts' / 'layer_diff.py'


def model_path():
    d = Path(os.environ.get('BITEYE_DEPTH_CACHE', Path.home() / '.cache' / 'biteye-depth')); d.mkdir(parents=True, exist_ok=True)
    p = d / 'depth_anything_v2_vits_dynamic.onnx'
    if p.exists() and p.stat().st_size == MODEL_SIZE:
        return p
    print('téléchargement du modèle de profondeur (%s, %.0f Mo)…' % (MODEL_LICENSE, MODEL_SIZE / 1e6), file=sys.stderr)
    tmp = p.with_suffix('.part'); h = hashlib.sha256()
    with urllib.request.urlopen(MODEL_URL, timeout=120) as r, open(tmp, 'wb') as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b); h.update(b)
    if tmp.stat().st_size != MODEL_SIZE or h.hexdigest() != MODEL_SHA:
        tmp.unlink(); sys.exit('modèle de profondeur : taille ou SHA256 inattendus, fichier supprimé')
    tmp.rename(p); return p


def boxes(lst):
    return [tuple(map(int, b.split(','))) for b in lst]


def guided(I, p, r, eps):
    m = lambda z: cv2.boxFilter(z, -1, (2 * r + 1, 2 * r + 1))
    mI, mp = m(I), m(p); a = (m(I * p) - mI * mp) / (m(I * I) - mI * mI + eps); b = mp - a * mI
    return m(a) * I + m(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('photo'); ap.add_argument('--out', required=True)
    ap.add_argument('--plan', choices=['fond', 'personne'], default='fond'); ap.add_argument('--word'); ap.add_argument('--color')
    ap.add_argument('--amplitude', default='moyenne'); ap.add_argument('--duree', type=float, default=3.0)
    ap.add_argument('--exclude', nargs='*', default=[]); ap.add_argument('--erase', nargs='*', default=[]); ap.add_argument('--blur-poly')
    ap.add_argument('--x0', type=int); ap.add_argument('--cx', type=int); ap.add_argument('--cy', type=int)
    ap.add_argument('--maxw', type=int, default=640, help='largeur maximale du mot (px de la toile 1080)')
    ap.add_argument('--fw', type=float, default=0.25, help='facteur de parallaxe du mot (0 = mur, 1 = premier plan)')
    ap.add_argument('--target', type=float, default=0.32); ap.add_argument('--t0', type=float, default=0.18); ap.add_argument('--t1', type=float, default=0.30)
    ap.add_argument('--font'); ap.add_argument('--depth-w', type=int, default=756); ap.add_argument('--threads', type=int, default=3)
    ap.add_argument('--preview', action='store_true'); ap.add_argument('--compare-detourage', action='store_true')
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True); T = {}; t_all = time.time()

    bgr = cv2.imread(a.photo)
    if bgr is None: sys.exit('photo illisible : ' + a.photo)
    H, W = bgr.shape[:2]
    er = np.zeros((H, W), np.uint8)
    for x, y, w, h in boxes(a.erase): er[y:y + h, x:x + w] = 255
    if er.any(): bgr = cv2.inpaint(bgr, er, 9, cv2.INPAINT_TELEA)

    # 1. profondeur (disparité relative, grand = proche)
    import onnxruntime as ort
    so = ort.SessionOptions(); so.intra_op_num_threads = a.threads
    sess = ort.InferenceSession(str(model_path()), so, providers=['CPUExecutionProvider'])
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    dw = a.depth_w // 14 * 14; dh = int(round(H / W * dw / 14)) * 14
    x = ((cv2.resize(rgb, (dw, dh), interpolation=cv2.INTER_CUBIC) - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).astype(np.float32).transpose(2, 0, 1)[None]
    t = time.time(); D = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]; T['profondeur_s'] = round(time.time() - t, 2)
    D = cv2.resize(D.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    lo, hi = np.percentile(D, 0.5), np.percentile(D, 99.5); D = np.clip((D - lo) / (hi - lo), 0, 1) + 0.01
    cv2.imwrite(str(out / 'profondeur16.png'), ((D - 0.01) * 65535).clip(0, 65535).astype(np.uint16))
    cv2.imwrite(str(out / 'profondeur_viz.jpg'), cv2.applyColorMap((np.log(D / 0.01) / np.log(101) * 255).astype(np.uint8), cv2.COLORMAP_INFERNO))

    # 2. matte personnes
    t = time.time()
    from rembg import new_session, remove
    mt = np.asarray(remove(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)), session=new_session('u2net_human_seg'), only_mask=True), np.float32) / 255
    T['matte_s'] = round(time.time() - t, 2)
    for x_, y_, w_, h_ in boxes(a.exclude) + boxes(a.erase): mt[y_:y_ + h_, x_:x_ + w_] = 0
    pm = cv2.morphologyEx((mt > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    ff = pm.copy(); cv2.floodFill(ff, np.zeros((H + 2, W + 2), np.uint8), (0, 0), 1); pm = pm | (ff == 0).astype(np.uint8)  # trous comblés
    n, lab, st, _ = cv2.connectedComponentsWithStats(pm, 8)
    for i in range(1, n):
        if st[i, 4] < 0.004 * H * W: pm[lab == i] = 0

    # 3. fenêtre 9:16 et plan du mur du fond (la disparité d'un plan est affine en x, y : ajustement robuste sur les pixels lointains)
    S = CH / H; ww = CW / S
    if a.x0 is None:
        xs_ = np.nonzero(pm.any(0))[0]; c_ = (xs_.min() + xs_.max()) / 2 if len(xs_) else W / 2
        a.x0 = int(np.clip(c_ - ww / 2, 0, max(W - ww, 0)))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); win = (xx >= a.x0) & (xx < a.x0 + ww)
    sel = (pm == 0) & win; sel &= D < np.percentile(D[sel], 35)
    for _ in range(4):
        A = np.c_[xx[sel], yy[sel], np.ones(sel.sum())]; c, *_ = np.linalg.lstsq(A, D[sel], rcond=None)
        P = c[0] * xx + c[1] * yy + c[2]; R = (D - P) / np.maximum(P, 1e-3)
        sel = (pm == 0) & win & (np.abs(R) < 0.10)
    occ = np.clip((R - a.t0) / (a.t1 - a.t0), 0, 1).astype(np.float32)
    occ = np.maximum(occ, cv2.erode(pm, np.ones((9, 9), np.uint8)).astype(np.float32))  # une personne est toujours devant le mur
    ob = (occ > 0.5).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(ob, 8); pd = cv2.dilate(pm, np.ones((15, 15), np.uint8))
    for i in range(1, n):  # éléments proches qui ne touchent ni le bas ni une personne (plafond, luminaires) -> AP2
        reg = lab == i
        if st[i, 1] + st[i, 3] < 0.5 * H and not (pd[reg] > 0).any(): occ[cv2.dilate(reg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0] = 0
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    occ = np.clip(guided(g, occ, 6, 2e-3), 0, 1); occ[occ < 0.03] = 0; occ[occ > 0.97] = 1
    ps = cv2.GaussianBlur(cv2.dilate(pm, np.ones((7, 7), np.uint8)).astype(np.float32), (0, 0), 2)
    a_pers, a_ap1 = occ * ps, occ * (1 - ps)

    # 4. AP2 comblé derrière tout ce qui est devant le mur
    t = time.time()
    hole = cv2.dilate((occ > 0.02).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0
    small = cv2.resize(bgr, (W // 2, H // 2), interpolation=cv2.INTER_AREA); hs = cv2.resize(hole.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
    fill = cv2.resize(cv2.inpaint(small, hs * 255, 6, cv2.INPAINT_TELEA), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    hp = bgr.astype(np.float32) - cv2.GaussianBlur(bgr.astype(np.float32), (0, 0), 1.5)
    sd = float(np.median(np.abs(hp[(~hole) & win])) * 1.4826)
    fill += np.random.default_rng(1).normal(0, sd, fill.shape)
    K = ~hole; idx = np.arange(W)[None].repeat(H, 0); rows = np.arange(H)[:, None].repeat(W, 1); band = 64; src = bgr.astype(np.float32)
    L_ = np.maximum.accumulate(np.where(K, idx, -1), axis=1); R_ = np.fliplr(np.minimum.accumulate(np.fliplr(np.where(K, idx, W)), axis=1))
    dl, dr = idx - L_, R_ - idx; xl = np.clip(L_ - dl, 0, W - 1); xr = np.clip(R_ + dr, 0, W - 1)
    okl = (L_ >= 0) & (dl <= band) & K[rows, xl]; okr = (R_ < W) & (dr <= band) & K[rows, xr]
    wl = okl * (1 - np.clip(dl / band, 0, 1)) + 1e-6; wr = okr * (1 - np.clip(dr / band, 0, 1)) + 1e-6
    mir = cv2.GaussianBlur((src[rows, xl] * wl[..., None] + src[rows, xr] * wr[..., None]) / (wl + wr)[..., None], (1, 5), 0)
    wm_ = cv2.GaussianBlur((np.clip(np.maximum(wl, wr) * 2, 0, 1) * (okl | okr)).astype(np.float32), (0, 0), 3)[..., None]
    fill = fill * (1 - wm_) + mir * wm_
    hf = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 1.5)[..., None]
    ap2 = (bgr * (1 - hf) + fill * hf).clip(0, 255).astype(np.uint8); shown = bgr
    if a.blur_poly:
        pts = np.array(list(map(int, a.blur_poly.split(','))), np.int32).reshape(-1, 2)
        pk = np.zeros((H, W), np.uint8); cv2.fillPoly(pk, [pts], 255); pk = cv2.GaussianBlur(pk.astype(np.float32), (0, 0), 2)[..., None] / 255
        bl = cv2.GaussianBlur(ap2.astype(np.float32), (0, 0), 18) + np.random.default_rng(2).normal(0, max(sd, 2), ap2.shape)
        ap2 = (ap2 * (1 - pk) + bl * pk).clip(0, 255).astype(np.uint8); shown = (bgr * (1 - pk) + bl * pk).clip(0, 255).astype(np.uint8)
    T['comblement_s'] = round(time.time() - t, 2)
    rgba = lambda im, al: np.dstack([im, (al * 255).astype(np.uint8)])
    cv2.imwrite(str(out / 'calque_personnes.png'), rgba(bgr, a_pers)); cv2.imwrite(str(out / 'calque_AP1.png'), rgba(bgr, a_ap1))
    cv2.imwrite(str(out / 'calque_AP2.png'), ap2)
    res = {'modele': MODEL_LICENSE, 'photo': os.path.basename(a.photo), 'taille': [W, H], 'x0': a.x0, 'echelle_9x16': round(S, 4),
           'plan': a.plan, 'seuils_residu': [a.t0, a.t1], 'grain_sd': round(sd, 2), 'temps': T,
           'mouvement': {'AP2': 0, 'mot': a.fw, 'personnes_et_AP1': 1}}
    if not a.word:
        T['total_s'] = round(time.time() - t_all, 2); json.dump(res, open(out / 'calques.json', 'w'), indent=1, ensure_ascii=False); return 0

    # 5. mot inséré, placement automatique (part cachée ~ target, lettres de bord <= 50 %), mesures aux 3 instants du plan
    def warp(img, dx):
        return cv2.warpAffine(img, np.float32([[S, 0, -a.x0 * S + dx], [0, S, 0]]), (CW, CH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fp = a.font
    if not fp:
        for f_ in ['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf']:
            if os.path.exists(f_): fp = f_; break
    size = 300
    while True:
        fnt = ImageFont.truetype(fp, size); bb = fnt.getbbox(a.word)
        if bb[2] - bb[0] <= a.maxw or size < 40: break
        size -= 6
    def word_mask(cx, cy, dx=0):
        im = Image.new('L', (CW, CH), 0); bb = fnt.getbbox(a.word)
        ox = cx - (bb[0] + bb[2]) / 2 + dx; oy = cy - (bb[1] + bb[3]) / 2; ImageDraw.Draw(im).text((ox, oy), a.word, font=fnt, fill=255)
        return np.asarray(im, np.float32) / 255, [ox + fnt.getlength(a.word[:i]) for i in range(len(a.word) + 1)], \
            (int(ox + bb[0]), int(oy + bb[1]), int(bb[2] - bb[0]), int(bb[3] - bb[1]))
    def occ_c(dx):
        o = np.clip(warp(np.dstack([a_pers, a_ap1, mt]), dx), 0, 1)
        return o if a.plan == 'fond' else np.dstack([o[..., 0], np.zeros_like(o[..., 0]), o[..., 2], o[..., 1]])
    def hidden(wmk, oc, xs):
        oa = (oc[..., 0] + oc[..., 1]) > 0.5; tot = wmk > 0.5; n_ = max(tot.sum(), 1)
        lets = [float((tot[:, int(xs[i]):int(xs[i + 1])] & oa[:, int(xs[i]):int(xs[i + 1])]).sum() / max(tot[:, int(xs[i]):int(xs[i + 1])].sum(), 1)) for i in range(len(xs) - 1)]
        return float((tot & oa).sum() / n_), float((tot & (oc[..., 0] > 0.5)).sum() / n_), lets
    oc0 = occ_c(0); wpx = fnt.getbbox(a.word)[2] - fnt.getbbox(a.word)[0]; best = None
    cxs = [a.cx] if a.cx else list(range(int(60 + wpx / 2), int(900 - wpx / 2) + 1, 20)) or [480]
    cys = [a.cy] if a.cy else range(380, 1320, 10)
    for cx in cxs:
        for cy in cys:
            wmk, xs, box = word_mask(cx, cy); h, hp_, lets = hidden(wmk, oc0, xs)
            if box[1] < 260 or lets[0] > 0.5 or lets[-1] > 0.5: continue
            sc = abs(h - a.target) + 0.0001 * (cy - 380)
            if best is None or sc < best[0]: best = (sc, cx, cy)
    if best is None: best = (0, cxs[0], list(cys)[0])
    CX, CY = best[1], best[2]
    wm0, _, _ = word_mask(CX, CY); lum = float(cv2.cvtColor(warp(ap2, 0), cv2.COLOR_BGR2GRAY)[wm0 > 0.5].mean())
    col = np.array([74, 42, 30], np.float32) if lum > 140 else np.array([220, 236, 244], np.float32)  # bleu nuit ou crème selon le fond
    if a.color: col = np.array([int(a.color[i:i + 2], 16) for i in (5, 3, 1)], np.float32)
    BG, IMG, SH = warp(ap2.astype(np.float32), 0), warp(shown.astype(np.float32), 0), warp(bgr.astype(np.float32), 0)
    def frame(A, u, det=False):
        dfg = A * u; wmk, xs, box = word_mask(CX, CY, A * a.fw * u); oc = occ_c(dfg); fg = warp(bgr.astype(np.float32), dfg)
        if det:  # comparaison : plaque = photo d'origine (la personne y reste), sujet = matte seule
            base = IMG.copy(); al = oc[..., 2:3]; oc = np.dstack([al[..., 0], np.zeros_like(al[..., 0])])
        else:
            base = BG.copy(); al = np.clip(oc[..., 0] + oc[..., 1], 0, 1)[..., None]
            if a.plan == 'personne': base = base * (1 - oc[..., 3:4]) + fg * oc[..., 3:4]
        text = base * (1 - wmk[..., None]) + col * wmk[..., None]
        sh = np.roll(cv2.GaussianBlur(al[..., 0], (0, 0), 14), (14, 10), (0, 1))[..., None] * 0.18  # ombre douce <= 0,20
        plaque = base * (1 - sh); text = text * (1 - sh); final = text * (1 - al) + fg * al
        return [z.clip(0, 255).astype(np.uint8) for z in (plaque, text, final)], hidden(wmk, oc, xs), box
    amp = a.amplitude
    levels = dict(AMPS) if amp == 'tous' else ({amp: AMPS[amp]} if amp in AMPS else {'%gpx_s' % float(amp): float(amp)})
    todo = [(k, v * a.duree, False) for k, v in levels.items()] + ([('detourage_seul', 20 * a.duree, True)] if a.compare_detourage else [])
    res.update({'mot': a.word, 'police': os.path.basename(fp), 'police_px': size, 'mot_cx': CX, 'mot_cy': CY,
                'couleur': '#%02X%02X%02X' % tuple(int(v) for v in col[::-1]), 'luminance_fond_mot': round(lum, 1), 'mesures': {}})
    ok = True; tmp = out / '_ld'; tmp.mkdir(exist_ok=True); t = time.time()
    for name, A, det in todo:
        res['mesures'][name] = {'ecart_px': A}
        for u, lab_ in ((-0.5, 'debut'), (0.0, 'milieu'), (0.5, 'fin')):
            (pl, tx, fi), (h, hp_, lets), box = frame(A, u, det)
            m = {'cache_pct': round(100 * h, 1), 'cache_par_personnes_pct': round(100 * hp_, 1),
                 'premiere_lettre_pct': round(100 * lets[0], 1), 'derniere_lettre_pct': round(100 * lets[-1], 1)}
            if LAYER_DIFF.exists():
                ps_ = [tmp / (k + '.png') for k in ('plaque', 'texte', 'final')]
                for p_, im_ in zip(ps_, (pl, tx, fi)): cv2.imwrite(str(p_), im_)
                r = subprocess.run([sys.executable, '-I', str(LAYER_DIFF), 'behind', *map(str, ps_), '--box', ','.join(map(str, box)), '--min', '0.25', '--max', '0.40'],
                                   capture_output=True, text=True)
                m['layer_diff'] = r.stdout.strip()
            if not det and (not 25 <= m['cache_pct'] <= 40 or max(lets[0], lets[-1]) > 0.5): ok = False
            res['mesures'][name][lab_] = m
            if u: cv2.imwrite(str(out / ('apercu_%s_%s.jpg' % (name, lab_))), fi, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(name, {k: v['cache_pct'] for k, v in res['mesures'][name].items() if k != 'ecart_px'}, flush=True)
    for p_ in tmp.glob('*.png'): p_.unlink()
    tmp.rmdir(); T['mesures_s'] = round(time.time() - t, 2)
    if a.preview:
        t = time.time(); name, A, _ = todo[0]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '540x960', '-r', '30', '-i', '-',
                              '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', str(out / ('apercu_%s_%gs.mp4' % (name, a.duree)))], stdin=subprocess.PIPE)
        nf = int(30 * a.duree)
        for i in range(nf):
            (_, _, fi), _, _ = frame(A, -0.5 + i / (nf - 1)); p.stdin.write(cv2.resize(fi, (540, 960), interpolation=cv2.INTER_AREA).tobytes())
        p.stdin.close(); p.wait(); T['apercu_s'] = round(time.time() - t, 2)
    T['total_s'] = round(time.time() - t_all, 2); res['dans_les_bornes'] = ok
    json.dump(res, open(out / 'calques.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(T)); return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
