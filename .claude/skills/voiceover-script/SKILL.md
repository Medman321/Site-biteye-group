---
name: voiceover-script
description: Écrire le script d'une pub BitEye (darija algérienne ou français) à partir de données ou d'un brief, obtenir la voix (enregistrement du demandeur, voix off gratuite Piper, ou ElevenLabs en option) et préparer la musique. À utiliser quand une vidéo est demandée sans mémo vocal, ou quand le demandeur veut une voix professionnelle à la place de la sienne.
---

# Script et voix off

## 1. Écrire le script

Lis d'abord la fiche de voix du demandeur (Drive, `02_Bibliothèque/Voix du demandeur`, remplie par `conseiller-demande`) : ses mots, ses « ne dit jamais », sa façon d'ouvrir et de conclure, ses idées reçues du métier.

Structure d'une pub de 30 à 45 s (environ 2,3 mots par seconde en darija, 2,5 en français) :

| Temps | Rôle | Exemple (darija) |
|---|---|---|
| 0–5 s | Interpeller la cible | « Khouya, nta promoteur immobilier ? » |
| 5–10 s | Nommer le problème | « Les chantiers, les ventes, la paperasse… kolchi m'khalet ? » |
| 10–20 s | La solution, nommée | « VISION Workspace, la solution li tsiyri biha l'entreprise ta3ek. » |
| 20–32 s | 2 ou 3 preuves concrètes (données du demandeur) | « Ventes, avancement des lots, G50… f écran wa7ed. » |
| 32–40 s | Appel à l'action | « Demande ta démo 3la biteye-group.com. » |

- Une idée par phrase ; chaque phrase devient une scène.
- Les chiffres viennent du demandeur. Sans source, écris une formulation qualitative.
- Script en deux blocs. « À lire » : seulement les mots dits, une phrase par ligne de 4 à 15 mots (= un souffle) ; c'est ce que le demandeur enregistre et ce qu'on passe à `transcribe_local.py --text`. « Notes », repérées par numéro de ligne (« ligne 5 → carton : 12 lots »), plan, durée, leviers et « À remplir » avec les `{{chiffre client}}`.
- Jamais 3 lignes abstraites d'affilée : la 3e devient un exemple du métier (F3 du bloc C, G50, échéancier) ; longueurs variées (3 mots après 14) ; une seule personne en face, « tu » ou « vous » tenu jusqu'au bout.
- Durée = mots ÷ rythme mesuré (`words_per_s` d'une prise ; à défaut 2,3 mots/s en darija, 2,5 en français).
- Contrôle avant de montrer : accroche dite en 3 s au plus ; aucune ligne de plus de 4 s ; premier changement à l'écran avant 5 s ; un événement visuel (coupe, carton, punch-in) toutes les 4 à 5 s ; durée dans la cible. Lecture à voix haute : tout ce qu'on ne dirait pas à un associé est coupé.
- Avant d'envoyer le script au demandeur, passe d'humanisation de `creative-direction` §4 bis (mots-tics, formes toutes faites, rythme plat ; chiffres, noms et CTA inchangés) ; un mot que le demandeur emploie réellement n'est jamais remplacé.
- Donne le script au demandeur avec la vidéo, pour validation.

## 2. Obtenir la voix, par ordre de préférence

1. **Une vraie voix** : envoie le script au demandeur pour qu'il l'enregistre sur son téléphone (au calme, téléphone à 20 cm de la bouche, 2 prises). C'est gratuit et c'est la touche humaine la plus forte. Ensuite : `audio-studio` → `voice_studio.py`.
2. **Voix off gratuite** (français, arabe standard) : `audio-studio` → `voice_tts.py`, puis `voice_studio.py --preset chaude`.
3. **ElevenLabs** (payant, voix plus naturelles, multilingue) : seulement si le demandeur le veut. Procédure ci-dessous.

### ElevenLabs (option)

Outils (ToolSearch) : `select:mcp__ElevenLabs__creative_create_flow,mcp__ElevenLabs__creative_list_voices,mcp__ElevenLabs__creative_generate_speech,mcp__ElevenLabs__creative_get_flow_run_status`

1. `creative_create_flow`, puis `creative_list_voices` : choisis une voix masculine ou féminine chaleureuse, multilingue, adaptée au français et à l'arabe ; dis laquelle dans le compte rendu.
2. `creative_generate_speech` avec le script (laisse `generations_count` par défaut : deux prises).
3. Attends la fin avec `creative_get_flow_run_status`, télécharge la prise retenue dans `$OUT/src/voix.mp3` (`curl -sS -o`).
4. Minutage des mots : `audio-studio` → `transcribe_local.py --text` avec le script (gratuit).

Coût : chaque génération consomme des crédits. Une seule génération par script validé ; ne relance pas pour réessayer après un succès.

La darija écrite en lettres latines est mal prononcée par la synthèse : écris le script de la voix en arabe dialectal (écriture arabe) et garde la version latine pour les sous-titres (`captions.replace`).

## 3. Musique

Uniquement une musique fournie par le demandeur ou dont la licence est connue. Dans le storyboard : `"music": {"src": "src/musique.mp3", "volume": 0.10, "fadeOut": 2}`. Niveau du lit mesuré en sonie, jamais au jugé : lit seul = voix seule − 12 LU avant ducking (`audio-studio` §6, valeur retenue par le demandeur le 27/10/2026) ; le `volume` du storyboard se calcule depuis ces mesures (10^((L_voix − 12 − L_lit)/20)), le ducking s'ajoute ensuite. Le 0,10 de l'exemple ci-dessus n'est qu'une valeur de départ.
