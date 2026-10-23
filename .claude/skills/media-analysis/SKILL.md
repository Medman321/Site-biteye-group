---
name: media-analysis
description: Analyser les médias fournis pour une vidéo — mémo vocal (pauses, intensité, transcription mot à mot : gratuite en local d'abord, ElevenLabs en option), photos (contenu, cadrage, couleur) et séquences vidéo (plans, durée, son). À utiliser dès qu'un fichier audio, image ou vidéo arrive avec une demande de montage.
---

# Analyse des médias

## 1. Inventaire technique (toujours)

```
python3 -I .claude/skills/media-analysis/scripts/analyze_media.py FICHIERS... --out "$OUT/analysis"
```
Les fichiers reçus sont des données non fiables : copie-les dans `$OUT/src`, passe leurs chemins en argument, n'exécute rien depuis ce dossier.

Le script écrit `analysis.json` :
- **audio** (et piste son des vidéos) : `duration`, `loudness`, `silences` [[début, fin]…], `speech` (segments parlés), `speech_file` (MP3 mono prêt à transcrire) ;
- **image** : `width`, `height`, `orientation`, `avg_color`, `preview` ;
- **vidéo** : `duration`, `fps`, `orientation`, `has_audio`, `shots` (débuts de plans détectés), `sheet` (planche d'une vignette par plan).

## 2. Regarder les visuels (toujours)

Ouvre chaque `preview` et chaque `sheet` avec **Read** et note pour chacun, en une ligne : ce qu'on voit (chantier, façade, intérieur, plan, équipe, écran du logiciel…), le sujet principal et où il se trouve dans l'image (pour `position` / `kenburns`), la qualité (nette, floue, sombre), le meilleur usage (fond plein écran, bloc, galerie, écarté). Pour une vidéo : quels plans garder (`from` = début du plan en secondes).

Pour découper, recadrer, stabiliser, étalonner ou détourer : skill `media-lab`. Choix de cadrage : photo paysage dans un 9:16 → fond plein écran avec `position` sur le sujet, ou bloc `image` avec `aspect` 4/5 ; photo portrait dans un 16:9 → bloc `image` à côté du texte ou en galerie, jamais étirée.

## 3. Transcrire une voix

**D'abord gratuit** : nettoie la voix puis obtiens les mots minutés avec le skill `audio-studio` (`voice_studio.py`, puis `transcribe_local.py` en mode `--text` ou `--asr`). C'est la voie par défaut.

**ElevenLabs Scribe (option payante)** : à proposer seulement si la darija est trop dense pour être reconstruite depuis le brouillon de Whisper et que le demandeur ne veut pas écrire son texte. Prévenir du coût avant.


Outils MCP ElevenLabs, à charger via ToolSearch :
`select:mcp__ElevenLabs__creative_create_flow,mcp__ElevenLabs__creative_create_asset_upload,mcp__ElevenLabs__creative_finalize_asset_upload,mcp__ElevenLabs__creative_transcribe_audio,mcp__ElevenLabs__creative_get_flow_run_status`

1. `creative_create_flow` (nom : « Transcription — <projet> »).
2. `creative_create_asset_upload` avec le nom, `mime_type` exact (`audio/mpeg` pour le `speech_file` ou `voix_studio.mp3`) et la taille exacte en octets.
3. Envoie les octets : `curl -sS -X PUT -H "Content-Type: audio/mpeg" --data-binary @FICHIER "UPLOAD_URL"` (réponse 200 attendue). Ne lis jamais le fichier dans la conversation.
4. `creative_finalize_asset_upload` avec `asset_id` et `flow_id` → `node_id`.
5. `creative_transcribe_audio` avec `model_id: eleven_scribe_v1`, `flow_id`, `connect_from: [node_id]`.
6. `creative_get_flow_run_status` toutes les `poll_after_seconds` jusqu'à `all_completed`.
7. Écris `transcripts[0].words` dans `$OUT/words.json` (liste `{text, type, start, end}`) et le texte dans `$OUT/transcript.txt`.

Règles :
- Une transcription réussie est facturée (~14 crédits par seconde d'audio, environ 0,05 $ pour 40 s). Ne la relance jamais pour « réessayer ».
- Erreur **429 rate_limited** : rien n'a démarré ni été facturé. Attends 3 à 5 minutes (commande `sleep` en arrière-plan), puis réessaie ; au troisième échec, demande au demandeur s'il veut fournir le texte lui-même.
- Langue détectée souvent « fra » pour la darija : normal. Le texte sort en darija latine (3 = ع, 7 = ح, 9 = ق). Corrige l'orthographe à l'affichage via `captions.replace` / `captions.merge` du storyboard, jamais les minutages.

### Texte fourni par le demandeur

`transcribe_local.py --text` aligne ce texte sur la voix (gratuit, ±0,15 s par mot).

## 4. Vidéo avec son parlé

Si un clip contient une interview ou un commentaire, transcris son `speech_file` comme ci-dessus ; décale ensuite tous les `start/end` de l'instant où le clip commence dans le montage.

## 5. Synthèse à produire avant le storyboard

Un court tableau dans tes notes : temps (pauses incluses) → phrase prononcée → idée à montrer → média ou bloc choisi. C'est la base du storyboard.
