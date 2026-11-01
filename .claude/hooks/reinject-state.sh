#!/usr/bin/env bash
# Après un compactage du contexte : réinjecte l'état COURT (etat-en-cours.md, plafonné) et les dernières lignes du budget.
# L'historique (.claude/state/archive/) n'est jamais réinjecté : il se lit par extraits, à la demande.
d="${CLAUDE_PROJECT_DIR:-.}/.claude/state"
[ -f "$d/etat-en-cours.md" ] || exit 0
max=8000
echo "État de travail (source de vérité après compactage) :"
echo
head -c "$max" "$d/etat-en-cours.md"
[ "$(wc -c < "$d/etat-en-cours.md")" -gt "$max" ] && echo && echo "[état tronqué à $max octets : le réécrire plus court]"
if [ -f "$d/budget-hebdo.md" ]; then
  echo; echo "=== budget-hebdo.md (3 dernières lignes) ==="; tail -n 3 "$d/budget-hebdo.md"
fi
