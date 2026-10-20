# Administration du site — mise en service

L’administration (`biteye-group.com/admin/`) permet de gérer **les références** et **les prestations** du site,
avec des **droits d’accès** par rôle. Les données sont stockées dans **Supabase** (base de données, comptes et
stockage des logos), le site restant hébergé sur GitHub Pages.

Tant que Supabase n’est pas configuré, le site affiche son contenu intégré : rien ne casse.

## Les rôles

| | Administrateur | Éditeur | Compte sans rôle |
|---|:-:|:-:|:-:|
| Voir l’administration | ✓ | ✓ | — (écran « en attente ») |
| Ajouter, modifier une référence ou une prestation | ✓ | ✓ | — |
| Masquer / publier | ✓ | ✓ | — |
| Supprimer définitivement | ✓ | — | — |
| Attribuer les rôles | ✓ | — | — |
| Consulter le journal des modifications | ✓ | — | — |

Ces règles sont appliquées **par la base elle-même** (Row Level Security) : même en contournant l’interface,
un éditeur ne peut ni supprimer ni changer un rôle. Il reste toujours au moins un administrateur.

## Mise en service (une seule fois, environ 15 minutes)

### 1. Créer le projet Supabase
1. Créez un compte sur <https://supabase.com> puis **New project** (région conseillée : *Frankfurt*, la plus proche d’Alger).
2. Notez le mot de passe de la base dans un endroit sûr.

### 2. Créer les tables et les droits
1. Dans le projet : **SQL Editor** › **New query**.
2. Collez le contenu de [`schema.sql`](schema.sql) et cliquez **Run**.
3. Nouvelle requête : collez [`seed.sql`](seed.sql) et cliquez **Run** (importe les 171 références actuelles du site).

`schema.sql` peut être relancé sans risque après une mise à jour du site : il ajoute ce qui manque (par exemple les tables `demandes`, `temoignages`, `reglages` et l’espace de stockage `videos`) sans effacer le contenu.

### 3. Régler la connexion
Dans **Authentication** › **URL Configuration** :
- **Site URL** : `https://biteye-group.com/admin/`
- **Redirect URLs** : ajoutez `https://biteye-group.com/admin/`

Ces adresses servent aux liens reçus par e-mail (confirmation du compte, mot de passe oublié).
Dans **Authentication** › **Email Templates**, vous pouvez traduire les e-mails en français.

### 4. Brancher le site
Dans **Project Settings** › **API**, copiez l’**URL du projet** et la clé **anon public** (ou **publishable**),
puis renseignez-les dans [`config.js`](../config.js) à la racine du site :

```js
window.BITEYE_DB = {
  url: 'https://abcdefgh.supabase.co',
  cle: 'eyJhbGciOi…'   // ou sb_publishable_…
};
```

Ces deux valeurs sont **publiques par nature** (elles sont lisibles dans le site) : la sécurité repose sur les
règles de la base, pas sur ce fichier. Ne mettez **jamais** la clé *service_role* ou *secret* dans le site.

Enregistrez, publiez sur GitHub : le site lit désormais ses références et ses prestations dans Supabase.

### 5. Devenir administrateur
1. Ouvrez `https://biteye-group.com/admin/`, cliquez **Créer un compte**, puis confirmez votre e-mail.
2. Dans Supabase › **SQL Editor**, exécutez (avec votre adresse) :

```sql
update public.profils set role = 'admin' where email = 'votre.adresse@exemple.com';
```

C’est la seule commande à taper : ensuite, tout se fait depuis l’administration.

## Ajouter un collaborateur
1. La personne ouvre `biteye-group.com/admin/` et clique **Créer un compte**.
2. Vous ouvrez l’onglet **Comptes** (un badge signale les comptes en attente) et lui donnez le rôle **Éditeur**
   ou **Administrateur**. Pour lui retirer l’accès : rôle **Aucun**.

Pour empêcher toute création de compte spontanée, désactivez **Authentication › Providers › Email › Allow new users
to sign up** et invitez les personnes depuis **Authentication › Users › Invite user**.

## Ce que gère l’administration
- **Références** : nom, ville(s), filtres du site (Oran, Alger, Autres wilayas), logo (redimensionné
  automatiquement), ordre d’affichage, publiée ou masquée. Les compteurs du site (« 171 références »,
  filtres, note de bas de page) se mettent à jour d’eux-mêmes ; le bandeau des partenaires aussi.
- **Prestations** : chaque prestation publiée obtient sa **fiche plein écran** au style du site
  (`biteye-group.com/#p-adresse`), sa **tuile** dans « Quel est votre besoin ? », son entrée dans le **menu Services**
  et un **onglet** dans toutes les fiches. Les cinq fiches d’origine restent intégrées au site.
- **Demandes** : les demandes envoyées par le formulaire du site (démonstration, rendez-vous d’un salon,
  accompagnement commercial), à rappeler puis marquer « traitées » ; export CSV pour Excel ou le CRM BitEye.
  Le site peut seulement déposer une demande : il ne peut ni les lire ni les modifier.
- **Témoignages** : les vidéos de vos clients (nom, fonction, société, phrase clé, vidéo de 50 Mo maximum,
  image d’aperçu), publiées ou masquées. Tant qu’aucun témoignage n’est publié, le site affiche trois emplacements « bientôt disponible ».
- **Vidéo** : la vidéo de présentation affichée après l’en-tête (MP4 ou WebM, 50 Mo maximum, image d’aperçu
  et titre facultatifs), affichée ou masquée d’un clic. Sans vidéo publiée, le site affiche « Vidéo bientôt disponible ».
- **Journal** : qui a ajouté, modifié, masqué ou supprimé quoi, et quand.

## Essais en local
`schema.sql` accepte les logos en `http://localhost` pour les essais ; en production, les logos sont servis en https par Supabase.
