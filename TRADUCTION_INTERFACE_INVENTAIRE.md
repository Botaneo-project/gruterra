# Gruterra — Inventaire traduction interface

Objectif : éviter les doublons de traduction et migrer `interface.py` par zones cohérentes.

- Textes visibles ou probablement visibles détectés : 549
- Déjà présents à l’identique dans `fr.json` : 12
- À classer / migrer progressivement : 537

## Règle de travail

- Toute nouvelle fonctionnalité qui ajoute un texte visible doit ajouter la clé dans `fr.json` et `en.json` en même temps.
- Ne pas créer une nouvelle clé si une clé existante couvre déjà exactement le même sens.
- Migrer par zone fonctionnelle : synchronisation, paramètres, historique, Netatmo/Raspberry, alertes, ajout plante/capteur.
- Garder `i18n.py` comme chargeur uniquement ; éviter d’y remettre des traductions longues.

## État par zone

### etat_global_config

- Total repéré : 21
- Déjà couvert JSON : 1
- À traiter : 20

Exemples à migrer/classer :
- ligne 109 : `Pr\xe9pare un texte Unicode pour Tkinter sans supprimer accents ni emojis valides.`
- ligne 160 : `\U0001f326\ufe0f Donn\xe9es m\xe9t\xe9o non charg\xe9es`
- ligne 248 : `%d/%m/%Y \xe0 %H:%M:%S`
- ligne 314 : ` % \xb7 seuil `
- ligne 317 : `\U0001f7e0 Batterie \xe0 surveiller : `
- ligne 317 : ` % \xb7 seuil `
- ligne 361 : `Historique Mi Flora : aucun import lanc\xe9 depuis l'interface.`
- ligne 371 : ` d\xe9j\xe0 connue(s)`
- ligne 372 : `import r\xe9ussi`
- ligne 373 : `Historique Mi Flora : dernier import le `
- ligne 375 : `Historique Mi Flora : dernier essai le `
- ligne 375 : `\xe9chec`
- ligne 465 : `lundi \xe0 vendredi`
- ligne 478 : `Auto d\xe9sactiv\xe9e \xb7 `
- ligne 481 : ` \xb7 d\xe9j\xe0 faite aujourd'hui \xe0 `
- ligne 483 : ` \xb7 en attente`
- ligne 504 : `V\xe9rifie p\xe9riodiquement si la synchronisation automatique doit partir.`
- ligne 523 : `Lance la synchro du jour en r\xe9utilisant le bouton existant.`

### analyses_plantes

- Total repéré : 120
- Déjà couvert JSON : 0
- À traiter : 120

Exemples à migrer/classer :
- ligne 679 : `Aucune donn\xe9e`
- ligne 679 : `Anciennet\xe9 inconnue`
- ligne 712 : `\U0001f7e2 Mesure r\xe9cente \xb7 `
- ligne 714 : `\U0001f7e0 Mesure \xe0 surveiller \xb7 `
- ligne 715 : `\U0001f534 Mesure ancienne \xb7 `
- ligne 799 : `\U0001f7e0 Suivi post-arrosage : humidit\xe9 encore basse`
- ligne 804 : `\U0001f534 Humidit\xe9 tr\xe8s basse`
- ligne 817 : `\U0001f7e0 Humidit\xe9 \xe0 surveiller`
- ligne 823 : `\U0001f7e2 Humidit\xe9 correcte`
- ligne 861 : `Lumi\xe8re 24 h : pas assez de mesures`
- ligne 889 : `Lumi\xe8re faible sur 24 h`
- ligne 890 : `\xc9clairage conseill\xe9.`
- ligne 895 : `Pic lumineux isol\xe9`
- ligne 898 : `Le pic ressemble \xe0 une exposition ponctuelle ; la moyenne reste faible pour juger la journ\xe9e compl\xe8te.`
- ligne 904 : `Lumi\xe8re \xe0 surveiller`
- ligne 907 : `La plante re\xe7oit peu de vraie lumi\xe8re utile.`
- ligne 913 : `Lumi\xe8re correcte aujourd'hui`
- ligne 958 : `Pr\xe9vision 48-72 h : pas assez de donn\xe9es`

### cartes_plantes

- Total repéré : 88
- Déjà couvert JSON : 2
- À traiter : 86

