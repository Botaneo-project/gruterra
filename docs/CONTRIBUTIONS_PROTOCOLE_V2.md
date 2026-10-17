# Préparation locale du protocole signé V2

10/10/2026 — code de développement, partage désactivé.

`contribution_identite.py` gère l’identité privée. `contribution_protocole.py` construit le message et l’enveloppe sans accès réseau. Aucun jeton privé de test serveur ne doit être distribué avec l’application.

Le message ASCII signé contient neuf lignes séparées par LF, sans saut de ligne final :

1. GRUTERRA-SIGNED-REQUEST-V2
2. https://api.gruterra.fr
3. POST
4. /v2/contributions ou /v2/withdrawals
5. identifiant ed25519: + SHA-256 des 32 octets publics
6. request_id UUID v4 canonique minuscule
7. challenge_id UUID v4 canonique minuscule
8. nonce de 32 octets en base64 standard canonique avec padding
9. SHA-256 hexadécimal minuscule des octets exacts du contenu

L’enveloppe contient exclusivement protocol_version=2, contributor_id, public_key, request_id, challenge_id, payload_b64 et signature. Le nonce appartient au défi serveur, pas à l’enveloppe. L’identifiant et la clé publique sont contrôlés avant signature. La clé privée reste locale.

Ce protocole est spécifique à Gruterra, avec signature Ed25519 ; il ne doit pas être présenté comme RFC 9421. Le contenu est sérialisé une fois ; aucune resérialisation avant l’empreinte ou lors d’une reprise. La validation métier du contenu et l’accord utilisateur restent à brancher avant toute utilisation réseau.

Une reprise conserve request_id et les mêmes octets mais obtient un nouveau défi et une nouvelle signature. La fonction locale peut refuser un défi expiré selon l’horloge PC ; seul le serveur garantit sa durée réelle, son rattachement à l’identité/opération et sa consommation unique atomique.

Tests locaux : le vecteur public utilisé par le diagnostic PHP est conservé dans tests/fixtures/contribution_signature_v2.json, sans clé privée. Python reconstruit le même message octet par octet et vérifie sa signature. Les variantes de contenu, chemin, défi et saut de ligne sont refusées. Cela ne remplace pas une exécution du nouveau client applicatif sur PHP ni les tests serveur de concurrence/rejeu.

À terminer : client réseau désactivable, consentement et aperçu, stockage durable des requêtes et reçus, tests entre identités et concurrence côté serveur, règles de conservation/retrait/anti-abus. La réception publique reste fermée.
