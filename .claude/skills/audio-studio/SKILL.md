---
name: audio-studio
description: Traitement audio gratuit et local pour les vidéos BitEye — rendre un mémo vocal de téléphone « studio » (débruitage RNNoise, égalisation, compression, normalisation -14 LUFS), transcrire et minuter les mots sans ElevenLabs (alignement local, Whisper local), générer une voix off gratuite (Piper). À utiliser pour tout fichier audio ou toute piste son de vidéo.
---

# Studio audio gratuit

Tout tourne en local avec ffmpeg, Python et des modèles libres téléchargés une fois depuis GitHub (dans `~/.cache/biteye-models`, ~1,3 Go). Aucun compte, aucun crédit. ElevenLabs reste une option, jamais un passage obligé.

Installation (une fois par session, ~1 min) : `bash .claude/skills/biteye-video-ad/scripts/setup_free_tools.sh`

```
AS=.claude/skills/audio-studio/scripts
```

## 1. Mémo vocal → voix « studio »

```
python3 -I $AS/voice_studio.py "$OUT/src/voix.m4a" --out "$OUT/audio" [--preset voix|chaude|claire|brute] [--target -14]
```
Chaîne : passe-haut 75 Hz → RNNoise (réseau neuronal) + débruitage spectral → de-esser → égalisation (moins de « carton » à 250 Hz, présence à 3 kHz, air à 10 kHz) → compresseur → expandeur doux entre les phrases → normalisation EBU R128 en deux passes.

| Situation | Réglage |
|---|---|
| Mémo normal, pièce calme | défaut (`--preset voix`) |
| Voix grave, ton « radio » | `--preset chaude` |
| Écoute sur petits haut-parleurs, chantier, voiture | `--preset claire` |
| Pièce très bruyante (rue, chantier) | `--strong-gate`, éventuellement `--denoise-mix 1` |
| Voix déjà propre (micro pro) | `--preset brute --no-gate` |
| Cible | `--target -14` réseaux sociaux (défaut), `-16` site, YouTube |

Contrôle obligatoire : lis `studio_report.json` (avant / après : LUFS, crête, bruit de fond) et regarde `compare.png` (spectrogrammes avant / après) avec Read. Attendu : bruit de fond plus bas de 8 dB ou plus par rapport à la voix, pas de « trous » dans les syllabes. Voix métallique ou « sous l'eau » : refais avec `--denoise-mix 0.6`.

Le minutage n'est jamais modifié (pas de suppression de silences) : les temps des mots restent valables, à ±40 ms. Utilise `voix_studio.mp3` comme `voice` dans le storyboard.

## 2. Mots minutés, sans ElevenLabs

Ordre de préférence :

1. **Texte connu** (le demandeur a écrit ou dicté ce qu'il dit, ou il valide un brouillon) : alignement local, le plus fiable pour la darija.
   ```
   python3 $AS/transcribe_local.py "$OUT/audio/voix_studio.wav" --out "$OUT" --text "$OUT/texte.txt"
   ```
   Mesuré sur le mémo de référence : écart médian de 0,10 s, moyen de 0,14 s par mot avec ElevenLabs. Écris le texte exactement comme prononcé, ponctuation comprise : elle aide à placer les pauses.
2. **Texte inconnu** : Whisper local (modèle turbo, ~1 Go), puis alignement.
   ```
   python3 $AS/transcribe_local.py "$OUT/audio/voix_studio.wav" --out "$OUT" --asr --lang fr
   ```
   Très bon en français et en arabe standard. En darija, il donne une approximation phonétique (« Mou la entreprise réalisation », « Lik la solution idéal ») : reconstruis le texte darija à partir de ce brouillon et du contexte, montre-le au demandeur pour correction, puis relance en mode `--text`.
3. **ElevenLabs Scribe** (option payante, skill `media-analysis`) : seulement si le demandeur le préfère ou si la darija est trop dense pour être reconstruite. Le dire avant, avec le coût (~14 crédits par seconde).

Sortie : `words.json` (format ElevenLabs, directement utilisable par `motion-engine`) et `transcript.txt`.

## 3. Raccourcir ou remonter une voix (synchronisation conservée)

Un mémo trop long pour la plateforme (Reels : 15–35 s) se coupe sans refaire la transcription :
```
python3 -I $AS/edit_voice.py "$OUT/audio/voix_studio.wav" --words "$OUT/words.json" --out "$OUT/audio/montage" \
        [--start 0.9] [--end 37.2] [--max-pause 0.6] [--remove-words 16-18] [--remove 14.5-15.9]
```
**Règle BitEye : les silences servent la compréhension.** Ne coupe que les respirations ; garde les pauses qui séparent deux idées et celles qui créent une attente.
- `--max-pause 0.45` : pauses de respiration (au milieu d'une phrase) ramenées à 0,45 s ;
- `--idea-pause 0.9` : pauses qui ferment une idée (après . ? ! :) gardées jusqu'à 0,9 s ;
- `--set-pause T:LEN` : une pause précise à la longueur voulue, pour un suspense avant un mot clé (« la solution… *idéale* » : `14.9:0.75`) ;
- `--keep A-B` : silence voulu, jamais coupé (révélation du logo, effet).
La sortie liste chaque pause (avant → après, type) : relis-la, ajuste les pauses de suspense, et montre la liste au demandeur avec la durée obtenue.
Autres options : `--remove-words` retire une phrase par indices de mots (ceux de `words.json`), `--start/--end` coupent le début et la fin. Sortie : `voix_montee.wav` et un `words.json` décalé (vérifié : moins de 0,08 s d'écart avec la voix réelle). Les coupes se proposent dans la proposition ; le demandeur les valide.

## 4. Voix off gratuite

Quand il n'y a pas de mémo :
```
python3 $AS/voice_tts.py --text-file "$OUT/script.txt" --out "$OUT/audio/vo.wav" --voice fr-homme|fr-femme|ar-homme
python3 -I $AS/voice_studio.py "$OUT/audio/vo.wav" --out "$OUT/audio" --preset chaude
python3 $AS/transcribe_local.py "$OUT/audio/voix_studio.wav" --out "$OUT" --text "$OUT/script.txt"
```
Une phrase par ligne : chaque ligne devient une respiration. Pas de voix darija gratuite : propose plutôt au demandeur d'enregistrer le script lui-même sur son téléphone. C'est gratuit, et c'est la touche humaine la plus forte.

## 5. Son d'un clip vidéo

`python3 -I .claude/skills/media-lab/scripts/media_lab.py audio clip.mp4 "$OUT/audio/clip.wav"`, puis `voice_studio.py` dessus, si quelqu'un parle dans le clip. Pour garder l'ambiance du chantier (béton, outils), utilise `--preset brute --no-gate` et un volume de 0,3 à 0,5 dans `audioMix` : ce son réel fait partie de la touche humaine.

## 6. Musique

Uniquement fournie par le demandeur, ou sous licence libre dont la source est notée dans le compte rendu. Volume 0,08 à 0,14 sous une voix.
