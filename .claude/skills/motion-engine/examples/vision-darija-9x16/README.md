# Exemple : pub VISION Workspace en darija (9:16, 41 s)

Première pub produite avec ce moteur, à partir d'un mémo vocal de 38 s.

- `storyboard.json` — scènes et blocs minutés sur la voix.
- `words.json` — transcription ElevenLabs mot à mot (57 mots).
- `voix.mp3` — non versionné : déposer le mémo vocal ici pour reconstruire la vidéo.

```
python3 -I ../../scripts/build.py storyboard.json --out /tmp/pub
node ../../scripts/render.js /tmp/pub/pub-vision-workspace.local.html --mp4 /tmp/pub/pub-vision-workspace.mp4
```
