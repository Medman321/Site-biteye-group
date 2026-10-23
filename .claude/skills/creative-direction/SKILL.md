---
name: creative-direction
description: Direction créative des vidéos marketing BitEye — hook des 1,5 premières secondes, touche humaine maximale, règles anti « vidéo IA générique », adaptation à chaque plateforme (Instagram, TikTok, YouTube, Facebook, LinkedIn, WhatsApp, site officiel) et grille de contrôle avant livraison. À lire avant d'écrire toute proposition ou tout storyboard.
---

# Direction créative BitEye

Objectif : une vidéo qu'un promoteur, un chef de chantier ou un syndic algérien regarde jusqu'au bout, reconnaît comme « faite par des gens du métier » et partage. Pas une démo de logiciel.

## 1. Le hook (0 à 1,5 s)

Le premier plan décide de tout. Il doit être visible **dès l'image 0** (pas d'écran vide, pas de logo d'ouverture) et provoquer une réaction. Formules qui marchent dans ce métier :

| Formule | Exemple |
|---|---|
| La douleur concrète, chiffrée | « 3 classeurs, 2 fichiers Excel, 0 visibilité. » |
| L'interpellation directe en darija | « Khouya, nta promoteur ? » avec le visage ou la voix de la personne |
| La scène vraie du quotidien | message WhatsApp du chef de chantier à 7 h : « ch7al bqa f le rond à béton ? » |
| Le contraste avant / après | photo du bureau plein de dossiers → même bureau, un écran |
| La question qui pique | « Ton acquéreur te demande où en est son F3. Tu réponds quoi ? » |
| Le chiffre surprenant (fourni par le client) | « 1,84 milliard engagé… et tu le suis sur un cahier ? » |

Moteur : `"flashes": [0.0]`, animation `slam` ou `punch` sur le premier titre, `at` ≈ 0,05. La voix commence à moins de 0,5 s : sinon, coupe le début avec `audio-studio` → `edit_voice.py --start`, ou démarre sur un texte fort.

## 2. La touche humaine (au moins 3 par vidéo)

- **Une vraie voix** : celle du demandeur, d'un client, d'un chef de chantier. La voix de synthèse vient en dernier recours.
- **De vrais visages et de vrais lieux** : photos et vidéos du client (chantier, bureau, équipe, remise des clés). Chaque voix réelle a son bandeau nom + poste + photo (`lowerthird`) quand elle commence à parler.
- **Le geste de la main** : notes manuscrites (`note`), mots entourés ou soulignés à la main (`mark`), polaroïds avec du scotch (`polaroid`), autocollants (`sticker`). Avec parcimonie : 1 ou 2 par scène.
- **Les canaux du quotidien** : conversations WhatsApp (`chat`), texte tapé en direct (`typewriter`).
- **L'imperfection assumée** : léger tremblé de caméra (`"handheld": 0.6` à `1`), grain (`"grain": 0.08` à `0.14`), son d'ambiance réel (chantier, bureau) sous la voix.
- **La langue et les références locales** : darija naturelle, wilayas, F3/F4, VSP, G50, café du matin, Ramadan, rentrée. Humour léger et respectueux.
- **Un vrai témoignage** dès qu'il existe (`quote` + photo + nom), avec l'accord de la personne.

## 3. Les écrans du logiciel : toujours dessinés

On ne montre **jamais** la vraie interface de VISION, même si des captures sont fournies : elle ne doit pas être divulguée, et une maquette dessinée est plus lisible en vidéo. Les captures du client servent seulement de référence (quelles informations, quel vocabulaire).
- Blocs : `app` (tableau de bord : indicateurs, avancement par lot), `schedule` (échéancier acquéreurs, statuts en pastilles), `phone` (application mobile), `chat`.
- Une maquette = une seule idée lisible en 2 s : 3 indicateurs, 4 ou 5 lignes, gros caractères, statuts en couleur.
- Données fictives et plausibles (« Résidence Les Oliviers », « Bloc C », « F3 »), avec la mention « Données fictives » en bas de l'écran (automatique ; `fictive: false` interdit sauf accord écrit du demandeur).

