# Récupérer une mise à jour interrompue

Préparation locale du 18/10/2026 — pas encore une nouvelle version publiée.

## Fonctionnement

Avant de remplacer le programme, Gruterra conserve une sauvegarde, vérifie son contenu et écrit un journal des fichiers concernés. Chaque remplacement est annoncé dans ce journal avant de commencer. Une copie autonome du moteur de récupération est conservée avec la sauvegarde, pour fonctionner même si le programme a été partiellement remplacé.

Si le processus s'arrête avant validation, fermer Gruterra puis utiliser **Lancer_Gruterra.bat** ou **Lancer_Demo.bat**, selon le mode habituel. Avec les nouveaux lanceurs installés, la récupération intervient avant l'ouverture de l'interface et avant l'accès à la base réelle ou de démonstration. Les fichiers de l'ancienne version sont restaurés ; les fichiers ajoutés par la tentative sont retirés. Les données et configurations privées ne font pas partie de ce remplacement.

Un message indique que la version précédente a été restaurée. La mise à jour n'est alors pas considérée comme réussie : la vérifier à nouveau dans les paramètres après récupération. La sauvegarde reste conservée.

Si tous les remplacements ont été validés mais que le processus s'est arrêté avant de nettoyer le journal, les fichiers validés sont vérifiés et la nouvelle version est conservée.

## Si la récupération est bloquée

L'application ne s'ouvre pas si la sauvegarde est corrompue, le journal incompréhensible, un fichier verrouillé ou une nouvelle modification locale incompatible avec le retrait d'un fichier ajouté. Une autre mise à jour active bloque également un deuxième lancement ou une deuxième installation.

Conserver `_security_backups`, le programme et les données. Ne pas supprimer manuellement `update-pending.json` pour forcer l'ouverture : cela retirerait le contrôle sans réparer l'installation. Demander un diagnostic en conservant la sauvegarde ; ne pas partager de configurations privées ou de bases personnelles.

Le journal `update-pending.json` et le moteur autonome `update-recovery.py` se trouvent dans `_security_backups`. Le moteur peut être lancé directement avec Python pour une récupération locale lorsqu'un lanceur du programme est endommagé ; cette opération doit viser le dossier d'installation concerné. Elle ne télécharge rien et ne touche pas aux jetons.

L'installateur refuse de remplacer le programme si une mise à jour ou récupération est active ou inachevée. Il faut d'abord terminer la récupération ou traiter son blocage.

## Limites des vérifications

Les essais arrêtent réellement des processus sur des installations fictives : pendant la préparation d'un fichier, après plusieurs remplacements, après validation et pendant une restauration. Les essais incluent les deux lanceurs, un moteur principal incompatible, une sauvegarde corrompue et des chemins de journal interdits. Les données privées fictives restent inchangées.

Cela ne constitue pas un essai de coupure électrique matérielle. Les écritures sont vidées et les remplacements atomiques sont utilisés, mais une perte ou corruption du disque peut aussi rendre la sauvegarde inutilisable. La première mise à jour exécutée par un ancien updater ne bénéficie pas rétroactivement de ce mécanisme : les nouveaux lanceurs et l'updater doivent être installés. Un lancement direct de `_app/interface.py` n'est pas le parcours de récupération.

## English

Before replacing program files, Gruterra keeps a verified backup and records each replacement intent. A standalone recovery engine is stored alongside the backup, outside the program files being replaced.

After an interrupted update, close Gruterra and use the normal real or demo launcher. Once the new launchers are installed, recovery runs before the interface opens or a real/demo database is accessed. An unfinished update restores the previous program and removes files added by that attempt. A committed update is verified and retained. Backups remain available.

If recovery is blocked, the application does not start. Keep the backup and journal; do not delete the journal to bypass the check. An active updater or unfinished recovery also blocks setup. No network, account credentials or private user data are needed for recovery.

Tests forcibly terminate real child processes on fictional installations. They do not reproduce a physical power cut or disk failure. Older updaters do not gain these protections retroactively, and launching `_app/interface.py` directly is not a recovery path. These changes remain local preparation, not a published release.
