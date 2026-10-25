---
name: bibliotheque-techniques
description: Bibliothèque des techniques de montage et de publicité tirées des vidéos de référence choisies par BitEye (dossier Drive « Vidéos pour apprentissage ») — accroches, rythme, transitions, présentation du produit, texte à l'écran, son, CTA — chacune avec sa transposition à VISION Workspace. À lire au moment du concept et du storyboard ; à enrichir à chaque nouvelle vidéo de référence.
---

# Bibliothèque des techniques (vidéos de référence du demandeur)

Le demandeur dépose dans Google Drive (`BitEye — Studio vidéo / 02_Bibliothèque / Vidéos pour apprentissage`) des pubs qui lui plaisent. Chacune est analysée (structure, rythme, transitions, présentation du produit, texte, son, publicité) puis ses techniques transposables sont ajoutées ici. Aucune vidéo ni capture n'entre dans ce dépôt public : seulement la description des techniques.

## Procédure d'analyse (à chaque nouvelle vidéo)

1. Registre Drive « Registre des vidéos analysées » : ne traiter que les nouvelles. Fichier ≤ 10 Mo (limite du connecteur) ; au-delà, demander l'envoi direct dans la session.
2. Un agent par lot de vidéos (`sonnet`) : `scdet`, planches de scènes, `silencedetect`, `ebur128`, lecture des images ; analyse en 8 points (fiche, structure et rythme, montage, présentation du produit, texte, son, publicité, transposition BitEye).
3. **Squelette du script** (9e point, gratuit et local) :
   - Source : le fichier déposé par le demandeur, jamais un téléchargement depuis un lien (instagram.com, tiktok.com, youtube.com sont bloqués ici : on ne contourne rien, pas de yt-dlp).
   - Voix : `python3 .claude/skills/audio-studio/scripts/transcribe_local.py VIDEO --out $SCRATCH/ref --asr --lang auto` (VAD automatique sous la musique). La sortie donne `first_word` et `words_per_s` ; avec musique, le premier mot se lit là, pas dans `silencedetect`.
   - Texte à l'écran (le hook est souvent écrit, pas dit) : planche de 0 à 3 s à 10 images/s, `ffmpeg -i VIDEO -t 3 -vf "fps=10,scale=180:-2,tile=6x5" -frames:v 1 $SCRATCH/ref/hook_0-3s.jpg` (une image, 30 vignettes à 0,1 s).
   - Relève les instants du hook, du problème, de la bascule, de la preuve et du CTA, croisés avec les coupes `scdet`, puis la catégorie et le mécanisme du hook (Banque de hooks ci-dessous). Une ligne : « hook 0–1,8 s (écrit, curiosité) | problème 1,8–6 | bascule 6,5 | preuve 7–15 (1 chiffre) | CTA 15–18 (WhatsApp) | 1er mot 0,3 s, 2,7 mots/s ».
   - Darija : la transcription n'est qu'approchée ; classe le hook après écoute ou texte corrigé (`--text`). Vidéo sans voix : champs « n/a », le squelette vient des textes à l'écran.
   - Droits : la transcription complète d'un tiers reste dans le scratchpad ou le Drive privé (ni dépôt, ni issue, ni artefact, ni Release). Ici n'entrent que le squelette chiffré et la technique reformulée : paraphrase, ou citation de 3 mots au plus.
4. La session ajoute ici les techniques nouvelles (une ligne : technique — où on l'a vue — comment l'utiliser chez BitEye — à éviter) et met à jour les fiches concernées ; dans « Vidéos analysées », la colonne « Apports » cite la catégorie du hook et la structure ; registre Drive mis à jour ; pull request.

## Usage : proposer au cas par cas

Décision du demandeur (24/10/2026) : cette bibliothèque élargit la gamme de montage de l'équipe. Elle ne s'applique pas d'office : à chaque vidéo, le stratège (3) et le chef monteur (9) choisissent 1 à 3 techniques qui servent le message et **les proposent au demandeur** dans le concept (« technique — où on l'a vue — ce qu'elle apporte ici »). Les vidéos BitEye parlent du logiciel VISION Workspace : aucune technique n'impose de filmer le projet d'un client.

## Génération IA (option A) — autorisée par le demandeur, au cas par cas

