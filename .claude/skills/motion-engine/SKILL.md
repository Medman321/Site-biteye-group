---
name: motion-engine
description: Moteur de motion design BitEye — transforme un storyboard.json (scènes, blocs animés minutés, voix, sous-titres mot à mot, photos, clips, musique) en page HTML synchronisée puis en MP4 1080p via Playwright et ffmpeg. Référence complète des blocs, des formats et des commandes de rendu.
---

# Moteur de motion BitEye

```
engine/template.html   moteur (CSS + JS), rendu = fonction pure du temps t
scripts/build.py       storyboard.json → <slug>.html, <slug>.local.html, <slug>.render.json, <slug>.cues.json (V3), media/
scripts/render.js      page → planche d'images (--stills, --tsheets) ou MP4 (--mp4, maître 4K --scale 2 --master), audio mixé par ffmpeg
examples/              storyboards validés : pub darija 9:16 et sa version 16:9 (même voix, words.json), touche humaine, transitions-9x16 (V3)
```
Prérequis : python3, ffmpeg, node + playwright avec Chromium (présents dans les sessions cloud ; ailleurs `npm i -g playwright && npx playwright install chromium`).

## Commandes

```
ENG=.claude/skills/motion-engine/scripts
python3 -I $ENG/build.py STORYBOARD.json --out OUT [--sidecar]
node $ENG/render.js OUT/<slug>.local.html --stills OUT/stills [--times 1.5,6,12]
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 [--fps 30]
node $ENG/render.js OUT/<slug>.local.html --tsheets OUT/transitions            # V3 : 10 images consécutives par transition
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 --scale 2 --master --deliver1080 [--maxrate 8M] [--hevc]
```
- Rendu : ~2,5 images/s en 9:16 (41 s ≈ 2 min) ; plus lent avec des clips vidéo (chaque image attend la position exacte du clip).
- Médias embarqués en base64 tant que le total reste sous ~14 Mo ; au-delà (ou avec `--sidecar`), la page référence `media/…` : garder le dossier à côté du HTML, et le publier via `files`.
- Les clips sont convertis en WebM VP9 sans son (le Chromium de rendu ne lit pas le H.264). Leur son passe par `audioMix`.
- `--stills` prend une image juste avant la fin de chaque scène (tous les blocs sont entrés) et renvoie `fit` : le facteur de réduction de chaque scène (1 = tient sans réduction). En dessous de 0,9, allège la scène ou passe-la en `split`.
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

Champs communs : `at` (entrée, s — **mets le `start` du mot prononcé**), `anim` (`up` défaut, `down`, `left`, `right`, `fade`, `pop`, `zoom`, `rise`, `punch` et `slam` pour un hook, `drop` pour une photo posée), `out` (sortie anticipée), `tilt` (inclinaison en degrés, effet posé à la main), `mark` (`circle`, `underline`, `arrow`, `cross`, `check` : trait au feutre animé autour du bloc, `markAt`, `markColor`), `animOpts` (`dur`, `os` échelle de sortie, `outDur`…). Texte : `*mot*` = accent, `\n` = retour à la ligne.

