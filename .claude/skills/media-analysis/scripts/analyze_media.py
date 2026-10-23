#!/usr/bin/env python3
"""Inspect the media a user hands over for a video: voice memos, music, photos, video clips.

Usage: python3 -I analyze_media.py FILE [FILE ...] --out OUT_DIR

Writes OUT_DIR/analysis.json and, for each visual file, a preview JPEG to look at with Read:
  - photo  → <name>.preview.jpg (max 1024 px)
  - video  → <name>.sheet.jpg (one thumbnail per detected shot, or every few seconds)
For audio (and for the soundtrack of a video) it reports duration, loudness and the pauses
(silences) — the natural cut points for scenes — and writes <name>.speech.mp3, ready to upload
for transcription.
Only ffmpeg/ffprobe are required.
"""
import argparse, json, os, re, subprocess, sys

AUDIO = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.opus', '.flac', '.amr', '.3gp'}
VIDEO = {'.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v'}
IMAGE = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.bmp', '.gif', '.tif', '.tiff'}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = sh(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', path])
    return json.loads(r.stdout or '{}')


def silences(path, db=-35, d=0.35):
    err = sh(['ffmpeg', '-hide_banner', '-i', path, '-af', f'silencedetect=n={db}dB:d={d}', '-vn', '-f', 'null', '-']).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    return [[round(a, 2), round(b, 2)] for a, b in zip(st, en + [None] * (len(st) - len(en))) if b is not None]


def loudness(path):
    err = sh(['ffmpeg', '-hide_banner', '-i', path, '-af', 'volumedetect', '-vn', '-f', 'null', '-']).stderr
    m = re.search(r'mean_volume: ([-\d.]+)', err); x = re.search(r'max_volume: ([-\d.]+)', err)
    return {'mean_db': float(m.group(1)) if m else None, 'max_db': float(x.group(1)) if x else None}


def speech_segments(sil, dur):
    """Spans where someone is speaking, between pauses."""
    segs, t = [], 0.0
    for a, b in sil:
        if a - t > 0.15:
            segs.append([round(t, 2), round(a, 2)])
        t = b
    if dur - t > 0.15:
        segs.append([round(t, 2), round(dur, 2)])
    return segs


def avg_color(path):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', 'scale=1:1', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
    return '#%02X%02X%02X' % tuple(r.stdout[:3]) if len(r.stdout) >= 3 else None


def shots(path, dur, thr=0.32):
    err = sh(['ffmpeg', '-hide_banner', '-i', path, '-vf', f"select='gt(scene,{thr})',showinfo", '-an', '-f', 'null', '-']).stderr
    cuts = [round(float(x), 2) for x in re.findall(r'pts_time:([\d.]+)', err)]
    return [0.0] + [c for c in cuts if c > 0.3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report = []
    for f in a.files:
        name = os.path.splitext(os.path.basename(f))[0]
        ext = os.path.splitext(f)[1].lower()
        info = probe(f)
        streams = info.get('streams', [])
        v = next((s for s in streams if s.get('codec_type') == 'video'), None)
        au = next((s for s in streams if s.get('codec_type') == 'audio'), None)
        dur = float(info.get('format', {}).get('duration') or 0)
        item = {'file': os.path.abspath(f), 'size_mb': round(os.path.getsize(f) / 1e6, 2)}
        kind = 'audio' if ext in AUDIO or (au and not v) else 'image' if ext in IMAGE or (v and dur < 0.1) else 'video' if v else 'unknown'
        item['kind'] = kind
        if kind == 'image':
            w, h = v['width'], v['height']
            rot = abs(int((v.get('tags') or {}).get('rotate', 0) or 0))
            if rot in (90, 270): w, h = h, w
            item.update(width=w, height=h, orientation='portrait' if h > w else 'landscape' if w > h else 'square', avg_color=avg_color(f))
            prev = os.path.join(a.out, name + '.preview.jpg')
            sh(['ffmpeg', '-y', '-v', 'error', '-i', f, '-vf', "scale='min(1024,iw)':-2", '-frames:v', '1', prev])
            item['preview'] = prev
        if kind == 'video':
            w, h = v['width'], v['height']
            rot = abs(int((v.get('tags') or {}).get('rotate', 0) or 0))
            for sd in v.get('side_data_list', []) or []:
                if 'rotation' in sd: rot = abs(int(sd['rotation']))
            if rot in (90, 270): w, h = h, w
            fr = v.get('avg_frame_rate', '0/1').split('/')
            item.update(width=w, height=h, duration=round(dur, 2), fps=round(int(fr[0]) / max(1, int(fr[1])), 2),
                        orientation='portrait' if h > w else 'landscape' if w > h else 'square', has_audio=bool(au))
            cuts = shots(f, dur)
            if len(cuts) < 3:
                step = max(1.0, dur / 8)
                cuts = [round(i * step, 2) for i in range(int(dur // step) + 1) if i * step < dur - 0.2]
            item['shots'] = cuts[:24]
            thumbs = []
            for i, t in enumerate(item['shots']):
                tp = os.path.join(a.out, f'.{name}_{i:02d}.jpg')
                sh(['ffmpeg', '-y', '-v', 'error', '-ss', str(t + 0.2), '-i', f, '-frames:v', '1', '-vf', 'scale=360:-2', tp])
                thumbs.append(tp)
            sheet = os.path.join(a.out, name + '.sheet.jpg')
            cols = min(6, len(thumbs))
            sh(['ffmpeg', '-y', '-v', 'error', '-pattern_type', 'glob', '-i', os.path.join(a.out, f'.{name}_*.jpg'),
                '-vf', f'tile={cols}x{-(-len(thumbs) // cols)}:padding=6', '-frames:v', '1', sheet])
            for tp in thumbs:
                os.remove(tp)
            item['sheet'] = sheet
        if kind in ('audio', 'video') and au:
            sil = silences(f)
            item.update(duration=round(dur, 2), loudness=loudness(f), silences=sil, speech=speech_segments(sil, dur))
            sp = os.path.join(a.out, name + '.speech.mp3')
            sh(['ffmpeg', '-y', '-v', 'error', '-i', f, '-vn', '-ac', '1', '-ar', '44100', '-b:a', '128k', sp])
            item['speech_file'] = sp
            item['speech_file_bytes'] = os.path.getsize(sp)
        report.append(item)
    out = os.path.join(a.out, 'analysis.json')
    json.dump(report, open(out, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
