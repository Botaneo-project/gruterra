# Journal technique des opérations Gruterra

Commandes et résultats utiles au suivi du développement. Les commandes contenant des secrets, adresses privées ou identifiants personnels sont exclues. Ce journal est destiné à être versionné ; ce ne sont pas des instructions à exécuter automatiquement.


## 15/10/2026 — Préparation Home Assistant pour les capteurs Zigbee

Demande : préparer l'arrivée des capteurs, en laissant la clé Zigbee sous la responsabilité de Home Assistant. Aucun accès réseau Home Assistant activé.

Lectures effectuées depuis la racine du dépôt (chemins relatifs utilisables sur un autre poste) :

```powershell
rg --files -g AGENTS.md -g '*mqtt*' -g '*capteur*' -g '*sensor*'
Get-Content _app/database.py -TotalCount 140
Get-Content _app/services/capteurs.py -TotalCount 130
rg -n -i 'home.assistant|mqtt|zigbee' _app --glob '*.py' --glob '!test*'
Get-Content tests/test_weather_store.py -TotalCount 35
Get-Content requirements.txt -TotalCount 60
```

Constat : création des capteurs liée à une adresse BLE ; aucun connecteur Home Assistant existant retrouvé. Une recherche par motifs Windows sur les fichiers de mesures a échoué sans modifier de fichier ; elle n'a pas servi de preuve d'absence.

Fichiers ajoutés : `_app/home_assistant_sensors.py`, `tests/test_home_assistant_sensors.py`, `docs/HOME_ASSISTANT_PREPARATION.md`. Copie des fichiers préparés par un script local temporaire, sans exécution de collecte ni migration de base.

Vérification prévue après copie :

```powershell
python -X utf8 -B -m unittest discover -s tests -p test_home_assistant_sensors.py -v
git diff --check -- docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Premier passage : 6 tests réussis et 2 erreurs de fermeture SQLite sous Windows. Correction : fermer explicitement les connexions, car le contexte transactionnel SQLite ne ferme pas le fichier. Les fichiers du module et du test ont été recopiés puis la même commande de tests a été relancée. Résultat final : 8 tests réussis sur données fictives ; contrôle git diff --check réussi. Aucun relevé utilisateur modifié. Mise à jour finale du résultat par remplacement textuel dans ce journal. Aucune publication GitHub.


## 15/10/2026 — Client Home Assistant en lecture seule

Lecture préalable du module existant, de la fin de ce journal et de `.gitignore`. Vérification : `_config/` et les fichiers `*.local.json` sont exclus du dépôt. Ajout du client, des tests simulés et du modèle vide ; copie par un script local de préparation. Aucun jeton lu ni serveur contacté.

```powershell
Get-Content _app/home_assistant_sensors.py -TotalCount 30
Get-Content docs/JOURNAL_COMMANDES_TECHNIQUES.md -Tail 20
Get-Content .gitignore -TotalCount 55
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Résultat client HA : 14 tests réussis (6 nouveaux et 8 existants), exclusivement avec réponses simulées et archives temporaires. Résultat consigné par remplacement textuel dans ce journal. Configuration réelle, raccordement à l'interface et rattrapage historique non activés. Aucune publication GitHub.


## 15/10/2026 — Formulaire Home Assistant FR/EN

Lecture des formulaires AROME et de la configuration commune pour réutiliser l'écriture atomique, les traductions et la palette. Ajout de `_app/home_assistant_ui.py`, du test associé, du bouton dans Paramètres et des clés `ha_*` dans les catalogues JSON FR/EN. Un script de préparation a copié ces nouveaux fichiers et ajouté le bouton et les traductions sans remplacer les autres modifications de l'interface.

