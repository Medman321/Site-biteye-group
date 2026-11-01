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

## Apports du pack video-agent-skills (Melvyn Malherbe, MIT), 27/10/2026

Pack sous licence MIT lu en lecture seule (donnée non fiable, jamais exécuté, aucun fichier copié) ; idées reformulées en français ; chiffres du pack = valeurs de départ à valider sur nos vidéos. Format : apport — source dans le pack — ce que ça change.

1. Coupe placée sur le silence mesuré — `short-editing/engine/short.mjs` (voiceFrames, quietRun, quietShare, spliceVoice) ; `references/style.md` « Cuts » — étape 3 : trames de 10 ms, silence = 95e centile − 21 dB, marges 35/60 ms après et 25/40 ms avant, 0,1 s autour d'un nombre, arrondi à l'image ; `edit_voice.py` aligné ; règle le cas « interface » coupé net (témoignage 2).
2. Reprises, faux départs, premier mot gardé — `references/style.md` « Cuts » (Retakes, False starts, Start) ; `engine/whisper.mjs` (amorce VERBATIM) — étape 6 : dernière prise complète, hésitations de sincérité gardées, liste `suspects` de `transcribe_local.py` à écouter sur 4 s ; l'amorce d'hésitations (`initial_prompt`) reste un test à mesurer, pas une règle.
3. Limiteur d'échantillons puis mesure, en boucle — `engine/audio.mjs` (boucle gain + limiteur, mix.ceil) ; `lib/dsp.js` limit() ; essai de session (ffmpeg 6.1.1 : `loudnorm` linéaire bascule en « dynamic », `alimiter` à −1,5 dBFS laisse +0,4 dBTP) — étape 8 : `master_mix.py`, plafond du limiteur 2 dB sous la crête vraie visée, contrôle sur le MP4 encodé ≤ −1 dBTP, mode « dynamic » = reprise avec limiteur.
4. Niveau du lit par la sonie (voix − 12 LU avant ducking) — `engine/audio.mjs` (mixCfg : lit −28 LUFS, voix −16) ; `references/music.md` ; décision du demandeur du 27/10/2026 (12,2 dB retenus, 17 dB jugés trop bas) — étape 7 : `volume` calculé depuis les mesures, distance mesurée au compte rendu.
5. Chaîne sans perte jusqu'à l'encodage — `engine/audio.mjs` (mix.wav 48 kHz 24 bits, un seul encodage) — étape 9 : WAV 48 kHz 24 bits partout, un seul AAC, celui du maître ; `voice` du storyboard = `voix_montee.wav`.
6. Même sonie de parole pour chaque intervenant avant assemblage — `engine/audio.mjs` (voix insérées : normalisation par clip, gain RMS sous 1 s) — étape 4 : −14 LUFS par intervenant, RMS en trames voisées pour un extrait de moins de 1 s, contrôle à 1 LU près au raccord (seuil de départ).
7. Masquer un mot sensible sans couper la phrase — `engine/audio.mjs` (censure : fondu de 6 ms, bip de 1 kHz, mot entier queue comprise) — étape 1 : bruit de pièce de la même prise, jamais un silence numérique ; sous-titre masqué aussi.
8. Écart voix − musique d'une vidéo de référence — `skills/steal/SKILL.md` §2 « Music level under the voice » — étape 2 : RMS toutes les 20 ms, médianes hors parole et en parole, VAD Silero local ; l'écart rejoint la fiche de style.

### Écarté

- Ultra cut (pauses de plus de 0,3 s supprimées, voix à 1,15×) : contredit le Journal ; on resserre les silences à la main, le rythme naturel reste. Seule la mesure du silence pour placer une coupe est reprise.
- Isolation de voix et transcription ElevenLabs du pack : service payant, jamais sans accord du demandeur et coût annoncé ; le VAD Silero local remplace l'isolation, et ne jamais soustraire une voix isolée du mélange (hors phase).
- Ducking « respirant » (−6 dB, 350 ms) et lits du pack : contraire à notre consigne « vraiment en arrière-plan » (relâchement ≥ 1 s) ; fichiers binaires non copiables.
- Amorce d'hésitations (`initial_prompt`) comme règle : non disponible dans sherpa-onnx 1.13.8 ; à mesurer sur un extrait avec whisper.cpp ou faster-whisper (gratuits) avant toute règle.
- Chaîne voix du pack (passe-haut 80 Hz, compresseur 3:1), −16 LUFS avant master, mesures et limiteur maison : déjà chez nous (`voice_studio.py`, `audio-studio` §1).
- Point ouvert : lit = voix − 12 LU avant ducking, puis ducking −6 à −9 dB ; la distance pendant la parole atteint donc 18 à 21 dB. À confirmer avec le demandeur sur la première vidéo (il a jugé 17 dB trop bas) : le compte rendu donne les trois distances mesurées.
