# Capteurs Zigbee via Home Assistant — préparation du 15/10/2026

## Architecture retenue

Capteurs Zigbee → clé USB gérée par Home Assistant → entités Home Assistant → Gruterra.

Home Assistant conserve la gestion de la clé, des appairages et de la disponibilité. Gruterra ne prend pas possession du port USB. ZHA ou Zigbee2MQTT restent possibles ; aucune installation Zigbee ou MQTT n'est effectuée par cette préparation. La collecte Bluetooth existante reste indépendante.

Matériel annoncé : deux Arteco 4-en-1, un Gleco de luminosité, un FOXONEER de luminosité, une clé Haozee. Les modèles techniques, le chipset et les capacités effectivement exposées restent à vérifier après réception.

## Ce qui est préparé

`_app/home_assistant_sensors.py` accepte des états Home Assistant fournis par l'appelant, sans réseau. L'association explicite indique instance, entité, appareil, modèle et grandeur. Température, humidité du sol, humidité de l'air et éclairement restent distincts. Les unités sont contrôlées ; aucune calibration ou conversion entre modèles n'est inventée.

Les états `unavailable` et `unknown` ne deviennent jamais zéro. Une vraie valeur zéro est conservée. La date de réception et `last_updated` sont séparées. Une date d'état ancienne, future ou absente est signalée. `last_updated` est une date d'état Home Assistant, pas une preuve de date de mesure physique ; `measured_at` reste donc nul et les données sont exclues de l'historique des plantes à ce stade.

Le document d'état reçu est conservé comme donnée source Home Assistant ; ce n'est pas une trame Zigbee brute. La calibration est inconnue. Une relecture du même état ne crée pas de nouveau relevé ; un contenu modifié est conservé distinctement. L'archive SQLite doit être choisie explicitement par l'appelant : aucun chemin vers la base utilisateur n'est configuré. Toute la sélection est validée avant écriture.

## Limites et suite

- Préparation hors ligne uniquement, sans connexion, abonnement MQTT, jeton ni collecte activée.
- Pas encore de nouveau bouton ou d'affichage dans l'application.
- Le simple état actuel ne permet pas de rattraper une nuit entière : prévoir l'historique Home Assistant ou une collecte continue avec file persistante sur le Pi.
- Après appairage : relever les identifiants d'entités, modèles, unités, fréquence et date réelle disponible par appareil ; ne pas déduire humidité de l'air/du sol du seul symbole `%`.
- Définir un accès local Home Assistant et sa configuration privée, sans incorporer un jeton aux guides ou exemples publics.
- Prévoir les tests de coupure, reprise, changement d'entité et de modèle avant l'intégration à l'historique et aux analyses.
- La fraîcheur de l'état est une indication technique ; elle ne garantit pas un nouveau relevé radio.

