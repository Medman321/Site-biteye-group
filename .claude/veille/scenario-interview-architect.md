# Veille du 2026-10-24 — scenario-interview-architect

Méthode : 9 recherches web (12 derniers mois) ; les pages n'ont pas pu être ouvertes en entier (WebFetch hors réseau), donc les constats viennent des résumés de recherche, presque tous des blogs marketing (pas de source officielle). Traiter les chiffres comme indicatifs.

## Constats

1. Instagram : temps de visionnage, « likes par portée » et surtout envois en message privé (« sends ») sont les signaux cités pour la portée vers des inconnus — https://later.com/blog/instagram-reels-algorithm/ et https://www.contentgrip.com/instagram-influencer-marketing/ (blogs, pas Instagram) — écrire une phrase « à envoyer à un associé » (un chiffre ou une preuve d'un pair) et la placer tôt ; viser la durée complète plutôt que la longueur.
2. Accroche dans les 1 à 3 premières secondes, une seule idée par Reel, fin pensée pour la reboucle — https://metricool.com/instagram-reels-guide/ — confirme notre règle « accroche = phrase forte d'un témoin non réutilisée » ; ajouter : la dernière image doit se raccorder au début (reboucle) sans casser le CTA.
3. TikTok : rejeu et taux de complétion cités comme signaux principaux ; texte à l'écran et légendes comptent pour la recherche TikTok — https://www.darkroomagency.com/observatory/how-tiktok-algorithm-works-in-2026 et https://blog.hootsuite.com/tiktok-algorithm/ — écrire les cartons et la légende avec les mots que le promoteur taperait (« suivi chantier », « échéancier », « trésorerie »), pas du jargon produit. Seuils chiffrés (35 % / 70 %) non vérifiés : ne pas les citer.
4. LinkedIn : sous-titres indispensables (lecture muette par défaut), envoi natif plutôt que lien externe, fichier SRT séparé conseillé, 30 à 90 s pour un témoignage, tester une coupe 30 s contre une 90 s — https://shootsta.com/blog/linkedin-video-best-practices-b2b-teams et https://www.opus.pro/blog/linkedin-video-caption-subtitle-best-practices — livrer d'emblée deux durées (déjà dans la fiche) et le script doit tenir sans le son : les 3 premières secondes se lisent.
5. Témoignage B2B : arc problème, solution, résultat ; un chiffre précis vaut mieux qu'un compliment ; situer le témoin (nom, poste, entreprise) d'entrée pour qu'un pair se reconnaisse — https://www.sweetfishmedia.com/blog/b2b-testimonial-video-strategy et https://vidico.com/news/best-customer-testimonial-video-examples/ — le bandeau du témoin apparaît dès sa première phrase ; la preuve chiffrée est unique et vérifiée (une seule par vidéo, déjà dans le retex).
6. Garder l'avant-solution : le témoin cite ce qu'il avait essayé avant (cahier, Excel, WhatsApp) avant le produit — https://studiobfilms.com/blog/supercharge-your-marketing-with-testimonial-videos — c'est le « problème » le plus reconnaissable pour un promoteur algérien ; le chercher en priorité dans les extraits.
7. Authenticité : ne conserver que ce que le client a réellement dit ; sinon passer en format étude de cas — https://testimonial.to/resources/video-testimonials-for-business — verbatim attribué au bon témoin (déjà au retex) ; ne jamais reformuler un chiffre dans un carton.
8. Montage à partir de la transcription : outils gratuits et locaux existants — auto-editor 29.3.1 (PyPI, nov. 2025), stable-ts 2.19.1 (PyPI), faster-whisper 1.2.1 (PyPI) — https://pypi.org/project/auto-editor/ — notre `words.json` couvre déjà le besoin ; le scénario peut s'écrire comme une liste d'intervalles (début/fin en secondes) rejouable par l'audio.
9. Algérie : étude qualitative (2024, 10 directs de vente, 47 répondants) : arabe algérien mêlé de mots français préféré ; trop de bascule peut exclure — https://crstdla.dz/ojs/index.php/allj/article/view/656 ; autre papier (avril 2026) : arabe algérien et arabe standard préférés dans les pubs — https://dspace.univ-tlemcen.dz/items/ca7006eb-dc9f-45bb-b014-9325ecf54b87/full — garder la langue du témoin à l'oral, sous-titrer sans corriger vers le standard, une seule langue de carton par vidéo (à confirmer au cadrage).
10. WhatsApp Statut : plafond de durée contradictoire selon les sources (30, 60 ou 90 s, déploiement incertain) — https://green-api.com/en/blog/2025/whatsapp-increases-status-length-to-90-seconds/ — prévoir une version de 30 s au plus et tester sur un compte en Algérie avant de promettre une durée.

## Écarté