Exemples à migrer/classer :
- ligne 1700 : `contr\xf4le humidit\xe9 0 %`
- ligne 1702 : `Humidit\xe9 0 % d\xe9tect\xe9e \xb7 aucun contr\xf4le : pas de capteur actif`
- ligne 1703 : `Humidit\xe9 0 % d\xe9tect\xe9e \xb7 contr\xf4le programm\xe9 lanc\xe9`
- ligne 1728 : `Ajoute une sortie balcon pass\xe9e avec date de sortie et de retour.`
- ligne 1742 : `\u2600\ufe0f Exposition balcon \xb7 `
- ligne 1779 : `Date invalide. Format conseill\xe9 : 25/09/2026 14:30`
- ligne 1782 : `Le retour doit \xeatre apr\xe8s la sortie.`
- ligne 1793 : `Plante sortie temporairement sur le balcon. Dur\xe9e d\xe9clar\xe9e : `
- ligne 1793 : ` Les pics de lumi\xe8re de cette p\xe9riode doivent \xeatre interpr\xe9t\xe9s comme une exposition ext\xe9rieure ponctuelle.`
- ligne 1801 : `Plante rentr\xe9e \xe0 l'int\xe9rieur apr\xe8s une exposition balcon d\xe9clar\xe9e de `
- ligne 1801 : ` Les mesures suivantes correspondent de nouveau \xe0 l'emplacement habituel.`
- ligne 1802 : `Retour int\xe9rieur`
- ligne 1807 : `Impossible d'enregistrer l'exposition : `
- ligne 1812 : `Exposition balcon ajout\xe9e pour `
- ligne 1823 : `Enregistre un \xe9v\xe9nement d'exposition ext\xe9rieure dans le journal de la plante apr\xe8s validation.`
- ligne 1827 : `%d/%m/%Y \xe0 %H:%M`
- ligne 1830 : `Plante sortie temporairement sur le balcon. Les pics de lumi\xe8re suivants doivent \xeatre interpr\xe9t\xe9s comme une exposition ext\xe9rieure ponctuelle.`
- ligne 1831 : `Sortie balcon not\xe9e pour `

### netatmo_meteo

- Total repéré : 52
- Déjà couvert JSON : 1
- À traiter : 51

Exemples à migrer/classer :
- ligne 2952 : `\U0001f4c8 Historique mesures`
- ligne 2954 : `\U0001f4c8 Historique / raccourci`
- ligne 3051 : `Pr\xe9vision +2 h indisponible`
- ligne 3078 : `M\xe9t\xe9o locale`
- ligne 3078 : `M\xe9t\xe9o locale`
- ligne 3082 : `Pr\xe9vision non charg\xe9e pour le moment.`
- ligne 3098 : `\U0001f321\ufe0f Temp\xe9rature`
- ligne 3104 : `Pr\xe9vision locale charg\xe9e.`
- ligne 3106 : ` \xb7 Donn\xe9e affich\xe9e depuis le cache.`
- ligne 3194 : `Colle un identifiant Netatmo ou un lien weathermap.`
- ligne 3221 : `Impossible d'enregistrer le favori Netatmo.`
- ligne 3232 : `Station d\xe9j\xe0 pr\xe9sente dans les favoris Gruterra.`
- ligne 3234 : `Station ajout\xe9e aux favoris Gruterra. Lance Actualiser Netatmo pour charger ses donn\xe9es.`
- ligne 3274 : `Le nom ne peut pas \xeatre vide.`
- ligne 3367 : `Temp\xe9rature`
- ligne 3379 : `Temp\xe9rature min`
- ligne 3380 : `Temp\xe9rature max`
- ligne 3467 : `non remont\xe9`

### synchronisation

- Total repéré : 43
- Déjà couvert JSON : 0
- À traiter : 43

