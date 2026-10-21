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

### 17/10/2026 — Bootstrap Python Windows
- Recherche du Python installé par Gruterra avant les commandes du PATH, contrôle de version à chaque sonde, py -3 pour éviter un Python incompatible.
- Cinq tests isolés réussis ; seuls téléchargement et installation Windows réels restent non validés sur poste vierge. Aucun Python existant désinstallé ou réinstallé.
- Lot de test local contenant seulement le BAT corrigé, requirements.txt et les instructions ; aucune release créée.

### 17/10/2026 — Formulaires secondaires accessibles
- Défaut reproduit sur les deux fenêtres AROME/Netatmo Pi : Enregistrer disparaissait à texte agrandi. Corps défilant partagé ui_scroll_form.py et pied fixe, sans modification des fonctions de sauvegarde.
- Radio-boutons harmonisés dans le thème, libellé Fermer réutilisé depuis les JSON FR/EN. Aucun secret chargé pour les contrôles, formulaires remplis uniquement par des valeurs vides fictives, aucun réseau ni transfert de jetons.
- Démo : même code GUI exercé en FR/EN, clair/sombre et taille compacte ; pas de nouvelle donnée à ajouter au générateur. Contrôles programmatiques de géométrie et masquage, sans validation visuelle exhaustive sur chaque écran Windows.
- Modifications locales, sans commit, push ni release ; installateur EXE encore à préparer.

Résultat du lot fenêtres secondaires : 318 tests réussis. Archive candidate temporaire de 230 fichiers, incluant explicitement ui_scroll_form.py hors sélection Git actuelle, extraite et vraie démo lancée avec succès ; zéro erreur GUI et zéro requête réseau sur le parcours contrôlé. ZIP temporaire supprimé. Aucun changement des données utilisateur, de version ou publication.

### 17/10/2026 — Premier installateur EXE local
- Compilateur officiel Inno 7.1.0 signé Pyrsys B.V. vérifié puis extrait en mode portable ; aucun ajout global de cet outil.
- Script FR/EN de préversion et constructeur sécurisé ajoutés ; mode BAT sans pause pour l’exécution automatique, échec bloquant et journal privé local.
- EXE installé dans un dossier temporaire avec espaces ; dépendances et vraie démo vérifiées, réinstallation et désinstallation réussies sans perte des données fictives. Disposition de raccourcis isolée, pas d’entrée de désinstallation Windows pour le test.
- Artefact normal de test conservé sous _dist ; non signé, code interne toujours 0.1.6-dev, pas une release 0.1.7 publiée.

Bilan du lot EXE : 320 tests réussis ; aucune alerte de valeur privée sur les fichiers modifiés/nouveaux. Préversion normale compilée dans _dist, statut Authenticode NotSigned confirmé. Variante isolée testée avec succès : installation, dépendances, démo, réinstallation et désinstallation conservant les données fictives. Les différences de disposition de raccourcis et de registre sont décrites dans docs/INSTALLATEUR_EXE_TEST.md. Pas de commit, push ou release dans ce lot.

### 17/10/2026 — Retour utilisateur sur l’EXE
Installation signalée OK par l’utilisateur. Contexte Python préalable et démarrage de la démo en attente de précision ; aucune autre validation déduite de ce seul retour. Aucune publication.

Précisions du retour EXE : Python déjà installé ; démo ouverte avec succès après installation. Parcours utilisateur avec Python existant validé, sans extension au scénario poste vierge.


## 18/10/2026 — Corrections issues de l’audit global

- Modifications locales : récupération après échec de mise à jour, verrou avant installation, historique défilant et actualisé après import, fuseau d'éclairage commun et graphique sans lissage.
- Tests ciblés sur installations/relevés fictifs, puis suite complète : `python -X utf8 -B -m unittest discover -s tests -q` — 330 tests réussis.
- Contrôle de contenu : `python -X utf8 -B verifier_avant_github.py` ; cohérence : `git diff --check` — réussis (avertissement de normalisation des fins de ligne uniquement).
- Compilation/essai isolé du script Inno avec données fictives : refus pendant utilisation, aucun remplacement, puis réussite après libération. Aucune entrée menu Démarrer ni registre de désinstallation pour ce test.
- Reconstruction locale : `python -X utf8 -B prepare_windows_installer.py --compiler <compilateur-Inno-officiel-verifie> --additional-file _app/ui_scroll_form.py --additional-file _app/ui_data_events.py` — 231 fichiers, non signé, non publié.
- Aucun changement de base utilisateur, aucune activation de partage, aucun push, aucun changement de version.

Limites et travaux restants : docs/AUDIT_GLOBAL_2026-10-18.md.


### 18/10/2026 — Comparaisons et cycles

- Corrections des sous-fenêtres de l'historique et réutilisation des composants défilants ; aucun changement de schéma ni d'enregistrement utilisateur.
- Tests ciblés : `python -X utf8 -B -m unittest discover -s tests -p test_history_comparison_windows.py -v`.
- Suite complète : `python -X utf8 -B -m unittest discover -s tests -q` — **338 tests réussis** ; vérification de contenu incluant les nouveaux fichiers et `git diff --check` réussies.
- Scénarios fictifs : actualisation et copie, ajout de fraction, nouveau cycle, sélection retirée, ouverture vide, lecture inaccessible, reprise et redimensionnement ; FR/EN, clair/sombre, texte agrandi.
- Installateur local de préparation reconstruit selon la commande documentée plus haut, sans publication. Le scénario Python absent reste en attente ; aucune version modifiée.


### 18/10/2026 — États météo et cache

