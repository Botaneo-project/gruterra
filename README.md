# Gruterra

> Nom officiel du projet : **Gruterra**. Certains fichiers, variables d’environnement, services Raspberry et chemins conservent encore le nom technique historique `botaneo` pour préserver la compatibilité avec les installations existantes.

Pour découvrir le projet sans matériel : [guide du mode démonstration](GUIDE_DEMO.md).

Gruterra est une application locale de suivi des plantes. Elle centralise les plantes, les capteurs Mi Flora, les mesures enregistrées dans SQLite, les arrosages, les rappels et les données météo Netatmo.

Le projet est prévu d’abord pour un usage local sous Windows. Les données réelles, les tokens et la base SQLite personnelle restent sur le PC de l’utilisateur.


## Audit local avant envoi GitHub

Une commande permet de lancer les contrôles principaux sans capteur :

```powershell
cd C:\Plantes
py audit_botaneo.py
```

Elle exécute les tests automatisés, la vérification avant GitHub, un contrôle du diff Git et affiche les fichiers encore modifiés à relire avant commit. La couverture détaillée est décrite dans [tests/README.md](tests/README.md).

## Fonctionnalités principales

- Interface graphique Tkinter.
- Interface console.
- Suivi de plantes avec ou sans capteur actif.
- Association d’un capteur Mi Flora à une plante.
- Lecture Bluetooth Mi Flora avec plusieurs tentatives de scan.
- Enregistrement des mesures dans SQLite.
- Historique des mesures avec vue graphique.
- Mini base de plantes avec autocomplétion.
- Besoins de base par plante : lumière, arrosage, sol, température.
- Arrosage manuel et rappel programmable.
- Centre d’alertes local : batterie, rappels, données anciennes, météo proche.
- Intégration Netatmo privée et publique.
- Synthèse météo locale à partir des meilleures données disponibles.
- Prévision locale à environ +2 h.
- Mode sombre et options d’affichage.
- Fenêtre `À propos` avec version locale, chemins utiles, état Raspberry et rappel sécurité.
- Sauvegarde locale du projet vers un ou plusieurs disques.

## Installation

Gruterra nécessite Python 3.14 ou une version compatible.

Installer les dépendances :

```powershell
py -m pip install -r requirements.txt
```

Si le lanceur `py` n’est pas disponible, utiliser l’exécutable Python installé sur le PC.

Tkinter et SQLite sont fournis avec une installation Python Windows standard.

## Lancement

Interface graphique :

```powershell
cd C:\Plantes\_app
py interface.py
```

Interface console :

```powershell
cd C:\Plantes\_app
py app.py
```

Pour un raccourci Windows, utiliser `pythonw.exe` avec `_app\interface.py` comme cible et `_app` comme dossier de démarrage.

## Mode démo

Le mode démo permet de tester l’interface sans capteur Mi Flora, sans compte Netatmo et sans base personnelle. Il crée une base SQLite fictive dans `_app/data/demo/plantes_demo.db`, avec quelques plantes, mesures, arrosages et observations d’exemple.

```powershell
cd C:\Plantes\_app
py lancer_demo.py
```

La base démo est recréable avec :

```powershell
cd C:\Plantes\_app
py creer_base_demo.py
```

Cette base reste locale et n’est pas publiée dans Git. Les données sont volontairement fictives.

## Structure principale

```text
Gruterra/
├── README.md
├── TODO.md
├── requirements.txt
├── backup_botaneo.py
├── botaneo.local.example.json
├── netatmo_config.example.json
└── _app/
    ├── interface.py
    ├── app.py
    ├── database.py
    ├── creer_base_demo.py
    ├── lancer_demo.py
    ├── mini_base_plantes.py
    ├── previsions_meteo.py
    ├── meteo_cache.py
    ├── sync_miflora.py
    ├── vue_historique.py
    ├── capteurs/
    ├── services/              # logique testable extraite de l'interface
    ├── ui/
    └── assets/
```

## Vérification avant envoi GitHub

Avant de faire un commit ou un push, lancer :

```powershell
cd C:\Plantes
py verifier_avant_github.py
```

