# Gruterra — météo Raspberry, préparation du 12 octobre 2026

## État réel

Le PC conserve son accès Netatmo pour une météo fraîche et actualise son cache sans ajouter de nouvelles pluies à l'historique. Ses identifiants et son historique n'ont pas été modifiés par cette préparation.

Le Raspberry dispose des commandes d'export/accusé, d'un collecteur préparé et d'une sauvegarde météo. La collecte est **désactivée** : aucune autorisation indépendante n'est configurée, aucun relevé réel ni cycle horaire n'est validé. L'import PC reste une option explicite dans Paramètres → Météo du Raspberry.

## Réalisé

- `weather_collect.py` : collecteur sans dépendance graphique, verrou exclusif, dates source UTC, valeurs décimales et nulles, sélection des stations publiques configurées. Données personnelles : pression de la station et modules extérieurs NAModule1/2/3 ; température et humidité intérieures exclues.
- Zéro conservé. Un champ absent ne crée pas d'observation. Le cumul public `rain_60min` est enregistré sur 3600 secondes, sans inventer les bornes exactes. Les autres cumuls restent de période inconnue tant que leur définition n'est pas confirmée : aucune somme n'est proposée.
- `weather_backup.py` : copie SQLite cohérente, contrôle d'intégrité, 14 fichiers quotidiens retenus sur le Pi. Appel intégré à la sauvegarde quotidienne existante ; un échec météo fait échouer le service, sans supprimer sa sauvegarde Mi Flora.
- `weather_backup_pc.py` : copie par SSH/SCP, vérification taille/empreinte/intégrité, reprise au prochain import. Aucune suppression des anciennes copies PC ni remplacement de base active.
- L'import PC tente la copie de sauvegarde après un transfert complet, y compris si la file est vide. Une erreur de sauvegarde apparaît dans le bilan sans invalider les observations déjà reçues.
- `weather_view.py` : bouton Observations météo importées dans les réglages météo Raspberry. Tableau FR/EN avec station, module, champ source, valeur, unité, date source UTC, récupération, période et sélection. Les révisions ambiguës sont conservées mais écartées des analyses ; les cumuls ne sont jamais additionnés.
- Unités `gruterra-weather.service` et `.timer` installées mais non activées. Horaire prévu : chaque heure à :05, décalage aléatoire jusqu'à 30 secondes, rattrapage d'un passage au démarrage. Cela ne reconstitue pas des données publiques anciennes.

## Blocage OAuth et marche à suivre

Le même refresh token ne doit pas être renouvelé séparément sur le PC et le Pi. Le souhait d'une météo PC fraîche même lorsque le Pi est absent impose de préserver l'accès PC et de fournir au Pi un accès dont l'indépendance est vérifiée. Une copie du token PC, même dans un autre fichier, ne suffit pas.

Préparer une application/autorisation Netatmo dédiée au Pi via le parcours officiel, avec le droit météo personnelle `read_station` et l'accès public requis. Vérifier ensuite que le renouvellement Pi ne casse pas l'accès PC. Ne pas transmettre les secrets dans une conversation, un commit ou une sortie de diagnostic.

Modèles anonymes : `raspberry/weather.json.example` et `raspberry/weather-oauth.json.example`. Les fichiers réels seront `~/botaneo/config/weather.json` et `weather-oauth.json`, dossier 0700 et fichiers 0600. Renseigner une petite zone autour de la station retenue à partir des coordonnées déjà configurées. Les autres favoris PC restent inchangés.

`independent_authorization` est une attestation de configuration, **pas une preuve technique d'indépendance**. Ne le passer à true qu'après contrôle de l'origine de l'autorisation. Le couple access/refresh est remplacé atomiquement et sous le verrou du collecteur. Les erreurs ne contiennent que des codes expurgés. Les identifiants ne sont ni exportés ni inclus dans la sauvegarde des observations.

## Activation future — uniquement après l'autorisation

1. Vérifier les droits, la définition des cumuls et l'accès aux stations retenues. La présence d'un scope dans un fichier ne suffit pas : vérifier une réponse API réelle.
2. Activer le réglage privé de collecte et lancer un passage manuel. Contrôler les statuts de chaque source et les dates réelles ; une station absente ne devient pas une pluie nulle.
3. Déclencher une sauvegarde météo et importer via Gruterra. Comparer dates/unités/valeurs, refaire la synchronisation et contrôler les doublons.
4. Vérifier le renouvellement OAuth et que le PC conserve son accès direct. Une erreur d'autorisation exige une reconnexion, pas une boucle rapide de tentatives.
5. Activer seulement alors `gruterra-weather.timer`. Tester un passage avec PC effectivement éteint, puis récupérer les observations à son retour.
6. Tester un redémarrage physique du Pi. Le service dispose d'une planification persistante, mais ce scénario matériel n'a pas été effectué pendant cette préparation.

Les limites publiées par Netatmo sont de 50 requêtes / 10 secondes et 500 / heure par compte. Elles concernent aussi les autres usages du compte. Budget nominal du collecteur : deux appels météo par passage, plus renouvellement éventuel ; respecter Retry-After en cas de 429. Les restrictions effectives de l'application restent à vérifier avec son autorisation.

