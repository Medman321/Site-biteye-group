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

Moteur : l'accroche est **déjà posée à l'image 0** : `shown: true` (ou `at` de −0,3 à −0,5 s) sur le premier titre, déjà en mouvement (compteur en cours, texte qui s'écrit, plan qui avance), et un changement visible avant 1 s. Plus de flash à 0 avec un titre qui entre à 0,05 s : l'image 0 sort blanche ou vide, et les aperçus des fils (Facebook, WhatsApp, LinkedIn) et certaines vignettes prennent cette image. Un flash reste possible à la coupe accroche → corps (grammaire R10). La même image sert de couverture (centre 1080×1350). La voix commence à moins de 0,5 s : sinon, coupe le début avec `audio-studio` → `edit_voice.py --start`, ou démarre sur un texte fort.

Autres catégories (preuve par un pair, erreur qui coûte, boucle refermée, actualité), mécanismes, hooks visuels et grille de choix : « Banque de hooks » de `bibliotheque-techniques`. Rien d'inventé, aucune promesse de vues, et toute question posée par le hook trouve sa réponse avant le CTA.

Jamais en première phrase : salut ou prénom, « dans cette vidéo », « aujourd'hui je vais vous montrer », question oui/non à réponse évidente (« Vous voulez plus de ventes ? »), « saviez-vous que » + fait connu, contexte avant l'affirmation (« la semaine dernière, je réfléchissais… »), ni une promesse que la suite ne tient pas. L'interpellation qui identifie la cible (« Nta promoteur ? ») reste permise. Contrôle : les 5 premiers mots de la voix.

Un hook travaillé est une mini-histoire en 2 actes avec renversement sur un mot-pivot (« mais », « jusqu'à ce que ») : acte 1, la douleur posée en moins d'une seconde ; acte 2, la bascule, avec un impact doux (coup de grave ≤ 0,1 s) sur le mot-pivot et le gain en badge. Un seul mouvement principal à la fois : l'acte 2 démarre quand l'acte 1 est posé. Un hook qui ne fait que placer un objet et le faire glisser est à refaire, pas à retoucher.

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
- Images générées par IA de personnes, de chantiers ou de bureaux (exception : option A de `bibliotheque-techniques`, proposée et validée au cas par cas, jamais un « look IA générique »). Photos de banque d'images avec des gens « trop parfaits ».
- Phrases creuses : « révolutionnez », « libérez le potentiel », « solution innovante de pointe », « à l'ère du numérique ».
- Voix de synthèse monotone sur toute la vidéo, musique « corporate » générique à fond.
- Animer tout en même temps : un seul mouvement principal à la fois.
- Clips d'accroche tiers (packs de « hooks », vidéos virales sans rapport avec le métier) et promesses de vues : droits inconnus, public hors cible.
- Textes centrés qui disent la même chose que la voix, mot pour mot : l'écran **montre** (chiffre, écran, objet), la voix **raconte**.
- Durée trop longue : chaque scène doit apporter une information nouvelle, sinon coupe.

## 4 bis. Passe d'humanisation

Dernière passe sur tout texte lu ou publié (voix off, cartons, légende, commentaire épinglé) :
1. mots-tics : plonger, véritable, incontournable, crucial, primordial, booster, décupler, optimiser sans chiffre, tirer parti de, « permettre de » partout, la clé du succès, en effet / de plus / par ailleurs, en somme, il est important de noter, à l'ère du numérique, sans plus attendre, n'hésitez pas à, que vous soyez… ou… ; en darija, le lien formel de l'arabe standard que personne ne dit à voix haute ;
2. formes : un seul « ce n'est pas X, c'est Y » par texte (et seulement si X est une croyance réelle), trois adjectifs en rafale, phrases hachées, « Le résultat ? » suivi de sa réponse, annonce (« voici pourquoi : »), récapitulatif final, appât d'engagement ;
3. rythme plat (toutes les phrases de 12 à 16 mots) ;
4. lecture à voix haute ;
5. chiffres, noms et CTA inchangés.

Note de 0 à 2 sur 5 contrôles (propre, mots, formes, rythme, faits) : validé à 9/10 avec les faits à 2, sinon seconde passe. Un mot que la personne dit réellement n'est jamais remplacé ; chaque correction du demandeur rejoint « Ne dit jamais » (`biteye-brand` § Ton). Caractères invisibles et typographie : `texte_controle.py` (`biteye-video-ad` §4).

## 5. Structure narrative (30 à 45 s)

Structure du Journal : **Hook** 0–3 s → **Lead** avant 10 s (la promesse, explicite : problème vécu, puis la « bascule et si… » de 8–12 s) → **Body 1, 2, 3** (une idée chacun, chaque bloc ouvert par une relance ; la solution montrée dans le vrai métier, 2 ou 3 preuves concrètes, pas 7 ; preuve sociale ou chiffre client si fourni) → **CTA** simple (dernières 3–4 s).
La relance principale tombe à 40–60 % de la durée (question nouvelle, chiffre, retournement ou objection levée avec un chiffre) ; sous 25 s elle est facultative. Variante 15 s : hook → une preuve → CTA.

## 6. Par plateforme

| Plateforme | Format | Durée conseillée | Particularités |
|---|---|---|---|
| Instagram Reels, TikTok, YouTube Shorts | 9:16, `"safe": true` | 15–35 s | hook visuel immédiat ; sous-titres obligatoires (lecture sans son) ; zones du haut et du bas réservées aux boutons ; rythme rapide ; à l'écran, le CTA WhatsApp unique + mot-code, « commentez <mot-code> » en légende et commentaire épinglé (`biteye-brand` § Appel à l'action) |
| Stories Instagram / Facebook, statut WhatsApp | 9:16, `"safe": true` | ≤ 15 s par segment (statut ≤ 60 s) | une idée par segment ; CTA vers le site ou WhatsApp Business |
| Fil Facebook / Instagram | 4:5 (ou 1:1) | 20–45 s | lecture sans son par défaut : texte à l'écran autonome ; les 3 premières secondes valent une affiche |
| LinkedIn | 1:1 ou 4:5 | 30–60 s | ton professionnel, français ; preuves chiffrées, témoignages ; moins de darija |
| YouTube (vidéo, pré-roll) | 16:9 | 30–90 s (pré-roll : message avant 5 s) | le logo et la promesse avant le bouton « Ignorer » ; plus de détails produit |
| Site officiel (en-tête, page produit) | 16:9 (et 9:16 pour le mobile) | 20–40 s, en boucle | lue sans son, en boucle : c'est un **montage différent**, pas une simple déclinaison du Reel (pas de voix ni de sous-titres karaoké, textes autonomes, `wave: false`, écran final court, fin qui se raccorde au début) |
| Salon, écran en boutique | 16:9 | boucle 30–60 s | sans son : tout passe par le texte et l'image |

Miniature 16:9 (YouTube, site) : image réelle extraite de la vidéo, 1280×720, JPG de moins de 2 Mo (à vérifier sur la page officielle de la plateforme), un seul sujet, 3 mots au plus, fort contraste, rien dans le coin bas droit (la plateforme y affiche la durée), lisible en vignette réduite ; jamais de visage généré. Couverture 9:16 : `biteye-video-ad` §4.

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
10. La question ou la promesse du hook trouve-t-elle sa réponse avant le CTA ?

Un « non » = corrige avant de rendre le MP4.
