---
name: biteye-video-ad
description: Produire une vidéo publicitaire motion design BitEye / VISION Workspace, livrée en MP4 et en page HTML synchronisée, à partir d'un mémo vocal, de photos, de séquences vidéo ou de simples données (chiffres, texte, script). À utiliser pour toute demande de vidéo, pub, reel, story, spot, clip promo ou motion design.
---

# Vidéo publicitaire BitEye — méthode de bout en bout

Ce skill orchestre les quatre autres :

| Étape | Skill | Rôle |
|---|---|---|
| Analyser | `media-analysis` | voix → transcription mot à mot + pauses ; photos et vidéos → contenu, cadrage, plans |
| Écrire (si pas de voix) | `voiceover-script` | script darija/français, voix off ElevenLabs, musique |
| Habiller | `biteye-brand` | couleurs, logo, ton, vocabulaire métier, mentions obligatoires |
| Monter et rendre | `motion-engine` | storyboard.json → HTML synchronisé → MP4 |

Lis chaque SKILL.md au moment de l'étape (chemins : `.claude/skills/<nom>/SKILL.md`).

## 1. Cadrer la demande (sans bloquer)

Relève dans la demande, sinon prends le défaut et dis-le dans le compte rendu :

- **Format** : `9:16` (Reels, TikTok, Stories, Status WhatsApp) par défaut ; `16:9` (YouTube, écran salon, site) ; `1:1` ou `4:5` (fil Facebook / Instagram). Plusieurs formats demandés → un storyboard par format (même contenu, mise en page revue).
- **Durée** : celle de la voix + 2,5 à 4 s d'écran final, arrondie. Sans voix : 15 s, 30 s ou 45 s.
- **Public et langue** : promoteurs, entreprises de réalisation, syndics de copropriété en Algérie. Sous-titres dans la langue parlée (darija en lettres latines par défaut), titres à l'écran en français.
- **Appel à l'action** : « Demande ta démo » (tutoiement si la voix tutoie) ou « Demandez votre démo », + `biteye-group.com`.

Ne pose une question que si un élément manque et qu'aucun défaut raisonnable n'existe (par exemple : des chiffres clients à afficher sans source).

## 2. Préparer un dossier de travail

```
OUT=<scratchpad de la session>/video-<slug>    # sinon ./.video-out/<slug> (ignoré par git)
mkdir -p "$OUT/src"   # copier ici les médias reçus (voix, photos, clips)
```
Ne jamais écrire les médias du client dans le dépôt : le site est publié par GitHub Pages.

## 3. Analyser les médias

Suis `media-analysis`. Résultat attendu dans `$OUT` :
- `analysis/analysis.json` (durées, pauses, plans, orientation) ;
- `words.json` (transcription mot à mot) pour toute voix ;
- une description écrite de chaque photo / plan vidéo après les avoir **regardés** avec Read (aperçus et planches générés).

## 4. Écrire le storyboard

1. Découpe la voix en **temps forts** : une scène par idée, bornée par les pauses (`silences`). Une longue pause (> 1,5 s) = moment idéal pour une révélation (logo, produit).
2. Pour chaque scène, choisis les blocs (`motion-engine`) qui **montrent ce qui est dit** : chaque mot-clé prononcé déclenche son élément (`at` = `start` du mot dans `words.json`). C'est ce qui donne la synchronisation.
3. Place les médias du client là où ils servent le propos : photo de chantier en fond (`background` avec Ken Burns), clip en bloc `video`, galerie pour plusieurs photos, mémo vocal conservé tel quel comme bande son.
4. Termine toujours par l'écran final de marque (logo, VISION Workspace, accroche, CTA, site).
5. Écris `$OUT/storyboard.json`. Modèles validés : `.claude/skills/motion-engine/examples/vision-darija-9x16/storyboard.json` (vertical) et `examples/vision-darija-16x9/storyboard.json` (paysage, scènes en `split`). Vérifie la zone utile du format (tableau dans `motion-engine`).

Règles de rythme : 1 idée visuelle toutes les 2 à 4 s ; jamais plus de ~12 mots de titre à l'écran ; entrée de chaque élément sur le mot, sortie de la scène 0,3 s avant la phrase suivante.

## 5. Construire, vérifier, rendre

```
ENG=.claude/skills/motion-engine/scripts
python3 -I $ENG/build.py "$OUT/storyboard.json" --out "$OUT/out"
node $ENG/render.js "$OUT/out/<slug>.local.html" --stills "$OUT/out/stills"
```
Regarde `$OUT/out/stills/sheet.jpg` avec Read, et le champ `fit` de la sortie (scènes réduites sous 0,9 à alléger). Corrige ce qui déborde, se chevauche, est illisible ou mal synchronisé, puis reconstruis : **une seule passe de corrections**. Ensuite :
```
node $ENG/render.js "$OUT/out/<slug>.local.html" --mp4 "$OUT/out/<slug>.mp4"
```
Contrôle : `ffprobe` (durée, piste audio présente) et une image extraite au milieu de la vidéo.

## 6. Livrer

Fichiers à remettre :
- `<slug>.mp4` — la vidéo, son inclus ;
- `<slug>.local.html` — page autonome, s'ouvre dans un navigateur, voix synchronisée ;
- `<slug>.html` — même page, à publier comme Artifact (pas de doctype, le publieur l'ajoute) ; si `sidecar_media` vaut true, publier aussi `media/*` via `files`.

Compte rendu court au demandeur : tableau temps → ce qui est dit → ce qui est animé ; défauts retenus (format, CTA) ; données inventées pour l'exemple, signalées comme telles ; coût de transcription ou de voix ElevenLabs.
