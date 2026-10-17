# Contrat météo PC/Raspberry — proposition v1

11/10/2026. Proposition applicative à confirmer côté Raspberry. Aucun timer ou transfert OAuth activé. Identifiants de l’exemple entièrement fictifs.

## Transport et versions

SSH authentifié via les paramètres existants ; opérations dédiées weather_export et weather_ack. Ne pas modifier le protocole Mi Flora.
JSON UTF-8 sans BOM. protocol = gruterra-weather-sync ; protocol_version = 1 ; observation_schema_version = 1 pour les lots. Versions inconnues refusées, sans accusé.
device_id : identité existante du Pi, comparée à la configuration PC attendue ; pas une preuve d’authentification à elle seule.
Limites : 500 lignes et 1 000 000 octets par message ; pas de chaînes de plus de 256 caractères hors limites précisées ci-dessous. Rejeter les clés JSON répétées, nombres non finis et champs inconnus à cette version. pending est un entier >= len(rows), nombre total de révisions en attente avant cet export.

## Observation : champs exacts

Tous les champs suivants sont présents. null est autorisé seulement là où précisé.

| Champ | Type et règles |
|---|---|
| source | netatmo_public ou netatmo_personal |
| station_id | chaîne non vide, identifiant exact de la source |
| module_id | chaîne non vide ou null si réellement indisponible |
| api_field | nom exact du champ API, chaîne non vide |
| metric | rainfall, temperature, relative_humidity, air_pressure, wind_speed, wind_gust, wind_direction ou gust_direction |
| value | chaîne décimale canonique ou null explicitement reçu ; maximum 64 caractères |
| unit | mm, degC, percent, hPa, km/h ou degree selon la métrique |
| source_time | UTC YYYY-MM-DDTHH:MM:SSZ ou null ; pas de date de récupération substituée |
| time_precision | second, minute ou unknown ; une précision minute exige secondes 00 ; unknown exige source_time null |
| period | objet exact kind/duration_seconds/start/end décrit ci-dessous |
| temporal_quality | source_timestamp ou missing_timestamp, cohérent avec source_time |
| provenance | netatmo:getpublicdata ou netatmo:getstationsdata, cohérent avec source |

value : pas d’exposant, signe +, zéro négatif ou zéros superflus. Exemples : 0, 2.4, -1.5. Zéro valide ; null distinct d’un champ API absent (ce dernier ne produit aucune observation). Ne pas arrondir la précision source. Pluie >= 0 ; humidité 0..100 ; direction 0..360 ; pression et vitesses >= 0. Température peut être négative.
Unités : rainfall/mm, temperature/degC, relative_humidity/percent, air_pressure/hPa, wind_speed et wind_gust/km/h, directions/degree. Toute conversion est explicite et identique sur PC/Pi ; aucun mélange de données intérieures et extérieures par défaut.

period : kind = rolling, calendar_day, instant ou unknown. duration_seconds entier positif ou null. rolling exige une durée connue ; instant et unknown exigent durée null. Pour calendar_day, ne pas supposer 86400 secondes lors du changement d’heure. start et end sont des UTC ou null : les deux sont renseignés ensemble seulement si les bornes réelles sont connues, start < end. Si durée et bornes sont fournies, elles doivent concorder.
Pour rain_60min : rolling, 3600 secondes. Pour rain_24h : rolling, 86400 secondes seulement après confirmation de la définition de cet endpoint. Ne pas appliquer cette règle automatiquement à sum_rain_24 des données personnelles : définition à vérifier avant activation. Une définition incertaine utilise unknown et interdit toute sommation.

## Enveloppe de chaque ligne

observation_id, revision_hash, observation, retrieved_at : champs obligatoires.
retrieved_at : UTC à la seconde de récupération, hors identité et hors empreinte de révision ; deux récupérations d’une même mesure restent un doublon.

Canonicalisation v1 : objets triés par clés, tableaux dans leur ordre, JSON compact sans espaces, Unicode littéral UTF-8, pas de slash échappé. Nombres uniquement entiers dans les objets hachés ; valeurs de mesure en chaînes décimales pour éviter les divergences de sérialisation flottante.

