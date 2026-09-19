# Botaneo

Pour découvrir le projet sans matériel : [guide du mode démonstration](GUIDE_DEMO.md).

Botaneo est une application locale de suivi des plantes. Elle centralise les plantes, les capteurs Mi Flora, les mesures enregistrées dans SQLite, les arrosages, les rappels et les données météo Netatmo.

Le projet est prévu d’abord pour un usage local sous Windows. Les données réelles, les tokens et la base SQLite personnelle restent sur le PC de l’utilisateur.

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
- Sauvegarde locale du projet vers un ou plusieurs disques.

## Installation

Botaneo nécessite Python 3.14 ou une version compatible.

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
Botaneo/
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
    ├── services/
    ├── ui/
    └── assets/
```

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

Botaneo peut afficher :

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

## Maintenance

- Sauvegarder la base avant toute migration.
- Ne pas exposer les tokens Netatmo, Météo-France ou e-mail.
- Garder les fichiers `.example.json` anonymes.
- Tester la lecture Bluetooth après toute modification Mi Flora.
- Garder Netatmo indépendant de Mi Flora : une erreur météo ne doit pas bloquer le capteur.

## Licence

Aucune licence n’est encore définie. Avant une publication publique, choisir une licence adaptée au niveau de partage souhaité.


## Suivi Raspberry sur Windows 11

Une carte « Raspberry Pi · Suivi quotidien » contrôle la disponibilité du Pi par SSH. Les réglages permettent de choisir une heure quotidienne, un délai de nouvel essai, une tolérance et le mode déplacement. Le contrôle est rattrapé à l’ouverture de Botaneo si une échéance a été manquée. Il fonctionne uniquement lorsque l’application est ouverte. Aucun service Windows ni e-mail automatique n’est installé.

La configuration privée est dans `_config/raspberry.local.json` ; l’état et les incidents, bornés à 200, sont dans `_app/data/raspberry_suivi.sqlite3`. La clé privée reste dans le dossier SSH Windows et son contenu n’est jamais lu par l’application. Le contrôle utilise SSH sans mot de passe interactif, vérifie l’identité de l’hôte et n’exécute que `hostname`.

**Un contact réussi n’est pas une synchronisation de mesures.** La collecte Raspberry et le transfert vers la base PC restent à développer. La carte l’indique explicitement. L’absence de réponse ne permet pas de distinguer une panne Wi-Fi d’une coupure électrique. En déplacement sans accès distant, suspendre le suivi automatique. Les délais suivent l’heure locale du PC.


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
