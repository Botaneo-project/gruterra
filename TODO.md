# TODO Gruterra

Ce fichier sert à garder une trace claire des idées et des prochaines étapes. Les éléments déjà en place sont conservés ici uniquement pour savoir où on en est, mais ils ne doivent plus être relancés sauf bug ou amélioration ciblée.

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
- [ ] Publier une première release ZIP officielle avec SHA256 pour activer réellement `--apply`.
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

- [x] Installation neuve : créer le schéma principal `plantes`, `capteurs`, `mesures` directement dans `database.py`, avec clés étrangères actives et index utiles.

## GitHub, sauvegarde et sécurité

- Maintenir `README.md`, `RASPBERRY.md`, `TODO.md` et `CONTEXTE_AGENT_BOTANEO.md` à jour après les grosses évolutions.
- Lancer `py verifier_avant_github.py` avant chaque commit/push.
- Ne jamais stocker les tokens Netatmo, Météo-France, e-mail, clés SSH ou bases réelles dans GitHub.
- Garder les secrets dans des fichiers locaux ignorés par Git, surtout `_config/`.
- Garder uniquement des fichiers `.example.json` anonymes dans GitHub.
- Lire la liste des fichiers modifiés avant chaque envoi GitHub, même si le dépôt est privé.
- Ne pas pousser un fichier de contexte interne détaillé sans validation explicite si le contrôle automatique le juge sensible.
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

- [ ] Assumer Gruterra comme projet francophone tant que l'interface n'est pas traduite.
- [ ] Préparer plus tard un vrai système de traduction de l'interface, sans dupliquer toute la logique métier.
- [x] Ajouter un premier README anglais `README_EN.md` et un guide démo anglais `GUIDE_DEMO_EN.md`.
- [ ] Identifier les prochains textes publics à traduire : aide installation, Netatmo, Raspberry, erreurs fréquentes.
- [ ] Éviter de présenter Discord ou GitHub comme entièrement anglophones tant que l'application reste française.
