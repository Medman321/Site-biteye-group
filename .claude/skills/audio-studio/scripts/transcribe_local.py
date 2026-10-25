#!/usr/bin/env python3
"""Free, local word timings for a voice: no ElevenLabs, no account, no credits.

Two modes, same output (words.json in the ElevenLabs format: [{text, type, start, end}]):

  1. Known text (best for darija):  --text FILE.txt   or   --text-string "Khouya, nta promoteur…"
     The text the person actually said is aligned on the audio.
  2. Unknown text:  --asr [--model turbo|small] [--lang fr|ar|en|auto]
     Whisper runs locally (sherpa-onnx, models from GitHub), then its words are aligned.
     Good in French and Arabic; weak on darija written in Latin letters: show the result to the
     requester and re-run with --text once corrected. --lang auto lets Whisper detect the language
     (on the start of each chunk: unreliable on darija mixed with French).
     Music under the voice (ads, reference videos): pauses vanish, so speech regions come from the
     local Silero VAD instead (--vad auto, default: switched on when the noise floor is high).
     Regions are capped at 20 s so Whisper (30 s window) never truncates a chunk.

Alignment: speech regions come from the pauses in the audio; words are spread over speaking
time in proportion to their length, never across a pause, then each boundary snaps to the
nearest dip of loudness (±120 ms). Accuracy is typically ±0.1–0.2 s per word, enough for
word-by-word captions and cues.

Usage: python3 transcribe_local.py AUDIO --out OUT_DIR (--text F | --text-string S | --asr)
Setup once: pip install sherpa-onnx numpy ; models download themselves into ~/.cache/biteye-models.
"""
import argparse, json, os, re, subprocess, sys, tarfile, urllib.request

CACHE = os.path.expanduser('~/.cache/biteye-models')
REL = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/'


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def pcm16k(path):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def speech_regions(path, dur, db=-38, d=0.18):
    err = sh(['ffmpeg', '-hide_banner', '-i', path, '-af', f'silencedetect=n={db}dB:d={d}', '-f', 'null', '-']).stderr
    st = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', err)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    regs, t = [], 0.0
    for a, b in zip(st, en + [dur] * (len(st) - len(en))):
        if a - t > 0.08:
            regs.append([max(0, t), a])
        t = b
    if dur - t > 0.08:
        regs.append([t, dur])
    return regs


def envelope(a, hop=160):
    import numpy as np
    n = len(a) // hop
    return np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)  # 10 ms frames


def env_regions(env, min_pause=0.22):
    """Speech regions from the 10 ms loudness envelope (adapts to the recording level)."""
    import numpy as np
    sm = np.convolve(env, np.ones(5) / 5, mode='same')
    floor, loud = np.percentile(sm, 10), np.percentile(sm, 95)
    thr = max(floor * 3, loud * 0.06)
    on = sm > thr
    regs, i, n = [], 0, len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            regs.append([i / 100, j / 100]); i = j
        else:
            i += 1
    merged = []
    for r in regs:
        if merged and r[0] - merged[-1][1] < min_pause:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [r for r in merged if r[1] - r[0] >= 0.08]


def music_bed(env):
    """True when the quiet frames stay loud (music or constant noise under the voice)."""
    import numpy as np
    sm = np.convolve(env, np.ones(5) / 5, mode='same')
    return float(np.percentile(sm, 10) / (np.percentile(sm, 95) + 1e-12)) > 0.15


def vad_regions(audio, max_len=20):
    """Speech regions from the local Silero VAD (sherpa-onnx): robust to a music bed."""
    import sherpa_onnx
    c = sherpa_onnx.VadModelConfig()
    c.silero_vad.model = os.path.join(CACHE, 'silero_vad.onnx')
    if not os.path.isfile(c.silero_vad.model):
        os.makedirs(CACHE, exist_ok=True)
        urllib.request.urlretrieve(REL + 'silero_vad.onnx', c.silero_vad.model)
    c.silero_vad.threshold, c.silero_vad.min_silence_duration = 0.5, 0.25
    c.silero_vad.min_speech_duration, c.silero_vad.max_speech_duration = 0.1, max_len
    c.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(c, buffer_size_in_seconds=max(60, int(len(audio) / 16000) + 10))
    w = c.silero_vad.window_size
    for i in range(0, len(audio), w):
        vad.accept_waveform(audio[i:i + w])
    vad.flush()
    regs, dur = [], len(audio) / 16000
    while not vad.empty():
        s = vad.front  # the VAD fires late on soft onsets: pad 0.3 s before, 0.15 s after
        a, b = max(0.0, s.start / 16000 - 0.3), min(dur, (s.start + len(s.samples)) / 16000 + 0.15)
        if regs and a <= regs[-1][1]:
            a = regs[-1][1]
        regs.append([round(a, 2), round(b, 2)])
        vad.pop()
    return [r for r in regs if r[1] - r[0] >= 0.08]