```powershell
Get-Content _app/arome_credentials_ui.py -TotalCount 210
Get-Content _app/botaneo_config.py -TotalCount 155
Get-Content tests/test_arome_credentials_ui.py -TotalCount 90
Get-Content _app/i18n.py -TotalCount 75
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- _app/interface.py _app/locales/fr.json _app/locales/en.json docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Vérification supplémentaire prévue : ouvrir le formulaire avec configuration fictive en français et anglais, puis fermer sans sauvegarder ; aucun accès réseau ni fichier privé effectif. Résultats : 18 tests réussis ; ouverture FR/EN réussie en fenêtre 620 × 440, jeton masqué et bouton Enregistrer visible. Vérification effectuée par un script local de simulation avec configuration fictive et sauvegarde neutralisée. Résultat consigné par remplacement textuel dans ce journal. Aucun envoi GitHub.


## 15/10/2026 — Protection Windows du jeton Home Assistant

Vérification de présence du fichier privé sans afficher son contenu ; aucun fichier présent au début de l'opération. Ajout du module DPAPI, migration en mémoire/écriture atomique, adaptation du formulaire et du client, textes FR/EN et tests de chiffrement avec jetons fictifs. Aucune modification des accès Home Assistant ni connexion réseau.

```powershell
Get-Content _app/home_assistant_ui.py -TotalCount 60
Get-Content _app/home_assistant_client.py -Tail 12
Test-Path _config/home_assistant.local.json
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Les scripts de préparation copient uniquement les fichiers ajoutés et appliquent des remplacements ciblés aux fichiers existants. Une recherche Git en lecture initiale a échoué dans le contexte restreint ; les exclusions sont définies dans `.gitignore` et seront contrôlées dans le contexte du dépôt. Résultats DPAPI : 22 tests réussis sous Windows, dont 4 tests dédiés avec des secrets fictifs. Le chiffrement/déchiffrement réel DPAPI, la migration et le remplacement d’un blob illisible sont vérifiés. Le script de finalisation contrôle aussi la présence d’une configuration réelle et la migre si nécessaire, sans afficher de valeur privée. Résultat consigné par remplacement textuel dans ce journal. Relancer Gruterra avant toute saisie pour charger la nouvelle protection. Aucune publication GitHub.


## 15/10/2026 — Diagnostic du refus de sauvegarde Home Assistant

Signalement utilisateur : refus d'enregistrement, adresse confirmée valide. Aucun contrôle réseau n'est effectué par la sauvegarde ; ce refus ne prouve pas un jeton expiré. Le chemin `.venv/Scripts/python.exe` essayé n'existe pas sur ce poste ; le processus Gruterra utilise Python 3.14. Le test d'écriture atomique/chiffrement/déchiffrement a réussi dans un sous-dossier temporaire de `_config`, avec jeton fictif et nettoyage à la fin.

Ajout de messages FR/EN distincts pour URL, format de jeton, association, protection Windows et accès au fichier. Aucun jeton utilisateur, argument de processus ou message d'exception brut affiché. Cause exacte de la saisie utilisateur encore à déterminer ; ne pas présenter les tests fictifs comme une validation de son jeton.

Commandes de contrôle :
```powershell
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/JOURNAL_COMMANDES_TECHNIQUES.md
```

Une recherche limitée du processus Gruterra a vérifié uniquement son chemin exécutable, sans afficher sa ligne de commande. Résultats : 22 tests réussis ; sauvegarde chiffrée simulée réussie dans le dossier privé. Résultat consigné par remplacement textuel dans ce journal. Relance nécessaire pour charger les nouveaux messages. Aucune publication GitHub.


## 15/10/2026 — Vérification réelle de l’accès Home Assistant

À la demande de l'utilisateur après nouvel enregistrement : lecture locale du format sans sortie de valeurs sensibles ; vérification du blob DPAPI et de son déchiffrement en mémoire. Un script local a exécuté un seul GET `/api/` sur l'adresse privée préalablement confirmée, avec délai limité, sans proxy d'environnement ni redirection. Le corps de réponse et le jeton ne sont ni affichés ni conservés dans le journal.

Résultat : jeton chiffré sur disque sans champ en clair ; déchiffrement Windows réussi ; API HTTP 200. Collecte toujours désactivée, aucune entité configurée. Le succès valide l'authentification générale, pas encore la lecture des futurs capteurs. Aucun état de capteur récupéré ni accès administrateur modifié. Aucun envoi GitHub.


