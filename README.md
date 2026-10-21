# Site BitEye — biteye-group.com

Site vitrine de BitEye et de VISION Workspace (promotion immobilière, réalisation, gestion de copropriété).

Site statique en une page :

- `index.html` — page d'accueil (HTML, CSS et JS intégrés) ; charge les bibliothèques depuis `vendor/`
- `admin/` — administration du site : demandes reçues, références, prestations, agenda, vidéo de présentation, témoignages et équipe, avec droits d'accès (administrateur, éditeur)
- `i18n.js` — traductions anglaise et arabe des textes de la page (clé : le texte français)
- `config.js` — adresse et clé publique de la base Supabase utilisée par l'administration (vide : le site affiche son contenu intégré)
- `supabase/` — schéma de la base, import des références et **guide de mise en service** ([`supabase/README.md`](supabase/README.md))
- `vendor/` — Three.js 0.159 (ville 3D du héros), GSAP 3.12.5 + ScrollTrigger (animations), Lenis 1.1.13 (défilement fluide), supabase-js 2.108 (administration)
- `build.py` — génère `dist/biteye-site.html`, le site en **un seul fichier** autonome (bibliothèques, configuration et images intégrées), qui s'ouvre d'un double-clic, même hors ligne
- `favicon.svg` — icône du site
- `CNAME` — domaine personnalisé `biteye-group.com` (GitHub Pages)

Après toute modification de `index.html`, `i18n.js` ou `config.js`, relancer `python3 build.py`.

## Langues

Le site existe en français (par défaut), en anglais et en arabe (mise en page de droite à gauche) : sélecteur FR · EN · ع dans la barre de navigation et dans le menu mobile, ou directement `?lang=en` / `?lang=ar` dans l'adresse. Le choix du visiteur est mémorisé dans son navigateur.

Chaque texte de la page est cherché tel quel dans `i18n.js` ; un texte modifié dans `index.html` sans mise à jour de `i18n.js` reste affiché en français dans les autres langues. Le contenu saisi dans l'administration (références, prestations, événements) n'est pas traduit, sauf l'événement d'exemple Elogia 2026.

## Mise en ligne

Guide complet pour l'hébergeur et Supabase : [`DEPLOIEMENT.md`](DEPLOIEMENT.md). Le fichier `.htaccess` fourni règle HTTPS, cache et types de fichiers sur Apache.

## Aperçu local

```sh
python3 -m http.server 8000
# puis ouvrir http://localhost:8000 (site) et http://localhost:8000/admin/ (administration)
```

## Vidéo de présentation

L'emplacement est juste après l'en-tête (`#video`). Deux façons d'y mettre la vidéo :

- depuis l'administration, onglet **Vidéo** (une fois Supabase en service) ;
- ou en déposant le fichier dans `assets/video/` et en renseignant `data-src` (et `data-poster` pour l'image d'aperçu) sur `<div class="vid" id="vid">` dans `index.html`.

Format conseillé : MP4 H.264 + AAC, 1920×1080, 50 Mo maximum. Rien n'est téléchargé avant le clic sur « Lire », hormis la durée.

## Formulaire de contact

Une fois Supabase branché (`config.js`), le formulaire envoie directement chaque demande dans l'administration (onglet **Demandes**, export CSV). Pour la relier au CRM BitEye, renseigner `window.BITEYE_CRM.url` dans `config.js` : chaque demande y est aussi envoyée en JSON. Sans base ni CRM, le formulaire rédige la demande dans la messagerie du visiteur.

## Reste à faire avant la mise en ligne

- Mettre en service l'administration : suivre [`supabase/README.md`](supabase/README.md).
- Remplacer les maquettes d'écran (données fictives) par de vraies captures de VISION.
- Relier le formulaire au CRM BitEye (`window.BITEYE_CRM.url` dans `config.js`).
- Faire relire les versions anglaise et arabe par un locuteur natif.
- Compléter l'adresse et le lien Google Maps du bureau d'Oran (section `#bureaux` de `index.html`), ajouter les liens LinkedIn et des photos en meilleure qualité pour l'équipe (onglet Équipe).
- Déposer la vidéo de présentation et les témoignages vidéo des clients (onglets Vidéo et Témoignages).
