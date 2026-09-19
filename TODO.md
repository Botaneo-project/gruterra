# TODO Botaneo

Ce fichier sert à garder une trace claire des idées et des prochaines étapes. Les éléments déjà en place sont conservés ici uniquement pour savoir où on en est, mais ils ne doivent plus être relancés sauf bug ou amélioration ciblée.

## État actuel déjà en place

- Interface graphique principale avec mode sombre et plusieurs teintes.
- Mode clair harmonisé avec une palette Botaneo plus douce et cohérente avec le mode sombre.
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
- Mode démo ajouté pour tester Botaneo avec une base fictive, sans capteur, token ou données personnelles.

## Priorité courte

### 1. Finaliser les alertes

- Terminer l’affichage clair de l’état batterie : OK, à surveiller, faible.
- Garder le seuil batterie modifiable dans les paramètres.
- Préparer les alertes par plante, sélectionnables depuis l’interface.
- Prévoir les rappels par e-mail pour les plantes sans capteur ou hors domicile.
- Utiliser Outlook local plus tard, puisque le PC est déjà configuré.
- Mémoriser la dernière alerte envoyée pour éviter un e-mail à chaque synchronisation.
- Ajouter un délai minimal entre deux alertes identiques.
- Ne pas envoyer d’e-mail automatiquement tant que le destinataire et les règles ne sont pas validés.

### 2. Améliorer l’interface quand il y aura beaucoup de plantes

- Prévoir une vue compacte pour éviter de devoir défiler si on a 30 à 50 plantes.
- Améliorer plus tard les filtres plantes si besoin : recherche par nom, tri manuel, regroupement par pièce.
- Garder une zone de décision visible au-dessus des graphiques.
- Permettre à terme de choisir l’ordre des blocs : météo locale, plantes, alertes, graphiques.
- Continuer à améliorer la lisibilité des graphiques en mode sombre.

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

## Historique Mi Flora

- Tester sur le capteur réel le bouton manuel `Importer historique Mi Flora`.
- Convertir plus tard les entrées historiques brutes en mesures datées quand la reconstruction des dates sera validée.
- Ne jamais activer l’effacement de la mémoire Mi Flora sans validation claire.
- Garder les entrées douteuses à part plutôt que remplacer les mesures existantes.
- Surveiller les prochains essais : si Windows coupe encore la lecture historique, les entrées déjà lues restent conservées.

## Analyse plante et prévisions 48-72 h

À faire quand il y aura assez d’historique fiable.

- Ajouter une zone de décision en haut : `À faire aujourd’hui`, `À surveiller`, `Prévision 48-72 h`.
- Exemple : `Votre Crassula devrait nécessiter une intervention dans les prochaines 24 h.`
- Calculer les tendances d’humidité du sol.
- Estimer le prochain arrosage probable.
- Détecter une baisse de luminosité sur plusieurs jours.
- Comparer la température actuelle avec la moyenne récente.
- Interpréter prudemment la conductivité, sans alerte trop agressive.
- Croiser les besoins de base de la plante avec les mesures réelles.

## Journal d’événements plante

- Garder l’historique des arrosages manuels.
- Ajouter plus tard d’autres événements depuis l’interface : observation, rempotage, déplacement, engrais, taille, changement de capteur.
- Afficher ces événements dans la fiche plante.
- Utiliser ces événements pour mieux interpréter les courbes.

## GitHub, sauvegarde et sécurité

- Préparer un README propre pour expliquer le projet.
- Prévoir un dépôt GitHub quand le projet sera assez stable.
- Ne jamais stocker les tokens Netatmo, Météo-France ou e-mail dans GitHub.
- Garder les secrets dans des fichiers locaux ignorés par Git.
- Prévoir une sauvegarde simple de la base de données.
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
- Garder des couleurs dans les tuiles météo, mais utiliser seulement la palette Botaneo pour éviter un rendu instable.
- Organiser la météo en trois niveaux : synthèse météo locale, stations favorites, stations proches repliées.
- Ajouter un statut météo court en haut, par exemple : `Météo locale : sec prévu · vent faible · station favorite active`.
- Réduire le bruit visuel dans Netatmo : moins d’emojis répétés, titres plus courts, valeurs mieux alignées.
- Rendre les boutons secondaires Netatmo plus discrets : `↑`, `↓`, `Renommer`.
- Prévoir plus tard de vraies petites icônes météo locales dans `assets`, plutôt que de dépendre des emojis Windows.
- Revoir le logo d’en-tête avec une vraie version icône simplifiée, pensée pour une petite taille.




## Raspberry : suivi Windows installé le 16 septembre 2026