**Photos et vidéos de clients** (décision du 24/10/2026) : l'IA ne sert qu'à la restauration (netteté, agrandissement, débruitage, artefacts : `image-restoration-engineer`). Elle ne crée jamais de contenu : rien d'ajouté, rien d'inventé, aucun mouvement fabriqué. L'option A ci-dessous ne s'applique qu'aux visuels propres à BitEye (maquettes, décors abstraits).

Méthode « construction en gravité inversée » (vidéo de référence analysée le 24/10/2026, prompts complets dans le Drive : « Rapport — Construction par IA ») :
1. Une image finale RÉELLE (photo, perspective officielle ou, pour le logiciel, une maquette d'écran dessinée « Données fictives ») verrouille le résultat.
2. Trois stades intermédiaires générés depuis cette image (≈ 25 %, 55 %, 85 %), chacun avec la référence réelle + les précédents « pour la continuité seulement », et une longue liste de négations (« même point de vue, même cadrage 9:16, rien qui n'existe pas sur la référence, pas d'étages en plus, pas de texte ni de logo »).
3. Storyboard de 4 images dans l'ordre (3 stades + la référence).
4. Un seul prompt vidéo de 8 à 10 s minuté par tranches de 2 s (un mouvement de caméra par tranche), avec la consigne « la dernière image = la référence exactement ».
5. Montage : le clip tel quel + habillage du moteur ; creux sonore d'une demi-seconde puis impact au moment où tout se pose.
Modèle de prompt d'image (à adapter) : « USE THE UPLOADED REFERENCE AS THE ABSOLUTE FINAL STATE. CREATE AN EARLIER STAGE, APPROXIMATELY X % ASSEMBLED. PRESERVE THE EXACT SAME FRAMING (9:16), CAMERA ANGLE, LIGHTING AND SURROUNDINGS. ELEMENTS ARE FLYING UPWARD TOWARD THEIR EXACT FINAL POSITIONS. EVERY GENERATED COMPONENT MUST EXIST IN THE REFERENCE. DO NOT REDESIGN, DO NOT ADD ANYTHING NOT VISIBLE IN THE REFERENCE. NO TEXT, NO LOGOS, NO WATERMARK. »
Idées pour le logiciel : un tableau de bord VISION Workspace (maquette dessinée) qui « s'assemble » pièce par pièce ; les modules qui se posent comme des étages ; un chantier abstrait (pas celui d'un client) qui se construit pendant que le suivi s'affiche.
**Garde-fous obligatoires** : proposition au demandeur avec coût annoncé avant (outils payants : générateur d'images à référence type Gemini « Nano Banana » ou GPT-image, générateur vidéo à images clés type Kling, Seedance ou Veo — tarifs et droits d'usage commercial vérifiés au moment du projet) ; dernier plan toujours réel ou maquette officielle ; aucune vraie interface du logiciel ; aucun chiffre, prix ou délai tiré d'une image générée ; mention « animation d'illustration » et étiquette IA de la plateforme ; aucun média confidentiel envoyé à un service externe sans vérification de ses conditions ; contrôle image par image contre la référence ; jamais de « look IA générique » (déformations visibles = refus).
Sans IA (option B, gratuite, dans notre moteur) : référence découpée en calques qui montent et se posent avec inertie, poussière en particules discrètes, flou de mouvement ; frise avant → après avec images réelles recalées.

## Techniques retenues

### Accroche
- **Question-accusation ou paradoxe dès l'image 0**, sans logo ni intro (« Vous n'avez toujours pas de stratégie ? », « Une pub ne commence pas par une pub ») — Spira (2 pubs, oct. 2026). Chez BitEye : « Vous suivez encore vos acquéreurs sur Excel ? », « Un promoteur ne vend pas des logements. Il vend des échéances tenues. » Texte en apparition mot à mot (flou → net) + léger coup de grave à 0,08 s.

### Rythme et montage
- **Peu de coupes, relancées par un punch-in** (recadrage +10 à 15 % sur une coupe tombant dans un creux de voix, la phrase repart ≈ 0,1 s après) — Spira. Chez BitEye : témoignages et face caméra ; c'est la version « coupe » de notre `zoomPunch`. Le rythme vient du texte : une idée toutes les 1 à 3 s.
- **Liste qui s'empile** (un élément par seconde, mots-clés en couleur d'accent) — Spira. Chez BitEye : modules (Estate, Build, Co-Owner…) ou douleurs du promoteur.

