# Exemple : bibliothèque de transitions (9:16, 13,6 s, sans voix ni média)

Montre les 5 transitions du moteur V3, une par scène, et la caméra vivante (`drift`) sur chaque plan :

| # | Instant de coupe | Transition | Ce qu'on voit |
|---|---|---|---|
| 1 | 1,30 s | `zoomPunch` dans une même scène | coupe dans la plaque (saut de 2,2 s dans la source) cachée par un zoom 1,00 → 1,12 de 8 images, plaque et sujet ensemble |
| 2 | 2,60 s | `whip` vers la gauche | balayage de 8 images avec flou directionnel |
| 3 | 5,20 s | `matchCut` | le « visage » (halo) du plan B est posé à la place et à la taille de celui du plan A, puis la caméra se relâche |
| 4 | 7,80 s | `zoomThrough` | plongée dans le mot « VISION » jusqu'à remplir l'écran, sortie sur le plan suivant |
| 5 | 10,40 s | `maskReveal` | le plan suivant apparaît dans la silhouette détourée (WebM avec alpha) qui grandit |

Aucun fichier média : les plaques (dégradés + grille) et la silhouette sont générées par ffmpeg au build (`media.<clé>.lavfi`). Les temps de chaque transition sont dans `<slug>.cues.json` après le build.

```
ENG=../../scripts
python3 -I $ENG/build.py storyboard.json --out /tmp/tr
node $ENG/render.js /tmp/tr/transitions-9x16.local.html --tsheets /tmp/tr/planches
node $ENG/render.js /tmp/tr/transitions-9x16.local.html --mp4 /tmp/tr/transitions-4k.mp4 --scale 2 --master --deliver1080
```
