#!/usr/bin/env python3
"""Audit des transitions d'une vidéo, mesuré image par image (ffmpeg + numpy + OpenCV ; MediaPipe si présent).

  sources <video> [--min-diff 8] [--ratio 3] [--scdet 10]
      Coupes cachées d'une source (ancien montage, rush) AVANT tout montage : temps, image, écart, rapport au voisinage
      (méthode « adaptative » de PySceneDetect, recodée), score `scdet` de ffmpeg ; flashs (image isolée) et images doublées à part.
  cuts <video> (--cuts 5.57,10.03,… | --storyboard storyboard.json|cues.json|transitions.json) [--sheet planche.jpg] [--json out.json]
      Pour chaque coupe (recalée sur l'image du plus grand saut à ±3 images) :
        rampe   = images de mouvement ou de flou juste AVANT la coupe (flux optique, zoom, chute de netteté), et APRÈS (relâche) ;
        lum     = saut de luminance moyenne (0-255) entre t-1 et t ;
        visages = détection à t-1, t, t+1 (et t±6 comme référence) : visage coupé par le bord, visage en double (fantôme) ;
        fantôme = image isolée ou image mélangée A+B ; direction = sens du mouvement inversé de part et d'autre de la coupe.
      Verdict par coupe : OK ou À REVOIR (raisons). `--sheet` : une rangée de 7 images (t-4 … t+2) par coupe, visages encadrés.
Code de sortie : 0 tout OK, 1 au moins une coupe À REVOIR (ou une coupe cachée trouvée en mode sources), 2 erreur.
Détecteur de visages (--faces auto) : MediaPipe (solutions, ou tâches avec --mp-model .tflite), sinon YuNet (OpenCV DNN, MIT,
--yunet ou ~/.cache/biteye-transitions/face_detection_yunet_2023mar.onnx), sinon Haar (fourni avec opencv-python < 5).
Coût : ≈ 10 à 30 s pour 40 s de vidéo 1080x1920, aucun jeton de modèle. Rien n'est écrit hors des chemins donnés."""
import argparse, json, math, os, re, subprocess, sys, tempfile
import numpy as np
try:
    import cv2
except ImportError:
    sys.exit('OpenCV absent : pip install "opencv-python-headless<5" (la branche 5 ne fournit plus les cascades Haar)')

YUNET_DEFAULT = os.path.expanduser('~/.cache/biteye-transitions/face_detection_yunet_2023mar.onnx')
AFTER_TYPES = {'maskreveal', 'fade', 'dissolve', 'crossfade', 'xfade', 'lightleak'}   # la transition se joue après la coupe


def probe(v):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,r_frame_rate,nb_frames:format=duration', '-of', 'json', v],
                       capture_output=True, text=True)
    if r.returncode: sys.exit('ffprobe : ' + r.stderr.strip())
    d = json.loads(r.stdout); s = d['streams'][0]; n, q = s['r_frame_rate'].split('/')
    return int(s['width']), int(s['height']), float(n) / float(q), float(d['format'].get('duration', 0))


def size_for(w, h, long_side):
    k = long_side / max(w, h)
    return max(2, int(round(w * k / 2)) * 2), max(2, int(round(h * k / 2)) * 2)


