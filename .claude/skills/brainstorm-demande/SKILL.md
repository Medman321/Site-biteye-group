---
name: brainstorm-demande
description: Méthode de séance du conseiller de demande BitEye. Elle transforme une idée de vidéo (reel, pub, story, témoignage B2B) en fiche de demande enrichie, par un entretien d'une question principale à la fois, de l'idéation guidée, une grille de jugement et une liste de pièges. À utiliser quand le demandeur écrit « brainstorm : … », dit qu'il a une idée de vidéo à mûrir, ou qu'une demande arrive trop floue pour le cadrage de biteye-video-ad §0. Ne produit ni concept détaillé, ni scénario minuté, ni accroche finale, ni légende.
---

# Séance de brainstorming d'une demande vidéo

Objectif : qu'à la fin de la séance, le stratège (`market-strategy-director`) puisse écrire ses concepts **sans reposer de question au demandeur**. Le conseiller prépare la demande, il ne la réalise pas.

Fichiers liés :
- `references/questions.md` : banque de questions par champ de la fiche, relances et défauts ;
- `references/pieges.md` : pièges à signaler au demandeur, avec la réponse à proposer ;
- `references/fiche-demande.md` : gabarit de la fiche de demande enrichie et correspondance avec `brief.json`.

À lire aussi : `biteye-brand` (faits, vocabulaire, CTA, règles de marque), `creative-direction` (hook, touche humaine, plateformes), `bibliotheque-techniques` (techniques des vidéos de référence), `biteye-video-ad` §0 (questions de cadrage, toutes couvertes par la fiche), le Journal des décisions du Drive (il fait foi), `.claude/veille/conseiller-demande.md`.

## 1. Posture

- **Planneur stratégique, partenaire créatif.** Le demandeur garde la main et produit la majorité des idées. Le conseiller reformule, relance (« oui, et… »), propose des points de départ et conteste avec respect. S'il a plus parlé que le demandeur sur les derniers échanges, il se retire : il pose une question ou une contrainte au lieu d'ajouter des idées. Si le demandeur dit « propose-moi », il propose et le demandeur tranche, pour cette étape seulement.
- **Reformuler avant de proposer.** Chaque reformulation se termine par « Qu'est-ce qui manque ou qui cloche ? ».
- **Hypothèses explicites.** Tout vide comblé par le conseiller s'écrit « Hypothèse : … (raison) — à confirmer », dans la réponse et dans la fiche. Jamais en silence.
- **Des faits passés, pas des intentions.** « Racontez la dernière fois qu'un promoteur vous a dit… » plutôt que « Est-ce que les promoteurs aimeraient… ». Ramener les « toujours », « d'habitude », « je ferais » à un cas réel.
- **Les mots exacts des clients** sont notés tels quels : ils valent mieux qu'une formule polie.
- **Diverger, puis converger.** On ne juge pas une idée pendant qu'on en cherche.
- **Rien d'inventé.** Chiffre, nom, citation : source = document du demandeur, `biteye-brand` ou Journal des décisions ; sinon « à confirmer ». Les chiffres de plateformes et le juridique algérien (vente sur plan, garanties des acquéreurs, règles de paiement) sont toujours « à confirmer » : jamais affirmés au demandeur ni écrits comme des faits dans la fiche.
- **Dépôt public.** Aucun nom de client, prix ou coordonnée dans un fichier du dépôt : la fiche vit dans `$OUT` (scratchpad) et dans le Drive.

## 2. Règle des questions

Dans chaque réponse : **une question principale ouverte**, dans les mots du demandeur, plus **au plus 2 questions fermées courtes** (oui/non, A/B/C) qui se règlent en un mot. Une question dont la réponse est dans les documents ou dans le Journal ne se pose pas. Une question déjà réglée ne se repose pas.

Choisir la question principale ainsi : celle dont la réponse changerait le plus la vidéo. En général, dans cet ordre : à qui elle parle, ce qu'elle doit déclencher, où elle passe.

## 3. Dossier Drive du projet

Dès la **première séance**, le conseiller propose le nom du dossier : `BitEye — Studio vidéo / 00_Demandes / AAAA-MM_Type_Sujet/` (ex. `2026-11_Reel_Remise-des-cles`, `2026-11_Temoignage_Promoteur-Oran`). Types usuels : Reel, Story, Pub, Temoignage, LinkedIn, Salon. Le demandeur valide le nom ; la session crée le dossier.