| type | champs | usage |
|---|---|---|
| `headline` | `text`, `size` (110), `italic`, `color:"lime"` | titre |
| `eyebrow` | `text` | surtitre citron en capitales |
| `body` | `text`, `size` | phrase d'appui |
| `letters` | `text`, `size`, `stagger` | mot qui s'écrit lettre par lettre |
| `arabic` | `text`, `size` | texte arabe (RTL) |
| `quote` | `text`, `author` | témoignage |
| `chip` / `chips` | `text`, `flag:"dz"`, `icon` / `items[]` | pastille / rangée de pastilles |
| `cards` | `items[{kicker,title,desc,icon \| illustration:"tower"\|"crane", at}]`, `separator{text,at}` | 2 ou 3 profils, offres |
| `pillars` | `items[{title,desc,icon,at}]` | modules, piliers (empilés en 9:16, en ligne en 16:9) |
| `checklist` | `items[]`, `at`, `every` ou `ats[]` | liste qui se coche |
| `tiles` | `items[[titre,sous-titre]]`, `at`, `sortAt`, `columns` | désordre → rangé (sur « organiser ») |
| `stats` | `items[{label,value,suffix,decimals,at}]` | gros chiffres qui défilent |
| `app` | `window`, `title`, `subtitle`, `sidebar[]`, `active`, `kpis[{label,value,suffix,decimals}]`, `kpisAt`, `bars{title,items[{label,value}]}`, `barsAt` | maquette dessinée de VISION Workspace (« Données fictives » ajouté) |
| `schedule` | `title`, `subtitle`, `rows[[nom, montant/date, statut, "ok"\|"wait"\|"late"]]`, `rowsAt`, `every` | échéancier acquéreurs dessiné |
| `phone` | `title`, `items[{icon, text, sub, at}]` | écran d'application mobile dessiné |
| `image` | `src`, `height` ou `aspect`, `position`, `kenburns` (ou `false`), `label` | photo |
| `video` | `src`, `from`, `height` ou `aspect`, `label`, `audio` | clip (muet ; son via `audioMix`) |
| `gallery` | `items[{src,label,at}]`, `columns` | plusieurs photos qui apparaissent |
| `logo` | `size`, `draw` (tracé animé, défaut true) | logo BitEye |
| `wordmark` | `text` (défaut `VISION *Workspace*`), `size` | nom du produit |
| `cta` | `text` | bouton citron qui pulse |
| `url` | `text` (défaut biteye-group.com) | site |
| `rings` | `ats[]` | ondes décoratives (accueil, révélation) |
| `note` | `text`, `size` (72), `ar`, `color:"ink"` | note manuscrite (Caveat ; `ar` : Aref Ruqaa) |
| `sticker` | `text` | autocollant (avec `tilt`) |
| `typewriter` | `text`, `cps` (lettres/s), `size` | texte tapé en direct avec curseur |
| `chat` | `items[{who, text, time, from:"in"\|"out", at, typing}]` | conversation WhatsApp ; « en train d'écrire » avant chaque message reçu |
| `lowerthird` | `name`, `role`, `photo` | bandeau nom + rôle d'une vraie personne |
| `polaroid` | `src`, `caption`, `aspect`, `width` (760) | photo papier avec scotch et légende manuscrite |
| `spacer` / `html` | `h` / `html` | espace / contenu libre (dernier recours) |

Icônes : `chart building tower crane doc check key users wallet calendar tools map truck coins shield home phone spark`.

Exemple de hook et de touches humaines : `examples/touche-humaine-9x16/storyboard.json`. Les exemples ne contiennent aucun média (dépôt public) : `voix.mp3` et `chantier.jpg` sont à déposer, ou à remplacer par des médias de test (le contrôle GitHub les génère).

## Synchroniser avec la voix

1. Pour chaque mot-clé, `at` = son `start` dans `words.json` (indices : ordre des mots, à partir de 0).
2. Une scène commence 0,05 à 0,1 s avant son premier mot et se termine juste avant le premier mot de la scène suivante.
3. Les pauses longues accueillent une révélation (logo, produit) : masque la barre de marque à ce moment (`brandSpans`).
4. Laisse l'écran final 2,5 à 4 s après la fin de la voix (`duration` arrondie, par exemple 41 s pour 38,4 s de voix).

## Contrôle qualité (une passe)

Après `--stills`, regarde `sheet.jpg` : texte coupé ou trop petit, chevauchements, scène vide, sous-titre qui couvre un visuel, photo mal cadrée, clip noir (ce dernier signale un codec illisible : reconstruire). Ajoute `--times` sur les moments délicats (révélations, listes). Puis rends le MP4 et vérifie avec `ffprobe -v error -show_entries stream=codec_type,duration -of compact OUT/<slug>.mp4`.

## Étendre le moteur

Un nouveau type de bloc s'ajoute dans `template.html` : `B.<type> = (b, sc, stage) => élément` ; animer avec `A(el, tin, tout, kind)` ou un `HOOKS.push(t => …)` qui ne dépend que de `t`. Tout doit rester une fonction du temps (pas d'animation CSS ni de `setTimeout`), sinon le MP4 ne correspond plus à la page.

Structure d'une scène (V3) : `section.scene` (visibilité, masque, flou de la scène entière) > `.sv` (transformation « scene ») > `.camf` (flou des médias) > `.cam` (caméra : `drift`, `zoomPunch`, `matchCut`) > fond + `.layers` ; les blocs sont dans `.sv`, hors de la caméra. Un calque vidéo/sujet/image : `.ly` (visibilité, flou) > `.lyi` (caméra du calque) > `.lyi` (zoom V2). Une nouvelle transition = des opérations `t => [s, tx, ty]` poussées dans `camOf(mover, filt).ops` (le flou de mouvement se calcule seul à partir de ces opérations à t−δ).

