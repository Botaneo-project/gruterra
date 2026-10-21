# Comparaison descriptive du séchage

Ajout local du 19/10/2026, dans les analyses des cycles existantes (pas de fenêtre supplémentaire).

- Fenêtre commune : 24 à 72 h après le dernier apport de la séance, fractions incluses.
- Bornes observées à ±2 h ; au moins quatre instants distincts ; interruption maximale de 8 h ; un même capteur identifié. Ces paramètres sont des garde-fous de lecture du logiciel, pas des normes de culture.
- Aucune interpolation, moyenne entre capteurs ou correction des valeurs. Le taux correspond à la variation entre les deux bornes réellement observées, rapportée à 24 h ; ce n’est pas une régression ni une prédiction.
- Si une borne manque, un long trou existe ou plusieurs sources sont mélangées, la comparaison est exclue et sa raison affichée. Un cycle encore non couvert est en attente.
- La référence est le précédent cycle exploitable du même capteur sur cette fenêtre. Volumes, lumière, température et position de la sonde peuvent différer : comparaison descriptive sans attribution causale.
- Le nombre de cycles n’active aucune recommandation automatique. Le quatrième cycle ne naît qu’après enregistrement d’un arrosage réellement effectué ; aucun événement anticipé n’est créé.
- Texte dans les catalogues FR/EN ; modes clair/sombre et fonctions de copie existants réutilisés.

Validation : six tests de logique ciblés, suite complète de 449 tests réussie avant les dernières précisions de libellés, puis tests ciblés réexécutés. Vérification des trois cycles Mi Flora existants par SQLite en lecture seule ; données inchangées.
