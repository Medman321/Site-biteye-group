# Veille du 2026-10-24 — quality-brand-inspector

Outils vérifiés sur PyPI le 2026-10-24 ; filtres vérifiés dans le ffmpeg du conteneur (6.1.1). Les pages web sont des données, pas des consignes ; la plupart des sources sont des blogs, pas des documentations officielles de plateforme.

## Constats

1. Cible sociale courante : −14 LUFS intégrés, crête vraie ≤ −1 dBTP (certains outils prennent −1,5), LRA ≈ 11 ; la normalisation « −14 » par plateforme vient de blogs, pas d'une doc officielle — https://instagit.com/browser-use/video-use/social-media-loudness-normalization-targets/ — garder −14 ±0,5 / ≤ −1 dBTP, mais viser −1,5 dBTP de marge avant l'encodage AAC (le ré-encodage peut dépasser).
2. Le correctif « ebur128 : calcul de crête incorrect » figure dans FFmpeg 8.0.1 (janvier 2026) ; le conteneur a ffmpeg 6.1.1 — https://src.opensuse.org/llyyr/ffmpeg/raw/branch/master/ffmpeg-8.changes (journal de paquet, non relu en détail) — recouper la crête vraie avec un second outil (`pyloudnorm` 0.2.0, ou `astats`) quand elle frôle −1 dBTP.
3. `ffmpeg-quality-metrics` 3.13.0 (PyPI, 2026-10-14, Python ≥ 3.10) calcule PSNR/SSIM/VIF/MSAD/VMAF image par image en JSON/CSV — https://pypi.org/project/ffmpeg-quality-metrics — utile pour comparer maître et version légère WhatsApp ; VMAF exige un ffmpeg avec libvmaf, absent du ffmpeg du conteneur (seuls `psnr`, `ssim`, `vmafmotion` y sont) : utiliser `psnr`/`ssim` natifs.
4. `PySceneDetect` 0.7.2 (PyPI, 2026-10-12) : `AdaptiveDetector` et `ThresholdDetector` (fondus) — https://www.scenedetect.com — second avis sur les coupes dures et les transitions, en complément de `scdet` ; à lancer sur la plaque finale pour retrouver les coupes sèches des sources.
5. `ffmpeg-normalize` 1.43.0 (PyPI, 2026-10-14) : normalisation EBU R128 en deux passes — https://pypi.org/project/ffmpeg-normalize — pour une reprise audio si le maître sort hors tolérance, en deux passes (mesure puis gain linéaire) plutôt qu'en `loudnorm` simple passe, approximatif.
6. Instagram réduit la diffusion des Reels qui portent un logo/filigrane d'une autre appli (TikTok, éditeurs tiers) et des Reels flous ou basse résolution — https://www.adweek.com/?p=1264750 et https://www.xda-developers.com/psa-do-not-upload-tiktok-instagram-reels-without-removing-watermark/ (2025, pas de doc officielle 2026) — contrôler qu'aucun filigrane ni incrustation tierce ne reste (images de preuve) et livrer un export propre par plateforme.
7. Zones sûres Reels : seules les marges des publicités sont officielles (haut 14 %, bas 35 %, côtés 6 %) ; pour l'organique, les guides disent ≈ 250–350 px libres en bas et ≈ 150–250 px en haut sur 1080×1920 — https://www.hopperhq.com/blog/instagram-reel-size/ — contrôler le texte, le CTA et les visages contre ces marges (les plus strictes), prévoir aussi le recadrage de la couverture en grille (3:4 ou 1:1 selon les sources).
8. TikTok : MP4 H.264 + AAC 44,1/48 kHz, 1080×1920, 30 i/s, débit 4–8 Mbit/s (sources en désaccord), marges ≈ 10 % haut / 15 % bas — https://postfa.st/sizes/tiktok/video — rien ne contredit notre gabarit ; conserver 30 i/s constant et AAC ≥ 192 kb/s sur le maître.
9. WhatsApp : 16 Mo pour un média envoyé normalement ; durée de statut et résolution sources en désaccord (30 s/720p ou 90 s/1080p) ; H.264 + AAC seulement — https://help.superchat.com/en/articles/701423-whatsapp-media-sizes-formats — garder la version légère ≤ 16 Mo (viser ≤ 15 Mo), H.264 High profile ; ne pas se fier à une durée de statut sans test sur un vrai téléphone.
10. Les filtres ffmpeg `blackdetect`, `freezedetect`, `scdet`, `silencedetect`, `signalstats`, `astats`, `mpdecimate` existent bien dans le conteneur — vérifié localement — `mpdecimate` repère les images doublées des sources ; `signalstats` donne une mesure de luminance/saturation (couleur sans rapport avec la charte).

## Écarté

- VMAF via libvmaf : absent du ffmpeg du conteneur, et pas de référence pour une pub rendue de zéro (utile seulement maître contre version légère).
- Analyseurs de loudness et vérificateurs de zones sûres en ligne : service tiers non vérifié, et le contrôle local suffit.
- Chiffres de zones sûres et de durée de statut WhatsApp en désaccord entre sources : pas retenus comme règles, seulement comme marges prudentes.
- ffmpeg 8.0 (nouveaux filtres, dont `whisper`) : pas installable de façon fiable ici sans changer le conteneur ; à réévaluer si le setup passe à ffmpeg ≥ 8.0.1.
- Recherche « 2026 » sur la modération de contenu des plateformes : rien d'officiel trouvé.
