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
  quoi := coalesce(nullif(ligne ->> 'nom', ''), ligne ->> 'titre', ligne ->> 'email');
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
drop trigger if exists journaliser on public.profils;
create trigger journaliser after update of role on public.profils
  for each row execute function public.journaliser();

-- ═══════════════════════════════ Droits d'accès ═══════════════════════════════

alter table public.profils            enable row level security;
alter table public.references_clients enable row level security;
alter table public.prestations        enable row level security;
alter table public.journal            enable row level security;

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

drop policy if exists "journal : admin" on public.journal;
create policy "journal : admin" on public.journal
  for select to authenticated using (public.est_admin());

-- ═══════════════════════════════ Logos (stockage) ═══════════════════════════════

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('logos', 'logos', true, 1048576, array['image/webp', 'image/png', 'image/jpeg'])
on conflict (id) do update set public = true, file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "logos : lecture publique" on storage.objects;
create policy "logos : lecture publique" on storage.objects
  for select using (bucket_id = 'logos');
drop policy if exists "logos : ajout par l'équipe" on storage.objects;
create policy "logos : ajout par l'équipe" on storage.objects
  for insert to authenticated with check (bucket_id = 'logos' and public.est_equipe());
drop policy if exists "logos : remplacement par l'équipe" on storage.objects;
create policy "logos : remplacement par l'équipe" on storage.objects
  for update to authenticated using (bucket_id = 'logos' and public.est_equipe());
drop policy if exists "logos : suppression par l'équipe" on storage.objects;
create policy "logos : suppression par l'équipe" on storage.objects
  for delete to authenticated using (bucket_id = 'logos' and public.est_equipe());
