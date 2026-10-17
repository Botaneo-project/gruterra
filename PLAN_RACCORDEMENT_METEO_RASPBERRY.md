# Raccordement météo Raspberry — plan applicatif

Plan du 11/10/2026. Collecte horaire non activée ; aucun transfert de token prévu par ce plan.

Référence : RACCORDEMENT_METEO_RASPBERRY.md, proposition du 11/10/2026.

## 1. Valider le contrat commun avec le Raspberry

- Définir ensemble un exemple fictif complet d’observation, un lot paginé et son accusé.
- Fixer les versions, champs obligatoires/facultatifs, unités, représentation des UTC et périodes de cumul.
- Définir l’identité canonique, les révisions, la reprise et les limites de taille.
- Préserver les identifiants des stations choisis dans la configuration privée. Aucun remplacement silencieux ni retrait des autres favoris.

Livrable : contrat accepté par les deux côtés avant raccordement réseau.

## 2. Préparer le stockage PC

- Ajouter des tables versionnées d’observations et reçus dans la base météo locale.
- Garder la table pluie existante et ses dates telles qu’elles sont ; ne pas inventer d’UTC pour les anciennes dates ambiguës.
- Conserver valeurs nulles explicites, module, provenance, date source, date de récupération et définition source du cumul.
- Dédupliquer les mêmes observations ; garder les révisions au lieu d’écraser une valeur corrigée.
- Utiliser une normalisation commune pour les futurs relevés PC et Pi.

Livrable : migration non destructive et importeur testé sur copies fictives.

## 3. Préparer la synchronisation

- Raccorder weather_export / weather_ack au parcours SSH existant, séparément de Mi Flora.
- Valider tout lot avant import transactionnel ; accuser uniquement après conservation durable.
- Rejouer sans doublon après coupure ou accusé perdu ; ne rien effacer à l’accusé.
- Prévoir les erreurs expurgées et un bilan lisible : nouvelles observations, doublons, révisions, sources absentes.

## 4. Afficher les données importées

- Adapter les lecteurs météo et l’historique pluie aux observations versionnées.
- Afficher station, date source, origine Raspberry et fraîcheur réelle.
- Distinguer zéro, absence et observation non datée.
- Traduire immédiatement les nouveaux textes dans les JSON FR/EN.
- Ne pas sommer les cumuls glissants ni les stations ; ne pas déduire l’heure exacte d’une averse.

## 5. Valider sécurité, sauvegarde et collecte réelle

- Convenir explicitement du propriétaire OAuth : Pi seul dans ce mode, ou autorisations distinctes vérifiées.
- Ne pas désactiver la collecte PC existante avant validation de la bascule et de son retour arrière.
- Vérifier droits et quotas Netatmo ; tester expiration, rotation, 429 et invalid_grant sans secrets dans les journaux.
- Étendre les sauvegardes Raspberry à weather.sqlite3 et vérifier copie/restauration PC.
- Tester une collecte réelle manuelle, l’import deux fois et les reprises.
- Activer le timer uniquement après validation ; vérifier ensuite PC éteint et redémarrage Pi.

## Critères de validation applicative

Tests : zéro/null/absent, plusieurs modules, changement d’heure, dates anciennes/inconnues, révisions, lots invalides, import répété, coupure avant/après transaction, accusé perdu, migration et restauration.

L’état reste « préparation » jusqu’aux essais réels. Ne pas annoncer « collecte horaire opérationnelle » sur la seule réussite des simulations.

## Publication

Mettre à jour les guides et les notes de version lorsque le comportement est effectivement validé. Ce plan n’autorise ni une nouvelle release ni l’activation du timer.

## Décision actualisée — secours PC

Le PC conserve son accès Netatmo actuel pour les consultations fraîches. Ces consultations actualisent uniquement le cache d’affichage, sans ajouter d’historique de pluie ; l’historique existant reste conservé. L’archivage des futures observations collectées sur Pi reste distinct.
Le Pi devra disposer d’un accès indépendant effectivement vérifié, ou d’une gestion partagée sûre encore à définir. Aucun refresh token actuel n’est copié et aucune bascule de propriétaire OAuth n’est appliquée. Cette décision remplace l’orientation « Pi seul propriétaire » du plan, pas les précautions de rotation ou de confidentialité.
