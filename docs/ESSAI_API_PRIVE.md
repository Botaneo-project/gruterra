# Essai privé application–API

Lanceur distinct de l’interface : `tools/essai_contribution_api_prive.py`. Par défaut, simulation locale sans réseau. Il utilise les vrais modules d’identité, de signature, de validation et de suivi, une identité temporaire et l’exemple entièrement fictif du format v2. Aucun accès à plantes.db. Le répertoire privé est isolé avant import ; les modules déjà chargés provoquent un refus.

Simulation : `py tools\essai_contribution_api_prive.py`

Essai réseau explicite, seulement après accord avec la partie web : `py tools\essai_contribution_api_prive.py --network`

Prérequis : dépendances Gruterra installées, certificat HTTPS valide, profil privé lifecycle-test-60s configuré côté API et fenêtre temporaire de test ouverte. Le jeton privé est saisi de façon masquée ; aucun argument ou fichier de configuration ne le contient. Les redirections sont refusées, les réponses limitées à 1 Mio et les appels à 20 secondes. Aucun test automatique ordinaire ne contacte l’API.

Le parcours teste réception, reprise sans prolongation, échéance locale, expiration HTTP 410, retrait ciblé et refus de recréation. Il tente un retrait global de nettoyage même après échec. Si une opération reste incertaine, la sérialisation locale est conservée et le nettoyage peut nécessiter une intervention serveur ; cette absence de confirmation est affichée, avec seulement l’identifiant technique fictif. La clé temporaire et le suivi sont détruits en fin de processus. Les traces techniques serveur ne sont pas effacées par ce nettoyage.

Le rapport console n’imprime ni clé, ni jeton, ni contenu de contribution. Il ne confirme jamais lui-même la fermeture de l’API : après essai réseau, remettre les services de test hors service et faire confirmer cette fermeture par l’utilisateur. Aucun cron ni partage public n’est activé. La simulation ne valide ni MySQL réel, ni purge, ni restauration Likuid.

## Diagnostic sans secret

Le lanceur affiche chaque étape et chaque contrôle réussi immédiatement. Une réponse indique uniquement son statut HTTP et un code d’erreur figurant dans une liste fermée ; un autre code est affiché « non reconnu ». Une réponse HTML ou JSON invalide conserve le statut HTTP sans afficher son contenu. Un échec local ou réseau sans réponse affiche « HTTP indisponible ». Le premier échec est affiché avant la tentative de nettoyage ; un échec de nettoyage a son propre diagnostic. Aucune exception brute, clé, jeton, en-tête ni contenu n’est imprimé. Ces messages n’identifient pas encore la cause profonde : un rejet lors de la validation applicative est distingué d’un refus HTTP.
