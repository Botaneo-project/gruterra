# Gruterra 0.1.7-dev — préversion du 21 octobre 2026

## Changements importants

- Synchronisation : priorité aux relevés récents et vérification de leur fraîcheur.
- Arrosage : suivi immédiat et à dix minutes ; observation du drainage modifiable après coup dans l’historique. Le suivi différé nécessite le PC allumé et Gruterra ouvert.
- Historique : copie de plusieurs lignes par clic droit ou Ctrl+C, améliorations de lecture et de suivi des capteurs connectés.
- Sauvegardes : prise en compte de la base réellement utilisée, copie SQLite cohérente et vérifications avant finalisation.
- Démo : réglages et caches isolés des données réelles.
- Raspberry : chemins personnalisés repris dans les outils et services.

- Centre d’alertes : suivi contextualisé après arrosage, repères avant/après, qualité des mesures et observations de santé, avec conservation des alertes critiques. Préparation des repères par cycle sans seuil optimal appris.

## Statut

Préversion de test. Partage communautaire désactivé. La publication ne remplace pas automatiquement une installation locale.
L’installateur Windows est non signé et prépare Python et ses dépendances : ce n’est pas un exécutable autonome contenant Python. Le test sur un PC sans Python reste à réaliser.

## English

Test prerelease. Faster fresh-reading synchronization, immediate and ten-minute watering follow-up, editable drainage observations, multi-row copying, reliable active-database backups, isolated demo settings and configurable Raspberry paths. Delayed follow-up requires Gruterra running on an awake PC. Community sharing remains disabled. The unsigned Windows installer prepares Python and dependencies; testing on a computer without Python remains pending.

## Validation

539 tests réussis sur copie isolée. Démo démarrée depuis l’archive extraite, sans réseau ni données privées. L’installation complète sur PC sans Python reste à vérifier.
