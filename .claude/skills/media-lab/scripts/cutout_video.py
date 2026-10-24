#!/usr/bin/env python3
"""Détourage vidéo d'un sujet SUR LA PLAQUE (toile 1080x1920, placement identique, matte pleine hauteur), en un ou plusieurs travaux.
Remplace subject_plate.py et les 8 lanceurs run_*.sh de la V2 (z, z_v2, z_v3, n_v3, n2_split, plates_subtil, mots, mots_plein).
Modèles : u2net_human_seg (rembg) ou rvm (onnx dans ~/.u2net). Lissages : moyenne temporelle 3 images (u2net) / 75-25 (rvm), érosion 1 px, flou 1,5 px,
aucun fondu en haut (le crâne reste net jusqu'au bord de la plaque), fondu de 30 px à gauche, à droite et en bas de la zone 1000x1500 (x 40-1040, y 100-1600).
Usage unique : cutout_video.py <plaque.webm> <image0> <nb_images> <u2net|rvm> <sortie.webm>
Usage lot    : cutout_video.py --jobs travaux.txt [--log lot.log]     (une ligne par travail : plaque image0 nb methode sortie ; # = commentaire)
Après chaque travail : contrôle de la tête (head_top qui saute de > 25 px entre deux images = crâne coupé) ; le lot s'arrête au premier défaut.
Écrit <sortie>_info.json (head_x, head_top par image), _first.png, _mid.png. Voir align_check.py pour vérifier le placement avant rendu.
Conseil de coût : OMP_NUM_THREADS=3 nice -n 10 ; ~1 s de calcul par image (mesuré V2 : 2 513 s pour 2 346 images sur 37 travaux)."""
import sys, os, glob, json, subprocess, tempfile, shutil, time
import numpy as np
from PIL import Image, ImageFilter
X0, Y0, W, H = 40, 100, 1000, 1500

def run(vid, i0, n, meth, out):
    tmp = tempfile.mkdtemp(prefix='subjp_', dir=os.path.dirname(os.path.abspath(out))); fr = os.path.join(tmp, 'f'); os.makedirs(fr)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-vf', f"select='between(n\\,{i0}\\,{i0 + n - 1})',crop={W}:{H}:{X0}:{Y0}", '-vsync', '0',
                    os.path.join(fr, '%04d.png')], check=True)
    files = sorted(glob.glob(fr + '/*.png')); assert len(files) == n, (len(files), n)
    A = []
    if meth == 'rvm':
        import onnxruntime as ort
        sess = ort.InferenceSession(os.path.expanduser('~/.u2net/rvm_mobilenetv3_fp32.onnx'), providers=['CPUExecutionProvider'])
        rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4; dr = np.array([0.25], np.float32)
        ld = lambda f: np.asarray(Image.open(f).convert('RGB'), np.float32).transpose(2, 0, 1)[None] / 255
        first = ld(files[0])
        for _ in range(3):
            _, _, *rec = sess.run(None, {'src': first, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': dr})
        for f in files:
            _, pha, *rec = sess.run(None, {'src': ld(f), 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': dr})
            A.append(np.clip(pha[0, 0], 0, 1))
        A = np.stack(A); A = 0.75 * A + 0.25 * np.concatenate([A[:1], A[:-1]])
    else:
        from rembg import new_session, remove
        sess = new_session('u2net_human_seg')
        for f in files:
            A.append(np.asarray(remove(Image.open(f).convert('RGB'), session=sess, only_mask=True), np.float32) / 255)
        A = np.stack(A); p = np.concatenate([A[:1], A, A[-1:]]); A = (p[:-2] + p[1:-1] + p[2:]) / 3
    yy, xx = np.mgrid[0:H, 0:W]
    edge = np.clip(np.minimum.reduce([xx / 30, (W - 1 - xx) / 30, (H - 1 - yy) / 30]), 0, 1).astype(np.float32)
    od = os.path.join(tmp, 'o'); os.makedirs(od); info = []
    for i, f in enumerate(files):
        al = Image.fromarray((A[i] * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
        a = np.asarray(al, np.float32) / 255 * edge
        ys, xs = np.nonzero(a > 0.5)
        if len(ys):
            top = ys.min(); band = xs[(ys > top + 20) & (ys < top + 260)]
            info.append({'head_x': round(float(np.median(band) if len(band) else xs.mean()) + X0, 1), 'head_top': int(top + Y0), 'face_y': int(top + Y0 + 230)})
        rgb = Image.open(f).convert('RGB'); can = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        rgb.putalpha(Image.fromarray((a * 255).astype(np.uint8))); can.paste(rgb, (X0, Y0)); can.save(os.path.join(od, '%04d.png' % i))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(od, '%04d.png'), '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
                    '-b:v', '0', '-crf', '26', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '4', '-auto-alt-ref', '0', out], check=True)
    shutil.copy(os.path.join(od, '0000.png'), out.replace('.webm', '_first.png')); shutil.copy(os.path.join(od, '%04d.png' % (n // 2)), out.replace('.webm', '_mid.png'))
    hx = [x['head_x'] for x in info]; ht = [x['head_top'] for x in info]
    json.dump({'frames': n, 'source': [vid, i0], 'head_x_med': float(np.median(hx)), 'head_x_range': [min(hx), max(hx)], 'head_top_med': float(np.median(ht)),
               'head_top_range': [min(ht), max(ht)], 'per_frame': info}, open(out.replace('.webm', '_info.json'), 'w'), indent=0)
    shutil.rmtree(tmp); print('ok', out, n, 'head x~%.0f top~%.0f' % (np.median(hx), np.median(ht)))

def gate(out):
    info = json.load(open(out.replace('.webm', '_info.json')))['per_frame']; ht = [f['head_top'] for f in info]
    jumps = [k for k in range(1, len(ht)) if abs(ht[k] - ht[k - 1]) > 25]
    return jumps

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--jobs':
        log = sys.argv[sys.argv.index('--log') + 1] if '--log' in sys.argv else None
        for line in open(sys.argv[2]):
            line = line.split('#')[0].split()
            if not line: continue
            t0 = time.time(); run(line[0], int(line[1]), int(line[2]), line[3], line[4]); j = gate(line[4])
            msg = '%s %d s%s' % (line[4], time.time() - t0, '' if not j else ' DEFAUT tête : saut head_top aux images %s' % j[:5])
            print(msg); open(log, 'a').write(msg + '\n') if log else None
            if j: sys.exit(1)
    else:
        run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]); j = gate(sys.argv[5])
        if j: print('DEFAUT tête : saut head_top aux images', j[:5]); sys.exit(1)