- Vue météo importée et cache Netatmo : source/date de récupération explicites, actualisation des fenêtres, avertissement si affichage conservé, réponses mal formées refusées.
- Tests ciblés : `python -X utf8 -B -m unittest discover -s tests -p test_weather_cache_status.py -v` et `python -X utf8 -B -m unittest discover -s tests -p test_weather_view_freshness.py -v`.
- Suite complète : `python -X utf8 -B -m unittest discover -s tests -q` — **348 tests réussis**. Jeux de données fictifs uniquement, aucune requête météo réelle et aucune modification OAuth.
- Contrôle public incluant les nouveaux fichiers et `git diff --check`, puis reconstruction locale de l'installateur selon la commande déjà documentée. Aucun push ni changement de version.


### 18/10/2026 — Centre d'alertes

- Correction des dates UTC et futures, rappels calendaires, tri par priorité et liste dépliable ; états indisponibles explicites. Vérification d'un nouvel arrosage sur base fictive.
- Prévisions simulées : rejet des créneaux passés et du cache expiré ; une pluie absente ou partielle ne devient pas zéro. Aucun nouveau seuil de rafale.
- Tests ciblés : `python -X utf8 -B -m unittest discover -s tests -p test_alerts_consistency.py -v` ; suite complète : **363 tests réussis**.
- Contrôle public incluant les nouveaux fichiers, puis reconstruction locale avec les trois sélections supplémentaires : `--additional-file _app/ui_scroll_form.py --additional-file _app/ui_data_events.py --additional-file _app/services/alertes_temps.py`.
- Aucun réseau météo réel, aucune base utilisateur modifiée, aucun e-mail envoyé, aucun push et aucune nouvelle release.


### 18/10/2026 — Récupération après arrêt forcé de l’updater

- Journal durable, moteur autonome, verrou partagé, récupération avant ouverture réelle/démo ; fichiers privés exclus.
- Tests ciblés : `python -X utf8 -B -m unittest discover -s tests -p test_update_crash_recovery.py -v` ; suite complète : **371 tests réussis**.
- De vrais processus enfants ont été arrêtés sur des dossiers fictifs ; aucun processus utilisateur interrompu. Restauration interrompue puis reprise, validation terminée, sauvegarde corrompue, chemins privés et conflits testés.
- Script Inno compilé/essayé avec fichiers fictifs : refus pour application/updater actifs et journal en attente, puis réussite après résolution. Aucune simulation de coupure électrique matérielle.
- Sélection additionnelle pour la reconstruction locale : modules graphiques/alertes déjà documentés, `--additional-file update_recovery.py --additional-file docs/RECUPERATION_MISE_A_JOUR.md`.
- Aucun jeton modifié, aucun réseau météo, aucune base réelle modifiée, aucun push ni nouvelle release.

### 18/10/2026 — parcours intégré du candidat actuel
Exécution du contrôle local `verify_current_update_cycle.py` : sélection publique du constructeur EXE (234 fichiers), archive et installation temporaires, lancement réel de la démo, application avec sauvegarde, comparaison des empreintes privées fictives puis redémarrage automatique via BAT. Résultat : succès, zéro tentative réseau, zéro erreur graphique détectée. Rapport local : `CORRECTED_UPDATE_AND_RESTART_REPORT.json`. Aucun push ni changement de version. Test sans nouvelle installation des dépendances et avec téléchargement simulé.

### 18/10/2026 — récupération avec la démo complète
Contrôle supplémentaire sur une copie complète de 234 fichiers : démarrage de la vraie démo, arrêt brutal du processus de mise à jour après remplacement du module de récupération par un module de test incompatible, puis lancement officiel de la démo. La copie figée de récupération restaure le programme précédent et supprime le journal uniquement après succès. La démo et sa fenêtre éclairage se rouvrent ; empreintes de la base de démonstration et des fichiers de configuration conservées. Zéro tentative réseau et zéro erreur graphique détectée. Ce test d'arrêt de processus ne simule pas une coupure physique de courant. Rapport local : REAL_DEMO_RECOVERY_20261018.json ; lanceur : verify_real_demo_recovery.py. Données réelles et GitHub inchangés.

### 18/10/2026 — rattrapage Home Assistant : compte rendu accessible
Compte rendu remplacé par un texte en lecture seule, sélectionnable et copiable, avec son propre défilement. Corps de fenêtre défilant, note adaptée à la largeur, confirmation et fermeture fixes sur deux lignes pour éviter les débordements. Aucun changement du protocole ni activation de collecte. Test graphique sur données fictives : rapport long, copie Unicode, erreur de préparation affichée, actions accessibles à 620 × 420 et facteur Tk 2.0, FR/EN, clair/sombre. Les 371 tests existants passent ; le nouveau test (quatre combinaisons langue/thème) passe également. Aucun contrôle visuel natif revendiqué. L'EXE déjà construit précède cette correction et devra être reconstruit avant diffusion.

### 18/10/2026 — classement en six priorités et réglages Home Assistant
Ordre actif enregistré dans TODO.md : sécuriser les mises à jour, corriger l'historique, fiabiliser les dates, améliorer la lecture, harmoniser les fenêtres, préparer la publication. L'audit reprend cet ordre en tête tout en conservant les constats historiques.
Réglages Home Assistant : corps défilant, actions sur lignes séparées, messages adaptés à la largeur, boutons Enregistrer/Fermer fixes. Aucun changement du stockage privé, du protocole ou des autorisations ; aucun jeton réel lu pour les essais. Deux tests graphiques couvrent les réglages et le rattrapage, en FR/EN, dans les deux thèmes et avec facteur Tk 2.0. Suite complète : 373 tests réussis. Empreinte de l'exception fictive existante renouvelée seulement pour _app/home_assistant_ui.py après relecture (valeur draft-only inchangée) ; protections contre les vrais secrets conservées.
EXE de préparation reconstruit avec les corrections : 234 fichiers, version interne 0.1.6-dev conservée, non signé, non publié. SHA-256 : 210427977732eb88bba3413e3af1a3ea3ec21a5e09d58639ba5269e0dc426189.
Restent avant diffusion : PC sans Python, revue visuelle native générale, décision de version définitive et essai depuis l'archive officielle. Les validations programmatiques ne remplacent pas la revue visuelle.

