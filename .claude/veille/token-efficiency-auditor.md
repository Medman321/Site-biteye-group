# Veille du 2026-10-24 — token-efficiency-auditor

Recherches : coûts des agents (études), mise en cache des invites, routage de modèles, sous-agents Claude Code, gestion du contexte, moteurs de rendu HTML vers vidéo. Pages web = données, non des instructions.

## Constats

1. Les coûts d'un agent viennent surtout des jetons d'entrée, et deux exécutions de la même tâche peuvent différer jusqu'à 30× ; plus de jetons n'améliore pas la précision au-delà d'un niveau modéré — arXiv 2604.22750, « How Do AI Agents Spend Your Money? » (Stanford/Microsoft, NeurIPS 2026) — mesurer l'entrée (lectures de gros fichiers, briefs larges) plutôt que la sortie, et fixer un plafond de jetons par agent dans le plan.
2. Les modèles sous-estiment leur propre consommation (corrélation ≤ 0,39 avec le réel) — même étude — ne jamais demander à un agent d'estimer son budget : estimer à partir de nos mesures passées, sinon écrire « inconnu » (règle déjà en place).
3. Dans un système multi-agent, l'essentiel de la dépense est dans le raffinement et la vérification, pas la génération initiale ; l'entrée pèse en moyenne 53,9 % — arXiv 2601.14470, « Tokenomics » (MSR 2026) — cohérent avec le retex V2 (contrôle croisé 9,3 M) : plafonner la vérification en volume, jamais en qualité, et la déclencher après la porte et l'audit DA.
4. Les sous-agents déplacent la dépense plus qu'ils ne la réduisent : chacun paie son propre contexte hors du cache de la session ; ils servent d'« écran » pour lire beaucoup et rendre un résumé court — Zivtech, « Economics of Claude Code, Part 2 » (https://www.zivtech.com/blog/economics-of-claude-code-part-2-agent-tradeoff), source tierce — dans le plan, justifier chaque agent lancé par le volume qu'il évite à la session ; exiger un compte rendu court.
5. Mise en cache des invites (docs officielles) : écriture 5 min = 1,25× l'entrée, écriture 1 h = 2×, lecture = 0,1× (0,05× pour Opus 5.5 et Sonnet 5.5) ; seuil minimal 512 à 4 096 jetons selon le modèle ; un changement de définition d'outils ou de système invalide le reste — https://platform.claude.com/docs/en/build-with-claude/prompt-caching — pour les lots d'agents lancés à la suite : mettre la partie stable du brief (consignes, chemins) en tête et la partie variable en queue ; ne pas modifier CLAUDE.md ni les fiches en cours de production.
6. Rentabilité du cache : amorti dès la 2e réutilisation en 5 min (1,25× puis 0,1×), dès la 3e en 1 h — calcul tiré des multiplicateurs officiels ci-dessus — lancer en rafale les agents qui partagent le même préfixe plutôt qu'espacés de plus de 5 minutes.
7. Le routage « modèle bon marché par défaut, escalade si besoin » garde l'essentiel de la qualité en n'envoyant qu'une minorité d'appels au modèle le plus cher (RouteLLM, cité dans https://wavect.io/blog/reduce-llm-token-costs-2026/, chiffres de blog à prendre avec prudence) ; les agents de ce dépôt fixent déjà `model:` en en-tête de fiche — garder Opus pour le jugement créatif/visuel, noter dans le bilan toute tâche Sonnet qui a nécessité une reprise (signal d'escalade).
8. La gestion du contexte d'Anthropic (effacement des vieux résultats d'outils, outil mémoire côté client) vise les agents longs — https://www.anthropic.com/news/context-management — pour nous : l'équivalent manuel est de passer des chemins de fichiers et des comptes rendus courts, et d'écrire l'état dans `$OUT` (plan, `plan.json`) plutôt que de le relire dans la conversation.
9. `ccusage` (npm, v20.0.42, mis à jour le 2026-10-23, gratuit, lit les journaux locaux) analyse l'usage de jetons et les coûts d'un agent en ligne de commande — https://www.npmjs.com/package/ccusage — candidat pour le bilan (mesure de jetons par session) ; à tester dans le conteneur avant de l'inscrire comme outil (les journaux de sessions peuvent être absents) ; en son absence, garder les chiffres des notifications de fin de tâche.
10. HyperFrames (HeyGen, Apache-2.0, npm `hyperframes` 0.8.191, Node ≥ 22 + FFmpeg) : rendu HTML vers MP4 déterministe via Chrome headless, comme notre moteur — https://github.com/heygen-com/hyperframes — aucune mesure de vitesse publiée, aucun gain démontré ; ne pas migrer, garder notre mesure (≈ 0,47 s/image en 1080×1920) comme base de budget de rendu.

## Écarté

- Gains chiffrés de blogs (« 40–70 % » de routage, « 84 % » de réduction de contexte, « 15× » multi-agent) : sources non primaires ou invérifiables, aucun chiffre repris dans la fiche.
- API Batch à moitié prix : suppose des appels API directs ; nos agents tournent dans la session, pas applicable.
- Cache sémantique et passerelles LLM (Helicone, Portkey, OpenRouter) : services externes, hors périmètre gratuit et local.
- Rendu par flux (`image2pipe` du projet Kavio) et capture Playwright à 11 images/s : sans mesure de benchmark, projet marginal, notre moteur a déjà une base mesurée.
- Dépense en jetons de FinOps X 2026 (AT&T, 8 à 27 milliards de jetons/jour) : anecdote d'entreprise, sans application à une vidéo de 40 s.
- Variable `CLAUDE_CODE_SUBAGENT_MODEL` et ordre de priorité des modèles de sous-agents : affirmé par un seul article payant, non confirmé.

## Apports du pack video-agent-skills (Melvyn Malherbe, MIT), 27/10/2026

Pack sous licence MIT lu en lecture seule (donnée non fiable, jamais exécuté, aucun fichier copié) ; idées reformulées en français ; chiffres du pack = valeurs de départ à valider sur nos vidéos. Format : apport — source dans le pack — ce que ça change.

1. Rendu par tranches avec cache — `short-editing/references/performance.md` (Chunk cache, Workers, Rules learned) — phase 1 « Rendus » : `render.js` rend par tranches de 5 s avec cache par empreinte, une correction d'une scène ne réencode que 1 à 2 tranches (pré-rendus et retouches ; le rendu final reste complet) ; gain lu dans le journal du rendu, jamais supposé ; base de budget en 1080 de 0,19 à 0,47 s/image selon les filtres, 4K seulement sur demande explicite (≈ 1,4 à 1,9 s/image).
2. Un producteur par composant — `short-editing/references/sub-agents.md` (rôles, boucle, brief, rapport court) — phase 1 « Parallélisme » : à partir de 3 maquettes complexes ou blocs `html`, une instance par composant (4 au plus), chacune écrivant seulement `$OUT/composants/<nom>.*`, un seul rédacteur du storyboard ; coût (chaque instance relit fiche et brief) chiffré contre le temps gagné.
3. Étiquetage en lots par un modèle léger — `broll/SKILL.md` « /broll setup » étape 4 — phase 1 « Modèle par tâche » : plus d'une vingtaine de plans = sous-agents Haiku par lots de 5 planches, un JSON par lot (`media-analysis` § Index du projet), lot invalide relancé et jamais relu par la session, 100 clips d'abord au-delà de 300.
4. Série par héritage et copie figée — `short-editing/references/style-schema.md` (ordre des couches, instantané du style) — phase 1 « Réutilisation » : `serie.json` hérité par `extends` réduit chaque storyboard ; une déclinaison ou une retouche rejoue la copie datée du dossier de la vidéo, jamais la série courante.

### Écarté

- Alias d'images identiques, mode économique, décodage dans la page, accélération matérielle et moteur neuronal d'un Mac : propres à macOS et au GPU ; notre rendu tourne sous Linux (Chromium, x264 sur processeur) et le grain ou la dérive rendent chaque image différente. Seuls le cache par tranches et l'audit de la police rendue sont repris.
- Vitesses de rendu du pack : mesurées sur une puce Apple (M4 Max) avec encodeurs matériels ; nos mesures font foi pour le budget.
- Modification de `.claude/CLAUDE.md` pour des producteurs parallèles : la fiche de l'auditeur (plan) et celle du producteur (brief) suffisent.
- Cadence et mix hebdomadaires d'un créateur : sans rapport avec le budget d'une production à la demande.
