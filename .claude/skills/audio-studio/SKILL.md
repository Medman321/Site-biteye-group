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

Contrôle obligatoire : lis `studio_report.json` (avant / après : LUFS, crête vraie, bruit de fond ; champs à ajouter au rapport : mode et LRA du `loudnorm`, « dynamic » = la crête a imposé un traitement dynamique, à reprendre) et regarde `compare.png` (spectrogrammes avant / après) avec Read. Attendu : bruit de fond plus bas de 8 dB ou plus par rapport à la voix, pas de « trous » dans les syllabes. Voix métallique ou « sous l'eau » : refais avec `--denoise-mix 0.6`.

**Plosives d'un mémo de téléphone** (« p », « b » à 20 cm du micro) : repère le souffle sur la bande 80–160 Hz (pas de 10 ms ; seuil à fixer sur 2 ou 3 mémos réels) ; sur la seule fenêtre du souffle (80 ms au plus), passe-haut à 240 Hz (24 dB/oct, deux biquads) avec fondus de 12 ms et −3 dB ; rien ne change ailleurs. Contrôle : pic grave aplati au spectrogramme, voyelle suivante inchangée à l'écoute. Une option `--deplosive` de `voice_studio.py` s'écrit si le cas revient deux fois.

Le minutage n'est jamais modifié (pas de suppression de silences) : les temps des mots restent valables, à ±40 ms. Utilise `voix_studio.wav` (48 kHz 24 bits) comme `voice` dans le storyboard ; le `.mp3` sert à l'écoute et à l'envoi seulement.

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
   Langue inconnue : `--lang auto` (détection par Whisper, peu fiable sur la darija mêlée de français). **Musique sous la voix** (pub, vidéo de référence) : sans pauses, les zones de parole se perdaient (46 mots sur 142 au test, oct. 2026). Le VAD Silero local prend alors le relais (`--vad auto`, par défaut ; `on` pour le forcer) et chaque zone est plafonnée à 20 s. Mesuré sur une voix de 53 s mêlée à un lit continu : 142 mots, 24 s de calcul, écart médian de 0,14 s par mot (90 % sous 0,35 s) avec la voix seule. Assez pour le squelette d'un script, pas pour des sous-titres mot à mot. La sortie donne `first_word`, `last_word_end` et `words_per_s`, et liste `chunks_without_words` (musique seule, ou parole manquée : écoute ce passage).
3. **ElevenLabs Scribe** (option payante, skill `media-analysis`) : seulement si le demandeur le préfère ou si la darija est trop dense pour être reconstruite. Le dire avant, avec le coût (~14 crédits par seconde).

Sortie : `words.json` (format ElevenLabs, directement utilisable par `motion-engine`) et `transcript.txt`.

**Reprises lissées** : `transcribe_local.py` écrira aussi (option à écrire) `suspects`, la liste des endroits où le modèle a pu lisser une reprise (mot de plus de 0,6 s, suite de mots répétée, mot sans sens dans la phrase, avec son instant). Écoute 4 s autour avant de couper ou de garder. Amorce d'hésitations (`--prompt` de whisper.cpp, `initial_prompt` de faster-whisper) : option à tester sur un extrait avec reprise ; non disponible dans sherpa-onnx 1.13.8.

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

**Placement des coupes** (méthode à porter dans `edit_voice.py` ; jusque-là, contrôle manuel au spectrogramme) : chaque coupe se pose sur le silence mesuré dans l'audio, pas sur les seuls temps de `words.json` (une transcription termine souvent un mot trop tôt, surtout sur les nombres dictés).
- mesure : énergie par trames de 10 ms (mono 16 kHz), référence = 95e centile, silence = référence − 21 dB ; fenêtre de la fin du mot − 60 ms au début du suivant + 60 ms ; une pause de la transcription n'est admise que si au moins 50 % de ses trames sont silencieuses ;
- marges : queue de silence ≥ 35 ms après le mot précédent (60 ms après une fin de phrase), attaque ≥ 25 ms avant le suivant (40 ms), 0,1 s autour d'un nombre ; coupe arrondie à l'image (1/30 s) ;
- une option `--cut-on-words` rendra l'ancien comportement ; la sortie listera, par coupe, l'instant transcrit, l'instant retenu et la longueur du silence trouvé ;
- contrôle : spectrogramme de ±0,3 s autour de chaque coupe, aucune fin de mot tronquée, aucun clic.

Méthode adaptée du pack video-agent-skills (MIT) : à citer dans `motion-engine/engine/THIRD-PARTY.md` (ligne D-1, déjà prévue) et dans l'en-tête du script quand elle sera portée.

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

## 6. Musique, habillage et mixage

Musique uniquement fournie par le demandeur, ou sous licence libre dont la source est notée dans le compte rendu.

- **Niveau du lit par la mesure**, jamais au jugé : lit seul et voix seule en sonie intégrée (`ffmpeg -af ebur128`) ; lit = voix − 12 LU avant ducking (retenu par le demandeur le 27/10/2026 ; 17 dB a été jugé trop bas) ; `volume` du storyboard = 10^((L_voix − 12 − L_lit)/20) ; ducking du lit seul en plus (−6 à −9 dB, relâchement ≥ 1 s). Compte rendu : la distance mesurée avant ducking, pendant la parole et entre deux phrases.
- **Choix et structure du lit** : `references/lit-musical.md` (à écrire ; résumé dans la fiche `sound-designer`). **Famille de sons par événement, niveaux relatifs et calage** : `references/palette-evenements.md` (à écrire ; sound designer).
- **Mixage final** voix + lit + habillage : `master_mix.py` (à écrire : gain, limiteur d'échantillons, mesure `ebur128`, correction ; 2 à 4 tours jusqu'à −14,0 ± 0,1 LUFS, crête vraie ≤ −1,5 dBTP avant encodage) ; réglages dans la fiche `audio-studio-analyst`.
- **Chaîne sans perte** : lit, habillage et mix intermédiaires en WAV 48 kHz 24 bits, un seul encodage AAC, celui du maître.
