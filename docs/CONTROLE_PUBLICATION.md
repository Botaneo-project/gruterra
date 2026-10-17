# Contrôle des données privées avant GitHub

Le contrôle distingue les noms de champs des valeurs. Exemple de modèle public accepté :

```json
{"access_token": "", "refresh_token": "", "client_secret": ""}
```

Un nom dans une traduction ou une lecture de configuration n’est pas une valeur secrète codée en dur. Une valeur statique renseignée dans un champ sensible bloque le contrôle, même si elle est courte. Les chaînes vides, les espaces seuls et la valeur JSON null sont considérés comme absents. Les configurations privées, bases et sauvegardes restent interdites par leur emplacement ou leur nom, même vides.

Les fichiers Python sont analysés sans les exécuter : affectations, dictionnaires, arguments nommés, valeurs par défaut et JSON embarqué. JSON et exemples structurés sont analysés récursivement. Les autres textes sont contrôlés pour les affectations usuelles. Les formats reconnaissables de jetons et blocs de clés privées sont cherchés indépendamment de ces champs, y compris dans les gros fichiers. Les diagnostics ne montrent jamais les valeurs détectées.

## Données fictives des tests

Certains tests ont besoin de valeurs inventées non vides pour tester un refus, un chiffrement ou une requête simulée. Le formulaire Home Assistant utilise aussi une valeur factice sans accès réseau pour valider la structure d’une association avant enregistrement. Ces seules sources relues le 17/10/2026 sont recensées dans `publication_fixtures_reviewed.json`, par empreinte SHA-256 de leur texte exact. Une modification du contenu invalide cette autorisation et impose une nouvelle relecture. Le fichier d’empreintes n’est jamais régénéré automatiquement par le vérificateur. Les modèles de configuration ne bénéficient pas de ces exceptions : leurs champs privés doivent rester vides.

Une empreinte autorisée ne permet jamais de contourner le refus d’un format de jeton reconnaissable ou d’un bloc de clé privée. Les anciens passe-droits par nom de fichier pour le contenu ont été retirés.

## Limites

Ce contrôle complète la séparation des fichiers privés, `.gitignore`, les tests et la relecture avant publication. Il ne peut pas identifier tous les formats de secrets, toutes les syntaxes ou des valeurs construites dynamiquement. Les références de configuration lues à l’exécution ne sont pas publiées avec leurs valeurs locales. Ce mécanisme n’est pas un coffre-fort ni une garantie exhaustive contre une fuite.
