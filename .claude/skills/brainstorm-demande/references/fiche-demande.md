# Gabarit de la fiche de demande enrichie

Le brouillon vit dans `$OUT/fiche-demande.md` dès le premier échange ; la session le copie dans le Drive (« Fiche de demande » du dossier `00_Demandes / AAAA-MM_Type_Sujet/`). Rien de confidentiel ne va dans le dépôt.

Statuts possibles par champ : **réglé** (réponse du demandeur ou d'un document), **hypothèse** (proposée par le conseiller, avec sa raison), **à confirmer** (sans réponse, ou fait à vérifier : chiffre de plateforme, juridique).

```markdown
# Fiche de demande — <titre de travail>
Version <n> · <date> · statut : brouillon | finale · validée par : <nom>
Dossier Drive : BitEye — Studio vidéo / 00_Demandes / <AAAA-MM_Type_Sujet>/
Sorties : BitEye — Studio vidéo / 01_Productions / <AAAA-MM_Type_Sujet> / V1…

## En une phrase (30 s)
<quoi, pour qui, pour quoi faire, où, pour quand>

## Cadrage (biteye-video-ad §0)
| Champ | Réponse | Source | Statut |
|---|---|---|---|
| Diffusion et formats | … | demandeur / document / hypothèse | réglé / hypothèse / à confirmer |
| Objectif + mesure | … | | |
| Vidéo de marque ou de démo | … | | |
| Cible principale (et cible exclue) · rôle dans la décision | … | | |
| Langue (voix · sous-titres · cartons) | … | | |
| Style · références aimées / rejetées (et pourquoi) | … | | |
| Identité visuelle | … | | |
| Niveau de finition | … | | |
| Durée maximale | … | | |
| Voix (nom · poste · photo · accord) | … | | |
| Médias disponibles (originaux ?) | … | | |
| Noms de marque cités dans les sources | … | | |
| Infos à afficher autorisées | … | | |
| CTA | … | | |
| Échéance · validation | … | | |

## Stratégie
- Moment déclencheur : …
- Insight (1re personne) : « … »
- Proposition unique (une phrase, sans « et ») : …
- Raisons d'y croire (sourcées) : …
- Frein principal et réponse : …
- Réaction attendue — pense : … · ressent : … · fait : …
- Mots exacts des clients : « … »

## Pistes pour le stratège (points de départ, pas des concepts)
| # | Piste | Technique | Trame (PAS / AIDA / Avant-Après-Pont) | Verdict grille | Pourquoi |
|---|---|---|---|---|---|
Pistes écartées : … (raison)

## Contraintes et obligatoires
Marque · juridique (à confirmer) · client · confidentialité · plateforme

## Hypothèses et points à confirmer
- Hypothèse : … (raison) — à confirmer par …

## Risques signalés au demandeur
- … (décision du demandeur : …)

## Questions laissées au stratège
- …

## Journal de séance
- <date> · décision : … · par : demandeur / conseiller
```

## Correspondance avec `$OUT/brief.json`

À la passation, la session remplit `brief.json` (`biteye-video-ad` §0) depuis le tableau « Cadrage ». Clés alignées sur les `brief.json` des productions précédentes (ajouter une clé plutôt que d'en renommer une) :

| Champ de la fiche | Clé de `brief.json` |
|---|---|
| Diffusion et formats | `sorties` (liste : plateforme + format) |
| Objectif + mesure | `objectif`, `mesure` |
| Vidéo de marque ou de démo | `nature` |
| Cible principale · cible exclue | `cible`, `cible_exclue` |
| Langue | `langue` (`voix`, `sous_titres`, `cartons`) |
| Contraintes et obligatoires | `contraintes` |
| Style · références | `style`, `references` |
| Identité visuelle | `palette` |
| Niveau de finition | `finition` (`standard` / `premium`) |
| Durée maximale | `duree_s` |
| Voix | `temoins` (liste : `nom`, `poste`, `photo`) et `accord_temoins` |
| Médias disponibles | `medias` (chemins Drive) |
| Noms de marque cités | `noms_sources` |
| Infos à afficher | `infos` |
| CTA | `cta` |
| Échéance · validation | `echeance`, `validation` |
| Proposition unique, insight, moment, frein, preuves | `strategie` (objet) |
| Pistes retenues | `pistes` (pour le stratège, points de départ) |
| Champs « à confirmer » | `a_confirmer` (liste des clés concernées) |

La session ne repose ensuite que les questions listées dans `a_confirmer`.
