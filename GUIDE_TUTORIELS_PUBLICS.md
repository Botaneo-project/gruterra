# Plan tutoriels Discord et Reddit

Objectif : préparer des contenus simples pour aider les nouveaux utilisateurs à tester Gruterra sans devoir lire tout le dépôt.

## Tutoriel Discord

But : accueillir quelqu’un qui arrive sur le serveur et lui permettre de tester Gruterra en 10 à 15 minutes.

### Format conseillé

- Message épinglé dans `#welcome` ou `#useful-links`.
- Version courte dans `#announcements` au moment d’une release.
- Aide détaillée dans `#installation-help` et `#aide-installation-fr`.

### Structure du tutoriel

1. **Ce qu’est Gruterra**
   - Application locale de suivi de plantes.
   - Fonctionne en mode démo sans matériel.
   - Peut ensuite utiliser Mi Flora, Raspberry Pi et Netatmo.

2. **Tester sans matériel**
   - Télécharger la release ZIP.
   - Lire `GUIDE_INSTALLATION.md`.
   - Lancer le mode démo.
   - Explorer la Crassula démo, l’historique et les cycles d’arrosage.

3. **Que regarder en premier**
   - Accueil.
   - Historique.
   - Comparaison des cycles d’arrosage.
   - Rappels/arrosages manuels.
   - Netatmo seulement si compte configuré.

4. **Demander de l’aide**
   - Indiquer Windows/Raspberry.
   - Dire si c’est mode démo ou vrais capteurs.
   - Copier le message d’erreur exact.
   - Ne jamais poster de token, mot de passe ou config privée.

5. **Salons utiles**
   - `#welcome` : présentation.
   - `#useful-links` : liens.
   - `#installation-help` : aide générale.
   - `#discussion-fr` : discussion française.
   - `#bugs-feedback` : bugs.
   - `#ideas` : idées.

### Placement automatique avec le bot

Le bot peut publier ou mettre à jour les messages d’accueil et de tutoriel dans les salons prévus.

Commande à lancer dans Discord, idéalement depuis `#bot-commands`, salon privé réservé aux admins :

```text
!post_guides_gruterra
```

Cette commande vérifie les salons connus (`#welcome`, `#useful-links`, `#installation-help`, `#sensors-and-data`, `#discussion-fr`, `#aide-installation-fr`, etc.), puis publie le message adapté ou met à jour l’ancien message du bot si celui-ci existe déjà.

Elle ne recrée pas la structure du serveur et ne touche pas aux rôles. Pour refaire toute la structure, utiliser seulement ponctuellement `!setup_gruterra` avec `DISCORD_SETUP_ENABLED=1`.

Le salon `#bot-commands` est prévu comme salon privé : seuls les admins Gruterra doivent pouvoir y écrire et y lire les commandes. Le bot y publie aussi un mémo des commandes utiles et tente de l’épingler automatiquement. Les commandes de nettoyage ne suppriment pas les messages épinglés ; après un nettoyage, le bot vérifie aussi que le mémo des commandes existe encore.

### Message Discord court prêt à adapter

```text
🌱 Nouveau sur Gruterra ?

Le plus simple est de commencer par le mode démo : aucun capteur, Raspberry ou compte Netatmo nécessaire.

1. Téléchargez la dernière release ZIP.
2. Suivez GUIDE_INSTALLATION.md.
3. Lancez _app\lancer_demo.py.
4. Regardez d’abord l’accueil, l’historique et les cycles d’arrosage.

Besoin d’aide ? Postez dans #installation-help ou #aide-installation-fr avec votre système, la commande lancée et le message d’erreur exact.

Ne partagez jamais vos tokens, mots de passe ou fichiers de configuration privée.
```

## Tutoriel Reddit

But : présenter Gruterra sans faire spam/self-promotion agressive et donner un chemin de test simple.

### Format conseillé

- Un post principal court.
- Une seule image : choisir la capture la plus claire, probablement accueil ou historique démo.
- Mettre le lien GitHub.
- Mettre le lien Discord seulement si le serveur est prêt et stable.
- Préciser que le projet est jeune, local et français-first.

### Angle recommandé

Ne pas vendre Gruterra comme une app finie. Présenter comme :

- projet open-source local ;
- suivi de plantes avec historique ;
- mode démo testable sans matériel ;
- recherche de retours sur l’interface, l’historique et les cycles d’arrosage.

### Structure du post Reddit

1. **Titre anglais court**
   - Exemple : `I built a local plant tracking app with sensor history and watering cycle analysis`

2. **Début du post**
   - Dire que c’est un projet personnel/open-source.
   - Dire que ça peut être testé sans capteur via le mode démo.

3. **Fonctionnalités clés**
   - Plant list.
   - Mi Flora / Flower Care support.
   - Watering logs.
   - Light and soil moisture history.
   - Watering cycle comparison.
   - Optional Raspberry Pi collector.
   - Optional Netatmo weather context.

4. **Ce qu’on cherche**
   - Retours sur le mode démo.
   - Retours sur l’historique.
   - Retours sur l’utilité des analyses d’arrosage.
   - Idées pour rendre l’installation plus simple.

5. **Liens**
   - GitHub.
   - Discord si prêt.

### Corps Reddit prêt à adapter

```markdown
I built a small open-source local app for plant tracking, called Gruterra.

It started as a personal tool to follow a Crassula with Mi Flora / Flower Care data, watering history, light exposure and local weather context. The goal is not only to display sensor values, but to understand what happens over time: watering response, drying speed, light peaks, missing data and longer trends.

It can be tested without any sensor using the demo mode.

Current features:

- local desktop app;
- demo mode with sample plants and history;
- Mi Flora / Flower Care measurements;
- watering logs and reminders;
- graph history with day selection;
- watering cycle comparison;
- optional Raspberry Pi collector;
- optional Netatmo weather context;
- basic auto-update preparation.

The project is still early and mostly French-first, but I’m starting to make it easier to test and document.

I’m mainly looking for feedback on:

- whether the demo mode is understandable;
- whether the history and watering cycle views are useful;
- what would make installation easier;
- what plant tracking features would actually help.

GitHub: https://github.com/Botaneo-project/gruterra
Discord: <lien Discord à ajouter si prêt>
```

## Ordre conseillé

1. Finaliser la première release ZIP.
2. Vérifier que `GUIDE_INSTALLATION.md` est clair.
3. Tester le mode démo depuis un dossier propre.
4. Mettre à jour le message Discord d’accueil.
5. Poster Reddit avec une seule capture claire.
6. Répondre aux retours sans promettre trop vite de grosses fonctionnalités.

## À ne pas faire

- Ne pas poster de tokens ou captures avec configuration privée.
- Ne pas annoncer chaque petit commit.
- Ne pas présenter l’auto-update comme totalement fini tant que la première release n’est pas publiée et testée.
- Ne pas prétendre que l’app est entièrement traduite en anglais.
