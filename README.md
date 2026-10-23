# Site BitEye — biteye-group.com

Site vitrine de BitEye et de VISION Workspace (promotion immobilière, réalisation, gestion de copropriété).

Site statique en une page, sans étape de build :

- `index.html` — page d'accueil (HTML, CSS et JS intégrés ; polices Google Fonts, animations GSAP via cdnjs)
- `favicon.svg` — icône du site
- `CNAME` — domaine personnalisé `biteye-group.com` (GitHub Pages)

## Aperçu local

```sh
python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

## Reste à faire avant la mise en ligne

- Remplacer les maquettes d'écran (données fictives) par de vraies captures de VISION.
- Brancher l'envoi du formulaire de démonstration (aujourd'hui il affiche seulement un message).
- Ajouter les logos clients (avec leur accord) à la place des emplacements vides.
- Confirmer les couleurs de la charte (vert forêt `#0F1A14`, citron `#C4EF4E`) et l'adresse `contact@biteye-group.com`.
- Version arabe (RTL).

## Studio vidéo (Claude Code)

`.claude/` contient une équipe d'agents Claude Code qui produit les vidéos marketing de VISION Workspace (MP4 + page HTML synchronisée) à partir de mémos vocaux, de photos et de vidéos, avec des outils gratuits : voir `.claude/CLAUDE.md`.

- Commander une vidéo : issue « Demande de vidéo ».
- Rendre une vidéo dans le cloud : Actions → « Vidéo · rendu ».
- Chaque modification du moteur est contrôlée par « Vidéo · contrôle du moteur ».

Dépôt public : ne versez ici aucun média client.
