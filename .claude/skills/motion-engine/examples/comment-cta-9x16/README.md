# Exemple : CTA par commentaire (9:16, 6 s, sans média)

Montre le bloc `commentCta` (moteur V4) : sur le dernier plan d'un témoin (visage simulé par un dégradé et une silhouette générés par ffmpeg), une feuille de commentaires neutre monte depuis le bas, le mot-code « FORMATION 1 » se tape lettre par lettre, « Publier » est touché, le commentaire apparaît (compteur 12 → 13, cœur), puis la bannière de la réponse automatique tombe du haut avec le début du lien WhatsApp. La feuille redescend et un `whip` mène à l'écran final avec le CTA WhatsApp unique.

| τ (s depuis `at` = 0,2) | Ce qu'on voit |
|---|---|
| 0,00 | la feuille monte (ressort critique, 0,35 s) ; les sous-titres remontent au-dessus d'elle |
| 0,40 | appui du curseur au bout du champ de saisie |
| 0,55 → 1,05 | « FORMATION 1 » tapé (0,05 s par signe), en couleur d'accent |
| 1,25 / 1,30 | appui sur « Publier » (−7 %) / le commentaire s'insère, compteur +1 |
| 1,50 | le cœur se remplit |
| 2,10 | bannière « BitEye @biteye_logiciels · maintenant » + texte de la réponse + lien |
| 3,20 → 3,46 | la feuille redescend, la bannière s'efface ; `whip` à 3,9 s |

Tout est dans la zone sûre « reels » du gabarit du DA (65 px sur les côtés, 250 px en haut, 400 px en bas) : `render.js --stills` le mesure (`hors_zone`, `taille_min` et `contraste_faible` vides).

```
ENG=../../scripts
python3 -I $ENG/build.py storyboard.json --out /tmp/cc
node $ENG/render.js /tmp/cc/exemple-comment-cta.local.html --stills /tmp/cc/stills --times 0.6,1.25,2.7,3.5 --contrast --fonts --scene-exits
node $ENG/render.js /tmp/cc/exemple-comment-cta.local.html --mp4 /tmp/cc/exemple-comment-cta.mp4 --maxrate 2M
```

Variantes : `"variant": "tiktok"` (avec `"safeZone": "tiktok"` dans l'en-tête : feuille dans 44 → 940 px, ligne « BitEye a aimé votre commentaire » à la place de la bannière, 3 s) ; `"variant": "sheet"` (feuille seule, LinkedIn ou statut) ; `"lang": "ar"` (libellés arabes, de droite à gauche, à faire relire).

Règles : **à proposer au demandeur** sur une planche de 3 niveaux (sobre : feuille seule ; moyen : + cœur ; complet : + bannière), **jamais d'office**, et seulement si la réponse automatique est active sur la plateforme du post. `reply` = texte exact de cette réponse (ici un exemple). La voix ne dit pas « commentez » : le mot-code passe par la légende et le commentaire épinglé ; le CTA écrit reste celui de l'écran final. Le témoin, la phrase et le nombre de commentaires sont fictifs. En production, l'écran final dure 3 à 4 s (phrase immobile 3 s, numéro lisible 2,5 s) : ici il est raccourci pour tenir en 6 s.
