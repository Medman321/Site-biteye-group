---
name: motion-engine
description: Moteur de motion design BitEye — transforme un storyboard.json (scènes, blocs animés minutés, voix, sous-titres mot à mot, photos, clips, musique) en page HTML synchronisée puis en MP4 1080p via Playwright et ffmpeg. Référence complète des blocs, des formats et des commandes de rendu.
---

# Moteur de motion BitEye

```
engine/template.html   moteur (CSS + JS), rendu = fonction pure du temps t
scripts/build.py       storyboard.json → <slug>.html, <slug>.local.html, <slug>.render.json, <slug>.cues.json, <slug>.srt (V4), media/
scripts/render.js      page → planche d'images + contrôles (--stills, --tsheets) ou MP4 (--mp4 ; maître 1080 --quality 100 --bt709), audio mixé par ffmpeg
engine/THIRD-PARTY.md  code adapté d'un tiers (pack video-agent-skills, licence MIT) : à compléter à chaque emprunt
examples/              storyboards validés : pub darija 9:16 et sa version 16:9 (même voix, words.json), touche humaine, transitions-9x16 (V3), comment-cta-9x16 (V4)
```
Prérequis : python3, ffmpeg, node + playwright avec Chromium (présents dans les sessions cloud ; ailleurs `npm i -g playwright && npx playwright install chromium`).

## Commandes

