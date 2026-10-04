# Publier une release Gruterra pour l’auto-update

Ce guide sert à publier une archive officielle que le bouton `Update` de Gruterra pourra vérifier puis appliquer.

## 1. Préparer l’archive locale

Depuis le dossier du projet :

```powershell
py prepare_release.py
```

Le script refuse de travailler si Git contient des changements non validés. C’est volontaire : l’archive doit correspondre exactement au code publié.

Le résultat est créé dans `_dist/` :

- `gruterra-<version>.zip` : archive à envoyer dans GitHub Release ;
- `gruterra-<version>-release-info.txt` : SHA256 et lignes à reporter dans `version_manifest.json` ;
- `version_manifest-<version>-ready.json` : manifeste complet prêt à copier après publication de la release.

Le dossier `_dist/` est ignoré par Git.

## 2. Créer la release GitHub

Sur GitHub :

1. Ouvrir le dépôt Gruterra.
2. Aller dans `Releases`.
3. Créer une nouvelle release.
4. Utiliser un tag du type `v0.1.3-dev` ou `v0.1.4`.
5. Joindre l’archive ZIP générée dans `_dist/`.
6. Publier la release.

## 3. Activer l’auto-update

Après publication, modifier `version_manifest.json` avec les valeurs indiquées dans le fichier `release-info` :

```json
{
  "archive_url": "https://github.com/Botaneo-project/gruterra/releases/download/v0.1.3-dev/gruterra-0.1.3-dev.zip",
  "sha256": "SHA256_DE_L_ARCHIVE",
  "mise_a_jour_automatique": true
}
```

Puis lancer :

```powershell
py audit_botaneo.py
git add -- version_manifest.json
git commit -m "Activer auto update version <version>"
git push origin main
```

## 4. Annoncer la release sur Discord

Si le bot Gruterra tourne, lancer dans Discord :

`	ext
!release_gruterra
`

La commande publie un message dans #changelog si le salon existe, sinon dans #announcements ou #useful-links.

## 5. Vérifier côté application

Dans Gruterra :

1. Ouvrir `À propos`.
2. Cliquer `Vérifier les mises à jour`.
3. Cliquer `Update` pour simuler.
4. Utiliser `Appliquer update` seulement si le diagnostic est cohérent.

## Sécurité

L’update reste bloqué si :

- `mise_a_jour_automatique` vaut `false` ;
- `archive_url` est vide ;
- le SHA256 est absent ou invalide ;
- les protections locales ne sont pas détectées.

Les données utilisateur sont préservées : base locale, configuration privée, sauvegardes, historique, dossier de données et token Discord local.
