# Consignes Claude — dépôt Site BitEye

## Demandes de vidéo : l'équipe et l'ordre de passage

Toute demande de vidéo, pub, reel, story, spot, clip ou motion design suit la méthode `.claude/skills/biteye-video-ad/SKILL.md`. La session principale est le chef d'orchestre : les agents ne peuvent pas s'appeler entre eux, c'est donc elle qui les lance.

| Agent | Rôle |
|---|---|
| `biteye-audio-engineer` | voix « studio » et mots minutés, outils gratuits |
| `biteye-media-editor` | vidéos et photos : plans, coupes, recadrage, stabilisation, étalonnage, détourage, outils gratuits |
| `biteye-marketing-strategist` | veille web, empreinte BitEye, 2 ou 3 concepts à valider |
| `biteye-video-producer` | storyboard, animation synchronisée, contrôle, MP4 + HTML |

1. **Cadrer d'abord** : dès que la demande et ses fichiers arrivent, pose au demandeur les questions de cadrage (`biteye-video-ad` §0 : diffusion et formats, objectif, cible et langue, style et identité, infos à afficher). Ne lance aucun agent avant les réponses, sauf l'étape 2 qui n'en dépend pas.
2. **Préparer en parallèle** (un seul message, agents en arrière-plan) : `biteye-audio-engineer` pour chaque voix, `biteye-media-editor` pour les vidéos et les photos. Donne-leur les chemins absolus des fichiers et le dossier `$OUT` (scratchpad de la session, sinon `./.video-out/<slug>/`).
3. **Proposer** : `biteye-marketing-strategist` avec le brief, la transcription et `media.md`. Montre au demandeur le concept recommandé et les autres concepts (publie `proposition.md` en page si c'est utile), ainsi que les mots incertains de la transcription. **Attends son choix.**
4. **Produire** : `biteye-video-producer` avec le brief, le concept choisi et les médias préparés.
5. **Livrer** : publie `<slug>.html` comme Artifact (avec `media/*` via `files` si l'agent l'indique), envoie les MP4 et la page `.local.html`, et résume les comptes rendus.
6. **Retouches** : renvoie-les au même agent (SendMessage), avec le dossier et le storyboard existants.

Raccourci : pour une simple retouche ou une déclinaison de format d'une vidéo déjà validée, va directement à l'étape 4.

Si les agents ne sont pas disponibles dans la session (ils se chargent au démarrage), applique toi-même les skills dans le même ordre, ou lance un agent générique en lui demandant de suivre le fichier de l'agent concerné.

## Outils

Gratuits et locaux par défaut (`bash .claude/skills/biteye-video-ad/scripts/setup_free_tools.sh`). ElevenLabs et tout service payant seulement si le demandeur le veut, coût annoncé avant.

## Site

Le site (`index.html`, `favicon.svg`, `CNAME`) est publié par GitHub Pages sur biteye-group.com. N'y ajoute ni vidéos ni médias de clients ; les dossiers commençant par un point (`.claude/`, `.video-out/`) ne sont pas publiés.
