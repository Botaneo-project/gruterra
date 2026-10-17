# TODO Gruterra

Ce fichier sert à garder une trace claire des idées et des prochaines étapes. Les éléments déjà en place sont conservés ici uniquement pour savoir où on en est, mais ils ne doivent plus être relancés sauf bug ou amélioration ciblée.

## Règle permanente — démo à maintenir avec chaque fonctionnalité

Toute nouvelle fonctionnalité ou modification visible inclut la vérification et, si nécessaire, l’actualisation de la démo dans le même lot : exemples fictifs adaptés, isolement des données/configurations, FR/EN et thèmes si concernés, aucune collecte réelle ni contribution. Voir `CONTRIBUTING.md`. Ne pas considérer le lot terminé si cette vérification manque ; documenter toute limite.

## Priorités consolidées — 10/10/2026

La release publiée reste **0.1.6-dev**. Les corrections présentes sur main depuis cette publication seront livrées ensemble dans une prochaine release ; aucun nouvel envoi Reddit ni annonce Discord effectué par cette relecture. Un seul TODO actif à la racine ; ROADMAP en est la vue publique courte. Les sections anciennes ci-dessous gardent la trace du travail et ne constituent pas une nouvelle liste prioritaire.

1. PC de secours et traductions : utilisation actuelle validée par l’utilisateur le 10/10/2026. Après la prochaine release, contrôler seulement les changements livrés depuis la 0.1.6-dev (redémarrage automatique et diagnostic de source).
2. Documentation et Discord : guides locaux remis à jour ; recharger le bot puis actualiser les tutos existants, sans reset, et contrôler avec une vue membre normale.
3. Relecture visuelle FR/EN, captures publiques et météo sur données réelles.
4. Restauration complète utilisateur : export déjà disponible ; parcours de restauration et chiffrement des sauvegardes privées restent à préparer.
5. Contributions au futur site : identité/clé locale préparées et testées, partage désactivé ; contrat, aperçu, consentement d’envoi, reçus et retrait restent à raccorder.

## Release 0.1.6-dev — 2026-10-09

- [x] Regrouper les traductions, drapeaux, paramètres défilants, historique, palette claire et parcours update dans une version de test.
- [x] Release v0.1.6-dev publiée avec archive officielle et SHA-256. Passage réel dans un dossier isolé avec l’updater 0.1.5 validé : données démo et préférences conservées.
- [x] Test fonctionnel utilisateur 0.1.5-dev → 0.1.6-dev réussi : refus de réinstallation identique, détection de la nouvelle version, sauvegarde créée, 115 fichiers installés, relancement OK, un seul bouton et message « Gruterra est à jour ».
- [x] PC de secours : validation globale de la version actuelle par l’utilisateur le 10/10/2026 ; aucun problème restant signalé. Conservation des données/préférences également vérifiée dans le test isolé.
- [x] Redémarrage automatique après succès : auxiliaire attendant la fin réelle de l’ancien processus avant de lancer une seule instance dans le même mode. Test Windows avec verrou réel réussi.
- [ ] Valider ce comportement côté utilisateur après installation de la prochaine release.
- [x] Source explicite : GitHub, local seul ou repli local en cas d’échec réseau. Pas de confirmation « à jour » en ligne en cas de repli, ni d’installation autorisée depuis un repli local. Tests FR/EN et priorité à GitHub sur un ancien manifeste 0.1.4-dev.
- [ ] Vérifier ces mentions sur le PC de secours avec et sans réseau après la prochaine release.
- Ne pas remanier davantage le parcours d’interface validé. Les deux points techniques ci-dessus restent à vérifier avant une diffusion plus large.

## Mise à jour — parcours progressif du 2026-10-09

- [x] Paramètres : Vérifier → Préparer → Appliquer. Si la version est à jour, aucune action d’installation ni confirmation d’archive.
- [x] Préparation : archive officielle, SHA-256, protections et sauvegarde locale ; aucun fichier remplacé. Application avec recontrôle et sauvegarde avant remplacement.
- [x] À propos renvoie aux Paramètres pour installer ; contrôles FR/EN et tests sur archives fictives.
- [x] Parcours validé par le test utilisateur de la 0.1.6-dev ; voir les deux vérifications techniques restantes dans la section release.

## Paramètres — 2026-10-09

- [x] Drapeaux France/Royaume-Uni dessinés localement à côté de Français/English, sans dépendre des emojis Windows.
- [x] Fenêtre redimensionnable avec défilement ; Enregistrer/Annuler et erreurs restent accessibles dans un pied fixe.

## Thèmes — 2026-10-09

- [x] Tous les boutons de navigation suivent la palette lors du passage clair/sombre, y compris Plantes, Données et synthèses et État Gruterra. Libellés FR : Mode clair / Mode sombre ; EN : Light mode / Dark mode.

## Historique — corrections de lisibilité du 2026-10-09

- [x] Sélection d’une date disponible depuis toutes les périodes, en FR/EN ; le choix ouvre la vue Journée.
- [x] Badges sortie/retour balcon et arrosage répartis sur plusieurs lignes sans chevauchement, avec fond lisible dans une fenêtre réduite.

## Traduction FR/EN — 2026-10-09

- [x] Grand lot de traduction : interface, paramètres, synchronisation PC/Raspberry, historique et cycles, fiches de besoins, Netatmo, sauvegardes et diagnostics de mise à jour.
- [x] Catalogue JSON FR/EN commun ; les textes des nouvelles fonctionnalités doivent être ajoutés dans les deux langues avec les mêmes paramètres de formatage.
- [x] Identifiants métier préservés : séries de mesures, filtres, état de santé et événements balcon continuent de fonctionner indépendamment de la langue affichée.
- [x] Contrôles automatisés des clés et paramètres FR/EN, calculs des cycles inchangés, sélection des séries et fiches botaniques ; lancement isolé de la démo FR puis EN, paramètres, À propos, historique et filtres.
- [x] Traductions de la version actuelle jugées satisfaisantes par l’utilisateur le 10/10/2026. Validation d’usage, sans prétendre à une relecture linguistique exhaustive ni au contrôle de tous les messages Raspberry. Les observations personnelles et anciennes notes restent dans leur langue d’origine.

## État des lieux urgent — 2026-10-05

Cette section sert de point d'entrée rapide après les grosses modifications récentes. Elle ne remplace pas les sections détaillées plus bas ; elle indique ce qu'il faut vérifier en premier si un agent reprend le dossier ou si un bug apparaît.

### À vérifier en priorité

- [x] Auto-update : test fonctionnel principal 0.1.5-dev → 0.1.6-dev réussi côté utilisateur. Fermeture/redémarrage automatiques et source du manifeste restent à vérifier (section release).
- [x] Traduction : validation d’usage utilisateur le 10/10/2026 ; corriger les nouveaux écarts s’ils sont signalés.
- [ ] Discord : vérifier que les messages socle et tutoriels sont épinglés, qu'ils ne sont pas supprimés par les commandes de clean, que `#bot-commands`, `#admin-notes` et `#dev-follow-up` restent privés, et que les salons FR/EN ont chacun leur message adapté.
- [ ] Raspberry : vérifier sur un cycle réel que les mesures annoncées comme rapatriées correspondent bien à des mesures nouvelles pour le PC, éventuellement collectées pendant que Gruterra était fermé.
- [ ] Démo publique : lancer `Lancer_Demo.py`, vérifier que la première impression est propre, que les captures publiques correspondent encore à l'interface actuelle et que le README ne promet rien qui n'est pas visible en démo.
- [x] Installation/utilisation sur PC de secours : validées globalement par l’utilisateur le 10/10/2026. Parcours documenté : télécharger → extraire → Installer_Gruterra.bat → Lancer_Demo.bat.
- [ ] GitHub public : relire la fiche README après chaque gros push pour éviter les promesses dépassées, les anciens noms Botaneo visibles hors contexte, ou une confusion entre projet francophone et accueil anglophone.

### Bugs / risques à surveiller

- [ ] Après chaque évolution structurante, mettre à jour le tutoriel GitHub de base : README, guide installation, guide démo si concerné, et notes de release.
- [ ] Les textes de synchronisation peuvent encore être trop verbeux ou ambigus quand une mesure est demandée au Raspberry mais récupérée seulement au passage suivant.
- [ ] Les imports Raspberry et historique Mi Flora doivent rester idempotents : relancer une synchro ne doit pas créer de doublons.
- [ ] Les mesures sans date exploitable doivent rester bloquées ou supprimées selon la règle actuelle, même si elles contiennent lumière, humidité ou conductivité.
- [ ] Les valeurs suspectes, notamment humidité 0 %, doivent être conservées en brut mais clairement exclues des statistiques quand elles sont jugées non exploitables.
- [ ] Les cycles d'arrosage doivent rester prudents : ne jamais conclure que toute la motte est sèche ou humide à partir de la seule zone mesurée par le Mi Flora.
- [ ] Les fichiers privés de reprise agent, secrets, bases réelles, captures temporaires, bot Discord local et configurations doivent rester hors GitHub public.

### Prochaine action recommandée

Voir les priorités consolidées du 10/10 en tête de fichier. Le test principal de l’update est réussi ; les contrôles utilisateur restants ne doivent pas être confondus avec une absence d’updater.

## État actuel déjà en place

- Dépôt GitHub renommé : `Botaneo-project/gruterra`; remote local mis à jour et description GitHub corrigée.

- Nom officiel du projet : Gruterra.
- Mémoire de compatibilité conservée avec l’ancien nom technique `botaneo` pour les fichiers, variables, services Raspberry et chemins existants.

- Interface graphique principale avec mode sombre et plusieurs teintes.
- Mode clair harmonisé avec une palette Gruterra plus douce et cohérente avec le mode sombre.
- Possibilité d’ajouter une plante depuis l’interface.
- Possibilité d’avoir une plante sans capteur actif.
- Affichage de l’état d’une plante : avec capteur, sans capteur, ancien capteur conservé.
- Préparation de l’association future d’un nouveau capteur Mi Flora à une plante existante.
- Mini base de plantes avec autocomplétion.
- Mini base enrichie avec plusieurs plantes d’intérieur courantes.
- Fiches de besoins de base déjà préparées pour certaines plantes, dont Crassula et Mammillaria.
- Saisie manuelle toujours possible si la plante n’existe pas dans la mini base.
- Mesures Mi Flora : humidité du sol, température du terreau, luminosité, conductivité, batterie.
- Historique Mi Flora conservé sans suppression volontaire des données.
- Historique brut Mi Flora conservé dans une table séparée avec protection anti-doublon.
- Ancienne archive locale de 119 entrées historiques reprise : 118 entrées uniques conservées.
- Bouton manuel `Importer historique Mi Flora` ajouté sur les plantes avec capteur actif.
- Raccourci historique ajouté : une plante sans mesures explique la situation et propose d’ouvrir une plante qui possède déjà un historique.
- Import historique manuel corrigé : historique pur, conservation partielle si Windows coupe la connexion.
- Synchronisation principale branchée sur l’import historique Mi Flora : historique d’abord, mesure directe ensuite.
- Affichage de la batterie Mi Flora avec seuil configurable.
- Arrosage manuel possible pour une plante, même sans capteur.
- Rappel d’arrosage programmable en nombre de jours.
- Base de données prête pour mémoriser les arrosages, rappels et besoins des plantes.
- Table de journal plante créée pour enregistrer les observations manuelles.
- Netatmo intégré dans l’interface avec distinction privé / public.
- Netatmo : favoris, renommage local, ordre d’affichage et données rares visibles quand disponibles.
- Netatmo : distinction entre valeur zéro réelle, donnée vide et donnée non remontée.
- Prévision météo locale à environ +2 h déjà préparée avec les coordonnées renseignées.
- Bloc météo locale déplaçable en haut de l’interface via les paramètres.
- Filtres simples sur les plantes : zone, pièce, avec capteur, sans capteur, à surveiller.
- Synchronisation automatique quotidienne validée : heure, jours, réarmement et date de dernière exécution.
- Protection contre deux synchronisations lancées exactement en même temps.
- README initial prévu pour préparer un futur dépôt GitHub.
- Mode démo ajouté pour tester Gruterra avec une base fictive, sans capteur, token ou données personnelles.
- Script `verifier_avant_github.py` ajouté pour contrôler les fichiers sensibles avant commit ou push.
- Script `audit_botaneo.py` ajouté pour lancer tests automatisés, vérification avant GitHub, contrôle du diff et affichage des fichiers modifiés en une commande.
- Tests ajoutés pour le script d’audit local afin de vérifier ses retours OK/échec et son comportement sans Git disponible.
- Documentation des tests ajoutée dans `tests/README.md` pour expliquer la couverture et les limites matérielles.
- Dépôt GitHub préparé pour publication publique et utilisé pour sauvegarder les évolutions validées.
- Statut de synchronisation copiable depuis l’interface.
- Synchronisation : sous-étapes détaillées pendant les phases longues.
- Lecture historique Mi Flora PC en plusieurs passes, sans effacement, avec reprise partielle et signalement des données manquantes.
- Synchronisation manuelle : récupération Raspberry en priorité, puis lecture Bluetooth PC de secours si aucune mesure fraîche ne remonte.
- Raspberry : collecte planifiée quatre fois par jour via `botaneo-collect.timer`.
- Raspberry : scripts d’installation et de mise à jour disponibles dans `raspberry/install/`.
- Écran historique enrichi avec résumé, tendance, repères post-arrosage et qualité des données.
- Historique : sélection d’une journée avec moyennes, minimums/maximums et pic lumineux du jour.
- Fenêtre `À propos` ajoutée : version locale, révision Git, chemins utiles, état Raspberry et rappel sécurité.
- Fenêtre `Santé système` enrichie avec un diagnostic Raspberry : température, disque libre, mémoire, sauvegardes locales, écriture et erreurs disque récentes.
- Document de reprise agent créé : `CONTEXTE_AGENT_BOTANEO.md` avec architecture, Raspberry, secrets, process GitHub, Plante de Jade et priorités.


