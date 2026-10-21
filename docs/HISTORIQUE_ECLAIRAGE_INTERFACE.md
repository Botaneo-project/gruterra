# Historique pendant l’éclairage — interface du 15/10/2026

Après relance de Gruterra : fiche plante → Historique → Historique pendant l’éclairage.

- Horaires d’allumage/extinction en haut, boutons d’enregistrement et de synchronisation Pi séparés des données.
- Sélection directe d’une journée et quatre résumés : nombre de relevés, moyenne, minimum, maximum.
- Onglet « Journée sélectionnée » : graphique et tableau des relevés ; cliquer sur un point ou sélectionner une ligne les relie par un repère orange.
- Onglet « Comparer les journées » : tableau des 30 derniers jours ; choisir une ligne actualise la journée détaillée.
- Commandes Copier la journée, Actualiser et Fermer toujours dans une zone fixe en bas. Le contenu principal et les tableaux peuvent défiler dans une petite fenêtre.

Le graphique reprend toute la plage horaire configurée, y compris les portions sans relevé. Points et segments représentent uniquement les valeurs reçues : aucun lissage, aucune extrapolation aux extrémités ; interruption de ligne après un trou supérieur à 90 minutes. La courbe se redimensionne avec la fenêtre, en respectant le thème clair/sombre. Le zéro reste un vrai relevé.

Les horaires modifiés mais non appliqués sont signalés. Actualiser peut recalculer une plage sans la sauvegarder ; le résumé le précise. « Enregistrer et recalculer » écrit les horaires pour cette plante. Le bouton Pi conserve la procédure de synchronisation et de résolution de conflit existante.

Les calculs `light_schedule.analyse`, la période de 30 jours et la base utilisateur ne sont pas modifiés. La moyenne est celle des échantillons disponibles, pas une moyenne pondérée par durée ni une intégrale lumineuse. Les horaires actuels s’appliquent aux journées affichées. Une journée qui traverse minuit reste associée au jour d’allumage.

Textes nouveaux dans les catalogues FR/EN. Vérifications sur données fictives : fenêtre compacte et grande, thèmes clair/sombre, copie simulée incluant zéro, redimensionnement, plage traversant minuit et conservation des données/horaires. Une copie locale de l’ancien module est conservée dans `_security_backups`. Aucune publication GitHub.


## Repères de lecture et navigation

Les boutons Précédent/Suivant parcourent les journées disponibles. Le sélecteur, la comparaison des jours et le détail gardent la même sélection. La copie reste limitée à la journée sélectionnée.

Le résumé indique la première et la dernière mesures présentes et le plus grand intervalle entre deux mesures, sans inclure les bords de la plage. Un relevé unique ne produit pas de faux intervalle. Le statut horaire distingue une plage à venir, en cours ou terminée. « Terminée » signifie uniquement que l’heure de fin est passée, jamais que tous les relevés sont présents ; aucune fréquence théorique ni durée lumineuse n’est déduite.


## Couleurs communes et navigation lisible

Les palettes de l’interface principale et de l’historique sont désormais centralisées dans `_app/ui_palette.py`. Les couleurs principales ne changent pas ; le thème clair de l’historique reprend exactement leurs valeurs, comme le thème sombre. Les couleurs additionnelles des séries historiques restent disponibles.

Les deux onglets natifs Windows sont remplacés par des boutons de navigation à libellés complets : « Journée sélectionnée » et « Comparer les journées ». Le bouton actif utilise le vert principal avec un texte noir ou blanc choisi pour le contraste. Aucun emoji ni pictogramme n’est nécessaire pour les lire. Le bouton d’enregistrement reprend le même accent vert.


## Démonstration actualisée — 15/10/2026

La démo utilise les mêmes écrans et palettes que l’application réelle. Le jeu fictif a été rafraîchi avec quatre plantes et 480 relevés : variation artificielle pendant la plage 09:50–15:50, valeur nulle sur une journée et deux heures manquantes sur une autre pour illustrer les interruptions. Ces valeurs ne constituent ni une simulation horticole validée ni des recommandations d’éclairage.

Les horaires de démo sont stockés dans `_app/data/demo/config/light-schedules.json`, séparés de `_config/light-schedules.json`. La synchronisation Pi ne lit pas la configuration réelle en mode démo. Une ancienne base fictive a été sauvegardée dans `_security_backups` avant remplacement ; aucune base ou configuration réelle n’a été remplacée. Les lancements suivants ne régénèrent pas la démo si sa base existe déjà.


