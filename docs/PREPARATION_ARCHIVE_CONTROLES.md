# Contrôles avant prochaine archive Gruterra

État local vérifié le 16/10/2026. Aucune version publiée ou manifeste modifié.

Le constructeur utilise uniquement les fichiers suivis par Git. La liste courante omet des modules nécessaires aux écrans récents : elle est donc refusée avant toute création de ZIP, même avec `--allow-dirty`. Le contrôle d’arbre propre reste également en place pour une préparation officielle.

Contrôle sans création :

```powershell
python -X utf8 -B prepare_release.py --check-files
```

Ce contrôle refuse les chemins privés/temporaires, bases de données, configuration effective, sauvegardes et modules Python locaux importés mais absents de la sélection. Les exemples vides `.local.json.example` restent autorisés. Il analyse les imports Python déclarés, y compris à l’intérieur des fonctions, mais ne garantit pas la résolution de tout chargement dynamique ni la présence des dépendances externes.

Liste candidate vérifiée par résolution récursive : 153 fichiers, dont 34 modules nécessaires supplémentaires. Cette liste candidate n’a pas été ajoutée à Git et n’a pas produit d’archive. Elle porte sur les dépendances du code ; les documents et tests nouvellement créés devront être relus et inclus séparément selon le périmètre retenu.

## Modules nécessaires hors de la sélection Git actuelle

- `_app/arome_credentials_ui.py`
- `_app/communes_meteo.py`
- `_app/contribution_donnees.py`
- `_app/contribution_identite.py`
- `_app/contribution_protocole.py`
- `_app/contribution_suivi.py`
- `_app/home_assistant_archive.py`
- `_app/home_assistant_catchup.py`
- `_app/home_assistant_catchup_ui.py`
- `_app/home_assistant_client.py`
- `_app/home_assistant_demo.py`
- `_app/home_assistant_history.py`
- `_app/home_assistant_registry.py`
- `_app/home_assistant_secrets.py`
- `_app/home_assistant_sensors.py`
- `_app/home_assistant_ui.py`
- `_app/lamp_sync.py`
- `_app/light_schedule.py`
- `_app/light_window_ui.py`
- `_app/meteo_nappes.py`
- `_app/meteo_pluie.py`
- `_app/meteo_synthese.py`
- `_app/netatmo_pi_credentials_ui.py`
- `_app/pluie_meteofrance.py`
- `_app/sensor_source_policy.py`
- `_app/ui_palette.py`
- `_app/weather_backup_pc.py`
- `_app/weather_protocol.py`
- `_app/weather_store.py`
- `_app/weather_sync.py`
- `_app/weather_view.py`
- `raspberry/collector/pi_web_i18n.py`
- `raspberry/weather_backup.py`
- `raspberry/weather_outbox.py`

## Avant publication

1. Relire et sélectionner explicitement les fichiers publics à intégrer, avec leurs documents et tests ; ne jamais ajouter globalement les fichiers locaux.
2. Vérifier les secrets contenus dans les fichiers : le contrôle de chemins/imports ne remplace pas cette relecture.
3. Inclure les changements validés dans Git, puis refaire `--check-files`, les contrôles GitHub et la validation dans un dossier extrait isolé.
4. Vérifier le lancement réel et démo, les fichiers de langue, les assets et la conservation des données lors de la mise à jour.
5. Choisir la version et ses notes de publication ensemble ; publier uniquement sur autorisation.

Validation de ce renforcement : cinq tests sur répertoires temporaires (module manquant, chemins privés, échappement de chemin, exemple public autorisé et mode de contrôle sans écriture). La démo n’a pas de nouveau parcours visible pour ce changement d’outillage ; son générateur fait partie des sources dont les imports sont vérifiés.


## Essai d’extraction isolée — 17/10/2026

Une archive strictement temporaire de 153 fichiers a été construite depuis la liste candidate, nommée explicitement « audit-local-non-publie », puis extraite dans un répertoire temporaire. Elle comprend les 34 modules nécessaires supplémentaires hors sélection Git. Aucun ajout Git ni modification de version/manifeste n'a été effectué.

Contrôles réussis : points d'entrée, fichier VERSION, palettes et modules récents présents ; vérification de motifs de jetons JWT/GitHub sans afficher de contenu ; lancement réel de `Lancer_Demo.py` depuis la copie extraite avec Python isolé (`-I`) ; création de la base fictive et des réglages uniquement sous l'extraction ; ouverture du nouvel écran d'éclairage et disponibilité de l'exemple HA fictif ; version locale cohérente avec VERSION. Zéro erreur de callback GUI et zéro tentative réseau sur ce parcours court, avec connexion réseau explicitement neutralisée.

Le ZIP et son extraction ont été supprimés à la fin du test. Ce test n'a pas lancé l'application réelle sur les données utilisateur, installé Python ou les dépendances, testé les actions différées après fermeture de la fenêtre ni validé une mise à jour de bout en bout. Il utilise le Python et les bibliothèques déjà disponibles sur ce poste. Il ne constitue pas un audit complet de secrets ou une validation de diffusion publique.

