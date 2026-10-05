# Installer Gruterra depuis une release ZIP

Ce guide s’adresse aux personnes qui téléchargent Gruterra depuis une release GitHub, sans utiliser Git.

## 1. Télécharger

1. Ouvrir la page GitHub du projet.
2. Aller dans `Releases`.
3. Télécharger l’archive `gruterra-<version>.zip`.
4. Décompresser l’archive dans un dossier simple, par exemple :

```text
C:\Gruterra
```

Éviter de lancer Gruterra directement depuis le ZIP non décompressé.

## 2. Installer Python

Installer Python pour Windows depuis :

```text
https://www.python.org/downloads/windows/
```

Pendant l’installation, garder le lanceur `py` activé. Tkinter doit être disponible, car l’interface graphique l’utilise.

## 3. Installer les dépendances

Méthode simple, sans PowerShell : double-cliquer sur le fichier situé à la racine du dossier Gruterra :

```text
Installer_Gruterra.bat
```

Ce script crée l'environnement local `.venv` et installe les dépendances de `requirements.txt`.

Méthode manuelle si besoin : ouvrir PowerShell dans le dossier décompressé, puis lancer :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si Python est introuvable, installez Python depuis le site officiel et gardez le lanceur `py` activé. Tkinter doit être disponible avec l'installation Python.

## 4. Tester sans matériel

Pour découvrir Gruterra sans capteur, lancer le mode démo :

```powershell
.\.venv\Scripts\python.exe Lancer_Demo.py
```

Le mode démo n’utilise ni Mi Flora, ni Raspberry Pi, ni compte Netatmo.

## 5. Lancer l’application principale

Quand vous voulez utiliser votre propre base locale :

```powershell
.\.venv\Scripts\python.exe Lancer_Gruterra.py
```

Gruterra créera ou utilisera ses fichiers locaux selon la configuration disponible.

## 6. Mise à jour

Si une release officielle contient une archive et un SHA256 valide, Gruterra peut proposer la mise à jour au démarrage ou depuis `À propos`.

Le système de mise à jour :

- télécharge l’archive officielle ;
- vérifie le SHA256 ;
- sauvegarde les fichiers actuels ;
- remplace les fichiers du programme ;
- préserve les données personnelles ;
- demande de relancer Gruterra après application.

Les données locales à préserver ne doivent pas être envoyées sur GitHub :

- `plantes.db` ;
- `_config/` ;
- `_security_backups/` ;
- `_historique/` ;
- `_app/data/` ;
- `discord_bot/.env`.

## 7. Configuration optionnelle

Les fichiers d’exemple peuvent être copiés puis adaptés localement :

- `botaneo.local.example.json` ;
- `netatmo_config.example.json` ;
- `email.local.example.json` ;
- `discord_bot/.env.example`.

Ne publiez jamais vos tokens, mots de passe, refresh tokens ou fichiers de configuration privée.

## 8. En cas de problème

Pour demander de l’aide, indiquez :

- votre système : Windows, Raspberry Pi ou autre ;
- la version de Gruterra ;
- la commande lancée ;
- le message d’erreur exact ;
- si vous utilisez le mode démo, Mi Flora, Raspberry Pi ou Netatmo.

Évitez de partager des captures contenant des secrets ou des données privées.