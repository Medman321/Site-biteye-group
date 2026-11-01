#!/usr/bin/env python3
"""Contrôle des textes publiés (légende, commentaire épinglé, cartons) : sortie vide exigée.

Usage :
    python3 -I texte_controle.py legende.md cartons.txt [--mot-code "FORMATION 1"]
    python3 -I texte_controle.py --self-test

Signale (une ligne `fichier:ligne: code : message` par constat, code retour 1) :
- invisible    : caractères invisibles (U+200B, U+200C, U+200D hors emoji, U+2060, U+FEFF,
                 U+00AD, U+E0000 à U+E007F) ;
- cadratin     : tiret cadratin (U+2014) employé comme pause (hors début de ligne) ;
- puce         : ligne qui commence par un emoji ou une flèche en guise de puce ;
- gras         : gras partout (plus de 5 passages en gras, ou plus de 20 % du texte) ;
- majuscules   : ligne de 4 mots ou plus dont presque chaque mot commence par une majuscule ;
- hashtags     : plus de 5 hashtags dans un même fichier ;
- mot-code     : espace insécable (U+00A0, U+202F) à l'intérieur d'un mot-code : il doit se
                 recopier à l'identique (après « commentez », ou avec --mot-code).
L'espace insécable française avant « : ; ! ? » et dans les guillemets est conservée.
Les seuils sont des valeurs de départ. Python standard uniquement.
"""
import argparse
import re
import sys

SEUIL_HASHTAGS = 5
SEUIL_GRAS_PASSAGES = 5
SEUIL_GRAS_PART = 0.20
SEUIL_MAJUSCULES = 0.8
INSECABLES = "\u00a0\u202f"
FLECHES = set("→⇒➡➔➜➤►▶▸➢⟶↳↪⬅⬆⬇↑↓←↔")
PUCES_SYMBOLES = set("✅✔✓✗✘❌☑✳✴❇⭐★☆👉👇👆👈")


def est_emoji(c):
    cp = ord(c)
    return (0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF
            or 0x2300 <= cp <= 0x23FF or cp in (0xFE0F, 0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122))


def est_invisible(c, avant, apres):
    cp = ord(c)
    if cp in (0x200B, 0x200C, 0x2060, 0xFEFF, 0x00AD) or 0xE0000 <= cp <= 0xE007F:
        return True
    if cp == 0x200D:
        return not (est_emoji(avant) and est_emoji(apres))
    return False


def controle_texte(texte, nom="texte", mot_code=None):
    constats = []

    def ajoute(ligne, code, message):
        constats.append(f"{nom}:{ligne}: {code} : {message}")

    lignes = texte.split("\n")
    for numero, ligne in enumerate(lignes, start=1):
        for i, c in enumerate(ligne):
            avant = ligne[i - 1] if i > 0 else ""
            apres = ligne[i + 1] if i + 1 < len(ligne) else ""
            if est_invisible(c, avant, apres):
                ajoute(numero, "invisible", f"caractère U+{ord(c):04X} à la colonne {i + 1}")
        for m in re.finditer("—", ligne):
            if ligne[: m.start()].strip():
                ajoute(numero, "cadratin", "tiret cadratin utilisé comme pause (virgule, point ou deux-points)")
                break
        debut = ligne.lstrip()
        if debut and (debut[0] in FLECHES or debut[0] in PUCES_SYMBOLES
                      or (est_emoji(debut[0]) and debut[0] != "️")):
            ajoute(numero, "puce", f"puce en emoji ou en flèche ({debut[0]})")
        mots = [w for w in re.findall(r"[^\W\d_]{3,}", ligne) if not w.startswith("#")]
        if (len(ligne.split()) >= 4 and len(mots) >= 4 and not ligne.lstrip().startswith("#")
                and ligne.upper() != ligne):
            majuscules = sum(1 for w in mots if w[0].isupper())
            if majuscules / len(mots) >= SEUIL_MAJUSCULES:
                ajoute(numero, "majuscules", "majuscule à presque chaque mot : écrire en phrase")

    gras = re.findall(r"\*\*(.+?)\*\*|__(.+?)__", texte, flags=re.S)
    passages = [a or b for a, b in gras]
    visible = len(re.sub(r"\s", "", texte))
    if passages:
        part = sum(len(re.sub(r"\s", "", p)) for p in passages) / max(visible, 1)
        if len(passages) > SEUIL_GRAS_PASSAGES or part > SEUIL_GRAS_PART:
            ajoute(1, "gras", f"gras partout ({len(passages)} passages, {part:.0%} du texte)")

    hashtags = re.findall(r"(?<![\w#])#(?=[^\W\d_])\w+", texte)
    if len(hashtags) > SEUIL_HASHTAGS:
        ajoute(1, "hashtags", f"{len(hashtags)} hashtags (5 au plus)")

    separateur = r"[ \t" + INSECABLES + r"]+"
    motifs = []
    if mot_code:
        motifs.append(separateur.join(re.escape(j) for j in mot_code.split()))
    motifs.append(r"(?i:commentez)[ \t" + INSECABLES + r"]+((?:[A-ZÀ-Ý0-9]+[ \t" + INSECABLES + r"]?)+)")
    for motif in motifs:
        for m in re.finditer(motif, texte):
            extrait = m.group(1) if m.groups() else m.group(0)
            if any(c in extrait for c in INSECABLES):
                numero = texte.count("\n", 0, m.start()) + 1
                ajoute(numero, "mot-code", f"espace insécable dans le mot-code « {extrait.strip()} »")
    return constats