### Texte à l'écran
- **Pastilles « verre dépoli »** (fond translucide flouté) pour les textes incrustés, une seule couleur d'accent, texte sur le buste jamais sur le visage, entrée floue → nette, sortie en fondu — Spira.
- **« X ≠ Y »** (« Publier ≠ stratégie ») — Spira. Chez BitEye : « Un tableur ≠ un suivi », « Encaisser ≠ maîtriser sa trésorerie ».
- **Compteur animé** (0 % → valeur) — Spira. Chez BitEye : seulement avec un chiffre réel et sourcé (banque de données de `biteye-brand`).

### Présentation du produit et personnage
- **Un personnage qui porte la marque** et une **métaphore filée du métier** (médecin : diagnostic, fondations) — Spira. Chez BitEye : métaphore du chantier (fondations, plan, réception des travaux) ; personnage crédible pour des promoteurs (pas d'humour sur l'âge).

### Preuve et CTA
- **Preuve chiffrée + liste concrète, puis CTA à mot-clé** (« Écrivez DIAGNOSTIC ») — Spira. Chez BitEye : CTA WhatsApp (« Écrivez DÉMO au 0560 06 36 41 »), plus courant en Algérie que le commentaire.
- **À éviter** : CTA minuscule affiché 2 s (Spira « Mamie ») ; chiffres sans source ; durée > 35 s pour un Reel.

### Visites immobilières (Windermere, Lake Nona, Sunridge — oct. 2026), classées par impact

Format : technique — où vue (W = Windermere, L = Lake Nona, S = Sunridge, temps en s) — comment l'utiliser chez BitEye — à éviter.

