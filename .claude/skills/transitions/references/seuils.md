# Seuils mesurables des transitions (valeurs par défaut de `transition_audit.py`)

Toutes les mesures se font sur l'image réduite à 270×480 (écarts, flux, luminance) ou 540×960 (netteté, visages), à la cadence de la vidéo (30 i/s). Un seuil changé pour un projet est écrit dans `transitions.json` (`seuils`) avec sa raison.

| Mesure | Définition | Seuil par défaut | Option | Origine |
|---|---|---|---|---|
| Coupe franche | écart moyen BGR (0-255) entre t−1 et t | ≥ 12 | `--hard` | en dessous, coupe douce ou fondu : rampe non exigée |
| **Rampe avant** | images consécutives juste avant la coupe où l'un de ces signes dépasse la référence calme du plan : flux optique moyen ≥ max(0,8 px ; 1,5 × réf.), composante zoom ≥ max(0,35 px ; 2 × réf.), écart image à image ≥ max(4 ; 2 × réf.), netteté (variance du laplacien) ≤ 0,85 × réf. et en baisse | **≥ 3 images** | `--ramp`, `--mag`, `--div`, `--dmin`, `--blur` | `.claude/CLAUDE.md` (Efficacité, Transitions) ; retex V3 |
| Relâche après | même calcul après la coupe | information (exigée ≥ 3 pour `maskReveal`, fondus) | — | — |
| Référence calme | quartile bas de t−20 … t−6 (sans dépasser la coupe précédente) | — | — | évite qu'une transition voisine fausse la référence |
| **Saut visible** | coupe franche d'écart ≥ 18 que ni le flou (netteté t−1 ≤ 0,5 × réf.) ni le mouvement (flux t−1 ≥ 3 px) ne masquent | aucun | `--visible`, `--mask-blur`, `--mask-flow` | V3 : 22,13 (32) et 29,67 (44) vus par le demandeur |
| **Luminance** | écart de luminance moyenne entre t−1 et t | ≤ 12 ; au-delà, « brutal » seulement s'il fait plus de 2 × les sauts voisins (sinon « progressive », en note) | `--luma` | grille du DA (YAVG > 12 = à examiner) |
| **Visage coupé** | boîte du visage à moins de 1 % du bord du cadre à t−1, t ou t+1 | aucun | — | retex V2 (visage coupé 9-14 s) |
| **Visage en double** | plus de grands visages qu'en t±6, ou deux visages de même taille (×0,7 à ×1,4), même hauteur, centres à moins de 1,5 largeur | aucun | — | surimpression, détourage décalé |
| **Image fantôme** | image isolée (t−1 ≈ t+1, t différente), coupe en deux temps encadrée d'images calmes, ou une seule image mélangée A+B | aucune | — | fondu < 2 images, image de la source oubliée |
| **Direction** | translation moyenne (3 images avant contre 3 après) opposée, chacune ≥ 1,5 px/img | aucune inversion | `--dir-min` | raccord dans le mouvement, whips |
| « Subtil » | un effet discret garde un plancher de visibilité : `layer_diff.py effect` ≥ 0,5 % de pixels changés ; une rampe « douce » garde ses 3 images mesurées | plancher | — | retex V2 (effets devenus invisibles) |

## Valeurs de départ par transition (pour atteindre les seuils)

- `zoomPunch` : rampe d'au moins 4 images (`at` = cut − 0,133) et `peak` ≥ 1,04 ; mesuré en V3 : `peak` 1,04 sur 3 images ne donne qu'**1 image** au-dessus du seuil (5,57) ; viser 1,06 ou ajouter `blur` 1,2.
- `whip` : 8 images ; le flou masque le saut ; vérifier la luminance si B est beaucoup plus sombre ou clair (V3 : 25 par image vers l'écran final).
- `maskReveal` : `ease: "area"` pour une croissance de surface linéaire (pas de saut de luminance) ; relâche ≥ 3 images.
- `matchCut` : écart des centres de visage < 8 % de la largeur après recalage, rapport de taille ≤ 1,3.
- Fondu par calques : au moins 6 images ; 1 à 3 images = image fantôme.

## Résultats de référence (V3, 1080×1920, 30 i/s, YuNet)

| Coupe | Transition | Rampe | Saut | Verdict de l'outil |
|---|---|---|---|---|
| 5,57 | zoomPunch `peak` 1,04 | 1 | 12,7 | À REVOIR (rampe déclarée de 3 images, une seule visible) |
| 10,03 | zoomPunch recalé (coupe franche + relâche) | 0 | 21,0 | À REVOIR (rampe, saut visible) |
| 13,00 | zoomPunch avec flou | 5 | 24,3 | OK |
| 22,13 | zoomPunch | 3 | 32,1 | À REVOIR (saut de source visible) |
| 29,67 | zoomPunch sans flou | 3 | 44,5 | À REVOIR (saut de source visible) |
| 35,53 | whip vers l'écran final | 3 à 4 | 51 à 68 | OK (luminance progressive) |

Le contrôle qualité V3.2 (mesures à la main) donnait : rampes de 5, 3 et 4 images à 13,00, 22,13 et 29,67, sauts de 23,7, 31,0 et 43,8. L'outil retrouve ces valeurs à une image près.
