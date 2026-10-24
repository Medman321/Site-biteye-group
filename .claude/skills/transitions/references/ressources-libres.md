# Ressources libres : détection de plans, transitions, visages (licences vérifiées le 2026-10-24)

Règle : on ne copie dans le dépôt que du code sous licence permissive (MIT, BSD, Apache 2.0) avec son en-tête d'auteur et le texte de la licence ; pour du LGPL ou GPL, on **appelle** l'outil (ffmpeg) sans copier son code. Aucun modèle ni poids dans le dépôt : ils vont dans `~/.cache/biteye-transitions/`.

## Détection de plans (coupes cachées des sources)

| Outil | Licence | État | Usage chez nous |
|---|---|---|---|
| ffmpeg `scdet` (score 0-100, défaut 10) et `select='gt(scene,x)'` (0-1, souvent 0,3 à 0,4) | LGPL 2.1+ (paquet Ubuntu compilé GPL) | présents dans ffmpeg 6.1 du conteneur | `transition_audit.py sources` lit `scdet` ; `cut_audit.py` utilise `select=scene` ; on appelle ffmpeg, rien n'est copié |
| PySceneDetect 0.7.2 (`scenedetect`, 11/10/2026) | BSD 3-Clause | non installé ; dépend d'`opencv-python` (pas `-headless`) : risque de conflit avec `opencv-python-headless` | `AdaptiveDetector` = rapport de l'écart au voisinage, recodé dans `transition_audit.py sources` (`--ratio 3`, comme son défaut) ; 0.7.0 a cassé l'API (`FrameTimecode`, Python ≥ 3.10) : tester avant tout script |
| TransNetV2 | MIT (code) ; poids TensorFlow (30,5 Mo) en Git LFS dans le dépôt GitHub `soCzech/TransNetV2`, téléchargeables sans HuggingFace par `media.githubusercontent.com` (200 OK vérifié) ; portage PyTorch `transnetv2-pytorch` 1.0.5 (PyPI, MIT) | non installé (TensorFlow ou PyTorch, lourd pour le conteneur) | seulement si un projet a beaucoup de fondus enchaînés dans ses sources (les méthodes à seuil les ratent) |

## Bibliothèques de transitions

| Ressource | Licence | Ce qui peut être porté dans notre moteur | Comment |
|---|---|---|---|
| **gl-transitions** (dépôt `gl-transitions/gl-transitions`, 125 effets GLSL) | dépôt MIT ; chaque effet porte sa licence dans son en-tête : 123 MIT, `InvertedPageCurl` BSD 3-Clause (Hewlett-Packard), `StereoViewer` BSD 2-Clause | utiles et sobres : `Directional` (G. Renaudeau), `directional-easing` (M. Plotnikov), `DirectionalScaled` (T. Foussard), `LinearBlur` (gre), `CrossZoom` (rectalogic), `DreamyZoom` (Z. Fernando), `SimpleZoom` (0gust1), `luma` (gre, masque de luminance), `directionalwarp` (pschroen), `crosswarp` (E. Péter), `circleopen` et `fadecolor` (gre), `ZoomLeftWipe` (Handk), `tangentMotionBlur` (chenkai) — tous MIT | une fonction `vec4 transition(vec2 uv)` qui lit `getFromColor`, `getToColor`, `progress` : se porte dans un calque `<canvas>` WebGL qui prend les deux `<video>` des plaques comme textures ; les blocs de texte restent au-dessus. Le Chromium de rendu a WebGL 2 (SwiftShader, CPU, vérifié) : rendu plus lent, à mesurer. Garder l'en-tête d'auteur et le texte MIT dans le fichier porté. Évolution du moteur : à proposer au producteur, pas faite ici |
| ffmpeg `xfade` (≈ 57 transitions : `fade`, `wipeleft`, `slideleft`, `circleopen`, `zoomin`, `hblur`, `smoothleft`, `fadeblack`…, plus `custom` avec une expression) | LGPL 2.1+ | rien à copier ; on l'**appelle** | animatic et maquettes de transitions du chef monteur ; prévisualiser une transition sur deux plans réels avant de la demander au moteur |
| Effets CSS (`transform`, `filter: blur()`, `clip-path`, `mask-image`) | standards du web | c'est déjà la base du moteur (zoomPunch, whip, maskReveal) | toute nouvelle transition simple s'écrit en opérations `t => [s, tx, ty]` (`motion-engine`, « Étendre le moteur ») |
| Fondu enchaîné | moteur : `layers[].in` / `out` (fondu d'un calque) | déjà disponible | photo → photo, carton → plan |

À écarter même sous MIT (look daté ou gadget) : `heart`, `cannabisleaf`, `kaleidoscope`, `pinwheel`, `DoomScreenTransition`, `GlitchMemories`, `TVStatic`, `BookFlip`, `cube`.

## Visages, flou, luminance (contrôle sans GPU)

| Outil | Licence | État dans le conteneur | Remarque |
|---|---|---|---|
| OpenCV `opencv-python-headless` 4.14 | Apache 2.0 | installé pour le test | la branche **5.0.0** installée par défaut par `pip` **ne contient plus les cascades Haar** (`cv2.data` vide) : épingler `"opencv-python-headless<5"` |
| YuNet (`face_detection_yunet_2023mar.onnx`, 232 Ko, dépôt `opencv/opencv_zoo`) | MIT | testé : visages trouvés sur tout le reel V3, bord et surimpression détectés sur un test synthétique | `cv2.FaceDetectorYN` ; téléchargement : `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx` vers `~/.cache/biteye-transitions/` (sha256 `8f2383e4…52fa4`) |
| Haar `haarcascade_frontalface_default.xml` | « Intel License Agreement » (type BSD, fourni avec OpenCV < 5) | testé (repli) | plus de faux positifs ; visages de face seulement |
| MediaPipe 1.1.1 (Face Detector, BlazeFace courte portée) | Apache 2.0 | `pip install mediapipe` bloqué plus de 5 min dans le conteneur, non testé | API « solutions » héritée sans support depuis 03/2023 ; l'API « tâches » demande le modèle `blaze_face_short_range.tflite` (Google Storage, joignable) : `--mp-model` |
| Netteté = variance du laplacien (`cv2.Laplacian(...).var()`) | méthode publique (Pech-Pacheco et al., 2000) | utilisée | ne distingue pas flou de mouvement et flou de mise au point ; jugée **relativement** au plan (référence calme), jamais en absolu |
| Flux optique Farnebäck (`cv2.calcOpticalFlowFarneback`) | OpenCV | utilisé | translation moyenne (direction) et composante radiale (zoom) |