Exemples à migrer/classer :
- ligne 4726 : `\U0001f4e5 Historique Mi Flora `
- ligne 4726 : ` \xb7 scan passe `
- ligne 4727 : ` depuis l\u2019entr\xe9e `
- ligne 4728 : ` r\xe9cup\xe9r\xe9e(s)`
- ligne 4732 : `\U0001f4e5 Historique Mi Flora `
- ligne 4732 : ` \xb7 connexion Bluetooth, passe `
- ligne 4733 : ` r\xe9cup\xe9r\xe9e(s)`
- ligne 4737 : `\U0001f4e5 Historique Mi Flora `
- ligne 4737 : ` \xb7 lecture m\xe9moire depuis l\u2019entr\xe9e `
- ligne 4738 : ` r\xe9cup\xe9r\xe9e(s)`
- ligne 4742 : `\U0001f4e5 Historique Mi Flora `
- ligne 4742 : ` \xb7 passe `
- ligne 4743 : ` termin\xe9e, `
- ligne 4743 : ` entr\xe9e(s) lue(s) \xb7 `
- ligne 4743 : ` r\xe9cup\xe9r\xe9e(s)`
- ligne 4748 : `\U0001f4e5 Historique Mi Flora `
- ligne 4748 : ` \xb7 enregistrement local, `
- ligne 4749 : ` entr\xe9e(s) r\xe9cup\xe9r\xe9e(s), `

### parametres_update_sante_maintenance

- Total repéré : 98
- Déjà couvert JSON : 4
- À traiter : 94

Exemples à migrer/classer :
- ligne 5236 : `Une mise \xe0 jour Gruterra est disponible : `
- ligne 5236 : `.

Voulez-vous la t\xe9l\xe9charger et l'appliquer maintenant ?

Vous pouvez r\xe9pondre Non et continuer \xe0 utiliser Gruterra normalement, y compris synchroniser les capteurs.`
- ligne 5274 : `R\xe9vision Git : `
- ligne 5280 : `- R\xe9glages personnels : `
- ligne 5285 : `- Raspberry optionnel : collecte et rattrapage`
- ligne 5286 : `- Netatmo priv\xe9/public et m\xe9t\xe9o locale`
- ligne 5288 : `- historique graphique avec qualit\xe9 des donn\xe9es`
- ligne 5290 : `Raspberry : `
- ligne 5294 : `S\xe9curit\xe9 :`
- ligne 5295 : `- les acc\xe8s priv\xe9s, bases r\xe9elles et sauvegardes restent sur ce PC`
- ligne 5297 : `- les documents priv\xe9s de passation ne sont pas publi\xe9s`
- ligne 5311 : `\U0001f33f Gruterra`
- ligne 5494 : ` synth\xe8se(s) calcul\xe9e(s)`
- ligne 5494 : `aucune synth\xe8se calcul\xe9e`
- ligne 5497 : `table non initialis\xe9e`
- ligne 5499 : `all\xe8gement \xe0 envisager plus tard`
- ligne 5499 : `aucune action n\xe9cessaire`
- ligne 5503 : `Fichier de donn\xe9es utilis\xe9 : `

### ajout_plante_capteur

- Total repéré : 11
- Déjà couvert JSON : 0
- À traiter : 11

Exemples à migrer/classer :
- ligne 6393 : `Esp\xe8ce`
- ligne 6394 : `Zone ou pi\xe8ce`
- ligne 6484 : `Plante non connue dans la mini base. Vous pouvez quand m\xeame l'ajouter manuellement.`
- ligne 6512 : `Int\xe9rieur`
- ligne 6513 : `Ext\xe9rieur`
- ligne 6559 : `Ajout impossible. V\xe9rifiez l'acc\xe8s \xe0 la base.`
- ligne 6566 : `Plante ajout\xe9e. Elle peut rester sans capteur ou recevoir un capteur plus tard.`
- ligne 6616 : `Il faut une plante sans capteur actif. Ajoutez d'abord une plante depuis l'interface.`
- ligne 6630 : `Plante \xe0 associer`
- ligne 6644 : `Ajout impossible. V\xe9rifiez l'acc\xe8s \xe0 la base et \xe0 la sauvegarde.`
- ligne 6648 : `Capteur ajout\xe9. Cliquez sur Synchroniser pour effectuer sa premi\xe8re lecture.`

### export_analyse_historique

- Total repéré : 55
- Déjà couvert JSON : 1
- À traiter : 54

