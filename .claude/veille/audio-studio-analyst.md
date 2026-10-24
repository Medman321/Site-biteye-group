# Veille du 2026-10-24 — audio-studio-analyst

Méthode : 9 recherches web (12 derniers mois), versions vérifiées sur PyPI le 2026-10-24, options ffmpeg vérifiées en local (ffmpeg 6.1.1). Le conteneur n'ouvre pas les pages web (WebFetch bloqué), donc les constats viennent des résumés de recherche : fiabilité moyenne, à confirmer par une mesure locale avant de changer une règle.

## Constats

1. Mastering en deux passes : mesure `loudnorm` (`print_format=json`), puis seconde passe avec `measured_I/LRA/TP/thresh` et `linear=true` ; `LRA` cible haute (≈ 20) pour éviter le repli en mode dynamique ; `dual_mono=true` pour une voix mono lue sur haut-parleur stéréo — https://www.animethemes.moe/wiki/encoding/workflow et https://github.com/slhck/ffmpeg-normalize — notre mastering passe en 2 passes linéaires, avec contrôle `ebur128` ensuite (options confirmées dans ffmpeg 6.1.1 local).
2. −14 LUFS / −1 dBTP pour Instagram, TikTok, LinkedIn est une convention d'outils, pas une règle officielle publiée par les plateformes ; YouTube ne fait que baisser ce qui dépasse −14 — https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026 et https://opus.pro/blog/best-loudness-normalizers — on garde −14 ±0,5 ; ne jamais écraser la dynamique pour « sonner plus fort » (sinon baisse plus forte à la lecture).
3. Instagram Reels : audio AAC, 48 kHz maximum, mono ou stéréo, ≈ 128 kbit/s ; si l'import échoue, ré-encoder — https://www.ayrshare.com/docs/media-guidelines/instagram (guide tiers, pas Meta) — livrer l'audio en AAC-LC 48 kHz ≥ 128 kbit/s ; garder −1,5 dBTP de marge pour le ré-encodage de la plateforme.
4. Le débruitage neuronal dégrade la reconnaissance vocale (une fiche modèle DeepFilterNet3 note un WER de 0,533 à 0,583) — https://huggingface.co/soniqo/DeepFilterNet3-ONNX — aligner et transcrire sur la voix d'origine (ou à peine nettoyée), réserver `voix_studio.wav` à l'écoute et au mixage ; les temps restent identiques puisque le minutage n'est pas modifié. À mesurer sur un extrait avant d'en faire la règle.
5. Silero VAD 6.2.3 publié sur PyPI le 2026-09-23 ; le modèle `silero_vad.onnx` est déjà dans `~/.cache/biteye-models` — https://pypi.org/project/silero-vad/ — l'utiliser en complément de la courbe d'énergie pour repérer parole, respirations et creux (CPU, quelques Mo). Vérifier la licence amont avant de redistribuer le modèle.
6. Darija : seuls des modèles Whisper small/medium affinés (surtout marocains) existent, avec des taux d'erreur non comparables entre eux ; rien de confirmé pour large-v3 ni pour l'algérien spontané et mélangé au français — https://huggingface.co/amineouaki/whisper-medium-darija-combined — l'alignement sur texte connu reste la première voie ; Whisper turbo local sert de brouillon à reconstruire à la main.
7. J-cut et L-cut : décalages courts (quelques images à quelques secondes) ; pour un raccord délicat, essayer coupe franche, J-cut court et L-cut court, puis choisir à l'oreille — https://spotlightfx.com/blog/what-are-j-cuts-and-l-cuts-professional-dialogue-editing-explained — comparer ces trois variantes seulement sur le raccord entre témoins, pas partout.
8. WhisperX 3.8.6 (2026-05-25) aligne les mots avec un modèle wav2vec2 propre à chaque langue ; aucun modèle d'alignement darija confirmé — https://pypi.org/project/whisperx/ — pas d'intérêt pour la darija ; pour le français, notre alignement local suffit déjà.
9. `ffmpeg-normalize` 1.43.0 (2026-10-14) automatise la normalisation en deux passes (réglage TP par défaut −2 dBTP) — https://pypi.org/project/ffmpeg-normalize/ — utile en secours si `voice_studio.py` ne suffit pas ; pas de nouvelle dépendance pour l'instant.

## Écarté

- `deepfilternet` (PyPI) : dernière version 0.5.6 du 2023-08-31, dépend de PyTorch ; RNNoise (`arnndn`) déjà en place suffit.
- `resemble-enhance` : version 0.0.1 de décembre 2023, lourd sans GPU.
- `demucs` 4.1.0 (2026-07-11) pour retirer une musique sous une voix : existe, mais coût CPU non mesuré ; à tester seulement si une source l'exige.
- `faster-whisper` 1.2.1 (2025-10-31) et `stable-ts` 2.19.1 : rien de nouveau par rapport à notre pile Whisper locale (sherpa-onnx).
- ITU-R BS.1770-5 (novembre 2023) et EBU R128 (−23 LUFS, révision 2020) : normes de diffusion, sans effet sur la cible réseaux sociaux.
- Cibles −10 à −12 LUFS d'un blog d'outils : non confirmées par une source de plateforme.