### 18/10/2026 — fenêtres locales de contribution
Information : texte et commandes dans un corps défilant, fermeture fixe, sauvegarde/restauration/suivi disposés verticalement, palette héritée de la fenêtre parente ou transmise explicitement. Suivi : notice adaptée à la largeur, fermeture fixe, tableau défilable sur deux axes et couleurs du thème principal. Les opérations de gestion des clés, la signification des reçus, les protections de la démo et le protocole restent inchangés ; partage désactivé.
Trois tests supplémentaires : accès aux actions à 440 × 320, lecture du suivi à 460 × 300, facteur Tk 2.0, FR/EN et clair/sombre ; aucune action de clé en démo. Identités et reçus fictifs ou simulés uniquement. Suite complète : 376 tests réussis. La validation est programmatique, pas une revue visuelle native exhaustive. Aucun push ni changement de version.

### 18/10/2026 — installation Zigbee dans Home Assistant
Intervention par l'interface Home Assistant, après connexion effectuée par l'utilisateur : Mosquitto broker officiel 7.1.1 installé et démarré ; dépôt officiel https://github.com/zigbee2mqtt/hassio-zigbee2mqtt ajouté ; Zigbee2MQTT stable 2.14.2-1 installé. Les deux applications apparaissent en cours d'exécution, mais Zigbee2MQTT affiche seulement son assistant de première configuration : aucun réseau Zigbee opérationnel confirmé.
Aucun adaptateur proposé dans l'assistant et aucun port tty USB visible dans Matériel système, même après actualisation. Configuration non soumise, aucun appairage lancé, aucune intégration existante supprimée. Démarrage automatique Zigbee2MQTT laissé désactivé tant que le matériel et la configuration ne sont pas validés ; raccourci latéral activé. Mosquitto conserve son démarrage automatique par défaut. Aucun firmware flashé, aucun jeton Gruterra modifié. Prochaine action : vérifier/rebrancher la clé sur le Raspberry exécutant Home Assistant, puis contrôler son port stable et son type avant configuration. Capture locale de la liste des applications conservée dans l'espace de travail, sans secret.

### 18/10/2026 — nouvelle détection et premier démarrage Zigbee
Vérification via le terminal Home Assistant : lsusb et liste /dev/serial/by-id ; périphérique USB 1a86:7523 présent, /dev/ttyUSB0, chemin /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0. Le nom by-id est générique (pas de numéro de série unique constaté) : attention si un second adaptateur identique est ajouté.
Après relance de l'application, périphérique sélectionné dans l'assistant ; pilote zstack retenu selon la fiche officielle Haozee CC2652P + CH340C, 115200 bauds, rtscts désactivé. Paramètres MQTT locaux fournis automatiquement conservés ; aucune valeur secrète copiée dans ce journal. Découverte Home Assistant activée par défaut conservée, intégration MQTT Mosquitto ajoutée avec confirmation de succès dans l'interface.
Premier démarrage : Serialport opened, puis échec explicite network commissioning timed out / ZDO stateChangeInd après 100000 ms. Application ensuite en état Erreur : réseau Zigbee non opérationnel, aucun appairage lancé. L'erreur mentionne notamment des identifiants de réseau en conflit, sans prouver cette cause. Pas de changement répété d'identifiants ni effacement de mémoire radio, aucun flash firmware. Démarrage automatique maintenu désactivé. Prochaine étape physique : débrancher dix secondes puis rebrancher la clé, idéalement sur une rallonge USB et éloignée du Raspberry ; refaire un démarrage contrôlé. Si persistant, confirmer référence/firmware et analyser avant toute réinitialisation.
Sources : https://www.haozee.com/products/haozee-zigbee-3-0-usb-dongle-plus-universal-zigbee-wireless-gateway-hub-support-home-assistant-zigbee2mqtt-raspbian-ubuntu-maco ; https://www.zigbee2mqtt.io/guide/adapters/zstack.html ; https://www.zigbee2mqtt.io/guide/installation/20_zigbee2mqtt-fails-to-start_crashes-runtime.html

### 18/10/2026 — essai après remise sous tension de la clé
Nouveau lancement avec port/pilote conservés : même échec network commissioning timed out à 15:32:34 (horloge du journal Home Assistant), après ouverture du port série. La reconnaissance USB est confirmée, mais elle ne prouve pas la création du réseau radio.
Avant un essai avec nouveaux PAN ID et Extended PAN ID, copie privée de configuration conservée sur Home Assistant : /config/zigbee2mqtt/configuration.before-network-test.yaml (copie sans écrasement). Aucun contenu secret affiché par cette opération. Nouveaux identifiants générés dans l'assistant, clé réseau conservée, aucun appairage existant dans ce réseau. Résultat de cet essai consigné séparément après vérification. Aucun firmware flashé ni mémoire radio effacée.
Résultat de l'essai PAN/Extended PAN différents : même délai dépassé, à 15:35:39 dans le journal Home Assistant. Aucune conclusion certaine de conflit PAN ni de firmware défectueux. Configuration précédente restaurée depuis la sauvegarde et comparaison octet par octet réussie (original_configuration_restored). Copie de l'essai infructueux conservée uniquement dans /config/zigbee2mqtt/configuration.failed-pan-test.yaml sur Home Assistant. Le service reste en erreur, démarrage automatique désactivé ; MQTT reste installé/configuré. Prochaine investigation : référence matérielle et firmware coordinateur exacts, puis alimentation/interférences ; aucune mise à jour firmware autorisée ou exécutée dans cet essai.