## Porte avant rendu (outils V2)
`bash .claude/skills/motion-engine/scripts/pre_render_gate.sh PROD [animatic.mp4]` (align_check, coupes non prévues, ffprobe, sonie) doit être vert avant le rendu final et avant tout contrôle croisé.
`layer_diff.py behind|effect` : mot vraiment derrière la tête / effet visible mais pas trop fort, sur 2 ou 3 images clés. `cut_audit.py` : coupes non prévues. `make_lite.sh` : version WhatsApp ≤ 16 Mo. `cut_audit.py` a été testé sur un MP4 réel ; `layer_diff.py` seulement sur des images de synthèse, et son mode `behind` attend une option `--hide` de `render.js` qui n'existe pas encore.

## Ajouts du moteur V2 (témoignage)

- `theme: "temoignage"` (couleurs ambre/champagne tirées des vidéos) en plus de `officiel` et `v2`.
- Médias `.webm` VP9 copiés tels quels (plaques plein cadre, sujets détourés avec alpha `yuva420p`) pour la composition 2.5D : fond → effets → sujet.
- Options d'en-tête : `accents`, `plainBg`, `glowColor`, `capStyle`, `capPlain`, `capMoves`, `capHide` (masquer les sous-titres sur des plages), `brandTop`, `brandCompact`.
- `render.js` préchauffe la page avant la première image (sinon l'image 0 pouvait sortir sans ses vidéos).

## Moteur V3 (premium) : 4K, transitions, caméra vivante

Exemple complet : `examples/transitions-9x16/` (les 5 transitions, sans média : plaques générées par ffmpeg).

### Rendu 4K net et encodage maître

| Option `render.js` | Effet |
|---|---|
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
| `zoomPunch` | 8 images, coupe à 30 % | plaques + sujet (`target: "media"`) | `to` (1,12), `from` (sinon le cadrage précédent : alternance 1,00 ↔ 1,12 automatique), `origin` ("50% 40%"), `blur` |
| `whip` | 8 images, coupe au milieu | scène entière (A et B côte à côte, panoramique continu) | `dir` (`left`, `right`, `up`, `down`), `blur` |
| `zoomThrough` | 0,9 s, coupe à 62 % | scène entière | `el` (id d'un bloc ou d'un calque `fx`, ex. le mot magazine) ou `x`,`y`, `dx`,`dy`, `to` (16), `fromB` (1,8), `fill` (couleur qui remplit l'écran à la coupe, défaut couleur du mot, `false` pour aucune) |
| `maskReveal` | 0,8 s à partir de la coupe | B apparaît dans la silhouette de A | sujet = premier calque `subject` de A (ou `src` : un WebM alpha), `grow` (7), `origin` ("50% 45%"), `feather` (6 px), `shape: "circle"` avec `x`,`y`,`r0`,`r1` |
| `matchCut` | coupe sèche puis 0,6 s de relâche | plaques + sujet | `faceA`, `faceB` : `{x, y, s}` (centre et hauteur du visage en px de la toile), `hold: true` (pas de relâche), `pre` (0,25 s) ; la plus petite tête est toujours agrandie, jamais l'inverse ; le cadrage ne montre jamais de bord |

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
- Flou de mouvement : 2 échantillons de l'image placés là où la caméra était à t−1/120 s et t−1/60 s (obturateur 180°), opacités 0,34 et 0,2 × `blur` (1 par défaut, 0 = aucun) ; le `whip` ajoute un flou gaussien dans le sens du mouvement. Une image avec flou coûte environ 2,5 fois une image normale.
- Vérifier chaque transition sur sa planche : `render.js … --tsheets DIR` (coupe − 4 … coupe + 5 images ; `maskReveal` : milieu de la croissance).

### Caméra vivante

`"drift": 0.03` sur une scène = push-in de 3 % sur toute la durée du plan, appliqué au fond, à la plaque, aux effets et au sujet détouré ensemble (les blocs de texte restent fixes). Forme longue : `{"scale": 0.03, "x": -20, "y": 0, "origin": "50% 40%", "ease": "inOut"}` (x, y = panoramique en px ; sans `scale`, l'échelle minimale qui cache les bords est calculée). Aussi possible sur un calque (`layers[].drift`, même valeur sur la plaque et le sujet).

### Médias de test générés

Une entrée de `media` peut être `{"lavfi": "gradients=s=1080x1920:…", "duration": 4, "alpha": false}` : ffmpeg génère le WebM au build (`"alpha": true` → `yuva420p`, pour un faux sujet détouré ; `"image": true` → PNG). Les graphes qui lisent un fichier (`movie=`, `file=`…) sont refusés. Sert aux exemples et aux essais ; jamais pour une vidéo client.
