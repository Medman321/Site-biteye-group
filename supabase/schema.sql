-- BitEye — base de données du site biteye-group.com (Supabase)
--
-- À exécuter une seule fois : Supabase > SQL Editor > New query > coller ce fichier > Run.
-- Le script peut être relancé sans risque : il ne recrée que ce qui manque et remet les règles à jour.
--
-- Deux rôles :
--   admin   : gère tout, y compris les comptes, les rôles et la suppression définitive.
--   editeur : ajoute et modifie les références et les prestations (il peut les masquer, pas les supprimer).
-- Un compte qui vient d'être créé n'a aucun droit tant qu'un administrateur ne lui a pas donné un rôle.
-- Toutes les règles sont appliquées par la base elle-même (Row Level Security) : l'interface ne fait que les refléter.

-- ═══════════════════════════════ Comptes et rôles ═══════════════════════════════

do $$ begin
  create type public.role_site as enum ('admin', 'editeur');
exception when duplicate_object then null; end $$;

create table if not exists public.profils (
  id      uuid primary key references auth.users (id) on delete cascade,
  email   text not null,
  nom     text not null default '',
  role    public.role_site,                 -- vide : compte en attente, aucun droit
  cree_le timestamptz not null default now()
);

create or replace function public.mon_role() returns public.role_site
language sql stable security definer set search_path = public as $$
  select role from public.profils where id = auth.uid()
$$;

create or replace function public.est_equipe() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce(public.mon_role() in ('admin', 'editeur'), false)
$$;

create or replace function public.est_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce(public.mon_role() = 'admin', false)
$$;

-- Chaque nouveau compte reçoit sa fiche, sans rôle
create or replace function public.nouveau_compte() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profils (id, email, nom)
  values (new.id, new.email, coalesce(left(trim(new.raw_user_meta_data ->> 'nom'), 80), ''))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists nouveau_compte on auth.users;
create trigger nouveau_compte after insert on auth.users
  for each row execute function public.nouveau_compte();

-- Il reste toujours au moins un administrateur
create or replace function public.garder_un_admin() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if old.role = 'admin' and new.role is distinct from 'admin'
     and not exists (select 1 from public.profils where role = 'admin' and id <> old.id) then
    raise exception 'Il doit rester au moins un administrateur.' using errcode = 'P0001';
  end if;
  return new;
end $$;

drop trigger if exists garder_un_admin on public.profils;
create trigger garder_un_admin before update of role on public.profils
  for each row execute function public.garder_un_admin();

-- ═══════════════════════════════ Contenu du site ═══════════════════════════════

create table if not exists public.references_clients (
  id          bigint generated always as identity primary key,
  nom         text not null check (char_length(trim(nom)) between 2 and 120),
  ville       text not null check (char_length(trim(ville)) between 2 and 80),
  -- filtres du site : oran, alger, autres (une référence peut être dans plusieurs)
  groupes     text[] not null default '{autres}'
              check (cardinality(groupes) > 0 and groupes <@ array['oran', 'alger', 'autres']),
  -- https (stockage Supabase), assets/ (logos livrés avec le site) ; http://localhost seulement pour les essais locaux
  logo_url    text check (logo_url is null or logo_url ~ '^(https://|assets/|http://(localhost|127\.0\.0\.1)(:[0-9]+)?/)'),
  ordre       integer not null default 1000,
  publie      boolean not null default true,
  modifie_le  timestamptz not null default now(),
  modifie_par uuid references auth.users (id) on delete set null
);

alter table public.references_clients drop constraint if exists references_clients_logo_url_check;
alter table public.references_clients add constraint references_clients_logo_url_check
  check (logo_url is null or logo_url ~ '^(https://|assets/|http://(localhost|127\.0\.0\.1)(:[0-9]+)?/)');

