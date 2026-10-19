# Site BitEye — biteye-group.com

Site vitrine de BitEye et de VISION Workspace (promotion immobilière, réalisation, gestion de copropriété).

Site statique en une page :

- `index.html` — page d'accueil (HTML, CSS et JS intégrés) ; charge les bibliothèques depuis `vendor/`
- `vendor/` — Three.js 0.159 (ville 3D du héros), GSAP 3.12.5 + ScrollTrigger (animations), Lenis 1.1.13 (défilement fluide)
- `build.py` — génère `dist/biteye-site.html`, le site en **un seul fichier** autonome (bibliothèques et favicon intégrés), qui s'ouvre d'un double-clic, même hors ligne
- `favicon.svg` — icône du site
- `CNAME` — domaine personnalisé `biteye-group.com` (GitHub Pages)

Après toute modification de `index.html`, relancer `python3 build.py`.

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