## Audit technique — seconde passe

État après les dernières corrections : le schéma principal et les clés étrangères sont corrigés. Les prochains risques sont moins visibles que les bugs fonctionnels, mais ils conditionnent la stabilité future.

- [x] Schéma principal : `database.py` crée maintenant `plantes`, `capteurs`, `mesures` et les index utiles pour une installation neuve.
- [x] Clés étrangères SQLite activées dans `get_connection()`.
- [x] Créer le module dédié `_app/botaneo_dates.py` : date locale, UTC, parsing ISO, affichage local et comparaisons sûres.
- [x] Remplacer les conversions de dates critiques Raspberry/Mi Flora par `_app/botaneo_dates.py` pour les imports UTC, les dates locales PC et les mesures rapatriées.
- [x] Remplacer les conversions critiques de l’historique graphique par `_app/botaneo_dates.py` : points de courbe, tris, tableaux, qualité des données, repères arrosage et filtres de période.
- [ ] Continuer le remplacement progressif dans l’interface : rappels, alertes et exports texte.
- [ ] Auditer les dates Raspberry / PC / historique Mi Flora pour éviter les mélanges entre UTC, heure locale et ISO sans fuseau.
- [ ] Vérifier les threads Tkinter : aucun thread secondaire ne doit modifier directement un widget, tout doit repasser par `root.after(...)`.
- [x] Créer une première suite de tests automatisés pour les éléments purs : schéma base vide, suppression des mesures sans date, sessions d’arrosage et dates centralisées.
- [x] Étendre les tests automatisés aux zéros suspects : un 0 % isolé est conservé dans les données, mais exclu des graphiques/statistiques d’humidité.
- [x] Étendre les tests automatisés aux cycles d’arrosage simples : humidité avant, première mesure, pic, fin et vitesse de séchage.
- [x] Étendre les tests automatisés à l’import Raspberry : ajout d’une mesure courante et déduplication idempotente.
- [x] Étendre les tests aux cycles d’arrosage fractionnés simples : début de session, total 40 + 55 ml, mesures entre deux apports et cohérence temporelle.
- [x] Étendre les tests à l’historique Raspberry brut : trame Mi Flora valide, archive conservée, mesure exploitable ajoutée et déduplication idempotente.
- [ ] Étendre plus tard les tests à l’analyse séparée de chaque fraction d’une session.
- [x] Extraire une première partie de la logique d’arrosage vers `_app/services/analyse_arrosage.py` : cycles, sessions, texte d’analyse et résumé, avec tests de non-régression.
- [ ] Continuer plus tard l’extraction des autres morceaux d’analyse plante liés à l’arrosage si l’interface évolue.
- [x] Extraire une première partie de la logique lumière vers `_app/services/analyse_lumiere.py` : expositions balcon, filtrage par jour/période, séparation intérieur/balcon dans les résumés.
- [ ] Préparer progressivement la réduction de `interface.py` et `vue_historique.py`, sans découpage brutal de l’interface graphique.
- [x] Documenter clairement que la page web Raspberry en HTTP est acceptable uniquement sur réseau local privé et ne doit pas être exposée à Internet.
- [ ] Nettoyer les doublons et fichiers anciens seulement après stabilisation et vérification qu’ils ne servent plus de référence.

## Prochaine suite recommandée

- [x] Historique : ajouter une première fenêtre de comparaison de deux journées avec tableau et texte copiable.
- Historique : prochaine étape graphique, superposer deux journées sur la même échelle horaire.
- [x] Historique : ajouter une première fenêtre de résumé des cycles d’arrosage, avec réponse à l’eau et vitesse de séchage.
- [x] Historique : comparer deux cycles d’arrosage en tableau, avec hausse observée, séchage et texte copiable.
- [x] Historique : superposer deux cycles d’arrosage sur une même échelle temporelle, en humidité depuis l’arrosage.
- [x] Historique : ajouter le choix de mesure dans le graphique comparatif des cycles : humidité, lumière, température, conductivité.
- [x] Historique : ajouter les repères 24 h et 48 h dans le graphique comparatif des cycles.
- [x] Historique : améliorer la vue graphique des cycles avec repères visuels dédiés : arrosage, pic A/B, 24 h, 48 h, légende simple et moins de texte brut.
- [x] Historique : afficher les valeurs d’humidité proches de 24 h et 48 h dans la comparaison des cycles, sans inventer de valeur si aucune mesure proche n’existe.
- [x] État Gruterra : afficher un contrôle explicite des mesures et synthèses entièrement à zéro.
- [x] Analyse des cycles d’arrosage : version simple et prudente, centrée sur hausse observée, retour au départ et séchage après pic.
- [x] Pour chaque cycle : repérer l’humidité avant arrosage, le pic observé, la baisse après pic et la qualité des mesures disponibles.
- [x] Stabiliser l’analyse plante autour de l’arrosage : phrase courte, repères 10 min / 1 h / 24 h / 48 h et comparaison avant/après.
- [x] Historique : ajouter un bouton `Resynchroniser` pour relancer la synchronisation depuis l’écran historique.
- Garder le Bluetooth et la synchronisation Raspberry en observation pendant quelques cycles avant de modifier encore la collecte.
- Reprendre ensuite l’interface des alertes, sans envoyer de mails automatiquement.

## Priorité courte

### 1. Finaliser les alertes

- Terminer l’affichage clair de l’état batterie : OK, à surveiller, faible.
- Garder le seuil batterie modifiable dans les paramètres.
- Préparer les alertes par plante, sélectionnables depuis l’interface.
- Prévoir les rappels par e-mail pour les plantes sans capteur ou hors domicile.
- SMTP sécurisé local prévu comme piste principale ; Outlook local reste une option secondaire.
- Mémoire de dernière alerte préparée pour éviter un e-mail à chaque synchronisation.
- Délai minimal entre deux alertes identiques préparé en mode test.
- Ne pas envoyer d’e-mail automatiquement tant que le destinataire et les règles ne sont pas validés.

### 2. Améliorer l’interface quand il y aura beaucoup de plantes

- Prévoir une vue compacte pour éviter de devoir défiler si on a 30 à 50 plantes.
- Améliorer plus tard les filtres plantes si besoin : recherche par nom, tri manuel, regroupement par pièce.
- Zone de décision visible au-dessus des mesures : déjà en place, à affiner avec plus de données.
- Permettre à terme de choisir l’ordre des blocs : météo locale, plantes, alertes, graphiques.
- [x] Permettre de masquer les plantes sur l’accueil pour préparer une organisation par onglets ou sections dédiées.
- [x] Ajouter une vue dédiée `Plantes` accessible depuis la barre d’actions, utile quand les plantes sont masquées sur l’accueil.
- Historique enrichi avec résumé, tendance, repères post-arrosage et copie du résumé.

### 3. Fiches plantes et mini base

- Continuer à enrichir la mini base de plantes d’intérieur courantes.
- Ajouter progressivement les besoins de base : lumière, humidité du sol, température, arrosage indicatif.
- Transformer plus tard les besoins en vrais seuils exploitables par l’analyse.
- Prévoir une modification des fiches depuis l’interface.
- Prévoir plus tard des images de plantes, idéalement avec cache local pour éviter de dépendre du web à chaque affichage.

## Météo et Netatmo

- Garder les stations Netatmo favorites les plus utiles en haut.
- Permettre de renommer localement une station favorite de manière claire.
- Continuer à afficher les données rares quand elles existent : pluie, vent, rafales, direction, pression.
- Étudier plus tard l’affichage d’une carte Netatmo publique avec stations favorites.
- Prévoir une sélection locale des stations publiques utiles autour du domicile approximatif.
- Ajouter les prévisions météo surtout quand un capteur extérieur ou une station publique fiable est disponible.
- Garder la prévision +2 h comme donnée utile pour pluie, température, humidité, vent et rafales.
- Prévision +2 h : utiliser le code météo pour éviter `Ciel non disponible` quand la source le fournit.
- Ne pas intégrer de token Météo-France officiel tant que le portail ou le compte ne sont pas stables.


## Sessions d’arrosage à prévoir

Objectif : préparer une évolution sans casser l’enregistrement actuel des arrosages. Tant que cette partie n’est pas développée, le bouton d’arrosage doit continuer à enregistrer chaque apport comme aujourd’hui.

- [x] Regrouper logiquement plusieurs apports proches, par exemple 40 ml + 55 ml, en une session d’arrosage de 95 ml sans supprimer les deux lignes brutes.
- [x] Calculer automatiquement le volume total de la session, avec le détail des apports et de leurs horaires.
- [x] Conserver l’état du substrat au début de la session uniquement ; les compléments peuvent rester `non renseigné`.
- [x] Ajouter des champs facultatifs : arrosage progressif, eau utilisée, pot sorti du cache-pot, répartition de l’eau, drainage observé, délai avant drainage, commentaire libre.
- [x] Basculer l’analyse post-arrosage sur le début de session.
- [ ] Ajouter plus tard une vraie analyse séparée de la réaction à chaque fraction d’une session ; le regroupement logique de la session est maintenant couvert par test.
- [x] Ne plus afficher seulement `arrosage 55 ml` si cet apport appartient à une session totale de 95 ml.
- [x] Conserver les données originales en base : le regroupement est logique, pas une fusion destructive des lignes.
- [x] Garantir la cohérence temporelle : l’analyse post-arrosage part du début de session, une mesure antérieure à un complément n’est pas attribuée à ce complément.
- [ ] Continuer l’amélioration de la lumière contextualisée : comparaison de journées intérieur/balcon, future lampe horticole, interprétation plante.
- [ ] Conserver les indicateurs de qualité des données pour éviter que les périodes très denses faussent les moyennes.
- [x] Distinguer dans la synchronisation `synchronisation terminée` et `nouvelle mesure effectivement acquise`.
- [x] Répéter dans les analyses que le Mi Flora mesure une zone du substrat et ne prouve pas à lui seul l’état de toute la motte.

## Historique Mi Flora

- Garder la règle de sécurité : aucune suppression de mémoire Mi Flora sans validation claire.
- Continuer à surveiller les lectures partielles Windows BLE : les entrées déjà lues doivent rester conservées.
- Prévoir plus tard un mode `Importer historique long`, séparé de la synchronisation normale, avec plus de passes et une progression dédiée.
- Améliorer l’affichage de la source des mesures : Raspberry, PC direct, historique importé.
- Conserver les entrées douteuses à part plutôt que remplacer les mesures existantes.

## Analyse plante et prévisions 48-72 h

État actuel : la zone de décision existe déjà (`À faire aujourd’hui`, `À surveiller`, `Prévision 48-72 h`) et l’analyse post-arrosage commence à exploiter les mesures réelles. La suite doit rester prudente tant que l’historique n’est pas assez dense.

