---
name: bibliotheque-techniques
description: Bibliothèque des techniques de montage et de publicité tirées des vidéos de référence choisies par BitEye (dossier Drive « Vidéos pour apprentissage ») — accroches, rythme, transitions, présentation du produit, texte à l'écran, son, CTA — chacune avec sa transposition à VISION Workspace. À lire au moment du concept et du storyboard ; à enrichir à chaque nouvelle vidéo de référence.
---

# Bibliothèque des techniques (vidéos de référence du demandeur)

Le demandeur dépose dans Google Drive (`BitEye — Studio vidéo / 02_Bibliothèque / Vidéos pour apprentissage`) des pubs qui lui plaisent. Chacune est analysée (structure, rythme, transitions, présentation du produit, texte, son, publicité) puis ses techniques transposables sont ajoutées ici. Aucune vidéo ni capture n'entre dans ce dépôt public : seulement la description des techniques.

## Procédure d'analyse (à chaque nouvelle vidéo)

1. Registre Drive « Registre des vidéos analysées » : ne traiter que les nouvelles. Fichier ≤ 10 Mo (limite du connecteur) ; au-delà, demander l'envoi direct dans la session.
2. Un agent par lot de vidéos (`sonnet`) : `scdet`, planches de scènes, `silencedetect`, `ebur128`, lecture des images ; analyse en 8 points (fiche, structure et rythme, montage, présentation du produit, texte, son, publicité, transposition BitEye).
3. La session ajoute ici les techniques nouvelles (une ligne : technique — où on l'a vue — comment l'utiliser chez BitEye — à éviter) et met à jour les fiches concernées ; registre Drive mis à jour ; pull request.

## Techniques retenues

### Accroche
- **Question-accusation ou paradoxe dès l'image 0**, sans logo ni intro (« Vous n'avez toujours pas de stratégie ? », « Une pub ne commence pas par une pub ») — Spira (2 pubs, oct. 2026). Chez BitEye : « Vous suivez encore vos acquéreurs sur Excel ? », « Un promoteur ne vend pas des logements. Il vend des échéances tenues. » Texte en apparition mot à mot (flou → net) + léger coup de grave à 0,08 s.

### Rythme et montage
- **Peu de coupes, relancées par un punch-in** (recadrage +10 à 15 % sur une coupe tombant dans un creux de voix, la phrase repart ≈ 0,1 s après) — Spira. Chez BitEye : témoignages et face caméra ; c'est la version « coupe » de notre `zoomPunch`. Le rythme vient du texte : une idée toutes les 1 à 3 s.
- **Liste qui s'empile** (un élément par seconde, mots-clés en couleur d'accent) — Spira. Chez BitEye : modules (Estate, Build, Co-Owner…) ou douleurs du promoteur.

### Texte à l'écran
- **Pastilles « verre dépoli »** (fond translucide flouté) pour les textes incrustés, une seule couleur d'accent, texte sur le buste jamais sur le visage, entrée floue → nette, sortie en fondu — Spira.
- **« X ≠ Y »** (« Publier ≠ stratégie ») — Spira. Chez BitEye : « Un tableur ≠ un suivi », « Encaisser ≠ maîtriser sa trésorerie ».
- **Compteur animé** (0 % → valeur) — Spira. Chez BitEye : seulement avec un chiffre réel et sourcé (banque de données de `biteye-brand`).

### Présentation du produit et personnage
- **Un personnage qui porte la marque** et une **métaphore filée du métier** (médecin : diagnostic, fondations) — Spira. Chez BitEye : métaphore du chantier (fondations, plan, réception des travaux) ; personnage crédible pour des promoteurs (pas d'humour sur l'âge).

### Preuve et CTA
- **Preuve chiffrée + liste concrète, puis CTA à mot-clé** (« Écrivez DIAGNOSTIC ») — Spira. Chez BitEye : CTA WhatsApp (« Écrivez DÉMO au 0560 06 36 41 »), plus courant en Algérie que le commentaire.
- **À éviter** : CTA minuscule affiché 2 s (Spira « Mamie ») ; chiffres sans source ; durée > 35 s pour un Reel.

## Vidéos analysées

| Vidéo (Drive) | Analysée | Apports |
|---|---|---|
| Spira — « Les conseils de Mamie » (23 s) | 2026-10-24 | accroche-accusation, punch-in unique, pastilles verre dépoli, compteur |
| Spira — « Une pub ne commence pas par une pub » (42 s) | 2026-10-24 | paradoxe, liste qui s'empile, métaphore filée, CTA à mot-clé |
| 715 Sunridge Drive, 4 Chase Rd Windermere, Lake Nona (immobilier US) | en attente | fichiers > 10 Mo : à recevoir dans la session ou réduits |