-- Prestations ajoutées depuis l'administration. Chacune a sa fiche plein écran sur le site (#p-<slug>),
-- sa tuile dans « Quel est votre besoin ? » et son entrée dans le menu Services.
create table if not exists public.prestations (
  id               bigint generated always as identity primary key,
  slug             text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and char_length(slug) <= 50),
  titre            text not null check (char_length(trim(titre)) between 2 and 60),
  accroche         text not null check (char_length(trim(accroche)) between 2 and 80),
  accroche_couleur text not null default '' check (char_length(accroche_couleur) <= 60),
  description      text not null default '' check (char_length(description) <= 600),
  icone            text not null default 'outils'
                   check (icone in ('logiciel', 'distance', 'serveur', 'securite', 'equipe', 'outils',
                                    'graphique', 'document', 'telephone', 'camera', 'formation', 'support')),
  -- blocs de la fiche : [{"titre": "…", "points": ["…", "…"]}]
  blocs            jsonb not null default '[]' check (jsonb_typeof(blocs) = 'array' and jsonb_array_length(blocs) <= 6),
  -- besoins qui allument la tuile (« Tout mettre en place » les allume toutes)
  besoins          text[] not null default '{}' check (besoins <@ array['equiper', 'distance', 'vendre']),
  ordre            integer not null default 1000,
  publie           boolean not null default false,
  modifie_le       timestamptz not null default now(),
  modifie_par      uuid references auth.users (id) on delete set null
);


-- Agenda : salons, journées portes ouvertes, conférences… Chaque événement publié apparaît dans la section
-- « Agenda » du site (le prochain en grand) et a sa fiche plein écran (#e-<slug>).
create table if not exists public.evenements (
  id               bigint generated always as identity primary key,
  slug             text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and char_length(slug) <= 50),
  titre            text not null check (char_length(trim(titre)) between 2 and 80),
  type             text not null default 'salon'
                   check (type in ('salon', 'portes-ouvertes', 'conference', 'formation', 'autre')),
  lieu             text not null default '' check (char_length(lieu) <= 120),
  ville            text not null default '' check (char_length(ville) <= 60),
  date_debut       date not null,
  date_fin         date,
  -- dates pas encore annoncées : le site affiche « periode » (ex. « Décembre 2026 ») et « Dates à confirmer »
  dates_confirmees boolean not null default true,
  periode          text not null default '' check (char_length(periode) <= 60),
  stand            text not null default '' check (char_length(stand) <= 80),
  organisateur     text not null default '' check (char_length(organisateur) <= 120),
  accroche         text not null default '' check (char_length(accroche) <= 200),
  description      text not null default '' check (char_length(description) <= 1200),
  -- programme : [{"titre": "…", "texte": "…"}]
  programme        jsonb not null default '[]' check (jsonb_typeof(programme) = 'array' and jsonb_array_length(programme) <= 10),
  image_url        text check (image_url is null or image_url ~ '^(https://|assets/|http://(localhost|127\.0\.0\.1)(:[0-9]+)?/)'),
  lien_externe     text check (lien_externe is null or lien_externe ~ '^https://'),
  rendez_vous      boolean not null default true,   -- bouton « Réserver un rendez-vous »
  publie           boolean not null default false,
  modifie_le       timestamptz not null default now(),
  modifie_par      uuid references auth.users (id) on delete set null,
  check (date_fin is null or date_fin >= date_debut)
);

-- Réglages du site : une ligne par réglage. video_accueil = {"url", "poster", "titre", "publie"}
create table if not exists public.reglages (
  cle         text primary key check (cle in ('video_accueil')),
  valeur      jsonb not null default '{}' check (jsonb_typeof(valeur) = 'object'),
  modifie_le  timestamptz not null default now(),
  modifie_par uuid references auth.users (id) on delete set null
);

-- Témoignages vidéo des clients (section « Nos clients en parlent »)
create table if not exists public.temoignages (
  id          bigint generated always as identity primary key,
  nom         text not null check (char_length(trim(nom)) between 2 and 80),
  societe     text not null default '' check (char_length(societe) <= 120),
  fonction    text not null default '' check (char_length(fonction) <= 80),
  citation    text not null default '' check (char_length(citation) <= 220),
  video_url   text not null check (video_url ~ '^(https://|assets/|http://(localhost|127\.0\.0\.1)(:[0-9]+)?/)'),
  poster      text check (poster is null or poster ~ '^(https://|assets/|http://(localhost|127\.0\.0\.1)(:[0-9]+)?/)'),
  ordre       integer not null default 100,
  publie      boolean not null default false,
  modifie_le  timestamptz not null default now(),
  modifie_par uuid references auth.users (id) on delete set null
);

-- Métier du client (pastille affichée sous la vidéo) ; ajouté après coup, d'où « add column if not exists »
alter table public.temoignages add column if not exists metier text not null default ''
  check (metier in ('', 'Promotion immobilière', 'Réalisation', 'Gestion de copropriété', 'Plusieurs métiers'));

