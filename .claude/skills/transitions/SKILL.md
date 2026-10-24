---
name: transitions
description: Conception et preuve des transitions des vidéos BitEye — repérage des coupes cachées dans les sources avant tout montage, choix de chaque transition selon la relation entre les deux scènes (grammaire de raccords → transition du moteur, paramètres, son J-cut / L-cut / souffle), fiche `transitions.json` par coupe pour le producteur et le sound designer, puis vérification image par image (rampe ≥ 3 images, visage jamais coupé ni dédoublé, pas de saut de luminance brutal, direction du mouvement continue, pas d'image fantôme) avec `scripts/transition_audit.py`. À utiliser dès qu'une vidéo a plusieurs plans ou des sources déjà montées ; obligatoire en premium.
---

# Transitions BitEye : choisir, ficher, prouver

Partage des rôles : le **chef monteur** décide **où et quand** on coupe (`edl.md`, animatic) ; le **concepteur de transitions** décide **comment** on passe d'une scène à l'autre et le prouve par des mesures ; le **producteur** applique la fiche dans le storyboard ; le **sound designer** pose les sons de la fiche ; le **DA** juge le rendu.

Défauts réels qui motivent ce skill (retex V2 et V3, `.claude/retex/2026-10-temoignage-v2.md`) : visage coupé entre 9 et 14 s par une coupe cachée de la source ; transitions timides ou sans rampe avant la coupe (NO GO du DA en V3) ; même famille de défaut revenue après l'audit ; transitions choisies sans lien avec la relation entre les scènes.

```
SK=.claude/skills/transitions/scripts
python3 -I $SK/transition_audit.py sources SOURCE.mp4 [--sheet src.jpg] [--json src.json]
python3 -I $SK/transition_audit.py cuts VIDEO.mp4 --storyboard $OUT/transitions.json [--sheet planche.jpg] [--json mesures.json] [-v]
python3 -I $SK/transition_audit.py cuts VIDEO.mp4 --cuts 5.57,10.03,13.00          # temps à la main
```
Prérequis : ffmpeg, numpy, `pip install "opencv-python-headless<5"` (la branche 5 n'a plus les cascades Haar). Visages : MediaPipe s'il est installé, sinon YuNet (`~/.cache/biteye-transitions/face_detection_yunet_2023mar.onnx`, MIT, adresse dans `references/ressources-libres.md`), sinon Haar. Le détecteur utilisé est écrit en tête du rapport. ≈ 10 à 15 s pour 40 s de 1080×1920 ; aucun jeton de modèle.

## 1. Repérer les coupes cachées des sources (avant tout montage)

Pour chaque source vidéo (rush, ancien montage, plaque restaurée) : `transition_audit.py sources`. Sortie : temps, image, écart, rapport au voisinage (méthode « adaptative » de PySceneDetect), score `scdet` de ffmpeg ; puis les images isolées (flash, image fantôme) et le nombre d'images doublées (utile au détourage : grille d'images de la plaque).

- Regarder la planche `--sheet` (paires t−1 | t) : une incrustation qui entre, un fondu vers un logo ou un geste rapide peuvent sortir comme coupe ; on les note « faux positif », on ne les supprime pas.
- Chaque coupe cachée **dans une plage retenue par le monteur** devient une ligne de la fiche (relation R1 en général) : elle aura une transition conçue, jamais une coupe sèche.
- Tout plan source sans image propre (carton, incrustation qu'on ne peut pas masquer) est signalé à la planification (règle Efficacité de `.claude/CLAUDE.md`).
- Les coupes non prévues d'un MP4 déjà rendu se cherchent avec `motion-engine/scripts/cut_audit.py` (comparaison au storyboard) : ne pas le refaire.

## 2. Choisir chaque transition : la grammaire

Pour chaque changement de plan de `edl.md` (et chaque coupe cachée gardée), nommer la **relation** entre A et B, puis appliquer la ligne de `references/grammaire.md` :

| Relation | Transition de départ | Son |
|---|---|---|
| R1 même intervenant, même idée | `zoomPunch` pic puis retour, rampe 4 img, `peak` 1,06 | voix continue, micro-souffle ou rien |
| R2 même intervenant, idée nouvelle | `zoomPunch` fort ou `whip` court | souffle + impact |
| R3 changement d'intervenant | `maskReveal` (`ease: "area"`) ou `zoomThrough` dans un mot-pont | **J-cut** 0,2 à 0,4 s, nappe |
| R4 intervenants cadrés pareil | `matchCut` (`faceA`, `faceB` mesurés) | accent sur le temps |
| R5 problème → solution | `zoomThrough` dans le mot du problème | creux 0,3 s puis impact |
| R6 visage → écran du logiciel | `whip` dans le sens du regard, ou `zoomThrough` dans l'objet | **L-cut**, souffle + clic |
| R7 écran → visage | `zoomPunch` arrière ou `maskReveal` cercle | J-cut court |
| R8 saut de lieu ou de temps | `whip` (même direction tout le film) ou `matchCut` sur la forme | souffle long, ambiances croisées |
| R9 photo → photo | `matchCut` sur la forme, ou fondu par calques ≥ 6 img avec `drift` de même sens | sur le temps de la musique |
| R10 accroche → corps | `zoomPunch` pic ou flash d'une image | coup de grave |
| R11 fin → CTA | `whip` ou plongée dans l'œil du logo (`target: "scene"`) | L-cut, souffle, impact, jingle |
| R12 carton ↔ plan | premium : `maskReveal` cercle ou fondu 6 à 10 img | sur le temps |
| R13 même mouvement des deux côtés | coupe sur l'action + `whip` de même sens | son du geste à cheval |

Règles de choix : une transition voyante seulement là où le sens change (témoin, chapitre, CTA) ; une seule direction de whip dans le film ; techniques de la `bibliotheque-techniques` (whip calé sur un geste, punch-in, fuite de lumière ≤ 2) proposées, pas imposées ; règles de raccord (180°, regard, forme, coupe sur l'action) rappelées dans la grammaire §2. Paramètres exacts des types : `motion-engine` SKILL.md, « Transitions ».

## 3. La fiche : `$OUT/transitions.json` et `$OUT/transitions.md`

Une entrée par coupe, dans l'ordre du film. Le producteur la recopie dans `storyboard.json` (`transition` de la scène ou liste `transitions`) ; le sound designer en tire ses repères ; l'outil la relit (`--storyboard transitions.json`, clés `coupes[].cut` et `type`).

```json
{"video": "temoignage-v4", "fps": 30,
 "seuils": {"rampe_min": 3, "luma_max": 12, "saut_visible": 18},
 "coupes": [
  {"n": 1, "cut": 13.0, "de": "naila-1", "vers": "naila-2", "relation": "R1", "coupe_source": true,
   "type": "zoomPunch", "at": 12.867, "dur": 0.3, "direction": "avant (zoom)",
   "params": {"scene": "naila", "from": 1.0, "peak": 1.06, "to": 1.12, "origin": "50% 35%", "blur": 1.2},
   "rampe_images": 4,
   "son": {"raccord": "aucun, voix continue", "habillage": "micro-souffle de 12,87 à 13,00, sans impact"},
   "raison": "même phrase, la source change d'expression : flou de rampe pour masquer le saut",
   "mesure": {"rampe": null, "saut": null, "verdict": null}}]}
```

`transitions.md` = le même contenu en tableau lisible (n°, temps, de → vers, relation, transition et paramètres, son, raison), plus la liste des coupes cachées des sources et ce qu'on en fait. Après mesure, la colonne `mesure` est remplie (rampe, saut, verdict).

## 4. Vérifier, image par image (avant l'audit du DA)

Sur quoi mesurer : la mesure exige 30 i/s et au moins 20 images avant chaque coupe.
1. **Pré-rendu de contrôle** à 30 i/s du storyboard appliqué (`render.js --mp4 … --fps 30`, 1080×1920, sans `--scale 2` ni `--master` ; `--scale 0.5` pour du 540×960, non testé à ce jour). Ce n'est pas le rendu final.
2. `transition_audit.py cuts PRE.mp4 --storyboard $OUT/transitions.json --sheet $OUT/transitions-planche.jpg --json $OUT/transitions-mesures.json`.
3. Pour une transition douteuse, regarder aussi sa planche du moteur : `render.js … --tsheets $OUT/tsheets` (10 images consécutives par transition).
4. Corriger la fiche (paramètres, point de coupe proposé au monteur), faire réappliquer, re-mesurer : **une seule boucle**, puis remettre au DA les mesures et la planche.

Ce que l'outil contrôle à chaque coupe (seuils détaillés : `references/seuils.md`) :

| Contrôle | Exigé | Note |
|---|---|---|
| rampe avant la coupe (mouvement, zoom ou flou mesurés) | **≥ 3 images** | `maskReveal`, fondus : rampe ou relâche ≥ 3 |
| saut visible (coupe franche non masquée par le flou ou le mouvement) | aucun | cas V3 : 22,13 et 29,67 |
| saut de luminance entre t−1 et t | ≤ 12 sur 255, sinon progressif | whip vers un fond sombre : vérifier |
| visage à t−1, t, t+1 | jamais coupé par le bord ni dédoublé ; ne saute pas de plus de 2 % de la largeur (centre des yeux) sur une coupe franche nette | Δx, Δy (yeux, px de la vidéo) et taille notés à chaque coupe |
| image fantôme | aucune (image isolée, coupe en deux temps, image mélangée seule) | fondu ≥ 6 images |
| direction du mouvement | pas d'inversion de part et d'autre | whips, coupe sur l'action |
| relâche, transition sans effet | signalées en note | `end` = `cut` (lu dans `cues.json` ou le storyboard), `matchCut` aux listes `a`/`b` vides |

Lecture : la coupe déclarée (`cut` du storyboard ou de `cues.json`, image `ceil(cut × fps)`) est gardée si elle est franche et suit un zoom fort continu, dont les images comptent alors comme rampe (V3, 17,17 : ×1,41 en 4 images). Avec `--cuts` (temps arrondis), la coupe est recalée sur le plus grand saut à ±3 images. Les yeux viennent de YuNet ou MediaPipe ; avec Haar, le centre de la boîte sert de repli (noté « boîte »). Un clignement rend les yeux moins sûrs (V3, 10,03 : −76 px mesurés en 540×960, −87 px en pleine résolution).

Le visage « coupé » par un détourage décalé (V2) ne se voit pas à la seule détection : la porte avant rendu le contrôle (`motion-engine/scripts/pre_render_gate.sh` → `media-lab/scripts/align_check.py`). Les deux portes sont complémentaires ; aucune ne remplace l'autre.

## 5. Garde-fous

- **Rampe ≥ 3 images mesurées**, pas déclarées : en V3, un `zoomPunch` à `peak` 1,04 sur 3 images n'a donné qu'une image visible (5,57).
- **Visage jamais coupé ni dédoublé** autour d'une coupe ; centre de l'action (yeux) au point d'origine des zooms.
- **« Subtil » garde un plancher de visibilité** : rampe ≥ 3 images, effet `layer_diff.py effect` ≥ 0,5 % de pixels changés. Un désaccord de goût (plus fort, plus doux) se tranche sur une planche de 3 niveaux de 2 images clés, jamais par un rendu.
- **Aucune coupe sèche entre deux plans en premium**, coupes cachées des sources comprises ; en standard, coupe franche sur le temps acceptée pour les cartons et démos.
- **Animatic refait** par le monteur après toute passe qui déplace une coupe ; la fiche suit la nouvelle `edl.md`.
- Aucune image générée par IA, sauf « Génération IA (option A) » de `bibliotheque-techniques`. Aucun média ni planche dans le dépôt Git (public) : tout dans `$OUT`.
- Le concepteur ne déplace pas une coupe : il le **propose** au monteur avec la raison mesurée (ex. « couper 2 images plus tôt, bouche fermée »).

## 6. Compte rendu (≤ 15 lignes)

Coupes cachées trouvées par source ; nombre de transitions par relation ; tableau des coupes À REVOIR avec la raison mesurée et la correction ; chemins de `transitions.json`, `transitions.md`, de la planche et des mesures ; propositions faites au monteur.

## Références

- `references/grammaire.md` : grammaire complète (13 relations, paramètres, son, pièges, règles de raccord).
- `references/seuils.md` : définitions et seuils de chaque mesure, valeurs de départ par transition, résultats de référence V3.
- `references/ressources-libres.md` : PySceneDetect, `scdet`, TransNetV2, gl-transitions, `xfade`, YuNet, MediaPipe, avec leurs licences et ce qui est portable dans le moteur.
- Outils réutilisés : `motion-engine/scripts/cut_audit.py`, `layer_diff.py`, `pre_render_gate.sh`, `render.js --tsheets`, `media-lab/scripts/align_check.py`.
