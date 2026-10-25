#!/usr/bin/env python3
"""Consommation de la semaine et quota du jour, à partir des journaux locaux de Claude Code.

Lit ~/.claude/projects/**/*.jsonl (session principale, sous-agents, workflows), compte une seule
fois chaque réponse du modèle (message.id), et regroupe par jour (heure d'Alger, UTC+1) et par modèle.

La limite hebdomadaire du compte n'est pas lisible ici : elle est exprimée en pourcentage dans
l'application (/usage). Les « unités » ci-dessous sont un indicateur relatif (base Sonnet = 1) qui pondère
le modèle et le type de jeton. Avec --pct (pourcentage affiché par /usage), l'outil se calibre et
donne le quota restant par jour jusqu'à la réinitialisation.

Exemples :
  python3 conso_hebdo.py --reset "2026-11-01 03:00"
  python3 conso_hebdo.py --reset "2026-11-01 03:00" --pct 38 --json
"""
import argparse
import glob
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

ALGER = timezone(timedelta(hours=1))
# Poids relatifs indicatifs par modèle (Sonnet = 1) et par type de jeton.
MODELE = {"opus": 5.0, "fable": 5.0, "sonnet": 1.0, "haiku": 0.33}
JETON = {"input_tokens": 1.0, "cache_creation_input_tokens": 1.25,
         "cache_read_input_tokens": 0.1, "output_tokens": 5.0}


def poids_modele(nom):
    nom = (nom or "").lower()
    for cle, w in MODELE.items():
        if cle in nom:
            return w
    return 1.0


def lire(racine, debut):
    vus = set()
    par_jour = defaultdict(lambda: defaultdict(float))
    jetons_jour = defaultdict(int)
    for chemin in glob.glob(os.path.join(racine, "**", "*.jsonl"), recursive=True):
        try:
            f = open(chemin, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with f:
            for ligne in f:
                if '"usage"' not in ligne:
                    continue
                try:
                    d = json.loads(ligne)
                except ValueError:
                    continue
                m = d.get("message") or {}
                u = m.get("usage") if isinstance(m, dict) else None
                if not u or not d.get("timestamp"):
                    continue
                cle = m.get("id") or d.get("requestId") or d.get("uuid")
                if cle in vus:
                    continue
                vus.add(cle)
                t = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone(ALGER)
                if t < debut:
                    continue
                jour = t.strftime("%Y-%m-%d")
                w = poids_modele(m.get("model"))
                unites = sum(JETON[k] * (u.get(k) or 0) for k in JETON) * w / 1e6
                par_jour[jour][m.get("model") or "?"] += unites
                jetons_jour[jour] += sum(u.get(k) or 0 for k in JETON)
    return par_jour, jetons_jour


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--reset", required=True, help="prochaine réinitialisation, heure d'Alger : 'AAAA-MM-JJ HH:MM'")
    p.add_argument("--pct", type=float, help="pourcentage hebdomadaire déjà consommé, lu dans /usage")
    p.add_argument("--reserve", type=float, default=10.0, help="pourcentage gardé en réserve pour la fin de semaine")
    p.add_argument("--racine", default=os.path.expanduser("~/.claude/projects"))
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    reset = datetime.strptime(a.reset, "%Y-%m-%d %H:%M").replace(tzinfo=ALGER)
    debut = reset - timedelta(days=7)
    maintenant = datetime.now(ALGER)
    par_jour, jetons = lire(a.racine, debut)
    total = sum(sum(v.values()) for v in par_jour.values())
    aujourd_hui = maintenant.strftime("%Y-%m-%d")
    conso_jour = sum(par_jour.get(aujourd_hui, {}).values())
    jours_restants = max((reset - maintenant).total_seconds() / 86400, 0.01)

    res = {"debut_semaine": debut.isoformat(), "reset": reset.isoformat(),
           "jours_restants": round(jours_restants, 2), "unites_semaine": round(total, 2),
           "unites_aujourdhui": round(conso_jour, 2),
           "par_jour": {j: {"unites": round(sum(v.values()), 2), "jetons": jetons[j],
                            "par_modele": {k: round(x, 2) for k, x in sorted(v.items())}}
                        for j, v in sorted(par_jour.items())}}
    if a.pct is not None and total > 0:
        unite_par_pct = total / max(a.pct, 0.1)
        dispo_pct = max(100 - a.pct - a.reserve, 0)
        quota_jour_pct = dispo_pct / max(jours_restants, 1)
        res.update({"pct_consomme": a.pct, "reserve_pct": a.reserve,
                    "pct_disponible": round(dispo_pct, 1),
                    "quota_jour_pct": round(quota_jour_pct, 1),
                    "quota_jour_unites": round(quota_jour_pct * unite_par_pct, 2),
                    "aujourdhui_pct_estime": round(conso_jour / unite_par_pct, 1)})
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    print(f"Semaine du {debut:%d/%m %H:%M} au {reset:%d/%m %H:%M} (Alger) · {jours_restants:.1f} j restants")
    for j, v in res["par_jour"].items():
        print(f"  {j} : {v['unites']:8.2f} unités · {v['jetons']:>12,} jetons")
    print(f"Total semaine : {total:.2f} unités · aujourd'hui : {conso_jour:.2f}")
    if "quota_jour_pct" in res:
        print(f"Consommé {a.pct:.0f} % · réserve {a.reserve:.0f} % · disponible {res['pct_disponible']} %"
              f" → quota du jour ≈ {res['quota_jour_pct']} % ({res['quota_jour_unites']} unités) ;"
              f" aujourd'hui ≈ {res['aujourdhui_pct_estime']} %")
    else:
        print("Ajoute --pct <pourcentage lu dans /usage> pour calibrer et obtenir le quota du jour.")


if __name__ == "__main__":
    main()
