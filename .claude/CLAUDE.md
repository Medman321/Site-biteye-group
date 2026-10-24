# Consignes Claude — dépôt Site BitEye

## Demandes de vidéo : l'équipe et l'ordre de passage

Toute demande de vidéo, pub, reel, story, spot, clip ou motion design suit la méthode `.claude/skills/biteye-video-ad/SKILL.md`, avec l'équipe ci-dessous. Les agents 9 à 13 ne sont lancés que si le plan d'efficacité (8) les juge utiles.

| # | Agent | Rôle |
|---|---|---|
| 0 | session principale (coordinateur) | orchestration, arbitrages, questions au demandeur, livraison |
| 1 | `scenario-interview-architect` | narration B2B, ordre et liaison des extraits, ponts entre intervenants, voix off |
| 2 | `audio-studio-analyst` | analyse au dixième de seconde, coupes sur les creux, raccords J/L-cut, room tone, lit musical avec ducking, mastering −14 LUFS |
| 3 | `market-strategy-director` | veille, concepts, copywriting VISION Workspace, structure 40 s, légendes Instagram/TikTok/LinkedIn |
| 4 | `art-direction-design-critic` | audit esthétique AVANT le rendu final : transitions, flous, couleurs, lisibilité |
| 5 | `vfx-roto-compositing-engineer` | préparation des vidéos/photos, raccord couleur, détourage 2.5D (animations entre l'intervenant et son fond), masquage d'incrustations, .jsx After Effects optionnel |
| 6 | `motion-video-producer` | storyboard, moteur HTML/Playwright/ffmpeg, rendu MP4 + HTML |
| 7 | `quality-brand-inspector` | contrôle qualité et marque APRÈS rendu, verdict livrable / à reprendre |
| 8 | `token-efficiency-auditor` | responsable de l'efficacité, qui chapeaute tout : plan d'exécution et budget AVANT, bilan mesuré et capitalisation APRÈS ; jamais d'économie sur la qualité |
| 9 | `chief-editor-monteur` | animatic basse définition, rythme, ordre et durée des plans, verdict montage avant tout rendu soigné |
| 10 | `image-restoration-engineer` | débruitage, netteté, agrandissement Real-ESRGAN, artefacts de compression, ralentis (seulement si les sources le demandent) |
| 11 | `colorist` | scopes, raccord couleur entre sources, look et LUT .cube, couleurs d'accent mesurées dans les images |
| 12 | `sound-designer` | habillage sonore calé sur les animations, musique coupée sur les temps, jingle (l'ingénieur du son mixe) |
| 13 | `motion-3d-artist` | 3D Blender (bpy), suivi de mouvement (OpenCV, MediaPipe), parallaxe, 1 ou 2 effets avancés par vidéo |
| 14 | `conseiller-demande` | partenaire de brainstorming du demandeur AVANT la fiche : questions, pistes, contre-propositions, lecture des documents fournis, fiche de demande enrichie remplie toute seule (Drive `00_Demandes/<projet>/`) |
| 15 | `concepteur-transitions` | comment on passe d'une scène à l'autre : coupes cachées des sources, transition choisie selon la relation entre les scènes (grammaire de raccords), fiche `transitions.json` pour 6 et 12, preuve mesurée (rampe ≥ 3 images, visages, luminance, direction, fantôme) avant l'audit DA ; obligatoire en premium |

0. **Brainstormer** (facultatif, à l'initiative du demandeur : « brainstorm : … ») : la session lance 14 et relaie l'échange **mot pour mot** dans les deux sens (même instance reprise par SendMessage) ; elle n'intervient que si une proposition contredit une décision du Journal. Après chaque échange, la fiche brouillon est copiée dans le Drive (`00_Demandes/<projet>/Fiche de demande`). Au « lance » du demandeur, la fiche remplit `brief.json` : le cadrage (1) se réduit à une confirmation et les pistes vont à 3 comme points de départ.
1. **Cadrer** : questions de cadrage (`biteye-video-ad` §0 : diffusion et formats, objectif, cible et langue, style, nom + poste + photo de chaque voix, infos à afficher).
2. **Planifier** : 8 écrit `plan-efficacite.md` (équipe minimale, modèle par tâche, fichiers à réutiliser, parallélisme, rendus d'essai, budget). La session suit ce plan.
3. **Préparer en parallèle** : 2 (son) et 5 (image) sur chaque média ; 10 dès qu'une source est sous la résolution de livraison ou compressée (obligatoire) ; 11 dès qu'il y a plusieurs sources ; 3 fait la veille.
4. **Proposer** : 3 (concepts, en s'appuyant sur `bibliotheque-techniques`, les vidéos de référence du demandeur) puis 1 (scénario minuté du concept choisi). **Attendre le choix du demandeur.**
5. **Pré-rendu** : 9 monte l'animatic et le valide ; 15 repère les coupes cachées et écrit `transitions.json` (relation → transition, paramètres, son) ; 6 construit le storyboard et les images clés en appliquant la fiche, avec les calques de 13 et l'habillage de 12 ; 15 mesure le pré-rendu de contrôle (`transitions/scripts/transition_audit.py cuts`) ; 4 audite (grille « sophistication » en premium) ; 6 corrige (une passe).
6. **Rendre** : 6 rend les MP4 (premium : maître 4K 2160×3840 + version 1080 réduite du maître + version WhatsApp) ; 7 contrôle ; une reprise si « à reprendre ».
7. **Livrer** : la session publie la page en Artifact et envoie les MP4, la légende (3) et le rapport qualité (7).
8. **Bilan** : 8 audite l'efficacité ; la session applique les capitalisations validées.
9. **Apprentissage** : toute nouvelle vidéo du dossier Drive « Vidéos pour apprentissage » est analysée et ses techniques ajoutées à `bibliotheque-techniques` (registre Drive des vidéos analysées).
10. **Veille d'expertise** : la session écrit le retour d'expérience (`.claude/retex/`) puis lance `veille-expertise` (une veille web par agent, fiches mises à jour, pull request). Aussi chaque mois, par la tâche planifiée « Veille d'expertise BitEye ».

**Niveau premium** (choisi au cadrage) : agents 9, 10 (si source faible), 11, 12, 13 et 15 obligatoires ; aucune coupe sèche entre deux plans (transitions de la bibliothèque du moteur : zoomPunch, zoomThrough, maskReveal, whip, matchCut) ; caméra vivante (léger mouvement continu sur chaque plan) ; 3 plans de profondeur (fond, graphisme, personne) ; un seul concept visuel validé sur planche ; écran final animé.

Les agents ne peuvent pas s'appeler entre eux : la session principale les lance, transmet les fichiers et arbitre. Retouches : renvoyer au même agent (SendMessage).

Raccourci : pour une simple retouche ou une déclinaison de format d'une vidéo déjà validée, va directement à l'étape 5 (8 peut sauter le plan).

Si les agents ne sont pas disponibles dans la session (ils se chargent au démarrage), applique toi-même les skills dans le même ordre, ou lance un agent générique en lui demandant de suivre le fichier de l'agent concerné.

## Efficacité (règles permanentes, enrichies par chaque bilan)

- Ne refais jamais ce qui existe dans `$OUT` : transmets les chemins aux agents.
- Briefs compacts : la liste exacte des fichiers à lire et le format du compte rendu.
- Seulement les agents utiles à la demande ; le moins cher des modèles qui tient la qualité.
- Images clés et animatic avant tout rendu complet ; un seul rendu final par format.
- Un script écrit deux fois devient un outil CLI dans un skill.
- Jamais d'économie sur l'audit DA, le contrôle qualité, l'écoute des coupes, les noms et le CTA.
- Porte avant rendu : pas de rendu complet tant que l'alignement personne détourée / fond n'est pas vérifié image par image (écart, crâne non coupé, coupes de la source repérées) ; images clés aux bornes de chaque calque détouré (t−1, t, t+1 image), pas seulement à heures fixes.
- Contrôle croisé plafonné : seulement après la porte et l'audit DA ; 1 contradicteur par constat (3 si bloquant), au plus 20 agents et 1 M de jetons, coût annoncé au demandeur avant. Référence V2 : 9,3 M de jetons pour 18 défauts, contre 0,2 M pour un contrôle qualité unique.
- Goût contradictoire (DA ↔ demandeur) et tout calcul de plus de 20 min (restauration, rendu 4K) : trancher d'abord sur une planche de 3 niveaux de 2 images clés, jamais par un rendu ; un effet « subtil » garde un plancher de visibilité mesuré.
- Transitions : le DA donne ses seuils mesurables avant le pré-rendu (rampe d'au moins 3 images avant chaque coupe) ; 15 les mesure avec `transition_audit.py` sur le pré-rendu de contrôle et sur le rendu final, avant l'audit DA et le contrôle qualité (le contrôle de la V3.2 avait laissé passer des rampes absentes que l'outil a trouvées) ; tout plan source sans image propre est décidé à la planification ; animatic refait après toute passe qui déplace une coupe.
- Mesure : relever le compteur de jetons d'une instance avant chaque reprise ; une attente de rendu se fait en tâche de fond, pas dans une instance reprise.
- Détourage : un seul lot, plages fixées par le storyboard, calculé sur la grille d'images de la plaque finale et pleine hauteur ; retirer du storyboard toute version remplacée.
- Cadrage : demander d'emblée si un nom de produit ou de marque cité dans une source (ex. « Vision Pro ») peut rester, avant toute coupe audio.

## Contexte de la session (plafond ≈ 40 %)

- État de travail tenu à jour dans `.claude/state/etat-en-cours.md` (hors Git) à chaque étape ; réinjecté automatiquement après un compactage (hook `SessionStart` « compact »). Il fait foi après un compactage.
- Lectures lourdes déléguées à des sous-agents (comptes rendus ≤ 15 lignes) ; dans la session, seulement des extraits.
- En fin d'étape : mettre l'état à jour, puis proposer au demandeur `/compact garde l'état en cours, les décisions et les chemins`.

## Google Drive « BitEye — Studio vidéo »

La session a l'autonomie complète sur ce dossier (créer, renommer, déplacer, mettre à la corbeille) ; elle garde la hiérarchie :

- racine : `LISEZ-MOI`, `Suivi des demandes vidéo` (tableur), `Journal des décisions` ;
- `00_Demandes/AAAA-MM_Type_Sujet/` : entrées du demandeur, `01_Vidéos`, `02_Photos`, `03_Mémos-audio`, `04_Documents`, plus `Fiche de demande` et `Notes de brainstorming` ;
- `01_Productions/<même nom>/V1, V2…` : sorties par version (vidéos déposées par le demandeur, rapport qualité, légendes, bilan) ;
- `02_Bibliothèque/` : `Vidéos pour apprentissage` (+ registre), `Charte et logos`, `Musiques et sons` ;
- `99_Archives/` : projets clos ou versions remplacées (on archive avant de mettre à la corbeille).

Le connecteur ne dépose pas de vidéo et n'édite pas un document existant : on recrée le document, puis on met l'ancien à la corbeille.

## GitHub (dépôt public)

- **Contrôle automatique** : toute modification de `.claude/skills/**` dans une pull request déclenche « Vidéo · contrôle du moteur » (reconstruit les exemples, planches et MP4 court en artefacts). Ne fusionne pas une PR dont ce contrôle est rouge.
- **Rendu dans le cloud** : « Vidéo · rendu » (Actions → Run workflow) rend un projet (dossier avec `storyboard.json` et `storyboard-*.json`), passe la voix au studio, joint MP4 + HTML + planches au run et, sur demande, crée une Release téléchargeable. Les médias arrivent par `archive_url` (lien .zip), jamais par un commit.
- **Demandes par issue** : modèle « Demande de vidéo » (questions de cadrage). Avec « @claude » dans l'issue et le secret configuré (`.github/workflows/claude.yml`), Claude traite la demande dans GitHub en suivant ces consignes ; sinon, traite l'issue depuis une session.
- **Public** : issues, artefacts, Releases et fichiers du dépôt sont visibles par tous. Pour des médias ou des vidéos confidentiels, utilise le scratchpad de la session ou un dépôt privé dédié.

## Outils

Gratuits et locaux par défaut (`bash .claude/skills/biteye-video-ad/scripts/setup_free_tools.sh`). ElevenLabs et tout service payant seulement si le demandeur le veut, coût annoncé avant.

## Site

Le site (`index.html`, `favicon.svg`, `CNAME`) est publié par GitHub Pages sur biteye-group.com. N'y ajoute ni vidéos ni médias de clients ; les dossiers commençant par un point (`.claude/`, `.video-out/`) ne sont pas publiés.
