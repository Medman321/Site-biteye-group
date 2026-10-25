# Banque de hooks

Provenance : veille de 5 outils du marché (générateurs de scripts, bibliothèques et fichiers de hooks vendus), oct. 2026. Seuls des principes génériques, reformulés par nous : aucune phrase, aucun clip, aucune sélection d'un éditeur. Ce sont des recettes internes, pas des techniques mesurées sur une vidéo : à valider sur planche (3 niveaux, 2 images clés) avant de les promettre.

**Règles**
- Rien d'inventé : chiffre, nom, témoignage et actualité viennent du client, de la banque de `biteye-brand` ou d'une source datée ; sinon la phrase est marquée « exemple ».
- Aucune promesse de vues ni de résultat (« 1 million de vues », « devenez viral »). Le succès se juge aux demandes de démo. Les chiffres des vendeurs (vidéos « analysées », hausse de rétention) ne servent jamais de repère.
- Promesse tenue : la question ou la boucle ouverte par le hook trouve sa réponse avant le CTA, sinon c'est du racolage.
- Hook lié au métier : jamais un clip tiers sans rapport (satisfaisant, raté, ASMR) collé avant la vidéo. Aucun clip, son ou gabarit d'un pack de hooks : droits inconnus, retrait d'annonce possible. On reconstruit le principe avec le moteur.
- Un seul mouvement principal dans les 1,5 premières secondes (`creative-direction` §4).

**Mécanismes** (classification de travail BitEye, pour comparer des hooks de formes différentes) : *curiosité* (une question qu'on veut voir refermée), *pertinence* (le promoteur se reconnaît), *rupture* (une attente cassée : image, phrase ou structure), *émotion* (agacement vécu, soulagement). Les formules en place s'y rattachent :
- curiosité : question qui pique (`creative-direction` §1), paradoxe et question-accusation (Accroche), promesse de curiosité (n° 2), liste annoncée et numérotée (n° 10) ;
- pertinence : interpellation en darija, scène vraie du quotidien (§1) ;
- rupture : avant/après (§1, fenêtre téléphone), « X ≠ Y », flash à l'image 0 + `slam` (§1) ;
- émotion : douleur concrète chiffrée, chiffre surprenant (§1).

**Catégories verbales en plus**

| Catégorie | Mécanisme | Formule (nos mots) | Exemple VISION Workspace | Requis | À éviter |
|---|---|---|---|---|---|
| Preuve par un pair | pertinence | le résultat dit par un promoteur identifiable, dès sa première phrase | la phrase forte du témoin (agent 1), bandeau nom + poste | témoin réel filmé, accord, verbatim ; une seule preuve chiffrée | « les experts disent », témoin fictif, titre gonflé |
| Erreur qui coûte | émotion | l'erreur faite sans le savoir, puis ce qu'elle coûte | « L'erreur qui coûte cher en fin de chantier : découvrir un retard de paiement le jour des clés. » | rien, sauf un coût chiffré (chiffre client) | peur gratuite ; viser un concurrent ou un client |
| Boucle refermée | curiosité | annoncer un changement sans le nommer, le montrer plus loin | « Ce que votre chef de chantier n'aura plus à faire lundi matin. » → le message WhatsApp (`chat`) devient l'écran `app` | la réponse est dans la vidéo, avant le CTA | réponse absente ou après le CTA |
| Actualité → conséquence | pertinence | un fait du secteur daté, puis ce qu'il change pour le promoteur | « [fait daté] : ce que ça change pour votre échéancier. » | fait sourcé, vérifié la semaine de publication | lecture juridique ; actualité périmée |

Médias : la preuve par un pair, la scène filmée et l'avant/après réel exigent des images du demandeur (aucune image IA de personnes, chantiers ou bureaux). Erreur qui coûte, boucle refermée, actualité, question et liste se font avec le moteur seul (maquettes « Données fictives »).
Structures qui vont avec (la table de référence reste `creative-direction` §5 et l'agent 3) : question d'acquéreur (« Mon F3, il en est où ? ») → réponse montrée dans `phone` → CTA ; actualité → conséquence → module → CTA.

**Hooks visuels** — déjà en place : flash à l'image 0 + `slam` ou `punch` (§1), plongée dans le mot qui fait mal (`zoomThrough`, grammaire R5), mouvement vers la caméra + texte géant (n° 1), avant/après en fenêtre téléphone, whip calé sur un geste (n° 3). En plus :
- **Les pièces tombent en place** : `anim: "drop"` (chute avec dépassement, 0,55 s) sur des cartes de lots, pastilles de statut ou pages d'échéancier, dans une maquette ; creux sonore de 0,5 s puis impact quand tout est posé. Exemple : les lots d'un bloc tombent dans l'échéancier, le dernier passe « réservé ». Rebond physique et poussière : bloc à développer, à ne pas promettre. Jamais en photoréalisme sur une photo de client : fond neutre, maquette ou élément vectoriel.
- **La silhouette ouvre l'écran** : `maskReveal` depuis la silhouette détourée de l'intervenant (agent 5), `ease` `area`. Exige une vidéo réelle de l'intervenant.
- Pistes non testées (ne pas promettre) : hook qui est lui-même la transition A → B (R5 garde le mot lisible 0,6 s avant la plongée, donc B arrive vers 1,15 s : à trancher sur planche) ; raccord de forme entre objets (classeur → tablette : `matchCut` ne prend que des visages, donc `zoomPunch` aligné à la main) ; ouverture par le résultat puis retour en arrière (pas de lecture inversée dans le moteur).

**Au concept** (agent 3) : 3 hooks de 3 catégories différentes par concept, notés de 0 à 2 sur 5 critères : lisible sans le son à l'image 0 ; spécifique (métier, lieu, chiffre du client) ; une idée en 8 mots au plus ; promesse tenue par la suite ; donnée et médias disponibles. Le mieux noté (sur 10) est recommandé, les 2 autres vont en alternatives ; le concept affiche « catégorie — mécanisme ».

**Après publication** : l'agent 3 note dans le Drive (`Suivi des demandes vidéo`) la catégorie et le mécanisme du hook, à côté des demandes de démo et des chiffres que le demandeur relève dans ses statistiques (noms des métriques à vérifier dans l'appli). Journal indicatif : aucune conclusion avant plusieurs dizaines de vidéos ; jamais dans ce dépôt. Deux ouvertures du même montage : seulement à la demande, coût annoncé (second rendu, second contrôle) ; par défaut, on compare d'une vidéo à l'autre.
