# Essai Windows : installation automatique de Python

Ce lot est un correctif de test local, pas une nouvelle release Gruterra.

## Sur le PC de test

1. Vérifier si Python est déjà installé. S’il l’est, ce PC testera la réutilisation d’un Python existant ; pour tester l’installation automatique, choisir un PC ou un Windows isolé qui n’en possède pas. Aucune désinstallation n’est nécessaire pour nos tests.
2. Télécharger et extraire l’archive Gruterra dans un nouveau dossier.
3. Copier `Installer_Gruterra.bat` et `requirements.txt` de ce lot à la racine de ce dossier Gruterra, en remplaçant ces deux fichiers.
4. Double-cliquer sur `Installer_Gruterra.bat`, avec une connexion Internet.
5. Laisser les six étapes se terminer, puis lancer `Lancer_Demo.bat`.

## Résultat attendu sans Python préalable

Le script ne trouve aucun Python compatible, télécharge Python 3.12.10 depuis python.org, l’installe, le redétecte à son emplacement précis, prépare l’environnement local, installe les dépendances et vérifie les imports ainsi que le fuseau Europe/Paris. Il atteint `[6/6] Gruterra est pret sur ce PC.` La fenêtre de démonstration doit ensuite s’ouvrir.

## Si cela échoue

Noter la dernière étape atteinte et copier le message d’erreur affiché. Le script s’arrête avant de lancer Gruterra si l’installation de Python échoue ; il ne doit pas annoncer une installation réussie.

## Déjà vérifié ici le 17/10/2026

Cinq tests Windows passent : détection sous un chemin avec espaces, priorité de l’interpréteur installé, échec du lancement démo correctement transmis, installation simulée suivie de redétection et arrêt si l’installation simulée échoue. La simulation crée un interpréteur temporaire ; elle ne télécharge ni n’exécute l’installateur Windows de Python. L’installation des dépendances et le lancement de la vraie démo ont été vérifiés séparément dans un environnement temporaire vide.

Windows Sandbox n’est pas disponible sur le PC de développement. L’installation réelle de Python sur un poste qui n’en possède pas reste donc à confirmer par cet essai.
