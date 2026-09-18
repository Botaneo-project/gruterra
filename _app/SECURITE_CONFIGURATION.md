# Configuration et socle Raspberry — 10 septembre 2026

## Audit et changements

Les identifiants OAuth étaient déjà séparés dans `C:\Plantes\_config\netatmo_config.json`.
Ce fichier et ses clés restent compatibles. Le renouvellement automatique conserve les nouveaux
access_token et refresh_token par remplacement atomique. La copie `.bak` automatique à chaque
renouvellement est supprimée; les anciennes copies ne sont pas supprimées.

Le module Netatmo contenait la localisation et les stations favorites dans son code et affichait
des réponses HTTP brutes dans les erreurs OAuth/API. Les paramètres privés sont maintenant dans
`_config\botaneo.local.json`, avec les valeurs précédentes conservées lors de l'installation.
Les erreurs réseau et HTTP ne révèlent plus le corps de réponse ni l'URL de requête.
Les chemins sont centralisés dans `botaneo_config.py`. `BOTANEO_CONFIG_DIR` peut désigner un autre
dossier privé complet. Aucun `.env` ni paquet supplémentaire n'est requis.

La recherche dans les scripts Python a identifié `capteurs/netatmo.py` comme utilisateur des tokens.
`interface.py`, `app.py` et `synchronisation_botaneo.py` consomment ce module.
Mi Flora, ses adresses BLE en base, ses délais, ses acquisitions et les scripts de synchronisation
restent inchangés. `database.py` utilise toujours `C:\Plantes\_app\plantes.db`.
La base `C:\Plantes\plantes.db` est distincte et reste intacte. Aucune migration SQL.

Le `.gitignore` à la racine exclut la configuration privée, ses copies, les bases, caches et journaux.
Il ne chiffre pas les fichiers et ne retire pas un fichier déjà suivi dans un éventuel dépôt.
Le script ZIP existant inclut `_config` : les ZIP et les anciennes copies contiennent donc des secrets
et doivent rester privés. Aucun secret existant n'a été révoqué.

## Boîtiers futurs : inactifs

La configuration locale contient `collecteurs: {"enabled": false, "devices": {}}`.
Aucun token réel ni boîtier fictif n'est créé. Aucun port, service, endpoint ou tâche planifiée ajouté.
`botaneo_collecteurs.nouvelle_identite()` fournit, lors d'un futur provisionnement explicite,
un identifiant `BOTANEO-RPI-<UUID>` et un token aléatoire de 32 octets.
Conserver le token brut uniquement sur le Pi, dans un fichier privé; placer dans `devices`, indexé
par device_id, uniquement `token_sha256` et `revoked: false`. Refuser tout identifiant inconnu,
token invalide, boîtier révoqué et toute requête tant que `enabled` vaut false.
`verifier_token` vérifie une fiche connue; ce n'est pas un serveur d'authentification.
Révoquer un seul boîtier avec `revoked: true`; une rotation remplace son empreinte.
Ne pas réutiliser les tokens Netatmo pour les boîtiers. Configurer TLS avant tout futur transport.

## Règles anti-doublons à appliquer au futur récepteur

Créer `measurement_id` (UUID) une seule fois lors de l'acquisition et le conserver avec la mesure
dans une file locale durable. Réutiliser le même ID après redémarrage, timeout ou nouvelle tentative.
Le futur récepteur devra imposer une contrainte UNIQUE `(device_id, measurement_id)` et enregistrer
la clé de réception et la mesure dans une même transaction. Répondre succès seulement après commit.
Un renvoi identique renvoie le même accusé sans nouvelle insertion; le même ID avec un contenu
différent doit être refusé. Supprimer de la file locale uniquement après cet accusé.
Conserver également sensor_id, measured_at en UTC et la version du format.
Ne pas dédupliquer sur les seules valeurs : deux acquisitions peuvent avoir des valeurs identiques.
La déduplication entre plusieurs collecteurs pour un même capteur nécessitera une règle distincte.
Ces règles sont documentées, pas activées : l'insertion actuelle de mesures reste inchangée.

## Journalisation

`botaneo_journal.evenement` accepte seulement trois événements techniques fixes et un statut HTTP
numérique. Netatmo l'utilise pour succès de renouvellement et échecs réseau/HTTP. Aucun message libre,
exception brute, header, token, coordonnées ou réponse serveur n'y est accepté.
Il utilise le logger Python `botaneo.securite`; aucun fichier ni handler global imposé à l'application.
Pour une future conservation sur disque, ajouter un handler avec rotation; ne pas activer le debug HTTP.

## Sauvegarde et retour arrière

Avant installation, un dossier daté dans `C:\Plantes\_security_backups` contient les fichiers remplacés,
la configuration OAuth privée et une sauvegarde SQLite cohérente de chacune des deux bases.
Un manifeste liste les fichiers initialement absents et les empreintes initiales.
Pour revenir en arrière, fermer Botaneo puis restaurer `files\_app\capteurs\netatmo.py`
et l'ancien `.gitignore` s'il existait. Les nouveaux modules peuvent rester inutilisés.
Ne pas restaurer d'anciens tokens après une rotation OAuth. Ne restaurer une base qu'en cas de besoin
distinct : cette intervention ne modifie ni données ni schéma.
Redémarrer Botaneo pour charger la configuration; ne lancer qu'une instance effectuant le refresh OAuth.

## Validation réalisée

Quatre tests hors ligne réussis : rotation OAuth et nouvelle tentative après HTTP 401,
masquage des erreurs réseau/HTTP, conservation du JSON précédent lors d'un échec de remplacement,
identifiants distincts, validation/révocation des tokens et refus des champs libres dans le journal.
Les fichiers installés correspondent aux fichiers vérifiés. Tous les scripts Python de `_app`
passent l'analyse syntaxique. Les secrets OAuth existants sont inchangés.
Les deux bases passent `integrity_check` et leur contenu SQL est identique aux sauvegardes.
Sauvegarde de cette intervention : `C:\Plantes\_security_backups\20260910_221300`.
Le runtime de vérification ne dispose pas de `requests` : le réseau a été simulé dans les tests.
Aucune acquisition physique BLE ni requête Netatmo réelle n'a été lancée. Une acquisition après
redémarrage de Botaneo reste la validation matérielle à effectuer dans son environnement habituel.
