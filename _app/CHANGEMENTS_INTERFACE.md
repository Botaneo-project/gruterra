# Affichage — 10 septembre 2026

- Mode sombre par défaut en l'absence de préférence. Le bouton clair/sombre mémorise
  le choix dans `_config/interface.local.json`, indépendamment des tokens et paramètres météo.
  Le fichier est exclu de Git par les règles existantes. Un problème de lecture utilise le mode sombre;
  un échec d'enregistrement est indiqué dans la barre d'état sans arrêter l'interface.
- Le bouton Historique utilise la palette active, y compris lorsqu'il est pressé.
- La progression ne revient plus à 90 % après la fin : les deux mises à jour Mi Flora
  s'exécutent avant le passage final à 100 %, au lieu d'être différées après celui-ci.
  100 % signifie que le traitement est terminé; le message détaille le résultat Mi Flora.
- Les libellés privée/publiques et les acquisitions restent inchangés.

Les fichiers précédents sont sauvegardés dans `_security_backups/ui_<date>` avant installation.
Redémarrer Botaneo après la fin d'une synchronisation pour charger ces modifications.
Pour revenir en arrière, fermer Botaneo et restaurer interface.py depuis cette sauvegarde.
Aucune modification des bases ou des secrets.
