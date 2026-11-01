#!/usr/bin/env python3
"""Médiane par format et posts hors norme d'un relevé de comptes (veille concurrents).

Usage :
    python3 -I mediane_hors_norme.py releve.csv --date AAAA-MM-JJ
    python3 -I mediane_hors_norme.py --self-test

Le CSV suit le gabarit de `marketing-research` §2 bis :
    lien,date,format,duree_s,vues,jaime,commentaires,hook,cta
Colonnes facultatives : compte, sponsorise, concours (valeur oui / 1 / vrai pour exclure).

Règles (valeurs de départ, à ajuster avec le demandeur) :
- fenêtre : posts publiés il y a 7 à 180 jours avant --date ; filtre sur la date de
  publication, jamais sur la place dans la grille (un post épinglé peut être ancien) ;
- sponsorisés et concours exclus (colonnes facultatives) ;
- médiane par format sur la colonne `vues` ; moins de 6 posts : « non calculé » ;
  6 à 9 : confiance faible ; 10 et plus : confiance normale ;
- multiple = vues ÷ médiane ; niveaux : x2 hors norme, x3 fort, x5 exceptionnel ;
- valeur absente ou illisible (« 12 K », compteur arrondi) : « n/d », jamais 0 ;
- couverture = posts mesurés ÷ posts relevés dans la fenêtre ;
- confiance du relevé : faible sous 5 hors-norme, moyenne de 5 à 9, élevée à partir de 10 ;
- au plus 2 pistes par compte (si la colonne `compte` existe) ; un post qui répète le hook
  d'un plus ancien du même compte : on garde l'original.

Python standard uniquement, aucune dépendance. Aucun calcul de tête au-delà de 6 posts.
"""
import argparse
import csv
import io
import re
import statistics
import sys
from datetime import date, datetime

FENETRE_MIN = 7
FENETRE_MAX = 180
MIN_CALCUL = 6
MIN_CONFIANCE = 10
OUI = {"oui", "o", "1", "vrai", "true", "yes", "x"}
NA = "n/d"


def parse_date(texte):
    texte = (texte or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texte, fmt).date()
        except ValueError:
            pass
    return None


def parse_nombre(texte):
    """Entier lisible ou None. « 12 400 » passe ; « 12,4 K » ou vide : n/d."""
    texte = (texte or "").strip()
    if not texte or texte.lower() in {"n/d", "nd", "-", "?"}:
        return None
    nettoye = re.sub(r"[ \u00a0\u202f.]", "", texte)
    return int(nettoye) if nettoye.isdigit() else None


def niveau(multiple):
    if multiple >= 5:
        return "x5 exceptionnel"
    if multiple >= 3:
        return "x3 fort"
    if multiple >= 2:
        return "x2 hors norme"
    return ""


def lire(contenu, ref):
    """Retourne (posts dans la fenêtre, écartés avec raison)."""
    lecteur = csv.DictReader(io.StringIO(contenu))
    posts, ecartes = [], []
    for i, ligne in enumerate(lecteur, start=2):
        ligne = {(k or "").strip().lower(): (v or "").strip() for k, v in ligne.items()}
        d = parse_date(ligne.get("date"))
        lien = ligne.get("lien") or f"ligne {i}"
        if d is None:
            ecartes.append((lien, "date illisible"))
            continue
        age = (ref - d).days
        if age < FENETRE_MIN:
            ecartes.append((lien, f"trop récent ({age} j)"))
            continue
        if age > FENETRE_MAX:
            ecartes.append((lien, f"trop ancien ({age} j)"))
            continue
        if ligne.get("sponsorise", "").lower() in OUI:
            ecartes.append((lien, "sponsorisé"))
            continue
        if ligne.get("concours", "").lower() in OUI:
            ecartes.append((lien, "concours"))
            continue
        posts.append({
            "lien": lien, "date": d, "age": age,
            "format": (ligne.get("format") or NA).lower(),
            "compte": ligne.get("compte", ""),
            "vues": parse_nombre(ligne.get("vues")),
            "hook": ligne.get("hook", ""),
            "cta": ligne.get("cta", ""),
        })
    return posts, ecartes


