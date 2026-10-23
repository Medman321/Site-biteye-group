# Consignes Claude — dépôt Site BitEye

## Demandes de vidéo : l'équipe et l'ordre de passage

Toute demande de vidéo, pub, reel, story, spot, clip ou motion design suit la méthode `.claude/skills/biteye-video-ad/SKILL.md`, avec l'équipe ci-dessous.

| # | Agent | Rôle |
|---|---|---|
| 0 | session principale (coordinateur) | orchestration, arbitrages, questions au demandeur, livraison |
| 1 | `scenario-interview-architect` | narration B2B, ordre et liaison des extraits, ponts entre intervenants, voix off |
| 2 | `audio-studio-analyst` | analyse au dixième de seconde, coupes sur les creux, raccords J/L-cut, room tone, lit musical avec ducking, mastering −14 LUFS |
| 3 | `market-strategy-director` | veille, concepts, copywriting VISION Workspace, structure 40 s, légendes Instagram/TikTok/LinkedIn |
| 4 | `art-direction-design-critic` | audit esthétique AVANT le rendu final : transitions, flous, couleurs, lisibilité |
| 5 | `vfx-roto-compositing-engineer` | préparation des vidéos/photos, raccord couleur, détourage 2.5D (animations entre l'intervenant et son fond), masquage d'incrustations, .jsx After Effects optionnel |
| 6 | `motion-video-producer` | storyboard, moteur HTML/Playwright/ffmpeg, rendu MP4 + HTML |
| 7 | `quality-brand-inspector` | contrôle qualité et marque APRÈS rendu, verdict livrable / à reprendre |
| 8 | `token-efficiency-auditor` | coûts mesurés, gaspillages, capitalisation des scripts en outils CLI |

1. **Cadrer** : questions de cadrage (`biteye-video-ad` §0 : diffusion et formats, objectif, cible et langue, style, nom + poste + photo de chaque voix, infos à afficher).
2. **Préparer en parallèle** : 2 (son) et 5 (image) sur chaque média ; 3 fait la veille.
3. **Proposer** : 3 (concepts) puis 1 (scénario minuté du concept choisi). **Attendre le choix du demandeur.**
4. **Pré-rendu** : 6 construit le storyboard et les images clés ; 4 audite ; 6 corrige (une passe).
5. **Rendre** : 6 rend les MP4 ; 7 contrôle ; une reprise si « à reprendre ».
6. **Livrer** : la session publie la page en Artifact et envoie les MP4, la légende (3) et le rapport qualité (7).
7. **Bilan** : 8 audite l'efficacité ; la session applique les capitalisations validées.

Les agents ne peuvent pas s'appeler entre eux : la session principale les lance, transmet les fichiers et arbitre. Retouches : renvoyer au même agent (SendMessage).

Raccourci : pour une simple retouche ou une déclinaison de format d'une vidéo déjà validée, va directement à l'étape 4.

Si les agents ne sont pas disponibles dans la session (ils se chargent au démarrage), applique toi-même les skills dans le même ordre, ou lance un agent générique en lui demandant de suivre le fichier de l'agent concerné.

## GitHub (dépôt public)

- **Contrôle automatique** : toute modification de `.claude/skills/**` dans une pull request déclenche « Vidéo · contrôle du moteur » (reconstruit les exemples, planches et MP4 court en artefacts). Ne fusionne pas une PR dont ce contrôle est rouge.
- **Rendu dans le cloud** : « Vidéo · rendu » (Actions → Run workflow) rend un projet (dossier avec `storyboard.json` et `storyboard-*.json`), passe la voix au studio, joint MP4 + HTML + planches au run et, sur demande, crée une Release téléchargeable. Les médias arrivent par `archive_url` (lien .zip), jamais par un commit.
- **Demandes par issue** : modèle « Demande de vidéo » (questions de cadrage). Avec « @claude » dans l'issue et le secret configuré (`.github/workflows/claude.yml`), Claude traite la demande dans GitHub en suivant ces consignes ; sinon, traite l'issue depuis une session.
- **Public** : issues, artefacts, Releases et fichiers du dépôt sont visibles par tous. Pour des médias ou des vidéos confidentiels, utilise le scratchpad de la session ou un dépôt privé dédié.

## Outils

Gratuits et locaux par défaut (`bash .claude/skills/biteye-video-ad/scripts/setup_free_tools.sh`). ElevenLabs et tout service payant seulement si le demandeur le veut, coût annoncé avant.

## Site

Le site (`index.html`, `favicon.svg`, `CNAME`) est publié par GitHub Pages sur biteye-group.com. N'y ajoute ni vidéos ni médias de clients ; les dossiers commençant par un point (`.claude/`, `.video-out/`) ne sont pas publiés.
