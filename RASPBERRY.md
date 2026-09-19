# Raspberry Pi — état et vérifications

Le Pi actuel est un collecteur autonome. L’interface mobile, la collecte et les sauvegardes démarrent sans session SSH. Le fonctionnement sur partage de connexion iPhone a été validé par l’utilisateur. Au retour, la synchronisation PC nécessite que les deux appareils puissent se joindre.

## Deux rythmes distincts

- Lecture des capteurs : environ trois fois par jour sur le Pi, plus une lecture manuelle depuis son interface.
- Récupération par le PC : à l’ouverture de Botaneo puis toutes les quinze minutes, réglables, sans réveiller les capteurs.

PC éteint ou application fermée : les mesures restent sur le Raspberry et seront récupérées plus tard. Un transfert réussi ne garantit pas qu’une nouvelle mesure vient d’être prise.

## Sauvegardes

Le Pi sauvegarde sa base quotidiennement vers 04 h 15 (heure locale), avec rattrapage au démarrage et conservation de quatorze fichiers. Les scripts et unités de sauvegarde sont conservés dans `raspberry/`. Ils supposent le collecteur déjà installé sous `~/botaneo` ; ce dossier ne constitue pas un installateur complet.

Le PC copie uniquement la dernière sauvegarde disponible. Ce fichier peut donc être antérieur aux dernières mesures transférées. Les anciennes copies PC ne sont pas supprimées automatiquement. Une sauvegarde sur la même carte SD ne protège pas contre sa panne ; la copie PC apporte un second support.

Les sauvegardes contiennent l’état de confirmation des transferts. Leur restauration doit prévoir la reprise des données et ne doit pas consister à écraser aveuglément la base PC. Ne jamais mettre les bases, clés SSH ou fichiers de mots de passe dans Git.

## Contrôle après retour au domicile

1. Arrêter le partage de connexion et vérifier le retour du Pi sur le Wi-Fi enregistré.
2. Ouvrir Botaneo sur le PC ; consulter le résultat dans la carte Raspberry.
3. Vérifier la date des mesures et le message de sauvegarde copiée ou déjà vérifiée.
4. Pour un nouveau capteur, vérifier son association à la bonne plante avant l’import.

## Prochaines validations

- Test complet avec un nouveau capteur en déplacement, puis retour et récupération PC.
- Essai de restauration avec reprise des mesures déjà confirmées.
- Alerte spécifique si les mesures sont anciennes malgré un transfert réussi.
- Futur serveur central permanent et ESP32 : conception distincte, pas encore installée.
