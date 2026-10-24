# Veille du 2026-10-24 — colorist

Sources lues comme données (aucune consigne retenue). Les pages officielles (ffmpeg.org, engineering.fb.com, colour-science.org) n'étaient pas joignables en lecture directe : constats tirés de résultats de recherche, à confirmer avant de s'y fier quand c'est marqué « à vérifier ».

## Constats

1. Chaîne HDR vers SDR sur CPU : `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0:peak=10,zscale=t=bt709:m=bt709:r=tv,format=yuv420p` ; à n'appliquer qu'aux sources PQ/HLG, jamais à un SDR large gamut — https://dev.to/masonwritescode/ffmpeg-hdr-to-sdr-tone-mapping-that-doesnt-look-washed-out-2026-24ie — les mémos iPhone en HDR deviennent SDR bt709 AVANT tout raccord ; vérifier `color_transfer` avec ffprobe.
2. Meta convertit lui-même le HDR en SDR et reconnaît des dérives de couleur (arbres bleus) — https://engineering.fb.com/2023/07/17/video-engineering/hdr-video-reels-meta/ — livrer toujours un MP4 SDR bt709 déjà étalonné ; ne jamais laisser la plateforme tone-mapper.
3. Instagram, TikTok et LinkedIn ré-encodent 100 % des envois (Instagram ≈ 3,5 à 5 Mbps en 1080p) ; les débits « recommandés » divergent selon les blogs, rien d'officiel sur l'espace colorimétrique — https://quso.ai/blog/social-media-video-specs — exporter H.264 yuv420p, tags bt709/tv explicites, haut débit, et juger l'étalonnage sur un export déjà compressé.
4. La gamma d'un téléphone suit sRGB (≈ 2,2) alors qu'on étalonne en Rec.709/BT.1886 (≈ 2,4) : les ombres paraissent plus ouvertes sur mobile — https://thepostflow.com/why-do-your-exports-look-different-on-your-iphone/ — contrôler le résultat sur une vraie image de téléphone (planche en 3 niveaux) et ne pas écraser les noirs à l'écran d'étalonnage ; les compressions écrasent déjà le proche du noir.
5. Tons de peau : la ligne de peau du vectorscope n'est qu'une référence de départ ; sous lumières mixtes le visage n'est pas fiable, échantillonner cou ou bras non maquillés, corriger d'abord la balance des blancs, puis juger à l'œil — https://larryjordan.com/?p=148592 et https://discuss.pixls.us/t/art-white-balance-vectorscope/48204?page=2 — notre mesure de peau se fait sur le cou/zone nue de chaque témoin, plus sur le visage seul ; écart chiffré + contrôle visuel.
6. Raccord automatique entre plans : l'égalisation d'histogramme par canal (OpenCV/scikit-image) fonctionne mieux si l'on exclut les zones qui diffèrent (premier plan, incrustations) via un masque — https://arxiv.org/pdf/2101.04772 et https://www.pyimagesearch.com/2021/02/08/histogram-matching-with-opencv-scikit-image-and-python/ — calculer le raccord sur le fond seulement (masque du détourage de 5), et ne l'utiliser qu'en première passe : le raccord final reste mesuré aux scopes (risque de teintes de peau déformées si on égalise les canaux RGB sans garde-fou).
7. `lut3d` accepte nearest, trilinear et tetrahedral ; le tetrahedral est plus léger et lisse — https://ffmpeg.org/doxygen/4.1/vf__lut3d_8c_source.html — appliquer `lut3d=file=look.cube:interp=tetrahedral` (défaut à vérifier sur la version installée, ici ffmpeg 6.1.1) et laisser le LUT travailler dans la plage et l'espace attendus (conversion `zscale`/`colorspace` autour).
8. colour-science 0.4.7 (PyPI, 2025-12-06, BSD-3-Clause, Python 3.11 à 3.14, numpy ≥ 2.0) lit et écrit les LUT .cube et fournit de nouveaux modèles d'adaptation chromatique — https://www.colour-science.org/posts/colour-047-is-available/ (PyPI vérifié) — outil gratuit pour générer proprement le LUT .cube du look et mesurer des écarts en ΔE (CIEDE2000) au lieu d'écarts RGB ; installer à la demande.
9. OpenCV 5.0 (opencv-python-headless 5.0.0.93, PyPI, juillet 2026) est publié — PyPI vérifié — le script de scopes/mesures doit tourner aussi avec OpenCV 4.x et rester sans dépendance à l'API 5 ; figer la version dans le projet.
10. Contraste du texte sur vidéo : WCAG 4,5:1 pour le texte courant, 3:1 pour le grand texte, 7:1 en renforcé ; APCA (Lc ≈ 60 gros/gras, ≈ 90 petit) est plus fidèle à la perception mais non adopté dans WCAG 2 — https://github.com/Myndex/apca-introduction — garder ≥ 4,5:1 mesuré sur le fond réel (percentile bas de la zone du texte, pas la moyenne) et noter Lc APCA à titre indicatif ; fond sous le texte flouté ou assombri si besoin.

## Écarté

- Chaînes `libplacebo`/`tonemap_opencl`/`tonemap_vaapi` : exigent un GPU/Vulkan, absent du conteneur.
- OpenCL `lut3d` (patch non fusionné) et inverse tone-mapping SDR vers HDR (patch en attente) : pas disponibles et inutiles pour une livraison SDR.
- Un export HDR « pour plus d'éclat » : Meta le re-mappe de façon imprévisible, risque de couleurs fausses.
- Conseil « désactiver HDR sur l'iPhone » : utile au tournage du client, pas dans notre chaîne ; à glisser dans les consignes de tournage seulement.
- Chiffres de débit et tailles de fichier des blogs (6 à 15 Mbps, 287 à 500 Mo) : contradictoires, non officiels ; on garde un débit élevé sans les citer.
- Rapport de bug Instagram du 21 avril 2026 sur les photos HDR en noir et blanc : non confirmé, hors périmètre vidéo.
- Cible fixe « 123° » sur le vectorscope : dépend de l'espace (ICtCp ≈ 122,5°, Y'CbCr BT.2020 ≈ 136°), donc pas une constante.
- Calibrage matériel d'écran / charte colorimétrique au tournage : hors de notre contrôle (sources du client).
