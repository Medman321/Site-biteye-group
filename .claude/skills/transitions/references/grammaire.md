# Grammaire des raccords BitEye : relation entre deux scènes → transition

À lire au moment de remplir `transitions.json`. Une ligne par relation : quand l'utiliser, la transition du moteur et ses paramètres de départ, le son, les pièges. Les paramètres sont des **points de départ** : la mesure (`transition_audit.py cuts`) tranche. Temps à 30 i/s : 1 image = 0,033 s.

Notations : `cut` = image où le plan change ; rampe = images de mouvement ou de flou juste avant `cut` ; J-cut = le son de B arrive avant son image ; L-cut = le son de A continue sur l'image de B. Sens de lecture : en français, « en avant » = le contenu part vers la gauche (`dir: "left"`) ; en arabe (sous-titres RTL), l'inverse : décider une fois pour tout le film.

## 1. Relations et transitions

| # | Relation entre A et B | Transition du moteur | Paramètres de départ | Son (pour le sound designer) | Pièges |
|---|---|---|---|---|---|
| R1 | **Même intervenant, même idée** (coupe dans la phrase, coupe cachée de la source qu'on garde) | `zoomPunch` pic puis retour, sur une respiration de la voix | `at` = cut − 0,133 (4 img), `dur` 0,3, `from` 1,00, `peak` 1,06, `to` 1,12 (alterner 1,12 ↔ 1,00 au punch suivant), `origin` sur les yeux ("50% 35%"), `blur` 1,2 si la source change d'expression | aucun raccord (voix continue) ; micro-souffle 0,1 s ou rien ; pas d'impact sur chaque punch | punch sans rampe (V3 : 10,03 et 17,17 mesurés à 0 image) ; saut d'expression visible (V3 : 29,67 sourire → « ou ») : choisir l'image de coupe bouche fermée ou au clignement, sinon flou plus fort |
| R2 | **Même intervenant, idée nouvelle** (nouveau chapitre, liste) | `zoomPunch` plus fort ou `whip` court | punch : `peak` 1,10, `to` 1,00 ; whip : 8 img, `dir` « en avant » | souffle + petit impact sur `cut` ; ou fuite de lumière (bibliothèque n° 13, 2 au plus par vidéo) | trop de whips (> 6 en 20 s, bibliothèque n° 3) |
| R3 | **Changement d'intervenant** (témoin A → témoin B), un seul par vidéo | `maskReveal` (B naît dans la silhouette de A) ; sinon `zoomThrough` dans un mot-pont | maskReveal : `grow` 7, `origin` sur le buste, `ease` `area` (pas de saut de luminance), 0,8 s ; zoomThrough : `el` = mot-pont, `to` 16, `fill` couleur d'accent mesurée | **J-cut** : voix de B 0,2 à 0,4 s avant son image ; nappe qui gonfle pendant le masque | jamais de coupe sèche entre deux personnes ; pont de sens obligatoire (scénariste) |
| R4 | **Changement d'intervenant à cadrage égal** (deux visages de même taille et même hauteur) | `matchCut` | `faceA`, `faceB` = centre et hauteur des visages (mesurés : `transition_audit.py cuts` note Δx, Δy, taille), `pre` 0,25 | coupe sur un temps fort de la musique, accent bref | écart de taille > 1,3 : le recadrage se voit ; la plus petite tête est agrandie, jamais l'inverse |
| R5 | **Problème → solution** (contraste, avant / après) | `zoomThrough` dans le mot du problème (« Excel ») qui remplit l'écran, puis la solution | `to` 16, `fromB` 1,8, `fill` = couleur du mot, coupe à 62 % | **creux de 0,3 s** puis impact sur l'arrivée de la solution (bibliothèque : « creux puis impact ») | le mot doit être lisible avant la plongée (≥ 0,6 s à l'écran) |
| R6 | **Visage → écran du logiciel** (maquette `app`, `phone`, `schedule`) | `whip` dans le sens du regard ou du geste de l'intervenant (raccord regard) ; ou `zoomThrough` dans un objet (téléphone, écran) | whip 8 img, `dir` = côté du regard, `blur` 1 ; zoomThrough `el` = l'objet | **L-cut** : la voix continue sur l'écran ; souffle + clic d'interface léger à l'arrivée | regard vers la droite et whip vers la gauche = faux raccord ; aucune vraie interface du logiciel |
| R7 | **Écran → visage** (retour à l'intervenant) | `zoomPunch` arrière (`from` 1,12 → `to` 1,00) ou `maskReveal` cercle depuis l'écran | cercle : `shape` "circle", `x`,`y` = centre de l'écran, `ease` `area` | J-cut court (0,15 s) si la phrase reprend | whip de retour en sens inverse seulement si l'aller était un whip (aller-retour lisible) |
| R8 | **Saut de lieu ou de temps** (chantier → bureau, « 6 mois plus tard ») | `whip` (même direction dans tout le film) ; ou `matchCut` sur la forme (tour ↔ barre de graphique) | whip 8 à 10 img, `blur` 1 ; carton de temps si besoin | souffle long + **ambiances croisées** 0,3 s (room tone de B sous la fin de A) | changer de direction de whip au milieu du film ; plus de 2 sauts de lieu en 40 s |
| R9 | **Photo → photo** (galerie, avant / après, plans d'un même chantier) | `matchCut` sur la forme si les photos se superposent ; sinon fondu enchaîné par calques (`layers[].out` de A et `in` de B, 6 à 10 img) avec `drift` dans le même sens | drift `x` même signe sur A et B (le Ken Burns continue), fondu ≥ 6 img | coupe sur le temps de la musique, déclencheur léger | Ken Burns qui s'inverse à la coupe ; fondu < 4 images (image fantôme) |
| R10 | **Accroche → corps** (après 1,5 s) | `zoomPunch` pic ou flash (`flashes`) | `peak` 1,08, rampe 3 img | coup de grave à la coupe | flash de plus d'une image (gêne et saut de luminance) |
| R11 | **Fin → appel à l'action** | `whip` (changement de rythme) ou `zoomPunch` `target: "scene"` dans l'œil du logo | whip 8 img ; punch `to` 1,4 sur le logo | L-cut sur les derniers mots, puis jingle ; souffle + impact | CTA qui arrive pendant le flou ; whip vers un fond sombre = saut de luminance (V3 : 35,53, 25 par image), le rendre progressif |
| R12 | **Carton ou texte ↔ plan** | coupe franche sur le temps acceptée en standard ; en premium `maskReveal` cercle ou fondu 6 à 10 img | — | sur le temps de la musique | carton sans mouvement (caméra vivante obligatoire en premium) |
| R13 | **Même mouvement des deux côtés** (geste, marche, panoramique) | coupe sur l'action (au premier tiers du geste) + `whip` dans le même sens si le mouvement est rapide | — | le son du geste chevauche la coupe | direction inversée de part et d'autre (mesurée : « direction inversée ») |

## 2. Règles de raccord (rappel)

- **Coupe sur l'action** : couper pendant le mouvement, au premier tiers, pour que l'œil suive le geste au lieu de voir la coupe.
- **Règle des 180°** : garder les personnes du même côté de l'axe ; un témoin qui regarde à droite dans A reste à droite dans la scène suivante s'il « répond ».
- **Raccord regard** : la direction du regard en A annonce ce que montre B (écran, autre témoin) ; même échelle de plan pour qu'il se lise.
- **Raccord sur la forme** (match cut) : même forme, même place à l'écran (visage ↔ visage, tour ↔ barre) ; mesurer les centres, pas à l'œil.
- **J-cut et L-cut** : J quand B doit intriguer (on l'entend avant de le voir), L quand la parole porte l'émotion et continue sur l'image suivante ; pour une démo directe, coupe franche sur le temps.
- **Transition motivée** : chaque mouvement de transition a une raison à l'image (geste, regard, mot) ou au son (temps de musique, respiration). Sans raison, on garde la coupe la plus simple qui passe les seuils.
- **Reels et TikTok** : la tendance 2025-2026 va vers peu d'effets, des coupes rapides et des visages réels ; une transition voyante se garde pour les 2 ou 3 changements qui portent le sens (témoin, chapitre, CTA).

## 3. Choisir quand deux transitions conviennent

1. Celle qui garde la direction du mouvement déjà établie dans le film.
2. Celle dont la rampe est la plus facile à rendre visible (une rampe de 3 images mesurées, pas déclarées).
3. Celle qui ne change pas la luminance moyenne de plus de 12 par image.
4. En cas de doute de goût : planche de 3 niveaux (même transition, 3 intensités) au demandeur, jamais un rendu.
