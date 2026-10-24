#!/usr/bin/env bash
# Version légère WhatsApp (<= 16 Mo) : 1080x1920, 30 i/s, H.264 High, 2 passes 2800 kb/s, AAC 128 kb/s + limiteur -1,6 dBFS (le AAC fait remonter la crête vraie de 0,4 dB), BT.709, +faststart.
# Usage : make_lite.sh entree.mp4 sortie.mp4 [debit_video_kbps]
set -euo pipefail
IN="$1"; OUT="$2"; VK="${3:-2800}"
W=$(mktemp -d)
VF="scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int:in_range=tv:in_color_matrix=bt601:out_color_matrix=bt709:out_range=tv,format=yuv420p"
COMMON=(-map 0:v:0 -vf "$VF" -c:v libx264 -profile:v high -level 4.1 -preset slow -b:v ${VK}k -maxrate $((VK*3/2))k -bufsize $((VK*3))k -r 30 -g 60 -keyint_min 30 -sc_threshold 40 -bf 2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)
ffmpeg -y -v error -i "$IN" "${COMMON[@]}" -pass 1 -passlogfile "$W/p" -an -f mp4 /dev/null
ffmpeg -y -v error -i "$IN" "${COMMON[@]}" -pass 2 -passlogfile "$W/p" -map 0:a:0 -af "alimiter=limit=0.83:attack=2:release=60:level=disabled" -c:a aac -b:a 128k -ar 48000 -ac 2 -shortest -movflags +faststart "$OUT"
rm -rf "$W"
