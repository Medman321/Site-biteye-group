#!/usr/bin/env python3
"""Free toolbox for the client's clips and photos (ffmpeg, plus rembg for cut-outs). No paid service.

  python3 -I media_lab.py shots     IN.mp4 --out DIR [--threshold 0.3]        # split into shots + contact sheet
  python3 -I media_lab.py cut       IN.mp4 OUT.mp4 --start 3.2 --end 7.9      # frame-accurate cut
  python3 -I media_lab.py reframe   IN.mp4 OUT.mp4 --aspect 9:16 [--x 0.5 --y 0.5] [--track]
  python3 -I media_lab.py stabilize IN.mp4 OUT.mp4 [--strength 15]            # handheld phone footage
  python3 -I media_lab.py grade     IN OUT [--look naturel|chaud|chantier|nuit|biteye] [--denoise] [--sharpen]
  python3 -I media_lab.py speed     IN.mp4 OUT.mp4 --factor 0.5 [--smooth]    # slow motion / timelapse
  python3 -I media_lab.py frames    IN.mp4 --out DIR [--every 1.0]            # stills to look at / to use as photos
  python3 -I media_lab.py photo     IN.jpg OUT.jpg [--aspect 4:5 --x 0.5 --y 0.4] [--look naturel] [--max 2160]
  python3 -I media_lab.py cutout    IN.jpg OUT.png                            # remove background (rembg, local)
  python3 -I media_lab.py audio     IN.mp4 OUT.wav                            # soundtrack, for the audio studio

Every command prints a JSON line with the output path(s). Inputs are never modified.
"""
import argparse, json, os, re, subprocess, sys

LOOKS = {
    # gentle correction for phone footage
    'naturel': 'eq=contrast=1.05:saturation=1.08:gamma=1.0,unsharp=5:5:0.4',
    # sunny site, warm tones
    'chaud': 'colortemperature=temperature=5200:mix=0.5,eq=contrast=1.07:saturation=1.12',
    # concrete and steel: punchy mids, a bit desaturated, crisp
    'chantier': 'eq=contrast=1.12:saturation=0.92:gamma=0.97,curves=preset=medium_contrast,unsharp=5:5:0.6',
    # night or dark interior: lift shadows, clean noise
    'nuit': 'hqdn3d=3:3:6:6,eq=gamma=1.25:contrast=1.05:saturation=1.05',
    # house look: neutral, slightly cool, green-teal shadows like the brand
    'biteye': 'eq=contrast=1.08:saturation=1.0,colorbalance=rs=-0.03:gs=0.02:bs=0.03:rh=0.02:bh=-0.02,unsharp=5:5:0.4',
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:], file=sys.stderr)
        sys.exit(r.returncode)
    return r


def probe(path):
    js = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]).stdout)
    v = next((s for s in js['streams'] if s['codec_type'] == 'video'), {})
    w, h = v.get('width', 0), v.get('height', 0)
    rot = abs(int((v.get('tags') or {}).get('rotate', 0) or 0))
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd: rot = abs(int(sd['rotation']))
    if rot in (90, 270): w, h = h, w
    return {'w': w, 'h': h, 'dur': float(js['format'].get('duration') or 0),
            'audio': any(s['codec_type'] == 'audio' for s in js['streams'])}


