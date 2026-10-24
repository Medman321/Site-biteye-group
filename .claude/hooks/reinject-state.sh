#!/usr/bin/env bash
# Après un compactage du contexte : réinjecte l'état de travail sauvegardé (.claude/state/*.md, hors Git).
d="${CLAUDE_PROJECT_DIR:-.}/.claude/state"
ls "$d"/*.md >/dev/null 2>&1 || exit 0
echo "État de travail sauvegardé avant le compactage (source de vérité, à relire) :"
for f in "$d"/*.md; do echo; echo "=== $(basename "$f") ==="; cat "$f"; done
