# Retour d'expérience : outil d'audit des transitions (novembre 2026)

Aucune vidéo livrée depuis la V3 premium du 24/10. Ce retex reprend ce qu'un vrai pré-rendu de la série a révélé sur `transitions/scripts/transition_audit.py` (corrigé par la PR #35 du 19/11/2026). Aucune donnée client ici.

## Ce qui s'est passé

1. Une transition d'ouverture (`zoomPunch` à `cut: 0.0` sur la première scène) faisait planter `cuts -v` (`KeyError`). Sans `-v`, elle sortait en `À REVOIR` « coupe hors de la vidéo », un faux défaut.
2. La grammaire de la série demande une ouverture vivante, mais l'outil ne savait pas la mesurer. Il y a maintenant `--open` : flux optique moyen des images 1 à 5 ≥ 0,8 px/img en 270×480, avec `--open-band y0,y1` parce que les voiles et textes fixes diluent la moyenne.
3. Un voile clair fixe apparu en fondu pendant t−20…t−6 gonflait la netteté de référence : 589 au lieu de ≈ 430 sur le plan voilé. Un saut visible passait donc pour masqué (t−1 lu à 44 % au lieu de 61 %), et le voile comptait comme une rampe de flou (sur une vidéo de test : rampe lue 10 images, réelle 2). La référence est désormais la plus basse de la médiane t−20…t−6 et de la médiane des images calmes t−8…t−6.

## Leçons par rôle

- **concepteur-transitions** : mesurer l'ouverture avec `--open` (et `--open-band` dès qu'un voile ou un texte fixe couvre l'image) ; une ligne `OUVERTURE` n'est pas un défaut mais une mesure à faire à part ; en `-v`, comparer les deux références de netteté : si elles divergent nettement, un calque fixe (voile, dégradé, texte) est apparu dans la fenêtre et la rampe doit être relue sur la planche.
- **art-direction-design-critic** : un voile ou un dégradé qui apparaît juste avant une coupe peut tromper les mesures ; le poser après la coupe ou au moins 20 images avant ; seuil d'ouverture vivante à donner avec les autres seuils avant le pré-rendu.
- **motion-video-producer** : éviter d'animer l'opacité d'un calque fixe pleine image dans les 20 images avant une coupe ; une transition sur la première scène se déclare avec `cut: 0` et se contrôle avec `--open`.
- **quality-brand-inspector** : sur le rendu final, relancer `transition_audit.py cuts … --open` ; une ouverture sous 0,8 px/img est à reprendre.
- **motion-3d-artist** : la caméra vivante doit se voir dès l'image 1 (≥ 0,8 px/img mesuré), pas seulement après l'ouverture.
- **token-efficiency-auditor** : le contrôle d'outil se teste sur une vidéo synthétique ffmpeg en CI (étape « Audit des transitions ») plutôt que sur un pré-rendu client ; aucune reprise de rendu nécessaire pour valider un correctif d'outil.
- **Autres rôles** : rien de nouveau depuis le retex V2/V3 (`2026-10-temoignage-v2.md`).
