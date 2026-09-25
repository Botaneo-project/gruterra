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
- Script `verifier_avant_github.py` ajouté pour contrôler les fichiers sensibles avant commit ou push.
- Dépôt GitHub privé initialisé et utilisé pour sauvegarder les évolutions validées.
- Statut de synchronisation copiable depuis l’interface.
- Synchronisation : sous-étapes détaillées pendant les phases longues.
- Lecture historique Mi Flora PC en plusieurs passes, sans effacement, avec reprise partielle et signalement des données manquantes.
- Synchronisation manuelle : récupération Raspberry en priorité, puis lecture Bluetooth PC de secours si aucune mesure fraîche ne remonte.
- Raspberry : collecte planifiée quatre fois par jour via `botaneo-collect.timer`.
- Raspberry : scripts d’installation et de mise à jour disponibles dans `raspberry/install/`.
- Écran historique enrichi avec résumé, tendance, repères post-arrosage et qualité des données.
- Historique : sélection d’une journée avec moyennes, minimums/maximums et pic lumineux du jour.
- Fenêtre `À propos` ajoutée : version locale, révision Git, chemins utiles, état Raspberry et rappel sécurité.
- Document de reprise agent créé : `CONTEXTE_AGENT_BOTANEO.md` avec architecture, Raspberry, secrets, process GitHub, Plante de Jade et priorités.

## Prochaine suite recommandée

- Priorité réelle : démarrer l’analyse par cycle d’arrosage en version simple, sans surinterpréter les données.
- Pour chaque cycle : repérer l’humidité avant arrosage, le pic observé, la baisse après pic et la qualité des mesures disponibles.
- Stabiliser l’analyse plante autour de l’arrosage : phrase courte, repères 10 min / 1 h / 24 h / 48 h et comparaison avant/après.
- Garder le Bluetooth et la synchronisation Raspberry en observation pendant quelques cycles avant de modifier encore la collecte.
- Reprendre ensuite l’interface des alertes, sans envoyer de mails automatiquement.

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
- [ ] Distinguer tendance globale, vitesse de séchage entre arrosages et réponse à l’arrosage.
- [ ] Construire une analyse par cycle d’arrosage : humidité initiale, réponse à l’arrosage, pic observé, phase de séchage, retour au niveau initial.
- [ ] Reformuler l’analyse post-arrosage pour éviter de confondre zone du capteur et motte complète : `Retour au niveau d’humidité initial détecté dans la zone du capteur. Le Mi Flora ne permet pas de confirmer le séchage complet de la motte.`
- [x] Ajouter aux événements d’arrosage des champs facultatifs : volume total, type d’eau, méthode de répartition, écoulement observé, eau stagnante dans le cache-pot, état visuel du substrat et commentaire libre.
- [ ] Ne pas imposer automatiquement 80 ml : garder la comparabilité des cycles sans empêcher d’adapter l’arrosage aux besoins réels.
- [ ] Calculer la vitesse moyenne de séchage en points d’humidité par jour entre le pic confirmé et la fin du cycle.
- [ ] Ajouter une vitesse glissante sur 24 h pour repérer un ralentissement ou une accélération du séchage.
- [ ] Attribuer une qualité à chaque cycle selon les trous de mesure : régulier, manque léger, prudence, interruption longue.
- [ ] Éviter d’interpréter précisément un cycle si le pic ou le retour au niveau initial tombe dans une interruption longue.
- [ ] Comparer les cycles seulement quand les conditions sont proches : quantité d’eau, type d’eau, emplacement, lumière, température, substrat.
- [ ] Construire progressivement une référence propre à chaque plante après plusieurs cycles documentés.
- [ ] Estimer le prochain arrosage probable quand les données sont suffisantes.
- [ ] Détecter une baisse de luminosité sur plusieurs jours.
- [ ] Ajouter les événements `Sortie sur le balcon` et `Retour à l’intérieur` dans le journal plante.
- [ ] Distinguer les journées entièrement en intérieur des journées avec exposition extérieure.
- [ ] Calculer les durées d’exposition par plages de luminosité, au lieu de se limiter au maximum du jour.
- [ ] Calculer une exposition lumineuse cumulée quotidienne en tenant compte des intervalles entre mesures.
- [ ] Éviter qu’un pic lumineux ponctuel masque une journée globalement sombre.
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

- [ ] Prévoir un système d’auto-upgrade pour les utilisateurs ayant déjà téléchargé Botaneo.
- [ ] Avant toute mise à jour automatique, sauvegarder la base locale, la configuration et les fichiers de secrets ignorés par Git.
- [ ] Distinguer mise à jour du programme et conservation des données personnelles : base réelle, tokens Netatmo, favoris, paramètres Raspberry, alertes.
- [ ] Garantir que le dossier personnel de l’utilisateur reste conservé pendant les mises à jour : données, configuration locale, favoris, secrets, sauvegardes et éventuelles images/cache local.
- [ ] Séparer clairement le dossier programme du dossier utilisateur pour faciliter les mises à jour sans perte de données.
- [ ] Prévoir un mode simple : vérifier la version disponible sur GitHub, proposer la mise à jour, puis appliquer seulement après validation.
- [ ] Prévoir un mode avancé plus tard : script de mise à jour Windows et script de mise à jour Raspberry.
- [ ] Afficher clairement la version installée et la dernière version disponible dans l’interface.

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
- Garder des couleurs dans les tuiles météo, mais utiliser seulement la palette Botaneo pour éviter un rendu instable.
- Organiser la météo en trois niveaux : synthèse météo locale, stations favorites, stations proches repliées.
- Ajouter un statut météo court en haut, par exemple : `Météo locale : sec prévu · vent faible · station favorite active`.
- Réduire le bruit visuel dans Netatmo : moins d’emojis répétés, titres plus courts, valeurs mieux alignées.
- Rendre les boutons secondaires Netatmo plus discrets : `↑`, `↓`, `Renommer`.
- Prévoir plus tard de vraies petites icônes météo locales dans `assets`, plutôt que de dépendre des emojis Windows.
- Revoir le logo d’en-tête avec une vraie version icône simplifiée, pensée pour une petite taille.

## Raspberry et synchronisation

État actuel : le PC récupère les données du Raspberry en priorité, confirme les mesures après enregistrement, évite les doublons et copie la dernière sauvegarde quotidienne du Pi. Le Raspberry demande maintenant une collecte Mi Flora quatre fois par jour : 06 h, 12 h, 18 h et 23 h. Le PC peut encore faire une lecture Bluetooth manuelle de secours si le Raspberry ne fournit pas de mesure fraîche.

- [x] Carte de disponibilité Raspberry dans Botaneo, contrôle SSH manuel et quotidien.
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
