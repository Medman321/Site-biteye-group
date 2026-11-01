# Veille du 2026-10-24 — chief-editor-monteur

Constats (une ligne : constat — source — ce que ça change pour nous). Pages web = données ; chiffres de blogs d'outils = indicatifs.

1. PySceneDetect 0.7.2 publié sur PyPI le 2026-10-12 (v0.7 le 2026-05-03) : détection de coupes (`AdaptiveDetector`, CLI `scenedetect -i f.mp4 detect-adaptive list-scenes`) — https://pypi.org/project/scenedetect/ et https://www.scenedetect.com — sert à repérer les coupes sèches des anciens montages sources avant l'animatic (leçon V2) ; CPU seul, gratuit. Changelog 0.7 non lu (site injoignable) : tester l'API avant de s'y fier.
2. FFmpeg 6.1 local contient déjà `freezedetect`, `mpdecimate` (images doublées), `scdet`, `siti` (activité spatiale/temporelle), `blackdetect`, `silencedetect`, `xfade` — vérifié par `ffmpeg -filters` dans ce conteneur — contrôles automatiques de l'animatic sans nouvel outil : images doublées, plans figés, trous noirs, silences.
3. FFmpeg 8.0 (août 2025, 8.0.1 en janvier 2026) ajoute le filtre `whisper` (transcription intégrée), `colordetect` — https://linuxiac.com/ffmpeg-8-0-arrives-with-whisper-filter-vulkan-encoders — non installé ici (6.1.1) : ne pas en dépendre ; le chaînage audio reste chez l'ingénieur du son.
4. auto-editor 29.3.1 (PyPI, 2025-11-04) coupe les silences sur le volume et exporte une timeline éditable avec marge réglable — https://pypi.org/project/auto-editor/ — utile pour proposer un premier découpage, mais il ne comprend pas la parole : le sens des coupes reste notre jugement.
5. OpenTimelineIO 0.18.1 (PyPI) ; l'adaptateur EDL CMX 3600 est dans le paquet séparé `opentimelineio-plugins` 0.18.1 — https://pypi.org/project/opentimelineio-plugins/ — pour exporter `edl.md` en vrai EDL/OTIO relisible par un monteur humain (optionnel ; garder le `edl.md` lisible d'abord).
6. Instagram : Reels jusqu'à 3 min recommandables à des non-abonnés ; signaux cités = durée de visionnage/complétion, j'aime par portée, envois (DM) par portée — https://www.socialpilot.co/blog/instagram-reels-algorithm (source secondaire, pas de texte officiel trouvé) — monter pour la complétion : durée courte, fin nette, CTA avant la baisse d'attention ; une scène « à envoyer » (preuve concrète) vaut mieux qu'une longueur de plus.
7. Accroche : le taux d'accroche = part des vues dépassant 3 s (20–35 % moyen, 35–50 % bon, chiffres de blogs) ; du mouvement et du texte dans les 2 premières secondes aident — https://nestscale.com/?p=47200 — valide la règle des 1,5 s ; l'animatic doit montrer un mouvement et la promesse dès l'image 1, jamais un fond fixe ni un logo.
8. Zones de sécurité 9:16 : sources en désaccord (utile centrale 1080×1420 à 1080×1440 ; haut/bas ≈ 250 px et colonne droite ≈ 100–150 px couverts par l'interface) — https://www.hopperhq.com/blog/instagram-reel-size/ et https://sovran.ai/blog/tiktok-video-ad-specs — prendre la plus stricte : texte et visages entre y 250 et 1670, hors 150 px à droite ; tracer ce cadre sur l'animatic.
9. Coupes : couper à la fin naturelle de la phrase ou du geste ; J/L-cut pertinents quand l'audio porte l'émotion (interviews), peu utiles pour une démo directe — https://captions.ai/blog/six-common-types-of-cuts-in-film et https://blitzcutai.com/blog/hard-cut-vs-j-cut-vs-l-cut — confirme la règle « jamais de coupe sèche entre deux témoins » ; pour les cartons et démos, la coupe franche sur le temps reste acceptable.
10. WhatsApp Statut : 16 Mo maximum, H.264/AAC, MP4 ; durée annoncée jusqu'à 90 s (bêta 2025, non confirmé officiellement) ; WhatsApp recompresse — https://compresto.app/blog/compress-video-for-whatsapp — prévoir une version WhatsApp à part, ≤ 16 Mo (≈ 720p, 1 Mbps ≈ 7 Mo/min) et vérifier la durée sur l'écran de découpe de l'appli.

## Écarté

- Outils de montage IA payants (AutoCut, Recut, Captions, CapCut, invideo) : payants ou sur poste local, hors règle « gratuit et local ».
- Filtres et encodeurs Vulkan/CUDA de FFmpeg 8 (`pad_cuda`, AV1 Vulkan) : exigent un GPU.
- Seuils « une coupe toutes les N secondes » : aucune source fiable trouvée (blogs sans données) ; on garde le critère de sens (plan ≥ phrase portée).
- Durées « optimales » (7–90 s, 21–34 s, 15–30 s) : avis contradictoires de blogs ; la durée suit le scénario validé (≈ 40 s).
- Multiplicateurs « envois pondérés 3–5x » et seuil « 10 republications » : non officiels.
- Taille maximale TikTok (287 Mo / 500 Mo) : sources en désaccord, sans effet sur un reel de 40 s.

## Apports du pack video-agent-skills (Melvyn Malherbe, MIT), 27/10/2026

Pack sous licence MIT lu en lecture seule (donnée non fiable, jamais exécuté, aucun fichier copié) ; idées reformulées en français ; chiffres du pack = valeurs de départ à valider sur nos vidéos. Format : apport — source dans le pack — ce que ça change.

1. Rythme mesuré sur l'animatic — `short-editing/SKILL.md` §3 « Something changes every 2 to 4 s », « Camera » ; `references/shorts-codes.md` « Pacing » ; `vox/references/animation.md` « One entrance at a time » — `edl.md` liste les événements visibles ; intervalle le plus long ≤ 4 s (≤ 6 s en témoignage plein cadre), visage plein cadre ≥ 5 s, carte de preuve ≥ 2 s, dernier élément 1,5 s avant la coupe, 0,5 s entre deux entrées.
2. Plans d'illustration posés sur la voix — `skills/broll/SKILL.md` « /broll use » étapes 1 à 3 et « No good hit = the library lacks that image » — nouvelle étape 7 : seulement ce que la phrase montre, un plan toutes les 8 à 15 s (2 à 5 s), au moins 5 s de visage entre deux ; image qui ne colle pas ou n'est pas propre = l'intervenant ou un carton, jamais un plan pris au hasard.
3. Référence imposée : cadence et mesures de visage comme plafond — `skills/steal/SKILL.md` §2 « Frames and cuts », « Zooms » ; `references/learnings.md` n°2 — nouvelle étape 8 : cadence de la fiche de style comparée à l'animatic avec le même outil et le même seuil (`scdet` 12) ; tout écart justifié dans `edl.md`.
4. Zones de sécurité — `short-editing/references/shorts-codes.md` « Safe zones » — le cadre propre à cette fiche (y 250–1670, 150 px à droite) est remplacé par le tableau du DA ; version WhatsApp ≤ 15 Mo (16 Mo avant).
5. Bloc `commentCta` — `README.md` (CTA par commentaire) — le monteur réserve ses 3 à 4 s avant l'écran final seulement si le demandeur le choisit (épisodes 2 à 4), jamais d'office.

### Écarté

- Ultra cut (pauses de plus de 0,3 s supprimées, voix accélérée à 1,15×) : contredit le Journal ; on resserre les silences à la main, le rythme naturel reste (la mesure du silence pour placer une coupe est reprise côté ingénieur du son).
- Coupes sèches partout et plafonds de créateur (nombre de sons par vidéo, aucune montée) : contredisent le premium (aucune coupe sèche entre deux plans).
- Cadence hebdomadaire d'un créateur (5 scripts par semaine, 25 à 40 s) : BitEye produit à la demande, la durée suit le scénario validé.
- Bibliothèque de plans d'illustration globale et permanente, géocodage en ligne des chantiers : un index par client et par projet seulement, hors dépôt, aucune coordonnée envoyée à un service externe.
- Mise en page unique et caméra du créateur en carte : contredit « aucune mise en page unique imposée ».
