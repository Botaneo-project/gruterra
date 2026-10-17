# AROME-PI — prévisions locales

Décision du 12/10/2026 : consulter toutes les 15 minutes aux quarts d’heure + 1 seconde (:00:01, :15:01, :30:01, :45:01). Utiliser un calendrier fixe, pas une attente de 901 secondes après chaque passage : aucun décalage cumulatif.

Le passage interroge les prévisions disponibles ; il ne garantit pas qu’un nouveau calcul du modèle soit publié à chaque passage. Une seconde de marge ne garantit pas la disponibilité des données : conserver l’heure du calcul, l’heure de consultation et les échéances réelles, et signaler les données anciennes.

Avant activation : valider un téléchargement local depuis le calcul récent, le champ de précipitations, les unités et les périodes de cumul. Ne pas additionner des cumuls ou mélanger plusieurs calculs. Les échéances passées ne deviennent pas des observations.

Conserver les prévisions dans un stockage distinct des observations pluie et de plantes.db. Garder le dernier résultat valide en cas d’échec, avec sa date ; pas de prévision manquante transformée en zéro.

Le timer reste non activé. L’hébergement du collecteur (PC ou Pi), l’accès durable AROME-PI, le renouvellement et les quotas restent à valider. Aucun jeton transféré au Raspberry.

Préparation applicative : arome_catalogue.py sélectionne le dernier calcul non futur encore exploitable, contrôle l’identité du champ, l’unité et les échéances. Calendrier fixe testé à minuit. Les métadonnées seules ne prouvent pas la sémantique des cumuls du GRIB : vérifier les bornes d’accumulation dans un téléchargement local avant affichage de quantités. Aucune prévision locale ni génération OAuth automatique validée à ce stade.

Renouvellement OAuth2 préparé en simulation : profil partagé sous verrou interprocessus, réutilisation du jeton valide, expiration issue de expires_in, sauvegarde atomique, diagnostics expurgés et absence de boucle de renouvellement. Aucun appel OAuth réel effectué. Si observations et AROME utilisent la même application, partager un seul gestionnaire/profil pour éviter des générations concurrentes ; vérifier les droits de cette application avant branchement. Les jetons manuels existants restent inchangés.