-- Membres de l'équipe (section « Les personnes derrière le produit »)
create table if not exists public.equipe (
  id          bigint generated always as identity primary key,
  nom         text not null check (char_length(trim(nom)) between 2 and 80),
  poste       text not null default '' check (char_length(poste) <= 80),
  pole        text not null default 'technique' check (pole in ('direction', 'technique', 'marketing')),
  photo_url   text check (photo_url is null or photo_url ~ '^(https://|assets/|http://(localhost|127\.0\.0\.1)(:[0-9]+)?/)'),
  linkedin    text check (linkedin is null or linkedin ~ '^https://([a-z]+\.)?linkedin\.com/'),
  ordre       integer not null default 100,
  publie      boolean not null default true,
  modifie_le  timestamptz not null default now(),
  modifie_par uuid references auth.users (id) on delete set null
);

-- Demandes envoyées par le formulaire du site (démonstration, rendez-vous, accompagnement)
create table if not exists public.demandes (
  id          bigint generated always as identity primary key,
  cree_le     timestamptz not null default now(),
  nom         text not null check (char_length(trim(nom)) between 2 and 80),
  societe     text not null check (char_length(trim(societe)) between 1 and 120),
  tel         text not null check (tel ~ '^[0-9 +.()-]{8,20}$'),
  metier      text not null default '' check (char_length(metier) <= 40),
  sujet       text not null default '' check (char_length(sujet) <= 140),
  langue      text not null default 'fr' check (langue in ('fr', 'en', 'ar')),
  page        text not null default '' check (char_length(page) <= 200),
  statut      text not null default 'nouvelle' check (statut in ('nouvelle', 'traitee')),
  note        text not null default '' check (char_length(note) <= 500),
  modifie_le  timestamptz,
  modifie_par uuid references auth.users (id) on delete set null
);

-- Anti-répétition : une même ligne téléphonique ne peut pas envoyer plus d'une demande par minute
create or replace function public.demande_freiner() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from public.demandes where tel = new.tel and cree_le > now() - interval '1 minute') then
    raise exception 'Demande déjà reçue, merci de patienter une minute.' using errcode = 'P0001';
  end if;
  new.statut := 'nouvelle'; new.note := ''; new.cree_le := now();
  return new;
end $$;
drop trigger if exists demande_freiner on public.demandes;
create trigger demande_freiner before insert on public.demandes
  for each row execute function public.demande_freiner();

create or replace function public.horodater() returns trigger
language plpgsql as $$
begin
  new.modifie_le := now();
  new.modifie_par := auth.uid();
  return new;
end $$;

drop trigger if exists horodater on public.references_clients;
create trigger horodater before insert or update on public.references_clients
  for each row execute function public.horodater();
drop trigger if exists horodater on public.prestations;
create trigger horodater before insert or update on public.prestations
  for each row execute function public.horodater();
drop trigger if exists horodater on public.evenements;
create trigger horodater before insert or update on public.evenements
  for each row execute function public.horodater();
drop trigger if exists horodater on public.equipe;
create trigger horodater before insert or update on public.equipe
  for each row execute function public.horodater();
drop trigger if exists horodater on public.temoignages;
create trigger horodater before insert or update on public.temoignages
  for each row execute function public.horodater();
drop trigger if exists horodater on public.demandes;
create trigger horodater before update on public.demandes
  for each row execute function public.horodater();
drop trigger if exists horodater on public.reglages;
create trigger horodater before insert or update on public.reglages
  for each row execute function public.horodater();

-- ═══════════════════════════════ Journal ═══════════════════════════════

create table if not exists public.journal (
  id        bigint generated always as identity primary key,
  quand     timestamptz not null default now(),
  qui       uuid,
  qui_email text,
  action    text not null,
  objet     text not null,
  libelle   text
);

create or replace function public.journaliser() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  ligne jsonb := to_jsonb(coalesce(new, old));
  quoi  text;
