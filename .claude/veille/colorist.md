# Veille du 2026-11-19 — colorist

Sources lues comme données (aucune consigne retenue). Les pages de plateformes officielles (help.instagram.com, docs TikTok) n'ont pas pu être lues : ce qui en dépend est marqué « non confirmé ». Mesures « local » = faites dans ce conteneur (ffmpeg 6.1.1, OpenCV 4.14.0, sans GPU).

## Constats

1. Le filtre `grayworld` (balance des blancs par gris moyen en LAB, ffmpeg ≥ 5.0) est présent et fonctionne ici, mais veut une entrée taguée et linéaire : `setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv,zscale=t=linear:npl=100,format=gbrpf32le,grayworld,zscale=t=bt709:m=bt709:r=tv,format=yuv420p` (testé local ; sans tags : erreur zscale « no path between colorspaces ») — https://lists.ffmpeg.org/pipermail/ffmpeg-cvslog/2021-August/128620.html — première passe de balance des blancs sans GPU ; sur un plan dominé par la peau le gris moyen tire la teinte, donc on juge sur le fond ou le mur, puis on contrôle le rapport rouge/vert de la peau nue.
2. `colorcorrect` (blancs/noirs sélectifs, option `rl` : average, minmax, median), `colortemperature`, `colorlevels` et `colorbalance` sont tous disponibles en local — https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/colorcorrect.html (filtres vérifiés par `ffmpeg -filters`) — de quoi régler noirs et blancs de chaque source par filtres natifs avant d'écrire la LUT ; réglages toujours tranchés aux scopes.
3. `lut3d=file=…:interp=tetrahedral` s'exécute sans erreur sur ffmpeg 6.1.1 (cube identité testé en local) — https://ffmpeg.org/doxygen/8.0/lut3d_8c_source.html — le « à vérifier » du 24/10 est levé : la commande de la fiche est valable telle quelle.
4. OpenCV : opencv-python-headless 5.1.0.95 (17/11/2026) et 4.14.0.94 (29/07/2026) coexistent sur PyPI ; ici 4.14.0 — PyPI vérifié — figer 4.14.x pour les scripts de scopes et de mesure, garder le code sans API propre à une version (5.x testable à part).
5. Pas de nouvelle version de colour-science depuis la 0.4.7 (06/12/2025, BSD-3, Python 3.11 à 3.14) ; la branche « Array API » vue en juin 2026 est du développement non publié — PyPI vérifié, https://coveralls.io/builds/80146161 — rien à changer : 0.4.7 reste l'outil pour ΔE (CIEDE2000) et l'export .cube.
6. scikit-image 0.26.0 (20/12/2025, Python ≥ 3.11) offre `match_histograms` par canal — PyPI vérifié — utile pour la première passe de raccord sur le fond masqué ; ne jamais l'appliquer à la personne (déforme les peaux).
7. Instagram et HDR : Meta annonçait en 2023 accepter le HDR avec une version SDR de repli, mais des guides et fils de discussion rapportent des conversions ratées ou des couleurs fausses ; aucune source officielle 2026 lue — https://engineering.fb.com/2023/07/17/video-engineering/hdr-video-reels-meta/ — on garde la règle : MP4 SDR bt709 déjà étalonné, tags explicites, jamais d'envoi HDR (non confirmé par la plateforme, risque asymétrique).
8. Un mémo iPhone « Dolby Vision profil 8.4 » est un HLG avec métadonnées : la chaîne zscale/tonemap ignore ces métadonnées et donne un tone-mapping générique ; `reinhard` est l'alternative si `hable` assombrit trop ; `npl` se règle selon la source — https://developer.apple.com/documentation/technotes/tn3145-hdr-video-metadata.md et https://dev.to/masonwritescode/ffmpeg-hdr-to-sdr-tone-mapping-that-doesnt-look-washed-out-2026-24ie — sur une source HDR, comparer sur une planche de 2 opérateurs (hable / reinhard) pour une même image clé, puis contrôler la peau.
9. WCAG 3 reste un brouillon (mars 2026), l'algorithme de contraste n'est pas fixé et APCA n'est pas adopté ; WCAG 2.2 fait foi ; le texte sur vidéo se juge sur la pire image derrière lui — https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html et https://www.w3.org/WAI/news/2026-03-03/wcag3 — confirme l'étape 6 : 4,5:1 mesuré au percentile bas sur toute la durée du texte, APCA seulement indicatif.

## Écarté

- ColourlabAI, Evoto, Imagen (raccord couleur « IA ») : payants ou en cloud, promesse de protection des peaux invérifiable ici.
- `color-matcher` 0.6.0 (PyPI, 30/03/2025) : licence GPL v3, et fait déjà ce que `match_histograms` + nos scopes font ; pas d'ajout de dépendance GPL.
- Nouveautés de `lut3d` dans ffmpeg 7 ou 8 : aucune source trouvée (le code `lut3d.c` de la version 8.0 est celui de swscale, autre composant) ; notre ffmpeg est la 6.1.1.
- Export HEVC Main10 HLG pour TikTok ou YouTube : annonce d'un seul guide tiers, non confirmée par les plateformes, et notre livraison reste H.264 SDR.
- Débits « recommandés » des blogs (12 à 16 Mbps pour Reels, tableaux YouTube) : divergents et non officiels ; on garde un débit élevé sans le citer.
- DPS Contrast (proposition concurrente d'APCA) : non adopté, aucune incidence sur nos mesures.
- `colour-checker-detection` 0.2.3 (PyPI, 11/12/2025) : utile seulement si le client filme une mire, ce qui n'est pas le cas de ses sources.