```
ENG=.claude/skills/motion-engine/scripts
python3 -I $ENG/build.py STORYBOARD.json --out OUT [--sidecar]
node $ENG/render.js OUT/<slug>.local.html --stills OUT/stills [--times 1.5,6,12]
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 [--fps 30]
node $ENG/render.js OUT/<slug>.local.html --tsheets OUT/transitions            # V3 : 10 images consécutives par transition
node $ENG/render.js OUT/<slug>.local.html --stills OUT/stills --contrast --fonts --scene-exits [--strict]   # V4 : contrôles mesurés
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 --quality 100 --bt709               # V4 : maître de livraison 1080
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 --cache OUT/cache [--chunk 5]        # V4 : pré-rendus par tranches réutilisées
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 --scale 2 --master --deliver1080 [--maxrate 8M] [--hevc]   # 4K : seulement sur demande explicite
```
- **Règle de livraison (27/10/2026)** : maître = 1080 `--quality 100 --bt709` (conversion BT.601 → BT.709 et étiquettes BT.709, x264 crf 16) + version WhatsApp ≤ 15 Mo (`make_lite.sh`) ; `--scale 2 --master` (4K) seulement si le demandeur le demande explicitement. Mesure : 0,36 s/image pour l'exemple comment-cta (6 s, plaques vidéo) en `--quality 100 --bt709`, ≈ 31 Mbit/s avec grain.
- Rendu : ~2,5 images/s en 9:16 (41 s ≈ 2 min) ; plus lent avec des clips vidéo (chaque image attend la position exacte du clip).
- Médias embarqués en base64 tant que le total reste sous ~14 Mo ; au-delà (ou avec `--sidecar`), la page référence `media/…` : garder le dossier à côté du HTML, et le publier via `files`.
- Les clips sont convertis en WebM VP9 sans son (le Chromium de rendu ne lit pas le H.264). Leur son passe par `audioMix`.
- `--stills` prend une image juste avant la fin de chaque scène (tous les blocs sont entrés) et renvoie `fit` : le facteur de réduction de chaque scène (1 = tient sans réduction). En dessous de 0,9, allège la scène ou passe-la en `split`.
- V4, toujours avec `--stills` : t = 0 est ajouté aux instants et le JSON contient `image0` (textes visibles à opacité > 0,9, contraste du plus grand texte contre les pixels derrière lui, plan de source présent, `ok` = un texte lisible ≥ 4,5:1 ou un plan de source, `alertes` : flash à 0 = image blanche, aucun bloc visible) ; `hors_zone` [{t, bloc, côté, px}] : boîte (mesurée par le DOM, coupée par les `overflow`) de chaque texte, logo, bandeau, CTA et feuille de commentaires hors du gabarit de zones sûres ; `taille_min` [{t, bloc, px, min}] : texte < 38 px après `fit` (34 px dans une maquette ou une interface dessinée, 58 px pour les sous-titres). Le bloc est l'indice `scène.bloc` (`marque` = barre de marque).
- Options : `--contrast` (contraste de chaque texte visible, `contraste_faible` sous 4,5:1, 3:1 à partir de 100 px), `--fonts` (famille réellement rendue de chaque nœud de texte par le protocole de débogage de Chrome → `stills/fonts.json`, code de sortie 2 si une police de secours remplace celle du thème), `--scene-exits` (3 images par changement de scène : fin, +0,15 s, +0,3 s ; opacité résiduelle des blocs de l'ancienne scène et recouvrements ; KO au-dessus de 0,02 à +0,3 s), `--strict` (code de sortie 3 si `image0`, `hors_zone`, `taille_min`, `contraste_faible` ou une sortie de scène échoue). `pre_render_gate.sh` lance `--fonts --scene-exits --strict` sur la page du projet.
- Un avertissement ffmpeg « Header missing / Invalid data found » sur un MP3 de téléphone vient du fichier source (dernière trame tronquée) : sans effet si le rendu finit avec `"ffmpeg":0`.

## Zone utile par format

Le contenu d'une scène se place entre la barre de marque et les sous-titres :

| Format | Taille | Zone utile (avec sous-titres) | Conseils |
|---|---|---|---|
| 9:16 | 1080×1920 | 960 × ~1240 px | empiler : titre, puis visuel ; idéal pour cartes, listes, maquette |
| 4:5 | 1080×1350 | 960 × ~670 px | 2 blocs par scène maximum |
| 1:1 | 1080×1080 | 960 × ~400 px | titre + un seul visuel ; préférer `wave:false` ou des sous-titres courts |
| 16:9 | 1920×1080 | 1800 × ~650 px | `split` (texte à gauche, visuel à droite), titres sur une ligne, tailles ÷ 1,3 |

Sans sous-titres, la zone gagne ~300 px de haut. Les cartes (560 px) et la maquette `app` (~1000 px) sont hautes : en paysage, mets-les dans la colonne droite d'un `split`.

**Zones sûres 9:16** : les valeurs sont celles du gabarit unique du DA (`art-direction-design-critic`, tableau des zones sûres), jamais recopiées ici. Le moteur les connaît sous les noms `reels` (défaut), `reels-pub`, `tiktok` et `whatsapp` ; `--stills` les mesure (`hors_zone`). Avec `"safeZone": "<nom>"` (V4) dans l'en-tête, la barre de marque, les marges du contenu et des sous-titres suivent ce gabarit (ex. TikTok : 140 px libres à droite) ; sans cette clé, la mise en page V3 reste identique (storyboards validés), mais la barre de marque (y = 150 en `safe`) est signalée hors zone : mets `"safeZone": "reels"` dans tout nouveau storyboard vertical.

## storyboard.json

```json
{
  "title": "Pub VISION Workspace", "slug": "pub-vision", "format": "9:16", "lang": "fr",
  "duration": 41,
  "voice": "src/voix.mp3",
  "captions": {"words": "words.json", "maxWords": 12, "pause": 1.6,
               "replace": {"8": "réalisation ?", "Matkhlilik": "Ma tkhallilek"},
               "merge": [[4, 5, "wella"]], "rtl": false},
  "media": {"chantier": "src/photo1.jpg", "drone": "src/clip.mp4"},
  "audioMix": [{"src": "drone", "start": 12.0, "from": 3.0, "duration": 4, "volume": 0.6}],
  "music": {"src": "src/musique.mp3", "volume": 0.12, "fadeOut": 2},
  "brand": true, "brandSpans": [[0.3, 17.9], [24.6, 36.9]], "wave": true, "poster": 39,
  "scenes": [ … ]
}
```
| Clé | Rôle |
|---|---|
| `format` | `9:16` 1080×1920, `16:9` 1920×1080, `1:1` 1080×1080, `4:5` 1080×1350 ; ou `size: [w,h]` |
| `duration` | durée totale (s) ; défaut = fin de la dernière scène + 1 |
| `voice` | bande son principale ; anime aussi le halo et l'onde. Sans `voice`, la vidéo est muette (les sous-titres restent possibles avec `captions.words`) |
| `captions.words` | `words.json` (ElevenLabs ou `audio-studio`). L'orthographe darija validée par le demandeur sur la première pub est dans `examples/vision-darija-9x16/storyboard.json` (`replace`, `merge`) : reprends-la. `replace` : clé = index du mot **d'origine** (chaîne, avant fusion) ou texte du mot ; `""` supprime un mot. `merge` [i, j, texte] : fusionne les mots d'origine i à j. `phrases` [[a,b],…] : force le découpage, indices **après** fusion. Découpage auto : ponctuation finale, pause > `pause` (1,6 s), plus de `maxWords` (12) mots ou de `maxChars` caractères (62 en vertical, 52 en paysage) |
| `media` | clé → fichier ; les blocs référencent la clé |
| `audioMix` | son d'un clip ou bruitage placé à `start`, lu depuis `from` |
| `music` | musique de fond, fondu en entrée et en sortie (fournie par le demandeur ; ne jamais télécharger de musique sans licence) |
| `brandSpans` | intervalles où la barre « VISION Workspace » est visible en haut (la masquer pendant une révélation du logo) |
| `poster` | instant affiché avant lecture (défaut : 1,5 s avant la fin) |
| `theme` | palette : `officiel` (bleu nuit + turquoise, défaut) ou `v2` (vert forêt + citron, sur demande). Le logo est toujours l'œil BitEye d'origine — voir `biteye-brand` |
| `safe` | `true` pour Reels / TikTok / Shorts / Stories : textes et sous-titres remontés hors des zones des boutons |
| `grain` | grain de film, 0,06 à 0,14 (touche humaine, cache la compression) |
| `safeZone` | V4 : gabarit de zones sûres (`reels`, `reels-pub`, `tiktok`, `whatsapp` ou `{top, bottom, left, right}`) ; `safeZones` surcharge les valeurs d'un nom *(non validé sur une vidéo client)* |
| `outDur` | V4 : durée des sorties de blocs (défaut 0,4 s inchangé ; **0,26 s conseillé**, courbe douce, opacité exactement 0 à la fin) |
| `holdPush` | V4 : poussée lente sur tout bloc tenu ≥ 3 s (0,025 = 2,5 % ; défaut 0, ou 0,025 avec `"premium": true`) ; aussi par bloc *(non validé sur une vidéo client)* |
| `extends` | V4 : `"serie.json"` (thème, polices, sous-titres, CTA + mot-code, `safe`, `grain`, `outDur`, `holdPush`…) fusionné sous le storyboard, dont la valeur gagne ; le build copie `serie.<date>.json` dans la sortie : une retouche ou une déclinaison pointe sur cette copie figée *(non validé sur une vidéo client)* |
| `handheld` | caméra à l'épaule, 0 (trépied) à 1 (léger tremblé) |
| `flashes` | instants de flash blanc (coupe nette, hook) ; ex. `[0.0]` |

### Scène

```json
{"id": "solution", "start": 12.65, "end": 18.1, "gap": 24, "align": "center", "split": 0,
 "background": {"src": "chantier", "dim": 0.9, "position": "50% 30%", "kenburns": {"from": 1.0, "to": 1.15, "x": -2, "y": 0}},
 "blocks": [ … ]}
```
La scène est visible de `start` à `end` (+0,4 s de sortie). `split: N` met les N premiers blocs dans une colonne gauche (alignée à gauche) et les autres dans une colonne droite : c'est la mise en page de base du 16:9. Le contenu est centré dans la zone utile (sous la barre de marque, au-dessus des sous-titres) et réduit automatiquement s'il déborde : si la planche montre une scène trop petite, retire des blocs plutôt que de compter sur la réduction.

### Blocs

Champs communs : `at` (entrée, s — **mets le `start` du mot prononcé** ; V4 : un `at` négatif est accepté, −0,3 à −0,5 s), `shown: true` (V4 : déjà dans son état final à t = 0 ; un `letters`, `typewriter` ou `stats` continue son mouvement, commencé à −0,3 s : l'image 0 n'est jamais vide), `anim` (`up` défaut, `down`, `left`, `right`, `fade`, `pop`, `zoom`, `rise`, `punch` et `slam` pour un hook, `drop` pour une photo posée, V4 `spring` : ressort critique sans dépassement, 40 px et 0,965 → 1), `out` (sortie anticipée), `tilt` (inclinaison en degrés, effet posé à la main), `mark` (`circle`, `underline`, `arrow`, `cross`, `check` : trait au feutre animé autour du bloc, `markAt`, `markColor`), `animOpts` (`dur`, `os` échelle de sortie, `outDur`…). Texte : `*mot*` = accent, `\n` = retour à la ligne.
V4 *(non validé sur une vidéo client)* : `moveKeys` [[t, x, y, échelle]] (le bloc reste et glisse ou grandit d'une clé à l'autre, ressort 12–14 réglable par `moveW` : une idée développée = un seul tableau qui évolue), `hero` {scale: 1.5, at} (entre grand et centré dans la zone utile, échelle 1,3 à 1,7, puis glisse à sa place avant l'élément suivant), `holdPush` (voir l'en-tête). Ces mouvements passent par les propriétés CSS `translate` et `scale`, composées avec l'animation d'entrée.

| type | champs | usage |
|---|---|---|
| `headline` | `text`, `size` (110), `italic`, `color:"lime"` | titre |
| `eyebrow` | `text` | surtitre citron en capitales |
| `body` | `text`, `size` | phrase d'appui |
| `letters` | `text`, `size`, `stagger` | mot qui s'écrit lettre par lettre |
| `arabic` | `text`, `size` | texte arabe (RTL) |
| `quote` | `text`, `author` ; V4 *(non validé sur une vidéo client)* : `mark: "highlight"` + `markAt` (un instant, ou un par phrase : surligneur d'accent à 38 % qui balaie la phrase en 0,7 s quand elle est dite, une phrase à la fois), `read` {at, cps} (mots pas encore dits à 45 % d'opacité) ; carte tenue 6 à 8 s (7 à 10 s avec nom, poste, entreprise et date), source réelle et accord | témoignage |
| `chip` / `chips` | `text`, `flag:"dz"`, `icon` / `items[]` | pastille / rangée de pastilles |
| `cards` | `items[{kicker,title,desc,icon \| illustration:"tower"\|"crane", at}]`, `separator{text,at}` | 2 ou 3 profils, offres |
| `pillars` | `items[{title,desc,icon,at}]` | modules, piliers (empilés en 9:16, en ligne en 16:9) |
| `checklist` | `items[]`, `at`, `every` ou `ats[]` | liste qui se coche |
| `tiles` | `items[[titre,sous-titre]]`, `at`, `sortAt`, `columns` | désordre → rangé (sur « organiser ») |
| `stats` | `items[{label,value,suffix,decimals,at}]` ; V4 : `ease: "outExpo"` (75 % de la valeur au cinquième du temps, 97 % à la moitié ; défaut 0,9 s, départ 0,12 s après l'entrée, largeur fixe), `dur`, `endAt` (le comptage finit sur la fin du mot-nombre) ; valeur finale tenue ≥ 1 s (sinon alerte du build) ; par bloc ou par item | gros chiffres qui défilent |
| `app` | `window`, `title`, `subtitle`, `sidebar[]`, `active`, `kpis[{label,value,suffix,decimals}]`, `kpisAt`, `bars{title,items[{label,value}]}`, `barsAt` ; V4 *(non validé sur une vidéo client)* : `ease`/`dur`/`endAt` des kpis, `viewKeys` [[t, échelle, x %, y %]] (zoom étagé 1 → 1,25 → 1,6 à 1,9, ressort sans dépassement ≈ 0,7 s, jamais de bord visible), `ring` {at, x %, y %, r px, dim 0,45, out} ou liste (anneau d'accent, le reste atténué, un seul à la fois), `bigValue` {text, at, size 110} (le chiffre lu, répété en grand sous la maquette), `bars.ecart` {at} + items `{prevu, ecart: "+12 %"}` (prévu gris et réalisé qui se remplissent dans les 0,3 s de l'entrée ; à `at`, le prévu devient un contour pointillé et la pastille d'écart remplace la valeur) | maquette dessinée de VISION Workspace (« Données fictives » ajouté) |
| `schedule` | `title`, `subtitle`, `rows[[nom, montant/date, statut, "ok"\|"wait"\|"late"]]`, `rowsAt`, `every` ; V4 : 5e valeur `{statusAt, to, cls}` ou ligne objet `{name, amount, status, cls, statusAt, statusTo, clsTo}` (le statut change à l'instant dit, coche tracée) | échéancier acquéreurs dessiné |
| `phone` | `title`, `items[{icon, text, sub, at}]` ; V4 : `statusAt`, `statusTo` (l'icône devient une coche tracée, le sous-titre change) | écran d'application mobile dessiné |
| `image` | `src`, `height` ou `aspect`, `position`, `kenburns` (ou `false`), `label` ; V4 : `viewKeys`, `ring`, `bigValue` comme `app` | photo |
| `video` | `src`, `from`, `height` ou `aspect`, `label`, `audio` | clip (muet ; son via `audioMix`) |
| `gallery` | `items[{src,label,at}]`, `columns` | plusieurs photos qui apparaissent |
| `logo` | `size`, `draw` (tracé animé, défaut true) | logo BitEye |
| `wordmark` | `text` (défaut `VISION *Workspace*`), `size` | nom du produit |
| `cta` | `text`, `wide` ; V4 : `pulse: false` (pas de pulsation ; le pulse reste le défaut tant que la planche avec le demandeur n'a pas tranché), `maxWidth` (px ; 900 pour tenir dans la zone sûre `reels` avec la pulsation) ; appui de 5 % quand un `pointer` le touche | bouton d'accent |
| `url` | `text` (défaut biteye-group.com) | site |
| `rings` | `ats[]` | ondes décoratives (accueil, révélation) |
| `note` | `text`, `size` (72), `ar`, `color:"ink"` | note manuscrite (Caveat ; `ar` : Aref Ruqaa) |
| `sticker` | `text` | autocollant (avec `tilt`) |
| `typewriter` | `text`, `cps` (lettres/s), `size` | texte tapé en direct avec curseur |
| `chat` | `items[{who, text, time, from:"in"\|"out", at, typing}]` | conversation WhatsApp ; « en train d'écrire » avant chaque message reçu |
| `lowerthird` | `name`, `role`, `photo` ; V4 : `roleSize` (px ; 38 = plancher du DA, le défaut 32 px est signalé par `taille_min`) | bandeau nom + rôle d'une vraie personne |
| `polaroid` | `src`, `caption`, `aspect`, `width` (760) | photo papier avec scotch et légende manuscrite |
| `pointer` | V4 *(non validé sur une vidéo client)* : `moves` [[t0, t1, x, y]] (px de la toile, adoucis ; t0 = t1 : saut pendant qu'il est caché), `press` [t \| [t, "id", échelle]] (appui 0,14 s, −7 % sur un bouton, −16 % sur une icône, −5 % sur un `cta` ; onde 0,42 s), `vis` [[a, b]] (défaut : 0,1 s avant le premier geste → 0,1 s après le dernier), `size` (92) | curseur ou doigt dessiné (disque blanc 32 % → 62 % à l'appui) |
| `commentCta` | V4 *(non validé sur une vidéo client)* : voir « Bloc commentCta » ci-dessous | feuille de commentaires neutre, mot-code tapé, réponse automatique |
| `spacer` / `html` | `h` / `html` | espace / contenu libre (dernier recours) |

Icônes : `chart building tower crane doc check key users wallet calendar tools map truck coins shield home phone spark`.

Exemple de hook et de touches humaines : `examples/touche-humaine-9x16/storyboard.json`. Les exemples ne contiennent aucun média (dépôt public) : `voix.mp3` et `chantier.jpg` sont à déposer, ou à remplacer par des médias de test (le contrôle GitHub les génère).

## Bloc commentCta (V4)

À **proposer au demandeur** (planche de 3 niveaux : sobre = feuille seule, moyen = + cœur, complet = + bannière), **jamais d'office**, et seulement si la réponse automatique est active sur la plateforme du post. Place : une scène de 3 à 4 s **juste avant l'écran final**, posée sur le plan en cours (visage du témoin ou dernier plan) ; sortie vers l'écran final par un `whip` ou une plongée dans l'œil du logo. La voix ne dit pas « commentez » (le mot-code est dans la légende et le commentaire épinglé) ; le CTA écrit unique reste celui de l'écran final. Exemple : `examples/comment-cta-9x16/`.

```json
{"type": "commentCta", "at": 36.2, "code": "FORMATION 1", "variant": "instagram",
 "reply": "Voici le lien WhatsApp : 05 60 06 36 41", "link": "wa.me/213560063641"}
```
| Champ | Rôle |
|---|---|
| `code` (ou `motCode`) | mot-code exact du brief ; le build refuse un caractère invisible ou des espaces en bord (il doit être recopiable) |
| `reply` | texte **exact** de la réponse automatique réglée par le demandeur (obligatoire en `instagram`, jamais inventé : le build échoue sans lui) ; deux lignes au plus |
| `link` | début du lien affiché sous la réponse (coupé par « … » s'il est trop long) |
| `variant` (ou `plateforme`) | `instagram` (défaut : feuille + bannière de message privé), `tiktok` (feuille + ligne « BitEye a aimé votre commentaire », 3 s ; mettre `"safeZone": "tiktok"` dans l'en-tête), `sheet` (feuille seule : LinkedIn, statut) |
| `dur` | 3 à 4 s (défaut 3,5 ; 3 en `tiktok`) ; refusé hors de l'intervalle, et si le mot-code est trop long pour la durée |
| `pseudo`, `brand` | `@biteye_logiciels` et `BitEye` par défaut (bannière, avec l'œil BitEye d'origine) |
| `count` | nombre de commentaires avant le geste (12), +1 à la publication ; aucun commentaire d'un tiers n'est montré |
| `labels`, `lang` | textes modifiables (`title`, `publish`, `you`, `now`, `placeholder`, `liked` avec `{brand}`) ; `lang: "ar"` : libellés arabes de droite à gauche (à faire relire) |
| `color`, `zone`, `dim` | accent (défaut : `accents` ou accent du thème), gabarit propre au bloc, voile sur le plan (0,06 ; 0,08 au plus sur un visage) |

Minutage (τ depuis `at`, calculé par le build et écrit dans `cues.json`) : 0 la feuille monte (ressort critique, 0,35 s) et les sous-titres remontent au-dessus d'elle (taille normale) ; 0,40 appui sur le champ ; 0,55 → +0,05 s par signe : saisie en couleur d'accent ; 1,25 appui sur « Publier » (plus tard si le code est long) ; +0,05 le commentaire « Vous · maintenant » s'insère, compteur +1 ; +0,2 cœur ; +0,8 bannière (instagram) ou ligne « a aimé » (tiktok) ; `dur` − 0,3 la feuille redescend (0,26 s, opacité 0 exacte ; non mesurée par `hors_zone` pendant sa sortie). Sons proposés dans `cues.json` : tap à +40 ms de chaque appui, tic par signe, pop à la publication, tap au cœur, deux cloches à la quinte à la bannière.
Géométrie : feuille de 350 px (392 en tiktok) posée sur le bas de la zone sûre, 13 px en retrait des côtés (la poussée de 2,5 % reste dedans) ; bannière en haut de la zone ; couleurs de la palette du storyboard (fond `panel` = bleu nuit éclairci `#0A2F47` en officiel, texte `#EAEEF1`, bouton et texte tapé en accent) ; icônes dessinées (bulle, cœur, lien), aucune icône, couleur, police ni nom de plateforme. Format 9:16 et `safe: true` obligatoires (refusé en 4:5, 1:1 et 16:9). Contrôle : `--stills --times` à τ 0,4, 1,05, 2,5 et sur la tenue, avec `--contrast` : `hors_zone`, `taille_min` et `contraste_faible` vides.

## Synchroniser avec la voix

1. Pour chaque mot-clé, `at` = son `start` dans `words.json` (indices : ordre des mots, à partir de 0).
2. Une scène commence 0,05 à 0,1 s avant son premier mot et se termine juste avant le premier mot de la scène suivante.
3. Les pauses longues accueillent une révélation (logo, produit) : masque la barre de marque à ce moment (`brandSpans`).
4. Laisse l'écran final 2,5 à 4 s après la fin de la voix (`duration` arrondie, par exemple 41 s pour 38,4 s de voix).

## Contrôle qualité (une passe)

Après `--stills`, regarde `sheet.jpg` : texte coupé ou trop petit, chevauchements, scène vide, sous-titre qui couvre un visuel, photo mal cadrée, clip noir (ce dernier signale un codec illisible : reconstruire). Ajoute `--times` sur les moments délicats (révélations, listes). Lis aussi le JSON : `image0.ok`, `hors_zone`, `taille_min` vides (V4 ; ajoute `--contrast --fonts --scene-exits` avant le rendu final). Puis rends le MP4 et vérifie avec `ffprobe -v error -count_frames -show_entries stream=codec_type,duration,nb_read_frames -of compact OUT/<slug>.mp4` (nombre d'images = durée × 30).

## Étendre le moteur

Un nouveau type de bloc s'ajoute dans `template.html` : `B.<type> = (b, sc, stage, host) => élément` (V4 : `host` = le `.sv` de la scène, pour un calque libre posé sur toute la toile comme `commentCta` ; une transformation en plus de l'entrée passe par `xf(el, t => [dx, dy, échelle])` ; `data-blk` = `scène.bloc` est posé automatiquement pour les mesures de `render.js`) ; animer avec `A(el, tin, tout, kind)` ou un `HOOKS.push(t => …)` qui ne dépend que de `t`. Tout doit rester une fonction du temps (pas d'animation CSS ni de `setTimeout`), sinon le MP4 ne correspond plus à la page.

Structure d'une scène (V3) : `section.scene` (visibilité, masque, flou de la scène entière) > `.sv` (transformation « scene ») > `.camf` (flou des médias) > `.cam` (caméra : `drift`, `zoomPunch`, `matchCut`) > fond + `.layers` ; les blocs sont dans `.sv`, hors de la caméra. Un calque vidéo/sujet/image : `.ly` (visibilité, flou) > `.lyi` (caméra du calque) > `.lyi` (zoom V2). Une nouvelle transition = des opérations `t => [s, tx, ty]` poussées dans `camOf(mover, filt).ops` (le flou de mouvement se calcule seul à partir de ces opérations à t−δ).

## Porte avant rendu (outils V2)
`bash .claude/skills/motion-engine/scripts/pre_render_gate.sh PROD [animatic.mp4]` (align_check, coupes non prévues, ffprobe avec nombre d'images, sonie et pic réel ≤ −1 dBTP ; V4 : contrôle de la page `PROD/out/*.local.html` par `render.js --stills --fonts --scene-exits --strict` : image 0, zones sûres, tailles, police rendue, sorties de scène) doit être vert avant le rendu final et avant tout contrôle croisé.
`layer_diff.py behind|effect` : mot vraiment derrière la tête / effet visible mais pas trop fort, sur 2 ou 3 images clés. `cut_audit.py` : coupes non prévues. `make_lite.sh` : version WhatsApp ≤ 16 Mo. `cut_audit.py` a été testé sur un MP4 réel ; `layer_diff.py` seulement sur des images de synthèse, et son mode `behind` attend une option `--hide` de `render.js` qui n'existe pas encore.

## Ajouts du moteur V2 (témoignage)

- `theme: "temoignage"` (couleurs ambre/champagne tirées des vidéos) en plus de `officiel` et `v2`.
- Médias `.webm` VP9 copiés tels quels (plaques plein cadre, sujets détourés avec alpha `yuva420p`) pour la composition 2.5D : fond → effets → sujet.
- Options d'en-tête : `accents`, `plainBg`, `glowColor`, `capStyle`, `capPlain`, `capMoves`, `capHide` (masquer les sous-titres sur des plages), `brandTop`, `brandCompact`.
- `render.js` préchauffe la page avant la première image (sinon l'image 0 pouvait sortir sans ses vidéos).

## Moteur V3 (premium) : 4K, transitions, caméra vivante

Exemple complet : `examples/transitions-9x16/` (les 5 transitions, sans média : plaques générées par ffmpeg).

### Rendu 4K net et encodage maître

Le 4K n'est rendu que sur demande explicite du demandeur (règle du 27/10/2026) ; le maître par défaut est le 1080 `--quality 100 --bt709`.

| Option `render.js` | Effet |
|---|---|
| `--bt709` (V4, sans `--master`) | rendu 1080 avec la conversion BT.601 → BT.709 et les étiquettes BT.709 ; x264 `medium`, crf 18, crf 16 avec `--quality 100` |
| `--scale 2` (ou `"renderScale": 2` dans le storyboard) | la page 1080×1920 est capturée avec `deviceScaleFactor: 2` → images 2160×3840 : textes, logo, SVG et grain nets. Au build, les clips gardent leur taille d'origine jusqu'à 3840 px (VP9 crf 30), les photos jusqu'à 4320 px de large |
| `--master` | libx264 `-preset slow -crf 14 -profile high -level 5.1` (5.2 au-delà de 30 i/s, 4.2 en 1080), `yuv420p`, conversion et étiquettes BT.709 (les captures JPEG sont en BT.601 pleine échelle), `+faststart`, captures JPEG qualité 95 |
| `--hevc` | avec `--master` : libx265 `-crf 16`, `hvc1` (lecture Apple), BT.709 |
| `--deliver1080` | écrit aussi `<slug>-1080.mp4` : réduction lanczos du maître, x264 crf 17, son copié (jamais un second rendu) |
| `--maxrate 8M` | plafonne le débit du fichier livré (TikTok ≈ 8 Mbit/s) |
| `--quality N` | qualité JPEG des captures (92 par défaut) |

Temps mesurés (exemple touche-humaine-9x16, 14 s, 420 images, 4 cœurs) : 0,19 s/image en 1080×1920 (x264 crf 18), 1,40 s/image en 2160×3840 maître (capture ≈ 0,45 s, le reste est x264 `slow` crf 14 en 4K) ; exemple transitions en 4K maître : 1,93 s/image (filtres de flou et masques). Un maître 4K avec grain pèse ≈ 150 à 250 Mbit/s (≈ 25 Mo par seconde) : le débit est plafonné à 240 Mbit/s (VBV) pour rester dans le niveau 5.1 ; livrer la version `-1080` (≈ 10 Mbit/s) et garder le maître pour l'archive.

### Transitions (`transition` sur une scène, ou liste `transitions`)

`transition` sur une scène = passage depuis la scène précédente ; la coupe (`cut`) est par défaut le `start` de la scène. Temps : `at` = début du mouvement, `cut` = image où le plan change, `end` = fin ; donner l'un des deux premiers suffit, `dur` a une valeur par défaut. Le build écrit `<slug>.cues.json` (début, coupe, fin et son conseillé de chaque transition) pour le sound designer, et `render.js --stills` les renvoie aussi (`transitions`).

| type | défaut | ce qui bouge | options |
|---|---|---|---|
| `zoomPunch` | 8 images, coupe à 30 % | plaques + sujet (`target: "media"`) | `to` (1,12), `from` (sinon le cadrage précédent : alternance 1,00 ↔ 1,12 automatique), `origin` ("50% 40%"), `blur`, `peak` (pic puis retour : `from` → `peak` en accélération jusqu'à `cut`, puis `peak` → `to` en décélération jusqu'à `end`) ; `target: "scene"` déplace aussi les blocs (ex. plongée dans un logo) |
| `whip` | 8 images, coupe au milieu | scène entière (A et B côte à côte, panoramique continu) | `dir` (`left`, `right`, `up`, `down`), `blur` |
| `zoomThrough` | 0,9 s, coupe à 62 % | scène entière | `el` (id d'un bloc ou d'un calque `fx`, ex. le mot magazine) ou `x`,`y`, `dx`,`dy`, `to` (16), `fromB` (1,8), `fill` (couleur qui remplit l'écran à la coupe, défaut couleur du mot, `false` pour aucune) |
| `maskReveal` | 0,8 s à partir de la coupe | B apparaît dans la silhouette de A | sujet = premier calque `subject` de A (ou `src` : un WebM alpha), `grow` (7), `origin` ("50% 45%"), `feather` (6 px), `shape: "circle"` avec `x`,`y`,`r0`,`r1`, `ease` du rayon (`in` par défaut, `out`, `inOut`, `area` : la surface du cercle croît linéairement, sans saut de luminance) |
| `matchCut` | coupe sèche puis 0,6 s de relâche | plaques + sujet | `faceA`, `faceB` : `{x, y, s}` (centre et hauteur du visage en px de la toile), `hold: true` (pas de relâche), `pre` (0,25 s) ; la plus petite tête est toujours agrandie, jamais l'inverse ; le cadrage ne montre jamais de bord |
| `morph` (V4 *(non validé sur une vidéo client)*) | 0,6 s à partir de la coupe | scène entière | `from` (id d'un bloc ou d'un calque de A, mesuré à chaque image) : B part du rectangle de cet élément et atteint le plein cadre (courbe très douce), marges et rayon d'angle fondent vers 0, décor de A atténué de 22 % au plus ; idéal quand un même visage ou une même carte se retrouve sur les mêmes pixels ; `cues.json` : « L-cut + souffle court » ; `--tsheets` prend le milieu de la croissance |

```json
{"id": "b", "start": 6.4, "end": 9.8, "transition": {"type": "whip", "dir": "left"}}
{"id": "c", "start": 9.8, "end": 13, "transition": {"type": "matchCut", "faceA": {"x": 540, "y": 700, "s": 260}, "faceB": {"x": 470, "y": 820, "s": 200}}}
"transitions": [
  {"type": "zoomPunch", "scene": "naila", "cut": 12.37},
  {"type": "zoomPunch", "scene": "naila", "a": ["plaque1", "sujet1"], "b": ["plaque2", "sujet2"], "cut": 15.1, "to": 1.0},
  {"type": "zoomThrough", "a": "mag", "b": "suite", "el": "motMag", "cut": 21.4}
]
```
- Dans une même scène : `"scene": id` sans `a`/`b` = une coupe dans la même plaque (la caméra de la scène zoome) ; avec `a`/`b` = deux listes d'`id` de calques (plaque + sujet de chaque plan, transformés ensemble).
- Punch « pic puis retour » (V3.1) : `{"type": "zoomPunch", "scene": "a", "at": 5.47, "cut": 5.567, "dur": 0.233, "from": 1, "peak": 1.04, "to": 1.01}` : la caméra accélère jusqu'à la coupe, qui tombe au pic, puis se pose. Sans `peak`, le comportement V3 (montée continue, collante) est inchangé. Une coupe franche avec relâche (matchCut « recalé ») s'obtient avec `at` = `cut` − 0,001 et `peak` = l'échelle de départ de B.
- Flou de mouvement : 2 échantillons de l'image placés là où la caméra était à t−1/120 s et t−1/60 s (obturateur 180°), opacités 0,34 et 0,2 × `blur` (1 par défaut, 0 = aucun) ; le `whip` ajoute un flou gaussien dans le sens du mouvement. Une image avec flou coûte environ 2,5 fois une image normale.
- Vérifier chaque transition sur sa planche : `render.js … --tsheets DIR` (coupe − 4 … coupe + 5 images ; `maskReveal` : milieu de la croissance).

### Caméra vivante

`"drift": 0.03` sur une scène = push-in de 3 % sur toute la durée du plan, appliqué au fond, à la plaque, aux effets et au sujet détouré ensemble (les blocs de texte restent fixes). Forme longue : `{"scale": 0.03, "x": -20, "y": 0, "origin": "50% 40%", "ease": "inOut"}` (x, y = panoramique en px ; sans `scale`, l'échelle minimale qui cache les bords est calculée). Aussi possible sur un calque (`layers[].drift`, même valeur sur la plaque et le sujet).

### Médias de test générés

Une entrée de `media` peut être `{"lavfi": "gradients=s=1080x1920:…", "duration": 4, "alpha": false}` : ffmpeg génère le WebM au build (`"alpha": true` → `yuva420p`, pour un faux sujet détouré ; `"image": true` → PNG). Les graphes qui lisent un fichier (`movie=`, `file=`…) sont refusés. Sert aux exemples et aux essais ; jamais pour une vidéo client.

## Moteur V4 (27/10/2026) : apports du pack video-agent-skills

Idées du pack de Melvyn Malherbe (licence MIT) qui complètent notre méthode, réécrites pour ce moteur ; les quelques extraits de code adaptés sont listés dans `engine/THIRD-PARTY.md`. Exemple : `examples/comment-cta-9x16/`. Chaque option marquée *(non validé sur une vidéo client)* le reste jusqu'à son premier usage réel.

- **Sous-titres courts** *(non validé sur une vidéo client)* : `captions.short: true` (9:16, à trancher sur une planche A/B des mêmes 3 images clés avec le demandeur, jamais imposé) : blocs de 1 à 3 mots, ≤ 16 signes, ≈ 80 px, coupés à la ponctuation et aux pauses > 0,35 s, par une coupe optimale qui ne finit jamais un bloc sur un mot faible (articles, prépositions, pronoms ; liste darija translittérée `w`, `f`, `b`, `l`, `men`, `3la`… à compléter par `captions.weak`) et préfère les blocs de trois mots. `captions.accents` : 1 ou 2 mots de sens par phrase (chiffre, nom du module) qui seuls prennent l'accent. Écrire les nombres en chiffres (`replace`) et masquer les sous-titres sur un carton qui porte les mêmes mots (`capHide`).
- **Fichier `.srt`** : écrit par le build dès que `captions.words` existe, après `replace` et `merge` : une entrée par phrase, ≤ 7 mots, ≤ 2 lignes de ≤ 36 signes (sinon coupée à la ponctuation ou à la plus longue pause, au plus près du milieu), numérotation continue. À joindre à la publication.
- **`cues.json` par bloc** : en plus des transitions (`kind: "transition"`), une ligne par bloc qui peut porter un son (`kind: "bloc"`, `famille` : pose, pop, cloche, compteur avec début et fin, saisie, tic, tap ; `at` ; `x` estimé pour le panoramique) ; le sound designer y choisit ses 3 à 5 temps forts, il ne sonorise pas tout.
- **Rendu par tranches** (`--cache DIR`, `--chunk 5`) : empreinte de chaque tranche = scènes, transitions et phrases qui la touchent à ±2 s, enveloppe de la voix, options globales, médias utilisés, `template.html`, `build.py` et `render.js` ; une tranche inchangée est réutilisée, les tranches sont assemblées sans réencodage (`concat`) et le son est mixé ensuite. Mesures (exemple touche humaine, 14 s, 4 cœurs) : rendu complet 60 s ; en tranches 63 s la première fois, 1 s sans changement, 43 s après une retouche de la dernière scène (2 tranches sur 3) ; écart à un rendu complet : 48,4 dB en moyenne, 44,5 dB au pire (encodages x264 distincts ; images capturées identiques). Usage : pré-rendus et retouches ; **le rendu final reste un rendu complet unique**. `--workers 2` mesuré à +8 % seulement (58 s contre 63 s) : sous le seuil de 25 %, on garde 1 page.
- **Son** : une voix WAV 48 kHz 24 bits est acceptée telle quelle (règle de production : le WAV d'`audio-studio`) ; le mix reste en flottant (`aformat=fltp`, `amix normalize=0`) avec un seul encodage AAC 192 kb/s. Les exemples gardent des `.mp3` (dépôt public sans média).
- **Contrôles** : `image0`, `hors_zone`, `taille_min`, `--contrast`, `--fonts`, `--scene-exits`, `--strict` (voir « Commandes »). Sorties de blocs : `outDur: 0.26` conseillé (les anciens storyboards gardent 0,4 s, qui laisse ≈ 6 % d'opacité à +0,3 s).
