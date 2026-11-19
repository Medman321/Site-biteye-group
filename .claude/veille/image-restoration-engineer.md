# Veille du 2026-11-19 — image-restoration-engineer

Recherches : 8 requêtes web (Real-ESRGAN et alternatives CPU, specs Reels, spandrel, WhatsApp, super-résolution vidéo récente, ffmpeg 8.x, TikTok/YouTube) et vérifications locales (PyPI, ffmpeg). Conteneur : 4 cœurs, pas de GPU. Les sources web sont des blogs ou pages de vendeurs : aucun débit n'est officiel. GitHub et huggingface.co sont bloqués par le proxy de cette session, donc les pages de releases et de modèles n'ont pas pu être lues.

## Constats

1. Aucune nouvelle version de Real-ESRGAN en 2026 : le dernier paquet PyPI `realesrgan` reste 0.3.0 (20/09/2022, vérifié sur l'API JSON de PyPI) et le build ncnn-vulkan reste v0.2.0 (avril 2022) — https://pypi.org/project/realesrgan/ — la chaîne `realesr-general-x4v3` ne change pas ; ne pas chercher de remplaçant sans GPU.
2. Aucun chiffre CPU publié pour l'agrandissement vidéo (les comparatifs 2026 ne donnent que du GPU ou du matériel AMD/NPU) — https://www.amd.com/en/developer/resources/technical-articles/2025/real-time-edge-optimized-ai-powered-parallel-pixel-upscaling-eng.html — notre mesure reste la référence : retex V2 = 1 110 images en ≈ 1 h 30 (≈ 5 s/image), à annoncer avant chaque lot.
3. `spandrel` 0.4.2 (21/02/2026) est toujours la dernière version (vérifié PyPI) ; charge les `.pth` sans `basicsr` et ajoute des architectures légères (RealPLKSR, MoSR) — https://pypi.org/project/spandrel/ — chemin à essayer en premier pour Real-ESRGAN sur CPU ; les architectures légères peuvent servir de plan B si x4v3 est trop lent, à tester sur 10 images.
4. `onnxruntime` 1.32.0 (13/11/2026, vérifié PyPI) : version à jour pour une inférence CPU ONNX — https://pypi.org/project/onnxruntime/ — repli si PyTorch n'est pas installé (c'était le cas le 24/10) ; il faut un export ONNX du modèle, à tester.
5. Les modèles de super-résolution vidéo récents (SeedVR2, FlashVSR, InstaVSR, Stream-DiffVSR) visent le GPU ; NanoVSR (ECCV 2026) et LIF-VSR (MDPI Sensors 2026) sont annoncés légers, sans chiffre CPU ni code vérifié — https://www.mdpi.com/1424-8220/26/2/637/html — rien à adopter ; garder le lissage temporel léger (`hqdn3d` temporel, `tmix`) après Real-ESRGAN pour limiter le scintillement.
6. Instagram : tout converge vers 1080×1920, H.264/AAC ; la lecture est plafonnée à 1080p, donc la 4K n'apporte que du poids, et les débits cités vont de 3,5 à 15 Mb/s sans source officielle — https://reap.video/blog/instagram-reels-size — confirme 1080 par défaut ; ne coder aucun débit.
7. WhatsApp : l'option « qualité d'origine » (sans compression) est seulement découverte dans une bêta Android (2.26.44.12, nov. 2026), non annoncée par Meta ; l'envoi « en document » reste le contournement connu — https://www.sammyfans.com/2026/11/06/whatsapp-is-testing-original-media-quality-option/ — ne pas promettre de qualité d'origine au demandeur ; garder la version WhatsApp ≤ 15 Mo et le contrôle de lisibilité à 720 p.
8. TikTok et YouTube recompressent tout ; les guides 2026 recommandent un débruitage léger puis une réduction de qualité haute, une netteté douce, et d'exporter depuis le fichier monté, pas depuis une copie téléchargée — https://unifab.ai/resource/how-to-make-tiktok-video-quality-better.htm — consolide notre chaîne (débruitage → agrandissement → lanczos → netteté légère) ; rappeler au cadrage de fournir le fichier d'origine de la caméra, jamais une copie WhatsApp.
9. Un guide signale qu'une image « plate » ou délavée après upload vient presque toujours de la gestion de couleur, pas du débit — https://www.spielcreative.com/blog/?p=20064 — hors de notre périmètre : à signaler au coloriste (agent 11) avant de blâmer la restauration.
10. Aucun nouveau débruiteur ffmpeg trouvé (pas de notes de version 8.1 lisibles) ; le wiki ffmpeg liste toujours 8 filtres de débruitage dont `hqdn3d`, `atadenoise`, `fftdnoiz`, `bm3d` — https://trac.ffmpeg.org/wiki/denoise — local : ffmpeg 6.1.1, `fftdnoiz` (FFT 3D) est disponible et peut être comparé à `hqdn3d` sur un plan bruité, sans promesse de gain.

## Outils vérifiés

- PyPI (API JSON, 19/11/2026) : `spandrel` 0.4.2 (21/02/2026), `onnxruntime` 1.32.0 (13/11/2026), `realesrgan` 0.3.0 (20/09/2022), `vsrife` 5.7.0 (09/02/2026), `opencv-python-headless` 5.1.0.95 (17/11/2026).
- ffmpeg local 6.1.1 (`ffmpeg -version`).
- Non vérifiables ici (GitHub et huggingface.co bloqués par le proxy) : releases Real-ESRGAN, NanoVSR ; cités d'après les résultats de recherche seulement.

## Écarté

- SeedVR2, FlashVSR, InstaVSR, Stream-DiffVSR, Video2X, Anime4K, CupScale, REAPPEAR (AMD) : GPU, NPU matériel, abandonnés ou par image sans cohérence temporelle ; inutilisables ou sans intérêt ici.
- NanoVSR et LIF-VSR : annoncés légers mais ni code ni poids vérifiés (accès bloqué) ; à revoir quand l'accès au modèle est ouvert.
- Topaz, UniFab, VideoProc, HitPaw, services en ligne : payants.
- Débits et durées Instagram, TikTok, YouTube, WhatsApp des blogs : contradictoires, non officiels ; jamais codés en dur.
- Option « qualité d'origine » de WhatsApp : bêta non confirmée.
