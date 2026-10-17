# Tutoriels Discord et Reddit

État relu le 10/10/2026 : release 0.1.6-dev ; main contient des corrections ultérieures non encore livrées. Ce document prépare les contenus, sans publication automatique.

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

Le bot peut publier ou mettre à jour les messages d’accueil et de tutoriel dans les salons prévus. Chaque salon créé par le bot possède un message d’introduction adapté à son usage.

Commande à lancer dans Discord, idéalement depuis `#bot-commands`, salon privé réservé aux admins :

```text
!post_guides_gruterra
```

Pour actualiser, privilégier `!post_guides_gruterra`, qui modifie les messages existants. Un reset ne doit pas être utilisé comme entretien courant ; il conserve les messages socle protégés. Commande de dépannage :

```text
!reset_guides_gruterra
```

Si `#bot-commands` est invisible ou inutilisable, lancer depuis un autre salon accessible :

```text
!fix_bot_commands
```

Si les salons d’information en lecture seule refusent les messages du bot (`#useful-links`, `#bot-log`, `#welcome`, etc.) :

```text
!fix_info_channels
```

Cette commande vérifie les salons connus (`#welcome`, `#useful-links`, `#installation-help`, `#sensors-and-data`, `#discussion-fr`, `#aide-installation-fr`, etc.), puis publie le message adapté ou met à jour l’ancien message du bot si celui-ci existe déjà.

Elle ne recrée pas la structure du serveur et ne touche pas aux rôles. Pour refaire toute la structure, utiliser seulement ponctuellement `!setup_gruterra` avec `DISCORD_SETUP_ENABLED=1`.

Le salon `#bot-commands` est prévu comme salon privé : seuls les admins Gruterra doivent pouvoir y écrire et y lire les commandes. Le bot y publie aussi un mémo des commandes utiles et tente de l’épingler automatiquement. Les commandes de nettoyage ne suppriment pas les messages épinglés ; après un nettoyage, le bot vérifie aussi que le mémo des commandes existe encore. Dans les salons en lecture seule comme `#welcome`, `#useful-links` ou `#bot-log`, `@everyone` reste bloqué en écriture, mais le bot doit recevoir explicitement le droit d’envoyer et de gérer ses messages.


### Tutoriels complets avec captures

Une fois les messages d’introduction propres, le bot peut publier des tutoriels plus détaillés dans les salons adaptés. Les captures du dossier local `capture/` sont jointes automatiquement si elles existent.

```text
!post_tutos_gruterra
```


Si les salons privés équipe refusent le bot (`#admin-notes`, `#dev-follow-up`, `#bot-commands`) :

```text
!fix_private_channels
```

Protection des messages socle : les introductions et tutoriels publiés par le bot sont épinglés automatiquement. Les commandes de nettoyage ignorent les messages épinglés. Pour vérifier ou ré-épingler tous les messages importants :

```text
!pin_base_messages
```

Pour repartir de zéro sur les tutos sans toucher aux messages épinglés :

```text
!reset_tutos_gruterra 300
```

Placement prévu :

- `#useful-links` : GitHub, Reddit et guides principaux ;
- `#installation-help` : installation en anglais ;
- `#aide-installation-fr` : installation en français ;
- `#demo-feedback` : mode démo avec captures ;
- `#plant-tracking` : historique et cycles d’arrosage avec captures ;
- `#sensors-and-data` : Mi Flora, Netatmo et Raspberry ;
- `#retours-fr` : plantes avec ou sans capteur ;
- `#bugs-feedback` : méthode de rapport de bug ;
- `#admin-notes` : mémo privé des commandes utiles Discord et Gruterra.

### Message Discord court prêt à adapter

```text
🌱 Nouveau sur Gruterra ?

Le plus simple est de commencer par le mode démo : aucun capteur, Raspberry ou compte Netatmo nécessaire.

1. Téléchargez la dernière release ZIP.
2. Suivez GUIDE_INSTALLATION.md.
3. Double-cliquez sur Installer_Gruterra.bat, puis Lancer_Demo.bat.
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
- Préciser que le projet est jeune et local, avec interface principale FR/EN et documentation encore partiellement française.

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
- guided updates from Settings, with archive verification and a local backup;

The project is still early. The main interface supports French and English; some detailed guides, personal notes and older release notes remain in French.

On Windows: download the official release ZIP, extract it, double-click Installer_Gruterra.bat, then Lancer_Demo.bat. The installer attempts to install Python if needed. No Git, sensor or Raspberry Pi is required for the demo.

Mi Flora readings describe the area around the sensor, not the condition of the entire root ball. Sharing contributions to a future website is not enabled.

I’m mainly looking for feedback on:

- whether the demo mode is understandable;
- whether the history and watering cycle views are useful;
- what would make installation easier;
- what plant tracking features would actually help.

GitHub: https://github.com/Botaneo-project/gruterra
Discord: <lien Discord à ajouter si prêt>
```