def frames(v, w, h, vf_extra='', select=None, stderr_file=None):
    """Itère (index, image BGR) ; `select` = liste de (a, b) inclusifs : un seul décodage, numéros d'image exacts."""
    vf = f'scale={w}:{h}:flags=area' + vf_extra
    if select:
        vf = "select='" + '+'.join(f'between(n\\,{a}\\,{b})' for a, b in select) + "'," + vf
    cmd = ['ffmpeg', '-v', 'info' if stderr_file else 'error', '-nostats', '-i', v, '-an', '-vf', vf, '-fps_mode', 'passthrough',
           '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr_file or subprocess.DEVNULL)
    idx = [i for a, b in select for i in range(a, b + 1)] if select else None
    k, size = 0, w * h * 3
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size: break
        yield (idx[k] if idx else k), np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        k += 1
    p.wait()


# ---------------------------------------------------------------- visages
class Faces:
    def __init__(self, pref, yunet, mp_model):
        self.kind, self.err = None, ''
        if pref in ('auto', 'mediapipe'):
            try:
                import mediapipe as mp
                if getattr(getattr(mp, 'solutions', None), 'face_detection', None):
                    self.mp = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)
                    self.kind = 'mediapipe'
                elif mp_model and os.path.exists(mp_model):
                    from mediapipe.tasks.python import BaseOptions, vision
                    self.mpi = mp
                    self.mp = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
                        base_options=BaseOptions(model_asset_path=mp_model), min_detection_confidence=0.6))
                    self.kind = 'mediapipe-tasks'
            except Exception as e:  # absent ou incompatible : repli
                self.err = 'mediapipe : %s' % str(e)[:80]
        if not self.kind and pref in ('auto', 'yunet'):
            path = yunet or YUNET_DEFAULT
            if os.path.exists(path) and hasattr(cv2, 'FaceDetectorYN'):
                self.yn = cv2.FaceDetectorYN.create(path, '', (320, 320), 0.75, 0.3, 50); self.kind = 'yunet'
        if not self.kind and pref in ('auto', 'haar'):
            xml = os.path.join(getattr(getattr(cv2, 'data', None), 'haarcascades', ''), 'haarcascade_frontalface_default.xml')
            if os.path.exists(xml):
                self.haar = cv2.CascadeClassifier(xml); self.kind = 'haar'
        if pref == 'none' or not self.kind: self.kind = self.kind or 'aucun'

    def __call__(self, img):
        """Liste de boîtes (x, y, w, h, score) en px de l'image ; une boîte peut déborder du cadre (MediaPipe, YuNet)."""
        H, W = img.shape[:2]
        if self.kind == 'mediapipe':
            r = self.mp.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); out = []
            for d in (r.detections or []):
                b = d.location_data.relative_bounding_box
                out.append((b.xmin * W, b.ymin * H, b.width * W, b.height * H, float(d.score[0])))
            return out
        if self.kind == 'mediapipe-tasks':
            im = self.mpi.Image(image_format=self.mpi.ImageFormat.SRGB, data=np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
            return [(d.bounding_box.origin_x, d.bounding_box.origin_y, d.bounding_box.width, d.bounding_box.height,
                     float(d.categories[0].score)) for d in self.mp.detect(im).detections]
        if self.kind == 'yunet':
            self.yn.setInputSize((W, H)); _, f = self.yn.detect(img)
            return [] if f is None else [tuple(float(v) for v in r[:4]) + (float(r[-1]),) for r in f]
        if self.kind == 'haar':
            g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); m = int(0.08 * W)
            return [(float(x), float(y), float(w), float(h), 1.0)
                    for x, y, w, h in self.haar.detectMultiScale(g, 1.1, 6, minSize=(m, m))]
        return []


def face_issues(boxes, W, H, base):
    """Défauts d'une image : bord (visage coupé par le cadre), double (plus de visages comparables qu'en référence)."""
    m = 0.01 * W; iss = []
    for x, y, w, h, s in boxes:
        if x < m or y < m or x + w > W - m or y + h > H - m: iss.append('bord')
    big = [b for b in boxes if b[2] >= 0.08 * W]
    if len(big) > base and len(big) >= 2:
        sz = sorted(b[2] for b in big)
        if sz[-2] >= 0.5 * sz[-1]: iss.append('double')
    for i, p in enumerate(big):            # surimpression : deux visages de même taille, même hauteur, presque collés
        for q in big[i + 1:]:
            if 0.7 <= p[2] / q[2] <= 1.4 and abs((p[1] + p[3] / 2) - (q[1] + q[3] / 2)) < 0.35 * p[3] \
                    and abs((p[0] + p[2] / 2) - (q[0] + q[2] / 2)) < 1.5 * max(p[2], q[2]) and 'double' not in iss:
                iss.append('double')
    return iss