## 15/10/2026 — Historique HA et doublons Bluetooth/HA

Demande utilisateur : empêcher en particulier la double entrée d'un Mi Flora visible en Bluetooth et Home Assistant. Lecture du client et de la fin du module d'états existants ; vérification de la documentation officielle API REST Home Assistant pour `filter_entity_id`, `end_time` et l'historique complet. Ajout de la politique de source unique par identité physique et de la lecture historique bornée ; tests uniquement simulés.

```powershell
Get-Content _app/home_assistant_client.py
Get-Content _app/home_assistant_sensors.py -Tail 35
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Le script de préparation copie uniquement les nouveaux modules/tests et ajoute la documentation. Résultats historique/source : 30 tests réussis, dont 8 nouveaux pour historique et politique de source. Le refus du Mi Flora déjà enregistré en BLE, des alias de même grandeur, des identités absentes et le rejeu de fenêtre sont vérifiés en simulation. Résultat consigné par remplacement textuel dans ce journal. Aucun appel aux états ou à l'historique réels, aucune mesure utilisateur modifiée, aucune publication GitHub.


## 15/10/2026 — Registre Bluetooth réel, statuts et aperçu manuel HA

Lecture du formulaire et de la politique de source existants. Ajout de `_app/home_assistant_registry.py` et de ses tests, intégration ciblée des champs identité/confirmation, statuts et aperçu dans le formulaire. Textes ajoutés aux catalogues FR/EN. Le registre SQLite est ouvert en lecture seule, sans afficher les adresses réelles. La lecture manuelle via l'aperçu vérifie le registre avant toute requête et n'archive aucune donnée.

```powershell
Get-Content _app/home_assistant_ui.py
Get-Content _app/sensor_source_policy.py
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Les scripts locaux copient les seuls nouveaux fichiers et modifient les blocs concernés du formulaire sans remplacer les autres modifications. Un script de simulation ouvre le formulaire FR/EN en fenêtre compacte et contrôle le bouton Enregistrer. Un contrôle de la vraie base renvoie uniquement le nombre d'adresses BLE et la réussite de sa lecture, sans afficher les identifiants. Aucun capteur HA réel ni jeton n'est affiché ; aucune écriture dans les relevés. Résultats registre/aperçu : 36 tests réussis, dont 6 nouveaux tests du registre et de l’aperçu. Registre réel lu avec succès (1 capteur Bluetooth), sans modification ni affichage de MAC. Formulaire compact FR/EN ouvert avec jeton masqué et bouton Enregistrer visible. Résultat consigné par un script local de finalisation dans ce journal. Aucune publication GitHub.


## 15/10/2026 — Archive HA transactionnelle et reprise

Lecture des modules de registre, historique et normalisation existants. Ajout de `_app/home_assistant_archive.py` et `tests/test_home_assistant_archive.py` par copie de nouveaux fichiers préparés localement. Tests exclusivement sur bases temporaires et états fictifs : succès durable, rejeu après réponse perdue, échec SQLite et rollback, lot modifié, trou de progression, renommage, révision et refus d'une base de plantes.

