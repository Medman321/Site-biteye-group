#!/usr/bin/env python3
"""Coupes non prévues dans un MP4 (jump cuts d'une source, saut de plaque) : compare les changements de plan détectés (ffmpeg scene)
aux coupes du storyboard (début de chaque scène et de chaque calque `video`, plus la liste facultative `cuts` du storyboard).
Fonctionne sur l'animatic 360x640 ou sur le MP4 final ; ~10 s pour 40 s de vidéo.
Usage : cut_audit.py video.mp4 storyboard.json [--scene-thr 0.25] [--tol 0.12]
Sortie : une ligne par coupe détectée non prévue (temps, score). Code 1 s'il y en a. Faux positifs possibles sur un flash ou un grand mouvement :
vérifier visuellement la ligne signalée (une image à t-0,05 et t+0,05), pas toute la vidéo."""
import argparse, json, re, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument('mp4'); ap.add_argument('sb')
ap.add_argument('--scene-thr', type=float, default=0.25); ap.add_argument('--tol', type=float, default=0.12)
a = ap.parse_args()
sb = json.load(open(a.sb)); planned = set(sb.get('cuts', []))
for sc in sb['scenes']:
    planned.add(sc['start'])
    for l in sc.get('layers', []):
        if l.get('kind') == 'video': planned.add(l['start'])
r = subprocess.run(['ffmpeg', '-v', 'info', '-i', a.mp4, '-vf', f"scale=270:-2,select='gt(scene,{a.scene_thr})',showinfo", '-an', '-f', 'null', '-'],
                   capture_output=True, text=True)
found = [float(m.group(1)) for m in re.finditer(r'pts_time:([0-9.]+)', r.stderr)]
unplanned = [t for t in found if not any(abs(t - p) <= a.tol for p in planned)]
print('%d changements détectés, %d coupes prévues, %d non prévues' % (len(found), len(planned), len(unplanned)))
for t in unplanned: print('  coupe non prévue à %.2f s' % t)
sys.exit(1 if unplanned else 0)