def cap_regions(regs, env, max_len=20):
    """Split any region longer than max_len at its quietest 10 ms frame (Whisper reads 30 s)."""
    import numpy as np
    sm = np.convolve(env, np.ones(5) / 5, mode='same')
    out = []
    for a, b in regs:
        while b - a > max_len:
            f0, f1 = int((a + max_len / 2) * 100), min(len(sm), int((a + max_len) * 100))
            cut = (f0 + int(sm[f0:f1].argmin())) / 100 if f1 > f0 else a + max_len
            out.append([a, cut]); a = cut
        out.append([a, b])
    return out


def _split_region(ws, L, a, b, sm):
    """Spread words over one region by length, then snap inner boundaries to loudness dips."""
    tot = sum(L[i] for i in ws)
    t, out = a, []
    for i in ws:
        d = (b - a) * L[i] / tot
        out.append([t, t + d]); t += d
    for k in range(len(out) - 1):
        t = out[k][1]
        f0, f1 = max(1, int((t - 0.15) * 100)), min(len(sm) - 2, int((t + 0.15) * 100))
        if f1 > f0:
            f = f0 + int(sm[f0:f1].argmin())
            t2 = min(max(f / 100, out[k][0] + 0.07), out[k + 1][1] - 0.07)
            out[k][1] = out[k + 1][0] = t2
    return out


def align(words, regs, env):
    """Words → [start, end]. 1) dynamic programming assigns consecutive words to each speech
    region (durations follow word lengths, punctuation prefers a pause after it, a region may
    stay empty: breath or noise); 2) inside a region, words follow their length and snap to
    loudness dips."""
    import numpy as np
    sm = np.convolve(env, np.ones(3) / 3, mode='same')
    L = [max(1, len(re.sub(r'\W', '', x))) + 1.5 for x in words]
    punct = [bool(re.search(r'[.,;:!?؟،]$', x)) for x in words]
    N, R = len(words), len(regs)
    rate = sum(b - a for a, b in regs) / sum(L)
    for _ in range(2):  # second pass with the speech rate of the first alignment
        INF = 1e18
        dp = [[INF] * (N + 1) for _ in range(R + 1)]; bk = [[0] * (N + 1) for _ in range(R + 1)]
        dp[0][0] = 0
        cum = [0]
        for x in L: cum.append(cum[-1] + x)
        for r in range(R):
            dur = regs[r][1] - regs[r][0]
            for j in range(N + 1):
                if dp[r][j] >= INF: continue
                # empty region
                c = dp[r][j] + (0.5 if dur < 0.35 else 3 + dur)
                if c < dp[r + 1][j]: dp[r + 1][j] = c; bk[r + 1][j] = j
                for j2 in range(j + 1, N + 1):
                    exp = (cum[j2] - cum[j]) * rate
                    if exp > dur * 3 + 2: break
                    c = dp[r][j] + ((dur - exp) / (0.3 * max(dur, exp) + 0.2)) ** 2
                    if punct[j2 - 1]: c -= 0.8
                    if j2 < N and punct[j2 - 1] is False and r == R - 1: c += 5
                    if c < dp[r + 1][j2]: dp[r + 1][j2] = c; bk[r + 1][j2] = j
        groups, j = [None] * R, N
        for r in range(R, 0, -1):
            j0 = bk[r][j]; groups[r - 1] = list(range(j0, j)); j = j0
        spoken = sum(regs[r][1] - regs[r][0] for r in range(R) if groups[r])
        rate = spoken / sum(L)
    out = [None] * N
    for r, ws in enumerate(groups):
        if ws:
            for i, se in zip(ws, _split_region(ws, L, regs[r][0], regs[r][1], sm)):
                out[i] = se
    return [[round(a, 2), round(max(b, a + 0.05), 2)] for a, b in out]


