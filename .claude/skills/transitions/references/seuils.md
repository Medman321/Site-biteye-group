# Seuils mesurables des transitions (valeurs par défaut de `transition_audit.py`)

Toutes les mesures se font sur l'image réduite à 270×480 (écarts, flux, luminance) ou 540×960 (netteté, visages), à la cadence de la vidéo (30 i/s). Un seuil changé pour un projet est écrit dans `transitions.json` (`seuils`) avec sa raison.

| Mesure | Définition | Seuil par défaut | Option | Origine |
|---|---|---|---|---|
| Coupe franche | écart moyen BGR (0-255) entre t−1 et t ; image recalée sur le plus grand saut à ±3 images, sauf si la coupe déclarée est franche, d'écart ≥ 0,5 × ce saut et précédée d'images toutes franches (zoom fort : elles sont sa rampe) | ≥ 12 | `--hard` | en dessous, coupe douce ou fondu : rampe non exigée ; V3 17,17 (zoom ×1,41 en 4 images pris pour la coupe) |
| **Rampe avant** | images consécutives juste avant la coupe où l'un de ces signes dépasse la référence calme du plan : flux optique moyen ≥ max(0,8 px ; 1,5 × réf.), composante zoom ≥ max(0,35 px ; 2 × réf.), écart image à image ≥ max(4 ; 2 × réf.), netteté (variance du laplacien) ≤ 0,85 × réf. et en baisse, écart des yeux qui varie de ≥ max(1,5 % ; 2 × réf.) par image | **≥ 3 images** | `--ramp`, `--mag`, `--div`, `--dmin`, `--blur`, `--face-zoom` | `.claude/CLAUDE.md` (Efficacité, Transitions) ; retex V3 |
| Bandes fixes | pixels figés (écart ≤ 1 sur toute la fenêtre de la coupe : barre de marque, cadre, sous-titre posé) exclus du flux, s'il reste ≥ 20 % de l'image | — | `--static` | ils diluaient le zoom mesuré (V3, 5,57) |
| Relâche après | même calcul après la coupe | information (exigée ≥ 3 pour `maskReveal`, fondus) | — | — |
| Référence calme | quartile bas de t−20 … t−6 (sans dépasser la coupe précédente) | — | — | évite qu'une transition voisine fausse la référence |
| **Saut visible** | coupe franche d'écart ≥ 18 que ni le flou (netteté t−1 ≤ 0,5 × réf.) ni le mouvement (flux t−1 ≥ 3 px) ne masquent | aucun | `--visible`, `--mask-blur`, `--mask-flow` | V3 : 22,13 (32) et 29,67 (44) vus par le demandeur |
| **Luminance** | écart de luminance moyenne entre t−1 et t | ≤ 12 ; au-delà, « brutal » seulement s'il fait plus de 2 × les sauts voisins (sinon « progressive », en note) | `--luma` | grille du DA (YAVG > 12 = à examiner) |
| **Visage coupé** | boîte du visage à moins de 1 % du bord du cadre à t−1, t ou t+1 | aucun | — | retex V2 (visage coupé 9-14 s) |
| **Visage qui saute** | coupe franche non masquée (ni flou ni mouvement à t−1), même taille de visage (×0,7 à ×1,4), centre des yeux décalé entre t−1 et t de plus de 2 % de la largeur | aucun | `--face-jump` | V3, 10,03 : 8,4 % (Δx −76, Δy −48 px), la plainte « visage du témoin qui se coupe » |
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
| 5,57 | zoomPunch `peak` 1,04 | 2 (1 avant la mesure par les yeux) | 12,7 | À REVOIR (rampe déclarée de 3 images, défaut mesurable seulement) |
| 10,03 | zoomPunch recalé (coupe franche + relâche) | 0 | 21,0 | À REVOIR (rampe, saut visible, visage qui saute de 8,4 %) |
| 11,27 | zoomPunch sans rampe (`at` = `cut`) | 2 | 21,0 | À REVOIR (vu après la correction de l'image de coupe : visage qui saute de 8,3 %) |
| 13,00 | zoomPunch avec flou | 5 | 24,3 | OK |
| 17,17 | zoomPunch ×1,41 en 4 images, sans relâche | 3 | 26,3 | OK (avant : coupe prise à 17,07, rampe 0, faux positif) |
| 22,13 | zoomPunch | 3 | 32,1 | À REVOIR (saut de source visible, visage qui saute de 5,5 %) |
| 29,67 | zoomPunch sans flou | 3 à 6 | 44,5 | À REVOIR (saut de source visible, visage qui saute de 14,3 %) |
| 35,53 | whip vers l'écran final | 3 à 4 | 51 à 68 | OK (luminance progressive) |

Le contrôle qualité V3.2 (mesures à la main) donnait : rampes de 5, 3 et 4 images à 13,00, 22,13 et 29,67, sauts de 23,7, 31,0 et 43,8. L'outil retrouve ces valeurs à une image près.