def enc_video(out):
    if out.lower().endswith('.webm'):
        return ['-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '4']
    return ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']


def crop_expr(w, h, aspect, x, y):
    aw, ah = (float(n) for n in aspect.split(':'))
    if w / h > aw / ah:   # too wide → crop width
        cw, ch = int(h * aw / ah) // 2 * 2, h
    else:
        cw, ch = w, int(w * ah / aw) // 2 * 2
    cx, cy = int((w - cw) * x), int((h - ch) * y)
    return cw, ch, cx, cy


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('shots'); p.add_argument('inp'); p.add_argument('--out', required=True); p.add_argument('--threshold', type=float, default=0.3)
    p = sub.add_parser('cut'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--start', type=float, required=True); p.add_argument('--end', type=float, required=True)
    p = sub.add_parser('reframe'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--aspect', default='9:16')
    p.add_argument('--x', type=float, default=0.5); p.add_argument('--y', type=float, default=0.5); p.add_argument('--to-x', type=float)
    p.add_argument('--size', default=None, help='e.g. 1080x1920')
    p = sub.add_parser('stabilize'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--strength', type=int, default=15)
    p = sub.add_parser('grade'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--look', default='naturel', choices=LOOKS)
    p.add_argument('--denoise', action='store_true'); p.add_argument('--sharpen', action='store_true')
    p = sub.add_parser('speed'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--factor', type=float, required=True); p.add_argument('--smooth', action='store_true')
    p = sub.add_parser('frames'); p.add_argument('inp'); p.add_argument('--out', required=True); p.add_argument('--every', type=float, default=1.0)
    p = sub.add_parser('photo'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--aspect'); p.add_argument('--x', type=float, default=0.5)
    p.add_argument('--y', type=float, default=0.5); p.add_argument('--look', default='naturel', choices=list(LOOKS) + ['aucun']); p.add_argument('--max', type=int, default=2160)
    p = sub.add_parser('cutout'); p.add_argument('inp'); p.add_argument('out')
    p = sub.add_parser('audio'); p.add_argument('inp'); p.add_argument('out')
    a = ap.parse_args()
    res = {'cmd': a.cmd}

    if a.cmd == 'shots':
        os.makedirs(a.out, exist_ok=True)
        info = probe(a.inp)
        err = subprocess.run(['ffmpeg', '-hide_banner', '-i', a.inp, '-vf', f"select='gt(scene,{a.threshold})',showinfo", '-an', '-f', 'null', '-'],
                             capture_output=True, text=True).stderr
        cuts = [0.0] + [round(float(t), 3) for t in re.findall(r'pts_time:([\d.]+)', err) if float(t) > 0.4] + [info['dur']]
        shots = []
        for i, (s, e) in enumerate(zip(cuts, cuts[1:])):
            if e - s < 0.4: continue
            o = os.path.join(a.out, f'plan_{i:02d}.mp4')
            run(['ffmpeg', '-y', '-v', 'error', '-ss', str(s), '-i', a.inp, '-t', str(e - s), *enc_video(o), '-c:a', 'aac', o])
            th = os.path.join(a.out, f'.thumb_{i:02d}.jpg')
            run(['ffmpeg', '-y', '-v', 'error', '-ss', str(s + min(0.5, (e - s) / 2)), '-i', a.inp, '-frames:v', '1', '-vf', 'scale=360:-2', th])
            shots.append({'file': o, 'start': s, 'end': e, 'duration': round(e - s, 2)})
        sheet = os.path.join(a.out, 'plans.jpg')
        cols = min(5, max(1, len(shots)))
        run(['ffmpeg', '-y', '-v', 'error', '-pattern_type', 'glob', '-i', os.path.join(a.out, '.thumb_*.jpg'),
             '-vf', f'tile={cols}x{-(-len(shots) // cols)}:padding=6', '-frames:v', '1', sheet])
        for f in os.listdir(a.out):
            if f.startswith('.thumb_'): os.remove(os.path.join(a.out, f))
        res.update(shots=shots, sheet=sheet)

    elif a.cmd == 'cut':
        run(['ffmpeg', '-y', '-v', 'error', '-ss', str(a.start), '-i', a.inp, '-t', str(a.end - a.start), *enc_video(a.out), '-c:a', 'aac', a.out])
        res['out'] = a.out

    elif a.cmd == 'reframe':
        info = probe(a.inp)
        cw, ch, cx, cy = crop_expr(info['w'], info['h'], a.aspect, a.x, a.y)
        if a.to_x is not None:  # slow pan from x to to_x over the clip
            _, _, cx2, _ = crop_expr(info['w'], info['h'], a.aspect, a.to_x, a.y)
            xexpr = f"'{cx}+({cx2}-{cx})*t/{max(0.1, info['dur'])}'"
        else:
            xexpr = str(cx)
        vf = f'crop={cw}:{ch}:{xexpr}:{cy}'
        if a.size: vf += f",scale={a.size.replace('x', ':')}:flags=lanczos"
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', vf, *enc_video(a.out), '-c:a', 'copy' if a.out.endswith('.mp4') else 'libopus', a.out])
        res.update(out=a.out, crop=[cw, ch, cx, cy])

    elif a.cmd == 'stabilize':
        trf = a.out + '.trf'
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', f'vidstabdetect=shakiness=6:accuracy=12:result={trf}', '-f', 'null', '-'])
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', f'vidstabtransform=input={trf}:smoothing={a.strength}:zoom=2:optzoom=1,unsharp=5:5:0.5',
             *enc_video(a.out), '-c:a', 'copy' if a.out.endswith('.mp4') else 'libopus', a.out])
        os.remove(trf)
        res['out'] = a.out

    elif a.cmd == 'grade':
        vf = ([ 'hqdn3d=2:2:4:4'] if a.denoise else []) + [LOOKS[a.look]] + (['unsharp=5:5:0.8'] if a.sharpen else [])
        is_img = a.inp.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', ','.join(vf)] + (['-q:v', '2'] if is_img else [*enc_video(a.out), '-c:a', 'copy']) + [a.out])
        res['out'] = a.out

    elif a.cmd == 'speed':
        f = a.factor
        vf = f'setpts=PTS/{f}' + (f",minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1" if a.smooth and f < 1 else '')
        tempo, af = f, []
        while tempo > 2: af.append('atempo=2'); tempo /= 2
        while tempo < 0.5: af.append('atempo=0.5'); tempo /= 0.5
        af.append(f'atempo={tempo}')
        cmd = ['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', vf, *enc_video(a.out)]
        cmd += (['-af', ','.join(af), '-c:a', 'aac'] if probe(a.inp)['audio'] else ['-an'])
        run(cmd + [a.out])
        res['out'] = a.out

    elif a.cmd == 'frames':
        os.makedirs(a.out, exist_ok=True)
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', f'fps=1/{a.every}', '-q:v', '2', os.path.join(a.out, 'image_%03d.jpg')])
        res['frames'] = sorted(os.path.join(a.out, f) for f in os.listdir(a.out) if f.startswith('image_'))

    elif a.cmd == 'photo':
        info = probe(a.inp)
        vf = []
        if a.aspect:
            cw, ch, cx, cy = crop_expr(info['w'], info['h'], a.aspect, a.x, a.y)
            vf.append(f'crop={cw}:{ch}:{cx}:{cy}')
        vf.append(f"scale='min({a.max},iw)':-2:flags=lanczos")
        if a.look != 'aucun': vf.append(LOOKS[a.look])
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vf', ','.join(vf), '-frames:v', '1', '-q:v', '2', a.out])
        res['out'] = a.out

    elif a.cmd == 'cutout':
        try:
            from rembg import remove, new_session
        except ImportError:
            print('pip install "rembg[cpu]"  (modèle u2net téléchargé une fois depuis GitHub)', file=sys.stderr); return 2
        sess = new_session('u2net')
        open(a.out, 'wb').write(remove(open(a.inp, 'rb').read(), session=sess))
        res['out'] = a.out

    elif a.cmd == 'audio':
        run(['ffmpeg', '-y', '-v', 'error', '-i', a.inp, '-vn', '-ac', '1', '-ar', '48000', a.out])
        res['out'] = a.out

    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
