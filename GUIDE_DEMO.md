# Tester Gruterra sous Windows

Ce guide permet de découvrir l’interface avec des données fictives, sans capteur Mi Flora, Raspberry Pi ni compte Netatmo.

## 1. Télécharger le projet

Ouvrez le dépôt GitHub :

```text
https://github.com/Botaneo-project/gruterra
```

Puis utilisez **Code → Download ZIP** et décompressez le dossier où vous voulez : Téléchargements, Documents, bureau ou autre dossier local.

## 2. Installer Python

Installez Python pour Windows depuis :

```text
https://www.python.org/downloads/windows/
```

Utilisez une installation standard avec Tkinter et le lanceur `py`.

## 3. Lancer la démo

Ouvrez PowerShell dans le dossier décompressé contenant `requirements.txt`, puis lancez :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Lancer_Demo.py
```

Pour les prochains lancements, utilisez `Lancer_Demo.py` pour la démo ou `Lancer_Gruterra.py` pour commencer une utilisation réelle vierge.

Aucun script d’activation PowerShell n’est requis.

## 4. Ce que la démo utilise

**Démo** : ouvre Gruterra avec des plantes fictives et des mesures d’exemple déjà présentes. **Utilisation réelle** : ouvre Gruterra avec votre future base locale, sans données fictives. La démo utilise :

```text
_app/data/demo/plantes_demo.db
```

Elle utilise aussi sa propre configuration de démonstration. Les collectes automatiques au démarrage sont désactivées en mode démo. Les boutons de synchronisation ne simulent pas de capteurs physiques, donc ne les utilisez pas pour le premier essai.

## 5. À explorer en priorité

- **Crassula démo** : historique riche sur plusieurs jours, cycles d’arrosage, repères 24 h / 48 h et pic lumineux lié à une sortie balcon.
- **Historique** : sélection d’une journée, graphique lumière, comparaison de cycles d’arrosage et synthèse copiable pour analyse.
- **Cactus balcon démo** : plante sans capteur actif, avec arrosage manuel et rappel futur.
- **Pothos démo** : exemple d’ancien capteur conservé.
- **Monstera démo** : mesures plus régulières, utiles pour comparer avec la Crassula.

## 6. Réinitialiser la base de démonstration

Vous pouvez modifier les données fictives. Pour recommencer avec une base démo propre, fermez Gruterra puis lancez :

```powershell
.\.venv\Scripts\python.exe _app\creer_base_demo.py
```

## 7. Retour utile

Un retour utile indique :

- l’écran utilisé ;
- l’action effectuée ;
- ce que vous attendiez ;
- ce qui s’est produit ;
- une capture sans information personnelle si nécessaire.

Ne transmettez aucune base personnelle ni configuration contenant des identifiants.

Version anglaise : [GUIDE_DEMO_EN.md](GUIDE_DEMO_EN.md).