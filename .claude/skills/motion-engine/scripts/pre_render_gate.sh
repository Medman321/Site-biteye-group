#!/usr/bin/env bash
# Porte avant rendu final et avant tout contrôle croisé : mesures déterministes, quelques secondes, zéro jeton de modèle.
# Usage : pre_render_gate.sh <prod> [animatic_ou_mp4] ; échoue (code 1) au premier défaut.
set -u
P="$1"; V="${2:-}"; ME="$(cd "$(dirname "$0")" && pwd)"; ML="$ME/../../media-lab/scripts"; rc=0
echo "== 1. alignement sujet/plaque + tête"; python3 -I "$ML/align_check.py" "$P" --info-gate || rc=1
if [ -n "$V" ]; then
  echo "== 2. coupes non prévues"; python3 -I "$ME/cut_audit.py" "$V" "$P/storyboard.json" || rc=1
  echo "== 3. flux et durée"; ffprobe -v error -show_entries stream=codec_type,width,height,duration -of compact "$V"
  echo "== 4. sonie"; ffmpeg -nostats -i "$V" -af ebur128=peak=true -f null - 2>&1 | grep -E 'I:|Peak:' | tail -n 2
fi
echo "== 5. à faire à la main : layer_diff.py behind (mots derrière la tête) et effect (flou, 2.5D) sur les images clés aux bornes de chaque sujet (t-1, t, t+1 image)"
[ $rc -eq 0 ] && echo "PORTE OK" || echo "PORTE FERMÉE : corriger avant de rendre"
exit $rc
