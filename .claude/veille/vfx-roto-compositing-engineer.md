# Veille du 2026-10-24 — vfx-roto-compositing-engineer

Méthode : 9 recherches web (12 derniers mois), versions vérifiées sur PyPI le 2026-10-24, scripts du dépôt relus (`media-lab/scripts/cutout_video.py`). Le conteneur n'ouvre pas les pages web (WebFetch non utilisé) : les constats viennent des résumés de recherche, fiabilité moyenne, à confirmer par une mesure locale avant de changer une règle.

## Constats

1. `rembg` 2.0.86 (PyPI, 2026-10-21) propose en plus de `u2net_human_seg` les modèles `birefnet-portrait` (portraits), `birefnet-general`, `isnet-general-use`, `bria-rmbg` — https://pypi.org/project/rembg/ et https://gigazine.net/gsc_news/en/20260510-rembg/ — tester `birefnet-portrait` sur UNE image clé (cheveux, mains) contre `u2net_human_seg` avant de détourer un lot ; un test rapporte quand même des mèches manquées, et BiRefNet est plus lent sur CPU : mesurer s/image.
2. `bria-rmbg` (RMBG 2.0) est sous licence non commerciale, et Bria V-RMBG 3.0 (vidéo, juin 2026) est un service commercial — https://blog.bria.ai/brias-new-state-of-the-art-remove-background-2.0-outperforms-the-competition et https://www.theatdb.com/news/bria-launches-v-rmbg-30-state-of-the-art-video-background-removal-model — inutilisable pour des vidéos clients de BitEye : ne jamais le choisir.
3. Robust Video Matting (RVM) est un matting vidéo temporel, exporté en ONNX (licence GPL-3.0) — https://sourceforge.net/projects/robust-video-matting.mirror/ — notre `cutout_video.py` le gère déjà (`rvm`, onnx mobilenetv3 dans `~/.u2net`) : c'est la voie contre le scintillement du masque ; garder `u2net_human_seg` comme repli et choisir sur une planche de bords, pas à l'intuition.
4. MatAnyone 2 (CVPR 2026) donne le meilleur matting vidéo cohérent mais n'est documenté que sur GPU CUDA, sous licence S-Lab non commerciale — https://arxiv.org/pdf/2501.14677 et https://huggingface.co/kamaz01/MatAnyone2 — non applicable (pas de GPU, licence).
5. MediaPipe 1.1.1 (PyPI, 2026-10-14) : l'API « tasks » Image Segmenter (modèles personne/fond, cheveux) fonctionne sur CPU, par image ou en flux vidéo — https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter — masque rapide et léger, utile comme masque de contrôle (alignement tête/mot, crâne non coupé) ; moins fin que rembg sur les bords : pas pour le matte final.
6. `transparent-background` (InSPyReNet, dernière version 1.3.4 de mai 2025) : la sortie RGBA n'existe pas en mode vidéo, seulement la carte de masque (`map`) — https://pypi.org/project/transparent-background/ — rien de neuf ; écarté.
7. SAM 2 / SAM 3 : exports ONNX et ports CPU (sam3.cpp, Ultralytics 8.3.237) existent mais le suivi vidéo mémorise le clip entier et vise le GPU — https://newreleases.io/project/pypi/ultralytics/release/8.3.237 et https://www.sourcepulse.org/projects/27861331 — trop lourd pour un lot de 30 s sans GPU ; à ne considérer que pour isoler UN objet (pas une personne) sur peu d'images.
8. WebM VP9 avec canal alpha : Chrome lit `yuva420p` en WebM depuis Chrome 31, avec encodage ffmpeg direct depuis une séquence PNG RGBA — https://developer.chrome.com/blog/alpha-transparency-in-chrome-video/ — notre chaîne (PNG RGBA -> `libvpx-vp9 -pix_fmt yuva420p`) est conforme ; ajouter `-auto-alt-ref 0` (nécessaire à l'alpha avec libvpx) et contrôler le canal par un `ffprobe` (tag `alpha_mode=1`) après export. ffmpeg local = 6.1.1 ; rien à changer.
9. L'effet « texte derrière le sujet » est désormais standard (modèles CapCut, outils web comme textbehindvideo.io, matting BEN2 en WebGPU) — https://pippit.capcut.com/templates/text-behind-the-person-effect et https://tools.rotato.app/text-behind-video — effet banal : le différenciateur est la qualité du bord, la fiabilité du recalage et une parallaxe lente, pas l'effet en soi (aucune source datée 2026 sur la tendance Reels/TikTok).
10. `opencv-python-headless` 5.0.0.93 (PyPI, 2026-07-02) et `onnxruntime` 1.31.0 (2026-10-09) sont sortis — https://pypi.org/project/opencv-python-headless/ et https://pypi.org/project/onnxruntime/ — ne pas migrer en cours de projet (OpenCV 5 est une version majeure) ; épingler les versions du conteneur et ne tester qu'à part.

## Écarté

- MatAnyone 2 : GPU CUDA seulement, licence non commerciale.
- Bria RMBG 2.0 / V-RMBG 3.0 : licence non commerciale ou service payant.
- `transparent-background` : pas de RGBA en vidéo, dernière version mai 2025.
- SAM 3 vidéo : mémoire et calcul GPU, trop lourd pour un détourage de personne sur CPU.
- Outils web « texte derrière la vidéo » (WebGPU, comptes) : pas reproductibles dans le conteneur, médias clients hors dépôt.
- Aucune source trouvée sur une règle de plateforme (Instagram, TikTok, LinkedIn) propre à la transparence ou au 2.5D ; rien à changer côté formats.