begin
  quoi := coalesce(nullif(ligne ->> 'nom', '') || coalesce(' · ' || nullif(ligne ->> 'societe', ''), ''), ligne ->> 'titre', ligne ->> 'email', ligne ->> 'cle');
  if tg_table_name = 'profils' then
    quoi := quoi || ' → ' || coalesce(new.role::text, 'sans rôle');
  end if;
  insert into public.journal (qui, qui_email, action, objet, libelle)
  values (auth.uid(), (select email from public.profils where id = auth.uid()),
          case tg_op when 'INSERT' then 'ajout' when 'UPDATE' then 'modification' else 'suppression' end,
          tg_table_name, quoi);
  return null;
end $$;

drop trigger if exists journaliser on public.references_clients;
create trigger journaliser after insert or update or delete on public.references_clients
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.prestations;
create trigger journaliser after insert or update or delete on public.prestations
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.evenements;
create trigger journaliser after insert or update or delete on public.evenements
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.equipe;
create trigger journaliser after insert or update or delete on public.equipe
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.temoignages;
create trigger journaliser after insert or update or delete on public.temoignages
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.demandes;
create trigger journaliser after update or delete on public.demandes
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.reglages;
create trigger journaliser after insert or update or delete on public.reglages
  for each row execute function public.journaliser();
drop trigger if exists journaliser on public.profils;
create trigger journaliser after update of role on public.profils
  for each row execute function public.journaliser();

-- ═══════════════════════════════ Droits d'accès ═══════════════════════════════

alter table public.profils            enable row level security;
alter table public.references_clients enable row level security;
alter table public.prestations        enable row level security;
alter table public.journal            enable row level security;
alter table public.evenements         enable row level security;
alter table public.reglages           enable row level security;
alter table public.temoignages        enable row level security;
alter table public.equipe             enable row level security;
alter table public.demandes           enable row level security;

-- Seuls le rôle et le nom d'un profil peuvent être modifiés (jamais l'identifiant ni l'e-mail)
revoke all on public.profils from anon;
revoke insert, update, delete on public.profils from authenticated;
grant select on public.profils to authenticated;
grant update (role, nom) on public.profils to authenticated;
revoke all on public.journal from anon;
revoke insert, update, delete on public.journal from authenticated;
grant select on public.journal to authenticated;

drop policy if exists "profils : soi-même ou admin" on public.profils;
create policy "profils : soi-même ou admin" on public.profils
  for select to authenticated using (id = auth.uid() or public.est_admin());
drop policy if exists "profils : rôles par l'admin" on public.profils;
create policy "profils : rôles par l'admin" on public.profils
  for update to authenticated using (public.est_admin()) with check (public.est_admin());

drop policy if exists "références : lecture" on public.references_clients;
create policy "références : lecture" on public.references_clients
  for select to anon, authenticated using (publie or public.est_equipe());
drop policy if exists "références : ajout" on public.references_clients;
create policy "références : ajout" on public.references_clients
  for insert to authenticated with check (public.est_equipe());
drop policy if exists "références : modification" on public.references_clients;
create policy "références : modification" on public.references_clients
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "références : suppression" on public.references_clients;
create policy "références : suppression" on public.references_clients
  for delete to authenticated using (public.est_admin());

drop policy if exists "prestations : lecture" on public.prestations;
create policy "prestations : lecture" on public.prestations
  for select to anon, authenticated using (publie or public.est_equipe());
drop policy if exists "prestations : ajout" on public.prestations;
create policy "prestations : ajout" on public.prestations
  for insert to authenticated with check (public.est_equipe());
drop policy if exists "prestations : modification" on public.prestations;
create policy "prestations : modification" on public.prestations
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "prestations : suppression" on public.prestations;
create policy "prestations : suppression" on public.prestations
  for delete to authenticated using (public.est_admin());

drop policy if exists "événements : lecture" on public.evenements;
create policy "événements : lecture" on public.evenements
  for select to anon, authenticated using (publie or public.est_equipe());
drop policy if exists "événements : ajout" on public.evenements;
create policy "événements : ajout" on public.evenements
  for insert to authenticated with check (public.est_equipe());
drop policy if exists "événements : modification" on public.evenements;
create policy "événements : modification" on public.evenements
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "événements : suppression" on public.evenements;
create policy "événements : suppression" on public.evenements
  for delete to authenticated using (public.est_admin());

-- Réglages : le site ne lit que ce qui est publié ; l'équipe modifie
drop policy if exists "réglages : lecture" on public.reglages;
create policy "réglages : lecture" on public.reglages
  for select to anon, authenticated using (coalesce((valeur ->> 'publie')::boolean, false) or public.est_equipe());