# ---------------------------------------------------------------- mesures
def flow_stats(g0, g1):
    f = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    h, w = g0.shape; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rx, ry = xx - w / 2, yy - h / 2; rn = np.sqrt(rx ** 2 + ry ** 2) + 1e-3
    div = float(np.mean((f[..., 0] * rx + f[..., 1] * ry) / rn))          # > 0 : zoom avant (les pixels fuient le centre)
    return float(np.mean(np.hypot(f[..., 0], f[..., 1]))), float(f[..., 0].mean()), float(f[..., 1].mean()), div


def load_cuts(a, fps):
    if a.cuts: return sorted({round(float(t) * fps): (float(t), None) for t in a.cuts.split(',') if t.strip()}.values())
    d = json.load(open(a.storyboard, encoding='utf-8')); out = []
    items = d if isinstance(d, list) else d.get('coupes') or d.get('transitions') if 'scenes' not in d else None
    if items is not None and 'scenes' not in (d if isinstance(d, dict) else {}):   # cues.json ou fiche transitions.json
        for it in items:
            t = it.get('cut', it.get('t', it.get('start')))
            if t is not None: out.append((float(t), it.get('type')))
    else:                                                   # storyboard.json du moteur
        sc = d['scenes']; first = min(s['start'] for s in sc)
        for s in sc:
            tr = s.get('transition') or {}
            if s['start'] > first + 1e-6: out.append((float(tr.get('cut', s['start'])), tr.get('type')))
            for l in s.get('layers', []):
                if l.get('kind') == 'video' and l['start'] > s['start'] + 1e-6: out.append((float(l['start']), None))
        for tr in d.get('transitions', []):
            if 'cut' in tr: out.append((float(tr['cut']), tr.get('type')))
        out += [(float(t), None) for t in d.get('cuts', [])]
    best = {}
    for t, ty in out:                                        # dédoublonne à une image près, garde le type déclaré
        k = round(t * fps)
        if k not in best or (ty and not best[k][1]): best[k] = (t, ty)
    return sorted(best.values())