## Ordre conseillé

1. Utiliser la dernière release ZIP publiée (0.1.6-dev au moment de cette relecture), sans confondre son contenu avec main.
2. Vérifier que `GUIDE_INSTALLATION.md` est clair.
3. Tester le mode démo depuis un dossier propre.
4. Mettre à jour le message Discord d’accueil.
5. Poster Reddit avec une seule capture claire.
6. Répondre aux retours sans promettre trop vite de grosses fonctionnalités.

## À ne pas faire

- Ne pas poster de tokens ou captures avec configuration privée.
- Ne pas annoncer chaque petit commit.
- Mentionner le passage 0.1.5-dev → 0.1.6-dev testé ; garder les contrôles de redémarrage et de conservation des données sur PC de secours dans la liste restante.
- Ne pas prétendre que l’app est entièrement traduite en anglais.


## Suivi des nappes — version en préparation après 0.1.6-dev
Dans Paramètres, ouvrir « Configurer le suivi des nappes (facultatif) ». Saisir un département français, chercher les stations puis choisir un point en vérifiant sa date de dernier relevé. « Actualiser les niveaux » récupère jusqu’à 100 relevés Hub’Eau / ADES ; « Enregistrer le choix » conserve la sélection. La case d’affichage ajoute un accès sur l’accueil au prochain rafraîchissement. Aucun appel automatique n’est effectué à l’ouverture.
Les niveaux en mètres NGF sont des altitudes ; les profondeurs sont rapportées au repère du forage. Ce ne sont ni un pourcentage de remplissage ni une alerte sécheresse. La courbe relie les relevés disponibles sans prouver une évolution continue. Le cache et le choix restent dans `_config/`, exclus de GitHub.
Source : https://www.data.gouv.fr/dataservices/hubeau-piezometrie

### Groundwater monitoring — upcoming version after 0.1.6-dev
Open the optional groundwater settings, enter a French department and choose a station after checking its last reading date. Refresh levels on request, then save your selection. The optional home screen shortcut appears after refreshing the home screen. No automatic fetch occurs at startup. Levels are elevations in metres NGF, not percentages full; depth uses the borehole reference point. Old readings and lines between observations must not be interpreted as current levels or continuous changes.

Le suivi des nappes masque désormais les stations sans relevé dans les 365 derniers jours. « Inclure les stations anciennes ou sans date » donne accès aux archives ; le tri utilise plusieurs pages. Un département peut ne fournir aucune station récente : essayer un département voisin, sans confondre proximité et aquifère. / Groundwater monitoring now defaults to stations with a reading within the last 365 days. Enable historical stations to browse archives; some departments have no recent station.

### Suivi des nappes — aide locale, non publiée
Le bouton « Comprendre les mesures » explique la date, le niveau NGF, la profondeur par rapport au repère et la qualification. Pour une nappe captive, une faible profondeur dans le forage ne signifie pas que l’aquifère est proche du sol. Le panneau adopte le thème actif de Gruterra.

The groundwater panel now includes measurement help in French and English and follows the active theme. NGF is an elevation; depth is relative to the borehole reference. Confined-aquifer pressure can raise water in the borehole. Qualification describes measurement validity, not drinking-water quality.

Le tableau distingue désormais la qualification et le statut de validation déclarés par Hub’Eau. Un tiret signifie que la source ou l’ancien cache ne fournit pas cette information, sans déduire une validation.
The table now separates qualification from the validation status reported by Hub’Eau. A dash indicates missing information, not an inferred validation.

### Consultation météo PC — modification locale non publiée
Les consultations Netatmo du PC actualisent le cache météo sans ajouter de relevés à l’historique pluie. L’historique déjà enregistré reste conservé. La collecte Raspberry requiert encore un accès validé ; aucun token PC n’est dupliqué.
PC Netatmo consultations refresh the weather cache without adding rainfall history. Existing history is preserved. Raspberry collection still requires validated access; PC tokens are not duplicated.

### Pluie Météo-France — modification locale non publiée
Paramètres → Pluie Météo-France — suivi séparé → Consulter les pluies proches. Les relevés horaires sont conservés dans _app/data/meteofrance_pluie.sqlite3, hors base des plantes et hors Git. Les dates affichées sont celles des observations. Les corrections ne sont pas additionnées. Aucun appel automatique ; clé privée dans _config/meteofrance.local.json. La consultation courante ne reconstitue pas à elle seule les dernières 24 heures.
Settings → Météo-France rainfall — separate records → Check nearby rainfall. Manual hourly readings are kept in a dedicated weather database, separately from plant data and Netatmo. Check source dates; revisions must not be added together. No automatic collection. The current lookup alone does not reconstruct the past 24 hours.

