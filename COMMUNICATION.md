# Gruterra — communication et captures

Ce fichier sert à préparer une présentation courte du projet pour GitHub, Reddit ou un message de testeurs.

## Présentation courte

Gruterra est une application locale de suivi des plantes d’intérieur. Elle combine les mesures Mi Flora, l’historique du capteur, les arrosages, les observations manuelles, la météo locale et une démo utilisable sans matériel.

L’objectif n’est pas seulement d’afficher des valeurs, mais d’aider à comprendre l’évolution d’une plante : humidité du substrat, lumière réellement reçue, réaction après arrosage, cycles de séchage et rappels pour les plantes sans capteur.

## Version Reddit courte

Je développe Gruterra, une petite application locale pour suivre mes plantes avec des capteurs Mi Flora, un Raspberry Pi et des données météo.

Le projet permet déjà de suivre l’humidité du sol, la température, la luminosité, la conductivité, les arrosages, les observations et les cycles après arrosage. Il y a aussi un mode démo pour tester l’application sans capteur.

Le but est de passer de “voici la mesure actuelle” à “voici ce qui change, ce qui mérite attention, et ce qu’il faudra vérifier ensuite”.

Le projet est encore en développement, mais je cherche des retours sur l’interface, la logique d’analyse des plantes et les idées utiles pour rendre le suivi plus pratique au quotidien.

## Version Reddit plus détaillée

Bonjour,

Je développe Gruterra, une application locale pour suivre les plantes d’intérieur avec des capteurs Mi Flora et, à terme, un petit collecteur Raspberry Pi.

L’application récupère les mesures du capteur : humidité du sol, température, luminosité et conductivité. Elle conserve l’historique, permet d’enregistrer les arrosages et les observations, puis commence à analyser les cycles après arrosage : humidité avant arrosage, pic observé, évolution après 24 h / 48 h, vitesse de séchage et qualité des données disponibles.

Je l’utilise notamment pour suivre une Crassula ovata. Le sujet principal est de comprendre si la plante manque d’eau, reçoit trop peu de lumière, ou si le substrat reste humide trop longtemps. L’idée est donc de garder les données brutes, mais aussi d’ajouter une lecture plus utile qu’un simple tableau de mesures.

Il y a aussi :

- un mode sombre ;
- une démo sans capteur ;
- une gestion des plantes sans capteur ;
- des rappels d’arrosage ;
- une intégration météo locale ;
- une préparation pour Raspberry Pi ;
- une vérification avant envoi GitHub pour éviter d’envoyer des secrets.

Le projet est encore en développement. Je serais intéressé par des retours sur l’interface, les graphiques, la logique d’analyse après arrosage, et les usages que vous verriez pour un suivi de plantes en local.

## Points à mettre en avant

- Application locale : les données personnelles restent sur la machine de l’utilisateur.
- Démo disponible sans capteur, sans Raspberry et sans compte Netatmo.
- Historique Mi Flora exploité pour analyser les tendances, pas seulement la dernière mesure.
- Suivi des plantes avec ou sans capteur.
- Arrosages et événements manuels reliés aux graphiques.
- Comparaison de cycles d’arrosage.
- Raspberry Pi prévu comme collecteur local pour fiabiliser les mesures.

## Ce qui est encore en développement

- Auto-update propre pour les futurs utilisateurs.
- Interface historique encore à améliorer visuellement.
- Installation Raspberry Pi simplifiée.
- Alertes e-mail et rappels avancés.
- Comparaison plus complète des journées et des cycles d’arrosage.
- Documentation utilisateur plus progressive.

## Captures recommandées

### 1. Accueil avec Crassula démo

But : montrer immédiatement l’intérêt de l’application.

À afficher :

- nom de la plante ;
- besoins de base ;
- mesures Mi Flora ;
- blocs “À faire aujourd’hui”, “À surveiller”, “Prévision 48-72 h”.

À éviter :

- données personnelles ;
- vraie adresse BLE personnelle ;
- station météo personnelle.

### 2. Historique lumière

But : montrer que Gruterra analyse la lumière dans le temps.

À afficher :

- journée sélectionnée ;
- graphique lumière ;
- pic lié à une sortie balcon ;
- axe horaire visible.

Message associé :

> La lumière est analysée sur la durée, pour éviter qu’un pic ponctuel masque une journée globalement sombre.

### 3. Cycle d’arrosage

But : montrer la partie la plus originale.

À afficher :

- arrosage ;
- humidité avant arrosage ;
- pic ;
- repères 24 h et 48 h ;
- comparaison entre deux cycles si visible.

Message associé :

> L’objectif est de comprendre comment le substrat réagit après un arrosage, sans confondre la mesure locale du Mi Flora avec l’état complet de la motte.

### 4. Plante sans capteur

But : montrer que l’application ne dépend pas uniquement du matériel.

À afficher :

- Cactus balcon démo ;
- dernier arrosage manuel ;
- prochaine date d’arrosage ou rappel ;
- absence de capteur clairement indiquée.

Message associé :

> Les plantes sans capteur peuvent aussi être suivies avec des rappels et des observations manuelles.

### 5. À propos / mise à jour

But : montrer que le projet devient distribuable.

À afficher :

- nom Gruterra ;
- version ;
- bouton de vérification des mises à jour ;
- indication claire si le dépôt privé empêche la vérification distante.

## Message court pour accompagner les captures

Quelques captures de Gruterra en mode démo. Les données sont fictives, mais elles montrent le fonctionnement prévu : suivi de plante, historique Mi Flora, cycles d’arrosage, lumière, rappels et plantes sans capteur.

Je cherche surtout des retours sur la lisibilité, les graphiques et les informations utiles à afficher en priorité.