def cmd_cuts(a):
    W0, H0, fps, dur = probe(a.video); n_tot = int(round(dur * fps))
    FW, FH = size_for(W0, H0, 960); AW, AH = size_for(W0, H0, 480)
    cuts = load_cuts(a, fps)
    if not cuts: sys.exit('aucune coupe à contrôler')
    win = [(max(0, round(t * fps) - 22), min(n_tot - 1, round(t * fps) + 12)) for t, _ in cuts]
    merged = []
    for s, e in sorted(win):
        if merged and s <= merged[-1][1] + 1: merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else: merged.append((s, e))
    F = dict(frames(a.video, FW, FH, select=merged))
    fd = Faces(a.faces, a.yunet, a.mp_model)
    small = {i: cv2.resize(im, (AW, AH), interpolation=cv2.INTER_AREA) for i, im in F.items()}
    gray = {i: cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for i, im in small.items()}
    sharp = {i: float(cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()) for i, im in F.items()}
    luma = {i: float(g.mean()) for i, g in gray.items()}
    D = lambda i, j: float(np.abs(small[i].astype(np.int16) - small[j].astype(np.int16)).mean())
    diff = {i: D(i - 1, i) for i in small if i - 1 in small}
    flow = {}
    def FL(i):
        if i not in flow and i - 1 in gray: flow[i] = flow_stats(gray[i - 1], gray[i])
        return flow.get(i)
    face_cache = {}
    def faces(i):
        if i not in face_cache: face_cache[i] = fd(F[i]) if i in F else []
        return face_cache[i]
    rows, prev_c = [], -10 ** 9
    for (t, ty), (s, e) in zip(cuts, win):
        n0 = round(t * fps)
        if n0 not in F or n0 - 1 not in F:
            rows.append({'t': t, 'type': ty, 'frame': n0, 'saut': 0, 'rampe_avant': 0, 'relache_apres': 0, 'lum': 0,
                         'verdict': 'À REVOIR', 'raisons': ['coupe hors de la vidéo (%d images)' % n_tot], 'notes': []}); continue
        cand = [k for k in range(n0 - 3, n0 + 4) if k in diff]
        c = max(cand, key=lambda k: diff[k]) if cand else n0
        hard = diff.get(c, 0) >= a.hard
        if not hard: c = n0
        # référence = le passage le plus calme du plan sortant (quartile bas de t-20 … t-6), pas une fenêtre fixe
        r0, r1 = max(prev_c + 1, c - 20, s + 1), c - 6
        ref = [k for k in range(r0, r1 + 1) if k in diff]
        q = lambda xs: float(np.percentile(xs, 25)) if xs else 0.0
        ref_mag, ref_div = q([FL(k)[0] for k in ref]), q([abs(FL(k)[3]) for k in ref])
        ref_d = q([diff[k] for k in ref])
        ref_sh = float(np.median([sharp[k] for k in ref])) if ref else max(sharp.get(c - 8, 0), 1)
        def moving(k, ref_sh_=ref_sh, step=-1):
            f = FL(k)
            if f is None: return False
            sk, sp = sharp.get(k, ref_sh_), sharp.get(k + step, ref_sh_)   # flou : netteté sous la référence ET qui baisse vers la coupe
            blur = ref_sh_ > 0 and sk <= a.blur * ref_sh_ and (sk < 0.97 * sp or sk <= 0.6 * ref_sh_)
            return (f[0] >= max(a.mag, 1.5 * ref_mag) or abs(f[3]) >= max(a.div, 2 * ref_div)
                    or diff.get(k, 0) >= max(a.dmin, 2 * ref_d) or blur)
        rb = 0
        for k in range(c - 1, c - 11, -1):
            if k in diff and moving(k): rb += 1
            else: break
        post = [k for k in range(c + 6, c + 12) if k in sharp]
        post_sh = float(np.median([sharp[k] for k in post])) if post else ref_sh
        ra = 0
        for k in range(c + 1, c + 11):
            if k in diff and moving(k, post_sh, +1): ra += 1
            else: break
        lum = abs(luma[c] - luma[c - 1]) if c in luma and c - 1 in luma else 0.0
        lum_win = max((abs(luma[k] - luma[k - 1]) for k in range(c - 5, c + 6) if k in luma and k - 1 in luma), default=0)
        reasons, notes = [], []
        # image fantôme : image isolée, coupe en deux temps, image mélangée A+B
        ghost = []
        for k in range(c - 3, c + 4):
            # deux sauts consécutifs encadrés d'images calmes (pas pendant un whip, où toutes les images bougent)
            if all(x in small for x in (k - 1, k, k + 1)) and diff.get(k, 0) >= a.hard and diff.get(k + 1, 0) >= a.hard \
                    and diff.get(k - 1, 0) < a.hard / 2 and diff.get(k + 2, 0) < a.hard / 2:
                ghost.append(('image isolée %d' if D(k - 1, k + 1) < 0.5 * min(diff[k], diff[k + 1]) else 'coupe en deux temps %d') % k)
        if hard and all(x in small for x in (c - 1, c, c + 1)):
            ab = D(c - 1, c + 1)
            mix = float(np.abs(small[c].astype(np.float32) - (small[c - 1].astype(np.float32) + small[c + 1]) / 2).mean())
            # une seule image mélangée (le plan suivant est posé dès t+1) ; un fondu enchaîné de plusieurs images n'est pas un fantôme
            if ab >= a.hard and mix < 0.2 * ab and diff.get(c + 1, 0) >= 0.3 * ab and diff.get(c + 2, 0) < a.hard / 2:
                ghost.append('image mélangée A+B %d' % c)
        ghost = sorted(set(ghost))
        # direction du mouvement de part et d'autre
        pre = [FL(k) for k in range(c - 3, c) if FL(k)]; pst = [FL(k) for k in range(c + 1, c + 4) if FL(k)]
        dirn = ''
        if pre and pst:
            vx0, vy0 = np.mean([f[1] for f in pre]), np.mean([f[2] for f in pre])
            vx1, vy1 = np.mean([f[1] for f in pst]), np.mean([f[2] for f in pst])
            m0, m1 = math.hypot(vx0, vy0), math.hypot(vx1, vy1)
            if m0 >= a.dir_min and m1 >= a.dir_min and (vx0 * vx1 + vy0 * vy1) / (m0 * m1) < 0:
                dirn = 'inversée (%.1f,%.1f → %.1f,%.1f px/img)' % (vx0, vy0, vx1, vy1)
        # visages
        fi = {}
        if fd.kind != 'aucun':
            base = max(len([b for b in faces(k) if b[2] >= 0.08 * FW]) for k in (c - 6, c + 6))
            for k in (c - 1, c, c + 1):
                if k in F: fi[k] = face_issues(faces(k), FW, FH, base)
        fbad = sorted({'%s à t%+d' % (x, k - c) for k, v in fi.items() for x in v})
        need_ramp = (ty or '').lower() not in AFTER_TYPES
        if hard:
            if need_ramp and rb < a.ramp: reasons.append('rampe %d img < %d' % (rb, a.ramp))
            if not need_ramp and max(rb, ra) < a.ramp: reasons.append('ni rampe ni relâche ≥ %d img' % a.ramp)
        else:
            notes.append('saut < %.0f : coupe douce ou fondu (rampe non exigée)' % a.hard)
        # saut visible : coupe franche nette (ni flou fort ni mouvement rapide à t-1 pour la masquer)
        f1m = FL(c - 1)
        masked = (sharp.get(c - 1, ref_sh) <= a.mask_blur * ref_sh) or (f1m is not None and f1m[0] >= a.mask_flow)
        if hard and diff.get(c, 0) >= a.visible and not masked:
            reasons.append('saut visible %.0f non masqué (netteté t-1 à %d %% de la réf.)' % (diff[c], 100 * sharp.get(c - 1, 0) / max(ref_sh, 1)))
        steps = [abs(luma[k] - luma[k - 1]) for k in (c - 1, c + 1) if k in luma and k - 1 in luma]
        if lum > a.luma and lum >= 2 * max(steps, default=0): reasons.append('saut de luminance %.1f > %.0f' % (lum, a.luma))
        elif lum > a.luma: notes.append('luminance progressive (%.0f à la coupe, voisins %s)' % (lum, '/'.join('%.0f' % x for x in steps)))
        if ghost: reasons.append('fantôme : ' + ', '.join(ghost))
        if dirn: reasons.append('direction ' + dirn)
        if fbad: reasons.append('visage : ' + ', '.join(fbad))
        if fd.kind != 'aucun' and not any(faces(k) for k in (c - 6, c - 1, c + 1, c + 6)): notes.append('aucun visage détecté')
        f0 = [b for b in faces(c - 1)] if fd.kind != 'aucun' else []
        f1 = [b for b in faces(c + 1)] if fd.kind != 'aucun' else []
        if f0 and f1:
            A, B = max(f0, key=lambda b: b[2]), max(f1, key=lambda b: b[2])
            notes.append('visage Δx %+d Δy %+d px, taille ×%.2f (en %dx%d)' % (
                (B[0] + B[2] / 2) - (A[0] + A[2] / 2), (B[1] + B[3] / 2) - (A[1] + A[3] / 2), B[2] / max(A[2], 1), FW, FH))
        rows.append({'t': t, 'type': ty, 'frame': c, 't_mesure': round(c / fps, 3), 'saut': round(diff.get(c, 0), 1),
                     'coupe_franche': hard, 'rampe_avant': rb, 'relache_apres': ra, 'lum': round(lum, 1),
                     'lum_max_fenetre': round(lum_win, 1),
                     'ecarts_avant': [round(diff[k], 1) for k in range(c - 5, c) if k in diff],
                     'nettete_avant': [round(sharp[k]) for k in range(c - 5, c + 1) if k in sharp],
                     'flux_avant': [round(FL(k)[0], 2) for k in range(c - 5, c) if FL(k)],
                     'zoom_avant': [round(FL(k)[3], 2) for k in range(c - 5, c) if FL(k)],
                     'luma_fenetre': [round(luma[k], 1) for k in range(c - 5, c + 3) if k in luma],
                     'reference': {'ecart': round(ref_d, 1), 'flux': round(ref_mag, 2), 'zoom': round(ref_div, 2), 'nettete': round(ref_sh)},
                     'visages': {str(k - c): [[round(v) for v in b[:4]] for b in faces(k)] for k in (c - 1, c, c + 1)} if fd.kind != 'aucun' else {},
                     'verdict': 'À REVOIR' if reasons else 'OK', 'raisons': reasons, 'notes': notes})
        prev_c = c
    print('détecteur de visages : %s%s | %d coupes | seuils : rampe ≥ %d img, saut franc ≥ %.0f, luminance ≤ %.0f'
          % (fd.kind, (' (' + fd.err + ')') if fd.kind != 'mediapipe' and fd.err else '', len(rows), a.ramp, a.hard, a.luma))
    print('%-7s %-11s %-6s %-6s %-6s %-6s %-5s %-9s %s' % ('t', 'type', 'image', 'saut', 'rampe', 'relâche', 'lum', 'verdict', 'raisons / notes'))
    for r in rows:
        print('%-7.2f %-11s %-6d %-6.1f %-6d %-7d %-5.1f %-9s %s' % (r['t'], (r['type'] or '-')[:11], r['frame'], r['saut'], r['rampe_avant'],
              r['relache_apres'], r['lum'], r['verdict'], ' ; '.join(r['raisons'] + r['notes'])))
        if a.verbose:
            print('        écarts t-5…t-1 %s | netteté t-5…t %s | flux %s | zoom %s | luma t-5…t+2 %s | réf. %s' % (
                r['ecarts_avant'], r['nettete_avant'], r['flux_avant'], r['zoom_avant'], r['luma_fenetre'], r['reference']))
    if a.json: json.dump({'video': a.video, 'fps': fps, 'detecteur': fd.kind, 'coupes': rows}, open(a.json, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if a.sheet: sheet(a.sheet, rows, F, faces, FW, FH, diff, luma)
    return 1 if any(r['verdict'] != 'OK' for r in rows) else 0


def sheet(path, rows, F, faces, FW, FH, diff, luma):
    tw, th = 216, int(round(216 * FH / FW)); tiles = []
    for r in [r for r in rows if r['frame'] in F]:
        c = r['frame']; line = []
        for k in range(c - 4, c + 3):
            im = cv2.resize(F[k], (tw, th), interpolation=cv2.INTER_AREA) if k in F else np.zeros((th, tw, 3), np.uint8)
            sx = tw / FW
            for x, y, w, h, s in faces(k) if k in F else []:
                bad = x < 0.01 * FW or y < 0.01 * FH or x + w > 0.99 * FW or y + h > 0.99 * FH
                cv2.rectangle(im, (int(x * sx), int(y * sx)), (int((x + w) * sx), int((y + h) * sx)), (0, 0, 255) if bad else (0, 220, 0), 2)
            lab = 't%+d  d%.1f  Y%.0f' % (k - c, diff.get(k, 0), luma.get(k, 0))
            cv2.rectangle(im, (0, th - 22), (tw, th), (0, 0, 0), -1)
            cv2.putText(im, lab, (4, th - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            if k == c: cv2.rectangle(im, (0, 0), (tw - 1, th - 1), (0, 200, 255), 3)
            line.append(im)
        head = np.zeros((26, tw * 7, 3), np.uint8)
        txt = '%.2f s  img %d  %s  rampe %d  relache %d  %s' % (r['t'], c, r['type'] or '', r['rampe_avant'], r['relache_apres'],
                                                              'OK' if r['verdict'] == 'OK' else 'A REVOIR')
        cv2.putText(head, txt, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 0) if r['verdict'] == 'OK' else (0, 80, 255), 1, cv2.LINE_AA)
        tiles.append(np.vstack([head, np.hstack(line)]))
    cv2.imwrite(path, np.vstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print('planche :', path)


def cmd_sources(a):
    W0, H0, fps, dur = probe(a.video); AW, AH = size_for(W0, H0, 240)
    with tempfile.TemporaryFile() as log:
        prev, d, lum = None, [], []
        for i, im in frames(a.video, AW, AH, vf_extra=',scdet=t=%g' % a.scdet, stderr_file=log):
            f = im.astype(np.int16); lum.append(float(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).mean()))
            d.append(0.0 if prev is None else float(np.abs(f - prev).mean())); prev = f
        log.seek(0); txt = log.read().decode('utf-8', 'replace')
    sc = {}
    for m in re.finditer(r'lavfi\.scd\.score:\s*([0-9.]+),\s*lavfi\.scd\.time:\s*([0-9.]+)', txt):
        sc[int(round(float(m.group(2)) * fps))] = float(m.group(1))
    d = np.array(d); n = len(d); k = a.window; cuts, flashes = [], []
    for i in range(1, n):
        nb = np.r_[d[max(1, i - k):i], d[i + 1:i + 1 + k]]
        ratio = d[i] / (nb.mean() + 0.5) if len(nb) else 0
        s = max((sc.get(j, 0) for j in (i - 1, i, i + 1)), default=0)   # scdet n'écrit que les scores au-dessus de son seuil
        if d[i] >= a.min_diff and (ratio >= a.ratio or s >= a.scdet):
            if i + 1 < n and d[i + 1] >= a.min_diff and 0 < i - 1 and \
                    abs(lum[i + 1] - lum[i - 1]) < 2 and d[i + 1] >= 0.6 * d[i]:
                flashes.append(i); continue
            if cuts and i - cuts[-1][0] <= 1: continue
            cuts.append((i, d[i], ratio, s))
    flashes = [f for f in flashes if not any(abs(f - c[0]) <= 1 for c in cuts)]
    dup = [i for i in range(1, n) if d[i] < a.dup]
    print('%s : %d images, %.3f i/s, %d coupes cachées (écart ≥ %.0f et ×%.0f le voisinage, ou scdet ≥ %g)'
          % (os.path.basename(a.video), n, fps, len(cuts), a.min_diff, a.ratio, a.scdet))
    print('%-8s %-6s %-7s %-7s %s' % ('t (s)', 'image', 'écart', 'rapport', 'scdet (0 = sous le seuil)'))
    for i, v, r, s in cuts: print('%-8.3f %-6d %-7.1f %-7.1f %.1f' % (i / fps, i, v, r, s))
    if flashes: print('images isolées (flash ou image fantôme) :', ', '.join('%.3f s (img %d)' % (i / fps, i) for i in flashes[:20]))
    if dup: print('images doublées (écart < %.1f) : %d, ex. %s' % (a.dup, len(dup), ', '.join('%d' % i for i in dup[:12])))
    if a.json:
        json.dump({'video': a.video, 'fps': fps, 'coupes': [{'t': round(i / fps, 3), 'frame': i, 'ecart': round(v, 1), 'rapport': round(r, 1),
                   'scdet': s} for i, v, r, s in cuts], 'isolees': flashes, 'doublees': dup}, open(a.json, 'w', encoding='utf-8'), indent=1)
    if a.sheet and cuts:   # paires t-1 | t de chaque coupe trouvée, 4 paires par rangée : on vérifie à l'œil (incrustation ≠ coupe)
        tw, th = size_for(W0, H0, 320); idx = sorted({j for i, *_ in cuts for j in (i - 1, i)})
        F = dict(frames(a.video, tw, th, select=[(j, j) for j in idx])); cells = []
        for i, v, r, sc_ in cuts:
            pair = np.hstack([F.get(i - 1, np.zeros((th, tw, 3), np.uint8)), F.get(i, np.zeros((th, tw, 3), np.uint8))]).copy()
            cv2.rectangle(pair, (0, 0), (2 * tw, 20), (0, 0, 0), -1)
            cv2.putText(pair, '%.3f s  img %d  d%.0f x%.0f' % (i / fps, i, v, r), (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            cells.append(np.pad(pair, ((0, 4), (0, 4), (0, 0))))
        while len(cells) % 4: cells.append(np.zeros_like(cells[0]))
        cv2.imwrite(a.sheet, np.vstack([np.hstack(cells[k:k + 4]) for k in range(0, len(cells), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
        print('planche :', a.sheet)
    return 1 if cuts or flashes else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='mode', required=True)
    s = sp.add_parser('sources'); s.add_argument('video')
    s.add_argument('--min-diff', type=float, default=8, help='écart moyen BGR minimal (0-255, en 135x240) pour une coupe')
    s.add_argument('--ratio', type=float, default=3, help='écart / moyenne des voisins (PySceneDetect adaptive : 3)')
    s.add_argument('--window', type=int, default=4, help='voisins de chaque côté pour le rapport')
    s.add_argument('--scdet', type=float, default=10, help='seuil du filtre ffmpeg scdet (0-100)')
    s.add_argument('--dup', type=float, default=0.3, help='écart sous lequel deux images sont doublées')
    s.add_argument('--json'); s.add_argument('--sheet', help='planche JPEG des paires t-1 | t')
    c = sp.add_parser('cuts'); c.add_argument('video')
    g = c.add_mutually_exclusive_group(required=True); g.add_argument('--cuts'); g.add_argument('--storyboard')
    c.add_argument('--ramp', type=int, default=3, help='images de rampe exigées avant une coupe franche')
    c.add_argument('--hard', type=float, default=12, help='écart moyen BGR (0-255, en 270x480) qui fait une coupe franche')
    c.add_argument('--luma', type=float, default=12, help='saut de luminance moyenne maximal à la coupe (0-255)')
    c.add_argument('--mag', type=float, default=0.8, help='flux optique moyen (px/img en 270x480) qui compte comme mouvement')
    c.add_argument('--dmin', type=float, default=4, help='écart image à image minimal (et ≥ 2 × référence) qui compte comme mouvement')
    c.add_argument('--div', type=float, default=0.35, help='composante zoom du flux (px/img) qui compte comme mouvement')
    c.add_argument('--blur', type=float, default=0.85, help='netteté ≤ blur × référence = image de flou')
    c.add_argument('--visible', type=float, default=18, help='saut (écart BGR) au-delà duquel une coupe non masquée se voit')
    c.add_argument('--mask-blur', type=float, default=0.5, help='netteté t-1 ≤ mask-blur × référence = saut masqué par le flou')
    c.add_argument('--mask-flow', type=float, default=3, help='flux t-1 ≥ mask-flow px/img = saut masqué par le mouvement')
    c.add_argument('--dir-min', type=float, default=1.5, help='translation minimale (px/img) pour juger la direction')
    c.add_argument('--faces', default='auto', choices=['auto', 'mediapipe', 'yunet', 'haar', 'none'])
    c.add_argument('--yunet'); c.add_argument('--mp-model')
    c.add_argument('--sheet'); c.add_argument('--json'); c.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()
    if not os.path.exists(a.video): sys.exit('vidéo introuvable : ' + a.video)
    sys.exit(cmd_sources(a) if a.mode == 'sources' else cmd_cuts(a))


if __name__ == '__main__':
    main()
