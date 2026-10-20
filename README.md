# Site BitEye — biteye-group.com

Site vitrine de BitEye et de VISION Workspace (promotion immobilière, réalisation, gestion de copropriété).

Site statique en une page :

- `index.html` — page d'accueil (HTML, CSS et JS intégrés) ; charge les bibliothèques depuis `vendor/`
- `admin/` — administration du site : références et prestations, avec droits d'accès (administrateur, éditeur)
- `config.js` — adresse et clé publique de la base Supabase utilisée par l'administration (vide : le site affiche son contenu intégré)
- `supabase/` — schéma de la base, import des références et **guide de mise en service** ([`supabase/README.md`](supabase/README.md))
- `vendor/` — Three.js 0.159 (ville 3D du héros), GSAP 3.12.5 + ScrollTrigger (animations), Lenis 1.1.13 (défilement fluide), supabase-js 2.108 (administration)
- `build.py` — génère `dist/biteye-site.html`, le site en **un seul fichier** autonome (bibliothèques, configuration et images intégrées), qui s'ouvre d'un double-clic, même hors ligne
- `favicon.svg` — icône du site
- `CNAME` — domaine personnalisé `biteye-group.com` (GitHub Pages)

Après toute modification de `index.html` ou de `config.js`, relancer `python3 build.py`.

## Aperçu local

```sh
python3 -m http.server 8000
# puis ouvrir http://localhost:8000 (site) et http://localhost:8000/admin/ (administration)
```

## Reste à faire avant la mise en ligne

- Mettre en service l'administration : suivre [`supabase/README.md`](supabase/README.md).
- Remplacer les maquettes d'écran (données fictives) par de vraies captures de VISION.
- Brancher le formulaire de démonstration sur un service d'envoi (aujourd'hui il ouvre la messagerie du visiteur avec la demande pré-remplie).
- Version arabe (RTL).