Références officielles : [API REST](https://developers.home-assistant.io/docs/api/rest/), [objets d'état et horodatages](https://www.home-assistant.io/docs/configuration/state_object/).


## Lecture REST préparée — 15/10/2026

Le module `_app/home_assistant_client.py` prépare uniquement la lecture des entités choisies via `GET /api/states/<entity_id>`. Aucun inventaire global, commande de service, appairage ou écriture vers Home Assistant. Il n'est pas encore appelé par l'interface ni par un timer.

Un exemple vide est fourni dans `docs/examples/home_assistant.local.json.example`. La future configuration effective devra rester dans `_config/home_assistant.local.json`, déjà exclu de Git. Ne pas mettre le vrai jeton dans le modèle public. `enabled` reste faux par défaut ; aucun fichier privé n'a été créé ou rempli durant cette étape.

Champs : version de configuration 1, activation explicite, URL de base, jeton local, identifiant stable de l'instance, seuil d'ancienneté d'état en secondes et liste d'associations d'entités. Chaque association possède `entity_id`, `device_id`, `model`, `metric`. Les grandeurs autorisées sont `soil_moisture`, `air_humidity`, `temperature`, `illuminance`. Les vraies entités seront connues après appairage ; ne pas les deviner.

Les redirections sont refusées afin de ne pas envoyer l'accès vers un autre hôte. HTTPS conserve la validation normale du certificat. HTTP est limité à une IP privée explicitement choisie ou localhost ; il reste en clair sur ce réseau et HTTPS est préférable lorsqu'il est disponible. Aucune requête automatique par proxy d'environnement. Limite de 64 Kio par état, délai de connexion 5 s et lecture 15 s ; 100 entités au maximum.

Les erreurs renvoient un code fixe et, si disponible, le statut HTTP. Ni jeton, ni corps de réponse, ni exception brute ne sont inclus au diagnostic. Pas de boucle de nouvelle tentative sur 401/403/429. Si une entité échoue, aucun instantané partiel n'est annoncé comme complet.

La lecture d'un état courant ne rattrape pas les mesures manquées : historique HA ou collecteur persistant sur Pi encore à préparer. Ces données ne sont pas injectées dans `plantes.db`. Les états inconnus, anciens et indisponibles sont transmis comme tels.


## Écran de préparation FR/EN — 15/10/2026

Après relance de Gruterra : Paramètres → Capteurs Home Assistant. Adresse et jeton peuvent rester vides tant que le matériel n'est pas disponible. Le jeton est masqué par défaut. Ajouter une entité ouvre un formulaire pour l'entité `sensor.nom`, l'identifiant local stable de l'appareil, le modèle et la grandeur. Plusieurs entités du même appareil doivent reprendre le même identifiant d'appareil.

Valider une association modifie la liste de la fenêtre ; « Enregistrer la préparation » écrit ensuite le fichier privé. La zone de validation reste fixe sous la liste défilante. Enregistrer force `enabled: false` pendant cette phase de préparation, préserve l'identité existante de l'instance et ne contacte jamais Home Assistant. Un brouillon vide est accepté. Une configuration illisible n'est pas écrasée. La démo ne collecte rien : cet écran ne propose aucune activation ni import.

Les textes sont dans les deux catalogues JSON, sans doublon de texte visible dans le code. Aucun fichier privé n'est créé à la simple ouverture. Les entités réelles, le rattrapage historique et l'intégration dans les vues des plantes restent à valider.


## Protection du jeton Windows — 15/10/2026

L'enregistrement du jeton en clair est remplacé par Windows DPAPI lié au compte courant (`CryptProtectData`, sans portée machine). Aucun mot de passe supplémentaire. Le fichier privé conserve `secret_storage: windows_dpapi_current_user_v1` et `access_token_protected` (blob chiffré en base64), sans champ `access_token` en clair. Le jeton est déchiffré seulement en mémoire. Aucun repli en clair si la protection échoue.

Un ancien fichier contenant `access_token` est migré atomiquement lors de sa lecture, sans créer de copie en clair. Les autres paramètres et l'identité de l'instance restent conservés. Le modèle public vide conserve des champs de saisie vides ; les fichiers effectifs générés par l'application utilisent le format protégé.

Si un blob est corrompu ou illisible après changement de compte/PC ou réinstallation, le formulaire indique de recréer un jeton dans Home Assistant. Un jeton de remplacement peut être enregistré sans changer l'identité locale ni les associations. Une sauvegarde vide ne supprime pas silencieusement le jeton illisible. Pour supprimer volontairement un jeton lisible, effacer le champ et enregistrer ; la révocation du jeton dans Home Assistant reste une action distincte.

Cette protection empêche la lecture du jeton par simple copie du JSON. Elle ne protège pas contre un logiciel agissant sous la même session Windows ni contre un administrateur ayant compromis la session. Elle ne rend pas un jeton administrateur limité à la lecture. Le fichier reste privé, exclu de Git et des journaux. Préférer un utilisateur Home Assistant dédié non administrateur et les droits minimaux compatibles à vérifier côté Home Assistant. Utiliser HTTPS lorsqu'il est disponible ; le chiffrement au repos ne chiffre pas une connexion HTTP.

Pas de promesse de portabilité du blob dans une sauvegarde après formatage : prévoir de recréer le jeton Home Assistant sur le nouveau poste. Sur Linux/Pi, cette implémentation refuse de stocker un nouveau secret plutôt que de le laisser en clair ; un stockage adapté sera à définir si ce connecteur y est déployé.


## Historique et unicité de source — 15/10/2026

L'identité d'un appareil physique doit être vérifiée indépendamment de son nom Home Assistant. Un Mi Flora déjà enregistré comme capteur Bluetooth ne doit pas être réimporté depuis Home Assistant. Le module `sensor_source_policy.py` normalise les adresses BLE et IEEE Zigbee et applique un registre local explicite de source de référence : `miflora_ble` ou `home_assistant`.

Les adresses BLE déjà enregistrées dans Gruterra prennent priorité sur une attribution concurrente à Home Assistant. Plusieurs grandeurs d'un même appareil restent possibles ; deux entités candidates pour le même appareil et la même grandeur sont refusées. Deux appareils distincts mesurant la même valeur restent distincts : aucune fusion fondée sur une ressemblance de nom, de valeur ou d'heure.

Le module de lecture `home_assistant_history.py` exige explicitement le registre et la liste des appareils BLE existants. Il refuse la lecture si `hardware_id` n'est pas confirmé dans les associations, avant tout appel réseau. Cette liste devra être lue dans la base réelle au moment du futur raccordement ; aucun registre n'est prérempli par déduction des noms. Le formulaire courant n'expose pas encore ce contrôle d'identité physique : les associations saisies restent des brouillons et ne suffisent pas à autoriser un import.

Lecture préparée de `/api/history/period/<start>` avec filtre sur les seules entités autorisées et fin explicite. Pas de réponse minimale pour conserver unités et identité. Fenêtre maximale de six heures, réponse limitée à 2 Mio et 10 000 états ; dépassement ou état incohérent fait échouer le lot entier. Aucun curseur n'est avancé, aucune requête automatique ni écriture dans l'historique des plantes.

Les états antérieurs au début de fenêtre, que HA peut fournir comme contexte initial, ne deviennent pas de nouveaux relevés. Fin de fenêtre exclue, début inclus. Rejeu d'un état identique : même identifiant et dédoublonnage. Deux valeurs identiques à des dates d'état différentes restent des états distincts. Date HA toujours distincte d'une date physique ; le module ne confirme pas une nouvelle mesure radio. Les réponses vides ne prouvent ni absence de mesure physique, ni conservation complète côté Recorder.

Reste à préparer avant activation : vérification des vrais identifiants, alimentation du registre depuis la base, lecture de conservation Recorder, archivage transactionnel et curseur de reprise après confirmation durable, traitement des révisions, écran d'association physique et test réel après appairage. Aucun historique réel Home Assistant n'a été lu durant cette préparation.


## Raccordement du registre et aperçu manuel — 15/10/2026

La liste Bluetooth est maintenant lue en mode SQLite strictement lecture seule depuis le chemin de base choisi par l'application. Aucun schéma ni capteur n'est créé lors du contrôle. Toutes les adresses enregistrées, y compris historiques, sont conservativement protégées ; une migration de source nécessitera une procédure distincte, pas un simple renommage.

Dans Paramètres → Capteurs Home Assistant, chaque association affiche son autorisation. Le formulaire permet de renseigner `ble:` + MAC ou `zigbee:` + adresse IEEE, puis de confirmer explicitement l'identité matérielle vérifiée dans Home Assistant et la source souhaitée. L'adresse n'est pas découverte automatiquement à partir du nom. Une identité inconnue reste en préparation. Deux entités du même appareil et de la même grandeur sont bloquées ; des grandeurs distinctes du même appareil restent autorisables.

Le bouton « Aperçu en lecture seule » relit le registre courant avant chaque tentative. Base absente, illisible, identité non confirmée ou conflit : aucune requête aux capteurs. L'aperçu valide porte sur toutes les associations de la liste ; pour tester une seule entité, préparer une liste contenant seulement celle-ci. Une base indisponible bloque le contrôle au lieu de faire croire qu'aucun doublon n'existe.

L'aperçu est un GET explicite des seuls états courants sélectionnés, exécuté dans un fil de travail pour ne pas bloquer la fenêtre. Il n'active pas la collecte. Les réponses sont seulement affichées (valeur, unité, date d'état UTC, disponibilité et ancienneté) : aucun archivage local et aucune écriture dans l'historique des plantes. Les paramètres en cours de saisie peuvent être utilisés pour cet aperçu sans être sauvegardés ; une première sauvegarde est nécessaire pour créer l'identité stable de la connexion. L'identifiant est conservé lors des sauvegardes suivantes.

Le journal et les exemples publics ne contiennent aucune adresse matérielle réelle. La correspondance physique devra être vérifiée après réception du matériel ; l'import réel et le rattrapage durable avec curseur restent désactivés et à raccorder ultérieurement. Aucun appel aux états Home Assistant réels n'a été nécessaire pour les tests de cette étape.


## Archive transactionnelle et reprise — 15/10/2026

`home_assistant_archive.py` prépare la conservation des réponses historiques dans un fichier SQLite séparé, fourni explicitement par l'appelant. Aucun chemin de production n'est créé par défaut. Le chemin de la base des plantes est refusé, comme tout fichier comportant des tables `plantes`, `capteurs` ou `mesures`. L'interface et les timers n'appellent pas cet archivage : aucune activation réelle à ce stade.

Chaque lot est entièrement revalidé à partir des états source avant écriture. Les droits de source sont revérifiés dans la liste Bluetooth courante. La transaction SQLite (`BEGIN IMMEDIATE`, `synchronous=FULL`) conserve ensemble les états, les révisions, le reçu local de fenêtre et la progression. Toute erreur pendant l'écriture annule l'ensemble de cette transaction. Après perte de la réponse au succès, le même lot peut être rejoué sans nouvelle entrée.

Les faits d'état sont regroupés par identité physique vérifiée, grandeur et date HA en UTC, indépendamment du nom de l'entité. Un renommage d'entité qui transmet le même fait ne double pas ce fait ; sa provenance reste conservée séparément. `0` et `0.0`, `lx` et `lux` sont équivalents pour cette détection, mais l'état source original reste intact. Une valeur différente à la même date constitue une révision conservée, jamais un remplacement silencieux. Ces états ne sont toujours pas assimilés à des mesures physiques confirmées et ne sont pas injectés dans les analyses des plantes.

La progression est propre à l'instance et à la sélection vérifiée d'entités/appareils. Un trou entre deux fenêtres est refusé ; une fenêtre rejouée ou chevauchante ne fait jamais reculer la progression. Changer la sélection crée un nouveau contexte de progression et impose de choisir explicitement le début de rattrapage. Un retour historique vide peut être consigné comme réponse reçue : la progression prouve uniquement que la réponse HA a été archivée, pas que tous les relevés physiques existent dans Recorder.

Restent à raccorder : orchestration de plusieurs fenêtres, choix de début de rattrapage, contrôle de la conservation Recorder et écran de validation avant activation. Une reprise automatique ne doit pas prétendre récupérer ce que Home Assistant n'a pas conservé. Aucun état réel n'a été récupéré ou archivé pendant les tests de cette étape.


## Parcours manuel de récupération raccordé — 15/10/2026

Après relance : Paramètres → Capteurs Home Assistant → Récupérer l'historique Home Assistant. Enregistrer les associations avant d'ouvrir ce parcours. Choisir 24 heures ou sept jours, puis « Préparer le récapitulatif ». Cette première action contrôle la configuration, les identités et la progression locale sans requête réseau ni création d'archive.

Le récapitulatif affiche les fenêtres UTC et la destination séparée. « Confirmer l'archivage séparé » autorise seulement cette récupération manuelle : pas de timer ni activation persistante. Au maximum quatre fenêtres de six heures par confirmation. Si une période reste à couvrir, préparer un nouveau récapitulatif. La configuration protégée existante et ses associations enregistrées sont utilisées ; les modifications non enregistrées dans la fenêtre principale ne sont pas reprises implicitement.

L'orchestrateur `home_assistant_catchup.py` vérifie que le plan et la progression sont toujours identiques au récapitulatif, réévalue le registre Bluetooth avant chaque lecture puis archive avant de poursuivre. Une erreur HTTP, de validation ou d'écriture interrompt l'opération, sans nouvelles tentatives en boucle. Les fenêtres déjà validées sont conservées. Une réponse perdue après archivage se reprend à partir de la progression durable. La démo (`BOTANEO_DEMO=1`) est refusée avant tout réseau ou archive.

Fichier effectif, créé seulement après confirmation : `_app/data/home_assistant_history.sqlite3`, exclu de Git. Il contient des états et métadonnées techniques privés, aucun jeton. Les données restent hors de `plantes.db` et des analyses des plantes. L'état de collecte automatique enregistré reste désactivé ; le consentement manuel à cette opération ne le modifie pas.

Une réponse HA vide reste une réponse archivée, pas une certification de couverture. La conservation Recorder n'est pas vérifiée automatiquement. Une reprise ancienne de plus de sept jours est bloquée pour examen plutôt qu'abandonnée silencieusement. Une identité matérielle fausse saisie manuellement ne peut pas être corrigée par simple comparaison des valeurs : les adresses doivent être réellement vérifiées dans Home Assistant avant utilisation.

Préparation logicielle validée avec réponses simulées. Prochain contrôle matériel : appairer un seul capteur Zigbee dans Home Assistant, relever son adresse IEEE et ses vraies entités/unités, confirmer son association, faire l'aperçu puis un rattrapage manuel court. La compatibilité exacte des appareils commandés reste à confirmer. Aucun rattrapage réel n'a été lancé durant cette préparation.


## Stabilisation démo — 16/10/2026

Les fonctions de lecture d’état, de configuration protégée et d’historique refusent maintenant explicitement `BOTANEO_DEMO=1` avant tout réseau ou accès au jeton. Le rattrapage était déjà bloqué ; les autres points d’entrée le sont aussi.

Dans la démo, le bouton d’aperçu devient « Voir un exemple fictif ». Il affiche quatre états générés en mémoire : humidité du sol, température, luminosité zéro et capteur d’humidité de l’air indisponible. Aucun paramètre ni jeton requis, aucun archivage, aucune connexion. Le titre et le texte précisent que l’exemple est fictif. Le fonctionnement réel ne change pas.