Si source_time est connu : observation_id = w1_ + SHA-256 hexadécimal minuscule du JSON canonique composé exactement de source, station_id, module_id, api_field, metric, source_time, time_precision et period.
Si source_time est inconnu : observation_id = wu1_ + UUID v4 généré une fois à la collecte et conservé par le producteur. Le rejeu conserve cet UUID ; aucune déduplication PC/Pi entre acquisitions distinctes non datées n’est prétendue possible.
revision_hash = SHA-256 hexadécimal minuscule du JSON canonique de l’objet observation complet. Même identité et même empreinte : doublon ; même identité et empreinte différente : révision conservée. Ne pas confondre ordre de réception et chronologie certaine des corrections.
Si module_id est null, l’identité ne permet pas de distinguer deux modules anonymes ayant le même champ et la même date : le collecteur doit alors conserver les observations séparément avec une identité wu1_ stable, signaler l’ambiguïté et ne pas les agréger.

## Export, import et accusé

weather_export : premières révisions non confirmées, ordre stable de stockage ; aucune suppression. Si pending > len(rows), le PC continue par lots après accusé. Pas de curseur fondé sur la date, car des relevés peuvent être corrigés ou non datés.
Le PC valide l’intégralité du lot et les empreintes avant transaction. Une erreur annule le lot complet et interdit l’accusé. Les doublons déjà conservés peuvent être accusés. Les observations non datées sont conservées à part, jamais affichées comme fraîches.
weather_ack : protocol/protocol_version/device_id/rows ; chaque ligne contient observation_id/revision_hash. Le Pi vérifie toutes les correspondances puis confirme atomiquement. Un même accusé répété réussit sans effet supplémentaire. Réponse : protocol/protocol_version/device_id/confirmed, confirmed égal au nombre de couples distincts demandés. Doublons dans un accusé refusés. Un accusé ne supprime rien et ne confirme aucune autre révision.
Accusé perdu : même export rejoué, import PC sans doublon puis nouvel accusé. Les empreintes contrôlent la cohérence ; SSH apporte l’authentification du transport.

## À confirmer avant de marquer l’étape terminée

- Accord Raspberry sur champs, limites, canonicalisation, cas non datés/modules inconnus et accusés idempotents.
- Vecteurs communs d’empreintes et tests de rejeu/révisions.
- Sémantique des cumuls publics/personnels et sélection des modules extérieurs.
- Stratégie d’affichage des révisions lorsque l’ordre source est inconnu.

Le contrat ne règle pas encore la propriété OAuth, les quotas, l’activation du timer ou la sauvegarde ; ce sont les étapes suivantes du plan.

## Clarifications normatives — priorité et périodes enrichies

Ces règles priment sur toute formulation précédente de cette proposition :

1. Si le module OU la date source est inconnu, utiliser wu1_ + UUID v4 stable à la collecte, même avec une date connue. Ne jamais reconstruire cet UUID à l’import. Deux acquisitions PC/Pi ambiguës ne sont pas automatiquement fusionnées.
2. Ajouter à chaque observation le champ obligatoire supersedes : null par défaut, ou objet observation_id/revision_hash désignant exactement l’ancienne observation lors d’une précision ultérieure de période. Ce champ est inclus dans revision_hash, exclu de l’identité métier. L’enrichissement des bornes crée une nouvelle identité ; les deux versions sont conservées mais une seule peut participer aux analyses.
3. L’importeur futur doit résoudre supersedes transactionnellement : même source/station/module/champ/métrique/date/valeur/unité et seules période/provenance de correction autorisées ; pas d’auto-référence, cycle ou remplacement divergent. Tant que le prédécesseur exact manque ou que la filiation est conflictuelle, conserver la ligne en attente de résolution et l’exclure des agrégations. Ne jamais compter simultanément le prédécesseur et son successeur résolu. Le validateur de format ne prouve pas cette résolution : elle exige le stockage et ses tests.
4. Limiter le lot à 500 lignes ET 1 000 000 octets UTF-8 réellement transmis. Réduire le nombre de lignes si nécessaire. Avec pending > 0, un lot vide est interdit ; une ligne trop grande déclenche weather_row_exceeds_batch_limit et arrête le passage au lieu de boucler.

Le fichier _app/weather_protocol.py est la source partagée à déployer à l’identique sur le Pi ; pas de copie indépendante à maintenir. Il valide les formats, identités et empreintes et construit des lots bornés. Aucun accès réseau, OAuth ou stockage n’est effectué.
Les essais d’accusé perdu et de rejeu portent ici sur le contrat ; la durabilité, l’idempotence du stockage et la résolution supersedes devront être testées à l’étape importeur/exporteur avant activation.
