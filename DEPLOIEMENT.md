# Mise en ligne du site BitEye — guide pour l'ingénieur

Ce document explique comment publier **biteye-group.com** et son **administration** chez l'hébergeur.
Durée : environ 1 heure, en comptant la création de la base de données.

---

## 1. Ce qu'est le projet

- Un **site statique** : HTML, CSS et JavaScript. **Aucun langage serveur** (ni PHP, ni Node), **aucune base locale**.
  N'importe quel hébergement web qui sert des fichiers en **HTTPS** convient (Apache/cPanel, Nginx, LiteSpeed…).
- L'**administration** (`/admin/`) et le formulaire de contact s'appuient sur **Supabase** (service en ligne :
  base PostgreSQL, comptes utilisateurs, stockage des logos et vidéos). Le navigateur parle directement à Supabase ;
  l'hébergeur n'a rien à installer pour cela.
- Tant que Supabase n'est pas configuré (`config.js` vide), le site fonctionne avec son contenu intégré
  et le formulaire ouvre la messagerie du visiteur : **on peut publier le site d'abord, brancher Supabase ensuite.**

## 2. Les fichiers à envoyer chez l'hébergeur

À placer à la **racine web** du domaine (souvent `public_html/` ou `www/`) :

| Élément | Rôle |
|---|---|
| `index.html` | le site (une seule page, tout le contenu) |
| `i18n.js` | traductions anglaise et arabe |
| `config.js` | connexion à Supabase et au CRM (à remplir, voir §4) |
| `favicon.svg` | icône du site |
| `assets/` | logos clients, images |
| `vendor/` | bibliothèques (Three.js, GSAP, Lenis, supabase-js) — **obligatoire**, utilisé aussi par l'administration |
| `admin/` | l'administration (`https://biteye-group.com/admin/`) |
| `.htaccess` | réglages Apache facultatifs mais conseillés (HTTPS, cache, types de fichiers) — voir §3 |

**À ne pas mettre en ligne** (utiles seulement au développement) : `supabase/` (scripts SQL), `dist/`, `build.py`,
`README.md`, `DEPLOIEMENT.md`, `CNAME` (fichier propre à GitHub Pages).

> `dist/biteye-site.html` est une version « tout-en-un » du site en un seul fichier, pratique pour une démonstration
> hors ligne. Elle n'est pas destinée à l'hébergement.

## 3. Réglages du serveur

- **HTTPS obligatoire** (certificat Let's Encrypt ou celui de l'hébergeur) : la connexion à l'administration l'exige.
- **Types de fichiers** : `.js` → `text/javascript`, `.svg` → `image/svg+xml`, `.webp` → `image/webp`,
  `.mp4` → `video/mp4`. Ils sont normalement déjà connus des serveurs récents.
- **Aucune réécriture d'adresse** n'est nécessaire (`/` et `/admin/` sont de vrais dossiers avec un `index.html`).
- Le fichier `.htaccess` fourni (Apache/LiteSpeed) force le HTTPS, active la compression et règle le cache.
  Sur Nginx, reproduire les mêmes règles dans la configuration du site.
- **Ressources externes** chargées par le site : polices Google (`fonts.googleapis.com`, `fonts.gstatic.com`),
  carte Google Maps intégrée (`www.google.com/maps`, section « Nos bureaux »),
  Supabase (`*.supabase.co`) et liens WhatsApp (`wa.me`). Si l'hébergeur ajoute une politique de sécurité
  (Content-Security-Policy), elle doit les autoriser, ainsi que les scripts intégrés à la page (`'unsafe-inline'`).

Vérification rapide après envoi : ouvrir `https://biteye-group.com/` puis `https://biteye-group.com/?lang=ar`
(mise en page de droite à gauche), et `https://biteye-group.com/admin/` (écran « Administration non configurée »
tant que §4 n'est pas fait — c'est normal).

## 4. Brancher l'administration (Supabase)

