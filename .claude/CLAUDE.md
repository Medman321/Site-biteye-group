# Consignes Claude — dépôt Site BitEye

## Demandes de vidéo

Toute demande de vidéo, pub, reel, story, spot, clip ou motion design (avec ou sans mémo vocal, photos, séquences vidéo ou données) est confiée à l'agent **`biteye-video-producer`** (`.claude/agents/biteye-video-producer.md`) :

1. Lance l'agent avec la demande complète, les chemins absolus des fichiers reçus, le format voulu s'il est précisé, et le dossier de sortie (scratchpad de la session, sinon `./.video-out/<slug>/`).
2. À son retour : publie `<slug>.html` comme Artifact (avec `media/*` via `files` si l'agent l'indique), envoie le MP4 et la page `<slug>.local.html` au demandeur, et résume le compte rendu de l'agent.
3. Une retouche demandée ensuite (texte, scène, format) repasse par le même agent, en lui indiquant le dossier et le storyboard existants.

Si l'agent n'est pas disponible dans la session, applique toi-même le skill `biteye-video-ad` (`.claude/skills/biteye-video-ad/SKILL.md`).

## Site

Le site (`index.html`, `favicon.svg`, `CNAME`) est publié par GitHub Pages sur biteye-group.com. N'y ajoute ni vidéos ni médias de clients ; les dossiers commençant par un point (`.claude/`, `.video-out/`) ne sont pas publiés.
