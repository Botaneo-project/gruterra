# Tester Gruterra sous Windows

Ce guide permet de découvrir l’interface avec des données fictives, sans capteur, Raspberry ni compte Netatmo.

1. Acceptez l’invitation GitHub et connectez-vous avec le compte invité.
2. Ouvrez https://github.com/Gruterra-project/botaneo puis **Code → Download ZIP**. Décompressez le dossier.
3. Installez Python pour Windows depuis https://www.python.org/downloads/windows/ avec Tkinter et le lanceur `py`.
4. Ouvrez PowerShell dans le dossier décompressé contenant `requirements.txt` et exécutez :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe _app\lancer_demo.py
```

Pour les prochains lancements, seule la dernière commande est nécessaire. Aucun script d’activation PowerShell n’est requis.

La démonstration utilise `_app/data/demo/plantes_demo.db` et sa propre configuration. Les collectes automatiques au démarrage sont désactivées en démo. Les boutons de synchronisation ne simulent pas de capteurs : n’en lancez pas pour ce premier essai.

À explorer : les fiches des plantes, leurs historiques et graphiques, les arrosages et le journal. Vous pouvez modifier les données fictives. Pour recommencer, fermez Gruterra puis lancez :

```powershell
.\.venv\Scripts\python.exe _app\creer_base_demo.py
```

Cette commande réinitialise la base de démonstration. Ne transmettez aucune base personnelle ni configuration contenant des identifiants.

Pour un retour utile, indiquez l’écran concerné, l’action effectuée, ce que vous attendiez et ce qui s’est produit. Ajoutez une capture sans données personnelles si nécessaire. L’accès GitHub en lecture seule permet de consulter et télécharger le projet.