- [x] Ajouter une zone de décision en haut : `À faire aujourd’hui`, `À surveiller`, `Prévision 48-72 h`.
- [x] Ajouter une extraction texte pour partager les données utiles avec une discussion d’analyse plante.
- [x] Afficher des repères post-arrosage dans l’historique.
- [x] Améliorer le résumé post-arrosage avec le nombre de mesures, la durée de suivi et l’ancienneté de la dernière mesure.
- [x] Centre d’alertes : afficher le prochain arrosage et le dernier arrosage manuel pour les plantes sans capteur.
- [x] Centre d’alertes : afficher le délai lisible du prochain arrosage et préparer le rappel mail une semaine avant.
- [ ] Améliorer la phrase de synthèse globale, par exemple : `Votre Crassula devrait nécessiter une intervention dans les prochaines 24 h.`
- [ ] Calculer les tendances d’humidité du sol avec plus de recul.
- [x] Distinguer dans l’analyse des cycles la réponse à l’arrosage, la vitesse de séchage après pic et la tendance récente sur 24 h.
- [x] Construire une analyse par cycle d’arrosage : humidité initiale, réponse à l’arrosage, pic observé, phase de séchage, retour au niveau initial.
- [x] Reformuler l’analyse post-arrosage pour éviter de confondre zone du capteur et motte complète : `Retour au niveau d’humidité initial détecté dans la zone du capteur. Le Mi Flora ne permet pas de confirmer le séchage complet de la motte.`
- [x] Ajouter aux événements d’arrosage des champs facultatifs : volume total, type d’eau, méthode de répartition, écoulement observé, eau stagnante dans le cache-pot, état visuel du substrat et commentaire libre.
- [ ] Ne pas imposer automatiquement 80 ml : garder la comparabilité des cycles sans empêcher d’adapter l’arrosage aux besoins réels.
- [x] Calculer la vitesse moyenne de séchage en points d’humidité par jour entre le pic confirmé et la fin du cycle.
- [x] Ajouter une vitesse sur 24 h pour repérer un ralentissement ou une accélération du séchage.
- [x] Attribuer une qualité à chaque cycle selon les trous de mesure : bonne, correcte, prudence, interruption longue.
- [x] Enrichir chaque cycle avec une lecture courte : hausse après arrosage, écart final au départ et retour proche/partiel/persistant dans la zone du capteur.
- [x] Adapter les alertes d’humidité après un arrosage récent : afficher un suivi post-arrosage au lieu d’une alerte sèche classique.
- [x] Signaler dans le cycle si le pic ou la dernière mesure tombe après une interruption longue.
- [x] Ajouter une alerte de comparabilité des cycles selon les données disponibles : quantité d’eau, type d’eau et qualité des mesures.
- [ ] Étendre plus tard la comparabilité aux conditions non encore structurées : emplacement, lumière, température, substrat.
- [ ] Construire progressivement une référence propre à chaque plante après plusieurs cycles documentés.
- [ ] Estimer le prochain arrosage probable quand les données sont suffisantes.
- [ ] Détecter une baisse de luminosité sur plusieurs jours.
- [x] Ajouter les événements `Sortie sur le balcon` et `Retour à l’intérieur` dans le journal plante.
- [ ] Distinguer les journées entièrement en intérieur des journées avec exposition extérieure.
- [x] Calculer les durées d’exposition par plages de luminosité, au lieu de se limiter au maximum du jour.
- [x] Calculer une exposition lumineuse cumulée quotidienne en tenant compte des intervalles entre mesures.
- [x] Éviter qu’un pic lumineux ponctuel masque une journée globalement sombre grâce au cumul lux·h et aux durées par plage.
- [ ] Préparer la comparaison entre lumière naturelle extérieure ponctuelle et lampe horticole.
- [ ] Comparer la température actuelle avec la moyenne récente.
- [ ] Interpréter prudemment la conductivité, sans alerte trop agressive.
- [ ] Croiser les besoins de base de la plante avec les mesures réelles.

## Journal d’événements plante

- Garder l’historique des arrosages manuels.
- Ajouter plus tard d’autres événements depuis l’interface : observation, rempotage, déplacement, engrais, taille, changement de capteur.
- Afficher ces événements dans la fiche plante.
- Utiliser ces événements pour mieux interpréter les courbes.

## Installation, mises à jour et distribution

- [x] Prévoir un système d’auto-upgrade pour les utilisateurs ayant déjà téléchargé Gruterra.
- [x] Préparer un plan de protection avant mise à jour : base locale, configuration, secrets ignorés, sauvegardes et données runtime.
- [x] Distinguer dans le plan de mise à jour le programme et les données personnelles : base réelle, tokens, favoris, paramètres Raspberry, alertes.
- [x] Lister explicitement les éléments personnels à conserver pendant les mises à jour : données, configuration locale, favoris, secrets, sauvegardes et caches locaux.
- [x] Préparer dans le plan de mise à jour la séparation logique entre programme remplaçable et données utilisateur à préserver.
- [ ] Déplacer réellement plus tard les données utilisateur vers un dossier dédié, avec migration et sauvegarde.
- [x] Préparer le comparateur de versions pour un futur mode simple : version locale / version distante, sans application automatique.
- [x] Brancher la vérification distante GitHub via `version_manifest.json`, sans téléchargement ni application automatique.
- [x] Ajouter un script public `update_gruterra.py` de validation non destructive, utilisable sans Git.
- [x] Étendre `update_gruterra.py` avec `--dry-run` et `--apply`, archive officielle, contrôle SHA256 et sauvegarde avant remplacement.
- [x] Ajouter un guide public d'installation depuis une release ZIP, avec lancement démo, lancement principal et rappel des données privées à préserver.
- [x] Planifier les tutoriels publics Discord et Reddit : parcours démo, installation ZIP, message court, post Reddit et ordre conseillé avant publication.
- [ ] Publier une première release ZIP officielle avec SHA256 pour activer réellement --apply.
- [x] Préparer un script Windows `update_gruterra.py` avec simulation, application contrôlée, SHA256 obligatoire et sauvegarde locale.
- [ ] Prévoir plus tard l’équivalent Raspberry complet côté `raspberry/install/`.
- [x] Afficher dans `À propos` la version locale, la révision Git et le résumé du plan de protection avant mise à jour.
- [x] Ajouter une vérification préparatoire du plan de mise à jour : prêt, prudence ou bloqué selon la présence de la base, de la configuration et des sauvegardes locales.
- [x] Afficher un résumé court et lisible du plan de mise à jour dans `À propos`, sans noms de fichiers secrets et sans activation automatique.
- [x] Préparer une lecture de manifeste de version local pour tester la comparaison de versions avant le branchement GitHub réel.
- [x] Ajouter un exemple public `version_manifest.example.json` et publier un manifeste public `version_manifest.json` sans secret.
- [x] Afficher dans `À propos` les notes et le lien informatif du manifeste local quand ils existent, sans action automatique.
- [x] Préparer un diagnostic structuré de mise à jour : état global, protections, version, blocages, éléments détectés et prochaines actions.
- [x] Préparer un export JSON en mémoire du diagnostic de mise à jour, sans écriture automatique de fichier.
- [x] Ajouter dans `À propos` un bouton pour copier le diagnostic de mise à jour JSON.
- [x] Remplacer les codes techniques du diagnostic update par des libellés plus lisibles dans l’affichage utilisateur.
- [x] Bloquer le diagnostic update si la séparation programme/données ou la liste des données personnelles à préserver manque dans le plan.
- [x] Afficher la dernière version disponible depuis GitHub dans le diagnostic À propos quand le manifeste distant répond.
- [x] Ajouter dans `À propos` un bouton `Vérifier les mises à jour`, à la demande, sans téléchargement ni application automatique.
- [x] Ajouter un accès mise à jour dans `Paramètres`, en gardant `À propos` pour le diagnostic et la version.
- [x] Ajouter dans `À propos` un bouton `Update` qui lance la simulation du script de mise à jour et un bouton d’application contrôlée avec confirmation.
- [x] Vérifier au démarrage si une mise à jour installable est disponible et proposer `Télécharger maintenant`, sans bloquer les synchronisations si l’utilisateur refuse.

- [x] Installation neuve : créer le schéma principal `plantes`, `capteurs`, `mesures` directement dans `database.py`, avec clés étrangères actives et index utiles.
- [x] Installer Windows : étapes lisibles, détection `py`/`python`, pip upgrade non bloquant et vérification finale des imports essentiels.

## Sauvegarde et restauration utilisateur complète

Objectif : permettre à un utilisateur de reconstruire son environnement Gruterra après formatage ou changement de PC, sans reconfigurer manuellement tous les services.

- [x] Distinguer deux usages : export de données partageable et sauvegarde complète privée.
- [x] Préparer un module technique `_app/sauvegarde_utilisateur.py` avec manifeste de sauvegarde, mode `donnees` et mode `complete`.
- [x] Marquer explicitement les sauvegardes complètes comme privées, car elles peuvent contenir tokens, identifiants techniques, `_config/`, base réelle et états runtime.
- [x] Exclure `_user_backups/` de Git et le bloquer dans `verifier_avant_github.py`.
- [x] Ajouter une interface `Exporter mes données` pour produire une archive sans secrets.
- [x] Ajouter une interface `Sauvegarde complète privée` avec avertissement très visible avant création.
- [ ] Étudier un chiffrement par mot de passe fiable pour les archives complètes contenant des secrets, sans inventer un chiffrement maison fragile.
- [ ] Préparer la restauration : vérifier l'archive, afficher son contenu, créer une sauvegarde automatique de l'état existant, puis restaurer seulement après confirmation.
- [ ] Tester la restauration sur un dossier temporaire avant toute restauration réelle sur le poste utilisateur.
- [ ] Documenter clairement que les sauvegardes complètes privées ne doivent jamais être partagées, envoyées sur Discord/Reddit ou publiées sur GitHub.

## GitHub, sauvegarde et sécurité

- Maintenir `README.md`, `RASPBERRY.md`, `TODO.md` et `CONTEXTE_AGENT_BOTANEO.md` à jour après les grosses évolutions.
- Lancer `py verifier_avant_github.py` avant chaque commit/push.
- Ne jamais stocker les tokens Netatmo, Météo-France, e-mail, clés SSH ou bases réelles dans GitHub.
- Garder les secrets dans des fichiers locaux ignorés par Git, surtout `_config/`.
- Garder uniquement des fichiers `.example.json` anonymes dans GitHub.
- Lire la liste des fichiers modifiés avant chaque envoi GitHub, même si le dépôt est privé.
- Ne pas pousser un fichier de contexte interne détaillé sans validation explicite si le contrôle automatique le juge sensible.
- Bloquer aussi les outils externes hors périmètre public, même sans secret, par exemple scripts de bot Discord, commandes de salons/rôles et assets Discord.
- Suivre le diagnostic de rétention des sauvegardes Raspberry ; ne nettoyer les anciennes copies qu’après validation manuelle.
- Garder un dossier historique pour les anciens fichiers non utilisés, sans les supprimer trop vite.


## Planning long terme

- Prévoir plus tard un vrai planning centralisé par jour.
- Pouvoir paramétrer les synchronisations selon les jours.
- Pouvoir paramétrer les mails selon les jours et selon le type d’alerte.
- Pouvoir paramétrer les rappels plantes longtemps à l’avance.
- Prévoir des notifications ou rappels sans devoir ouvrir l’application.
- Garder une logique simple : l’utilisateur choisit les jours, l’heure et le type d’action.
- Éviter d’envoyer plusieurs fois la même alerte si elle a déjà été traitée ou envoyée récemment.
- Préparer ce système seulement quand les alertes et la synchronisation locale seront bien stabilisées.
## À ne pas lancer maintenant

- MQTT / Home Assistant : intéressant plus tard, pas prioritaire tant que l’application locale évolue vite.
- Dashboard web moderne : possible plus tard, mais l’interface locale suffit pour avancer.
- Watchdog / relance automatique : pas utile pendant les tests, car il faut voir les erreurs.
- Notifications Windows : utile plus tard, après stabilisation des alertes.
- Envoi automatique d’e-mails : attendre que les règles d’alerte soient claires et validées.
- Intégration complète Météo-France officielle : attendre que le compte et les tokens soient fiables.
## Idées graphiques à garder de côté

- Continuer plus tard à harmoniser finement les cartes météo avec les cartes plantes : mêmes marges et espacements.
- Garder des couleurs dans les tuiles météo, mais utiliser seulement la palette Gruterra pour éviter un rendu instable.
- Organiser la météo en trois niveaux : synthèse météo locale, stations favorites, stations proches repliées.
- Ajouter un statut météo court en haut, par exemple : `Météo locale : sec prévu · vent faible · station favorite active`.
- Réduire le bruit visuel dans Netatmo : moins d’emojis répétés, titres plus courts, valeurs mieux alignées.
- Rendre les boutons secondaires Netatmo plus discrets : `↑`, `↓`, `Renommer`.
- Prévoir plus tard de vraies petites icônes météo locales dans `assets`, plutôt que de dépendre des emojis Windows.
- Revoir le logo d’en-tête avec une vraie version icône simplifiée, pensée pour une petite taille.


## Piste Bluetooth passif Mi Flora

- [ ] Étudier le décodage des annonces Bluetooth passives Mi Flora / Xiaomi BLE, inspiré de la méthode Home Assistant.
- [ ] Repères trouvés : intégration Home Assistant `xiaomi_ble`, bibliothèque `Bluetooth-Devices/xiaomi-ble`, service MiBeacon `0xFE95`, modèle Mi Flora / Flower Care `HHCCJCY01`, type appareil `0x0098`.
- [ ] Objets utiles à tester : température, humidité, luminosité, conductivité ; batterie à garder en lecture active car elle nécessite une connexion.
- [ ] Objectif : récupérer les mesures courantes sans connexion active quand le capteur diffuse déjà température, humidité, luminosité et conductivité.
- [ ] Garder la connexion active pour batterie, historique interne, firmware et diagnostics.
- [ ] Tester d’abord sur Raspberry, plus adapté à l’écoute régulière que le PC Windows.
- [ ] Vérifier que les mesures passives contiennent bien toutes les valeurs utiles selon le firmware du capteur ; Home Assistant indique qu’un firmware trop ancien peut ne pas diffuser les bons beacons.
- [ ] Prévoir un prototype isolé : scan BLE passif, journalisation des service data bruts par adresse, puis décodage hors base avant tout enregistrement automatique.
- [ ] Éviter de dépendre de Home Assistant comme source directe : s’inspirer de sa méthode, mais garder Gruterra autonome.