La préparation officielle reste conditionnée à la relecture et l'intégration explicite des fichiers publics, y compris documents et tests, puis au contrôle des secrets et à l'essai d'installation sur un poste vierge. La sélection Git seule reste actuellement incomplète ; aucune release n'est déclarée prête ou publiée.

### Contrôle complémentaire du 17/10/2026
La comparaison pluie utilise les favoris locaux, classés par distance connue, ou une station explicitement demandée. Une sélection explicite absente ne provoque aucun remplacement silencieux. Quatre tests passent : zéro réel, absence de favori, plusieurs favoris et distances invalides, priorité et absence de sélection explicite.
Après ces corrections, nouvel essai réussi de la démo depuis les 153 fichiers extraits : écran éclairage et exemple Home Assistant disponibles, version cohérente, aucune erreur GUI ni tentative réseau. Installation des dépendances sur PC vierge et mise à jour complète restent à tester. Aucune publication effectuée.

### Tests Windows reproductibles
Le fichier tests/test_windows_launchers.py conserve deux tests exécutables sur Windows : redétection et exécution de Python installé sous un chemin avec espaces, PATH vide ; lancement du BAT de démo avec un script cible fictif, succès puis erreur transmise. Les deux tests passent. Le script fictif vérifie le câblage du lanceur ; il ne remplace pas le contrôle séparé de la vraie interface démo depuis l'archive extraite. Aucun réseau, pip ou fichier utilisateur utilisé.

### Lancement réel par BAT depuis la copie extraite
Le 17/10/2026, Lancer_Demo.bat a lancé la vraie démo depuis les 153 fichiers candidats extraits sous un chemin temporaire. Un environnement .venv temporaire réutilisait les paquets disponibles sur le poste : aucune installation de dépendances réalisée. Réseau neutralisé, chemins de données isolés, écran éclairage et exemple HA fictif vérifiés, version cohérente et aucune erreur GUI sur ce parcours court. Fermeture automatique par le banc de test ; archive et environnement temporaires supprimés. Ce contrôle ne valide ni le téléchargement de Python ni une installation sur poste vierge.
L’installateur vérifie désormais aussi l’import du support Ed25519 de cryptography ; cette commande exacte réussit sur ce poste. Le guide reflète les six étapes affichées.

### Installation des dépendances en environnement vide — 17/10/2026
Ce contrôle complète et dépasse la limite des essais précédents concernant les paquets Python. Une nouvelle extraction temporaire des 153 fichiers candidats a reçu un environnement .venv sans accès aux paquets du Python hôte. Installer_Gruterra.bat a installé les dépendances de requirements.txt et terminé avec succès. Le contrôle pip check ne relève aucune incompatibilité. Lancer_Demo.bat a ensuite démarré la vraie démo avec cet environnement : chemins isolés, version cohérente, écran éclairage et exemple HA fictif disponibles, zéro erreur GUI et zéro tentative réseau pendant le parcours GUI contrôlé. Les accès réseau nécessaires au téléchargement des dépendances étaient autorisés pendant l'installation.
L'extraction, la base fictive et l'environnement ont été supprimés après contrôle. Python 3.14 déjà installé a servi à créer l'environnement vide ; le téléchargement automatique de Python 3.12.10 et son installation sur PC sans Python restent non testés. Ce résultat ne valide pas non plus une mise à jour complète d'une ancienne version ni une publication officielle.

### Cycle applicatif de mise à jour sur copie fictive — 17/10/2026
Une première ouverture de la vraie démo dans l'extraction candidate a créé ses données fictives. Des fichiers témoins locaux ont été ajoutés et la version de départ remplacée par une valeur de test. Le moteur appliquer_mise_a_jour a ensuite réellement remplacé les fichiers depuis l'archive candidate, avec vérification SHA-256 et création de sauvegarde. Le transport réseau seul était remplacé par une copie du ZIP local : aucun manifeste ni téléchargement GitHub vérifié ici.
Résultats : application réussie ; version candidate restaurée ; sauvegarde contenant la version de départ ; empreintes inchangées des fichiers privés contrôlés (configuration, historique, données et base de démo, témoins de base locale et ancienne sauvegarde). La sauvegarde du programme ne contient pas la configuration privée ni les données de démo. Nouvelle ouverture de la vraie démo après remplacement réussie, écran éclairage et exemple HA disponibles, aucune erreur GUI ni tentative réseau sur le parcours contrôlé.
Ce scénario part d'une copie du code candidat avec une version fictive de départ, pas d'une ancienne release officielle. Il ne valide pas la migration depuis une archive historique, le téléchargement GitHub ou l'enchaînement automatique fermeture/relance de l'interface. Tous les fichiers et données temporaires ont été supprimés après contrôle.

