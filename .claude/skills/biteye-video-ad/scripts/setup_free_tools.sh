#!/usr/bin/env bash
# Install the free, local toolchain used by the BitEye video agents (once per session/machine).
# ffmpeg and Playwright/Chromium are expected to be present (they are in Claude Code cloud sessions).
set -e
command -v ffmpeg >/dev/null || { echo "ffmpeg manquant : apt-get install -y ffmpeg"; exit 1; }
python3 -c "import sherpa_onnx, numpy" 2>/dev/null || pip install -q sherpa-onnx numpy
python3 -c "import rembg" 2>/dev/null || pip install -q "rembg[cpu]"
M=~/.cache/biteye-models; mkdir -p "$M"
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download
[ -f "$M/rnnoise-sh.rnnn" ] || curl -sSL -o "$M/rnnoise-sh.rnnn" https://raw.githubusercontent.com/GregorR/rnnoise-models/master/somnolent-hogwash-2018-09-01/sh.rnnn
# Whisper turbo (transcription locale) : téléchargé à la première utilisation de transcribe_local.py --asr
# Voix Piper : téléchargées à la première utilisation de voice_tts.py
node -e "require('/opt/node-tools/node_modules/playwright')" 2>/dev/null || node -e "require('playwright')" 2>/dev/null || npm i -g playwright
# Logo et identité visuelle (skills logo-design, canvas-design) : rendu SVG→PNG et polices arabes
python3 -c "import cairosvg" 2>/dev/null || pip install -q cairosvg
command -v rsvg-convert >/dev/null && fc-list | grep -qi 'NotoKufiArabic' || { apt-get install -y -q librsvg2-bin fonts-noto-core fonts-hosny-amiri >/dev/null 2>&1 || { apt-get update -q >/dev/null 2>&1 && apt-get install -y -q librsvg2-bin fonts-noto-core fonts-hosny-amiri >/dev/null 2>&1; }; }
echo "Outils gratuits prêts."
