# Tester Gruterra sous Windows

Ce guide permet de découvrir l’interface avec des données fictives, sans capteur Mi Flora, Raspberry Pi ni compte Netatmo.

## 1. Télécharger le projet

Ouvrez le dépôt GitHub :

```text
https://github.com/Botaneo-project/gruterra
```

Téléchargez de préférence l’archive `gruterra-<version>.zip` dans **Releases**, puis décompressez-la. **Code → Download ZIP** contient le code de développement, qui peut avancer après la dernière release.

## 2. Installer Python

Lancez d’abord `Installer_Gruterra.bat` : il tente d’installer Python automatiquement si nécessaire. En cas de blocage, installez Python pour Windows depuis :

```text
https://www.python.org/downloads/windows/
```

Utilisez une installation standard avec Tkinter et le lanceur `py`.

## 3. Lancer la démo

Méthode simple : double-cliquez sur `Installer_Gruterra.bat`, puis double-cliquez sur `Lancer_Demo.bat`. Si Python manque, l’installateur tente de l’installer automatiquement.

Méthode manuelle : ouvrez PowerShell dans le dossier décompressé contenant `requirements.txt`, puis lancez :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Lancer_Demo.py
```

Pour les prochains lancements, utilisez `Lancer_Demo.bat` pour la démo ou `Lancer_Gruterra.bat` pour commencer une utilisation réelle vierge.

Aucun script d’activation PowerShell n’est requis. Si `.venv` manque, `Lancer_Demo.bat` relance automatiquement `Installer_Gruterra.bat`, puis réessaie la démo. Évitez le double-clic sur `Lancer_Demo.py` sur un PC vierge : Windows peut ne rien afficher si l’association Python n’est pas prête.

## 4. Ce que la démo utilise

**Démo** : ouvre Gruterra avec des plantes fictives et des mesures d’exemple déjà présentes. **Utilisation réelle** : ouvre Gruterra avec votre future base locale, sans données fictives. La démo utilise :

```text
_app/data/demo/plantes_demo.db
```

Elle utilise aussi sa propre configuration de démonstration. La démo ne contient aucune sauvegarde privée, aucun token et aucune configuration personnelle. Les collectes automatiques au démarrage sont désactivées en mode démo. Les boutons de synchronisation ne simulent pas de capteurs physiques, donc ne les utilisez pas pour le premier essai.

## 5. À explorer en priorité

- **Crassula démo** : historique riche sur plusieurs jours, cycles d’arrosage, repères 24 h / 48 h et pic lumineux lié à une sortie balcon.
- **Historique** : sélection d’une journée, graphique lumière, comparaison de cycles d’arrosage et synthèse copiable pour analyse.
- **Cactus balcon démo** : plante sans capteur actif, avec arrosage manuel et rappel futur.
- **Pothos démo** : exemple d’ancien capteur conservé.
- **Monstera démo** : mesures plus régulières, utiles pour comparer avec la Crassula.

## Tester la mise à jour depuis la démo

Le mode démo ne lance pas la vérification automatique au démarrage, afin de ne pas gêner la découverte de l'application. En revanche, le test manuel reste possible dans `Paramètres` : `Vérifier les mises à jour` → `Préparer la mise à jour` → `Appliquer la mise à jour`. Si la version est déjà à jour, aucune installation n’est proposée.

La démo comme l’application réelle n’applique une archive que si le manifeste GitHub officiel contient une URL d'archive, un SHA256 valide et `mise_a_jour_automatique=true`.

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