Le panneau pluie affiche également le dernier cache PC de la station Netatmo choisie, avec ses cumuls 1 h / 24 h. Comparer uniquement des périodes horaires alignées ; le panneau ne calcule pas de différence et ne récupère pas Netatmo lui-même. Actualiser la météo PC puis rouvrir le panneau pour relire son cache.
The rainfall panel also shows the selected Netatmo station’s latest PC cache. Compare aligned hourly periods only; no automatic difference is calculated and the panel makes no Netatmo requests. Refresh PC weather and reopen the panel to read its cache.

Dans le panneau pluie, saisir un code postal puis Chercher la commune. Choisir une commune si plusieurs correspondent, puis Consulter les pluies proches. Les distances sont approximatives depuis son centre. Sans code postal, le point météo configuré reste utilisé. Aucun changement de la localisation Netatmo.
In the rainfall panel, enter a postal code, find and select a municipality, then check nearby rainfall. Distances are approximate from its centre. Without a postal code the configured weather location is used. Netatmo settings remain unchanged.

### Météo Raspberry — validation locale du 13/10/2026, non publiée

La collecte Netatmo Raspberry a effectué un premier passage réel et le timer horaire est activé. Les observations sont importées dans Gruterra à la synchronisation, avec sauvegarde vérifiée et reprise sans doublon. Paramètres → Météo du Raspberry → Observations météo importées permet de lire les dates source, unités, valeurs et périodes. L’accès Netatmo du PC reste disponible pour la consultation fraîche, sans nouvel archivage de pluie. Le scénario PC physiquement éteint et le redémarrage matériel restent à vérifier.

Raspberry Netatmo collection completed its first real cycle and the hourly timer is enabled. Gruterra imports observations during synchronisation, with verified backups and duplicate-free replay. Settings → Raspberry weather → Imported weather observations shows source dates, units, values and periods. Direct PC weather access remains available without adding rainfall history. A physically powered-off PC test and a Pi hardware restart still need verification.

Paramètres → Accès Météo-France AROME-PI : saisir l’Application ID pour OAuth2 ou le jeton temporaire, sans préfixe Basic/Bearer. Les secrets restent privés et masqués ; enregistrer n’active aucun timer. La validation du raccordement AROME local reste à effectuer.
Settings → Météo-France AROME-PI access: enter the OAuth2 Application ID or temporary token, without Basic/Bearer. Secrets remain private and masked; saving enables no timer. Local AROME integration still requires validation.


### Vérification du passage automatique — 13/10/2026

Le service météo du Raspberry a été déclenché par son timer à 22:06:18 (heure de Paris), avec un résultat réussi. Dix-huit observations issues des passages automatiques ont ensuite été importées sur le PC. La sauvegarde météo du Pi a été copiée et vérifiée sur le PC ; dates, unités et valeurs importées correspondent exactement aux observations exportées.

Le rejeu du lot ajoute zéro observation et reconnaît les 18 doublons. La synchronisation suivante confirme une file vide. Le timer horaire reste actif.

Cette vérification ne constitue pas encore un essai avec le PC physiquement éteint ni un test de redémarrage matériel du Raspberry.


### Historique pendant l’éclairage — présentation locale du 15/10/2026

FR : dans l’historique de la plante, ouvrir « Historique pendant l’éclairage ». Choisir une journée pour voir les résumés, la courbe et les relevés ; utiliser « Comparer les journées » pour la vue sur 30 jours. Copier ne reprend que la journée sélectionnée.

EN: open “History during lighting” from the plant history, select a day to review summaries, chart and readings, and use “Compare days” for the 30-day table. Copy exports only the selected day.

Guide détaillé : `docs/HISTORIQUE_ECLAIRAGE_INTERFACE.md`. Modification locale, version téléchargeable non publiée à ce stade.


### Démo éclairage actualisée — 15/10/2026

FR : lancer `Lancer_Demo.bat`, ouvrir la Crassula démo puis son historique pendant l’éclairage. Les exemples incluent un zéro et une interruption de relevés, tous fictifs. Les horaires de démo restent isolés et aucune synchronisation Pi réelle ne se lance depuis cet écran.

EN: run `Lancer_Demo.bat`, open the demo Crassula and its lighting-window history. Fictional examples include a zero reading and missing readings. Demo schedules are isolated; this screen does not connect to the real Pi.

Préparation locale : ces changements ne constituent pas une nouvelle archive téléchargeable publiée.


### Aperçu Home Assistant fictif — 16/10/2026

FR : dans la démo, Paramètres → Capteurs Home Assistant → Voir un exemple fictif. L’exemple fonctionne sans Home Assistant ni jeton et montre aussi zéro et indisponibilité.

EN: in demo mode, Settings → Home Assistant sensors → View fictional example. No Home Assistant instance or token is needed; zero and unavailable states are demonstrated.

Changement local uniquement, aucune nouvelle archive publique publiée.