### 18/10/2026 — identification photographique du coordinateur
Photos fournies par l'utilisateur : emballage Zigbee 3.0 USB Dongle, modèle ZG-808Z, puce indiquée CC2652P1, alimentation 5 V / 100 mA max ; étiquette commerciale HZ-USB Dongle. Cela conforte le choix du pilote zstack ; le port CH340 1a86:7523 observé est cohérent avec la fiche Haozee CC2652P1 + CH340C. La photo ne révèle pas la version de firmware réellement installée et ne permet pas de conclure qu'il faut flasher.
Fiche fabricant : https://www.haozee.com/products/haozee-zigbee-3-0-usb-dongle-plus-universal-zigbee-wireless-gateway-hub-support-home-assistant-zigbee2mqtt-raspbian-ubuntu-maco
Notice du modèle retrouvée : https://ae01.alicdn.com/kf/Sd51cbee7e72b43d9906b006f6f488037K.pdf
Ne pas appliquer un firmware de clé EFR32/Ember à ce modèle, ni choisir un fichier seulement d'après son nom commercial. Le défaut reste l'échec de création du réseau, distinct d'une absence de clé USB. Version/rôle du firmware et matériel à vérifier avant tout flash ou effacement radio. Les photos restent hors des sources publiques ; aucun fichier privé transféré.

### 18/10/2026 — antenne confirmée et lecture seule du firmware
Utilisateur : antenne vissée confirmée. Service Zigbee2MQTT vérifié en état error ; pas de nouveau lancement réseau pendant ces sondes. Les terminaux déjà installés ne disposent pas de Python3 pour l'outil de lecture envisagé. Tentative bornée via port série POSIX à 115200 : requête ZNP SYS_VERSION (FE 00 21 02 23), puis requête de redémarrage logiciel SYS_RESET_REQ type 1 suivie de SYS_VERSION. Aucune réponse exploitable reçue pendant les fenêtres de lecture ; aucun diagnostic définitif sur le firmware ou une panne matérielle ne peut en être tiré. Aucun accès aux clés, aucune commande d'effacement NVRAM, aucun flash. Configuration précédente conservée. Prochaine étape proposée : connexion USB au PC Windows pour identifier le port et tenter une interrogation avec un outil série adapté, avant de choisir toute image firmware.
Référence du protocole : https://github.com/Koenkk/zigbee-herdsman/blob/master/src/adapter/z-stack/znp/definition.ts (SYS version et resetReq).

### 18/10/2026 — lecture directe de la clé sous Windows
Détection Windows : USB-SERIAL CH340 (COM3), état pilote OK. pySerial 3.5 installé depuis PyPI dans un répertoire de diagnostic isolé de l'espace de travail, pas dans Python global ni Gruterra. Interrogation bornée ZNP : ping et SYS_VERSION, puis lecture des seules entrées non secrètes LOGICAL_TYPE (135), BDBNODEISONANETWORK (85), CHANLIST (132). Aucun accès aux clés.
Après séquence de démarrage normale du pilote (octet de sortie bootloader puis impulsion RTS sans flash), réponse SYS_VERSION valide : transport 2, produit 1, version 2.7.1, révision 20250321. Lectures suivantes directes : ping reçu, rôle configuré coordinateur, marqueur de réseau formé faux. CHANLIST lu sans canal actif ; cela ne suffit pas à prouver une cause, car les paramètres de formation BDB peuvent être distincts. Clé répondante sur Windows : pas de diagnostic de matériel mort ou de firmware absent. Aucun firmware remplacé, aucune écriture/effacement NVRAM. La création radio demeure non validée.
Outil et rapport de diagnostic locaux : zigbee_read_firmware.py et ZIGBEE_FIRMWARE_READ_20261018.json dans l'espace de travail Codex, non ajoutés à Git. Le port COM est fermé après chaque lecture.
Sources de vérification du protocole et de la séquence : https://github.com/Koenkk/zigbee-herdsman/blob/master/src/adapter/z-stack/znp/definition.ts ; https://github.com/Koenkk/zigbee-herdsman/blob/master/src/adapter/z-stack/znp/znp.ts ; https://github.com/Koenkk/zigbee-herdsman/blob/master/src/adapter/z-stack/constants/common.ts

### 18/10/2026 — recherche de cas communautaires comparables
Recherche demandée sur Reddit, forums et tickets du projet, sans modification du matériel.
1. Reddit : témoignage de fonctionnement du modèle exact ZG-808Z, interface CH340 et pilote zstack. Confirme la compatibilité possible, ne prouve pas le bon fonctionnement de chaque exemplaire : https://www.reddit.com/r/homeassistant/comments/1pgo5km/works_with_z2m_model_zg808z_zigbee_30_usb_dongle/
2. Retour direct HOMEd : ZG-808Z, CC2652, firmware 20250321, absence de réponse au reset logiciel ; auteur indique une résolution par la séquence RTS/contrôle de flux. Cela ressemble à notre lecture de version devenue possible après la séquence normale RTS sur Windows. Cas différent : HOMEd et non notre version Zigbee2MQTT ; reset=flow est une option HOMEd, ne pas la copier dans Zigbee2MQTT. Notre pilote Zigbee2MQTT réalise déjà une séquence RTS : piste à comparer, pas solution démontrée. https://community.homed.dev/d/84-problema-stik-sonoff-zg-808z
3. Ticket Zigbee2MQTT 27296 : Raspberry Pi 4, autre coordinateur CC2652P, firmware 20250321 et même erreur network commissioning timed out ; plusieurs essais de firmware sans résolution annoncée dans la description. Ne démontre ni défaut du modèle exact ni problème d'alimentation chez nous : https://github.com/Koenkk/zigbee2mqtt/issues/27296
4. Ticket herdsman 1767 : certains CC2652 mettent environ 76 s à former leur réseau après effacement ; correctif 1799 portant le délai de 60 à 100 s. Notre erreur attend déjà 100000 ms : le seul correctif de délai décrit est donc insuffisant pour expliquer/résoudre notre cas. https://github.com/Koenkk/zigbee-herdsman/issues/1767 ; https://github.com/Koenkk/zigbee-herdsman/pull/1799
Ordre d'investigation conservé : vérifier l'étiquette réelle du bloc et la sous-tension du Pi Home Assistant .39, puis comparer la réponse de démarrage sur le Pi et tester un autre canal si pertinent. Ni flash, ni réinitialisation, ni remplacement de clé justifiés par les témoignages seuls. Pas de cause certaine établie. Aucun nouveau test matériel effectué pendant cette recherche.

