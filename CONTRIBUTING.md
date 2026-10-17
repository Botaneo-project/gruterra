# Développement de Gruterra


## Règle permanente : faire évoluer la démo avec les fonctionnalités

Décision du 15/10/2026 : pour chaque nouvelle fonctionnalité ou modification visible, vérifier et mettre à jour la démonstration dans le même travail, avant de considérer la fonctionnalité terminée.

- Utiliser les mêmes écrans et composants que l’application réelle pour éviter une démo obsolète.
- Ajouter ou adapter des données entièrement fictives pour montrer le parcours normal et les cas utiles : absence de données, zéro, interruption ou erreur, selon la fonctionnalité.
- Vérifier le parcours en français et en anglais, avec les thèmes clair/sombre et une fenêtre réduite lorsque l’interface est concernée.
- Garder bases, paramètres, horaires et identités de démonstration isolés de l’installation réelle. Ne copier aucun secret ou donnée personnelle.
- Ne pas déclencher de collecte réelle, commande matérielle ou contribution communautaire depuis la démo ; fournir une simulation explicite si nécessaire.
- Préserver les essais existants : ne pas régénérer automatiquement la base à chaque lancement. Prévoir une sauvegarde avant tout rafraîchissement d’une démo locale existante.
- Mettre à jour le tutoriel et la to-do. Si une fonctionnalité ne peut pas être représentée en démo, expliquer la limite et noter la tâche restante.

La mise à jour locale de la démo n’entraîne pas automatiquement la publication d’une release GitHub.


## Avant de préparer une archive téléchargeable

Exécuter `python -X utf8 -B prepare_release.py --check-files` avant construction : un import local absent ou un chemin privé bloque la sortie. Ce contrôle fonctionne sans créer d’archive et sans exiger un arbre propre, pour permettre la revue avant commit. Il ne remplace pas la relecture des secrets, la sélection explicite des fichiers ni les tests après extraction. Ne jamais utiliser `--allow-dirty` pour contourner des fichiers manquants. Voir `docs/PREPARATION_ARCHIVE_CONTROLES.md`.


## Vérifier la démo depuis une extraction

Avant diffusion, vérifier aussi les nouveaux écrans depuis une copie extraite sans accès aux dossiers privés du développeur. Ne pas confondre un test avec les bibliothèques déjà installées et un essai d’installation complète sur PC vierge. Un ZIP candidat de contrôle doit être identifié comme non officiel et ne doit pas modifier le manifeste de mise à jour.
