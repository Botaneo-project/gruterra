# Roadmap publique Gruterra

Cette roadmap donne une vue courte de l’état du projet. Le fichier `TODO.md` conserve le suivi détaillé du développement.

## En place

- Interface locale Windows en Tkinter.
- Mode démonstration sans matériel.
- Suivi de plantes avec ou sans capteur actif.
- Mesures Mi Flora et historique graphique.
- Arrosages manuels, rappels et journal plante.
- Analyse prudente des cycles d’arrosage.
- Gestion des sorties balcon pour contextualiser la lumière.
- Mini base de plantes avec besoins de base.
- Intégration Netatmo configurable localement.
- Synchronisation Raspberry Pi optionnelle.
- Audit local avant envoi GitHub.
- Export de données et sauvegarde complète privée accessibles dans Base & synthèses ; restauration complète automatique encore à construire.
- Assistant de mise à jour GitHub prudent : vérification, simulation, sauvegarde locale et application seulement après validation explicite.

## Priorités courtes

- Compléter le test utilisateur de l’update : passage 0.1.5-dev → 0.1.6-dev réussi ; PC de secours validé pour la version actuelle ; contrôler les corrections de redémarrage et de source après leur livraison dans la prochaine release.
- Maintenir les traductions FR/EN des nouvelles fonctionnalités ; la version actuelle est jugée satisfaisante par l’utilisateur le 10/10/2026.
- Stabiliser Discord : messages socle épinglés, salons FR/EN cohérents, salons privés admin/bot protégés et tutoriels à jour.
- Rendre le mode démo plus agréable pour les nouveaux testeurs, avec captures publiques cohérentes.
- Améliorer encore la lecture graphique des cycles d’arrosage et la prudence des analyses plante.
- Clarifier l’installation Raspberry Pi et le sens des mesures rapatriées pendant que Gruterra était fermé.
- Ajouter la restauration complète utilisateur avec sauvegarde de l’état existant ; les boutons d’export sont déjà présents.

- Préparer le raccordement au futur site : clés locales privées déjà préparées sur main, partage désactivé et démo exclue ; contrat, aperçu et reçus restent à définir.

## Plus tard

- Migration vers un dossier utilisateur dédié.
- Notifications e-mail réellement activables après validation des règles.
- Collecte BLE passive Mi Flora plus poussée sur Raspberry.
- Configuration simplifiée des futurs ESP32 via réseau Wi‑Fi temporaire et page locale depuis téléphone.
- Comparaison avancée de journées et de cycles.
- Nettoyage progressif du vieux nom technique `botaneo` quand une vraie migration sera prête.