## ESP32 — configuration future

- [ ] Prévoir pour les futurs collecteurs ESP32 un mode configuration simple : au premier démarrage, l’ESP32 crée un réseau Wi‑Fi temporaire local.
- [ ] Depuis un téléphone, l’utilisateur se connecte à ce réseau puis ouvre une page de configuration captive ou locale pour renseigner Wi‑Fi, adresse Gruterra/Raspberry, nom du capteur et paramètres utiles.
- [ ] Après validation, l’ESP32 enregistre la configuration localement, coupe le point d’accès temporaire et rejoint le Wi‑Fi domestique.
- [ ] Prévoir un bouton ou une procédure de reset configuration pour relancer ce mode sans devoir reflasher l’ESP32.
- [ ] Ne jamais afficher ni envoyer les secrets ESP32 vers GitHub ; documenter seulement un exemple de configuration anonyme.

## Raspberry et synchronisation

État actuel : le PC récupère les données du Raspberry en priorité, confirme les mesures après enregistrement, évite les doublons et copie la dernière sauvegarde quotidienne du Pi. Le Raspberry demande maintenant une collecte Mi Flora quatre fois par jour : 06 h, 12 h, 18 h et 23 h. Le PC peut encore faire une lecture Bluetooth manuelle de secours si le Raspberry ne fournit pas de mesure fraîche.

- [x] Carte de disponibilité Raspberry dans Gruterra, contrôle SSH manuel et quotidien.
- [x] Récupération prioritaire des mesures Raspberry vers le PC.
- [x] Accusé après transaction, reprise et déduplication.
- [x] Sauvegarde quotidienne du Pi copiée et vérifiée côté PC.
- [x] Collecte Raspberry planifiée 4 fois par jour.
- [x] Scripts d’installation/mise à jour Raspberry dans `raspberry/install/`.
- [x] Secours Bluetooth PC manuel pour les capteurs normalement gérés par le Raspberry.
- [x] Afficher plus clairement l’ancienneté des dernières mesures, distincte du succès du transfert.
- [x] Afficher le nombre de mesures Raspberry en attente quand cette information est disponible.
- [x] Afficher un diagnostic de rétention des copies de sauvegarde Raspberry sur le PC.
- [ ] Ajouter plus tard un nettoyage manuel ou confirmé des anciennes sauvegardes Raspberry.
- [ ] Tester le cycle déplacement / nouveau capteur / retour / récupération PC.
- [ ] Tester une restauration Raspberry avec reprise des mesures déjà confirmées.
- [ ] Documenter plus précisément la reprise Wi-Fi après déplacement : retour réseau, contrôle SSH, récupération PC, sauvegarde copiée.
- [x] Distinguer clairement dans l’interface `Synchronisation terminée` et `Nouvelle mesure effectivement acquise`.
- [ ] Vérifier le chemin complet d’une mesure immédiate Raspberry : demande reçue, lecture Bluetooth effectuée, horodatage, délai avant récupération PC et éventuelle concurrence Bluetooth PC/Pi.

## Historique et graphiques — suivi restant

- [x] Sécurité base : refuser les nouvelles mesures sans date fiable et supprimer les anciennes mesures/archives sans date exploitable.
- [x] Archive brute Mi Flora conservée sans effacement.
- [x] Import graphique après archivage, avec déduplication.
- [x] Lectures partielles acceptées quand les entrées lues sont valides.
- [x] Lecture PC en plusieurs passes pour contourner les coupures BLE.
- [x] Synchronisation : afficher des sous-étapes détaillées pendant les phases longues.
- [x] Import historique simplifié : récupérer d’abord les historiques déjà collectés par le Raspberry.
- [x] Raspberry : permettre au PC de rejouer les historiques déjà confirmés sur le Pi.
- [ ] Améliorer encore le bouton Synchroniser avec deux lectures séparées : progression globale et progression historique Mi Flora.
- [x] À la fin d’une synchronisation, afficher clairement `Historique complet` ou `Historique encore à récupérer`, avec le nombre d’entrées récupérées / annoncées.
- [x] Clarifier la reprise historique : le Raspberry peut collecter plusieurs fois par jour, le PC récupère d’abord le Pi, puis peut compléter ponctuellement depuis le Bluetooth PC.
- [x] Afficher quand toutes les passes prévues sont terminées, même si l’historique reste incomplet à cause du Bluetooth.
- [x] Bandeau de qualité des données dans l’écran historique.
- [x] Fenêtre historique : bouton `Copier résumé` avec période, statistiques, qualité et ligne sélectionnée.
- [x] Historique : conserver les humidités à 0 % suspectes mais les exclure des statistiques/graphique.
- [x] Synchronisation : programmer une relecture de contrôle quand une mesure actuelle d’humidité vaut 0 %.
- [ ] Conserver la raison d’exclusion d’une mesure suspecte pour pouvoir la réexaminer plus tard.
- [ ] Afficher dans l’historique quand une valeur est exclue des statistiques mais conservée dans le tableau.
- [ ] Distinguer clairement donnée brute, mesure logique et mesure retenue pour une analyse donnée.
- [ ] Renforcer la déduplication sans confondre deux mesures identiques à des heures différentes avec un doublon réel.
- [ ] Garder la récupération de l’historique interne Mi Flora comme rattrapage même si le Raspberry collecte régulièrement.
- [ ] Ajouter un mode historique long séparé si les lectures normales restent limitées.
- [ ] Auditer les anciennes archives sans inventer leurs repères temporels.
- [x] Ajouter une extraction texte intégrée pour envoyer les données utiles à une discussion d’analyse plante.

## Collecte Mi Flora passive BLE

État actuel : un prototype Raspberry existe dans `raspberry/collector/passive_ble.py`. Il écoute les annonces MiBeacon `FE95` sans connexion active au capteur. Les premiers tests PC ont confirmé que le Mi Flora diffuse des valeurs décodables. Le 25/09/2026, une écoute passive de 90 s a reçu une mesure complète : 26.4 °C, 18 % humidité sol, 86 lux et 72 µS/cm.

- [x] Créer un prototype d'écoute passive BLE Mi Flora.
- [x] Décoder les objets MiBeacon utiles : température, humidité sol, luminosité, conductivité, batterie si diffusée.
- [x] Prévoir un mode affichage seul, sans écriture en base.
- [x] Prévoir un mode `--store` expérimental qui n'enregistre qu'une mesure complète.
- [x] Tester le prototype en local PC sans écriture : mesures complètes reçues passivement en 90 s puis en 5 min.
- [x] Ajouter un service manuel Raspberry `botaneo-passive-test.service`, non planifié automatiquement.
- [x] Tester sur Raspberry : service manuel 5 min validé, mesure complète enregistrée puis récupérée par le PC.
- [ ] Répéter le test Raspberry sur plusieurs fenêtres de 3 à 5 minutes.
- [ ] Vérifier si l'humidité sol est bien diffusée régulièrement sur le capteur actuel.
- [x] Vérifier que le PC importe les mesures passives courantes dont le brut est en JSON.
- [ ] Comparer les mesures passives avec les mesures actives et l'historique interne.
- [ ] Décider ensuite si un timer passif séparé est utile, sans remplacer l'import historique.

### Déduplication passive

- [x] Ajouter une déduplication avant insertion Raspberry pour les mesures passives quasi identiques reçues dans une fenêtre courte.
- [x] Ne jamais supprimer rétroactivement l'historique Mi Flora ni les mesures déjà synchronisées.
- [x] Conserver une nouvelle mesure si une valeur utile change, par exemple la lumière ou la conductivité.
- [ ] Observer plusieurs passages pour ajuster les seuils si la base reçoit encore trop de mesures passives répétitives.

## Synthèse journalière et compactage futur

État actuel : base technique dormante ajoutée dans `database.py`. Elle permet de diagnostiquer la taille de la base, de créer une table de synthèse journalière et de calculer/enregistrer des synthèses par capteur et par jour. Rien n'est exécuté automatiquement et aucune mesure brute n'est supprimée.

- [x] Définir un seuil de compactage conseillé à 5 Go.
- [x] Ajouter un diagnostic passif de taille de base.
- [x] Préparer une table `syntheses_mesures_journalieres`.
- [x] Calculer min/max/moyenne par jour pour température, humidité, luminosité et conductivité.
- [x] Conserver le nombre de mesures, première/dernière mesure et les sources détectées.
- [x] Ajouter un garde-fou qui bloque tout compactage destructeur.
- [x] Ajouter une fenêtre Maintenance indiquant la taille de la base, le seuil 5 Go, le nombre de mesures et l'état des synthèses.
- [x] Ajouter un bouton manuel `Préparer les synthèses`, sans suppression de mesures brutes.
- [x] Afficher les dernières synthèses préparées dans un tableau Maintenance.
- [x] Ajouter une fenêtre de détail pour consulter une synthèse journalière.
- [x] Afficher le nom de plante et le capteur dans les synthèses de Maintenance.
- [ ] Valider visuellement les synthèses avant toute suppression de mesures anciennes.
- [ ] Définir une politique de conservation : mesures brutes récentes, données autour des arrosages, événements importants et synthèses anciennes.


## Santé du système

- [x] Ajouter un diagnostic global local : base, synthèses, mesures par capteur.
- [x] Ajouter une fenêtre Santé système avec résumé copiable.
- [x] Afficher un tableau des capteurs avec dernière mesure, mesures passives et historiques.
- [ ] Ajouter plus tard un état visuel clair : OK, à surveiller, action conseillée.
- [ ] Ajouter plus tard les erreurs récentes de synchronisation si elles sont historisées.

## Validation restauration — 27 septembre 2026

- [x] Tester la sauvegarde du 26 septembre sur des copies temporaires : intégrité SQLite correcte.
- [x] Rejouer les 372 relevés, y compris déjà confirmés : deux passages sans doublon dans une copie du PC actuel.
- [x] Simuler la perte des mesures PC sur une copie : 369 mesures récupérées, 3 relevés sans date fiable ignorés, aucune erreur de clés étrangères.
- [ ] Tester séparément le redémarrage sur une carte SD restaurée : non couvert par le test logiciel.

La remise en attente a été effectuée uniquement sur une copie de la base Pi. Les bases utilisées et le Raspberry en fonctionnement n’ont pas été modifiés. Ce test ne constitue pas encore une commande de restauration accessible à l’utilisateur.

## Cohérence des analyses Crassula
- [x] Aligner le compteur de l'analyse post-arrosage avec le résumé exporté : l'ancienne analyse ne lisait que les 200 dernières mesures, alors que le résumé depuis le dernier arrosage utilise tout l'historique disponible.
- [x] Mieux contextualiser les pics lumineux liés aux sorties sur balcon pour qu'ils ne masquent pas la faible luminosité habituelle du salon : l’analyse 24 h distingue maintenant un pic isolé d’une journée réellement lumineuse.
- [x] Ajouter des événements dédiés `Sortie balcon` / `Retour intérieur` dans le journal plante, accessibles depuis la carte plante.
- [x] Sécuriser les boutons `Sortie balcon` et `Retour intérieur` avec une confirmation avant inscription dans le journal plante.
- [x] Permettre d'ajouter après coup une exposition balcon passée avec date/heure de sortie et date/heure de retour.

- [x] Afficher les expositions balcon dans le graphique historique sous forme de zone visuelle, sans modifier les mesures.

- [x] Afficher séparément les repères `sortie` et `retour` des expositions balcon dans le graphique historique.

- [x] Enrichir `Copier analyse plante` avec un contexte lumière : sorties balcon, moyenne globale, moyenne hors balcon et interprétation des pics.

- [x] Enrichir `Copier journée` avec les sorties balcon du jour et les statistiques lumière globale / hors balcon / pendant balcon.

## Alertes e-mail sécurisées
- [x] Préparer le terrain pour un SMTP sécurisé local : exemple public, fichier local ignoré, module de préparation en mode aperçu sans envoi automatique.
- [x] Garder Outlook local comme option secondaire dans le cadrage, sans en dépendre : l'application Outlook ou la session Windows peuvent ne pas être ouvertes.
- [x] Préparer la mémoire locale de dernière alerte par plante/type/titre pour éviter un e-mail à chaque synchronisation.
- [x] Ajouter le calcul du délai minimal entre deux alertes identiques, en mode test sans envoi.
- [x] Conserver le comportement actuel sans envoi automatique tant que le destinataire, les plantes concernées et les règles d'alerte ne sont pas validés explicitement.
- [x] Prévoir d'abord un mode test qui affiche le mail préparé sans l'envoyer.


- [x] Brancher le centre d'alertes sur un aperçu e-mail sans envoi réel.

- [x] Préparer la mémoire de dernière alerte envoyée et le délai minimal avant tout envoi SMTP réel.

