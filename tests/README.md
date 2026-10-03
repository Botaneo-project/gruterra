# Tests Gruterra

Les tests automatisés couvrent les briques pures qui peuvent être vérifiées sans capteur, sans token et sans vraie base utilisateur.

Commande recommandée depuis la racine du projet :

```powershell
cd C:\Plantes
py -m unittest discover -s tests -p "test_*.py"
```

La commande d'audit complète lance aussi ces tests :

```powershell
cd C:\Plantes
py audit_botaneo.py
```

## Couverture actuelle

- Schéma neuf : création des tables principales, ajout plante, capteur et mesure.
- Nettoyage : suppression des mesures sans date exploitable.
- Dates : parsing ISO, suffixe `Z`, conversion locale et affichage utilisateur.
- Sessions d'arrosage : regroupement logique de plusieurs apports proches sans supprimer les lignes brutes.
- Cycles d'arrosage : humidité avant, première mesure, pic, fin, baisse après pic et vitesse simple de séchage.
- Cycles fractionnés : session 40 ml + 55 ml, début de session, volume total et mesures entre deux apports.
- Zéros suspects : conservation en données brutes, exclusion des graphiques/statistiques d'humidité si le zéro est isolé.
- Import Raspberry courant : ajout, accusé et déduplication idempotente.
- Import historique Raspberry brut : trame Mi Flora valide, archive brute, mesure exploitable et déduplication.
- Script d'audit local : retour OK, retour échec et comportement sans Git disponible.

## Limites connues

Ces tests ne remplacent pas les essais matériels. Ils ne valident pas directement :

- Bluetooth Windows réel ;
- connexion SSH réelle au Raspberry ;
- scan Mi Flora réel ;
- interface Tkinter en interaction utilisateur ;
- Netatmo, Météo-France ou tout service externe ;
- restauration complète d'une carte SD Raspberry.

L'objectif est d'éviter les régressions sur les règles de base avant de modifier l'interface, la synchronisation ou les analyses.