### Archive historique et relance automatique — 17/10/2026
1. L'archive locale gruterra-0.1.5-dev.zip a été vérifiée contre le SHA-256 du manifeste de release conservé. Après extraction et génération de ses données démo, l'archive candidate a réellement été appliquée. La sauvegarde contient VERSION 0.1.5-dev ; les empreintes privées contrôlées sont inchangées ; la vraie démo redémarre avec le code candidat. Le téléchargement était simulé localement et l'authenticité de l'archive n'a pas été revérifiée en ligne.
2. Dans un essai distinct, la vraie interface démo extraite a appelé redemarrer_gruterra : fermeture automatique de la première instance, attente du processus et relance par restart_gruterra.py. La seconde instance a ouvert la démo et l'écran éclairage, sans erreur GUI ni requête réseau sur le parcours contrôlé. Le banc de test a attendu sa fermeture effective avant suppression de l'environnement. Un premier essai avait tenté le nettoyage trop tôt ; ce problème du banc de test a été corrigé.
Les deux scénarios réussissent séparément. Ils ne constituent pas encore un essai unique réunissant téléchargement GitHub, application et relance automatique après clic utilisateur. Aucun fichier de l'installation réelle, manifeste public ou version n'a été modifié.

### Parcours réseau réel et anomalie de la release publiée — 17/10/2026
Manifeste récupéré sur GitHub et archive officielle 0.1.6-dev téléchargée : empreinte SHA-256 conforme. Dans une extraction temporaire de la 0.1.5-dev, son propre updater a réellement téléchargé et appliqué cette archive officielle. Sauvegarde de VERSION 0.1.5-dev vérifiée, configuration fictive et base de démo inchangées pendant application, puis vraie démo 0.1.6-dev ouverte : succès.
ANOMALIE REPRODUITE : la relance de la 0.1.6-dev publiée crée la nouvelle instance avant fermeture de l'ancienne. Dans le test, la nouvelle instance affiche une information puis se termine sans ouvrir l'interface. Le code local corrigé attend déjà la sortie effective du parent via restart_gruterra.py ; ce parcours local a été validé séparément, mais il n'est pas dans l'archive publiée. L'absence du helper dans l'ancienne archive n'est pas en soi un fichier manquant : cette version utilise l'ancien mécanisme intégré.
La séquence réseau et application est donc validée, pas la relance de la release actuellement téléchargeable. Prévoir le correctif local et son helper dans la prochaine sélection de release, sans modifier silencieusement une archive publiée. Aucun envoi de données privées ; réseau neutralisé après installation pour le test GUI. Toutes les copies temporaires ont été supprimées.

### Correctif local de relance sécurisé — 17/10/2026
Le code local ferme l'interface puis utilise restart_gruterra.py pour attendre la fin effective du processus parent avant de relancer une seule instance dans le bon mode. Une nouvelle protection de prepare_release.py refuse avant écriture toute archive dont l'interface référence ce helper mais qui ne le contient pas : le lancement par subprocess n'était pas couvert par la seule analyse des imports. Sept tests de contenu réussis, dont absence du helper source, omission dans la sélection et sélection complète.
Un même scénario temporaire a appliqué l'archive candidate corrigée, vérifié la sauvegarde de la version précédente et les empreintes privées, puis fermé et relancé automatiquement la vraie interface démo. La seconde instance ouvre la démo, l'écran éclairage et l'exemple HA ; zéro erreur GUI et zéro tentative réseau sur ce parcours. Le ZIP est local et son transport simulé ; ce résultat concerne le code candidat, pas l'archive 0.1.6-dev actuellement sur GitHub. Dossiers et environnement temporaires supprimés.
Note proposée pour la prochaine version : Correction du redémarrage après mise à jour : Gruterra attend la fermeture complète de l'ancienne instance avant d'ouvrir la nouvelle. Protection de préparation des archives contre l'oubli du composant de relance. La version reste à choisir avant diffusion autorisée.

### Protection supplémentaire contre les archives mal composées — 17/10/2026
Le filtrage à l’application ne se limite plus à l’ancien chemin `plantes.db` à la racine : les fichiers `.db`, `.sqlite`, `.sqlite3` et leurs journaux/WAL/SHM restent exclus du remplacement, quel que soit leur emplacement. Les configurations `.local.json` restent privées. Les chemins privés sont comparés sans distinction de casse, et `_user_backups` ainsi que `.venv` sont conservés. Cette barrière complète l’exclusion des données lors de la préparation des archives.
Une reproduction d’application avec bases et configuration privées présentes dans le ZIP vérifie que le programme est mis à jour mais pas ces fichiers. Une seconde reproduction vérifie deux sauvegardes créées à la même seconde : elles possèdent désormais des noms distincts, réservés atomiquement, et conservent chacune leur contenu initial. Douze tests updater passent ; le cycle intégré de mise à jour et relance démo passe aussi.
Note pour la prochaine version : correction de la protection des bases locales, y compris `_app/plantes.db`, et de la collision des sauvegardes rapprochées. Les sauvegardes déjà créées ne sont ni renommées ni supprimées. Ces correctifs ne sont pas encore publiés.
