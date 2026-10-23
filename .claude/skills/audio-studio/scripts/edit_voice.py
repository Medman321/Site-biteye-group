#!/usr/bin/env python3
"""Shorten a voice: remove time ranges (long pauses, a repeated sentence) and shift the word
timings so captions and cues stay in sync. Free (ffmpeg only).

Usage: python3 -I edit_voice.py VOICE --words words.json --out OUT_DIR
                               [--remove 14.5-15.9,18.1-20.3] [--remove-words 16-18]
                               [--max-pause 0.45] [--idea-pause 0.9] [--keep 17.9-20.3]
                               [--start 0.8] [--end 37.3]

  --remove        time ranges to cut, in seconds
  --remove-words  word index ranges to cut (indices of words.json, inclusive): the cut spans
                  from the end of the previous word to the start of the next one
  --max-pause     breath pauses (inside a sentence) longer than this are shortened to it
  --idea-pause    pauses that close an idea (after . ? ! : or a comma followed by a long gap)
                  keep up to this length: they give the listener time to understand
  --keep          time ranges never cut (a deliberate silence: suspense, a reveal on screen)
  --set-pause     T:LEN,…  give the pause that contains time T exactly LEN seconds
                  (e.g. 14.9:0.7 keeps some suspense before a key word)
  --start/--end   trim the head / tail (keeps 0.15 s of air)
Writes OUT_DIR/voix_montee.wav, OUT_DIR/words.json (shifted) and OUT_DIR/cuts.json.
Each cut gets a 20 ms crossfade, so there is no click.
"""
import argparse, json, os, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('voice'); ap.add_argument('--words', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--remove', default=''); ap.add_argument('--remove-words', default='')
    ap.add_argument('--max-pause', type=float); ap.add_argument('--idea-pause', type=float, default=0.9)
    ap.add_argument('--keep', default=''); ap.add_argument('--set-pause', default=''); ap.add_argument('--start', type=float); ap.add_argument('--end', type=float)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    words = json.load(open(a.words, encoding='utf-8'))
    if isinstance(words, dict): words = words.get('words', [])
    words = [w for w in words if w.get('type', 'word') == 'word']
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.voice],
                               capture_output=True, text=True).stdout)

    cuts = []
    for r in filter(None, a.remove.split(',')):
        s, e = (float(x) for x in r.split('-')); cuts.append([s, e])
    for r in filter(None, a.remove_words.split(',')):
        i, j = (int(x) for x in r.split('-')) if '-' in r else (int(r), int(r))
        s = words[i - 1]['end'] if i > 0 else 0.0
        e = words[j + 1]['start'] if j + 1 < len(words) else dur
        cuts.append([s + 0.05, e - 0.05])
    keeps = [[float(x) for x in r.split('-')] for r in filter(None, a.keep.split(','))]
    pauses = []
    if a.max_pause:
        import re
        for w0, w1 in zip(words, words[1:]):
            gap = w1['start'] - w0['end']
            idea = bool(re.search(r'[.?!:;؟…]$', w0['text'])) or (w0['text'].endswith(',') and gap > 1.0)
            limit = max(a.idea_pause, a.max_pause) if idea else a.max_pause
            kind = 'idée' if idea else 'respiration'
            for sp in filter(None, a.set_pause.split(',')):
                t, ln = (float(x) for x in sp.split(':'))
                if w0['end'] <= t <= w1['start']:
                    limit, kind = ln, 'réglée (--set-pause)'
            if any(k0 < w1['start'] and k1 > w0['end'] for k0, k1 in keeps):
                pauses.append({'after': w0['text'], 'at': w0['end'], 'gap': round(gap, 2), 'type': 'gardée (--keep)', 'kept': round(gap, 2)})
                continue
            if gap > limit:
                cuts.append([w0['end'] + limit / 2, w1['start'] - limit / 2])
            if gap > 0.3:
                pauses.append({'after': w0['text'], 'at': w0['end'], 'gap': round(gap, 2), 'type': kind, 'kept': round(min(gap, limit), 2)})
    if a.start: cuts.append([0, max(0, a.start - 0.15)])
    if a.end: cuts.append([min(dur, a.end + 0.15), dur])
    # merge overlapping cuts
    cuts = sorted([c for c in cuts if c[1] - c[0] > 0.03])
    merged = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], c[1])
        else: merged.append(list(c))
    keep, t = [], 0.0
    for s, e in merged:
        if s > t: keep.append([t, s])
        t = e
    if t < dur: keep.append([t, dur])

    # audio: concatenate kept segments with short crossfades
    parts, labels = [], []
    for k, (s, e) in enumerate(keep):
        parts.append(f'[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[s{k}]'); labels.append(f'[s{k}]')
    if len(labels) == 1:
        fc = parts[0].replace(f'[s0]', '[o]')
    else:
        fc, cur = ';'.join(parts), labels[0]
        for k in range(1, len(labels)):
            nxt = f'[x{k}]' if k < len(labels) - 1 else '[o]'
            fc += f';{cur}{labels[k]}acrossfade=d=0.02:c1=tri:c2=tri{nxt}'; cur = nxt
    wav = os.path.join(a.out, 'voix_montee.wav')
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.voice, '-filter_complex', fc, '-map', '[o]', '-c:a', 'pcm_s24le', wav], capture_output=True, text=True)
    if r.returncode: print(r.stderr, file=sys.stderr); return 1

    # words: drop the ones inside a cut, shift the others
    def shift(t):
        removed = 0.0
        for s, e in merged:
            join = s > 0 and e < dur  # audio on both sides: crossfade overlaps 20 ms more
            if t >= e: removed += (e - s) + (0.02 if join else 0)
            elif t > s: return None
        return round(t - removed, 3)
    out_words, dropped = [], []
    for i, w in enumerate(words):
        s2, e2 = shift(w['start']), shift(w['end'])
        if s2 is None or e2 is None: dropped.append(i); continue
        out_words.append(dict(w, start=s2, end=e2))
    json.dump(out_words, open(os.path.join(a.out, 'words.json'), 'w'), ensure_ascii=False, indent=0)
    new_dur = sum(e - s for s, e in keep) - 0.02 * (len(keep) - 1)
    info = {'voice': wav, 'words': os.path.join(a.out, 'words.json'), 'cuts': merged, 'dropped_words': dropped, 'pauses': pauses,
            'duration_before': round(dur, 2), 'duration_after': round(new_dur, 2)}
    json.dump(info, open(os.path.join(a.out, 'cuts.json'), 'w'), indent=1)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