drop policy if exists "réglages : ajout" on public.reglages;
create policy "réglages : ajout" on public.reglages
  for insert to authenticated with check (public.est_equipe());
drop policy if exists "réglages : modification" on public.reglages;
create policy "réglages : modification" on public.reglages
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "réglages : suppression" on public.reglages;
create policy "réglages : suppression" on public.reglages
  for delete to authenticated using (public.est_admin());

drop policy if exists "équipe : lecture" on public.equipe;
create policy "équipe : lecture" on public.equipe
  for select to anon, authenticated using (publie or public.est_equipe());
drop policy if exists "équipe : ajout" on public.equipe;
create policy "équipe : ajout" on public.equipe
  for insert to authenticated with check (public.est_equipe());
drop policy if exists "équipe : modification" on public.equipe;
create policy "équipe : modification" on public.equipe
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "équipe : suppression" on public.equipe;
create policy "équipe : suppression" on public.equipe
  for delete to authenticated using (public.est_admin());

drop policy if exists "témoignages : lecture" on public.temoignages;
create policy "témoignages : lecture" on public.temoignages
  for select to anon, authenticated using (publie or public.est_equipe());
drop policy if exists "témoignages : ajout" on public.temoignages;
create policy "témoignages : ajout" on public.temoignages
  for insert to authenticated with check (public.est_equipe());
drop policy if exists "témoignages : modification" on public.temoignages;
create policy "témoignages : modification" on public.temoignages
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "témoignages : suppression" on public.temoignages;
create policy "témoignages : suppression" on public.temoignages
  for delete to authenticated using (public.est_admin());

-- Demandes : le site peut seulement en déposer ; l'équipe les lit et les traite
revoke all on public.demandes from anon;
grant insert (nom, societe, tel, metier, sujet, langue, page) on public.demandes to anon, authenticated;
drop policy if exists "demandes : dépôt" on public.demandes;
create policy "demandes : dépôt" on public.demandes
  for insert to anon, authenticated with check (true);
drop policy if exists "demandes : lecture" on public.demandes;
create policy "demandes : lecture" on public.demandes
  for select to authenticated using (public.est_equipe());
drop policy if exists "demandes : traitement" on public.demandes;
create policy "demandes : traitement" on public.demandes
  for update to authenticated using (public.est_equipe()) with check (public.est_equipe());
drop policy if exists "demandes : suppression" on public.demandes;
create policy "demandes : suppression" on public.demandes
  for delete to authenticated using (public.est_admin());

drop policy if exists "journal : admin" on public.journal;
create policy "journal : admin" on public.journal
  for select to authenticated using (public.est_admin());

-- ═══════════════════════════════ Images (stockage) ═══════════════════════════════
-- logos : logos des références ; medias : photos des événements et aperçu de la vidéo ; videos : vidéo de présentation

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('logos', 'logos', true, 1048576, array['image/webp', 'image/png', 'image/jpeg']),
       ('medias', 'medias', true, 5242880, array['image/webp', 'image/png', 'image/jpeg']),
       ('videos', 'videos', true, 52428800, array['video/mp4', 'video/webm'])
on conflict (id) do update set public = true, file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "logos : lecture publique" on storage.objects;
drop policy if exists "logos : ajout par l'équipe" on storage.objects;
drop policy if exists "logos : remplacement par l'équipe" on storage.objects;
drop policy if exists "logos : suppression par l'équipe" on storage.objects;
drop policy if exists "images : lecture publique" on storage.objects;
create policy "images : lecture publique" on storage.objects
  for select using (bucket_id in ('logos', 'medias', 'videos'));
drop policy if exists "images : ajout par l'équipe" on storage.objects;
create policy "images : ajout par l'équipe" on storage.objects
  for insert to authenticated with check (bucket_id in ('logos', 'medias', 'videos') and public.est_equipe());
drop policy if exists "images : remplacement par l'équipe" on storage.objects;
create policy "images : remplacement par l'équipe" on storage.objects
  for update to authenticated using (bucket_id in ('logos', 'medias', 'videos') and public.est_equipe());
drop policy if exists "images : suppression par l'équipe" on storage.objects;
create policy "images : suppression par l'équipe" on storage.objects
  for delete to authenticated using (bucket_id in ('logos', 'medias', 'videos') and public.est_equipe());
