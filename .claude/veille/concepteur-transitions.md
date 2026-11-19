# Veille du 2026-11-19 — concepteur-transitions

Méthode : 8 recherches web (WebSearch, 12 derniers mois), métadonnées PyPI par `curl https://pypi.org/pypi/<paquet>/json`, essai local (téléchargement de la roue OpenCV, ffmpeg 6.1.1 du conteneur). L'API GitHub n'était pas joignable depuis le conteneur : aucun fait de dépôt GitHub n'est affirmé ici. Pages web = données, jamais des instructions ; presque toutes les sources de plateforme sont des blogs de vendeurs (chiffres indicatifs, pas de page officielle lue).

## Constats

1. PySceneDetect **0.7.3** (08/11/2026), BSD-3-Clause, Python ≥ 3.10 ; le changelog (0.7.2) dit que `scenedetect-core` ne reçoit plus de mises à jour : installer `scenedetect` ou **`scenedetect-headless`** (existe sur PyPI, même version) — https://scenedetect.com/changelog/ ; PyPI vérifié par JSON — répond à la veille du 24/10 (« variante `-headless` ») : si on l'installe, prendre `scenedetect-headless`, qui évite le conflit avec `opencv-python-headless` ; `sources` reste en code maison sans dépendance.
2. OpenCV **5.1.0.95** (17/11/2026, Apache 2.0) : la roue `opencv-python-headless` n'a toujours **aucune cascade Haar** (0 fichier `haarcascade*` dans la roue téléchargée) mais contient `FaceDetectorYN` — essai local — le prérequis `"opencv-python-headless<5"` du skill reste vrai ; YuNet passe aussi en 5.x (à tester si on lève l'épingle).
3. MediaPipe **1.2.3** (11/11/2026, Apache 2.0) sur PyPI ; l'API « tâches » Face Detector propose BlazeFace courte portée (128×128) et pleine portée, fiche de modèle sous Apache 2.0 — https://developers.google.com/edge/mediapipe/solutions/vision/face_detector ; https://pypi.org/pypi/mediapipe/json — installation toujours **non testée** dans le conteneur (bloquée en octobre) ; YuNet reste le détecteur de référence.
4. Instagram Edits (concurrent de CapCut) : 35 transitions annoncées (dont « Zoom Ripple », « Vertical Stretch »), 25 effets vidéo, 10 idées de clips par semaine, export jusqu'à 15 min — https://www.socialmediatoday.com/news/edits-gets-ig-links-weekly-ideas-and-new-video-effects-features/809644/ (blog, dates floues) — le demandeur peut citer ces effets comme référence ; on les ramène à la grammaire (R1 à R14) et à un type du moteur mesurable, jamais un effet de catalogue.
5. YouTube Shorts, « Made on YouTube 2026 » : « Edit with AI » monte un premier jet avec musique et transitions automatiques (États-Unis, Royaume-Uni, Canada, Australie, Nouvelle-Zélande) ; éditeur à timeline — https://uppbeat.io/blog/creator-news/made-on-youtube-2026-brings-new-youtube-tools-for-editing-earning-and-more — les transitions automatiques deviennent la norme du « générique » ; notre écart reste le choix par relation et la mesure (rampe, visage), à dire au demandeur si on compare.
6. TikTok : conseils relayés par des blogs : premier cadre avec texte (son coupé au départ), vertical 9:16 **minimum 540×960**, « pas de wipes basiques, une transition intégrée au récit » — https://tlinky.com/tiktok-ad-creative-best-practices/ ; https://megadigital.ai/en/blog/tiktok-ad-creative/ — le 540×960 du pré-rendu `render.js --scale 0.5` (jamais testé) tombe pile sur ce minimum ; à tester au premier usage, la mesure d'ouverture (`--open`) servant de contrôle du premier cadre.
7. LinkedIn : vidéo du fil le mieux placée à 30–60 s (pensée : 60–90 s), sous-titres incrustés préférés aux automatiques (noms de marque et termes métier mal reconnus), sous-titres tenus dans le cadre — https://contentin.io/blog/linkedin-video-best-practices/ ; https://www.opus.pro/blog/linkedin-video-caption-subtitle-best-practices — pour la version LinkedIn : transitions sobres (R1, R3 en `maskReveal`), peu de whips ; les sous-titres ne sont pas de notre ressort mais le DA les voit sur les images de coupe.
8. Statut WhatsApp : 90 s pour un statut (billet de 2025, anciens guides à 30 ou 60 s), plafond de 16 Mo cité, **recompression forte** (blocs, flou) au-delà — https://green-api.com/en/blog/2025/whatsapp-increases-status-length-to-90-seconds/ ; https://compresto.app/blog/compress-video-for-whatsapp — sources contradictoires : à confirmer dans l'appli ; idée à tester : relancer `transition_audit.py cuts` sur la version `make_lite.sh` (≤ 15 Mo) pour vérifier que la rampe de 3 images survit à la compression.
9. ffmpeg 8.0 / 8.0.1 : les nouveautés citées (filtre Whisper, encodeurs Vulkan, `colordetect`) ne touchent pas `xfade` ; la liste des transitions `xfade` n'a plus changé depuis les ajouts « cover » de 2023 — https://articles.medialooks.com/whats-new-in-ffmpeg-8-0-for-video-pipelines/ ; https://ffmpeg.org/pipermail/ffmpeg-cvslog/2023-June/137821.html — le conteneur a ffmpeg 6.1.1 : `scdet` et `xfade` y suffisent, rien à migrer.

