#!/usr/bin/env bash
# Porte avant rendu final et avant tout contrôle croisé : mesures déterministes, quelques secondes, zéro jeton de modèle.
# Usage : pre_render_gate.sh <prod> [animatic_ou_mp4] ; échoue (code 1) au premier défaut.
# V4 : si une page <prod>/out/*.local.html (ou <prod>/*.local.html, ou $HTML) existe, contrôle de la page par render.js
#      (image 0, zones sûres, tailles minimales, police réellement rendue, sorties de scène) avec --strict.
set -u
P="$1"; V="${2:-}"; ME="$(cd "$(dirname "$0")" && pwd)"; ML="$ME/../../media-lab/scripts"; rc=0
echo "== 1. alignement sujet/plaque + tête"; python3 -I "$ML/align_check.py" "$P" --info-gate || rc=1
if [ -n "$V" ]; then
  echo "== 2. coupes non prévues"; python3 -I "$ME/cut_audit.py" "$V" "$P/storyboard.json" || rc=1
  echo "== 3. flux et durée (images, durée, piste son)"; ffprobe -v error -count_frames -show_entries stream=codec_type,width,height,duration,nb_read_frames -of compact "$V"
  echo "== 4. sonie (cible −14 LUFS, pic réel ≤ −1 dBTP)"; ffmpeg -nostats -i "$V" -af ebur128=peak=true -f null - 2>&1 | grep -E 'I:|Peak:' | tail -n 2
fi
HTML="${HTML:-$(ls "$P"/out/*.local.html "$P"/*.local.html 2>/dev/null | head -n 1)}"
if [ -n "$HTML" ]; then
  echo "== 5. page : image 0, zones sûres, tailles, polices, sorties de scène ($HTML)"
  node "$ME/render.js" "$HTML" --stills "$P/porte-stills" --fonts --scene-exits --strict > "$P/porte-stills.json"; c=$?
  python3 -I -c "import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps({k: d.get(k) for k in ('image0','hors_zone','taille_min','fonts','errors')}, ensure_ascii=False)[:3000]); print('sorties de scène KO :', [r['scene'] for r in d.get('scene_exits', []) if not r['ok']])" "$P/porte-stills.json"
  [ $c -eq 0 ] || rc=1
fi
echo "== 6. à faire à la main : layer_diff.py behind (mots derrière la tête) et effect (flou, 2.5D) sur les images clés aux bornes de chaque sujet (t-1, t, t+1 image)"
[ $rc -eq 0 ] && echo "PORTE OK" || echo "PORTE FERMÉE : corriger avant de rendre"
exit $rc
