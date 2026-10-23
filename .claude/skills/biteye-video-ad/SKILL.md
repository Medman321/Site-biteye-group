---
name: biteye-video-ad
description: Produire une vidéo marketing motion design BitEye / VISION Workspace, livrée en MP4 et en page HTML synchronisée, à partir d'un mémo vocal, de photos, de séquences vidéo ou de données. Méthode complète : questions de cadrage, analyse des médias, studio audio gratuit, veille web, proposition à valider, production, contrôle. À utiliser pour toute demande de vidéo, pub, reel, story, spot, clip promo ou motion design.
---

# Vidéo marketing BitEye : la méthode

| Étape | Skill | Qui (voir `.claude/CLAUDE.md`) |
|---|---|---|
| 0. Cadrer | ce fichier, §0 | session principale (questions au demandeur) |
| 1. Analyser et préparer les médias | `media-analysis`, `audio-studio`, `media-lab` | agents `biteye-audio-engineer` et `biteye-media-editor`, en parallèle |
| 2. Veille + proposition | `marketing-research`, `creative-direction`, `biteye-brand` | agent `biteye-marketing-strategist` |
| — validation par le demandeur — | | session principale |
| 3. Produire | `motion-engine`, `creative-direction` | agent `biteye-video-producer` |
| 4. Livrer | ce fichier, §4 | session principale |

Lis chaque SKILL.md au moment de l'étape (`.claude/skills/<nom>/SKILL.md`).

`$OUT` = le dossier de travail de la vidéo, donné par la session principale (scratchpad de la session, sinon `./.video-out/<slug>`). Tous les chemins `$OUT/...` des skills sont relatifs à lui. Outils gratuits : `bash .claude/skills/biteye-video-ad/scripts/setup_free_tools.sh` une fois par session.

## 0. Questions de cadrage (avant tout travail)

Pose-les en une fois (AskUserQuestion, 4 questions maximum par appel ; deux appels si nécessaire). Saute celles dont la réponse est déjà dans la demande.

1. **Diffusion** (choix multiple) : Reels Instagram / TikTok / YouTube Shorts · Story ou statut WhatsApp · fil Facebook / Instagram · LinkedIn · YouTube (vidéo ou pré-roll) · site officiel (en-tête, page produit) · salon / écran.
   → déduit les formats (`creative-direction` §5). Plusieurs diffusions = plusieurs sorties.
2. **Objectif** : faire connaître VISION · obtenir des demandes de démo · lancer un module (Estate, Build, Co-Owner) · témoignage client · événement (salon, offre) · recrutement.
3. **Cible et langue** : promoteurs · entreprises de réalisation · syndics · acquéreurs ; darija · français · arabe · mélange.
4. **Style** : terrain et humain (chantier, équipe, WhatsApp) · pédagogique (écrans du logiciel) · témoignage · humour léger. Identité : officielle (œil turquoise) ou site V2 (vert et citron), tant que BitEye n'a pas tranché (`biteye-brand`).
5. **Infos à afficher** : chiffres réels autorisés, nom du projet ou du client, offre, CTA (démo, WhatsApp, site, téléphone), durée maximale, musique fournie.

Note les réponses dans `$OUT/brief.json`. Sans réponse à une question : défaut raisonnable, signalé dans le compte rendu.

## 1. Analyser et préparer

Dossier de travail : `OUT=<scratchpad>/video-<slug>` (sinon `./.video-out/<slug>`, ignoré par git). Médias reçus copiés dans `$OUT/src`. Jamais de média dans le dépôt Git (le site est public).

- **Voix** (`audio-studio`) : `voice_studio.py` → `voix_studio.mp3` + rapport avant / après ; puis mots minutés avec `transcribe_local.py` (texte fourni ou Whisper local). ElevenLabs uniquement en option, avec accord.
- **Vidéos et photos** (`media-analysis` puis `media-lab`) : inventaire, planches regardées avec Read, plans choisis, coupés, stabilisés, recadrés, étalonnés ; photos recadrées, corrigées, éventuellement détourées.
- Résultat : `$OUT/media.md`, avec une ligne par média prêt (chemin, contenu, durée, usage proposé).

## 2. Veille et proposition

`marketing-research` : recherche web sur ce qui marche dans le secteur et sur la plateforme visée, mise à jour de l'empreinte BitEye, puis `$OUT/proposition.md` avec 2 ou 3 concepts conformes à `creative-direction` (hook, touches humaines, rien de générique). **Arrêt : le demandeur choisit un concept** (ou demande des changements) avant la production.

## 3. Produire

1. Storyboard `$OUT/storyboard.json` à partir du concept validé et des médias préparés :
   - une scène par idée, bornée par les pauses de la voix ; chaque élément entre sur le mot qui le nomme (`at` = `start` du mot) ;
   - hook à l'image 0 ; au moins 3 touches humaines ; `safe: true` pour les formats verticaux sociaux ; `theme` selon la réponse au cadrage ;
   - écran final adapté à la plateforme.
   Modèles : `.claude/skills/motion-engine/examples/` (pub darija 9:16, sa version 16:9, hook + touches humaines).
2. Build, puis planche :
   ```
   ENG=.claude/skills/motion-engine/scripts
   python3 -I $ENG/build.py "$OUT/storyboard.json" --out "$OUT/out"
   node $ENG/render.js "$OUT/out/<slug>.local.html" --stills "$OUT/out/stills"
   ```
3. Regarde `sheet.jpg` (Read) et le champ `fit`, puis applique la grille de contrôle de `creative-direction` §6. Une passe de corrections.
4. MP4 : `node $ENG/render.js "$OUT/out/<slug>.local.html" --mp4 "$OUT/out/<slug>.mp4"`, puis `ffprobe` (durée, piste audio) et une image extraite au milieu.
5. Un MP4 par format demandé : copie le storyboard, change `format` / `safe`, revois la mise en page (`split` en 16:9), contrôle la planche.

## 4. Livrer

Rendu long ou multi-formats : pousse le projet (storyboards seulement, pas les médias) et lance « Vidéo · rendu » sur GitHub avec `archive_url` pour les médias ; les fichiers finaux arrivent en artefact ou en Release. Voir `.claude/CLAUDE.md` § GitHub.

- `<slug>.mp4` (un par format) ; `<slug>.local.html` (page autonome, voix synchronisée) ; `<slug>.html` à publier comme Artifact (avec `media/*` via `files` si `sidecar_media`).
- Compte rendu : tableau temps → voix → animation ; grille de contrôle remplie ; défauts retenus ; données d'exemple signalées ; outils utilisés (gratuits ou payants, avec le coût) ; sources de la veille.