### 18/10/2026 — essai concluant sur port USB 2 Home Assistant
Clé déplacée par l'utilisateur sur USB 2. Vérifications via terminal web officiel : lien /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 présent vers ttyUSB0 ; cmp confirme la configuration de référence inchangée avant essai. Démarrage de Zigbee2MQTT puis Submit de l'onboarding sans changement de paramètres. Vers 19:18, journaux MQTT de découverte publiés et interface Zigbee2MQTT opérationnelle, zéro appareil associé, appairage fermé. Commande de lecture : ha apps logs 45df7312_zigbee2mqtt | tail -n 15.
Lancement au démarrage activé et vérifié dans la page Info ; chien de garde et mises à jour automatiques restent désactivés. Aucun flash ni effacement. Résultat compatible avec un problème lié au précédent environnement USB, sans distinguer alimentation, perturbations ou contact. Appairage des capteurs et stabilité longue durée restent à tester. Capture de preuve locale : zigbee-usb2-succes.png dans l'espace de travail Codex.

### 18/10 — Profils Zigbee dans le raccordement Home Assistant
Modifications locales des validations, du formulaire, des traductions FR/EN et de la démo. 52 tests Home Assistant et 6 nouveaux tests profils réussis avant dernière vérification de la démo. Aucune requête réseau, configuration privée, base de plantes, flash ou publication. Les tests utilisent des identités fictives. Guide : INTEGRATION_CAPTEURS_ZIGBEE.md.

### 18/10/2026 — raccordement réel Crassula-test en aperçu
Entités relevées dans les fiches Home Assistant, sans déduire les identifiants à partir des noms : quatre quantités distinctes du capteur Zigbee suffixe 0946. Lecture par le client Gruterra existant : HTTP 200, snapshot_ready. Contrôle de propriété et anti-doublon BLE autorisé. Association enregistrée dans la configuration privée locale, test_data=true, enabled=false. Configuration précédente sauvegardée localement dans _config, secret conservé chiffré ; aucun jeton affiché. Aucune ligne ajoutée aux mesures des plantes, aucune archive historique réelle ni import automatique activé.
Aperçu : sol 5 %, air 61 %, température 22,7 °C. Lux 0 avec état HA ancien (19h46 heure Paris) : ne constitue pas une nouvelle mesure physique. Rapport de contrôle sans jeton conservé dans l’espace de travail Codex : ZIGBEE_HA_PREVIEW_REPORT.json. Capteur EIT et Mi Flora non ajoutés/modifiés.

### 18/10 — Archive réelle test et moteur de retrait
Client historique HA borné du 18/10 19h40 à 22h39 Paris, quatre entités test 0946 : 32 états archivés séparément. Rejeu strict du lot : 0 ajout, 32 doublons ; aucun import plante/collecte automatique. Nouvelle purge limitée aux faits entièrement test, avec sauvegarde vérifiée et exclusion contre réimport, testée uniquement sur bases fictives. Aucune suppression réelle. Rapports locaux dans l’espace Codex, sans secrets.

### 18/10 — Interface de retrait des tests
Écran local bilingue relié au moteur de retrait, aperçu périmé à toute modification de sélection, confirmation explicite et sauvegarde avant retrait. 68 tests Home Assistant passent, comprenant 3 tests UI/date avec variantes FR/EN et thèmes ; aucune suppression réelle. Aperçu réel en lecture seule : 32 états/32 enveloppes du 0946 le 18/10. Aucun réseau ni changement d’association dans ce lot.

### 18/10 — Validation globale après intégration Zigbee
18 tests de retrait (incluant ceux de l’archive par héritage) puis suite complète tests/ : 403 réussis en environ 29 secondes. Scénarios de sauvegarde impossible, rollback SQL, faits mixtes, démo, base de plantes et rejeu modifié contrôlés sur données fictives. Aucune suppression réelle ni nouveau réseau. Pas de build ni publication.

### 18/10 — Finalisation du parcours applicatif Zigbee
Consultation depuis la carte détaillée de la plante et les réglages, graphiques sans interpolation, filtre par association privée, récupération bornée reliée au flux de synchronisation existant et bilan FR/EN. Association réelle 0946 → Crassula enregistrée avec test=true ; sync_on_request activé, configuration chiffrée sauvegardée avant modification. Récupération réelle : 5 états ajoutés, 37 au total. Données Mi Flora et plantes.db non modifiées. Suite complète 415 tests réussis. Stabilisation initiale des températures notée, pas d’effacement automatique. Aucune release/build.

### 18/10 — Analyse approfondie et firmware Arteco
Sources publiques officielles et correctifs conservés comme texte dans l’espace Codex, empreintes SHA-256. Comparaison du décodeur attendu pour Z2M 2.14.2 (26.115.1) avec master, pas preuve du contenu réel du conteneur. Lux x10, DP110 asymétrique, corrections signées identifiés. Recherche OTA sans image explicitement compatible trouvée. Archive locale analysée en lecture seule (37 états) ; indice d’états HA initiaux reconstruits au curseur signalé comme priorité. Aucun firmware exécuté, flash, calibration ou suppression. Rapport : ANALYSE_ARTECO_ZS304Z_2026-10-18.md.