Le script affiche les fichiers qui vont partir, bloque si un fichier sensible est suivi ou non ignoré, cherche des mots-clés de secrets dans les fichiers versionnés et vérifie que les fichiers Python compilent.


### Alertes e-mail SMTP local

Gruterra prépare une future option d’alertes e-mail via SMTP sécurisé local. Les paramètres réels doivent rester dans `_config/email.local.json`, ignoré par Git. Le dépôt contient seulement `email.local.example.json`, avec des valeurs fictives. Par défaut, le mode prévu est `preview` : Gruterra prépare le message sans l’envoyer. L’envoi réel ne devra être activé qu’après validation du destinataire, des plantes concernées et des règles d’alerte.

## Configuration locale

Les fichiers privés ne doivent pas être publiés.

Créer localement un dossier `_config` à côté de `_app`, puis y placer les fichiers nécessaires.

Exemple Netatmo privé :

```text
_config/netatmo_config.json
```

Un modèle publiable est fourni :

```text
netatmo_config.example.json
```

Exemple de configuration locale générale :

```text
_config/botaneo.local.json
```

Un modèle publiable est fourni :

```text
botaneo.local.example.json
```

## Base de données

La base active est locale :

```text
_app/plantes.db
```

Elle contient les plantes, capteurs, mesures, arrosages, rappels et besoins de base. Cette base réelle ne doit pas être publiée sur GitHub.

Si une base d’exemple est nécessaire plus tard, elle devra être générée séparément, sans données personnelles, sans tokens et sans historique réel.

## Mi Flora

Le module principal est :

```text
_app/capteurs/miflora.py
```

Comportement actuel :

- recherche du capteur par adresse Bluetooth ;
- plusieurs tentatives de scan pour réveiller le capteur ;
- lecture batterie et firmware quand disponibles ;
- demande de mesure via la caractéristique Mi Flora ;
- lecture température, humidité du sol, luminosité et conductivité.

Il faut éviter de modifier cette partie sans test réel avec le capteur.

## Netatmo et météo

Le module Netatmo est :

```text
_app/capteurs/netatmo.py
```

Les tokens Netatmo doivent rester dans `_config/netatmo_config.json`.

Gruterra peut afficher :

- les équipements Netatmo privés ;
- les stations publiques proches ;
- les stations favorites ;
- pluie, vent, rafales, température, humidité, pression ;
- une synthèse locale choisissant la meilleure source disponible ;
- une prévision locale à environ +2 h.

## Sauvegardes

Le script :

```text
backup_botaneo.py
```

crée une archive ZIP du projet local sur les disques configurés dans le script. Les sauvegardes restent locales et ne doivent pas être publiées.

## Fichiers exclus de GitHub

Le fichier `.gitignore` exclut notamment :

- `_config/` ;
- `_security_backups/` ;
- `_historique/` ;
- `_app/data/` ;
- les bases SQLite réelles ;
- les caches Python ;
- les fichiers `.bak`, `.tmp`, `.lock` ;
- les archives ZIP ;
- les scripts locaux de diagnostic, migration et test ponctuel.

## Mise à jour future

Gruterra prépare un futur système de mise à jour, mais aucun auto-upgrade réel n’est lancé pour l’instant.

Le module `_app/botaneo_update.py` prépare seulement les garde-fous :

- protéger la base `plantes.db` ;
- préserver `_config/`, `_security_backups/`, `_historique/` et `_app/data/` ;
- distinguer le programme remplaçable des données utilisateur ;
- bloquer le diagnostic si la séparation programme / données est absente ou incomplète ;
- éviter d’afficher les noms détaillés des fichiers secrets.

La fenêtre `À propos` affiche l’état de cette préparation et permet de copier un diagnostic JSON. Ce diagnostic reste informatif : il regroupe l’état global, les blocages, les données détectées et les prochaines actions, sans écrire de fichier automatiquement et sans autoriser une mise à jour.

La comparaison de version est préparée avec un manifeste local. Le format public est documenté dans `version_manifest.example.json` avec version, notes et URL informative ; le vrai `version_manifest.json` est ignoré par Git. Aucune vérification GitHub réelle, aucun téléchargement et aucune application automatique ne sont encore actifs.

