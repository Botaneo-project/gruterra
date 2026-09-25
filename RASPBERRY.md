# Raspberry Pi — état et vérifications

Le Pi actuel est un collecteur autonome. L’interface mobile, la collecte et les sauvegardes démarrent sans session SSH. Le fonctionnement sur partage de connexion iPhone a été validé par l’utilisateur. Au retour, la synchronisation PC nécessite que les deux appareils puissent se joindre.

## Deux rythmes distincts

- Lecture des capteurs : quatre demandes planifiées par jour sur le Pi, plus une lecture manuelle depuis son interface ou depuis Botaneo PC.
- Récupération par le PC : à l’ouverture de Botaneo puis toutes les quinze minutes, réglables, sans réveiller les capteurs.

PC éteint ou application fermée : les mesures restent sur le Raspberry et seront récupérées plus tard. Un transfert réussi ne garantit pas qu’une nouvelle mesure vient d’être prise.

## Sauvegardes

Le Pi demande une collecte Mi Flora à 06 h, 12 h, 18 h et 23 h via `botaneo-collect.timer`. Le script `request_collect.py` ne parle pas directement au Bluetooth : il crée la même demande que le bouton manuel, afin que le collecteur existant reste seul à lire les capteurs.

Le Pi sauvegarde sa base quotidiennement vers 04 h 15 (heure locale), avec rattrapage au démarrage et conservation de quatorze fichiers. Les scripts et unités de sauvegarde sont conservés dans `raspberry/`.

Une première base d’installation reproductible existe dans `raspberry/install/`. Elle installe les scripts de collecte/export/sauvegarde, les timers utilisateur et crée une configuration exemple sans secret. Elle ne remplace pas encore une image Raspberry complète prête à flasher.

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

## Prototype BLE passif Mi Flora

Un prototype expérimental existe dans `raspberry/collector/passive_ble.py`. Il écoute les annonces BLE `FE95` du Mi Flora / Flower Care sans connexion active au capteur. Il peut afficher les valeurs décodées et, avec l'option `--store`, enregistrer une mesure complète uniquement si température, humidité, luminosité et conductivité ont toutes été reçues pendant la fenêtre d'écoute.

Commande de test sur le Raspberry :

```bash
cd ~/botaneo/collector
python3 passive_ble.py --duration 180 --verbose
```

Commande avec enregistrement expérimental :

```bash
cd ~/botaneo/collector
python3 passive_ble.py --duration 300 --store
```

Cette collecte passive n'est pas encore activée par timer. Elle doit d'abord être observée sur plusieurs passages, car les annonces sont intermittentes et chaque paquet ne contient pas forcément toutes les mesures. La lecture active et l'import historique restent nécessaires pour la batterie, les diagnostics et le rattrapage des trous.

### Service manuel de test passif

Le service `botaneo-passive-test.service` est installé avec les scripts Raspberry mais n'est pas activé par timer. Il lance :

```bash
python3 ~/botaneo/collector/passive_ble.py --duration 300 --store
```

Il écrit dans la table `measurements` existante seulement si une mesure complète est reçue. La source est conservée dans le champ brut avec `source=passive_mibeacon`, ce qui permettra ensuite de distinguer ces mesures dans Botaneo.