1. **Hook de ≤ 1,5 s : mouvement vers la caméra + texte géant qui s'écrit dès 0,3 s + une personne** — Windermere 0–5 s (« THIS HOUSE » 0,27 s), Lake Nona 0–4,7 (« This is what $10M… », chiffre à 1,8 s), Sunridge 0–7,9 (« if you LOVE », 0,2 s) — intervenant qui marche vers l'écran, promesse en 3 mots, un chiffre ou une condition ; 1 seule idée par hook — à éviter : intro de logo, fond fixe, phrase de plus de 8 mots.
2. **Promesse = curiosité ou chiffre, jamais un titre neutre** — « this house is calling… gotcha » (W 0–5), « $10M just under buys you » (L 1,8–4,5), « 600K 👀 » en carte (S 2,2–4,2) — « 0 retard sur 3 chantiers » ou « 12 lots vendus en 3 semaines » (chiffres client confirmés) — à éviter : prix inventé, boucle ouverte jamais refermée.
3. **Transition par flou directionnel (whip) calée sur un mouvement de caméra, 3–6 images** — W 10,48 / 16,8 / 25,65 / 28,3 / 42,4, L 4,6–4,8 / 8,6 / 24,6, S 7,8 / 24,9 / 45,3 — raccorder deux maquettes ou une personne et un écran par un pan rapide dans le même sens (blur 0,1–0,2 s) ; remplace les fondus — à éviter : whip sans mouvement porteur, flou sur du texte lisible, plus de 6 whips en 20 s.
4. **Accélération puis relâchement du rythme** — S : 2,5 → 2,0 → 0,8 → 3 s/plan (43–52 s : 1 plan par temps), W : 0,5–0,9 s au début puis 3–6 s, L : plans longs parlés 5–11 s puis 0,4 s — storyboard BitEye en 4 temps : intro 2,5 s/plan, développement 2 s, rafale de 6–8 s à 1 temps/plan (les modules), final posé 3 s — à éviter : rythme constant, rafale de plus de 9 s, rafale sans lien avec la musique.
5. **Coupes sur le temps du lit musical, avance de 20–50 ms** — S 43,47–51,73 (94 BPM, 72 % des 32 coupes à ±70 ms, contre 22 % de hasard) ; W partiel (56 % à 135 BPM, hasard 32 %), L absent (11 %) — musique à tempo net (90–100 BPM) pour la rafale ; grille de coupes à 1 temps ; 2 plans de 2 temps pour décélérer — à éviter : caler tout le film (L et W montrent que la parole/le geste priment) ; tempo flou sous voix.
6. **Mots-clés à deux graisses ou accent de couleur, placés dans le tiers haut, derrière la personne (2.5D)** — W « THIS HOUSE » dégradé violet/vert derrière le toit, L « just under » jaune / « here in » violet, S « fully / remodeled » (fin + gras) derrière la tête — 1 mot d'accent (couleur de marque) par phrase, entrée par fondu + montée 0,3 s, 2–3 lignes empilées, capitale 5–8 % de la hauteur, détourage par l'agent 5 — à éviter : plus de 3 accents par écran, texte qui masque le visage, couleurs hors charte.
7. **Sous-titres mot par mot, très discrets, à hauteur de poitrine** — W 28–42 s (gras, centré), L 15–63 s (fin, 2 % de hauteur), S 0–58 s (fin, 1,8 %) — pour la darija/français : un mot par 0,2–0,4 s, blanc, sans cadre, taille 2–3 % ; pour les chiffres, le texte gros remplace le sous-titre — à éviter : sous-titres < 2 % de la hauteur illisibles sur mobile (L, S), pas de contraste sur fonds clairs.
8. **Personne réelle face caméra au moment de la preuve/du CTA** — W 38–42 s (cuisine), L 15–63 s (5 rubriques), S 56,6–58,4 s (pastille contact) — l'intervenant (nom + poste + photo) parle au centre, regard caméra, plan 4–6 s ; sinon l'écran logiciel — à éviter : plans parlés de plus de 11 s sans coupe ni média (L 52–63), personne minuscule dans un plan large (L 38–44).
9. **CTA identifié par une pastille nom + contact (verre dépoli, 2 s)** — S 56,5–58,4 (nom + téléphone + photo ronde) ; W/L : CTA seulement parlé ou logo (L 63,7–68,2) — « Prénom Nom, poste, WhatsApp/lien, photo ronde », entrée 0,3 s, tenue 2 s, sur un plan posé ; à valider avec la personne — à éviter : CTA seulement oral (W), noir final de 2,5 s (L 68,2–70,7), numéro illisible.
10. **Découpage en rubriques annoncées par une carte (liste)** — L « Number two/three/five » (26,0 / 37,5 / 52,2), titre de liste à 17,9–20,3 — « 5 choses qui changent pour un promoteur » : carte numérotée 1–2 s à chaque rubrique (même style, **toutes numérotées**), une rubrique = un écran du logiciel — à éviter : carte oubliée (rubriques 1 et 4 de L), liste de plus de 5.
11. **Plan d'ouverture/fermeture en vue d'ensemble (aérien) qui donne l'échelle** — W 42,4–45,8, L 63,7–68,2, S 58,4–60,9 — résidence ou chantier du client en drone, 2,5–4,5 s, avec fondu de logo 0,3 s ; sinon un zoom arrière de la maquette — à éviter : fond muet sans info ; plus de 4,5 s.
12. **Mouvement continu et raccord de sortie de cadre** — W 10,5–25,6 (vol FPV, raccords masqués), L 28,3–29,3 (l'agent sort, la caméra continue), S 24,9–25,0 (jardin → cuisine) — un seul geste de caméra virtuelle à travers plusieurs maquettes ; l'intervenant sort à droite, l'écran entre par le même vecteur — à éviter : FPV réel sans drone/pilote, plus de 8 raccords masqués d'affilée.
13. **Light leak / flash de couleur pour changer de chapitre** — W 5,17–5,27 et 35,13–35,67, S 51,7 — fuite orange 3 images entre deux modules (Estate → Build → Co-Owner) — à éviter : plus de 2 par vidéo (effet daté), teinte hors charte.
14. **Lit musical mastérisé à −14 LUFS avec ducking de 8–15 dB sous la voix** — W −14,1 (baisse de 8–15 dB à 27 s), L −14,1 (8–12 dB), S −14,2 (LRA 3,6, ducking faible) — mastering −14 LUFS, crête ≤ −1 dBTP, ducking 8–12 dB (déjà la méthode de l'agent 2) — à éviter : crête +1,2 dBTP (L), musique forte pendant la parole (S).
15. **Autres gestes de personnage fort** — W faux appel iPhone 0,5–2,4 s, S carte vidéo posée sur la paume 2,2–4,2 s — notification/appel natif ou écran sur la main de l'intervenant, tourné en motion design (agent 13 pour la main) — à éviter : fausse UI qui imite un vrai service ou une vraie marque tierce ; ne les utiliser qu'une fois par vidéo.

### Tutoriel « meubler une pièce vide avec l'IA » (Higgsfield, Nano Banana Pro, Kling 2.5 Turbo — oct. 2026)
- **Avant/après dans une fenêtre en forme de téléphone dès 0 s** (la transformation se fait en ≈ 1 s) — chez BitEye : un lot « libre » qui devient « réservé » dans une maquette VISION Estate, un tableau vide qui se remplit — à éviter : un avant/après trompeur pour un acheteur.
- **Accroche qui se referme en capsule puis en point, bascule en écran partagé** (orateur en haut, écran en bas, échelle en 0,25 s) — chez BitEye : intervenant en haut, maquette du logiciel en bas, couleurs de la vidéo.
- **Étapes numérotées de 2 à 4 mots** (« 1 Importer les lots » … « 5 Résultat »), une légende centrée par étape ; coupes sur les respirations ; attentes de calcul supprimées.
- **Résultat montré trois fois** (accroche, milieu, fin) ; voix seule propre possible sans musique (−14 LUFS).
- **Prompts affichés** (option A) : image « Furnish living room with modern furniture, including a sectional, rug, coffee table, light fixture and two accent chairs. Add greenery to the shelves and make everything proportional to the room. All the furniture should be modern and cozy in style, » ; vidéo « Each piece of furniture pops up and falls into place one by one. The camera has super smooth forward motion » — idée : les éléments d'un écran ou d'un bureau de promoteur qui « tombent en place un par un ».
- À éviter : CTA absent, texte flou par compression, fautes à l'écran.

### Traversée sans coupe (pub immobilière, oct. 2026)
- **Une personne traverse plusieurs pièces en un seul plan**, raccord « mur-rideau » (un panneau qui glisse révèle l'espace suivant), un mot-clé ancré dans chaque décor, la personne passe parfois devant le texte, fin qui boucle sur le début — chez BitEye : une « pièce » par module VISION (Estate, Build, Co-Owner…), panneau coulissant entre maquettes d'écran, intervenant détouré pleine hauteur — à éviter : 16:9 centré dans du 9:16, tenue qui change (signe d'IA), absence de produit et CTA faible.

**Non transposable** :
- Vol FPV intérieur et plans drone du bien fini ; lifestyle de luxe (voiture, bourg) ; prix en dollars. Chez BitEye : maquettes dessinées du logiciel, chantier ou résidence du client, chiffres du client en dinars (m², lots, délais), à faire confirmer.
- Le B2B exige une preuve chiffrée et un CTA écrit ; les 3 vidéos vendent un désir (acheteur particulier), BitEye vend un gain (promoteur).
- Marques, enseignes et coordonnées tierces vues dans ces vidéos : ne rien reprendre ; musique : jamais celle de ces vidéos.

## Banque de hooks

Référence complète dans `references/hooks.md` : règles (rien d'inventé, aucune promesse de vues, la question du hook trouve sa réponse avant le CTA), mécanismes, catégories transposées à VISION Workspace, hooks visuels faisables avec le moteur. À lire au moment du concept : chaque concept propose 3 hooks de 3 catégories, notés sur 10.

## Vidéos analysées

| Vidéo (Drive) | Analysée | Apports |
|---|---|---|
| Construction par IA « gravité inversée » (29,5 s) | 2026-10-24 | méthode option A, 4 prompts (rapport Drive) |
| Traversée de pièces sans coupe (15 s) | 2026-10-24 | plan unique, raccord mur-rideau, mot ancré dans le décor |
| Tutoriel « meubler une pièce avec l'IA » (81 s) | 2026-10-24 | avant/après en fenêtre téléphone, étapes numérotées, prompts |
| Spira — « Les conseils de Mamie » (23 s) | 2026-10-24 | accroche-accusation, punch-in unique, pastilles verre dépoli, compteur |
| Spira — « Une pub ne commence pas par une pub » (42 s) | 2026-10-24 | paradoxe, liste qui s'empile, métaphore filée, CTA à mot-clé |
| 4 Chase Rd, Windermere (45,8 s, 17 plans) | 2026-10-24 | accroche en mouvement + texte géant derrière la personne, whips calés sur le geste, fuites de lumière |
| Lake Nona Luxury Estate (70,7 s) | 2026-10-24 | chiffre dès 1,8 s, liste parlée en rubriques numérotées, plan aérien de fin |
| 715 Sunridge Drive (61 s, 33 plans) | 2026-10-24 | coupes sur le temps (94 BPM, 72 %), rafale à 1 temps par plan, pastille contact |
