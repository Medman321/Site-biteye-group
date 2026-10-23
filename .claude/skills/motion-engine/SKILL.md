---
name: motion-engine
description: Moteur de motion design BitEye — transforme un storyboard.json (scènes, blocs animés minutés, voix, sous-titres mot à mot, photos, clips, musique) en page HTML synchronisée puis en MP4 1080p via Playwright et ffmpeg. Référence complète des blocs, des formats et des commandes de rendu.
---

# Moteur de motion BitEye

```
engine/template.html   moteur (CSS + JS), rendu = fonction pure du temps t
scripts/build.py       storyboard.json → <slug>.html, <slug>.local.html, <slug>.render.json, media/
scripts/render.js      page → planche d'images (--stills) ou MP4 (--mp4), audio mixé par ffmpeg
examples/              storyboard validé (pub darija 9:16, 41 s) + words.json
```
Prérequis : python3, ffmpeg, node + playwright avec Chromium (présents dans les sessions cloud ; ailleurs `npm i -g playwright && npx playwright install chromium`).

## Commandes

```
ENG=.claude/skills/motion-engine/scripts
python3 -I $ENG/build.py STORYBOARD.json --out OUT [--sidecar]
node $ENG/render.js OUT/<slug>.local.html --stills OUT/stills [--times 1.5,6,12]
node $ENG/render.js OUT/<slug>.local.html --mp4 OUT/<slug>.mp4 [--fps 30]
```
- Rendu : ~2,5 images/s en 9:16 (41 s ≈ 2 min) ; plus lent avec des clips vidéo (chaque image attend la position exacte du clip).
- Médias embarqués en base64 tant que le total reste sous ~14 Mo ; au-delà (ou avec `--sidecar`), la page référence `media/…` : garder le dossier à côté du HTML, et le publier via `files`.
- Les clips sont convertis en WebM VP9 sans son (le Chromium de rendu ne lit pas le H.264). Leur son passe par `audioMix`.

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
| `voice` | bande son principale ; anime aussi le halo et l'onde |
| `captions.words` | `words.json` ElevenLabs ; `replace` par index de mot (chaîne) ou par texte ; `""` supprime un mot ; `merge` [i, j, texte] fusionne des mots ; `phrases` [[i,j],…] force le découpage (indices après fusion) |
| `media` | clé → fichier ; les blocs référencent la clé |
| `audioMix` | son d'un clip ou bruitage placé à `start`, lu depuis `from` |
| `music` | musique de fond, fondu en entrée et en sortie (fournie par le demandeur ; ne jamais télécharger de musique sans licence) |
| `brandSpans` | intervalles où la barre « VISION Workspace » est visible en haut (la masquer pendant une révélation du logo) |
| `poster` | instant affiché avant lecture (défaut : 1,5 s avant la fin) |

### Scène

```json
{"id": "solution", "start": 12.65, "end": 18.1, "gap": 24, "align": "center",
 "background": {"src": "chantier", "dim": 0.9, "position": "50% 30%", "kenburns": {"from": 1.0, "to": 1.15, "x": -2, "y": 0}},
 "blocks": [ … ]}
```
La scène est visible de `start` à `end` (+0,4 s de sortie). Le contenu est centré dans la zone utile (sous la barre de marque, au-dessus des sous-titres) et réduit automatiquement s'il déborde : si la planche montre une scène trop petite, retire des blocs plutôt que de compter sur la réduction.

### Blocs

Champs communs : `at` (entrée, s — **mets le `start` du mot prononcé**), `anim` (`up` défaut, `down`, `left`, `right`, `fade`, `pop`, `zoom`, `rise`), `out` (sortie anticipée), `animOpts` (`dur`, `os` échelle de sortie, `outDur`…). Texte : `*mot*` = citron, `\n` = retour à la ligne.

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
| `app` | `window`, `title`, `subtitle`, `sidebar[]`, `active`, `kpis[{label,value,suffix,decimals}]`, `kpisAt`, `bars{title,items[{label,value}]}`, `barsAt` | maquette de VISION Workspace |
| `image` | `src`, `height` ou `aspect`, `position`, `kenburns` (ou `false`), `label` | photo |
| `video` | `src`, `from`, `height` ou `aspect`, `label`, `audio` | clip (muet ; son via `audioMix`) |
| `gallery` | `items[{src,label,at}]`, `columns` | plusieurs photos qui apparaissent |
| `logo` | `size`, `draw` (tracé animé, défaut true) | logo BitEye |
| `wordmark` | `text` (défaut `VISION *Workspace*`), `size` | nom du produit |
| `cta` | `text` | bouton citron qui pulse |
| `url` | `text` (défaut biteye-group.com) | site |
| `rings` | `ats[]` | ondes décoratives (accueil, révélation) |
| `spacer` / `html` | `h` / `html` | espace / contenu libre (dernier recours) |

Icônes : `chart building tower crane doc check key users wallet calendar tools map truck coins shield home phone spark`.

## Synchroniser avec la voix

1. Pour chaque mot-clé, `at` = son `start` dans `words.json` (indices : ordre des mots, à partir de 0).
2. Une scène commence 0,05 à 0,1 s avant son premier mot et se termine juste avant le premier mot de la scène suivante.
3. Les pauses longues accueillent une révélation (logo, produit) : masque la barre de marque à ce moment (`brandSpans`).
4. Laisse l'écran final après la fin de la voix (3 à 4 s) : `duration` = fin de la voix + 3.

## Contrôle qualité (une passe)

Après `--stills`, regarde `sheet.jpg` : texte coupé ou trop petit, chevauchements, scène vide, sous-titre qui couvre un visuel, photo mal cadrée, clip noir (ce dernier signale un codec illisible : reconstruire). Ajoute `--times` sur les moments délicats (révélations, listes). Puis rends le MP4 et vérifie avec `ffprobe -v error -show_entries stream=codec_type,duration -of compact OUT/<slug>.mp4`.

## Étendre le moteur

Un nouveau type de bloc s'ajoute dans `template.html` : `B.<type> = (b, sc, stage) => élément` ; animer avec `A(el, tin, tout, kind)` ou un `HOOKS.push(t => …)` qui ne dépend que de `t`. Tout doit rester une fonction du temps (pas d'animation CSS ni de `setTimeout`), sinon le MP4 ne correspond plus à la page.