- [x] Améliorer le graphique historique : graduations horaires et repère sélectionnable avec heure/valeur du point le plus proche.
## Langue, traduction et internationalisation

- [x] Clarifier le statut : origine francophone, écrans principaux FR/EN ; ne pas promettre la traduction des notes personnelles et anciens changelogs.
- [x] Ajouter une préférence de langue français/anglais dans les paramètres.
- [x] Créer un premier module `i18n.py` pour centraliser les textes traduits.
- [x] Traduire les écrans principaux dans le catalogue JSON commun ; validation d’usage utilisateur reçue le 10/10/2026.
- [x] Ajouter un premier README anglais `README_EN.md` et un guide démo anglais `GUIDE_DEMO_EN.md`.
- [ ] Identifier les prochains textes publics à traduire : aide installation, Netatmo, Raspberry, erreurs fréquentes.
- [ ] Éviter de présenter Discord ou GitHub comme entièrement anglophones tant que l'application reste française.

- [x] Continuer la traduction progressive : boutons plante, historique, ajout plante, vue plantes, synchronisation et messages update visibles en démo.

### Météo locale — amélioration du 09/10/2026

- [x] Afficher la source et la date du relevé sous les indicateurs météo.
- [x] Adapter les tuiles aux fenêtres étroites (4, 2 ou 1 colonne).
- [x] Traduire les nouveaux libellés en français et en anglais.
- [x] Vérifier la disposition avec des données isolées ; audit local : 89 tests réussis.
- [ ] Confirmer la lisibilité avec les stations réelles sur le poste utilisateur.
- [ ] Définir les alertes météo importantes selon les plantes extérieures avant d’ajouter une nouvelle classification rouge.

Ces changements sont consolidés sur main ; aucune nouvelle release ne remplace la 0.1.6-dev pour le moment.

### Correction affichage météo / alertes — 09/10/2026

- [x] Sortir la synthèse de la section détaillée Netatmo pour la placer près du centre d’alertes sur l’accueil.
- [x] Afficher un bloc de prévision même sans station Netatmo.
- [x] Rafraîchir les alertes à la fin de l’actualisation météo seule.
- [x] Vérifier l’accueil complet FR/EN avec une prévision de rafales au-dessus du seuil existant, et sans station.
- [ ] Confirmer le rendu et les alertes sur les données météo réelles du poste utilisateur.

### Contributions — partie application (10/10/2026)

- [x] Information au premier lancement réel et accès depuis les paramètres, FR/EN.
- [x] Clé locale durable sur demande, sauvegarde et restauration sans remplacement d’une autre clé.
- [x] Partage désactivé ; aucun transport réseau implémenté.
- [x] Démo : aucune identité réelle ni envoi.
- [x] Tester présence de la clé dans le ZIP complet et absence dans l’export de données.
- [ ] Définir contrat commun application/site et clé de gestion avant activation réseau.
- [ ] Finaliser notice, finalités, durée de conservation et contact de secours.
- [ ] Intégrer l’aperçu des contributions et les reçus confirmés par le site.

### Clé de contribution — préparation du site (10/10/2026)

- [x] Centraliser la restauration locale et interdire son appel en mode démo.
- [x] Vérifier le couple identifiant/clé complet ; refuser tout remplacement, même si seule une des deux valeurs change.
- [x] Préserver un fichier existant incomplet ou illisible sans écrasement.
- [x] Tester restauration sur installation neuve, répétition, conflit et démo sur fichiers temporaires.
- [ ] Valider avec le site le contrat de gestion : identifiant public pseudonyme, clé privée distincte, retrait authentifié et reçu.
- [ ] Prévoir un aperçu et un accord explicite avant chaque futur envoi ; conserver le partage désactivé en attendant.

### Raccordement signé V2 — résultat transmis le 10/10/2026

- [x] Résultat côté hébergement rapporté par la conversation web : signature altérée refusée, envoi accepté, défi à usage unique, reprise sans doublon, retrait et non-recréation par un ancien envoi.
- [ ] Confirmer côté hébergement le retour de `enabled` et `enabled_v2` à false ; configuration serveur non accessible depuis cette vérification locale.
- [ ] Terminer tests entre deux identités, concurrence et erreurs transactionnelles côté API.
- [ ] Implémenter l’identité Ed25519 dans l’application : base64 standard avec padding, identifiant ed25519: + SHA-256 des 32 octets publics ; préserver l’ancienne identité locale.
- [ ] Préparer les signatures et tests communs Python/PHP avant tout raccordement utilisateur.
- [ ] Définir conservation, retraits, sauvegardes et limites anti-abus avant ouverture publique.

Ces résultats concernent le client de test de l’API, pas un parcours déjà intégré à Gruterra. Partage applicatif toujours désactivé.

### Identité locale Ed25519 — 10/10/2026

- [x] Nouveau format privé identity_version=2 : clé publique/seed de 32 octets, base64 standard avec padding, identifiant ed25519: + SHA-256 des octets publics.
- [x] Sauvegarde séparée chiffrée PKCS8 par mot de passe et restauration vérifiant le couple privé/public et l’identifiant.
- [x] Préserver l’ancienne identité, refuser la création automatique en sa présence et tout remplacement d’une identité Ed25519.
- [x] Démo bloquée ; aucune génération au lancement, aucun transport ; signature locale seulement.
- [ ] Préparer une migration explicite des anciennes identités et les signatures du message V2 convenu avec le site.
- [ ] Tester avec PHP les mêmes octets signés ; aucune connexion activée dans ce lot.

### Chaîne de provenance des mesures — réflexion du 10/10/2026

- [ ] Auditer la conservation effective des données brutes pour chaque source ; un champ donnees_brutes ne suffit pas à garantir des octets source complets.
- [ ] Prévoir valeur source → calibration versionnée → valeur interprétée → analyse, sans remplacement destructeur des relevés.
- [ ] Étendre le contrat communautaire au modèle de capteur et à la calibration : le V2 actuel ne contient que des valeurs interprétées et peut agréger les relevés à la même seconde par médiane. Ne pas envoyer les trames privées sans filtrage ; aucune compatibilité multi-matériel calibrée annoncée pour l’instant.

### Message signé applicatif V2 — 10/10/2026

- [x] Construire le message ASCII identique au vérificateur PHP et l’enveloppe signée sans réseau.
- [x] Vérifier le vecteur public PHP : octets exacts, empreinte, signature ; refuser les variantes de contenu/opération/défi et les encodages non canoniques.
- [x] Tester une reprise avec même request_id et mêmes octets mais nouveau défi/signature ; bloquer défi expiré et démo.
- [ ] Rejouer le nouveau client applicatif en test privé PHP ; consommation unique et concurrence sont des garanties serveur.
- [ ] Préparer le stockage durable des demandes/reçus et le parcours aperçu/accord avant transport réseau. Aucun jeton serveur de test dans l’application distribuée.

### Demandes, reçus et retraits locaux — 10/10/2026

- [x] Figer request_id et octets exacts dans un suivi SQLite privé, conservé après redémarrage.
- [x] Vérifier les reçus du profil privé actuel et garder une réponse incohérente à vérifier sans recréer de demande.
- [x] Conserver le reçu initial ; reprise HTTP 200 ne modifie ni réception ni échéance.
- [x] Distinguer réception historique, retrait actif confirmé et échéance locale, sans annoncer une suppression totale vérifiée.
- [x] Sérialiser localement les opérations par identité ; reprise d’un retrait global ne couvre pas les contributions ultérieures.
- [x] Ajouter la consultation FR/EN depuis Contributions et confidentialité, sans création de fichier à l’ouverture si aucun suivi n’existe.
- [ ] Brancher aperçu, accord et futur transport (validation métier v2 intégrée). Profil public, politique et règles d’expiration non négociés : aucun reçu public accepté par ce lot.
- [ ] Gérer les codes d’erreur serveur et la reprise bornée dans le futur client ; pas de transport ni d’activation dans ce lot.

- [x] Contributions : retrait préparé distinct d’une tentative, isolement de deux identités, concurrence locale et conservation du suivi dans la sauvegarde privée vérifiés (partage désactivé).

- [x] Contributions : validation métier complète v2 avant enregistrement d’une demande ; aucune resérialisation du contenu signé, données privées interdites et apports fractionnés conservés.

- [x] Profil privé lifecycle-test-60s : choix explicite, échéance exacte, migration du suivi historique et fins de parcours 410 sans recréation préparés localement ; transport et partage toujours désactivés.

- [x] Lanceur privé application/API isolé préparé, simulation sans réseau utilisant les vrais modules.
- [ ] Convenir de la fenêtre privée, lancer explicitement l’essai réseau fictif, confirmer nettoyage et fermeture serveur ; aucun essai réseau effectué par ce lot.

- [x] Essai privé : diagnostic par étape, HTTP et codes serveur autorisés ; contrôles affichés immédiatement ; échecs simulés et absence de secrets vérifiés avant nouvel essai réseau.

- [x] Synchronisation prioritaire : capteur attribué au Raspberry jamais relu automatiquement par le PC quand la collecte Pi est en attente, en cours ou en échec ; historique conservé.

- [x] Synthèse météo : modules personnels extérieurs/pluie/vent inclus, source disponible la plus proche par mesure, heures publiques extraites, absence distincte de 0 mm et pictogrammes vectoriels lisibles. Aucun relevé « Jamais » sans horaire.


## Météo — 11/10/2026
- [x] Synthèse : station personnelle, favoris équipés, puis station proche par mesure.
- [x] Suivi local des cumuls de pluie datés reçus, sans doublons ni addition de cumuls chevauchants. Dernier cumul positif affiché ; aucune averse exacte déduite.
- [ ] Vérifier les relevés réels après une prochaine récupération Netatmo : aucun accès réseau effectué pour ce chantier.
- [ ] Clarifier les fenêtres des cumuls privés Netatmo (journée/cumul glissant) avant analyse quotidienne.
- [ ] Nappes : étudier Hub’Eau Piézométrie (stations, chroniques, chroniques_tr). Conserver unité, date, repère et aquifère ; ne pas assimiler niveau à un pourcentage de remplissage. Source : https://www.data.gouv.fr/dataservices/hubeau-piezometrie

## Nappes — préparation locale 11/10/2026
- [x] Consultation facultative Hub’Eau depuis Paramètres : département, choix de station, dernière date, 100 niveaux historiques, qualification, courbe et cache privé. Aucun appel automatique au démarrage.
- [x] Service officiel vérifié sur un exemple public sans localisation utilisateur.
- [ ] Valider le parcours complet sur une station choisie par l’utilisateur ; distance et recherche géographique à ajouter si utiles. Liste limitée signalée à 500 stations.
- [ ] Lecture de la profondeur : vérifier le repère propre à la station avant comparaison ; aucune alerte sécheresse ni remplissage normalisé calculés.

- [x] Nappes : accepter 92380 / 92 380 comme département 92, refuser 380 avec explication ; distinguer HTTP, délai, connexion, certificat et format sans exception brute. Département 92 testé sur API publique ; erreur initiale de la fenêtre encore à confirmer après relance.

- [x] Nappes : stations avec dernier relevé dans les 365 jours par défaut, anciennes sur option, pagination jusqu’à 5000 sources avec avertissement si incomplète. Évite les choix anciens de 1992 issus de la seule première page.

- Vérification réseau du 92 le 11/10/2026 : 1053 stations, pagination complète, dernière date renvoyée 1993-07-28 ; aucun relevé dans les 365 derniers jours via le catalogue interrogé. Ne pas présenter ces stations comme actives. Prochaine étude : stations voisines et catalogue temps réel.

- [x] Nappes : aide FR/EN sur qualification, NGF, profondeur et nappes captives ; panneau et carte harmonisés avec le thème actif ; tableau défilant et courbe redessinée au redimensionnement.
- [ ] Évolution future : comparer les relevés de nappe aux pluies et capteurs extérieurs, avec dates réelles, lacunes visibles et distinction entre aquifères ; aucune recommandation d’arrosage déduite directement du niveau régional.

- [x] Nappes : afficher la masse d’eau déclarée et vider immédiatement les anciens relevés lors du changement de station ; empêcher un changement de sélection pendant une récupération.

- [x] Nappes : conserver et afficher le statut de validation original séparément de la qualification ; anciens caches compatibles et valeurs absentes indiquées par un tiret.

- [x] Bloc nappes de l’accueil : dernier niveau et date du cache correspondant à la station choisie, mention explicite de l’historique local ; aucun appel réseau automatique.

### Raccordement météo Raspberry — planifié le 11/10/2026

Plan détaillé : PLAN_RACCORDEMENT_METEO_RASPBERRY.md. Collecte non activée.

- [ ] Valider le contrat observations/lots/accusés avec la partie Raspberry.
- [ ] Ajouter le stockage météo PC versionné et une migration conservant l’historique existant.
- [ ] Préparer normalisation, déduplication, révisions et import transactionnel.
- [ ] Raccorder weather_export/weather_ack après accord sur le contrat.
- [ ] Adapter l’affichage pluie FR/EN aux relevés importés et à leur fraîcheur réelle.
- [ ] Valider la propriété OAuth et étendre les sauvegardes météo avec restauration testée.
- [ ] Tester collecte manuelle, synchronisation répétée et reprises ; puis valider le timer avec PC éteint.