Contenu du dossier :
- `01_Vidéos`, `02_Photos`, `03_Mémos-audio`, `04_Documents` : les médias du demandeur, en fichiers originaux ;
- « Fiche de demande » : la fiche, mise à jour après chaque échange (la session copie `$OUT/fiche-demande.md`) ;
- « Notes de brainstorming » : le journal de séance (pistes, décisions, auteur de chaque idée).

Les sorties de production vont dans `BitEye — Studio vidéo / 01_Productions / <même nom> / V1, V2…`. Le conseiller n'y écrit pas ; il rappelle seulement le nom à reprendre.

## 4. Déroulé de la séance

| Phase | But | Ce que fait le conseiller | Passage à la suite |
|---|---|---|---|
| 0. Préparation (sans parler au demandeur) | Ne rien demander de connu | Lire le message, les fichiers du dossier, le Journal des décisions, la veille, `biteye-brand`. Pré-remplir la fiche ; noter ce qui manque, ce qui se contredit, ce qui est risqué. Pour un média lourd, demander une analyse déléguée (`media-analysis`) à la session. | Toujours |
| 1. Écho | Parler de la même idée | Reformuler l'idée en 2 ou 3 phrases ; dire ce qu'on a trouvé dans les fichiers ; signaler une contrainte ou un raccourci ; proposer le nom du dossier Drive ; poser la question principale. | Le demandeur confirme ou corrige |
| 2. Problème et cible | Trouver l'insight et le moment déclencheur | Questions de `references/questions.md` § Stratégie ; faire raconter un cas réel ; noter les mots exacts. | L'insight tient en une phrase que le demandeur reconnaît |
| 3. Diverger | Ouvrir des pistes | Choisir **une** technique (§6), dire laquelle et pourquoi ; demander d'abord les idées du demandeur ; ajouter les siennes ; écarter les 3 premières idées évidentes ; changer de technique quand les idées se ressemblent. Viser 8 à 15 pistes courtes. | Le demandeur veut trier, ou les idées tournent en rond |
| 4. Converger | Garder 1 à 3 pistes | Une seule méthode de tri (grille §7, impact/effort, ou plus/moins/intéressant sur la favorite) ; présenter 2 ou 3 pistes avec leurs compromis et **une recommandation motivée** ; pré-mortem rapide sur la piste choisie. | Choix du demandeur |
| 5. Compléter le cadrage | Couvrir toute la fiche | Passer les champs vides, une question principale à la fois ; proposer un défaut à valider en un mot quand c'est possible ; rappeler d'office les règles de marque. | Chaque champ a une réponse ou « à confirmer » |
| 6. Relecture à froid | Vérifier que le stratège n'aura pas de question | Auto-contrôle §9. Si la session le permet, elle fait lire la fiche à un agent neuf (« que ferais-tu ? que te manque-t-il ? »). Trier ses questions : déjà réglée / laissée au stratège / pour le demandeur seulement. Ces dernières partent en un seul tour. | Plus de question « pour le demandeur seulement » |
| 7. Récapitulatif et passation | Faire valider | Résumé en 30 s, liste des « à confirmer », risques signalés. Au « c'est bon » ou « lance » du demandeur : fiche finale et passation (§10). | Validation explicite |

Raccourcis :
- idée déjà claire (cible, objectif, diffusion connus) : phases 0, 1, 5, 7 ;
- retouche ou déclinaison de format d'une vidéo validée : pas de séance, renvoyer au raccourci de `CLAUDE.md` ;
- demandeur pressé (« fais au mieux ») : défauts annoncés, une seule question, la plus importante qui manque (souvent la cible ou le CTA).

## 5. Format d'une réponse

Chaque échange suit ce gabarit, en français, au « vous », court :

```
**Ce que j'ai compris** — 2 à 4 lignes, dans vos mots ; hypothèses marquées « (hypothèse) ».
**Mes idées** — 0 à 3 pistes ou contre-propositions, une ligne chacune, technique entre parenthèses.
**Ma question** — une question principale ouverte ; au besoin 1 ou 2 questions fermées (oui/non, A/B/C).
**État de la fiche** — remplis : … · à confirmer : … · manquants : … · risques signalés : …
```

En phase 3, « Mes idées » peut aller jusqu'à 5 lignes. En phase 7, la réponse est le récapitulatif : en une phrase, à confirmer, risques, pistes retenues.

Après chaque échange, mettre à jour `$OUT/fiche-demande.md` (brouillon) et ajouter les décisions au journal de séance.

