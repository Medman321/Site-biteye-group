---
name: media-lab
description: Traitement gratuit et local des séquences vidéo et des photos du client pour les vidéos BitEye — découpe en plans, coupe précise, recadrage 9:16/4:5 avec panoramique, stabilisation, étalonnage, débruitage, ralenti, extraction d'images, détourage de photos. Aucun outil payant. À utiliser dès que des vidéos ou des photos sont fournies.
---

# Laboratoire vidéo et photo (gratuit)

Outils : ffmpeg (vidstab, scdet, hqdn3d, colortemperature, curves, minterpolate) et rembg (détourage par réseau u2net, modèle téléchargé une fois depuis GitHub). Tout reste en local.

```
ML=".claude/skills/media-lab/scripts/media_lab.py"
```
Travaille toujours sur des copies dans `$OUT/` ; les originaux restent intacts dans `$OUT/src`.

## Méthode pour des séquences vidéo

1. **Inventaire** : `media-analysis` (`analyze_media.py`) → durée, orientation, plans, son.
2. **Découper en plans** : `python3 -I $ML shots src/clip.mp4 --out $OUT/plans` → un fichier par plan + `plans.jpg`. Regarde la planche (Read) et choisis les plans utiles : action, visages, gestes, avant / après. Un bon plan dure 1,5 à 4 s dans une pub.
3. **Couper précisément** : `python3 -I $ML cut src/clip.mp4 $OUT/c1.mp4 --start 3.2 --end 6.0`.
4. **Stabiliser** les plans tournés à la main : `python3 -I $ML stabilize c1.mp4 c1s.mp4` (garde un léger tremblé : `--strength 8`, c'est humain ; 30 pour un plan très secoué).
5. **Recadrer pour le format** : `python3 -I $ML reframe c1s.mp4 c1v.mp4 --aspect 9:16 --x 0.4 --size 1080x1920`. `--x/--y` (0 à 1) placent le cadre sur le sujet ; `--to-x 0.7` fait un panoramique lent, utile pour un plan large de chantier recadré en vertical.
6. **Étalonner** : `python3 -I $ML grade c1v.mp4 c1g.mp4 --look chantier [--denoise] [--sharpen]`.
   Looks : `naturel` (correction légère), `chaud` (soleil, accueil), `chantier` (béton, acier, contraste), `nuit` (intérieur sombre), `biteye` (neutre, ombres légèrement teal). Un même look pour tous les plans d'une vidéo.
7. **Ralenti / accéléré** : `python3 -I $ML speed c1g.mp4 slow.mp4 --factor 0.5 --smooth` (ralenti fluide par interpolation) ; `--factor 8` pour un timelapse de chantier.
8. Place le résultat dans le storyboard (`media` + bloc `video` ou fond de scène `background`). Le moteur convertit lui-même en WebM.

## Méthode pour des photos

1. Regarde chaque photo (aperçus de `analyze_media.py`). Écarte les floues, les sombres irrécupérables et celles qui montrent des personnes non consentantes ou des documents sensibles.
2. **Recadrer + corriger** : `python3 -I $ML photo src/p1.jpg $OUT/p1.jpg --aspect 4:5 --x 0.5 --y 0.35 --look naturel`.
3. **Détourer** un sujet (personne, engin, maquette, téléphone) pour le poser sur le fond de marque : `python3 -I $ML cutout p1.jpg p1.png`. Vérifie les bords (Read). Cheveux et grilles se détourent mal : garde alors la photo entière en `polaroid`.
4. **Une vidéo comme réserve de photos** : `python3 -I $ML frames clip.mp4 --out $OUT/images --every 0.5`.

## Règles

- Les images du client sont le cœur de la touche humaine : vrais chantiers, vraies équipes, vrais bureaux. Les retoucher pour les rendre lisibles, jamais pour les rendre « parfaites » ou artificielles.
- Pas d'images générées par IA pour représenter des chantiers, des personnes ou des clients BitEye, sauf dérogation (option A de `bibliotheque-techniques` : proposée au demandeur au cas par cas, avec ses garde-fous).
- Captures d'écran de VISION : ne jamais les monter dans une vidéo (interface confidentielle). Elles servent de référence pour dessiner les maquettes (`creative-direction` §3).
- Visages de tiers et plaques d'immatriculation : flouter si la personne n'a pas donné son accord (`ffmpeg -vf "boxblur=10:enable='between(t,a,b)'"` sur une zone `crop`/`overlay`), ou choisir un autre plan.

## Contrôles et détourage vidéo (outils V2)

Écrits pendant la vidéo témoignage V2. `align_check.py` a été testé sur un vrai storyboard ; `cutout_video.py` n'a été que compilé : vérifie son premier lot sur 2 ou 3 images avant un long calcul.
- `python3 -I .claude/skills/media-lab/scripts/align_check.py PROD [--subjects z1] --info-gate` : alignement sujet/plaque image par image, `start` corrigé, crâne coupé (head_top plafonné ou qui saute). Échec = pas de rendu.
- `python3 -I .claude/skills/media-lab/scripts/cutout_video.py --jobs travaux.txt --log lot.log` : détourage sur la plaque en lot (une ligne : plaque image0 nb u2net|rvm sortie), arrêt au premier défaut de tête. Remplace les lanceurs `run_*.sh`.

## Plans de profondeur (photos)

`depth_layers.py` sépare une photo en 3 calques : personnes, AP1 (mobilier proche : table, écrans, panneaux) et AP2 (mur, comblé derrière tout le reste). Il essaie ensuite un mot inséré, avec 3 amplitudes de parallaxe et la mesure de la part cachée (`layer_diff.py behind` et masques). Testé sur 2 photos de formation (octobre 2026) : environ 6 s de calcul par photo, 1 min avec mesures et aperçu, CPU 3 fils.
- **Quand l'utiliser** : un mot ou un graphisme doit passer derrière des personnes **et** derrière du mobilier, ou une photo doit bouger en parallaxe sans que la personne apparaisse en double. Le détourage seul laisse la personne dans la plaque (doublon dès qu'on décale) et ne fait jamais passer le mot derrière une table ou un écran.
- **Commande type** : `python3 -I .claude/skills/media-lab/scripts/depth_layers.py photo.jpg --out $OUT/profondeur/p1 --word MOT --plan fond --amplitude tous --erase x,y,w,h --exclude x,y,w,h --preview --compare-detourage`. Utilise `--plan personne` quand un panneau est devant le mur à hauteur de tête, `--blur-poly` pour un écran à rendre illisible (seulement sur AP2, aucun visage flouté), `--font` pour la police de la vidéo. Code de sortie 1 si le mot sort de 25 à 40 % caché ou si une lettre de bord est cachée à plus de 50 %.
- **Modèle** : Depth Anything V2 Small (Apache-2.0), export ONNX de la release GitHub `fabio-sim/Depth-Anything-ONNX`. Il est téléchargé une fois dans `~/.cache/biteye-depth/`, taille et SHA256 vérifiés, et ne va jamais dans le dépôt.
- **Limites relevées** :
  - u2net_human_seg rate des vêtements (dos, bras, jambes) et prend parfois un objet pour une personne : ces morceaux tombent dans AP1 ; retire les faux positifs avec `--exclude` et vérifie `calque_personnes.png`.
  - Bouge **personnes et AP1 ensemble** (chaises et tables sont souvent devant les gens) ; seuls le mur et le mot bougent autrement (mot à 0,25 × l'amplitude).
  - **Amplitude moyenne (20 px/s) recommandée**. En forte (30 px/s), le comblement d'un mur texturé (marbre) se voit en bande floue et les lettres de bord sortent des bornes.
  - Contraste : un mot de la couleur des vêtements fausse la mesure et ne se lit pas ; `layer_diff` le signale.
- **Aucune IA générative sur les photos de clients** : le fond est comblé par OpenCV (TELEA, reflet du mur voisin, grain mesuré), jamais inventé.