- [x] Préparer le validateur commun météo v1 et les vecteurs fictifs : wu1_ prioritaire si module/date inconnu, filiation supersedes explicite, lots bornés non vides.
- [ ] Confirmer le contrat côté Pi et tester la résolution des périodes enrichies, révisions et accusés dans le stockage réel sur copies avant branchement.

- [x] Préparer l’import transactionnel météo sur bases fictives : accusé après commit, reçus durables, doublons et révisions conservés, exclusion des filiations de période non résolues.
- [ ] Raccorder l’import préparé au transport Pi après accord commun ; ajouter les essais de coupure et d’export/accusé réels. Collecte toujours inactive.

## Transport météo Raspberry — 11 octobre 2026

- [x] Export météo borné et accusé atomique, idempotent, sans suppression.
- [x] Protocole commun copié depuis _app/weather_protocol.py, sans version indépendante.
- [x] 19 tests fictifs passent sur Windows et Raspberry : import PC, reprises, révisions et limites.
- [x] Commandes weather_export/weather_ack installées ; export réel de la file vide vérifié.
- [ ] Raccorder la collecte Netatmo et sa configuration OAuth privée.
- [x] Étendre les sauvegardes à weather.sqlite3 avant activation (copie/restauration vérifiée le 12/10/2026).
- [x] Raccorder l'appel automatique du transport depuis la synchronisation PC (option explicite).
- [ ] Vérifier un relevé Netatmo réel et son import, puis la collecte horaire PC éteint.

Aucun timer météo activé. Aucun token transféré. Les relevés fictifs restent dans des bases temporaires ; aucune mesure fictive insérée dans la file installée.

- [x] Préparer les appels PC weather_export/weather_ack : transport SSH dédié UTF-8, lots bornés, accusé après import et reprises simulées contre l’outbox Raspberry.
- [ ] Activer explicitement weather_import_enabled et raccorder au parcours graphique après validation réelle ; aucune bascule OAuth ni collecte Netatmo effectuée.

- [x] Brancher l’import météo Pi dans la synchronisation PC avec réglage explicite désactivé par défaut, exclusions démo et bilan FR/EN. Aucun token ni timer modifié.
- [ ] Adapter les lecteurs météo aux observations versionnées, étendre les sauvegardes et valider le premier relevé réel jusqu’à l’affichage.

- [x] Secours météo PC : consultations Netatmo fraîches sans nouveaux enregistrements pluie, cache d’affichage maintenu et historique existant préservé.
- [ ] Pi : vérifier un accès Netatmo indépendant ou définir un partage OAuth sûr ; aucun refresh token PC dupliqué.

## Météo Raspberry — état consolidé du 12 octobre 2026

Guide : docs/WEATHER_RASPBERRY_PREPARATION.md. Cet état précise les étapes partielles ci-dessus.

- [x] Préparer et installer le collecteur météo, la gestion des erreurs et du renouvellement OAuth, et les unités horaires désactivées.
- [x] Intégrer la sauvegarde météo au passage quotidien existant ; copier et restaurer une sauvegarde de la base réelle vide sans remplacer la base active.
- [x] Ajouter la récupération vérifiée des sauvegardes au PC après une synchronisation complète.
- [x] Ajouter un tableau FR/EN des observations importées dans les réglages météo Raspberry : dates source, unités, périodes et révisions ; ouverture/actualisation testées.
- [x] Valider 37 tests météo Windows et 35 Raspberry sur données fictives. Aucun relevé fictif injecté dans les bases actives.
- [x] Préserver le choix PC : météo fraîche directe et cache, sans nouvel archivage pluie ni modification de ses tokens.
- [ ] Fournir et vérifier une autorisation Netatmo indépendante pour le Raspberry ; ne pas copier le refresh token PC.
- [ ] Vérifier une collecte réelle, son import répété sans doublons et son affichage, puis renouvellement OAuth sans perturber le PC.
- [ ] Activer ensuite le timer et vérifier un passage PC éteint et un redémarrage physique du Raspberry.
- [ ] Étendre ultérieurement les synthèses météo de l'accueil aux observations versionnées ; le tableau dédié est disponible.

Collecte toujours désactivée ; aucun appel Netatmo réel pendant cette préparation. Aucun secret transféré et aucune publication GitHub.
- [x] Pluie Météo-France : consultation manuelle dédiée FR/EN, 5 stations proches, rr1 horaire et dates réelles, base data/meteofrance_pluie.sqlite3 distincte de plantes.db et Netatmo ; aucun timer ni token transféré.
- [ ] Comparaison horaire Netatmo/Météo-France : afficher les périodes réelles côte à côte sans fusion ni somme ; accès Météo-France durable et sauvegarde de sa base à finaliser.

- [x] Comparaison informative dans le panneau pluie : cache de la station Netatmo choisie avec cumuls 1 h / 24 h et dates, face aux relevés horaires Météo-France ; aucune fusion ni différence automatique.

- [ ] AROME-PI : consultation toutes les 15 minutes aux quarts d’heure + 1 seconde, après validation d’une prévision locale, de l’accès durable et des quotas. Plan : PLAN_AROME_PI.md ; timer non activé.

- [x] AROME-PI : préparer sélection du calcul récent, validation des échéances UTC et unité pluie, calendrier fixe sans dérive avec passage à minuit.
- [ ] AROME-PI : télécharger une prévision locale, vérifier les bornes de cumul GRIB et intégrer Observé/Prévu ; renouvellement OAuth et timer restent non activés.

- [x] Interface iPhone Raspberry : page /weather authentifiée, 300 dernières versions stockées, filtre station, dates source et récupération, zéro/absence distincts. Installée le 12/10/2026 ; deux tests de lecture seule passent, base réelle vide vérifiée. Collecte météo inchangée et désactivée.

- [x] Préparer le gestionnaire OAuth2 Météo-France sous verrou avec expiration serveur et sauvegarde atomique, testé avec profils fictifs.
- [ ] Valider les identifiants OAuth, droits communs et la génération réelle ; extraction locale GRIB encore non validée (refus HTTP 401 au dernier essai).

- [x] Pluie Météo-France : recherche manuelle par code postal via geo.api.gouv.fr, choix des communes ambiguës, distances depuis le centre communal et localisation Netatmo inchangée.

- [x] Netatmo Raspberry : formulaire privé FR/EN de saisie masquée et exemple vierge ; aucun transfert ou activation à l’enregistrement.
- [ ] Accès Pi : applications distinctes confirmées et PC HTTP 200, mais renouvellement Pi refusé (authorization_required) au contrôle du 13/10/2026 ; corriger l’autorisation avant transfert et collecte.

- [x] 13/10/2026 : historique météo mobile, écran vide explicite et filtres station/mesure/période ; base Pi vérifiée à zéro observation, collecte toujours non activée.

- [x] 13/10/2026 : capteur nommé Crassula via configuration privée stable ; bilan journalier lumière moyenne/maximale, température et humidité moyennes, nombre et plage des relevés. Historique prioritaire sans mélange avec lectures ponctuelles ; limites et dates estimées signalées. Bornes de journée Paris, zéro, absence et repli testés.

## Interface Raspberry — bilan consolidé du 13/10/2026
- [x] Interface locale protégée, utilisable depuis iPhone ; lecture des capteurs à la demande.
- [x] Nom Crassula lié au capteur via configuration privée.
- [x] Bilan journalier lumière moyenne/maximale, température et humidité moyennes ; nombre de relevés et heures couvertes explicités.
- [x] Courbe lumière installée : Aujourd'hui / Hier / 7 jours, valeurs au toucher et au clavier, périodes Paris, interruptions au-delà de 90 minutes. Historique prioritaire ; lectures ponctuelles utilisées seulement en son absence.
- [x] Page météo locale avec filtres station/mesure/période et écran vide explicite.
- [x] Sauvegarde météo et restauration sur copie vérifiées ; import PC et tableau FR/EN préparés.
- [ ] Confirmer le confort de lecture et le toucher du graphique sur l'iPhone réel (données et syntaxe contrôlées ; 162 points réels disponibles lors du test).
- [ ] Corriger l'autorisation Netatmo Pi : renouvellement refusé au dernier contrôle du 13/10 ; conserver l'accès PC indépendant.
- [ ] Valider premier relevé météo réel, synchronisation répétée et affichage ; ensuite seulement activer l'horaire et tester PC éteint/redémarrage.
- [x] Courbes température et humidité du sol installées : sélecteur de mesure, périodes conservées, unités et échelles adaptées (températures négatives et humidité 0–100 %). Valeurs nulles et négatives testées ; validation tactile iPhone restante.

Aucune collecte météo activée dans ce chantier, aucune publication GitHub. Les autres chantiers météo PC ci-dessus restent inchangés.

### Météo Raspberry — validation réelle du 13/10/2026

- [x] Accès Netatmo indépendant autorisé et renouvelé, accès PC préservé.
- [x] Premier passage réel Pi : 9 observations collectées, sauvegardées et importées ; correspondance des données vérifiée.
- [x] Rejeu réel : 0 ajout / 9 doublons ; deuxième synchronisation vide.
- [x] Activer l’import PC et le timer météo utilisateur horaire après validation complète.
- [x] Collecte PC éteint et import au retour validés le 15/10/2026.
- [ ] Vérifier le redémarrage matériel du Raspberry et la reprise du timer.

Les états « collecte inactive » précédents sont historiques pour Netatmo Pi. AROME reste en préparation, sans timer activé.

- [x] Vérifier le timer Netatmo utilisateur actif et Linger=yes ; service manuel terminé avec succès. Premier passage programmé encore non observé.
- [x] Préparer une seule reprise OAuth Météo-France après 401, avec hôte HTTPS strict et sans redirection du secret.
- [ ] Restaurer/valider la configuration OAuth AROME : fichier actuel en bearer et application_id vide au 13/10/2026 ; aucune prévision locale ni timer AROME activés.

- [x] AROME-PI : formulaire privé FR/EN de saisie OAuth2 ou jeton temporaire dans Paramètres, secrets masqués, modèle vierge et aucune activation à l’enregistrement.


### Météo Raspberry : validation horaire du 13/10/2026

- [x] Vérifier un passage autonome du timer et importer ses observations : 18 importées, sauvegarde vérifiée, rejeu sans doublon, file vide.
- [x] Collecte PC éteint et reprise confirmées le 15/10/2026.
- [ ] Vérifier le redémarrage matériel du Pi et la reprise du timer.

### Prévisions sur interface Raspberry — 14/10/2026
- [x] Bloc prévisions 24 h installé : température, précipitations horaires, humidité, vent et rafales ; modèle AROME France fourni par Open-Meteo, attribution explicite.
- [x] Localisation PC transmise avec accord utilisateur ; configuration privée sur Pi, sans token copié.
- [x] Prévision réelle de 24 échéances vérifiée depuis le Pi ; cache horaire à la consultation, indépendant du PC. Échec réseau : copie conservée avec date et statut ancien ; nouvelle tentative espacée de 5 minutes.
- [x] Tests panne réseau, conservation du cache, zéro/absence et réutilisation sans nouvel appel.
- [ ] Vérifier le confort de consultation de ce bloc sur iPhone.
Ce bloc est distinct de l'accès direct AROME-PI : aucun timer AROME-PI activé et aucune observation pluie ajoutée par les prévisions.

### Historique pendant l’éclairage — 14/10/2026
- [x] Crassula : plage 09:50–15:50 initialisée sur PC et Pi, réglable par plante/capteur ; fichiers de configuration privés distincts.
- [x] Pi : historique dédié 7 jours, moyenne/minimum/maximum et relevés, graphique filtré par plage. PC : bouton dans Historique, fenêtre dédiée 30 jours avec tableau, courbe et observations.
- [x] Moyenne des échantillons, zéros inclus, fin de plage exclue, passage de minuit pris en charge ; aucun calcul de durée réelle d’éclairage ni intégrale lumineuse.
- [x] Bouton téléphone Copier les données du jour : toutes les mesures du jour (température, humidité, lumière, conductivité), sources et qualité des dates ; texte sélectionnable si presse-papiers bloqué.
- [x] Validation bornes horaires/zéros/minuit, ouverture fenêtre PC et lecture réelle Pi. Aucun relevé modifié.
- [ ] Confirmer la copie et le rendu sur iPhone réel.
- [x] Horaires PC/Pi synchronisés depuis le 14/10/2026 ; les horaires actuels restent appliqués rétroactivement.
- [ ] Traduire le nouvel écran éclairage PC en anglais et conserver des versions datées des horaires si nécessaire.