Source : https://helpcenter.netatmo.com/hc/it/articles/32413060985618-La-mia-app-mobile-Netatmo-mostra-l-errore-MaxUsageReached-perch%C3%A9

## Vérifications effectuées et limites

37 tests météo réussis sur Windows ; 35 sur Raspberry (les deux tests spécifiques au secours PC sont exécutés sur Windows). Tests sur données fictives : renouvellement, 401, indisponibilité, 429, cache d'attente, null/absence/zéro, modules extérieurs, précision décimale, rejeu, révisions, sauvegarde/restauration puis import.

Fenêtre FR/EN ouverte et actualisée automatiquement sur une base fictive, sans erreur de callback ; validation visuelle par l'utilisateur encore possible.

Sauvegarde de la **base météo réelle vide** du Pi copiée au PC, puis restaurée dans un dossier temporaire : intégrité correcte, zéro observation. Cela valide le chemin de sauvegarde, pas une collecte Netatmo réelle.

Aucun token copié ou renouvelé, aucune base active restaurée, aucun timer météo activé et aucune publication GitHub effectuée.

## Saisie applicative — 13/10/2026
Paramètres → Météo du Raspberry → Configurer l’accès Netatmo du Raspberry. Secrets masqués par défaut, enregistrement local uniquement ; aucun transfert ni activation. Exemple vierge : docs/examples/netatmo_raspberry_oauth.local.json.example.
Le contrôle réel distingue les applications PC/Pi et valide le PC (HTTP 200), mais le renouvellement Pi a retourné authorization_required. Aucun accès indépendant validé et aucune collecte activée.

## Activation réelle — 13/10/2026

Cette mise à jour remplace les états de préparation/désactivation décrits plus haut.

- Nouvelle application Netatmo Raspberry distincte, accès personnel et station publique choisis vérifiés. Renouvellement de son autorisation réussi ; accès PC toujours HTTP 200 après contrôle.
- Configuration indépendante transférée par SSH aux fichiers privés Pi, permissions 0600. Le PC conserve son propre accès ; ses consultations ne créent toujours pas d’historique pluie.
- Premier passage manuel : 3 observations personnelles, 6 publiques, 9 importées sur PC. Dates, unités, valeurs et périodes identiques à la source exportée.
- Rejeu du lot : 0 ajout, 9 doublons. Deuxième synchronisation : file vide, 0 ajout.
- Sauvegarde SQLite Pi et copie PC vérifiées ; aucun secret dans cette sauvegarde d’observations.
- Import météo PC activé dans la configuration locale.
- gruterra-weather.timer activé dans systemd utilisateur : chaque heure à :05, avec décalage aléatoire jusqu’à 30 secondes. Service et timer indépendants de Mi Flora.
- AROME-PI et son calendrier de 15 minutes restent séparés et non activés.

À vérifier encore : un passage horaire autonome, PC physiquement éteint, puis récupération au retour ; redémarrage matériel du Pi. Le passage manuel et l’activation du timer ne valident pas à eux seuls ces scénarios.

Le fichier PC netatmo_raspberry_oauth.local.json a servi à la saisie/transmission initiale. Une fois l’accès déployé, le Pi possède le couple rotatif actif : ne pas réimporter une ancienne copie de ses tokens ni les renouveler depuis un autre processus.


### Vérification du passage automatique — 13/10/2026

Le service météo du Raspberry a été déclenché par son timer à 22:06:18 (heure de Paris), avec un résultat réussi. Dix-huit observations issues des passages automatiques ont ensuite été importées sur le PC. La sauvegarde météo du Pi a été copiée et vérifiée sur le PC ; dates, unités et valeurs importées correspondent exactement aux observations exportées.

Le rejeu du lot ajoute zéro observation et reconnaît les 18 doublons. La synchronisation suivante confirme une file vide. Le timer horaire reste actif.

Cette vérification ne constitue pas encore un essai avec le PC physiquement éteint ni un test de redémarrage matériel du Raspberry.


## Lecture des observations sur le PC — amélioration locale du 18/10/2026

La fenêtre des observations importées se met à jour après une synchronisation. Le bouton Actualiser relit uniquement la base météo locale : il ne lance pas une collecte sur le Raspberry ou sur Netatmo.

La date d'actualisation de la fenêtre, la date de récupération et la date du relevé correspondent à des événements différents. Les dates UTC d'origine restent dans les colonnes. Une date inconnue n'est pas remplacée par l'heure de consultation.

Si la lecture échoue, les anciennes lignes restent affichées avec un avertissement. Si aucune observation n'est importée, cela ne signifie pas qu'il n'a pas plu. Une mesure de 0 mm est affichée comme telle ; une valeur absente reste marquée indisponible. Les cumuls ne sont pas additionnés.

Le statut Netatmo distingue également une récupération réussie sans station et une connexion impossible. En cas d'échec, les données conservées ne sont pas rajeunies. Ces changements sont locaux et ne modifient ni les accès, ni la collecte, ni le contrat météo PC/Pi.