def get_model(name):
    d = os.path.join(CACHE, f'sherpa-onnx-whisper-{name}')
    if not os.path.isdir(d):
        os.makedirs(CACHE, exist_ok=True)
        tmp = d + '.tar.bz2'
        urllib.request.urlretrieve(REL + f'sherpa-onnx-whisper-{name}.tar.bz2', tmp)
        with tarfile.open(tmp) as tf:
            tf.extractall(CACHE, filter='data')
        os.remove(tmp)
        for f in os.listdir(d):  # keep only the int8 models
            if f.endswith('.onnx') and '.int8.' not in f or f == 'test_wavs':
                p = os.path.join(d, f)
                (os.remove if os.path.isfile(p) else __import__('shutil').rmtree)(p)
    pre = os.path.join(d, name)
    return pre + '-encoder.int8.onnx', pre + '-decoder.int8.onnx', pre + '-tokens.txt'


def dedupe(ws):
    """Drop Whisper's repetition loops (the same 2-8 words repeated back to back)."""
    out = list(ws)
    for n in range(8, 1, -1):
        i = 0
        while i + 2 * n <= len(out):
            if [w.lower() for w in out[i:i + n]] == [w.lower() for w in out[i + n:i + 2 * n]]:
                del out[i + n:i + 2 * n]
            else:
                i += 1
    return out


def asr(audio, regs, model, lang):
    import sherpa_onnx
    enc, dec, tok = get_model(model)
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=enc, decoder=dec, tokens=tok, language='' if lang == 'auto' else lang, task='transcribe', num_threads=os.cpu_count() or 4)
    # short chunks (≤ 12 s, cut at pauses): Whisper loops less on short inputs
    chunks, cur = [], []
    for r in regs:
        if cur and (r[1] - cur[0][0] > 12 or cur[-1][1] - cur[0][0] > 2.5):
            chunks.append(cur); cur = []
        cur.append(r)
    if cur:
        chunks.append(cur)
    words_all, regs_all = [], []
    for ch in chunks:
        a, b = ch[0][0], ch[-1][1]
        s = rec.create_stream()
        s.accept_waveform(16000, audio[int(a * 16000):int(b * 16000)])
        rec.decode_stream(s)
        ws = dedupe(s.result.text.split())
        words_all.append(ws); regs_all.append(ch)
    return words_all, regs_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('audio')
    ap.add_argument('--out', required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--text'); g.add_argument('--text-string'); g.add_argument('--asr', action='store_true')
    ap.add_argument('--model', default='turbo', choices=['tiny', 'small', 'medium', 'turbo', 'large-v3'])
    ap.add_argument('--lang', default='fr', help='fr, ar, en… or auto (detected by Whisper)')
    ap.add_argument('--vad', default='auto', choices=['auto', 'on', 'off'],
                    help='speech regions from Silero VAD: auto = only under a music bed')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    audio = pcm16k(a.audio)
    dur = len(audio) / 16000
    env = envelope(audio)
    use_vad = a.vad == 'on' or (a.vad == 'auto' and a.asr and music_bed(env))
    regs = cap_regions(vad_regions(audio) if use_vad else env_regions(env), env)
    words, empty = [], []
    if a.asr:
        groups, rgroups = asr(audio, regs, a.model, a.lang)
        for ws, rg in zip(groups, rgroups):
            if ws:
                words += [{'text': t, 'type': 'word', 'start': s, 'end': e} for t, (s, e) in zip(ws, align(ws, rg, env))]
            elif rg[-1][1] - rg[0][0] > 2:
                empty.append([rg[0][0], rg[-1][1]])
        method = f'whisper-{a.model} ({a.lang}) local + alignement' + (' + VAD (musique sous la voix)' if use_vad else '')
    else:
        text = open(a.text, encoding='utf-8').read() if a.text else a.text_string
        ws = text.split()
        words = [{'text': t, 'type': 'word', 'start': s, 'end': e} for t, (s, e) in zip(ws, align(ws, regs, env))]
        method = 'texte fourni + alignement local'
    json.dump(words, open(os.path.join(a.out, 'words.json'), 'w'), ensure_ascii=False, indent=0)
    open(os.path.join(a.out, 'transcript.txt'), 'w', encoding='utf-8').write(' '.join(w['text'] for w in words) + '\n')
    summary = {'method': method, 'words': len(words), 'regions': len(regs), 'duration': round(dur, 2)}
    if words:  # script skeleton cues: first word, speech rate, completeness
        span = words[-1]['end'] - words[0]['start']
        summary.update({'first_word': words[0]['start'], 'last_word_end': words[-1]['end'],
                        'words_per_s': round(len(words) / span, 2) if span > 0 else None})
    if empty:
        summary['chunks_without_words'] = empty  # music only, or speech missed: listen before trusting
    summary.update({'words_json': os.path.join(a.out, 'words.json'), 'text': ' '.join(w['text'] for w in words)})
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
