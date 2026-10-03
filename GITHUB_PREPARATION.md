# Préparation GitHub Gruterra

Ce fichier sert de checklist avant de créer ou publier le dépôt GitHub.

## À publier

- `README.md`
- `TODO.md`
- `.gitignore`
- `requirements.txt`
- `backup_botaneo.py`
- `botaneo.local.example.json`
- `netatmo_config.example.json`
- `_app/interface.py`
- `_app/app.py`
- `_app/database.py`
- `_app/mini_base_plantes.py`
- `_app/previsions_meteo.py`
- `_app/meteo_cache.py`
- `_app/capteur_infos.py`
- `_app/sync_miflora.py`
- `_app/synchronisation_botaneo.py`
- `_app/botaneo_config.py`
- `_app/botaneo_collecteurs.py`
- `_app/botaneo_journal.py`
- `_app/vue_historique.py`
- `_app/instance_botaneo.py`
- `_app/ajout_capteur.py`
- `_app/capteurs/`
- `_app/services/`
- `_app/ui/`
- `_app/assets/`

## À ne pas publier

- `_config/` : contient les configurations locales et tokens.
- `_security_backups/` : sauvegardes de travail.
- `_historique/` : anciens essais conservés localement.
- `_app/data/` : caches Netatmo, prévisions, données capteurs locales.
- Toutes les bases SQLite réelles : `*.db`, `*.db-wal`, `*.db-shm`.
- Tous les fichiers `.bak`, `.backup`, `.pyc`, `.tmp`, `.lock`.
- Les tests, diagnostics, migrations et scripts ponctuels locaux.
- Les archives ZIP de sauvegarde.

## Points à vérifier avant publication

- Aucun token Netatmo ou Météo-France dans les fichiers suivis.
- Aucun mot de passe ou adresse personnelle dans les fichiers suivis.
- Les fichiers d’exemple de configuration ne contiennent que des valeurs fictives.
- L’application se lance encore depuis `_app/interface.py`.
- Le README explique clairement que la base réelle et les secrets restent locaux.

## Nettoyage local possible plus tard

À faire seulement quand l’application est stable :

- déplacer les anciens fichiers `.bak` encore présents dans `_app` vers `_historique/` ou `_security_backups/` ;
- supprimer les dossiers `__pycache__` ;
- conserver une seule base réelle active : `_app/plantes.db` ;
- garder les anciennes bases seulement dans les sauvegardes locales E: et J:.

## Liste actuelle simulée des fichiers publiables

Après exclusions, le projet contient environ 42 fichiers publiables. Cette liste est beaucoup plus saine que l’état brut du dossier, qui contient aussi des sauvegardes, caches, tests locaux et bases réelles.

Avant de créer le dépôt GitHub, refaire une dernière vérification pour s’assurer qu’aucun fichier sensible n’est visible.

## Vérification sécurité du 14/09/2026

Contrôle effectué avant préparation GitHub :

- 42 fichiers considérés comme publiables dans la simulation.
- 40 fichiers texte analysés.
- Aucun token Netatmo réel trouvé dans les fichiers publiables.
- Aucune coordonnée personnelle exacte trouvée dans les fichiers publiables.
- L’adresse Bluetooth réelle du capteur Mi Flora a été retirée des fichiers publiables.
- `_app/scanner_ble.py` utilise maintenant une adresse d’exemple et peut recevoir l’adresse réelle via une variable locale non publiée.
- `_app/synchronisation_botaneo.py` ne contient plus l’ancienne adresse de test réelle.
- Les bases de données, configurations locales, sauvegardes, journaux, caches et fichiers `.bak` restent exclus par `.gitignore`.

Conclusion : la préparation GitHub peut servir de copie propre du code, pendant que le travail continue normalement dans `C:\Plantes`.


## Favoris Netatmo publics

Les favoris Netatmo publics peuvent être ajoutés localement soit avec un identifiant de station, soit en collant un lien `https://weathermap.netatmo.com/?stationid=...`. Gruterra extrait uniquement l’identifiant utile et l’enregistre dans `_config/botaneo.local.json`, qui reste ignoré par GitHub.