```powershell
Get-Content _app/home_assistant_registry.py -Tail 25
Get-Content _app/home_assistant_history.py -TotalCount 120
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -v
git diff --check -- docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Aucun fichier d'archive réel créé, aucun token utilisé, aucune activation ou requête réseau, aucun relevé de plante modifié. Résultats archive/reprise : 44 tests réussis, dont 8 nouveaux tests d’archive transactionnelle. Coupure simulée par erreur SQLite : aucune fenêtre ni progression partielle conservée. Réponse perdue rejouée sans nouveau fait ; renommage et correction vérifiés. Résultat consigné par script local dans ce journal. Aucune publication GitHub.


## 15/10/2026 — Parcours de récupération manuel HA

Lecture de l'archive et du registre ; vérification du mode démo via `lancer_demo.py`. Ajout du coordinateur de fenêtres, de six tests de parcours et de l'écran FR/EN de préparation/confirmation. Un script copie les nouveaux fichiers et ajoute un bouton au formulaire existant avec les traductions JSON. Aucun token lu ou utilisé, aucun état réel collecté, aucune archive réelle créée.

```powershell
Get-Content _app/lancer_demo.py -TotalCount 65
Get-Content _app/home_assistant_archive.py -TotalCount 70
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -q
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Résultat : 50 tests réussis, dont six tests du parcours : confirmation obligatoire, récupération complète, reprise après HTTP 503, plan modifié refusé, démo exclue et limite de quatre fenêtres. L'état désactivé et le contenu de la base des plantes restent inchangés dans les tests. Vérification des deux fenêtres FR/EN réussie en taille compacte : confirmation visible et désactivée avant préparation, jeton masqué et sauvegarde visible. Scripts locaux de simulation sans accès réseau ni fichier privé ; résultat consigné par script de finalisation. Aucune publication GitHub.


## 15/10/2026 — Présentation de l’historique pendant l’éclairage

Lecture du module existant, de `light_schedule.py`, des traductions et de l’appel depuis l’historique. Remplacement du seul module de présentation, après copie privée de secours de l’ancienne version dans `_security_backups`. Ajout de textes FR/EN et de quatre tests de placement du graphique. Les calculs d’analyse et la synchronisation Pi restent ceux existants.

```powershell
Get-Content _app/light_window_ui.py
Get-Content _app/light_schedule.py -TotalCount 130
python -X utf8 -B -m unittest discover -s tests -p test_light_window_ui.py -v
python -X utf8 -B -m unittest discover -s tests -p test_lamp_sync.py -q
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/HISTORIQUE_ECLAIRAGE_INTERFACE.md docs/JOURNAL_COMMANDES_TECHNIQUES.md GUIDE_TUTORIELS_PUBLICS.md TODO.md
```

Résultats : quatre tests du graphique et deux tests existants de synchronisation réussis. Un script local de vérification ouvre l’écran sur base temporaire FR/EN, thèmes clair/sombre, tailles 620×460 et 1150×850 ; copie simulée (aucun accès au vrai presse-papiers), zéros conservés, validation accessible et aucune écriture de réglage ou de mesure. Dernier passage après les messages d’horaires non enregistrés : les quatre variantes FR/EN clair/sombre réussissent à nouveau, sans écriture de mesure ni de réglage. Résultat consigné par script local de finalisation. Aucune publication GitHub.


## 15/10/2026 — Repères et navigation de l’historique éclairage

Ajout ciblé d'un résumé des observations (dates extrêmes, intervalle intérieur maximal et statut temporel) et de la navigation entre jours. Le script local modifie les seuls blocs concernés et ajoute les textes FR/EN ; aucun horaire utilisateur ni relevé modifié. Les calculs de moyenne et la synchronisation Pi restent inchangés.