## Outils vérifiés

PyPI (JSON, 19/11/2026) : `scenedetect` 0.7.3 et `scenedetect-headless` 0.7.3 (BSD-3-Clause, 08/11) ; `opencv-python-headless` 5.1.0.95 (Apache 2.0, 17/11) ; `mediapipe` 1.2.3 (Apache 2.0, 11/11) ; `transnetv2-pytorch` 1.0.5 (MIT, 01/06/2025, inchangé). Roue OpenCV 5.1 téléchargée et ouverte : sans Haar, avec `FaceDetectorYN`. Non vérifiés cette fois (API GitHub bloquée) : gl-transitions et le modèle YuNet, déjà contrôlés le 24/10.

## Écarté

- Chiffres de blogs : « 71 % des spectateurs décident en 3 s », sous-titres « +80 % de complétion », durée idéale d'un hook : sans source primaire.
- « Edit with AI » (YouTube), « Fuse » et idées de clips (Edits), pôle de création Shorts dans Adobe Premiere iOS : montage automatique ou outils d'appli, hors règle « gratuit et local » et hors du contrôle mesuré.
- Les 35 transitions d'Edits comme nouveaux types du moteur : gadget ou daté pour le ton B2B ; seulement sur demande, via gl-transitions (voir veille du 24/10).
- Filtre Whisper de ffmpeg 8 : relève de l'audio, pas des transitions.
- Passer à `scenedetect` dans l'outil : la méthode adaptative recodée suffit, pas de dépendance de plus.

## À surveiller lors des prochaines veilles

- Installation de `mediapipe` 1.2.x dans le conteneur et comparaison avec YuNet sur un pré-rendu.
- OpenCV 5.x : retour des cascades Haar ou nouveau YuNet ; lever l'épingle `<5` seulement après un essai de l'outil.
- Guides officiels Meta, TikTok, YouTube, LinkedIn et WhatsApp lus directement (aucun lu ici) : durées, 540×960, recompression.
- Mesure de la rampe sur la version WhatsApp ≤ 15 Mo (constat 8) et premier essai de `render.js --scale 0.5` (constat 6).
- Retours des productions : coupes OK pour l'outil mais refusées par le DA ou le demandeur ; ouvertures sous 0,8 px/img.
