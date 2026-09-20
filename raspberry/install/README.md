# Installation Raspberry Botaneo

Ces scripts installent ou mettent à jour la partie Raspberry de Botaneo depuis GitHub.

## Installation

Méthode conseillée : télécharger, relire, puis lancer.

```bash
curl -O https://raw.githubusercontent.com/Botaneo-project/botaneo/main/raspberry/install/install_raspberry.sh
less install_raspberry.sh
bash install_raspberry.sh
```

Le script installe les fichiers dans `~/botaneo/collector/`, crée les dossiers `config/` et `data/`, installe les timers systemd utilisateur, puis active :

- `botaneo-collect.timer` : demande une collecte Mi Flora à 06 h, 12 h, 18 h et 23 h.
- `botaneo-backup.timer` : sauvegarde quotidienne de la base collecteur.

## Configuration locale

Le script ne crée pas de vraie configuration privée dans Git. Si `~/botaneo/config/collector.json` n’existe pas, il crée seulement :

```text
~/botaneo/config/collector.json.example
```

Copiez ce fichier en `collector.json`, puis renseignez les capteurs. Ne publiez jamais ce fichier s’il contient des informations privées.

## Mise à jour

```bash
curl -O https://raw.githubusercontent.com/Botaneo-project/botaneo/main/raspberry/install/update_raspberry.sh
less update_raspberry.sh
bash update_raspberry.sh
```

## Vérifications

```bash
systemctl --user list-timers 'botaneo-*'
systemctl --user status botaneo-collect.timer
systemctl --user status botaneo-backup.timer
```

## Notes

Les scripts n’installent pas encore un système complet depuis zéro. Ils supposent que Python, systemd utilisateur et la base du collecteur Botaneo existent ou peuvent être créés. L’objectif est de rendre la partie Raspberry reproductible sans inclure de secrets.