## 4. À bannir (le « look IA générique »)

- Particules lumineuses, néons violets ou bleus, dégradés « tech », robots, hologrammes, cerveaux, globes.
- Images générées par IA de personnes, de chantiers ou de bureaux. Photos de banque d'images avec des gens « trop parfaits ».
- Phrases creuses : « révolutionnez », « libérez le potentiel », « solution innovante de pointe », « à l'ère du numérique ».
- Voix de synthèse monotone sur toute la vidéo, musique « corporate » générique à fond.
- Animer tout en même temps : un seul mouvement principal à la fois.
- Textes centrés qui disent la même chose que la voix, mot pour mot : l'écran **montre** (chiffre, écran, objet), la voix **raconte**.
- Durée trop longue : chaque scène doit apporter une information nouvelle, sinon coupe.

## 5. Structure narrative (30 à 45 s)

Hook (0–2 s) → problème vécu (2–8 s) → « et si… » / bascule (8–12 s) → la solution montrée dans le vrai métier (12–30 s : 2 ou 3 preuves concrètes, pas 7) → preuve sociale ou chiffre client (si fourni) → appel à l'action simple (dernières 3–4 s).
Variante 15 s : hook → une preuve → CTA.

## 6. Par plateforme

| Plateforme | Format | Durée conseillée | Particularités |
|---|---|---|---|
| Instagram Reels, TikTok, YouTube Shorts | 9:16, `"safe": true` | 15–35 s | hook visuel immédiat ; sous-titres obligatoires (lecture sans son) ; zones du haut et du bas réservées aux boutons ; rythme rapide ; CTA « lien en bio » ou « écris DEMO en commentaire » |
| Stories Instagram / Facebook, statut WhatsApp | 9:16, `"safe": true` | ≤ 15 s par segment (statut ≤ 60 s) | une idée par segment ; CTA vers le site ou WhatsApp Business |
| Fil Facebook / Instagram | 4:5 (ou 1:1) | 20–45 s | lecture sans son par défaut : texte à l'écran autonome ; les 3 premières secondes valent une affiche |
| LinkedIn | 1:1 ou 4:5 | 30–60 s | ton professionnel, français ; preuves chiffrées, témoignages ; moins de darija |
| YouTube (vidéo, pré-roll) | 16:9 | 30–90 s (pré-roll : message avant 5 s) | le logo et la promesse avant le bouton « Ignorer » ; plus de détails produit |
| Site officiel (en-tête, page produit) | 16:9 (et 9:16 pour le mobile) | 20–40 s, en boucle | lue sans son, en boucle : c'est un **montage différent**, pas une simple déclinaison du Reel (pas de voix ni de sous-titres karaoké, textes autonomes, `wave: false`, écran final court, fin qui se raccorde au début) |
| Salon, écran en boutique | 16:9 | boucle 30–60 s | sans son : tout passe par le texte et l'image |

Vérifie les spécifications du moment par une recherche web si la demande vise une campagne payante (formats publicitaires, durées maximales).

Voix plus longue que la durée conseillée : propose dans la proposition des coupes précises (pauses, phrase répétée) avec la durée obtenue ; le demandeur tranche. Ne coupe jamais une voix sans son accord.

## 7. Grille de contrôle avant livraison

Note chaque point sur la planche (`sheet.jpg`) et dans le compte rendu :

1. Hook visible à l'image 0, compréhensible sans le son ?
2. Au moins 3 touches humaines, dont une dans les 3 premières secondes ?
3. Aucun élément de la liste « à bannir » ?
4. Une référence au métier ou à l'Algérie que seul BitEye mettrait ?
5. Sous-titres lisibles et hors des zones de la plateforme ?
6. Une seule promesse claire et un seul CTA, choisi selon la nature de la vidéo (`biteye-brand`) ?
7. Chiffres et noms : fournis par le client, ou signalés comme exemples ?
8. Chaque voix réelle a son bandeau nom + poste (+ photo) ? Les écrans du logiciel sont des maquettes marquées « Données fictives » ?
9. Les pauses qui séparent les idées sont-elles gardées après une coupe de la voix ?

Un « non » = corrige avant de rendre le MP4.