def analyser(contenu, ref):
    posts, ecartes = lire(contenu, ref)
    formats = {}
    for p in posts:
        formats.setdefault(p["format"], []).append(p)

    # doublons de hook : on garde le plus ancien du même compte
    vus = {}
    for p in sorted(posts, key=lambda x: x["date"]):
        cle = (p["compte"].lower(), re.sub(r"\W+", " ", p["hook"].lower()).strip())
        p["doublon"] = bool(cle[1]) and cle in vus
        vus.setdefault(cle, p["lien"])

    resume = {}
    nb_hors_norme = 0
    for nom, liste in formats.items():
        mesures = [p for p in liste if p["vues"] is not None]
        n = len(mesures)
        mediane = statistics.median([p["vues"] for p in mesures]) if n else None
        if n < MIN_CALCUL:
            statut = "non calculé"
        elif n < MIN_CONFIANCE:
            statut = "confiance faible"
        else:
            statut = "confiance normale"
        calcule = statut != "non calculé" and mediane is not None
        for p in liste:
            p["multiple"] = None
            p["niveau"] = ""
            if calcule and p["vues"] is not None and mediane > 0:
                p["multiple"] = p["vues"] / mediane
                p["niveau"] = niveau(p["multiple"])
                if p["niveau"] and not p["doublon"]:
                    nb_hors_norme += 1
        resume[nom] = {
            "relevés": len(liste), "mesurés": n,
            "médiane": mediane if calcule else None,
            "statut": statut,
            "médiane_nulle": calcule and mediane == 0,
        }
    if nb_hors_norme >= 10:
        confiance = "élevée"
    elif nb_hors_norme >= 5:
        confiance = "moyenne"
    else:
        confiance = "faible"
    return posts, ecartes, resume, nb_hors_norme, confiance


def rapport(contenu, ref):
    posts, ecartes, resume, nb, confiance = analyser(contenu, ref)
    sortie = [f"Relevé au {ref.isoformat()} : fenêtre {FENETRE_MIN} à {FENETRE_MAX} jours"]
    total = len(posts)
    mesures = sum(1 for p in posts if p["vues"] is not None)
    if total == 0:
        sortie.append("Aucun post dans la fenêtre : rien à calculer.")
    else:
        sortie.append(f"Couverture : {mesures} mesurés sur {total} relevés ({mesures * 100 // total} %)")
        sortie.append("")
        sortie.append("| Format | Relevés | Mesurés (n) | Médiane des vues | Statut |")
        sortie.append("|---|---|---|---|---|")
        for nom, r in sorted(resume.items()):
            med = NA if r["médiane"] is None else f"{r['médiane']:.0f}"
            statut = r["statut"] + (" ; médiane nulle, multiples n/d" if r["médiane_nulle"] else "")
            sortie.append(f"| {nom} | {r['relevés']} | {r['mesurés']} | {med} | {statut} |")
        sortie.append("")
        sortie.append("| Post | Format | Vues | Multiple | Niveau | Note |")
        sortie.append("|---|---|---|---|---|---|")
        par_compte = {}
        ordre = sorted(posts, key=lambda p: (-(p["multiple"] or 0), p["lien"]))
        for p in ordre:
            if not p["niveau"]:
                continue
            note = ""
            if p["doublon"]:
                note = "même hook qu'un post plus ancien : on garde l'original"
            else:
                k = p["compte"].lower()
                if k and par_compte.get(k, 0) >= 2:
                    note = "au-delà de 2 pistes pour ce compte"
                else:
                    par_compte[k] = par_compte.get(k, 0) + 1
            vues = NA if p["vues"] is None else str(p["vues"])
            sortie.append(f"| {p['lien']} | {p['format']} | {vues} | x{p['multiple']:.1f} | {p['niveau']} | {note} |")
        sortie.append("")
        sortie.append(f"Posts hors norme : {nb} ; confiance du relevé : {confiance}. "
                      "Un hors-norme reste une hypothèse (tendance, collaboration, publicité non déclarée).")
    if ecartes:
        sortie.append("")
        sortie.append("Écartés : " + " ; ".join(f"{lien} ({raison})" for lien, raison in ecartes))
    return "\n".join(sortie)


def _csv(lignes):
    return "lien,date,format,duree_s,vues,jaime,commentaires,hook,cta\n" + "\n".join(lignes) + "\n"


