# Retour d'expérience — vidéo témoignage V2 (octobre 2026)

Reel 9:16 de 39,8 s, deux témoins filmés dans deux lieux (anciens montages BitEye comme sources), effets 2.5D « magazine ». Verdict final : livrable. Ce document est lu par chaque agent lors de la mise à jour de son expertise ; chaque section dit ce que le rôle doit retenir.

## Ce que le demandeur a reproché, dans l'ordre

1. V1 : alternance brutale entre les deux témoins, cadre carré visible, vert de charte sans rapport avec les images, accroche faible, CTA inadapté.
2. V2 : flou autour des visages trop marqué → il veut du subtil.
3. Visage de Zahira « qui se coupe » entre 9 et 14 s (vu par le demandeur, pas par nos contrôles).
4. Pas d'animation visible entre les personnes et leur fond (les plafonds « subtil » les avaient rendues invisibles).
5. Les mots « magazine » n'étaient pas vraiment derrière les têtes.

## Leçons par rôle

- **scenario-interview-architect** : un seul passage d'un témoin à l'autre, avec un pont de sens ; accroche = phrase forte d'un témoin non réutilisée ensuite ; demander au cadrage si un nom de produit cité (ex. « Vision Pro ») peut rester, avant toute coupe.
- **audio-studio-analyst** : la coupe « Vision Pro » a été faite puis défaite (+105 k jetons) ; toujours garder une sauvegarde de l'état précédent et un plan de montage rejouable (`plan.json`) ; prolonger une nappe par fondu enchaîné sur une zone stationnaire ; vérifier le dernier coup du jingle après le ducking.
- **market-strategy-director** : données en banque, une seule preuve chiffrée par vidéo, selon le contexte ; « Chaque échéance, à temps. » interdit ; citations verbatim attribuées au bon témoin ; « 99 % » seulement adossé à du concret.
- **art-direction-design-critic** : ne jamais demander « plus » d'un effet sans planche de 3 niveaux (le DA avait demandé plus de flou, le demandeur voulait moins) ; un effet « subtil » garde un plancher de visibilité ; auditer aux bornes de chaque calque détouré, pas à heures fixes ; vérifier que le texte « derrière la tête » l'est vraiment.
- **vfx-roto-compositing-engineer** : détourer sur la plaque finale elle-même (même grille d'images : les sources contenaient des images doublées) ; détourage pleine hauteur (un plafond à 220 px coupait le crâne) ; plages exactes (un sujet décalé d'1 s a coupé le visage) ; repérer les coupes sèches des anciens montages et les traiter par changement d'échelle alterné ; une incrustation d'origine ne doit pas être tronquée par un recadrage.
- **motion-video-producer** : préchauffer la page avant l'image 0 (elle sortait sans vidéo) ; un calque ne s'affiche pas avant son début ; retirer du storyboard toute version remplacée ; mots « magazine » cachés à 25–40 % par la tête, lisibles ; rendu ≈ 0,47 s/image en 1080×1920.
- **quality-brand-inspector** : un contrôle qualité unique, ciblé sur les défauts connus, a suffi (0,2 M jetons) ; le contrôle croisé à 104 agents a coûté 9,3 M ; contrôler l'alignement sujet/plaque image par image autour de chaque raccord.
- **token-efficiency-auditor** : appliquer les règles « Efficacité » de `.claude/CLAUDE.md` (porte avant rendu, contrôle croisé plafonné, goût tranché sur planche).
- **chief-editor-monteur** : l'animatic a été sauté ; il aurait montré les coupes sèches de la source et le visage coupé avant tout rendu.
- **image-restoration-engineer** : non lancé ; sources = anciens montages compressés avec images doublées et incrustations ; à évaluer au prochain projet similaire.
- **colorist** : couleurs tirées des vidéos (ambre/miel, champagne/perle) ; le vert venait de décors translucides posés sur le fond bleu du thème ; règle R ≥ G + 12 pour nos calques seulement.
- **sound-designer** : jingle extrait de la source, confirmé par le client ; nappe synthétisée accordée sur le jingle ; licence à confirmer pour toute musique d'origine inconnue.
- **motion-3d-artist** : l'effet « couverture de magazine » (grand mot posé sur le fond, partiellement caché par la tête) a convaincu ; parallaxe lente (12–30 px/s) et ombre douce de la tête (≤ 0,20) ; un mot ne doit jamais flotter au-dessus de la tête.