### Synchronisation des horaires — 14/10/2026
- [x] Synchronisation bidirectionnelle des horaires liée au transfert des capteurs PC/Pi ; identification par capteur BLE et plante associée, sans serveur supplémentaire.
- [x] Référence commune conservée par appareil/capteur ; conflit si les deux côtés divergent, aucune priorité basée sur l'horloge système.
- [x] Résolution explicite dans Historique pendant l'éclairage → Synchroniser avec le Pi : conserver PC ou Pi, possibilité d'annuler. Contrôle de modifications concurrentes avant écriture.
- [x] Verrou partagé avec les enregistrements locaux, contrôle compare-and-set côté Pi, exclusion du mode démo et des associations ambiguës.
- [x] Tests fictifs push/pull/conflit/résolution et premier échange réel réussi sans modification des horaires existants.
Les mentions précédentes de réglages PC/Pi indépendants sont désormais dépassées. Une relance de Gruterra est nécessaire pour charger ce raccordement.


### Vérifications de reprise — 14/10/2026
- [x] Horaires : réponse perdue après enregistrement Pi puis reprise ; modification concurrente et choix de conflit obsolète refusés ; Pi indisponible sans modification locale.
- [x] Tests conservés dans tests/test_lamp_sync.py ; message explicite si aucun capteur associé sans ambiguïté.
- [x] Contrôle réel : service web actif, collecte Netatmo du 14/10 à 22:05 réussie.
- [ ] Validation matérielle restante : redémarrage Pi, confort tactile et copie iPhone. Collecte PC éteint validée le 15/10.

### Reprise après la nuit du 14 au 15/10/2026
- [x] Constater les collectes Netatmo nocturnes stockées et la lecture Crassula de 06:04 (heure de Paris).
- [x] Import réel : 14 relevés capteurs et 204 observations météo ajoutés, aucune file restante ; sauvegarde météo copiée.
- [x] Second passage météo vide, aucun ajout, sauvegarde vérifiée ; horaires PC/Pi concordants.
- [x] Arrêt physique nocturne du PC confirmé par l’utilisateur le 15/10 ; heures exactes non fournies.
- [ ] Redémarrage matériel Pi toujours non testé dans ce chantier (dernier démarrage observé : 19/09/2026).

### Autonomie nocturne confirmée — 15/10/2026
- [x] L’utilisateur confirme que le PC était complètement éteint cette nuit. Les collectes nocturnes du Pi et leur import au retour sont vérifiés : 14 relevés capteurs, 204 observations météo, rejeu vide et sauvegarde contrôlée. Horaires précis d’arrêt du PC non fournis.
- [ ] Reste à vérifier : redémarrage matériel du Raspberry et reprise des services/timers.


### Préparation Zigbee via Home Assistant — 15/10/2026

- [x] Préparer un adaptateur hors ligne des états HA : association explicite, unités, provenance, indisponibilité et datation distincte.
- [x] Documenter les commandes dans `docs/JOURNAL_COMMANDES_TECHNIQUES.md`.
- [ ] Vérifier les modèles et entités réels après appairage dans Home Assistant.
- [x] Raccorder la lecture manuelle et le rattrapage historique à l’archive séparée ; coupures et reprises validées en simulation.
- [ ] Valider le parcours de récupération sur un capteur réel après appairage et vérification de Recorder.
- [ ] Intégrer la source et la fraîcheur dans les écrans FR/EN après validation des données réelles.

- [x] Préparer la lecture REST des seules entités HA choisies : configuration désactivée, erreurs sans secret, redirections refusées, tests simulés et modèle vide.

- [x] Ajouter l’écran de préparation Home Assistant FR/EN dans Paramètres : jeton masqué, associations explicites, validation toujours accessible, sauvegarde locale désactivée sans réseau.

- [x] Protéger le jeton Home Assistant avec Windows DPAPI lié au compte : pas de clair sur disque, migration atomique, remplacement après perte du compte Windows.

- [x] Vérifier réellement l’authentification Home Assistant (15/10/2026) : API HTTP 200, jeton DPAPI confirmé, collecte désactivée ; entités à associer après appairage.

- [x] Préparer le refus des doublons Mi Flora Bluetooth/Home Assistant par identité physique et source de référence explicites ; refus avant lecture si identité non confirmée.
- [x] Préparer la lecture historique HA bornée à six heures, dédoublonnage de rejeu et exclusion du contexte antérieur ; tests simulés.
- [x] Raccorder la lecture du registre BLE réel aux identités physiques du formulaire et afficher les statuts de refus/autorisation.
- [ ] Vérifier les vrais identifiants matériels après appairage, puis raccorder l’archive et le curseur préparés à l’orchestration avant activation.


## Raspberry — référence consolidée au 15 octobre 2026

Cette section est la référence actuelle pour le Raspberry. Les livraisons datées ci-dessus sont le journal des étapes ; en cas de contradiction, cet état prévaut. La fiche de conversation `outputs/TODO_RASPBERRY.md` devient un résumé sans liste de tâches indépendante.

### Réalisé et vérifié

- [x] Collecteur autonome, stockage local, services et minuteurs installés ; lecture manuelle mise en file pour éviter les collectes concurrentes.
- [x] Interface mobile : mesures, dates, fraîcheur, état des capteurs, mesures en attente, progression et résultat des lectures.
- [x] Accès protégé par authentification ; action manuelle protégée par jeton ; aucun secret ni commande d’administration exposés par la page. Utilisation locale : ce constat ne vaut pas validation d’une exposition Internet.
- [x] Adresse domicile conservée dans la configuration privée ; historique météo : /weather. L’adresse peut changer sur un autre réseau.
- [x] Consultation iPhone à domicile confirmée par l’utilisateur.
- [x] Partage de connexion iPhone configuré et accès depuis l’iPhone fournisseur du partage confirmé par l’utilisateur.
- [x] Crassula : graphiques, bilan quotidien, plage d’éclairage réglable, historique dédié et copie journalière installés.
- [x] Synchronisation PC/Pi des relevés et des horaires, déduplication et conflits de réglages pris en charge.
- [x] Collecte Netatmo indépendante sur Pi active ; prévisions Météo-France via Open-Meteo disponibles à la consultation, distinctes d’AROME-PI direct.
- [x] Collecte pendant l’arrêt nocturne du PC puis import au retour validés le 15/10 : 14 relevés capteurs et 204 observations météo, rejeu vide.
- [x] Sauvegardes SQLite, copie PC et restauration météo sur copie vérifiées.
- [x] Alimentation : `throttled=0x0` le 15/10, aucune sous-tension signalée depuis le démarrage du 19/09. Ce constat ne garantit pas les alimentations futures.

### Actions restantes

- [ ] Tester un redémarrage matériel du Pi et vérifier interface, services, minuteurs et conservation des données après retour.
- [ ] Tester un autre Wi-Fi que le domicile et le partage iPhone.
- [ ] Formaliser puis tester la procédure pour retrouver le Pi après changement de réseau (nom local si disponible, sinon adresse attribuée par le routeur).
- [ ] Confirmer l’ajout d’un favori/raccourci iPhone ; ne pas le considérer créé sans confirmation utilisateur.
- [ ] Confirmer sur iPhone le confort des graphiques, des prévisions et la copie des données journalières.
- [ ] Traduire le nouvel écran d’éclairage PC en anglais ; envisager des versions datées des horaires pour préserver les analyses passées.
- [ ] Tester explicitement démarrage sans Internet, dates non fiables, capteur absent, arrêt du processus et reprise après perte réseau.
- [ ] Vérifier la rétention des journaux, l’espace disque et la procédure de déploiement/retour arrière ; cloner la microSD après validation.
- [ ] Auditer le secours Bluetooth PC coordonné, les alertes de retard et les anciennes archives historiques mentionnés dans la fiche de septembre, sans supposer ces essais terminés.
- [ ] Accès direct AROME-PI : autorisation et prévision locale à valider avant activation de son minuteur (indépendant du bloc Open-Meteo installé).

Les anciens détails de planification sont conservés dans l’archive de conversation `outputs/ARCHIVE_TODO_RASPBERRY_2026-09_2026-10-15.md`, à titre documentaire uniquement. Aucun test restant n’est coché par simple déduction.

- [x] Ajouter un aperçu manuel Home Assistant sans import : contrôle anti-doublons relu avant requête, interface FR/EN et états reçus affichés uniquement en mémoire.

- [x] Préparer l’archive transactionnelle Home Assistant séparée des plantes : reçu et progression dans la même transaction, reprise idempotente, révisions conservées, alias d’entités sans duplication de fait physique/datation HA.
- [x] Raccorder le rattrapage manuel à son récapitulatif, sa confirmation et sa progression transactionnelle.
- [ ] Vérifier la conservation Recorder et effectuer le premier essai sur un capteur Zigbee réel avant toute activation automatique.

- [x] Valider le parcours manuel Home Assistant de bout en bout en simulation : 50 tests, confirmation explicite, reprise après interruption, refus en démo et collecte persistante inchangée.

### Finition de l’historique d’éclairage — 15/10/2026
- [x] Traduire en français/anglais l’écran PC dédié : accès depuis Historique, horaires, tableau, relevés, aide, boutons et bilan.
- [x] Remplacer les exceptions brutes de cette fenêtre par des erreurs compréhensibles et traduites.
- [x] Vérifier ouverture et chargement des relevés en FR/EN, sans modifier les préférences ni les mesures.
- [ ] Traduire également les dialogues et bilans de synchronisation des horaires (module lamp_sync), encore en français.
- [ ] Versions datées des horaires : décision et réalisation restent séparées de la traduction terminée.


### Interface de l’historique pendant l’éclairage — 15/10/2026

- [x] Séparer horaires, résumés, journée détaillée et comparaison des jours.
- [x] Adapter le graphique et la palette à la fenêtre ; défilement principal et tableaux ; commandes fixes en bas.
- [x] Relier les points au tableau, copier la journée sélectionnée et distinguer les horaires non enregistrés.
- [x] Mettre les textes nouveaux dans les catalogues FR/EN et vérifier les vues sur données fictives sans toucher aux mesures.

- [x] Compléter l’historique éclairage avec les bornes observées, l’intervalle maximal et le statut horaire sans promesse de couverture ; navigation et sélection des jours synchronisées, tests FR/EN.

### Interface Raspberry bilingue — 15/10/2026
- [x] Français / English en haut des pages ; préférence conservée un an par cookie local HttpOnly/SameSite, par navigateur, défaut français.
- [x] Traduire les pages capteurs et météo : graphiques, plages d’éclairage, copie journalière, prévisions, états de collecte, aides et erreurs ; formats de dates/nombres adaptés à la langue, fuseaux et calculs inchangés.
- [x] Vérifier les deux scripts dans les deux langues, les clés API/CSRF inchangées et le choix de langue ; essais HTTP réels sur Pi avec identifiants fictifs : 401 sans connexion, cookie/navigation/API corrects.
- [x] Installer après sauvegarde ; service web actif. Module de traduction ajouté aux scripts d’installation.
- [ ] Confirmer le rendu et le passage FR/EN sur iPhone réel ; aucune autre langue ajoutée dans cette étape.

- [x] Harmoniser l’historique éclairage avec la palette principale partagée et remplacer les onglets natifs peu lisibles par des boutons texte contrastés, sans symboles dépendants de Windows.


### Démo éclairage — 15/10/2026

- [x] Isoler les horaires démo et bloquer la résolution Pi avant toute lecture de configuration réelle.
- [x] Rafraîchir le jeu fictif après sauvegarde de l’ancienne démo : quatre plantes, 480 relevés, zéro et trou de relevés.
- [x] Vérifier les chemins isolés dans un nouveau processus, le générateur fictif et la non-régression de la synchronisation réelle en tests.

### Synchronisation des horaires FR/EN — 16/10/2026
- [x] Traduire bilans, erreurs, reprise différée et dialogue de conflit dans la langue du PC.
- [x] Présenter les choix sous forme d’horaires lisibles (09:50–15:50) au lieu de structures techniques ; signaler un réglage absent.
- [x] Tests de synchronisation existants réussis ; dialogue de conflit et annulation vérifiés en français et anglais avec données fictives, sans appel réseau ni modification d’horaires.
Cette livraison clôt le point de traduction des dialogues lamp_sync resté ouvert le 15/10. Les tests matériels et tactiles restent à confirmer.

- [x] Stabiliser les accès Home Assistant en démo (16/10/2026) : tous les points de lecture refusent le mode démo avant réseau/configuration privée ; exemple fictif de quatre états dans le même écran, textes FR/EN et tests.


### Contrôles avant prochaine archive — 16/10/2026

- [x] Bloquer la construction si un module Python local requis manque ou si un chemin privé/base/sauvegarde est fourni.
- [x] Ajouter `prepare_release.py --check-files` pour contrôler sans créer d’archive ni modifier les versions.
- [x] Vérifier une liste candidate de 153 fichiers avec 34 dépendances locales supplémentaires nécessaires ; voir `docs/PREPARATION_ARCHIVE_CONTROLES.md`.
- [ ] Avant prochaine release : relire et intégrer explicitement les fichiers publics validés, refaire les contrôles de secrets puis tester une extraction isolée réelle/démo. La sélection Git actuelle ne suffit pas.