- [x] Carte de disponibilité Raspberry dans Botaneo, contrôle SSH manuel et quotidien.
- [x] Heure, délai de nouvel essai et tolérance configurables ; mode déplacement.
- [x] Dernier contact, dernière tentative, erreur, prochain essai et retour à la normale.
- [x] Persistance des incidents sans doublons et rattrapage après fermeture du PC.
- [ ] Développer la collecte autonome et la file locale sur le Pi.
- [ ] Ajouter la vraie synchronisation des mesures vers le PC avec accusé et déduplication.
- [ ] Afficher dernière synchronisation confirmée et nombre de mesures en attente.
- [ ] Prévoir un composant Windows en arrière-plan si un suivi application fermée est souhaité.

Le suivi installé est celui de la disponibilité : aucune réussite SSH ne compte comme mesure synchronisée.

## Synchronisation : Raspberry prioritaire (17 septembre 2026)

- [ ] Pour les capteurs affectés au Raspberry, récupérer ses mesures en priorité lors de la synchronisation PC.
- [ ] Confirmer leur enregistrement au Pi seulement après validation de la transaction dans la base PC.
- [ ] Dédupliquer les entrées historiques déjà récupérées directement par le PC, au-delà des seuls identifiants du collecteur ; préserver les trames et tenir compte des réinitialisations de l’horloge du capteur.
- [ ] Si le Pi est inaccessible, afficher le retard et réessayer plus tard, sans basculement Bluetooth automatique.
- [ ] Garder la lecture Bluetooth PC en secours manuel pour ces capteurs, avec coordination pour éviter les connexions simultanées.
- [ ] Conserver la collecte PC directe pour les capteurs non affectés au Raspberry.
- [ ] Tester un historique commun aux deux machines : aucun doublon ni perte après interruption.

Cette priorité reste à développer. La collecte autonome du Pi et la récupération de son historique sont opérationnelles ; le transfert vers la base Windows ne l’est pas encore.

## Synchronisation Raspberry installée — 17 septembre 2026

Le PC récupère désormais les données du Raspberry en priorité pour ses capteurs, avec confirmation après enregistrement et reprise sans doublons. Aucun basculement Bluetooth automatique si le Pi est absent ; les autres capteurs conservent leur lecture PC directe. Relancer Botaneo pour charger cette version.

La carte Raspberry récupère réellement les mesures. Horaire quotidien existant, reprises après échec et rattrapage à l'ouverture ; application ouverte nécessaire. Le mode déplacement suspend aussi le transfert manuel. Collecte Pi maintenue toutes les huit heures environ.

Validation : 12 tests, interface testée, transfert réel de 121 relevés, deuxième passage sans ajout, intégrité SQLite correcte. L'archive brute a reconnu 61 trames existantes sans les modifier. Sauvegarde : `_security_backups/raspberry_sync_20260917_225607`.

- [x] Transfert Pi prioritaire et conservation des autres collectes PC.
- [x] Accusé après transaction, reprise et déduplication des historiques.
- [x] Conservation des trames brutes et de la qualité des dates.
- [ ] Secours Bluetooth manuel coordonné.
- [ ] Alerte sur l'ancienneté des mesures, distincte du succès du transfert.
- [ ] Tests physiques de coupure, retour prolongé et restauration avec remise en attente des données du Pi.

Cette section remplace les anciennes mentions « transfert à développer ».


## Historique et graphiques — correction du 18 septembre 2026

- [x] Cause identifiée : la synchronisation Bluetooth PC alimentait l'archive brute sans appeler l'importeur des mesures affichées.
- [x] Raccorder l'importeur existant après archivage, avec validation des horloges et déduplication ; quatre tests réussis.
- [x] Préserver les lectures partielles dans l'archive et signaler l'absence d'ajout aux graphiques.
- [ ] Comparer les périodes et lectures partielles pour expliquer les 53 historiques supplémentaires du Pi.
- [ ] Auditer les anciennes archives sans inventer leurs repères temporels.
- [ ] Vérifier une prochaine lecture réelle sur un capteur lu directement par le PC.

Relancer Botaneo pour charger la correction. Les 121 mesures transférées du Pi le 17 septembre restent en place ; cette correction concerne les prochaines lectures Bluetooth directes du PC.


## Récupération Raspberry — 19 septembre 2026

Récupération à chaque ouverture de Botanéo, puis toutes les 15 minutes par défaut tant que l’application reste ouverte, après succès comme après échec. Intervalle réglable dans la carte Raspberry. Le mode déplacement et la désactivation suspendent les tentatives. Aucune tâche Windows permanente ajoutée, aucune collecte Bluetooth du Pi déclenchée. Relancer Botanéo pour charger cette version. Huit tests de planification réussis.

- [x] Copie vérifiée de la dernière sauvegarde Pi sur le PC après synchronisation.
- [ ] Définir une rétention des copies de sauvegarde sur le PC.
- [ ] Tester le cycle déplacement / nouveau capteur / retour / récupération PC.
