# Installateur Windows 0.1.7-dev

Préversion de test, non signée. L’installateur prépare Python et les dépendances ; Python n’est pas embarqué. Le test sur un PC sans Python reste à réaliser. Un essai avec Python déjà installé a réussi, avec ouverture de la démo.

L’installation se fait pour l’utilisateur courant, dans un dossier distinct par défaut. Fermer Gruterra avant de remplacer un programme utilisé. Les verrous d’application et de mise à jour empêchent les remplacements concurrents. Les données personnelles sont préservées lors de la désinstallation ; des fichiers générés peuvent rester.

Pour construire : utiliser `prepare_windows_installer.py --compiler <chemin vers ISCC.exe>` avec un compilateur Inno Setup officiel vérifié. La sélection publique et les valeurs sensibles sont contrôlées avant compilation. `--smoke` réserve les raccourcis au dossier temporaire et ne crée pas d’entrée de désinstallation ; ce mode n’est pas destiné aux utilisateurs.

Voir [l’essai sur PC vierge](TEST_INSTALLATION_PC_VIERGE.md) et [la récupération après mise à jour](RECUPERATION_MISE_A_JOUR.md).
