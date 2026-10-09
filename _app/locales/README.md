# Textes de Gruterra — français et anglais

`fr.json` et `en.json` contiennent les textes affichés par l'application. Les deux catalogues doivent avoir les mêmes clés et paramètres (`{count}`, `{v0:.1f}`, etc.). Ajouter directement les deux traductions pour chaque nouvelle fonctionnalité. Éviter de recopier un texte déjà présent ; utiliser des clés décrivant son sens pour les prochains ajouts.

L'interface utilise `t()`, l'historique `vh_t()` et les services `traduire_courant()` du module `i18n`. `utiliser_langue()` permet un contexte explicite pour les tests et exports sans modifier les préférences locales. Une préférence absente ou invalide revient au français.

Les identifiants métier, codes de statut, clés de séries et titres techniques des événements balcon restent stables. Traduire leur présentation, pas les valeurs stockées ou utilisées par les calculs. Les noms et observations saisis par l'utilisateur, les données historiques et les notes de version anciennes ne sont pas traduits automatiquement.

`traduire_texte_courant()` sert uniquement à présenter les libellés canoniques connus et les descriptions du catalogue botanique. Ne pas l'appliquer à du texte libre utilisateur.

Vérification : `py -m unittest discover -s tests -q`. Les tests vérifient les clés référencées dans le code, les paramètres FR/EN et l'invariance des résultats des cycles. Les outils historiques de maintenance et leurs journaux techniques ne font pas partie du catalogue de l'interface.
