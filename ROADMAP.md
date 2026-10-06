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
- Base technique pour distinguer export de données et sauvegarde complète privée.
- Assistant de mise à jour GitHub prudent : vérification, simulation, sauvegarde locale et application seulement après validation explicite.

## Priorités courtes

- Valider l’auto-update en conditions réelles : bouton dans l’application, téléchargement contrôlé, sauvegarde, application et redémarrage.
- Accélérer la traduction français / anglais sur les écrans visibles par un nouveau testeur.
- Stabiliser Discord : messages socle épinglés, salons FR/EN cohérents, salons privés admin/bot protégés et tutoriels à jour.
- Rendre le mode démo plus agréable pour les nouveaux testeurs, avec captures publiques cohérentes.
- Améliorer encore la lecture graphique des cycles d’arrosage et la prudence des analyses plante.
- Clarifier l’installation Raspberry Pi et le sens des mesures rapatriées pendant que Gruterra était fermé.
- Ajouter une interface de sauvegarde/restauration utilisateur complète, avec avertissement secrets et retour arrière.

## Plus tard

- Migration vers un dossier utilisateur dédié.
- Notifications e-mail réellement activables après validation des règles.
- Collecte BLE passive Mi Flora plus poussée sur Raspberry.
- Configuration simplifiée des futurs ESP32 via réseau Wi‑Fi temporaire et page locale depuis téléphone.
- Comparaison avancée de journées et de cycles.
- Nettoyage progressif du vieux nom technique `botaneo` quand une vraie migration sera prête.
