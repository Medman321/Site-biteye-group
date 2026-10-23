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
- Pas d'images générées par IA pour représenter des chantiers, des personnes ou des clients BitEye.
- Visages de tiers et plaques d'immatriculation : flouter si la personne n'a pas donné son accord (`ffmpeg -vf "boxblur=10:enable='between(t,a,b)'"` sur une zone `crop`/`overlay`), ou choisir un autre plan.
