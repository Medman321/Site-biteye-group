#!/usr/bin/env python3
"""Free local voice-over (Piper voices through sherpa-onnx). No account, no credits.

Usage: python3 voice_tts.py --text-file SCRIPT.txt --out OUT.wav [--voice fr-homme|fr-femme|ar-homme] [--speed 1.0]
       python3 voice_tts.py --text "Khouya, …" --out OUT.wav

One sentence per line in the script gives natural pauses between lines (--pause seconds).
Then run voice_studio.py on the result for the studio finish, and transcribe_local.py --text
on the same script for word timings.
Voices: fr-homme (fr_FR tom), fr-femme (fr_FR siwis), ar-homme (ar_JO kareem, arabe standard).
Darija has no free voice: write it in French or Arabic letters close to the pronunciation,
or record the person (best: a real voice is the strongest human touch).
"""
import argparse, os, sys, tarfile, urllib.request, wave

CACHE = os.path.expanduser('~/.cache/biteye-models')
REL = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/'
VOICES = {'fr-homme': 'vits-piper-fr_FR-tom-medium', 'fr-femme': 'vits-piper-fr_FR-siwis-medium', 'ar-homme': 'vits-piper-ar_JO-kareem-medium'}


def model_dir(name):
    d = os.path.join(CACHE, name)
    if not os.path.isdir(d):
        os.makedirs(CACHE, exist_ok=True)
        tmp = d + '.tar.bz2'
        urllib.request.urlretrieve(REL + name + '.tar.bz2', tmp)
        with tarfile.open(tmp) as tf:
            tf.extractall(CACHE, filter='data')
        os.remove(tmp)
    return d


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--text'); g.add_argument('--text-file')
    ap.add_argument('--out', required=True)
    ap.add_argument('--voice', default='fr-homme', choices=VOICES)
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--pause', type=float, default=0.45)
    a = ap.parse_args()
    import numpy as np, sherpa_onnx
    d = model_dir(VOICES[a.voice])
    onnx = next(os.path.join(d, f) for f in os.listdir(d) if f.endswith('.onnx'))
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(
        model=onnx, tokens=os.path.join(d, 'tokens.txt'), data_dir=os.path.join(d, 'espeak-ng-data')), num_threads=os.cpu_count() or 4))
    tts = sherpa_onnx.OfflineTts(cfg)
    text = a.text if a.text else open(a.text_file, encoding='utf-8').read()
    lines = [l.strip() for l in text.splitlines() if l.strip()] or [text]
    parts, sr = [], 22050
    for l in lines:
        au = tts.generate(l, sid=0, speed=a.speed)
        sr = au.sample_rate
        parts += [np.array(au.samples, dtype=np.float32), np.zeros(int(sr * a.pause), dtype=np.float32)]
    x = np.concatenate(parts)
    with wave.open(a.out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    print({'out': a.out, 'voice': a.voice, 'seconds': round(len(x) / sr, 2), 'lines': len(lines)})


if __name__ == '__main__':
    sys.exit(main())