```powershell
python -X utf8 -B -m unittest discover -s tests -p 'test_light_window*.py' -v
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/HISTORIQUE_ECLAIRAGE_INTERFACE.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Résultats : 7 tests réussis (4 existants, 3 nouveaux). Deux vérifications locales de fenêtres fictives FR/EN clair/sombre : petites/grandes tailles et navigation sur deux jours. Le contrôle de sélection des onglets et la copie simulée confirment que seule la journée choisie est copiée ; aucun accès au vrai presse-papiers. Aucune publication GitHub.


## 15/10/2026 — Ouverture de l’historique éclairage sur les données réelles

Contrôle en lecture seule sur la Crassula : données disponibles et sélection du dernier jour vérifiées, sans afficher ni modifier les mesures. La borne inclusive précédente pouvait afficher 31 dates malgré le libellé 30 jours ; ajout d’un filtre sur les jours d’allumage compris entre aujourd’hui moins 29 jours et aujourd’hui, en conservant la lecture de contexte nécessaire aux plages traversant minuit. Ouverture par un script local avec le module actuel, sans relancer la collecte ni modifier les horaires. Vérification par le script de navigation sur données fictives ; aucune publication GitHub.


## 15/10/2026 — Harmonisation des couleurs et navigation éclairage

Constat : palette claire différente entre interface principale et historique ; rendu des onglets natifs dépendant du thème Windows. Extraction des palettes principales inchangées dans `_app/ui_palette.py`, import depuis `interface.py` et enrichissement des couleurs de séries dans `vue_historique.py`. Remplacement ciblé du Notebook par deux boutons texte/panneaux dans `light_window_ui.py`. Aucune modification des calculs, données ou horaires.

```powershell
python -X utf8 -B -m unittest discover -s tests -p test_ui_palette.py -v
python -X utf8 -B -m unittest discover -s tests -p 'test_light_window*.py' -q
git diff --check -- _app/interface.py _app/vue_historique.py docs/HISTORIQUE_ECLAIRAGE_INTERFACE.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md
```

Résultats : deux tests de palette/contraste et sept tests de graphique/repères réussis ; navigation sur base fictive FR/EN clair/sombre réussie en petite et grande fenêtre. Contrôle supplémentaire réussi : couleurs et contraste des boutons actifs, affichage du bon panneau après chaque clic, quatre variantes FR/EN clair/sombre. Résultats consignés par script local de finalisation. Syntaxe des modules modifiés vérifiée sans exécuter l’interface principale. Aucune publication GitHub.


## 15/10/2026 — Actualisation et isolation de la démo éclairage

Vérification des générateurs et lanceur démo : écrans communs déjà à jour, mais le fichier d’horaires était fixé au dossier réel. Correction de `light_window_ui.CONFIG` et `lamp_sync.ROOT` pour suivre `BOTANEO_CONFIG_DIR`. Garde démo ajoutée avant lecture de configuration Pi dans la résolution manuelle. Textes FR/EN, scénarios fictifs du générateur et tests ajoutés.

```powershell
Get-Content _app/creer_base_demo.py -TotalCount 135
Get-Content _app/lancer_demo.py -TotalCount 60
python -X utf8 -B -m unittest discover -s tests -p test_lighting_demo.py -v
python -X utf8 -B -m unittest discover -s tests -p test_lamp_sync.py -q
git diff --check -- _app/light_window_ui.py _app/lamp_sync.py _app/creer_base_demo.py docs/HISTORIQUE_ECLAIRAGE_INTERFACE.md docs/JOURNAL_COMMANDES_TECHNIQUES.md GUIDE_TUTORIELS_PUBLICS.md TODO.md
```

Résultats : trois tests démo et deux tests existants de synchronisation réussis. Base candidate créée dans un dossier temporaire sous le dossier démo, vérifiée par `PRAGMA integrity_check` et comptages fictifs. Ancienne base démo sauvegardée par SQLite backup, puis remplacement atomique de la seule base fictive. 4 plantes, 480 relevés, 10 journées dans la plage ; valeur nulle et trou fictif présents. Le schéma peut être lu depuis la base locale, jamais ses données. Vérification FR/EN réussie sur la base fictive actualisée, en petite fenêtre et avec les chemins de configuration démo contrôlés. Résultats consignés par script local ; aucune mesure réelle modifiée. Aucune publication GitHub.


## 15/10/2026 — Règle permanente de maintenance de la démo

À la demande de l’utilisateur : ajout de la règle dans `CONTRIBUTING.md` et en tête des priorités du `TODO.md`. Chaque fonctionnalité doit inclure une vérification et une adaptation de sa démonstration fictive, avec isolement et documentation des limites. Édition documentaire uniquement, aucun test logiciel nécessaire, aucune publication GitHub. Ajouts réalisés par script local avec détection des titres pour éviter les doublons.


## 16/10/2026 — Stabilisation de l’aperçu Home Assistant en démo

Application de la règle de maintenance de démo : découverte d'un aperçu sans garde de mode explicite, alors que le rattrapage était déjà bloqué. Ajout des refus `demo_disabled` avant les chemins réseau/configuration et d'un module d'exemple fictif. L'interface de démonstration utilise ce module en mémoire et ne nécessite aucun vrai identifiant. Textes ajoutés aux catalogues FR/EN.

```powershell
Get-Content CONTRIBUTING.md -TotalCount 70
python -X utf8 -B -m unittest discover -s tests -p 'test_home_assistant*.py' -q
git diff --check -- _app/locales/fr.json _app/locales/en.json docs/HOME_ASSISTANT_PREPARATION.md docs/JOURNAL_COMMANDES_TECHNIQUES.md GUIDE_TUTORIELS_PUBLICS.md TODO.md
```

Résultat : 52 tests du connecteur réussis, dont deux nouveaux tests de gardes démo et d'exemple fictif. Ouverture et clic du bouton fictif FR/EN réussis : quatre états affichés, zéro conservé, indisponibilité distincte, réseau et lectures privées neutralisés. Résultat consigné par script local de finalisation. La lecture initiale du statut Git a échoué dans le contexte restreint ; aucune modification Git effectuée. Aucune donnée réelle ni configuration privée modifiée, aucune publication GitHub.


## 16/10/2026 — Sécurisation du contenu des prochaines archives

Lecture de `prepare_release.py` et du vérificateur GitHub, puis vérification en lecture seule des modules suivis. Constat : plusieurs nouveaux modules restent hors de Git ; aucune action de staging/commit/push n'a été effectuée. Ajout au constructeur d'un refus avant ZIP pour chemins privés, bases, sauvegardes et imports Python locaux manquants. Ajout de `--check-files`, sans archive/manifeste/changelog. Résolution des modules voisins et lecture Git des noms terminés par NUL.

```powershell
python -X utf8 -B -m unittest discover -s tests -p test_prepare_release_content.py -q
python -X utf8 -B prepare_release.py --check-files
git diff --check -- prepare_release.py docs/PREPARATION_ARCHIVE_CONTROLES.md docs/JOURNAL_COMMANDES_TECHNIQUES.md TODO.md CONTRIBUTING.md
```

Résultats : cinq tests réussis. Audit de la sélection Git réelle refusé comme attendu (modules manquants). Audit d'une liste candidate complétée par résolution d'imports : 153 fichiers dont 34 modules nécessaires supplémentaires, contrôle de contenu réussi. Liste candidate conservée dans le document dédié ; aucun ZIP officiel, aucune modification de version/manifeste/index Git, aucun jeton ou contenu privé affiché. Ce contrôle ne remplace pas une relecture complète de secrets avant publication. Aucune modification applicative visible : démo non régénérée pour cet outillage.


## 17/10/2026 — Test d’archive candidate après extraction

Vérification de la liste candidate et des lanceurs/version, sans exécuter de commandes de staging, commit ou publication. Un script local reconstitue les dépendances par analyse AST. Un second construit un ZIP de test dans un répertoire temporaire, vérifie les chemins avant extraction puis lance le script de vérification dans un processus Python `-I -B` avec la copie extraite comme dossier courant. Les chemins de configuration hérités sont effacés avant lancement de la démo ; le réseau est neutralisé. Aucune donnée privée n'est incorporée depuis les dossiers locaux exclus.

Lectures effectuées :
```powershell
Get-Content Lancer_Demo.py -TotalCount 26
Get-Content _app/interface.py -Tail 50
Get-Content version_manifest.example.json -TotalCount 18
git ls-files -- '*.md' '*.json' '*.bat' '*.txt'
```

Résultats : 153 fichiers dans le ZIP temporaire ; démarrage démo, fenêtre éclairage, exemple HA fictif et version locale cohérente vérifiés. Zéro erreur GUI et zéro tentative réseau pendant le court parcours. Le ZIP et le dossier extrait sont supprimés après fermeture. Aucun changement Git, manifeste ou installation réelle. L'installation des dépendances sur PC vierge n'est pas testée. Rapport local de contrôle limité aux booléens et comptes, sans jeton ni chemin utilisateur privé. Aucune publication GitHub.

### 17/10/2026 — Préparation des fichiers publics
- Retrait de la station Netatmo codée en dur dans la comparaison pluie : sélection explicite ou favori local le plus proche, sans station de remplacement imposée.
- Exemple Raspberry sans station personnelle ; plan et TODO sans référence au réseau du domicile.
- Deux tests de comparaison pluie réussis ; audit des 129 fichiers candidats sans jeton JWT, clé privée PEM ni identifiant secret littéral détecté par les contrôles ciblés. Ce contrôle ne constitue pas une garantie exhaustive.
- Aucune configuration privée modifiée ; aucun commit, push ou publication.

### 17/10/2026 — Vérifications Windows disponibles sur ce poste
- Dix tests updater réussis sur installations temporaires : préparation, empreinte, sauvegarde, refus de réinstallation et source du manifeste, fermeture/relance.
- Correction Installer_Gruterra.bat : chemin Python explicite conservé entre guillemets après redétection et installation, compatible avec les espaces.
- Exécution réelle de la routine BAT de redétection avec PATH vide et Python dans un environnement temporaire dont le chemin contient des espaces : interpréteur trouvé puis exécuté avec succès. Aucun téléchargement, installation de dépendances ou changement du Python utilisateur.
- Ce contrôle ne remplace pas un essai complet sur PC vierge. Aucune publication.

### 17/10/2026 — Non-régression des lanceurs Windows
- Ajout de tests/test_windows_launchers.py : deux tests réussis avec environnement Python temporaire, chemins contenant des espaces et aucune installation de dépendances.
- Validation du succès et de la propagation d'un échec du script cible par Lancer_Demo.bat. Documentation des limites du contrôle actualisée.
- Aucune modification de version ou publication.

### 17/10/2026 — BAT démo et composants indispensables
- Vraie démo lancée via son BAT dans une extraction et un environnement temporaires, sans réseau ni donnée utilisateur : succès.
- Contrôle final de cryptography/Ed25519 ajouté à Installer_Gruterra.bat ; commande d’import exacte vérifiée. Guide corrigé (six étapes).
- Pas de publication ni changement de version.

### 17/10/2026 — Installation isolée des dépendances
- Installer_Gruterra.bat exécuté avec succès dans l'extraction temporaire et un environnement vide ; paquets téléchargés/installés séparément de l'installation utilisateur ; pip check réussi.
- Vraie démo lancée ensuite par BAT avec ces paquets : succès. Aucune donnée privée utilisée ; extraction et environnement supprimés après essai.
- TODO et limites de validation actualisées. Pas de changement de version ni publication.

### 17/10/2026 — Application de mise à jour sur installation fictive
- Archive candidate réellement appliquée à une extraction temporaire après ouverture de la démo et création de témoins privés fictifs.
- SHA-256, sauvegarde de la version précédente, conservation des fichiers privés contrôlés et relancement de la démo vérifiés : succès.
- Transport réseau simulé ; ancienne release officielle et fermeture/relance automatique non testées dans ce scénario. Dossier temporaire supprimé, installation utilisateur intacte, aucune publication.

### 17/10/2026 — Ancienne archive et relance de la vraie interface
- Mise à jour depuis ZIP local 0.1.5-dev vérifié par manifeste conservé : réussie, sauvegarde et fichiers privés contrôlés préservés, démo relancée.
- Essai distinct de redemarrer_gruterra dans la vraie interface : fermeture puis seconde instance démo réussies ; attente de sortie ajoutée au banc de test avant nettoyage.
- Copie temporaire supprimée ; aucun changement de l'installation utilisateur, de version ou publication.

### 17/10/2026 — Réseau officiel et anomalie confirmée
- Lecture manifeste GitHub et téléchargement officiel avec SHA-256 vérifié.
- Updater historique 0.1.5-dev appliquant réellement la 0.1.6-dev : succès, sauvegarde et témoins privés conservés ; démo ouverte.
- Relance automatique de la version publiée : seconde interface non ouverte, dialogue d'information observé. Ancien mécanisme lance avant fermeture. Correctif local attente-parent non encore publié.
- Documentation et priorité TODO actualisées. Aucune publication ; installation réelle intacte.

### 17/10/2026 — Sécurisation du correctif relance
- prepare_release.py exige le helper de relance quand l'interface le référence ; tests couvrant source absente, sélection incomplète et archive complète.
- Sept tests de préparation réussis ; cycle unique local application, sauvegarde, conservation et relance automatique réelle de la démo réussi.
- Note de prochaine version préparée dans la documentation. Aucune version changée ni release publiée.

### 17/10/2026 — Deux bugs updater reproduits puis corrigés
- Une archive fictive contenant `_app/plantes.db`, une base à emplacement personnalisé, un fichier SQLite WAL, une configuration privée ou un dossier privé avec casse différente écrasait les témoins locaux : reproduction échouant avant correction, réussie après. Protection par types de bases et chemins privés normalisés, ajout de `_user_backups` et `.venv`.
- Deux sauvegardes avec horodatage identique écrasaient le même ZIP : reproduction puis correction avec nom réservé de façon unique par le système.
- Douze tests updater réussis. Cycle intégré candidat → application → sauvegarde → fermeture/relance de la vraie démo réussi en extraction temporaire. Aucune modification des données réelles.
- Inspection de la détection Python également effectuée ; pas de changement de cette logique dans ce lot. Correctifs conservés localement, sans release.

### 17/10/2026 — Fenêtres météo et couleurs partagées
- Défauts reproduits avant correction : Actualiser non affiché en petite fenêtre pluie ; observations importées en couleur système au lieu du thème demandé.
- Actions météo réservées en bas, textes adaptés à la largeur et choix de commune sur sa propre ligne. Observations météo au thème principal ; couleurs de tableaux et listes readonly appliquées par styles ttk propres à la palette, sans changer le thème Windows global.
- Trois tests GUI réussis couvrant pluie/observations FR/EN clair/sombre et boutons HA à 620 × 440. Contrôles programmatiques de géométrie/couleurs, pas une inspection de captures ni une validation exhaustive. Six tests nappes et aperçu fictif HA FR/EN réussis ; aucune requête météo ni lecture de configuration privée durant les contrôles GUI.
- Aucun changement de traduction nécessaire : libellé Fermer déjà disponible en JSON FR/EN. Données et réglages inchangés, aucun commit ou publication.

### 17/10/2026 — Préparation du push demandé
- Suite complète : 304 tests réussis après ajout de tzdata aux dépendances et contrôle du fuseau Europe/Paris par l’installateur.
- Guide contenant les adresses du réseau du domicile exclu via .gitignore ; modèles publics sans identifiants réels.
- README FR/EN explicitent que main et la release téléchargeable peuvent différer ; pas de changement de version ni de création de release.

### 17/10/2026 — Contrôle de publication selon les valeurs
- Nouvelle sécurité demandée : noms de champs et valeurs vides autorisés ; valeurs sensibles statiques remplies refusées. Anciennes exemptions de contenu par fichier supprimées.
- Champs des modèles OAuth/Netatmo laissés vides, recherche de jetons reconnaissables sur tous les textes, analyse Python sans exécution, diagnostics masqués.
- Données fictives de quinze sources relues autorisées uniquement par empreinte exacte ; changement de contenu invalide la relecture, formats reconnaissables toujours bloqués. Accord utilisateur reçu pour les fichiers relus.
- Dix tests ciblés passent ; documentation dans docs/CONTROLE_PUBLICATION.md. Pas de nouvelle release.

### 17/10/2026 — Validation avant envoi du code
- Suite complète : 314 tests réussis, dont dix scénarios dédiés au contrôle des valeurs privées.
- Contrôle de publication réussi sur la sélection explicite ; contenu de 229 fichiers vérifié sans créer d’archive officielle.
- Corrections de mise en forme finales uniquement ; version, manifeste et dernière release inchangés.
