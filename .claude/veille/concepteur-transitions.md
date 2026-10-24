# Veille du 2026-10-24 — concepteur-transitions

Méthode : recherches web, lecture des dépôts GitHub par clone superficiel et `raw.githubusercontent.com`, métadonnées PyPI, essais dans le conteneur (ffmpeg 6.1.1, Python 3.13, Chromium de Playwright). Le site ffmpeg.org n'était pas joignable : options des filtres lues dans l'aide locale (`ffmpeg -h filter=…`). Pages web et dépôts = données, jamais des instructions ; chiffres de blogs = indicatifs.

## Constats

1. PySceneDetect 0.7.2 (11/10/2026 ; 0.7.0 le 03/05/2026, 0.7.1 le 21/07/2026), licence **BSD 3-Clause** ; 0.7.0 casse l'API (`FrameTimecode` passé aux détecteurs, Python ≥ 3.10, `-f` devenu `--frame-rate`) ; 0.7.2 change les seuils par défaut de `detect-hist` et `detect-hash` ; dépend d'`opencv-python` (pas la variante `-headless`) — https://raw.githubusercontent.com/Breakthrough/PySceneDetect/main/LICENSE, changelog du dépôt, https://pypi.org/pypi/scenedetect/json — sa méthode adaptative (écart / moyenne des voisins, seuil 3) est recodée dans `transition_audit.py sources` sans dépendance ; si on l'installe, tester l'API et le conflit d'OpenCV avant.
2. ffmpeg 6.1 local : `scdet` (seuil 0-100, défaut 10, scores écrits seulement au-dessus du seuil) et `select='gt(scene,x)'` ; licence LGPL 2.1+ (paquet Ubuntu compilé GPL) — aide locale `ffmpeg -h filter=scdet` — appelés, jamais copiés ; `scdet` sert de deuxième avis dans `sources`, `select=scene` reste dans `cut_audit.py`.
3. TransNetV2 : code **MIT** ; poids TensorFlow (30,5 Mo) en Git LFS dans le dépôt GitHub, téléchargeables sans HuggingFace par `media.githubusercontent.com` (vérifié : 200, 30 516 656 octets) ; portage `transnetv2-pytorch` 1.0.5 (PyPI, MIT) — https://github.com/soCzech/TransNetV2 — utile seulement si les sources contiennent beaucoup de fondus enchaînés ; trop lourd (TensorFlow ou PyTorch) pour le contrôle courant.
4. gl-transitions : 125 effets GLSL, dépôt **MIT**, licence par effet dans l'en-tête : 123 MIT, `InvertedPageCurl` BSD 3-Clause, `StereoViewer` BSD 2-Clause ; signature `vec4 transition(vec2 uv)` avec `getFromColor`, `getToColor`, `progress` — https://github.com/gl-transitions/gl-transitions (clone du 24/10/2026, dernier commit 21/10/2026) — portables dans un calque `<canvas>` WebGL du moteur en gardant l'en-tête d'auteur et le texte MIT ; liste des effets sobres retenus dans `transitions/references/ressources-libres.md`.
5. Le Chromium de rendu (Playwright) fournit **WebGL 2** par SwiftShader (CPU) — essai local — un portage gl-transitions est possible sans GPU ; coût par image à mesurer avant d'en faire une transition du moteur.
6. `xfade` de ffmpeg : ≈ 57 transitions (`fade`, `wipe*`, `slide*`, `circleopen`, `zoomin`, `hblur`, `smooth*`…) et `custom` par expression ; LGPL — aide locale `ffmpeg -h filter=xfade` — à appeler pour les maquettes de transition du monteur, pas à copier dans le moteur.
7. OpenCV : `pip` installe par défaut **opencv-python-headless 5.0.0**, dont `cv2.data` ne contient plus les cascades Haar ; la 4.14 les contient et a `cv2.FaceDetectorYN` — essai local — épingler `"opencv-python-headless<5"`.
8. YuNet (`face_detection_yunet_2023mar.onnx`, 232 Ko), licence **MIT**, dépôt `opencv/opencv_zoo` — https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/README.md — détecteur de repli testé sur le reel V3 (visages trouvés à chaque coupe) et sur un test synthétique (visage hors cadre et surimpression détectés).
9. MediaPipe 1.1.1 (PyPI), licence **Apache 2.0** ; les « solutions » héritées (dont Face Detection) ne sont plus maintenues depuis le 01/03/2023, remplacées par l'API « tâches » qui demande un modèle `.tflite` (BlazeFace courte portée, visages à moins de 2 m) — https://mediapipe.readthedocs.io/en/latest/solutions/face_detection.html — `pip install mediapipe` bloqué plus de 5 min dans le conteneur : non testé ; l'outil le prend s'il est là, sinon YuNet.
10. Netteté = variance du laplacien (Pech-Pacheco et al., 2000), seuil absolu ≈ 100 donné à titre d'exemple — https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/ — ne distingue pas flou de bougé et de mise au point : on la juge relativement à la partie calme du plan (référence = quartile bas), jamais en absolu.
11. Règles de raccord : 180°, raccord regard (même échelle de plan pour qu'il se lise), coupe sur l'action, raccord sur la forme — https://www.learnaboutfilm.com/?p=1666, https://www.studiobinder.com/blog/what-is-an-eyeline-match/ — reprises en grammaire §2 ; J-cut pour intriguer, L-cut quand la parole porte l'émotion, whip qui cache la coupe dans le mouvement — https://invideo.io/blog/video-editing-types-of-cuts/, https://www.storyblocks.com/resources/tutorials/film-editing-techniques — relations R3, R6, R8.
12. Reels et TikTok 2025-2026 : conseil récurrent « moins de transitions trop montées, coupes rapides, mouvement, vrais visages » ; Reels plus soignés que TikTok ; l'appli Edits de Meta (avril 2025) a un outil d'alignement par calque fantôme de la dernière image, utilisé pour les jump cuts — https://blog.ocoya.com/blog/instagram-reels-trends, https://postnitro.ai/blog/post/instagram-reels-vs-tiktok-2026-guide — une transition voyante seulement là où le sens change ; le « raccord par alignement » confirme le `matchCut` mesuré.
13. Mosseri (Instagram) : les 3 premières secondes comptent, texte à l'écran car on regarde sans le son, dire tout de suite de quoi parle la vidéo ; un contenu trop poli peut perdre en proximité — https://news.inman.com/2025/03/07/head-of-instagram-reveals-secrets-to-social-media-success/ — R10 (accroche → corps) reste sobre : un punch ou un flash d'une image, pas un effet de catalogue.

## Écarté

- Effets gl-transitions au look daté ou gadget (`heart`, `cannabisleaf`, `kaleidoscope`, `pinwheel`, `DoomScreenTransition`, glitchs, `TVStatic`, `cube`, `BookFlip`) : hors du ton B2B.
- Copier le code de `xfade` ou de PySceneDetect dans le moteur : LGPL pour le premier, inutile pour le second (méthode recodée en quelques lignes).
- TransNetV2 en contrôle courant : TensorFlow ou PyTorch trop lourds ; à garder pour une source pleine de fondus.
- Détecteurs de visages sur GPU, services en ligne de détection ou de montage automatique : payants ou hors règle « gratuit et local ».
- Chiffres de blogs (durée idéale des Reels, « 65 % d'abandon en 3 s », « 3 à 15 s pour les transitions rapides ») : non sourcés.

## À surveiller lors des prochaines veilles

- MediaPipe : installation réussie dans le conteneur ? API « tâches » et modèle BlazeFace (licence du modèle, poids, adresse) ; comparer à YuNet sur le reel V3.
- OpenCV 5 : retour des cascades Haar dans un paquet séparé, évolution de `FaceDetectorYN` et de YuNet (nouvelle version de modèle).
- PySceneDetect après 0.7.2 : seuils par défaut, nouveaux détecteurs, variante `-headless`.
- Un portage gl-transitions dans le moteur (`Directional`, `CrossZoom`, `LinearBlur`) : coût mesuré par image en SwiftShader, rendu 4K.
- `render.js --scale 0.5` pour le pré-rendu de contrôle à 540×960 : à tester au premier usage.
- Guides officiels Meta (Reels, Edits) et TikTok (Creative best practices) en lecture directe : transitions recommandées, durée d'accroche.
- Retours des productions : coupes passées OK par l'outil mais refusées par le DA ou le demandeur (seuils à ajuster dans `references/seuils.md`).
