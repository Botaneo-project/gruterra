# Suivi des capteurs et points de fiabilité — 10 septembre 2026

## Ajouts

La carte de chaque plante affiche près du capteur sa dernière batterie connue et son firmware.
Le bouton « Détails du capteur » présente le nom Bluetooth, les dates de lecture séparées,
les services Bluetooth observés et les 50 derniers changements de version observés.
Les données apparaissent après une synchronisation, sans connexion Bluetooth supplémentaire.
La première version observée établit la référence; une version différente ajoute une entrée.
Les horodatages sont ceux de l'observation, pas ceux de l'installation du firmware.

Le lecteur Mi Flora utilisait déjà la caractéristique batterie/firmware. Les octets sont réutilisés;
la commande de mesure, les tentatives Bluetooth et les cinq valeurs retournées restent identiques.
Les fonctions console, les services et l'interface utilisant ce lecteur bénéficient du même cache.
Le nom et les services proviennent de la connexion existante, sans nouvelle requête de diagnostic.
Les tests historiques consultaient aussi l'horloge interne, le compteur et les données historiques :
ces opérations distinctes ne sont pas ajoutées à l'acquisition courante.
Les quatre mesures et la trame brute continuent d'être enregistrées comme auparavant.

Le cache `C:\Plantes\_app\data\capteurs` est séparé de `plantes.db`, exclu de Git,
écrit par remplacement atomique et indexé par adresse normalisée (nom de fichier SHA-256).
Une donnée absente/invalide n'efface pas une précédente valeur valide. Une lecture incomplète
est signalée et les dates propres à la batterie et au firmware restent accessibles.
Un échec de cache n'empêche pas l'acquisition des mesures. Aucune valeur réelle n'est inventée.

## Fiabilité corrigée

- Écriture atomique du cache météo pour éviter un fichier partiellement écrit après interruption.
- Cache météo JSON invalide ou de type incompatible ignoré au démarrage.
- Le bilan de synchronisation indique les sources en échec au lieu d'afficher seulement une coche
  de succès. 100 % signifie toujours que le traitement est terminé, même en cas d'erreur.

## Points restant à préparer

- L'interface synchronise actuellement le premier capteur actif. Prévoir sélection ou traitement
  séquentiel de tous les capteurs avant de multiplier les équipements.
- Les boutons empêchent les synchronisations concurrentes dans une fenêtre, mais deux processus
  Botaneo peuvent encore entrer en concurrence sur le Bluetooth, OAuth et les caches.
  Prévoir un verrou interprocessus avant de lancer plusieurs services ou collecteurs.
- Les sauvegardes ZIP et anciennes copies contiennent la configuration privée. La séparation
  des fichiers ne constitue pas un chiffrement; garder ces archives privées.
- Le cache météo possède encore une date globale : séparer à terme la fraîcheur privée/publique
  pour mieux distinguer des résultats partiels et des valeurs en cache.

## Futurs travaux sur les firmwares

Conserver d'abord le modèle exact et la version observée. Lors d'une recherche demandée,
comparer les notes du fabricant, les tags/commits des dépôts pertinents et leurs problèmes connus.
Distinguer le firmware du capteur des bibliothèques et intégrations qui lisent ses données.
Une version déclarée identique ne prouve pas que le contenu du firmware n'a pas changé.
Une version nouvelle ne prouve ni une vulnérabilité ni une mise à jour sûre.
Aucun dépôt n'a été audité ici, aucune veille planifiée et aucun flash automatique ajouté.

## Sauvegarde et validation

Les fichiers remplacés sont sauvegardés avant installation dans `_security_backups/capteurs_<date>`.
Aucune migration ni écriture de base n'est effectuée par l'installation.
Les tests utilisent un client Bluetooth simulé : même nombre de lectures et même commande,
compatibilité du tuple de mesure, batterie 0 %, version modifiée, lecture manquante,
cache endommagé et échec d'écriture sans perte de mesure.
Redémarrer Botaneo puis synchroniser pour obtenir les informations matérielles réelles.
