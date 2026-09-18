# Plusieurs capteurs, météo et navigation — 10 septembre 2026

## Utilisation

Fermer toutes les anciennes fenêtres et consoles Botaneo, puis relancer l'interface.
Le nouveau verrou est partagé par `interface.py`, `app.py` et `synchronisation_botaneo.py`.
Un deuxième lancement affiche un message et s'arrête. Le système libère le verrou à la fin
du processus, même après un arrêt brutal. Le fichier `.lock` peut rester présent : ne pas le supprimer.
Les anciens processus déjà ouverts et les scripts de diagnostic autonomes ne prennent pas ce verrou.
Ne pas lancer ces diagnostics en parallèle d'une acquisition.

Le bouton Synchroniser parcourt tous les capteurs actifs dans l'ordre de leur identifiant,
avec deux secondes entre capteurs. Une erreur n'empêche pas de passer au suivant.
Le panneau affiche le capteur en cours puis un résultat par capteur et un total.
Les fonctions existantes de synchronisation d'un seul capteur restent disponibles.

« Ajouter un capteur » ouvre un formulaire : nom, adresse Bluetooth et plante existante sans
capteur actif. Il ne lance pas de scan BLE. Les doublons actifs, adresses mal formées, noms vides
et associations déjà occupées sont refusés. La base est sauvegardée de façon cohérente avant
chaque insertion dans `_security_backups/ajouts_capteurs`. La première acquisition est déclenchée
ensuite par Synchroniser. Aucun capteur fictif n'est ajouté pendant l'installation.
Pour créer une plante ou déplacer un capteur existant, les fonctions console restent nécessaires.

La météo indique pour Privée et Publiques la date de leur propre dernière lecture réussie.
Un échec conserve les valeurs et la date précédentes et les marque « en cache ».
Une lecture réussie vide remplace bien les anciennes stations. Les lectures privée/publiques
restent indépendantes, y compris lors d'un échec de la station privée sans cache préalable.
La date correspond à la récupération par Botaneo, pas à l'instant de mesure de chaque module.
Au redémarrage les valeurs restaurées sont marquées en cache jusqu'à une nouvelle lecture.
Les anciens caches avec une seule date globale affichent « date inconnue » pour éviter d'attribuer
une fraîcheur inexacte à l'une des sources. Une prochaine lecture crée les deux dates distinctes.

La molette descend et remonte les cartes lorsque le pointeur se trouve dans la zone principale,
y compris au-dessus des boutons et des libellés. Les fenêtres Historique et Détails conservent
leur propre défilement. Les petits mouvements successifs de molette sont accumulés.

## Vérification et retour arrière

Sauvegarde des fichiers remplacés et de la base active avant installation dans
`C:\Plantes\_security_backups\suite_<date>`. Aucun changement de schéma.
Tests hors ligne : exclusion entre processus et reprise après arrêt, lecture séquentielle de
plusieurs capteurs avec poursuite après échec, météo partielle et redémarrage, ajout sur une copie
de la base avec rejet des doublons et vérification de la sauvegarde, molette et exclusion des fenêtres secondaires.
La validation physique Bluetooth et du rendu est à effectuer au prochain lancement habituel.
Pour revenir en arrière, fermer Botaneo puis restaurer les fichiers depuis la sauvegarde.
Ne pas restaurer la base si de nouvelles mesures ou de nouveaux capteurs ont été ajoutés depuis.
