# Code tiers dans le moteur et les scripts BitEye

## Code adapté du pack « video-agent-skills » (Melvyn Malherbe, licence MIT)

Source : dépôt `Melvynx/video-agent-skills`, version du 22/10/2026 (commit `4774fa4`), lu le 27/10/2026. Le pack a été lu, jamais exécuté ; aucun fichier n'a été copié. Les extraits ci-dessous sont courts, réécrits dans notre code et signalés en commentaire là où ils sont utilisés. Tout le reste des apports du pack (plan du 27/10/2026) est une paraphrase d'idées, sans code.

| Apport | Fichier d'origine dans le pack | Fichier chez nous | Ce qui a été repris et adapté |
|---|---|---|---|
| B-27 ressort critique | `skills/short-editing/engine/lib/kit.js` (`S(x, w)`) | `engine/template.html` (`spr`, `sprN`, `KINDS.spring`) | formule S(x, w) = 1 − (1 + w·x)·e^(−w·x) ; ajout d'une version normalisée sur [0, 1] pour nos animations `A()` |
| B-12 curseur et appui | `skills/short-editing/examples/insta-skills/source/ig-cta.html` et `examples/thinking-orbs/source/ig-cta.html` (`curAt`, `pressAt`, ondes) | `engine/template.html` (`curPos`, `pressK`, `makePointer`, bloc `pointer`) | déplacements [t0, t1, x, y] adoucis, appui de 0,14 s (−0,05 à +0,09 s), onde 0,45 → 1,3 en 0,42 s ; réécrit pour nos blocs (cibles par `id`, échelle par la propriété CSS `scale`, visibilité par fenêtres) |
| commentCta | mêmes fichiers `ig-cta.html` (et `ig-dm.html`, `tt-cta.html` pour la variante) | `engine/template.html` (bloc `commentCta`), `scripts/build.py` (`norm_comment_cta`) | chorégraphie et minutage seulement (feuille qui monte, saisie lettre par lettre, publication, compteur, cœur, bannière qui tombe) ; aucune icône, couleur, police ni nom de plateforme : feuille neutre dessinée dans la palette du storyboard |
| B-11 coupe des sous-titres courts | `skills/short-editing/engine/lib/timeline.js` (`captionChunks`, `phraseSplit`) | `scripts/build.py` (`short_blocks`, `WEAK`) | idée de la coupe optimale par programmation dynamique et de la liste de mots faibles ; code réécrit en Python, liste française et darija translittérée à nous |
| D-1 mesure du silence (prévu ; rien n'est encore porté au 27/10/2026) | `skills/short-editing/engine/short.mjs` (`voiceFrames`, `quietRun`, `quietShare`) | `.claude/skills/audio-studio/scripts/edit_voice.py` (fonction à ajouter par l'équipe audio, qui renverra à ce fichier dans l'en-tête du script ; le script actuel ne contient rien du pack) | mesure de la part de trames silencieuses autour d'une coupe ; aucune suppression automatique des pauses (décision du Journal) |

Texte de la licence d'origine :

```
MIT License

Copyright (c) 2026 Melvyn Malherbe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Polices

Inter, Inter Tight, IBM Plex Sans Arabic, Caveat, Aref Ruqaa et DM Serif Display sont chargées depuis Google Fonts (licence SIL Open Font License) ; aucune police n'est copiée dans ce dépôt.