Toute future mise à jour devra rester précédée d’une sauvegarde locale et d’une validation explicite.

## Analyse des cycles d’arrosage

Gruterra analyse les cycles d’arrosage sans conclure pour toute la motte : le Mi Flora mesure seulement sa zone. L’analyse compare l’humidité avant arrosage, le pic, la fin de cycle, la hausse après arrosage, l’écart final par rapport au départ, la baisse après pic, la vitesse observée et la qualité des mesures disponibles.

## Maintenance

- Sauvegarder la base avant toute migration.
- Ne pas exposer les tokens Netatmo, Météo-France ou e-mail.
- Garder les fichiers `.example.json` anonymes.
- Tester la lecture Bluetooth après toute modification Mi Flora.
- Garder Netatmo indépendant de Mi Flora : une erreur météo ne doit pas bloquer le capteur.

## Licence

Aucune licence n’est encore définie. Avant une publication publique, choisir une licence adaptée au niveau de partage souhaité.


## Raspberry Pi : collecte et synchronisation

Le Raspberry demande une collecte Mi Flora quatre fois par jour, à 06 h, 12 h, 18 h et 23 h, et conserve les mesures localement. Son interface mobile permet de demander une lecture immédiate. Le PC reste actuellement le centre de consultation ; le remplacement du PC par un serveur Raspberry et les collecteurs ESP32 sont des évolutions futures.

Gruterra récupère les mesures à chaque ouverture, puis toutes les quinze minutes par défaut tant que l’application est ouverte. Cet intervalle est réglable et ne déclenche pas une nouvelle lecture Bluetooth. Le mode déplacement suspend les transferts. Aucun service Windows permanent n’est nécessaire.

La réception est confirmée après enregistrement dans la base PC. Les reprises évitent les doublons ; les données sans date fiable restent archivées. Pour une synchronisation manuelle, le PC récupère d’abord les données Raspberry puis peut tenter une lecture Bluetooth locale de secours. Les collectes régulières restent confiées au Raspberry.

La lecture historique Mi Flora côté PC fonctionne sans effacement. Elle peut lire en plusieurs passes pour contourner les coupures BLE de Windows, accepte les lectures partielles valides, et signale clairement les entrées que le capteur annonce mais qui n’ont pas encore été récupérées.

Après une récupération réussie, le PC copie la dernière sauvegarde quotidienne disponible du Pi et vérifie sa taille, son empreinte et son intégrité SQLite. Un échec de copie est signalé sans annuler les mesures reçues ; la prochaine synchronisation réessaie. Les copies restent dans `_security_backups/raspberry_daily/`, sans remplacer la base active.

La configuration privée est dans `_config/raspberry.local.json`. La clé SSH reste sur le PC ; l’identité du Raspberry est vérifiée. Le suivi est conservé dans `_app/data/raspberry_sync_suivi.sqlite3`. La connexion locale doit être disponible ; aucun port Internet n’est requis pour ce fonctionnement.

Les scripts Raspberry sont dans `raspberry/`. Une base d’installation et de mise à jour est disponible dans `raspberry/install/`, sans secrets ni configuration privée. Voir [la fiche Raspberry](RASPBERRY.md) pour les limites et les vérifications. Relancer Gruterra après une mise à jour pour charger les nouveaux modules.


## Dépôt GitHub

Le dépôt public/privé attendu pour Gruterra est `https://github.com/Botaneo-project/gruterra`. L’ancien dépôt `Botaneo-project/botaneo` peut continuer à rediriger côté GitHub après renommage, mais les liens de documentation et les scripts d’installation pointent désormais vers `gruterra`.

## Compatibilité technique avec l’ancien nom Botaneo

Le nom officiel du projet est désormais **Gruterra**. Pour éviter de casser les installations existantes, certains éléments techniques conservent temporairement le nom historique `botaneo` : noms de fichiers Python, variables d’environnement `BOTANEO_*`, fichier local `_config/botaneo.local.json`, scripts d’audit, services Raspberry `botaneo-*` et chemin Raspberry `~/botaneo`. Ces noms sont gardés volontairement pour la compatibilité et pourront être migrés plus tard avec une procédure dédiée.