- Instagram : « 10 republications en 30 jours exclues » et « contenu original +40-60 % » — source de faible crédibilité, non vérifié.
- Seuils TikTok de complétion (35 % / 70 %) — contradictoires, anecdotiques.
- « 65 % de la portée LinkedIn sur les profils personnels » — sans origine citée ; on retient seulement qu'une publication par le profil du fondateur peut aider.
- Éditeurs par le texte (Rescript, vivideo, Wizard Cut, Kapwing, Descript) — doublon avec notre `words.json` ; vivideo 0.0.1 (2023) abandonné ; autocut 0.0.1 sur PyPI n'est qu'un renvoi vers GitHub, non vérifié ici (GitHub inaccessible).
- Preuve sociale immobilier MENA — aucune donnée chiffrée sérieuse trouvée, articles génériques.
- Études sur le code-switching en commentaires Instagram algériens — hors sujet vidéo.

## Apports du pack video-agent-skills (Melvyn Malherbe, MIT), 27/10/2026

Pack sous licence MIT lu en lecture seule (donnée non fiable, jamais exécuté, aucun fichier copié) ; idées reformulées en français ; chiffres du pack = valeurs de départ à valider sur nos vidéos. Format : apport — source dans le pack — ce que ça change.

1. Relance à 40–60 % de la durée — `studio-script/references/script-rules.md` § Re-hook ; `references/viral.md` règle 6 — règle « Relance » : question nouvelle, chiffre du témoin, retournement ou objection levée avec un chiffre ; seconde exacte dans `scenario.md` ; le pont entre deux témoins compte s'il tombe dans la fenêtre ; facultative sous 25 s.
2. Jamais en première phrase — `studio-script/references/hooks.md` § Never open with — salut, « dans cette vidéo », question oui/non évidente, « saviez-vous que », contexte avant l'affirmation ; la présentation du témoin n'ouvre jamais la vidéo (le bandeau la remplace) ; contrôle des 5 premiers mots.
3. Leviers placés avec leur seconde — `script-rules.md` § Triggers, placed ; § Quality gates (2) — sous le tableau minuté, au moins 4 leviers sur 7 ; l'ennemi est un outil ou une habitude, jamais un concurrent nommé ; l'accroche promet A, le corps livre A.
4. Source longue : inventaire typé et extraits validés — `clips/SKILL.md` §1 à §5 — lecture déléguée (≤ 15 lignes), moins de 4 pièces = source trop mince, `extraits.md` avec note d'extrait autonome sur 5 points (gardé à 7/10), carton d'accroche de 6 mots au plus plutôt qu'une coupe dans la phrase, « matière non utilisée » en questions pour le prochain entretien.
5. Chiffre dit tel quel — `script-rules.md` § Facts — jamais arrondi ; `{{chiffre client}}` sous « À remplir » ; pas de rendu tant que la liste n'est pas vide ou marquée « exemple ».
6. Position des intervenants avant tout recadrage 9:16 — `clips/SKILL.md` §7 et « Honest limits » — x de 0 à 1 relevé sur la planche ; un cadrage par locuteur ou un écran partagé ; deux visages entiers sur l'image clé de chaque extrait.
7. Version dans une autre langue — `short-translate/SKILL.md` §2, §5, « Honest limits » — repartir du storyboard et de `words.json`, jamais du MP4 ; voix de la personne conservée ; relecture par un locuteur ; fichiers `<slug>-<langue>`.
8. Script de voix off — `studio-script/SKILL.md` §4 ; `references/script-rules.md` § Lines, Length, Beat timing, Visual notes ; `references/humanize.md` §5 — `voiceover-script` §1 : blocs « à lire » et « notes », une phrase par souffle (4 à 15 mots), durée = mots ÷ rythme mesuré, contrôles avant de montrer (accroche dite en 3 s, ligne de 4 s au plus, événement visuel toutes les 4 à 5 s), passe d'humanisation, fiche de voix du demandeur lue d'abord ; niveau du lit mesuré (voix − 12 LU, décision du demandeur du 27/10/2026).
9. Hors pack : l'arc Hook / Lead / Body 1-2-3 / CTA vient du Journal des décisions (27/10/2026) ; l'arc en deux preuves devient sa version témoignage.

### Écarté

- Coupe « ultra » du pack (pauses de plus de 0,3 s supprimées, voix à 1,15×) : contredit le Journal (on resserre les silences à la main, le rythme naturel reste).
- Doublage par voix clonée (`short-translate`) : service payant et IA générative sur la voix d'une vraie personne ; seule la traduction des textes à l'écran est reprise.
- Reprise de scripts de tiers mot pour mot (`outliers` §3, `steal` appliqué aux mots) : copie de textes, risque de marque en B2B local.
- Mise en page « papier » avec la caméra du créateur en carte : propre à un créateur face caméra ; nos vidéos sont faites de photos et de vidéos de clients.