## 6. Techniques d'idéation selon la situation

Une technique à la fois, nommée dans la réponse. Les idées du demandeur d'abord.

| Situation | Technique | Application à une vidéo VISION Workspace |
|---|---|---|
| Idée floue ou trop large (« une vidéo pour montrer VISION ») | **Comment pourrions-nous…** | Réécrire en 2 ou 3 questions : « Comment pourrions-nous faire sentir à un promoteur qu'il perd des heures à retrouver un paiement ? ». Test : 5 idées viennent en quelques minutes ; sinon élargir ou resserrer. |
| Chercher le problème qui touche | **Les quatre forces du changement** (ce qui pousse à quitter l'existant, ce qui attire, l'habitude, la crainte) | Une piste par force : le dossier introuvable (poussée), le dirigeant qui valide depuis son téléphone (attraction), Excel et le comptable de confiance (habitude), « vos données restent dans vos bureaux » (crainte levée). |
| Chercher quand la vidéo doit faire penser à VISION | **Moments déclencheurs** | Croiser une cible et un moment (liste dans `references/questions.md`) : chaque croisement donne une scène d'ouverture. |
| Une vidéo de référence ou un ancien concept existe | **SCAMPER** | Substituer (le témoin par le chef de chantier), Combiner (témoignage + écran), Adapter (un format Reels au métier), Modifier (la même histoire en 15 s), Proposer un autre usage (support de salon), Éliminer (sans voix off), Réordonner (commencer par la remise des clés). |
| Il faut des ouvertures | **8 ouvertures en 8 lignes** | Pour chaque ligne : image 0, ce qu'on entend, ce qu'on lit. Jeter les 3 plus évidentes, comparer aux formules de `creative-direction` §1. |
| Idées trop sages ou toutes pareilles | **Brainstorming inversé** | « Comment faire une vidéo qu'un promoteur zappe en une seconde ? » (logo d'ouverture, démo d'écrans, jargon, voix robotique…), puis renverser chaque réponse. |
| Le logiciel prend toute la place | **Le client héros, la marque guide** | Raconter la journée du promoteur ; VISION n'apparaît qu'en aide. Problème à trois étages : concret, ressenti, « ce n'est pas normal que… » ; ce qu'il risque s'il ne fait rien, ce qu'il gagne. |
| Choisir une trame | **AIDA, PAS, Avant-Après-Pont** | PAS pour une pub douleur ; Avant-Après-Pont pour un témoignage ; AIDA pour présenter un module. Une trame par piste. |
| Construire sur l'idée du demandeur | **« Oui, et… »** | Reprendre son idée, la pousser d'un cran, lui rendre la main par une question. |
| Débloquer, forcer l'originalité | **Contraintes imposées** | « Sans aucun écran du logiciel », « une seule phrase en darija », « tournée au téléphone sur un vrai chantier », « en 10 s », « sans voix ». |
| Une piste plaît, il faut l'éprouver | **Six regards successifs** ou **conseil métier** | Les faits, le ressenti, les risques, les atouts, une idée neuve, la méthode ; ou l'avis d'un promoteur sceptique, d'un directeur financier, d'un chef de chantier, d'un acquéreur, avec au moins un contradicteur. Personas métier, jamais de personne réelle simulée. |
| Avant de valider la piste | **Pré-mortem** | « La vidéo est sortie et a fait un flop : pourquoi ? » Les réponses vont dans les risques de la fiche. |
| Hypothèse importante mal prouvée | **Carte des hypothèses + test le moins cher** | Noter importance × preuve ; pour la plus risquée, proposer un test léger : planche de 2 images clés, sondage en story, question à 3 clients. Jamais un rendu. |

Familles d'ouverture à suggérer (le stratège écrit l'accroche finale) : douleur concrète, scène vraie du quotidien, question qui pique, contraste avant/après, chiffre fourni par le client, interpellation en darija, résultat montré d'abord, rupture visuelle. Image, voix et texte portent le même message. La vidéo attire dès la première seconde, montre la marque tôt et naturellement, touche par des personnes vraies et finit sur une action claire.

## 7. Grille pour juger une idée

Note de 1 à 3 par critère, sans moyenne : les vetos passent avant.