### 18/10 — Raccordement luminosité indépendante
Device_id et entity_id relevés dans Home Assistant pour le ZG-106Z 52dd. Aperçu par client Gruterra HTTP 200 : 5 lx récent. Association privée test et Crassula, sauvegarde chiffrée préalable. Historique six heures : 499 états ajoutés, rejeu 0 ajout/499 doublons. Cinq associations configurées ; récupération de synchronisation existante conservée. Aucun réglage radio, firmware, calibration ou mesure Mi Flora modifié. Rapport local ZIGBEE_LIGHT_INTEGRATION_REPORT.json. Assistant de découverte utilisateur noté comme restant à développer.

### 19/10 — Contrôle après la nuit, 09h17 Paris
Lecture seule HA historique et instantané : HTTP 200. Arteco 0946 température21°C/air55%/sol8% à09h14, lux94 à09h04. Capteur52dd lux12 à09h17 ; autour de09h04 :5lx contre94Arteco, écarts6,69secondes. Aucun état indisponible dans les données retournées, pas preuve de continuité radio. Aucun réglage ni base utilisateur modifié. Bilan détaillé BILAN_CAPTEURS_2026-10-19.md.

### 19/10 — Datation des quantités
Documentation officielle HA vérifiée. Ajout d’une couche d’interprétation sans mutation de la structure/identité des archives : état, changement de valeur, rapport HA et récupération Gruterra séparés. État initial suspect et attributs seuls exclus du graphique, lignes originales gardées. Requête historique skip_initial_state=true et significant_changes_only=0. Lecture réelle HTTP200 :62 états/heure,0exactementàlaborne ; archive536états inchangée,4étatsinitiauxsuspects. Tests temporels/démo/GUI en cours de validation complète ; aucun réglage capteur, firmware ou calibration modifié.

Validation datation terminée : 422 tests complets réussis, puis tests Home Assistant revérifiés après actualisation de la démo. Sources locales uniquement ; relancer Gruterra pour charger les colonnes et statuts. Aucun import de mesure physique revendiqué, aucune donnée ancienne effacée.

### 19/10 — Résumé accueil et État Gruterra
Module home_assistant_summary en lecture seule sans accès réseau ni déchiffrement du jeton pour l’affichage. Bloc accueil et texte de santé reliés, mode test et ancienneté, sélection indépendante par capteur/quantité, démo et thèmes. Vérification par synchronisation existante autorisée :395 états ajoutés séparément ; deux appareils affichés, aucune mesure Mi Flora remplacée. 429 tests complets OK. Pas de publication/build.

### 19/10/2026 — Simplification accueil
Modification locale interface.py, ui_action_flow.py, meteo_pluie.py et catalogues FR/EN. Contrôle syntaxique, tests unitaires complets (429 OK), contrôle Tk des actions après redimensionnement et test SQLite fictif de chronologie pluie. Aucun changement des mesures de plantes ni activation de collecte. Redémarrage de l’application nécessaire pour charger le code.

### 19/10/2026 — Lecture du graphique HA
Ajout home_assistant_chart.py ; raccordement dashboard et traductions FR/EN. Contrôle de la conservation des zéros, exclusion des états incertains/conflits, affichage des axes à deux largeurs, puis 99 tests Home Assistant réussis. Aucune donnée réelle modifiée, aucune publication.

### 19/10/2026 — Ouverture du suivi connecté
Ouverture locale reproduite avec succès, blocage utilisateur non reproduit. Fenêtre désormais liée à la principale et ramenée au premier plan après construction ; message générique traduit en cas d’échec du bouton (aucun secret ni exception brute). Test d’ouverture réel local sans réseau et tests Home Assistant.

### 19/10/2026 — Cause du bouton identifiée
Import meteo_nappes manquant dans ouvrir_suivi_connecte : le module était importé seulement dans d’autres fonctions. Correction locale et test de régression exécutant le vrai callback extrait de l’interface, sans variable globale implicite.

### 19/10/2026 — Graphique vide malgré états archivés
Cause : valeurs numériques conservées en chaînes décimales, rejetées par le nouveau graphique. Conversion float limitée à l’affichage ; zéros préservés, non-finis/inconnus/conflits exclus. Tests de régression et vérification en lecture seule des quatre grandeurs réelles.

### 19/10/2026 — Lisibilité du graphique HA
Échelle automatique à graduations arrondies, option 0–100 % pour les humidités, sélecteur Tk aux couleurs explicites et contraste des en-têtes corrigé. Survol regroupant les états voisins horizontalement pour lire leurs heures et valeurs distinctes sans supprimer de données. 102 tests HA réussis.

### 19/10/2026 — États Zigbee rapprochés
Analyse lecture seule : 10 paires sol et 2 température espacées de moins d’une seconde, avec valeurs différentes. Origine précise non démontrée (trames/converter à confronter). Présentation graphique par groupes bornés à une seconde, par appareil et grandeur, barres d’écart orange et dernier état indiqué sans validation physique ; option états bruts. Archives inchangées. Test de conservation de tous les membres, séparation appareils, fenêtre non chaînée.

### 19/10/2026 — Préparation du correctif externe ZS-304Z
Source officielle v26.122.0 téléchargée, définition limitée au modèle ZS-304Z ; helpers signés rétroportés sur 26.115.1. Test Node isolé avec scripts d’installation désactivés : import, préparation de définition, DP3 brut, lux x10, offsets signés et DP110 validés. Fichiers relisibles dans docs/zigbee. Aucune activation : enable_external_js=false constaté ; accord explicite restant nécessaire avant ouverture de cette capacité.

