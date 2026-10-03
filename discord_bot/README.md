# Gruterra Discord Bot

Bot optionnel pour préparer un serveur Discord Gruterra.

Il crée une structure simple : annonces, discussion générale, aide installation, capteurs, retours, bugs et idées.

Aucun token réel ne doit être envoyé sur GitHub.

## Préparation Discord

1. Aller sur le portail développeur Discord.
2. Créer une application nommée `Gruterra`.
3. Ajouter un bot à cette application.
4. Activer les intents nécessaires si Discord les demande.
5. Inviter le bot sur le serveur avec les permissions de gestion des rôles et salons.
6. Copier le token du bot dans un fichier privé `.env`.

## Fichier privé `.env`

Créer le fichier :

```text
discord_bot/.env
```

Contenu :

```text
DISCORD_BOT_TOKEN=coller_le_token_du_bot_ici
```

Le fichier `.env` est ignoré par GitHub.

## Installation

```powershell
py -m pip install -r discord_bot/requirements.txt
```

## Lancement

```powershell
py discord_bot/gruterra_discord_bot.py
```

Dans Discord, un administrateur peut ensuite lancer :

```text
!setup_gruterra
```

Le bot crée alors les rôles et salons manquants. Il ne supprime pas les salons existants.

Pendant le setup, le bot publie aussi un message de présentation dans `#useful-links` si ce salon existe. Si un ancien message de présentation du bot existe déjà, il est mis à jour au lieu d'être dupliqué.

## Créer une invitation utilisateur

Un administrateur peut demander au bot une invitation permanente vers un salon public :

```text
!invite_gruterra
```

Cette invitation donne seulement accès au serveur avec les droits normaux du rôle `@everyone`. Elle ne donne pas les rôles `Gruterra Admin`, `Tester` ou `Contributor`.

Pour que cette commande fonctionne, le bot doit avoir la permission Discord `Créer une invitation instantanée` sur le salon utilisé.

## Structure créée

Rôles :

- `Gruterra Admin`
- `Tester`
- `Contributor`

Catégories et salons :

- `📢 INFORMATION`
  - `announcements`
  - `changelog`
  - `useful-links`
- `🌱 GRUTERRA`
  - `general`
  - `plant-tracking`
  - `sensors-and-data`
  - `installation-help`
- `🇫🇷 FRANÇAIS`
  - `discussion-fr`
  - `aide-installation-fr`
  - `retours-fr`
- `🧪 TESTS & FEEDBACK`
  - `demo-feedback`
  - `bugs-feedback`
  - `ideas`
- `🔒 TEAM`
  - `admin-notes`
  - `dev-follow-up`

La catégorie `🔒 TEAM` est visible seulement par les administrateurs Gruterra.

## Sécurité

- Ne jamais publier le token du bot.
- Ne jamais pousser `discord_bot/.env`.
- Garder le bot avec le minimum de permissions nécessaires.
- Ne pas donner de permission administrateur au bot si ce n’est pas nécessaire.
## Où trouver le token du bot Discord

Le token se récupère dans le portail développeur Discord :

```text
https://discord.com/developers/applications
```

Parcours général :

1. Créer ou ouvrir l’application `Gruterra`.
2. Aller dans **Bot**.
3. Cliquer sur **Reset Token** ou **View Token** selon l’état du bot.
4. Copier le token.
5. Le coller uniquement dans le fichier privé local `discord_bot/.env`.

Ne copiez jamais ce token dans GitHub, Reddit, Discord public ou une capture d’écran.

## Où ranger le token

Le fichier privé local doit être :

```text
discord_bot/.env
```

Exemple :

```text
DISCORD_BOT_TOKEN=coller_le_token_du_bot_ici
```

Le dépôt contient seulement :

```text
discord_bot/.env.example
```

Le vrai `.env` est ignoré par GitHub.

## Où inviter le bot sur le serveur

Dans le portail Discord Developer :

1. Ouvrir l’application `Gruterra`.
2. Aller dans **OAuth2**.
3. Aller dans **URL Generator**.
4. Cocher `bot`.
5. Permissions conseillées pour le setup initial :
   - Manage Roles ;
   - Manage Channels ;
   - View Channels ;
   - Send Messages ;
   - Read Message History.
6. Copier l’URL générée.
7. Ouvrir cette URL et choisir le serveur Discord Gruterra.

Après le setup, on pourra réduire les permissions si nécessaire.

## Désactiver la commande de setup

La commande `!setup_gruterra` sert seulement à créer la structure initiale du serveur.

Par sécurité, elle est désactivée par défaut avec :

```text
DISCORD_SETUP_ENABLED=0
```

Pour la réactiver temporairement, modifier `discord_bot/.env` :

```text
DISCORD_SETUP_ENABLED=1
```

Relancer le bot, lancer `!setup_gruterra`, puis remettre :

```text
DISCORD_SETUP_ENABLED=0
```

La commande demande aussi la permission Discord `Gérer le serveur`.