def self_test():
    ref = date(2026, 10, 27)
    echecs = []

    def verifie(nom, condition):
        if not condition:
            echecs.append(nom)

    # 1. fichier vide (en-tête seul) : pas de plantage
    _, _, resume, nb, conf = analyser(_csv([]), ref)
    verifie("vide : aucun format", resume == {} and nb == 0 and conf == "faible")
    verifie("vide : rapport", "Aucun post" in rapport(_csv([]), ref))

    # 2. petit échantillon : 3 posts -> « non calculé », aucun multiple
    petit = _csv([f"p{i},2026-09-0{i},reel,20,{100 * i},1,1,h{i},c" for i in range(1, 4)])
    posts, _, resume, _, _ = analyser(petit, ref)
    verifie("petit : non calculé", resume["reel"]["statut"] == "non calculé")
    verifie("petit : pas de multiple", all(p["multiple"] is None for p in posts))

    # 3. 6 posts : calcul, confiance faible ; médiane 1000 ; un post à 5000 = x5
    six = _csv([f"p{i},2026-09-0{i},reel,20,1000,1,1,h{i},c" for i in range(1, 6)]
               + ["p6,2026-09-06,reel,20,5000,1,1,h6,c"])
    posts, _, resume, nb, conf = analyser(six, ref)
    verifie("six : confiance faible", resume["reel"]["statut"] == "confiance faible")
    verifie("six : médiane", resume["reel"]["médiane"] == 1000)
    verifie("six : x5", [p for p in posts if p["lien"] == "p6"][0]["niveau"] == "x5 exceptionnel")
    verifie("six : relevé faible", nb == 1 and conf == "faible")

    # 4. médiane nulle : pas de division par zéro
    zero = _csv([f"p{i},2026-09-0{i},reel,20,0,1,1,h{i},c" for i in range(1, 6)]
                + ["p6,2026-09-06,reel,20,900,1,1,h6,c"])
    posts, _, resume, _, _ = analyser(zero, ref)
    verifie("zéro : médiane nulle signalée", resume["reel"]["médiane_nulle"])
    verifie("zéro : multiples absents", all(p["multiple"] is None for p in posts))

    # 5. fenêtre : 3 jours et 200 jours écartés, 7 jours gardé
    fen = _csv(["a,2026-10-24,reel,20,10,1,1,h,c",
                "b,2026-04-10,reel,20,10,1,1,h,c",
                "c,2026-10-20,reel,20,10,1,1,h,c"])
    posts, ecartes, _, _, _ = analyser(fen, ref)
    verifie("fenêtre : 1 gardé", [p["lien"] for p in posts] == ["c"])
    verifie("fenêtre : 2 écartés", len(ecartes) == 2)

    # 6. valeur absente ou arrondie : n/d, jamais 0
    nd = _csv(["a,2026-09-01,reel,20,,1,1,h,c", "b,2026-09-02,reel,20,12 K,1,1,h,c",
               "c,2026-09-03,reel,20,12 400,1,1,h,c"])
    posts, _, _, _, _ = analyser(nd, ref)
    vues = {p["lien"]: p["vues"] for p in posts}
    verifie("n/d : vide", vues["a"] is None)
    verifie("n/d : compteur arrondi", vues["b"] is None)
    verifie("n/d : espace des milliers", vues["c"] == 12400)
    verifie("n/d : couverture", "1 mesurés sur 3" in rapport(nd, ref))

    # 7. sponsorisé exclu, colonne facultative
    spons = ("lien,date,format,vues,sponsorise\n"
             "a,2026-09-01,reel,100,oui\nb,2026-09-02,reel,100,non\n")
    posts, ecartes, _, _, _ = analyser(spons, ref)
    verifie("sponsorisé exclu", [p["lien"] for p in posts] == ["b"] and ecartes[0][1] == "sponsorisé")

    # 8. confiance du relevé : 10 hors-norme -> élevée
    gros = _csv([f"p{i:02d},2026-09-01,reel,20,1000,1,1,h{i},c" for i in range(1, 22)]
                + [f"q{i:02d},2026-09-02,reel,20,9000,1,1,hq{i},c" for i in range(1, 11)])
    _, _, _, nb, conf = analyser(gros, ref)
    verifie("confiance élevée", conf == "élevée" and nb >= 10)

    # 9. doublon de hook : on garde le plus ancien
    dbl = _csv([f"p{i},2026-09-0{i},reel,20,1000,1,1,h{i},c" for i in range(1, 6)]
               + ["o,2026-08-01,reel,20,4000,1,1,même hook,c",
                  "n,2026-09-09,reel,20,4000,1,1,Même hook,c"])
    posts, _, _, _, _ = analyser(dbl, ref)
    par = {p["lien"]: p for p in posts}
    verifie("doublon : original gardé", not par["o"]["doublon"] and par["n"]["doublon"])

    if echecs:
        print("ÉCHEC :", "; ".join(echecs))
        return 1
    print("auto-test : 9 groupes de cas passés")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("csv", nargs="?", help="relevé CSV (gabarit de marketing-research §2 bis)")
    ap.add_argument("--date", help="date du relevé, AAAA-MM-JJ (défaut : aujourd'hui)")
    ap.add_argument("--self-test", action="store_true", help="vérifie le script sur des cas de test")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.csv:
        ap.error("fichier CSV requis (ou --self-test)")
    ref = parse_date(args.date) if args.date else date.today()
    if ref is None:
        ap.error("--date attendu au format AAAA-MM-JJ")
    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        contenu = f.read()
    print(rapport(contenu, ref))
    return 0


if __name__ == "__main__":
    sys.exit(main())