### Présentation météo mobile — 17/10/2026
- [x] Remplacer la longue liste d’heures par une carte : températures min/max prévues, bande horaire horizontale avec température/pluie, courbe température et barres de pluie alignées, détails au toucher.
- [x] Conserver dates, source, périodes de pluie et état du cache ; traductions FR/EN ajoutées.
- [x] Syntaxe des deux langues et cas simulés vide/absence/zéro/température négative/sélection vérifiés ; installé après sauvegarde, service actif.
- [ ] Confirmer le rendu réel et le confort tactile de cette nouvelle carte sur iPhone.


### Validation d’extraction candidate — 17/10/2026

- [x] Construire et extraire un ZIP temporaire non officiel incluant les 34 dépendances locales nécessaires.
- [x] Vérifier depuis l’extraction : démarrage démo, isolation des fichiers, éclairage, exemple HA et cohérence VERSION ; aucune tentative réseau ni erreur GUI sur le parcours court.
- [ ] Relecture puis intégration explicite des sources/documents/tests publics avant préparation officielle.
- [ ] Installation et dépendances sur PC vierge, puis contrôle de mise à jour de bout en bout avant diffusion ; non couverts par ce test d’extraction.

### Validation locale de préparation Windows — 17/10/2026
- [x] Archive candidate extraite dans un dossier temporaire, environnement Python vide sans paquets hérités, installation via Installer_Gruterra.bat et cohérence des dépendances vérifiées.
- [x] Vraie démo démarrée via Lancer_Demo.bat avec les dépendances nouvellement installées ; parcours court éclairage et exemple Home Assistant vérifiés sans réseau GUI.
- [ ] Tester le téléchargement et l'installation automatique de Python 3.12.10 sur un PC qui ne possède pas Python.
- [ ] Finaliser la sélection Git des fichiers publics et valider la mise à jour complète d'une ancienne version avant publication autorisée.

### Repères de la carte météo — 17/10/2026
- [x] Distinguer Aujourd’hui/Demain dans la bande horaire et les détails, en FR/EN ; dates selon le fuseau du téléphone.
- [x] Afficher la plage horaire couverte par chaque cumul de pluie prévu.
- [x] Signaler visuellement un cache ancien ou un échec de rafraîchissement, sans masquer les anciennes valeurs ni les présenter comme nouvelles.
- [x] Syntaxe FR/EN et compilation Pi validées, service actif après installation.
- [ ] Confirmation visuelle sur iPhone toujours attendue pour cette carte compacte.

### Santé et stockage du Raspberry — 17/10/2026
- [x] Contrôle réel : partition 15 Go, 3,2 Go utilisés (24 %), environ 11 Go libres ; données Gruterra 1,4 Mo et sauvegardes 8,3 Mo.
- [x] Aucun service utilisateur en échec ; collecte capteurs 18:02, météo 18:05 et sauvegarde quotidienne 04:17 terminées avec succès.
- [x] Alimentation : throttled=0x0 au contrôle.
- [x] Sauvegardes : 14 fichiers capteurs quotidiens, 6 météo actuellement ; intégrité SQLite des dernières copies du 17/10 validée en lecture seule. Rotation capteurs limitée à 14 jours vérifiée dans le programme.
- [x] Journaux : journald en stockage volatile (RAM), 16,4 Mo ; /var/log 1,1 Mo ; rsyslog inactif. Les journaux journald actuels ne persistent pas après redémarrage. Aucune limite personnalisée ajoutée, aucune purge effectuée.
- [ ] Si un diagnostic après redémarrage devient nécessaire, décider d’une conservation persistante bornée des journaux. Pas nécessaire au fonctionnement actuel.
Les tests matériels de redémarrage et les validations tactiles restent ouverts ; ce contrôle ne les remplace pas.

- [x] 17/10 : application réelle du ZIP candidat sur copie temporaire à version fictive, contrôle de la sauvegarde et des empreintes privées, puis redémarrage de la vraie démo réussis (transport réseau simulé).
- [ ] Compléter par une ancienne release officielle, le téléchargement GitHub et l'enchaînement automatique fermeture/relance ; le scénario fictif ne valide pas ces trois éléments.

### Complément de validation du 17/10/2026
- [x] Mise à jour depuis l'archive 0.1.5-dev conservée, SHA-256 conforme au manifeste local, conservation des fichiers privés contrôlés et relancement de la démo.
- [x] Fermeture et relance automatiques de la vraie interface démo via le mécanisme applicatif, dans une extraction temporaire (essai distinct de l'application du ZIP).
- [ ] Parcours unique depuis le téléchargement GitHub jusqu'à la relance après application ; installation de Python sur poste vierge ; sélection finale des fichiers Git et publication autorisée.

### Redémarrage matériel validé — 17/10/2026
- [x] Redémarrage effectué par l’utilisateur via sudo reboot ; nouvel identifiant de démarrage confirmé, retour à 19:36 heure de Paris.
- [x] Interface web revenue automatiquement (active, accès anonyme refusé HTTP 401), aucun service utilisateur en échec.
- [x] Minuteurs capteurs, météo et sauvegarde actifs et activés au démarrage ; prochaines échéances annoncées : météo 20:05, capteurs 23:00, sauvegarde le 18/10 vers 04:16.
- [x] Bases capteurs et météo lisibles et intègres après redémarrage : 189 mesures ponctuelles, 826 historiques, 852 observations météo.
- [x] Horloge NTP synchronisée, fuseau Europe/Paris ; throttled=0x0 après redémarrage.
- [x] Collecte météo automatique après redémarrage confirmée au contrôle du 17/10 à 21:19 : minuteur à 21:06:12, service réussi et données récupérées à 21:06:21 (Paris). Voir validation ci-dessous.
Les anciennes cases « tester un redémarrage » sont remplacées par cette validation. Les essais tactile/iPhone et autre Wi-Fi restent ouverts.

### Résultat du parcours GitHub réel — 17/10/2026
- [x] Updater de la 0.1.5-dev : téléchargement réel de la 0.1.6-dev officielle, empreinte, sauvegarde, application, conservation des deux fichiers privés contrôlés et ouverture de la démo validés.
- [ ] PRIORITÉ prochaine release : intégrer le correctif local de relance et _app/restart_gruterra.py. Échec de la relance automatique reproduit sur la 0.1.6-dev publiée : seconde instance lancée avant fermeture de la première, puis arrêt sans interface. Correctif local déjà testé ; pas encore diffusé.
- [ ] Vérifier ce même parcours avec la future archive corrigée avant annonce. Ne pas considérer la relance de la version publiée comme validée.

### Reprise après redémarrage — contrôle complet du 17/10/2026
- [x] Le service collecteur permanent a lancé sa lecture au démarrage : historique parcouru puis collecte terminée à 19:40 ; une nouvelle mesure importée sur le PC, file vide.
- [x] Collecte Netatmo de contrôle déclenchée manuellement après redémarrage : service réussi à 19:39, nouvelles dates de récupération confirmées.
- [x] Synchronisation météo : 81 observations en attente importées (stock antérieur inclus), rejeu vide sans nouvel ajout, sauvegarde existante vérifiée.
- [x] Collecte météo automatique après redémarrage confirmée au contrôle du 17/10 à 21:19 : minuteur à 21:06:12, service réussi et données récupérées à 21:06:21 (Paris). Voir validation ci-dessous.
Reprise du collecteur au démarrage, collecte météo manuelle et transfert PC validés ; aucune donnée supprimée.

### Correctif relance prêt localement — 17/10/2026
- [x] Protection de préparation ZIP contre l'absence du helper de relance ajouté ; sept tests de contenu passent.
- [x] Scénario unique local : application du candidat, sauvegarde, conservation des fichiers privés contrôlés, fermeture et relance de la vraie démo réussis.
- [ ] Diffuser le correctif dans une prochaine version autorisée et refaire le parcours depuis le téléchargement officiel. La 0.1.6-dev publiée reste inchangée.

### Accès local et changement de réseau — 17/10/2026
- [x] Documenter l’adresse par nom http://botaneo-pi.local:8765 et le recours à l’IP dans docs/ACCES_LOCAL_RASPBERRY.md.
- [x] Vérifier avahi actif et activé au démarrage ; accès Windows au nom local répond HTTP 401 (authentification requise). La capture iPhone du 17/10 confirme l’utilisation de ce nom au domicile.
- [x] Documenter la recherche via routeur, les réseaux invités et le raccourci Safari.
- [ ] Tester cette procédure sur un autre Wi-Fi et confirmer la création du raccourci iPhone.
- [x] Collecte météo automatique après redémarrage confirmée au contrôle du 17/10 à 21:19 : minuteur à 21:06:12, service réussi et données récupérées à 21:06:21 (Paris). Voir validation ci-dessous.

### Corrections locales de protection des données — 17/10/2026
- [x] Protéger toutes les bases SQLite et leurs fichiers associés, notamment `_app/plantes.db`, même si une archive les contient par erreur. Protéger aussi les configurations `.local.json`, `_user_backups` et `.venv`, indépendamment de la casse des chemins.
- [x] Éviter l’écrasement d’une sauvegarde par une autre créée dans la même seconde : réservation atomique d’un nom unique.
- [x] Douze tests updater réussis ; scénario intégré d’application, sauvegarde, conservation et relance automatique de la démo revérifié avec succès.
- [ ] Inclure ces correctifs dans la prochaine version lorsque sa publication sera décidée. Aucun changement de version ni publication maintenant.

### Corrections graphiques locales — 17/10/2026
- [x] Pluie Météo-France : pied de fenêtre réservé aux actions, Actualiser et Fermer visibles à 620 × 440 ; recherche et choix de commune sur deux lignes ; textes adaptés à la largeur.
- [x] Observations météo importées : reprise du thème principal, tableaux clair/sombre harmonisés, actions fixes et bouton Fermer.
- [x] Harmonisation partagée des tableaux et sélecteurs ttk, styles séparés par palette pour éviter de recolorer une autre fenêtre.
- [x] Géométrie et couleurs contrôlées FR/EN et clair/sombre ; actions Home Assistant contrôlées en fenêtre compacte ; aperçu fictif HA FR/EN et six tests nappes réussis.
- [ ] Poursuivre la revue des autres dialogues : ces contrôles ciblés ne constituent pas une validation de toutes les interfaces, ni un contrôle à tous les niveaux de zoom Windows.


### Horaires d’éclairage datés PC/Pi — 17/10/2026
- [x] Conserver les anciennes plages et la date d’application des changements, en heure de Paris.
- [x] Calculer les bilans et graphiques selon la plage du jour d’allumage ; gérer les plages passant minuit.
- [x] Synchroniser le profil complet avec ses dates, conserver la détection des conflits et bloquer un envoi daté vers un ancien exporteur Pi.
- [x] Déployer sur le Raspberry après sauvegarde des fichiers ; service web actif, accès anonyme refusé (401), horaires existants inchangés.
- [x] Vérifier 17 tests ciblés, les fenêtres PC FR/EN sur données fictives et la syntaxe des scripts mobiles FR/EN.
- [x] Vérifier une synchronisation réelle PC/Pi : zéro changement, réglages concordants.
- [ ] Vérifier visuellement sur l’iPhone après actualisation, puis constater le premier changement réel d’horaire à la prochaine modification souhaitée.

Règle : un changement enregistré prend effet à la date du jour à Paris. Plusieurs modifications le même jour remplacent la plage de ce jour. Une plage nocturne appartient au jour où elle commence. Les dates anciennes sans historique utilisent le réglage précédemment connu : aucun changement passé n’est reconstitué. Une moyenne reste celle des relevés disponibles, sans interpolation ni estimation d’exposition totale.

### Collecte automatique et essai de restauration — 17/10/2026
- [x] Confirmer le minuteur météo actif et activé, déclenchement à 21:06:12 et fin réussie à 21:06:21 après le redémarrage de 19:36.
- [x] Confirmer dans la base une date de récupération réelle 2026-10-17T19:06:21Z ; la réussite du service seule n’a pas servi de preuve.
- [x] Restaurer les dernières sauvegardes capteurs et météo dans un répertoire temporaire, vérifier empreintes, intégrité SQLite et nombres de lignes.
- [x] Relire ces copies avec les fonctions actuelles de l’interface et vérifier une écriture transactionnelle annulée : 184 mesures ponctuelles, 805 historiques capteurs et 723 observations météo dans les sauvegardes du 17/10.
- [x] Conserver l’outil réutilisable raspberry/check_backup_restore.py, également installé dans le dossier collector du Pi. Aucun minuteur ajouté.
Les bases actives et sauvegardes sources n’ont pas été remplacées. Cet essai valide la récupération des bases à la date de la sauvegarde, pas une restauration complète du système ou des accès privés. Les données collectées après cette sauvegarde n’y figurent pas.

### Sécurité de publication — 17/10/2026
- [x] Contrôle des valeurs : modèles vides acceptés, champs privés remplis bloqués, données locales toujours exclues.
- [x] Dix tests de sécurité réussis ; rares valeurs fictives relues limitées à l’empreinte exacte du fichier, aucune exemption permanente de contenu.
