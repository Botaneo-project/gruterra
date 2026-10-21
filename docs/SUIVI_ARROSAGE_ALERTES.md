# Centre d’alertes : suivi après arrosage

## Première étape

Le centre réutilise les sessions calculées par `database.construire_sessions_arrosage` : apports rapprochés regroupés pour la lecture, événements bruts inchangés. Le service `services/suivi_arrosage_alertes.py` est local, sans réseau ni écriture dans la base.

Durant les 48 heures après la fin d’une session, un message contextualisé remplace l’alerte isolée d’humidité basse du même capteur. Il affiche date, volume total connu, nombre d’apports, humidité avant/première après/dernière et conductivité avant/après disponible. Un suivi sous 20 % reste de niveau surveillance. Ce seuil est indicatif, sans apprentissage automatique d’une valeur optimale.

La référence avant doit dater de moins de 24 heures. Les mesures entre les fractions ne sont pas présentées comme réponse à la session complète. Une mesure postérieure à 48 heures ne suffit pas à décrire un état actuel. Les repères manquants restent inconnus. Une hausse de conductivité seule ne prouve pas une hausse d’humidité.

Une baisse d’au moins trois points par jour est signalée seulement avec au moins quatre horaires distincts, six heures de recul après le pic observé, aucune interruption supérieure à huit heures et aucun conflit à horaire identique. Il s’agit d’une règle descriptive explicite, pas d’un seuil physiologique.

Les alertes critiques existantes sont conservées. La dernière évaluation de santé structurée préoccupante reste visible, avec sa date, jusqu’à une nouvelle évaluation ; un arrosage ne l’annule pas.

## Qualité et limites

Une seule identité physique est analysée à la fois. Les doublons exacts ne deviennent pas de nouvelles observations temporelles. Des valeurs différentes au même horaire sont écartées indépendamment pour l’humidité et la conductivité. Aucune moyenne n’est inventée.

Les métadonnées brutes JSON `is_test`, `manual_test`, `exclude_from_analysis` ou `quality` (`test`, `invalid`, `suspect`, `excluded`) permettent d’exclure explicitement des relevés des calculs sans les effacer. Les anciens tests manuels non identifiés ne sont pas détectables automatiquement : leur marquage reste un chantier d’interface distinct. Le texte libre des observations n’est pas utilisé pour poser un diagnostic.

Le niveau de confiance est descriptif ou limité, sans probabilité chiffrée. Le Mi Flora mesure une zone du substrat, sans garantie sur toute la motte. Aucun arrosage n’est créé ou déclenché par ce service.

## Préparation des cycles

`observer_cycles` expose, par capteur et par session, durée depuis arrosage, volume, humidité initiale, pic observé, délai du pic, amplitude, vitesse descriptive lorsque les données le permettent et intervalle de retour au niveau initial lorsqu’un franchissement est effectivement encadré. Le cycle s’arrête avant le suivant. Aucun retour n’est interpolé à travers une longue interruption.

La comparaison horticole des cycles, le rapprochement avec les observations libres et la modification éventuelle de conseils restent à développer sur ces repères. Les services historiques de comparaison restent en place.

## Démonstration et distribution

La session fractionnée fictive de la démo est placée dans la fenêtre de suivi ; les anciennes démos enregistrées ne sont pas régénérées automatiquement. Les tests couvrent français/anglais et la conservation des alertes critiques. Aucun changement de schéma de données.

Cette modification est incluse dans la reconstruction locale de la candidate 0.1.7-dev du 21 octobre, après 539 tests réussis et vérification silencieuse de la démonstration. Aucune publication.
