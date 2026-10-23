#!/usr/bin/env python3
"""Make a phone voice memo sound like a studio recording, with free tools only (ffmpeg + RNNoise).

Usage: python3 -I voice_studio.py IN_AUDIO --out OUT_DIR [--preset voix|chaude|claire|brute]
                                  [--target -14] [--no-gate|--strong-gate] [--no-denoise]

Writes OUT_DIR/voix_studio.wav (48 kHz, 24-bit, for editing), voix_studio.mp3 (for the page),
studio_report.json (loudness and noise floor before/after) and compare.png (spectrograms
before/after, to look at with Read).

Timing is never changed (no silence removal, no time stretch): word timings stay valid.
The chain, in order:
  1. high-pass 75 Hz (rumble, handling noise), low-pass 15 kHz
  2. RNNoise neural denoiser (arnndn), then a light spectral denoise (afftdn) for the residue
  3. de-esser
  4. EQ: less "box" (250 Hz), presence (3 kHz), air (10 kHz shelf); depends on --preset
  5. compressor (steady level, "radio" density)
  6. soft expander between phrases (-10 dB; --strong-gate -18 dB; --no-gate to skip)
  7. two-pass loudness normalisation (EBU R128) to --target LUFS, true-peak -1.5 dBTP
"""
import argparse, json, os, re, subprocess, sys, urllib.request

MODEL_URL = 'https://raw.githubusercontent.com/GregorR/rnnoise-models/master/somnolent-hogwash-2018-09-01/sh.rnnn'
MODEL = os.path.expanduser('~/.cache/biteye-models/rnnoise-sh.rnnn')

PRESETS = {
    # warm, close-mic "studio" voice (default)
    'voix':   'equalizer=f=250:t=q:w=1.2:g=-3,equalizer=f=3200:t=q:w=1.0:g=2.5,treble=g=2:f=10000',
    # deeper, radio-like
    'chaude': 'bass=g=2.5:f=120,equalizer=f=300:t=q:w=1.2:g=-2,equalizer=f=2800:t=q:w=1.0:g=2,treble=g=1.5:f=10000',
    # very intelligible (busy places, small phone speakers)
    'claire': 'equalizer=f=220:t=q:w=1.2:g=-4,equalizer=f=3500:t=q:w=0.9:g=4,treble=g=3:f=9000',
    # clean only, no colour
    'brute':  'anull',
}


def ensure_model():
    if not os.path.exists(MODEL):
        os.makedirs(os.path.dirname(MODEL), exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    return MODEL


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def loudness(path):
    err = run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
    tail = err[err.rfind('Summary:'):]
    g = lambda k: (re.search(k + r':\s+([-\d.]+)', tail) or [None, None])[1]
    return {'lufs': float(g('I') or 0), 'lra': float(g('LRA') or 0), 'true_peak': float(g('Peak') or 0)}


def noise_floor(path):
    """RMS level (dB) of the quietest 10 % of 50 ms windows: the background noise."""
    err = run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'asetnsamples=2400,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level',
               '-f', 'null', '-']).stderr
    v = sorted(float(x) for x in re.findall(r'RMS_level=(-?\d+(?:\.\d+)?)', err))
    return round(v[len(v) // 10], 1) if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--out', required=True)
    ap.add_argument('--preset', default='voix', choices=PRESETS)
    ap.add_argument('--target', type=float, default=-14.0, help='LUFS: -14 réseaux sociaux, -16 site/podcast')
    ap.add_argument('--no-gate', action='store_true', help='garder le bruit de fond entre les phrases')
    ap.add_argument('--strong-gate', action='store_true', help='pièce très bruyante')
    ap.add_argument('--no-denoise', action='store_true')
    ap.add_argument('--denoise-mix', type=float, default=0.85, help='1 = RNNoise plein, plus bas = plus naturel')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    chain = ['aresample=48000', 'pan=mono|c0=0.5*c0+0.5*c1' if probe_channels(a.input) > 1 else 'anull',
             'highpass=f=75:poles=2', 'lowpass=f=15000']
    if not a.no_denoise:
        chain += [f'arnndn=m={ensure_model()}:mix={a.denoise_mix}', 'afftdn=nr=8:nf=-42:tn=1']
    chain += ['deesser=i=0.35:m=0.5:f=0.5', PRESETS[a.preset],
              'acompressor=threshold=-21dB:ratio=3:attack=6:release=90:makeup=2:knee=4']
    if not a.no_gate:
        # downward expander between phrases, so the compressor does not lift the room noise
        chain += ['agate=threshold=0.02:ratio=2.5:range=%s:attack=5:release=220:knee=3' % ('0.12' if a.strong_gate else '0.3')]
    pre = ','.join(c for c in chain if c != 'anull') or 'anull'

    stage1 = os.path.join(a.out, '.stage1.wav')
    r = run(['ffmpeg', '-y', '-v', 'error', '-i', a.input, '-af', pre, '-c:a', 'pcm_s24le', stage1])
    if r.returncode:
        print(r.stderr, file=sys.stderr); return 1

    # two-pass loudnorm: measure, then apply with linear gain
    m = run(['ffmpeg', '-hide_banner', '-i', stage1, '-af', f'loudnorm=I={a.target}:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-']).stderr
    js = json.loads(m[m.rfind('{'):m.rfind('}') + 1])
    ln = (f"loudnorm=I={a.target}:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    wav = os.path.join(a.out, 'voix_studio.wav')
    mp3 = os.path.join(a.out, 'voix_studio.mp3')
    run(['ffmpeg', '-y', '-v', 'error', '-i', stage1, '-af', ln + ',aresample=48000', '-c:a', 'pcm_s24le', wav])
    run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '192k', mp3])
    os.remove(stage1)

    png = os.path.join(a.out, 'compare.png')
    run(['ffmpeg', '-y', '-v', 'error', '-i', a.input, '-i', wav, '-filter_complex',
         '[0:a]aformat=channel_layouts=mono,showspectrumpic=s=1200x300:legend=0:color=intensity[a];'
         '[1:a]aformat=channel_layouts=mono,showspectrumpic=s=1200x300:legend=0:color=intensity[b];[a][b]vstack', png])

    dur = lambda p: float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).stdout or 0)
    rep = {'input': os.path.abspath(a.input), 'output_wav': wav, 'output_mp3': mp3, 'compare': png,
           'preset': a.preset, 'target_lufs': a.target, 'chain': pre,
           'before': dict(loudness(a.input), noise_floor_db=noise_floor(a.input), duration=round(dur(a.input), 3)),
           'after': dict(loudness(wav), noise_floor_db=noise_floor(wav), duration=round(dur(wav), 3))}
    json.dump(rep, open(os.path.join(a.out, 'studio_report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def probe_channels(p):
    out = run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels', '-of', 'csv=p=0', p]).stdout.strip()
    return int(out or 1)


if __name__ == '__main__':
    sys.exit(main())
