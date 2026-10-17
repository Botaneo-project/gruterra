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

## 2. Préparer Python

Commencez par `Installer_Gruterra.bat` : si Python manque, il tente d’installer Python 3.12.10 puis enchaîne sur les dépendances. Une installation manuelle est seulement un recours si cette étape est bloquée. Dans ce cas, utilisez :

```text
https://www.python.org/downloads/windows/
```

Version utilisée par l’installation automatique : Python 3.12.10. Pendant l’installation, garder le lanceur `py` activé si possible et cocher l’ajout de Python au PATH quand l’installateur le propose. Tkinter doit être disponible, car l’interface graphique l’utilise.

## 3. Installer les dépendances

Méthode simple, sans PowerShell : double-cliquer sur le fichier situé à la racine du dossier Gruterra :

```text
Installer_Gruterra.bat
```

Ce script détecte `py` ou `python`, crée l'environnement local `.venv`, vérifie `pip` sans le mettre à jour systématiquement, installe les dépendances de `requirements.txt`, puis vérifie les imports essentiels : `tkinter`, `requests`, `bleak` le support Ed25519 de `cryptography` et le fuseau `Europe/Paris` fourni par `tzdata`.

La fenêtre affiche des étapes lisibles (`[1/6]` à `[6/6]`) et reste ouverte en cas d'erreur pour permettre de copier le message. L'installation n'est considérée comme réussie qu'après cette vérification finale.

Méthode manuelle si besoin : ouvrir PowerShell dans le dossier décompressé, puis lancer :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si Python est introuvable, le BAT tente d’installer automatiquement Python depuis python.org. Si le téléchargement ou l’installation est bloqué, il affiche un message clair au lieu de laisser une erreur terminal incompréhensible. Tkinter doit être disponible avec l'installation Python.

## 4. Tester sans matériel

Après une installation réussie, double-cliquez sur `Lancer_Demo.bat`. Le premier test conseillé est le mode démo. Il ne demande ni capteur, ni Raspberry Pi, ni compte Netatmo :

```powershell
.\.venv\Scripts\python.exe Lancer_Demo.py
```

Le mode démo n’utilise ni Mi Flora, ni Raspberry Pi, ni compte Netatmo.

## 5. Lancer l’application principale

Quand vous voulez utiliser votre propre base locale, double-cliquez sur `Lancer_Gruterra.bat`. Équivalent en PowerShell :

```powershell
.\.venv\Scripts\python.exe Lancer_Gruterra.py
```

Gruterra créera ou utilisera ses fichiers locaux selon la configuration disponible.

## 6. Mise à jour

Si une release officielle contient une archive et un SHA256 valide, Gruterra peut proposer la mise à jour au démarrage ou depuis `Paramètres`. `À propos` renvoie vers les paramètres pour l’installation.

Le système de mise à jour :

- télécharge l’archive officielle ;
- vérifie le SHA256 ;
- sauvegarde les fichiers actuels ;
- remplace les fichiers du programme ;
- préserve les données personnelles ;
- le code actuel ferme Gruterra et attend la fin de l’ancienne instance avant de relancer le même mode ; ce redémarrage automatique reste à confirmer sur le PC de secours après la prochaine release.

Si Gruterra est à jour, aucun remplacement n’est proposé. Le passage 0.1.5-dev → 0.1.6-dev a été testé ; les corrections ultérieures sur main ne font pas encore partie de cette archive.

Les données locales à préserver ne doivent pas être envoyées sur GitHub :

- `plantes.db` ;
- `_config/` ;
- `_security_backups/` ;
- `_historique/` ;
- `_app/data/` ;
- `discord_bot/.env`.

## 7. Sauvegarder ses données

Gruterra distingue deux types de sauvegardes :

- **Exporter mes données** : archive destinée au partage, au diagnostic ou à l’analyse, sans configuration privée volontaire.
- **Sauvegarde complète privée** : archive locale de récupération après formatage ou changement de PC. Elle peut contenir la base réelle, les historiques, les paramètres, `_config/`, les tokens et d’autres secrets nécessaires à la restauration.

Une sauvegarde complète privée ne doit jamais être publiée sur GitHub, Reddit, Discord ou envoyée à quelqu’un sans vérification. Elle est destinée uniquement à l’utilisateur. Le dossier local prévu pour ces archives est `_user_backups/`, ignoré par Git.

Les boutons `Exporter mes données` et `Sauvegarde complète privée` sont disponibles depuis `Base & synthèses`. La restauration complète automatique n’est pas encore exposée dans l’interface. Quand elle sera ajoutée, Gruterra devra d’abord créer une sauvegarde de l’état existant pour permettre un retour arrière.

## 8. Configuration optionnelle

Les fichiers d’exemple peuvent être copiés puis adaptés localement :

- `botaneo.local.example.json` ;
- `netatmo_config.example.json` ;
- `email.local.example.json` ;
- `discord_bot/.env.example`.

Ne publiez jamais vos tokens, mots de passe, refresh tokens ou fichiers de configuration privée.

## 9. En cas de problème

Pour demander de l’aide, indiquez :

- votre système : Windows, Raspberry Pi ou autre ;
- la version de Gruterra ;
- la commande lancée ;
- le message d’erreur exact ;
- si vous utilisez le mode démo, Mi Flora, Raspberry Pi ou Netatmo.

Évitez de partager des captures contenant des secrets ou des données privées.