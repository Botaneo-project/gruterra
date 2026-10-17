# Suivi local des contributions — préparation du 10/10/2026

Dans Paramètres → Contributions et confidentialité → Suivi local des contributions, la consultation affiche les demandes connues du poste. Aucun partage ni import de reçu n’est proposé. Ouvrir une liste vide ne crée pas de clé ni de suivi.

Le stockage privé `_config/contribution_suivi.sqlite3` conserve identifiant de demande, octets exacts, empreinte et reçu initial. Après une coupure, la future reprise devra utiliser la même demande et les mêmes octets avec un nouveau défi. Aucun identifiant ne doit être régénéré automatiquement à cause d’une réponse incohérente.

Les états distinguent préparation, attente, réception historique, retrait en attente, retrait actif confirmé, échéance atteinte et réponse à vérifier. Une échéance dépassée sur l’horloge PC n’est pas une confirmation de purge. Un retrait actif n’atteste pas la disparition des sauvegardes serveur. Un ancien reçu accepted n’atteste pas la présence actuelle du contenu.

Le code accepte uniquement les reçus du profil privé de test actuel. `retention_until=null` ne signifie pas conservation illimitée. Les futurs reçus publics, la durée commune, la politique acceptée et le lien signé à cette politique restent à négocier ; aucun ajout à l’enveloppe V2 actuelle.

La couverture locale d’un retrait global est figée avant tentative, avec blocage des opérations concurrentes de la même identité. Sa reprise ne retire pas les futures contributions. Un suivi perdu ne peut pas reconstruire l’état du serveur, qui n’offre pas encore de consultation générale.

Le suivi est inclus dans la sauvegarde complète privée, exclu des exports partageables. Il contient des données de culture locales ; une demande de retrait communautaire ne supprime pas automatiquement les données personnelles du poste.

Le validateur métier V2 est maintenant appliqué avant la création de chaque demande de contribution. Les champs privés, références invalides, bornes, précision et horaires incohérents sont refusés sans enregistrer de demande. Les octets valides restent inchangés pour la signature.

Avant raccordement : brancher l’aperçu, recueillir le choix utilisateur, vérifier HTTPS et les erreurs réseau, puis valider durée/politique/retrait côté site. Aucun endpoint ni jeton de test utilisé par ce lot.

## Vérifications supplémentaires

Un retrait seulement préparé reste « préparé » jusqu’à sa tentative. Les tests locaux vérifient l’isolement entre deux identités, deux tentatives concurrentes sous une même identité (une seule passe en attente), et la récupération des octets et reçus après extraction du suivi depuis une sauvegarde complète. Le suivi est absent de l’export de données. Ces tests ne constituent pas des tests de concurrence du serveur ni une validation de sa suppression.

## Profil privé de cycle de vie

Le profil `lifecycle-test-60s` est accepté uniquement après sélection explicite lors de la préparation locale. Le reçu doit annoncer cette politique et exactement 60 secondes entre réception et échéance UTC. Les anciennes demandes restent `private-test-only` après migration sans modification de leurs octets. Le profil public reste refusé.

Les réponses HTTP 410 `contribution_expired` et `contribution_withdrawn` terminent la demande sans recréer un identifiant, sans écraser son reçu initial et sans prouver la disparition des sauvegardes. Une échéance locale reste distincte d’une expiration signalée par le serveur. Ces fonctions attendent un futur transport HTTPS contrôlé, ne sont pas exposées comme import de réponse arbitraire et ne réalisent aucun appel réseau.