def self_test():
    echecs = []

    def codes(texte, **kw):
        return {c.split(": ", 1)[1].split(" :")[0] for c in controle_texte(texte, **kw)}

    def verifie(nom, condition):
        if not condition:
            echecs.append(nom)

    verifie("propre", controle_texte("Commentez FORMATION 1 pour recevoir la présentation.\n"
                                     "Un logiciel pensé pour les promoteurs.") == [])
    verifie("insécable française gardée", controle_texte("Prêt à démarrer\u00a0? « Oui »\u202f!") == [])
    verifie("zéro largeur", codes("Bon\u200bjour") == {"invisible"})
    verifie("césure invisible", codes("pro\u00admoteur") == {"invisible"})
    verifie("BOM", codes("\ufeffBonjour") == {"invisible"})
    verifie("balise emoji", codes("Salut \U000E0041") == {"invisible"})
    verifie("ZWJ dans un emoji accepté", codes("Équipe \U0001F468\u200d\U0001F4BB au travail") == set())
    verifie("ZWJ isolé", codes("mot\u200dmot") == {"invisible"})
    verifie("cadratin pause", codes("Le chantier — enfin sous contrôle") == {"cadratin"})
    verifie("cadratin début de ligne accepté", codes("— Bonjour, dit-il.") == set())
    verifie("puce flèche", codes("→ Un tableau de bord") == {"puce"})
    verifie("puce emoji", codes("✅ Échéancier suivi") == {"puce"})
    verifie("gras partout", codes(" ".join(f"**mot{i}**" for i in range(7))) == {"gras"})
    verifie("gras rare accepté", codes("Un seul **mot** en gras dans une longue phrase de légende.") == set())
    verifie("majuscules", codes("Suivi Des Échéances Pour Les Promoteurs") == {"majuscules"})
    verifie("majuscules : phrase normale", codes("Suivi des échéances pour les promoteurs") == set())
    verifie("majuscules : code seul", codes("COMMENTEZ FORMATION 1 MAINTENANT") == set())
    verifie("6 hashtags", codes("#a1 #b2 #c3 #d4 #e5 #f6") == {"hashtags"})
    verifie("5 hashtags", codes("#a1 #b2 #c3 #d4 #e5") == set())
    verifie("titre markdown n'est pas un hashtag", codes("# Titre\n## Sous-titre") == set())
    verifie("mot-code insécable après commentez", codes("Commentez FORMATION\u00a01 ici") == {"mot-code"})
    verifie("mot-code insécable avec --mot-code", codes("Écris TÉMOIGNAGE\u202f2 en commentaire",
                                                         mot_code="TÉMOIGNAGE 2") == {"mot-code"})
    verifie("mot-code propre", codes("Commentez TÉMOIGNAGE 2 ici", mot_code="TÉMOIGNAGE 2") == set())
    verifie("texte vide", controle_texte("") == [])

    if echecs:
        print("ÉCHEC :", "; ".join(echecs))
        return 1
    print("auto-test : 24 cas passés")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fichiers", nargs="*", help="fichiers texte à contrôler")
    ap.add_argument("--mot-code", help="mot-code de la vidéo, ex. « FORMATION 1 »")
    ap.add_argument("--self-test", action="store_true", help="vérifie le script sur des cas de test")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.fichiers:
        ap.error("au moins un fichier texte est requis (ou --self-test)")
    constats = []
    for chemin in args.fichiers:
        with open(chemin, encoding="utf-8", newline="") as f:
            constats += controle_texte(f.read().replace("\r\n", "\n"), chemin, args.mot_code)
    for c in constats:
        print(c)
    return 1 if constats else 0


if __name__ == "__main__":
    sys.exit(main())
