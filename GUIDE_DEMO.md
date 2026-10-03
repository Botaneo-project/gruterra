# Tester Gruterra sous Windows

Ce guide permet de découvrir l’interface avec des données fictives, sans capteur, Raspberry ni compte Netatmo.

1. Ouvrez https://github.com/Botaneo-project/gruterra puis **Code → Download ZIP**. Décompressez le dossier.
2. Installez Python pour Windows depuis https://www.python.org/downloads/windows/ avec Tkinter et le lanceur `py`.
3. Ouvrez PowerShell dans le dossier décompressé contenant `requirements.txt` et exécutez :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe _app\lancer_demo.py
```

Pour les prochains lancements, seule la dernière commande est nécessaire. Aucun script d’activation PowerShell n’est requis.

La démonstration utilise `_app/data/demo/plantes_demo.db` et sa propre configuration. Les collectes automatiques au démarrage sont désactivées en démo. Les boutons de synchronisation ne simulent pas de capteurs : n’en lancez pas pour ce premier essai.

À explorer en priorité :

- **Crassula démo** : historique riche sur dix jours, deux cycles d’arrosage, une session fractionnée 40 + 55 ml, repères 24 h / 48 h et pic de lumière lié à une sortie balcon.
- **Historique** : sélection d’une journée, graphique lumière, comparaison de cycles d’arrosage et synthèse copiable pour analyse.
- **Cactus balcon démo** : plante sans capteur, avec arrosage manuel et rappel futur.
- **Pothos démo** : exemple d’ancien capteur conservé, utile pour vérifier l’état “ancien capteur”.
- **Monstera démo** : plante suivie avec des valeurs plus régulières pour comparer avec la Crassula.

Vous pouvez modifier les données fictives. Pour recommencer avec une démo propre, fermez Gruterra puis lancez :

```powershell
.\.venv\Scripts\python.exe _app\creer_base_demo.py
```

Cette commande réinitialise la base de démonstration. Ne transmettez aucune base personnelle ni configuration contenant des identifiants.

Pour un retour utile, indiquez l’écran concerné, l’action effectuée, ce que vous attendiez et ce qui s’est produit. Ajoutez une capture sans données personnelles si nécessaire. Le dépôt public permet de consulter et télécharger le projet.