### Horaires d’éclairage datés PC/Pi — 17/10/2026
- [x] Conserver les anciennes plages et la date d’application des changements, en heure de Paris.
- [x] Calculer les bilans et graphiques selon la plage du jour d’allumage ; gérer les plages passant minuit.
- [x] Synchroniser le profil complet avec ses dates, conserver la détection des conflits et bloquer un envoi daté vers un ancien exporteur Pi.
- [x] Déployer sur le Raspberry après sauvegarde des fichiers ; service web actif, accès anonyme refusé (401), horaires existants inchangés.
- [x] Vérifier 17 tests ciblés, les fenêtres PC FR/EN sur données fictives et la syntaxe des scripts mobiles FR/EN.
- [x] Vérifier une synchronisation réelle PC/Pi : zéro changement, réglages concordants.
- [ ] Vérifier visuellement sur l’iPhone après actualisation, puis constater le premier changement réel d’horaire à la prochaine modification souhaitée.

Règle : un changement enregistré prend effet à la date du jour à Paris. Plusieurs modifications le même jour remplacent la plage de ce jour. Une plage nocturne appartient au jour où elle commence. Les dates anciennes sans historique utilisent le réglage précédemment connu : aucun changement passé n’est reconstitué. Une moyenne reste celle des relevés disponibles, sans interpolation ni estimation d’exposition totale.


## Comparer les journées et les cycles — améliorations locales du 18/10/2026

Depuis l'historique, ouvrir **Comparer jours** ou **Cycles**. Les boutons Copier, Actualiser et Fermer restent en bas de la fenêtre ; le contenu peut défiler. Les tableaux possèdent aussi des barres de défilement pour accéder aux colonnes et aux lignes.

Après une synchronisation, les comparaisons ouvertes se mettent à jour en conservant les journées ou cycles choisis. Un ajout fractionné conserve la sélection du même arrosage. Si une sélection n'existe plus, choisir une autre journée ou un autre cycle dans la liste : l'ancien résultat est retiré pour éviter une confusion.

La mention « Source : base locale » indique que la fenêtre relit les données déjà reçues par Gruterra. Le bouton Actualiser ne déclenche pas à lui seul une collecte sur le capteur. Si la lecture échoue, l'affichage précédent reste visible avec un avertissement, également inclus dans la copie.

Dans le graphique des cycles, les liaisons sont non lissées et interrompues au-delà de deux heures entre relevés. Cela n'invente aucune mesure et ne change pas les moyennes. Ces améliorations sont locales et ne sont pas encore une nouvelle version publiée.


<a id="centre-alertes"></a>
## Centre d’alertes — préparation locale du 18/10/2026

Les éléments prioritaires apparaissent avant les informations. Si plus de six alertes existent, utiliser « Afficher les autres alertes » pour consulter la liste complète ; le choix reste conservé lors d'une actualisation. Le niveau est écrit dans chaque titre et ne dépend pas uniquement de la couleur.

« Non vérifié » signifie qu'une donnée ou une lecture manque : cela ne prouve ni une mesure récente ni l'absence d'un problème. Les rappels sont calculés selon les jours locaux. Après un nouvel arrosage, l'ancien rappel en retard ne doit plus être actif.

Une prévision de deux heures expirée ou sans date fiable ne déclenche plus d'alerte météo à venir. Une prévision de pluie absente n'est pas affichée comme zéro. Ces indications restent un contexte local pour les plantes, pas un dispositif officiel d'alerte météorologique. Les seuils existants n'ont pas été modifiés dans ce lot.

### English

Priority items appear before informational items. Use “Show the other alerts” to expand a list longer than six items; the choice is retained when the view refreshes. Each title states its level in words as well as colour.

“Not verified” means that data or a reading is unavailable. It does not prove a recent reading or the absence of a problem. Reminders use local calendar days, and recording a new watering closes the old overdue reminder.

Expired or undated two-hour forecasts no longer trigger upcoming weather alerts. Missing rain forecasts are distinct from zero. These messages provide plant-related context, not an official weather warning service. Existing thresholds remain unchanged. These changes are local preparation and have not been released.