### 19/10/2026 13:17 — Activation ZS-304Z autorisée
Accord explicite obtenu ; copie du fichier testé contrôlée par SHA-256, enable_external_js activé, redémarrage Zigbee2MQTT. Deux ZS-304Z reconnus, un convertisseur externe chargé, trois appareils toujours associés. Premier relevé réel …3498 à 13:18:23 : 0 % sol, 50 % air, 22,4 °C, 2050 lux final. Contrôle immédiat sans erreur fromZigbee ni chargement. Sauvegarde conservée et marqueur privé de changement de conversion lux enregistré ; données historiques inchangées.

### 19/10/2026 — Historique : contraste et disposition compacte
Filtres alignés avec libellés et largeurs naturelles, sélection lumière par défaut et première dans la liste ; indicateurs sur une ligne et repères rapides compacts. Champ Combobox natif remplacé uniquement pour le style local par un élément clam, sans modifier le thème global. 434 tests complets réussis avant ajout du contrôle de régression dédié ; contrôle FR/EN, clair/sombre, 860 pixels et lumière par défaut ajouté et exécuté.

### 19/10/2026 — Traçabilité de conversion et fraîcheur
Ajout sensor_conversion_notes.py (lecture locale contrôlée, désactivée en démo), notice et repère graphique au changement de conversion Arteco ; aucune archive recalculée. Historique Mi Flora : avertissement plus de 2 h depuis le dernier relevé importé, sans affirmer une panne de collecte. Tests du marqueur valide/invalide et isolation démo, suite complète exécutée. Aucune publication ou nouvelle collecte automatique.

### 19/10/2026 — Calculs et messages des cycles
Audit services/analyse_arrosage.py et construire_sessions_arrosage. Correction regroupement inter-plantes, volumes partiels/non finis, comparabilité des dates et conversion des humidités invalides ; qualité longue interruption prioritaire. Durée d’observation explicitée pour les taux normalisés sur 24 h, et contexte descriptif sans recommandation automatique. Nouveaux tests : fractions intercalées de deux plantes, volume inconnu/invalide, trou long avec deux mesures, dates ISO variées, humidités invalides et quatrième cycle fictif. Vérification des trois séances réelles par connexion SQLite mode ro ; aucune mesure ni aucun arrosage modifiés.

### 19/10/2026 — Comparaison descriptive des vitesses de séchage
Ajout services/comparaison_sechage.py et intégration à l’analyse/copie des cycles existantes. Fenêtre commune 24–72 h après dernier apport, bornes ±2 h, au moins quatre instants, trou maximal 8 h, source unique. Motifs précis d’exclusion et attente du prochain cycle ; aucune recommandation de volume/date ni arrosage anticipé. Six tests ciblés, suite complète 449 OK, contrôle des trois cycles réels en lecture seule.

### 19/10/2026 — Validation du parcours réel sur données fictives
Extraction AST des véritables fonctions de saisie, base SQLite temporaire et callbacks d’interface testés, sans importer le démarrage de l’application. Parcours confirmation/annulation, fractions 40+55, rappel, alertes et actualisation historique vérifiés. Correction risque de doublon après erreur secondaire de demande de collecte ; conservation du rappel futur pour un complément de séance ; quantités non finies rejetées ; défilement avec validation fixe et style local des sélecteurs. Tests n’écrivant jamais dans plantes.db réel et ne contactant aucun capteur.


### 20/10/2026 — Alerte humidité basse
Centre d’alerte : contrôle indépendant du dernier relevé de chaque capteur local actif, sous 20 %, daté de moins de 48 h. Source/date et vérification du substrat explicites en français/anglais ; aucun conseil automatique de volume. Relevés invalides, futurs et antérieurs au dernier arrosage exclus ; archives HA de test non utilisées. Tests sur données fictives ; aucune donnée réelle modifiée.


### 20/10/2026 — Reprise Home Assistant et démo
Correction du blocage après plus de sept jours : cible bornée sans saut de curseur, synchronisation et fenêtre de suivi. Réponses volumineuses subdivisées jusqu’à une minute, seize requêtes maximum par passage ; reprise au dernier enregistrement. Tests dix jours d’absence, sous-fenêtre échouée, budget et accusé perdu. Démo enrichie d’une chronologie fictive et cas zéro/indisponible/valeurs rapprochées. Guide docs/HOME_ASSISTANT_REPRISE_ET_SUIVI.md ; aucune collecte réelle ou modification des mesures du PC.


### 20/10/2026 — Associations et diagnostic Home Assistant
Ajout colonne plante dans les réglages, noms indisponibles signalés. Diagnostic traduit sur liste fermée : accès refusé, débit limité, serveur indisponible, connexion interrompue, association bloquée et historique trop volumineux. Statut HTTP numérique uniquement ; aucune exception, corps ou valeur privée affichés. Progrès partiel conservé et affichage réactualisé après échec. Correction complémentaire du rattrapage manuel après longue absence ; tests interface FR/EN clair/sombre et absence de fuite dans les messages.


### 20/10/2026 — Filtres du suivi connecté
Le choix de quantité recharge sa propre sélection : les états fréquents de luminosité ne masquent plus l’humidité du sol. Ajout filtre par capteur physique et indication quand les 2 000 états affichables sont dépassés. Dates filtrées avant la limite de lecture, y compris bornes sous-seconde et décalages de fuseau. Tests sur archive fictive et interactions réelles du sélecteur de démo en FR/EN clair/sombre ; aucune modification des archives réelles.


