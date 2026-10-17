# Vérifier la récupération des bases du Raspberry

Le contrôle `python3 ~/botaneo/collector/check_backup_restore.py` utilise les dernières sauvegardes quotidiennes capteurs et météo. Il travaille uniquement sur des copies temporaires, supprimées en fin de contrôle. Il ne remplace aucune base active et ne déclenche aucune collecte.

Il vérifie les empreintes, l’intégrité SQLite, les nombres de lignes, la lecture par l’interface actuelle et la possibilité d’écrire une transaction puis de l’annuler. Il affiche uniquement un résultat technique et des nombres de lignes, sans relevés détaillés ni identifiants d’accès. Un résultat en erreur nécessite une investigation ; ne pas écraser la base active pour essayer.

Contrôle réel réussi le 17 octobre 2026 sur les deux sauvegardes du jour : 184 mesures ponctuelles, 805 historiques capteurs, 723 observations météo.

Il s’agit d’un essai de récupération des données, pas d’une restauration complète du Raspberry. Les sauvegardes ne contiennent pas les données arrivées après leur création. La configuration privée et les accès doivent être récupérés séparément ; ne jamais les publier dans Git. Une restauration réelle doit conserver une copie des bases actives, interrompre les services qui écrivent, vérifier les fichiers récupérés puis contrôler le redémarrage et la synchronisation. Aucune restauration réelle n’a été effectuée lors de cet essai.