Exemples à migrer/classer :
- ligne 6698 : `, derni\xe8re `
- ligne 6721 : `Lumi\xe8re`
- ligne 6722 : `Temp\xe9rature`
- ligne 6723 : `Conductivit\xe9`
- ligne 6730 : `- Qualit\xe9 : `
- ligne 6730 : ` trou(s) sup\xe9rieur(s) \xe0 environ 1 h 48.`
- ligne 6744 : `retour int\xe9rieur`
- ligne 6813 : `Contexte lumi\xe8re :`
- ligne 6815 : ` exposition(s) balcon not\xe9e(s) sur les 14 derniers jours.`
- ligne 6819 : ` : sortie balcon d\xe9clar\xe9e, dur\xe9e `
- ligne 6821 : ` : sortie balcon d\xe9clar\xe9e, retour non not\xe9.`
- ligne 6823 : `- Aucune exposition balcon r\xe9cente not\xe9e dans le journal.`
- ligne 6828 : `- Lumi\xe8re `
- ligne 6836 : ` jusqu'\xe0 `
- ligne 6840 : `- Interpr\xe9tation : les pics lumineux sont contextualis\xe9s par les sorties balcon ; ils ne doivent pas masquer la luminosit\xe9 habituelle de l'emplacement int\xe9rieur.`
- ligne 6847 : `Plante introuvable dans Gruterra.`
- ligne 6872 : `quantit\xe9 non renseign\xe9e`
- ligne 6885 : `Arrosages r\xe9cents :`

### alertes_email

- Total repéré : 47
- Déjà couvert JSON : 0
- À traiter : 47

Exemples à migrer/classer :
- ligne 7146 : `\U0001f4c8 Historique de mesures`
- ligne 7156 : ` n'a pas encore de mesures capteur enregistr\xe9es. C'est normal pour une plante sans capteur actif.`
- ligne 7198 : `Aucune plante n'a encore d'historique de mesures. Apr\xe8s une synchronisation Mi Flora, le bouton ouvrira les graphiques.`
- ligne 7252 : `date \xe0 v\xe9rifier`
- ligne 7272 : `Mail de rappel pr\xe9vu : une semaine avant, date \xe0 v\xe9rifier.`
- ligne 7274 : `Mail de rappel : \xe0 pr\xe9parer maintenant, car l\u2019\xe9ch\xe9ance est \xe0 moins d\u2019une semaine.`
- ligne 7275 : `Mail de rappel pr\xe9vu environ le `
- ligne 7333 : `\U0001f4a7 Arrosage manuel \xe0 faire \xb7 `
- ligne 7336 : `\U0001f4a7 Arrosage manuel bient\xf4t \xb7 `
- ligne 7345 : `quantit\xe9 non renseign\xe9e`
- ligne 7349 : `Aucun rappel programm\xe9 : utile pour les plantes hors domicile ou sans mesure d'humidit\xe9.`
- ligne 7360 : `\U0001f50b Batterie faible \xb7 `
- ligne 7360 : ` % \xb7 seuil `
- ligne 7362 : `\U0001f50b Batterie \xe0 surveiller \xb7 `
- ligne 7370 : `\U0001f4e1 Donn\xe9e ancienne \xb7 `
- ligne 7370 : `Derni\xe8re mesure `
- ligne 7382 : `\U0001f4a7 Arrosage \xe0 faire \xb7 `
- ligne 7388 : `\U0001f4a7 Arrosage bient\xf4t \xb7 `

### accueil_toolbar

- Total repéré : 14
- Déjà couvert JSON : 3
- À traiter : 11

Exemples à migrer/classer :
- ligne 7646 : `\U0001f326\ufe0f M\xe9t\xe9o locale`
- ligne 7647 : `Netatmo et pr\xe9visions proches`
- ligne 7654 : `\U0001f514 \xc0 surveiller`
- ligne 7661 : `\U0001f5a5\ufe0f Suivi syst\xe8me`
- ligne 7662 : `\xe9tat local et contr\xf4les automatiques`
- ligne 7688 : ` affich\xe9e(s)`
- ligne 7717 : ` plante(s) masqu\xe9e(s) sur l'accueil`
- ligne 7744 : `\U0001f326\ufe0f M\xe9t\xe9o locale`
- ligne 7745 : `Netatmo et pr\xe9visions proches`
- ligne 7806 : `\U0001f331 Toutes les plantes`
- ligne 7807 : ` affich\xe9e(s)`

## Prochaine passe recommandée

1. Terminer le lot Synchronisation déjà commencé.
2. Migrer les textes de Paramètres, car ils sont visibles et structurants.
3. Ajouter un test qui vérifie que les clés utilisées dans `interface.py` existent dans les deux JSON.
4. Migrer ensuite Historique/graphiques, puis Netatmo/Raspberry.