### 20/10/2026 — Isolation Home Assistant en démo
Réglages alimentés exclusivement par quatre associations fictives ; aucun chargement de configuration privée ou inventaire réel. Champs de connexion et sauvegarde désactivés, protection directe de load/save_config et commit_history. Rattrapage manuel bloqué avant chargement des identifiants, y compris si un bouton est artificiellement réactivé. Tests de non-lecture/non-écriture avec fichier sentinelle, fonctions privées interdites et interface FR/EN clair/sombre.


### 20/10/2026 — Navigation par plante du suivi connecté
Ajout d’un filtre de plante dans la vue globale et d’une sélection explicite des capteurs sans plante. La liste des capteurs suit la plante choisie, une sélection incompatible est réinitialisée. Depuis une fiche plante, le périmètre reste fixe. Les plantes homonymes sont distinguées par leur identifiant. Tests de navigation FR/EN clair/sombre en petite fenêtre, sans accès à la base réelle.


### 20/10/2026 — Actualisation des associations ouvertes
Après sauvegarde réussie des réglages, notification dédiée aux fenêtres et à la synthèse d’accueil. Les associations et noms de plantes sont relus ; les filtres valides sont conservés et les sélections supprimées réinitialisées. Une fenêtre liée à une plante perd les capteurs qui lui ont été retirés. Configuration relue avant récupération ; en cas d’erreur, les anciens réglages ne sont pas réutilisés. Suppression des liaisons d’événements et minuteurs à la fermeture de la synthèse. Tests de sauvegarde vers deux fenêtres, configuration illisible et minuterie unique sur données fictives.


### 20/10/2026 — Contrôle avant activation Home Assistant
La sauvegarde avec synchronisation cochée exige une connexion renseignée, au moins une mesure, les identités physiques confirmées, un inventaire Gruterra lisible et aucune mesure en doublon ou déjà enregistrée en Bluetooth. Contrôles locaux sans connexion ; refus avant écriture privée. Les préparations incomplètes restent enregistrables avec synchronisation décochée. Tests sur fichiers sentinelles et registre fictif : identité conservée, doublons, ancienne synchronisation active et absence de réseau.


### 20/10/2026 — Disponibilité et récupération du suivi connecté
Colonnes distinctes disponibilité, ancienneté et type d’état : zéro conservé, indisponible/inconnu/conflit explicités, étiquette test conservée en cas de conflit. Une mise à jour d’attributs utilise la date du dernier changement de valeur pour l’ancienneté ; dates futures et états initiaux incertains signalés. Filtres verrouillés pendant récupération et restaurés après réussite/échec. Rappel d’interface annulé à la fermeture sans interrompre l’enregistrement. Tests UI FR/EN clair/sombre et trois scénarios de récupération entièrement simulés.


### 20/10/2026 — Lecture des archives volumineuses
Index de lecture ajoutés transactionnellement au prochain archivage : appareil/quantité/date, contenu par état et bornes de fenêtres. La vue limite les états avant de charger les contenus et évite le filtrage temporel quand aucune borne n’est demandée. Ouverture toujours en lecture seule, compatible avec les anciennes archives. Résultats avant/après identiques, conflits conservés ; rollback des index si la transaction échoue. Mesure sur 6 000 états fictifs, 2 000 affichés, médiane de trois essais : 5.9699 s avant, 0.0287 s après. Aucune archive réelle modifiée pendant cet essai.


### 20/10/2026 — Limite globale avant décodage des archives
La lecture applique la limite à toute la sélection avant de décoder les états, au lieu de charger jusqu’à cette limite pour chaque capteur. Ordre des dates et égalités déterministe conservé, filtres plante/quantité/date inchangés. Tests sur douze capteurs : seuls les contenus affichés sont décodés, archive strictement inchangée. Comparaison avant/après sur vingt capteurs fictifs et 20 000 états, 2 000 affichés : 0.3541 s puis 0.0421 s, médianes de trois essais, résultats complets identiques.


### 20/10/2026 — Préparation de distribution
Contrôle des dépendances sans créer d’archive : sélection Git incomplète, seize modules locaux nécessaires identifiés ; sélection explicite complète sur 245 fichiers. Vérificateur de valeurs signale trois fichiers à relire ; aucune exception modifiée. Protection ajoutée pour les catalogues FR/EN manquants, invalides ou incohérents. Option de fichiers supplémentaires limitée au contrôle, interdite pour créer une archive officielle. Compte rendu docs/CONTROLE_DISTRIBUTION_2026-10-20.md. Test PC sans Python toujours en attente ; aucun manifeste ou numéro de version changé.


### 20/10/2026 — Affichages en échec et longues légendes
Échec de lecture après changement de filtre : anciens états retirés du tableau et du graphique, erreur persistante au redimensionnement, reprise possible au prochain essai. Les valeurs archivées ne sont jamais effacées par ce traitement. Légendes multi-capteurs réparties en colonnes, hauteur adaptée pour conserver au moins 160 px de tracé et retour au format compact avec un seul capteur. Tests UI FR/EN clair/sombre : erreur simulée avec détail privé non affiché, récupération, soixante capteurs fictifs et points toujours sous les légendes. Comparaison physique des capteurs laissée en attente.


### 20/10/2026 — Résultats asynchrones et notification des vues
Module ui_async_result : résultats transmis sur le fil Tk principal, rappel supprimé après résultat ou fermeture d’un aperçu. Une récupération déjà lancée garde un suivi sur la racine pour notifier les vues restantes même si la fenêtre d’origine est fermée. Notifications diffusées depuis toute sous-fenêtre à l’accueil et aux autres fenêtres, y compris imbriquées. La fenêtre d’origine conserve son récapitulatif (notamment une période restant à récupérer). Synthèse d’accueil actualisée après import sans multiplier les minuteurs. Tests de livraison unique, aperçu fermé, récupération après fermeture et exclusion de l’origine ; données fictives uniquement. Ajouter _app/ui_async_result.py à la prochaine sélection de distribution.