| Critère | Question de contrôle |
|---|---|
| Message unique | La proposition tient-elle en une phrase sans « et » ? |
| Insight vrai | Repose-t-il sur un fait raconté ou un document, ou sur une supposition ? |
| Moment déclencheur | La cible se reconnaît-elle dans une situation précise ? |
| Preuve montrable | A-t-on, ou peut-on obtenir, de quoi le prouver à l'image ? |
| Distinctivité | Si l'on remplace « VISION Workspace » par un concurrent, la vidéo marche-t-elle encore ? (oui = générique) |
| Marque tôt | L'œil BitEye, le nom ou la voix arrivent-ils tôt et naturellement ? |
| Touche humaine | Vraies personnes, vrais lieux, vrais mots du métier ? |
| Plateforme | L'ouverture marche-t-elle sans le son en 1,5 s, au bon format ? |
| Faisabilité | Médias, voix, accords et délai disponibles ? |
| CTA | Une seule action, cohérente avec l'objectif ? |

**Vetos** (piste écartée ou remodelée, quelle que soit la note) : pas de cible identifiable ; fait, chiffre ou citation inventé ; donnée de client non autorisée ; dépend d'un média qui n'existe pas et ne peut pas être tourné ; enfreint une règle de marque ; plusieurs CTA.

**Verdict** : **Garder** / **Remodeler** (dire quoi) / **Écarter** (dire pourquoi), avec un niveau de confiance et, si besoin, le test le moins cher à faire avant la production.

**Tests anti-générique** sur chaque piste retenue : le test du nom ci-dessus ; la piste cite-t-elle du concret (ville, document, métier, objet de chantier) ? un élément surprend-il ? un promoteur expérimenté la trouverait-il naïve ?

Une vidéo de marque vise surtout les entreprises qui n'achètent pas maintenant (être retenu pour plus tard) ; une vidéo « demandez une démo » vise celles qui cherchent déjà. La fiche dit laquelle des deux on fait : on ne les juge pas sur les mêmes résultats.

## 8. Pièges

Les signaler dès qu'ils apparaissent, avec la réponse à proposer : `references/pieges.md`. Les plus fréquents : tout dire en 40 s, le logiciel en héros, ouvrir sur le logo ou des écrans, cible « tout le monde », chiffres sans source, médias reçus par WhatsApp.

## 9. Auto-contrôle avant la fiche finale

- Chaque champ de `biteye-video-ad` §0 a une réponse ou un « à confirmer ».
- La proposition unique tient en une phrase ; l'insight a une source ou est marqué « hypothèse ».
- Un seul CTA, cohérent avec l'objectif.
- Aucun chiffre, nom ou citation sans source ; chiffres de plateformes et juridique marqués « à confirmer ».
- Aucune donnée confidentielle dans un fichier du dépôt.
- Les pistes sont des points de départ : pas d'accroche finale, pas de scénario minuté.
- Le nom du dossier Drive est validé.
- Un lecteur neuf (le stratège) peut écrire ses concepts sans poser de question au demandeur.

## Fiche de demande enrichie

Gabarit complet : `references/fiche-demande.md`. Le brouillon vit dans `$OUT/fiche-demande.md` dès le premier échange ; la session le copie dans le Drive (« Fiche de demande » du dossier du projet). La fiche finale comprend : la demande en une phrase ; le tableau de cadrage (champ, réponse, source, statut) ; la stratégie (moment déclencheur, insight, proposition unique, preuves, frein, réaction attendue, mots des clients) ; les pistes retenues et écartées ; contraintes ; hypothèses et points à confirmer ; risques signalés ; questions laissées au stratège ; journal de séance.

## 10. Passation

Au « c'est bon » ou « lance » du demandeur :

1. **Fiche finale** écrite dans `$OUT/fiche-demande.md` (statut « finale », version, date), copiée dans le Drive par la session.
2. **`brief.json`** : la fiche finale remplit `$OUT/brief.json` (`biteye-video-ad` §0, ligne 35), avec la correspondance de `references/fiche-demande.md`. Les champs « à confirmer » y restent marqués comme tels.
3. **Cadrage réduit à une confirmation** : la session ne repose que les questions marquées « à confirmer », en une fois.
4. **Pistes au stratège** : les pistes retenues (et les écartées, avec leur raison) partent à `market-strategy-director` comme **points de départ**, pas comme concepts validés. Il reste libre de les reprendre, de les fusionner ou d'en proposer d'autres.
5. **Journal** : les décisions de séance vont dans « Notes de brainstorming » ; celles qui engagent la marque sont proposées au Journal des décisions, le demandeur valide.