Le guide détaillé est dans [`supabase/README.md`](supabase/README.md). En résumé :

1. Créer un compte sur <https://supabase.com> puis un projet (région conseillée : **Frankfurt**).
2. **SQL Editor** › exécuter `supabase/schema.sql`, puis `supabase/seed.sql` (171 références actuelles).
   `schema.sql` peut être relancé sans risque lors des mises à jour : il ajoute ce qui manque sans rien effacer.
3. **Authentication › URL Configuration** : *Site URL* et *Redirect URLs* = `https://biteye-group.com/admin/`.
4. **Authentication › Emails › SMTP** : configurer un **serveur d'envoi** (par exemple la messagerie
   de l'hébergeur). Sans cela, Supabase n'envoie que quelques e-mails par heure (confirmation de compte,
   mot de passe oublié).
5. **Project Settings › API** : copier l'URL du projet et la clé **publique** (*anon public* ou *publishable*)
   dans `config.js` :

   ```js
   window.BITEYE_DB = {
     url: 'https://abcdefgh.supabase.co',
     cle: 'sb_publishable_…'      // ou la clé anon « eyJ… »
   };
   ```

   Ces deux valeurs sont publiques par nature. **Ne jamais** mettre la clé *service_role* / *secret* dans le site.
6. Renvoyer `config.js` sur le serveur.
7. Premier administrateur : créer un compte sur `https://biteye-group.com/admin/`, confirmer l'e-mail, puis dans
   **SQL Editor** :

   ```sql
   update public.profils set role = 'admin' where email = 'adresse.du.responsable@biteye-group.com';
   ```

   Ensuite, les rôles des autres personnes se donnent depuis l'onglet **Comptes** de l'administration.
8. Conseillé : désactiver l'inscription libre (**Authentication › Providers › Email › Allow new users to sign up**)
   et inviter les collaborateurs depuis **Authentication › Users › Invite user**.

À partir de là, le formulaire du site enregistre les demandes dans l'onglet **Demandes**, et l'équipe peut gérer
références, prestations, agenda, vidéo de présentation, témoignages vidéo et membres de l'équipe (50 Mo maximum par vidéo).

## 5. Facultatif : relier le formulaire au CRM BitEye

Dans `config.js`, renseigner l'adresse qui doit recevoir chaque demande :

```js
window.BITEYE_CRM = { url: 'https://crm.biteye-group.com/api/demandes' };
```

Le site y envoie, en plus de Supabase, une requête `POST` en JSON :
`{ "nom", "societe", "tel", "metier", "sujet", "langue", "page" }`.
Le CRM doit répondre `2xx` et **autoriser l'origine** `https://biteye-group.com` (en-têtes CORS :
`Access-Control-Allow-Origin` et `Access-Control-Allow-Headers: Content-Type`, réponse à la requête `OPTIONS`).

## 6. Mettre à jour le site plus tard

- Contenu courant (références, prestations, agenda, vidéos, témoignages) : **depuis l'administration**, sans toucher aux fichiers.
- Modification du code : remplacer les fichiers concernés sur le serveur. Après une modification de `index.html`,
  relancer `python3 build.py` seulement si l'on souhaite régénérer la version tout-en-un `dist/`.
- Les textes anglais et arabes sont dans `i18n.js` (clé = texte français exact de la page).

## 7. Liste de contrôle après la mise en ligne

- [ ] `https://biteye-group.com` s'ouvre en HTTPS, `http://` redirige vers `https://`
- [ ] FR · EN · ع : les trois langues s'affichent (sélecteur dans la barre et dans le menu mobile)
- [ ] Ville 3D visible sur ordinateur, menu latéral sur mobile
- [ ] `/admin/` : connexion du premier administrateur, onglets visibles
- [ ] Formulaire de démonstration : la demande apparaît dans l'onglet **Demandes**
- [ ] Une référence ajoutée dans l'administration apparaît sur le site
- [ ] Bouton WhatsApp : ouvre une conversation avec le 0560 06 36 41
