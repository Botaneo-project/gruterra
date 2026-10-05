"""Préparation des mises à jour Gruterra, sans application automatique.

Ce module ne télécharge rien et ne modifie pas le programme. Il sert à préparer
un futur auto-upgrade en listant clairement ce qui doit être préservé avant
toute mise à jour : base locale, configuration privée, secrets, préférences et
sauvegardes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ELEMENTS_PERSONNELS = (
    "plantes.db",
    "_config",
    "_security_backups",
    "_historique",
    "_app/data",
)

FICHIERS_CONFIG_EXEMPLE = (
    "botaneo.local.example.json",
    "netatmo_config.example.json",
    "email.local.example.json",
)

VERSION_LOCALE_DEFAUT = "0.1.0-dev"
FICHIER_VERSION_LOCALE = "VERSION"
MANIFEST_DISTANT_DEFAUT = "https://raw.githubusercontent.com/Botaneo-project/gruterra/main/version_manifest.json"
TIMEOUT_MANIFEST_SECONDES = 5


@dataclass(frozen=True)
class ElementPersonnel:
    chemin: str
    existe: bool
    type: str
    raison: str


def detecter_element_personnel(racine, chemin_relatif) -> ElementPersonnel:
    racine = Path(racine)
    chemin = racine / chemin_relatif
    if chemin.is_dir():
        type_element = "dossier"
    elif chemin.is_file():
        type_element = "fichier"
    else:
        type_element = "absent"
    raisons = {
        "plantes.db": "base SQLite personnelle",
        "_config": "configuration privée, tokens et secrets locaux",
        "_security_backups": "sauvegardes locales de sécurité",
        "_historique": "anciens fichiers conservés localement",
        "_app/data": "suivis locaux, caches et états runtime",
    }
    return ElementPersonnel(
        chemin=chemin_relatif,
        existe=chemin.exists(),
        type=type_element,
        raison=raisons.get(chemin_relatif, "donnée locale à préserver"),
    )


def construire_separation_programme_donnees(racine) -> dict:
    racine = Path(racine)
    return {
        "programme_actuel": [
            "_app",
            "raspberry",
            "tests",
            "requirements.txt",
            "README.md",
            "TODO.md",
        ],
        "donnees_utilisateur_actuelles": list(ELEMENTS_PERSONNELS),
        "donnees_utilisateur_futures": [
            "dossier utilisateur Gruterra dédié",
            "base SQLite réelle",
            "configuration privée",
            "secrets et tokens",
            "préférences locales",
            "sauvegardes et caches runtime",
        ],
        "principe": "le programme pourra être remplacé, les données utilisateur devront rester conservées",
        "racine_actuelle": str(racine),
    }


def lire_version_locale(racine) -> str:
    """Retourne la version installée, incluse dans les archives de release."""

    chemin = Path(racine) / FICHIER_VERSION_LOCALE
    try:
        version = chemin.read_text(encoding="utf-8").strip()
    except OSError:
        return VERSION_LOCALE_DEFAUT
    return version or VERSION_LOCALE_DEFAUT


def construire_plan_mise_a_jour(racine, verifier_distant=False) -> dict:
    """Construit un plan de mise à jour en lecture seule."""

    racine = Path(racine)
    version_locale = lire_version_locale(racine)
    elements = [detecter_element_personnel(racine, item) for item in ELEMENTS_PERSONNELS]
    exemples = [str(item) for item in FICHIERS_CONFIG_EXEMPLE if (racine / item).exists()]
    plan = {
        "mode": "préparation uniquement",
        "racine": str(racine),
        "separation_programme_donnees": construire_separation_programme_donnees(racine),
        "elements_personnels": elements,
        "fichiers_exemple": exemples,
        "statut_version": construire_statut_version(
            version_locale=version_locale,
            chemin_manifest_local=racine / "version_manifest.json",
            url_manifest_distant=MANIFEST_DISTANT_DEFAUT,
            verifier_distant=verifier_distant,
        ),
        "actions_avant_update": [
            "fermer Gruterra",
            "lancer une sauvegarde locale",
            "vérifier que la base SQLite personnelle est sauvegardée",
            "préserver _config et les fichiers *.local.json",
            "appliquer la mise à jour seulement après validation explicite",
        ],
        "actions_interdites_sans_validation": [
            "supprimer la base réelle",
            "écraser _config",
            "supprimer les sauvegardes locales",
            "lancer un git reset ou un nettoyage destructeur",
        ],
    }
    plan["verification"] = verifier_plan_mise_a_jour(plan)
    return plan


def verifier_plan_mise_a_jour(plan) -> dict:
    """Vérifie si le plan contient les protections minimales avant une future mise à jour.

    Cette vérification reste informative : elle ne lance aucune mise à jour et ne
    modifie aucun fichier. Elle sert à éviter de présenter comme prêt un poste où
    la base, la configuration privée ou les sauvegardes locales ne sont pas
    identifiables.
    """

    elements = {element.chemin: element for element in plan.get("elements_personnels", [])}
    avertissements = []
    bloquants = []

    separation = plan.get("separation_programme_donnees", {})
    if not separation.get("programme_actuel") or not separation.get("donnees_utilisateur_actuelles"):
        bloquants.append("séparation programme/données absente du plan")
    else:
        donnees_attendues = set(ELEMENTS_PERSONNELS)
        donnees_plan = set(separation.get("donnees_utilisateur_actuelles", []))
        manquantes = sorted(donnees_attendues - donnees_plan)
        if manquantes:
            bloquants.append("données personnelles absentes du plan : " + ", ".join(manquantes))

    base = elements.get("plantes.db")
    if not base or not base.existe or base.type != "fichier":
        bloquants.append("base plantes.db introuvable")

    config = elements.get("_config")
    if not config or not config.existe or config.type != "dossier":
        avertissements.append("dossier _config absent ou non détecté")

    sauvegardes = elements.get("_security_backups")
    if not sauvegardes or not sauvegardes.existe:
        avertissements.append("aucune sauvegarde locale _security_backups détectée")

    statut = "pret"
    if avertissements:
        statut = "prudence"
    if bloquants:
        statut = "bloque"

    return {
        "statut": statut,
        "pret": statut == "pret",
        "application_autorisee": False,
        "bloquants": bloquants,
        "avertissements": avertissements,
        "message": message_verification_plan(statut, bloquants, avertissements),
    }


def message_verification_plan(statut, bloquants, avertissements):
    if statut == "pret":
        return "Protections principales détectées ; mise à jour toujours soumise à validation explicite."
    if statut == "bloque":
        return "Mise à jour à bloquer : " + ", ".join(bloquants)
    return "Mise à jour possible seulement avec prudence : " + ", ".join(avertissements)


def resume_court_mise_a_jour(plan) -> str:
    verification = plan.get("verification", {})
    elements = plan.get("elements_personnels", [])
    presents = [element.chemin for element in elements if element.existe]
    absents = [element.chemin for element in elements if not element.existe]
    statut = verification.get("statut", "inconnu")

    statut_version = plan.get("statut_version", {})
    lignes = [
        "Mise à jour future : préparation uniquement",
        f"- état du plan : {statut}",
        f"- contrôle : {verification.get('message', 'non effectué')}",
        f"- version : {statut_version.get('message', 'vérification non configurée')}",
    ]
    if statut_version.get("notes"):
        lignes.append(f"- notes : {statut_version.get('notes')}")
    if statut_version.get("url"):
        lignes.append(f"- lien informatif : {statut_version.get('url')}")
    lignes.extend([
        "- application automatique : désactivée",
        "- données personnelles : conservées séparément du programme",
        "- fichiers secrets : noms détaillés non affichés",
        "- à préserver : " + (", ".join(presents) if presents else "aucun élément personnel détecté"),
    ])
    if absents:
        lignes.append("- non présents sur ce poste : " + ", ".join(absents))
    lignes.append("- règle : sauvegarde locale et validation explicite avant toute application")
    return "\n".join(lignes)


def construire_diagnostic_mise_a_jour(racine, verifier_distant=False) -> dict:
    """Construit un diagnostic global, lisible par l'interface ou un futur script.

    Le diagnostic reste strictement en lecture seule : il ne télécharge rien, ne
    modifie aucun fichier et n'autorise jamais l'application automatique.
    """

    plan = construire_plan_mise_a_jour(racine, verifier_distant=verifier_distant)
    verification = plan.get("verification", {})
    statut_version = plan.get("statut_version", {})
    elements = plan.get("elements_personnels", [])
    presents = [element.chemin for element in elements if element.existe]
    absents = [element.chemin for element in elements if not element.existe]

    statut_global = "pret_a_verifier"
    if verification.get("statut") == "prudence":
        statut_global = "prudence"
    if verification.get("statut") == "bloque":
        statut_global = "bloque"

    prochaines_actions = [
        "faire une sauvegarde locale",
        "vérifier les données personnelles détectées",
        "relire les notes de version",
        "demander une validation explicite avant toute application",
    ]
    if statut_global == "bloque":
        prochaines_actions.insert(0, "corriger les éléments bloquants avant toute mise à jour")
    elif statut_global == "prudence":
        prochaines_actions.insert(0, "contrôler les avertissements avant de continuer")

    return {
        "statut_global": statut_global,
        "application_autorisee": False,
        "mode": plan.get("mode", "préparation uniquement"),
        "racine": plan.get("racine"),
        "version": statut_version,
        "verification": verification,
        "elements_presents": presents,
        "elements_absents": absents,
        "prochaines_actions": prochaines_actions,
        "resume": resume_court_mise_a_jour(plan),
    }


def libelle_statut_global(statut) -> str:
    libelles = {
        "pret_a_verifier": "Prêt pour vérification manuelle",
        "prudence": "À contrôler avant mise à jour",
        "bloque": "Bloqué tant que les protections manquent",
    }
    return libelles.get(statut, "État inconnu")


def exporter_diagnostic_mise_a_jour_json(diagnostic) -> str:
    """Retourne un rapport JSON lisible, sans écrire de fichier."""

    rapport = {
        "type": "diagnostic_mise_a_jour_botaneo",
        "statut_global": diagnostic.get("statut_global"),
        "mode": diagnostic.get("mode"),
        "application_autorisee": bool(diagnostic.get("application_autorisee", False)),
        "version": diagnostic.get("version", {}),
        "verification": diagnostic.get("verification", {}),
        "elements_presents": list(diagnostic.get("elements_presents", [])),
        "elements_absents": list(diagnostic.get("elements_absents", [])),
        "prochaines_actions": list(diagnostic.get("prochaines_actions", [])),
    }
    return json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True)


def formater_diagnostic_mise_a_jour(diagnostic) -> str:
    statut_global = diagnostic.get('statut_global', 'inconnu')
    lignes = [
        "Diagnostic de mise à jour Gruterra",
        f"État : {libelle_statut_global(statut_global)}",
        f"Code état : {statut_global}",
        f"Mode : {diagnostic.get('mode', 'préparation uniquement')}",
        f"Application automatique autorisée : {'oui' if diagnostic.get('application_autorisee') else 'non'}",
        "",
        diagnostic.get("resume", "Résumé indisponible."),
        "",
        "Prochaines actions :",
    ]
    lignes.extend(f"- {action}" for action in diagnostic.get("prochaines_actions", []))
    return "\n".join(lignes)


def formater_plan_mise_a_jour(plan) -> str:
    lignes = [
        "Plan de mise à jour Gruterra",
        f"Mode : {plan.get('mode', 'préparation')}",
        f"Racine : {plan.get('racine', 'inconnue')}",
        plan.get("statut_version", {}).get("message", "Vérification de version non configurée."),
        plan.get("verification", {}).get("message", "Vérification du plan non effectuée."),
        "",
        "Séparation programme / données :",
        f"- principe : {plan.get('separation_programme_donnees', {}).get('principe', 'à définir')}",
        "- programme remplaçable : " + ", ".join(plan.get("separation_programme_donnees", {}).get("programme_actuel", [])),
        "- données à conserver : " + ", ".join(plan.get("separation_programme_donnees", {}).get("donnees_utilisateur_actuelles", [])),
        "",
        "Éléments personnels à préserver :",
    ]
    for element in plan.get("elements_personnels", []):
        etat = "présent" if element.existe else "absent"
        lignes.append(f"- {element.chemin} · {etat} · {element.raison}")
    lignes.extend(["", "Avant toute mise à jour :"])
    lignes.extend(f"- {action}" for action in plan.get("actions_avant_update", []))
    lignes.extend(["", "Interdit sans validation explicite :"])
    lignes.extend(f"- {action}" for action in plan.get("actions_interdites_sans_validation", []))
    return "\n".join(lignes)


def normaliser_version(version):
    texte = str(version or "").strip().lower()
    if texte.startswith("v"):
        texte = texte[1:]
    suffixe_dev = "dev" in texte or "alpha" in texte or "beta" in texte or "rc" in texte
    principal = texte.split("-")[0]
    morceaux = []
    for part in principal.split("."):
        try:
            morceaux.append(int(part))
        except ValueError:
            chiffres = "".join(car for car in part if car.isdigit())
            morceaux.append(int(chiffres) if chiffres else 0)
    while len(morceaux) < 3:
        morceaux.append(0)
    return tuple(morceaux[:3]), suffixe_dev


def comparer_versions(version_locale, version_distante):
    locale, locale_dev = normaliser_version(version_locale)
    distante, distante_dev = normaliser_version(version_distante)
    if distante > locale:
        statut = "mise_a_jour_disponible"
    elif distante == locale and locale_dev and not distante_dev:
        statut = "version_stable_disponible"
    elif distante == locale:
        statut = "a_jour"
    else:
        statut = "locale_plus_recente"
    return {
        "version_locale": str(version_locale),
        "version_distante": str(version_distante),
        "statut": statut,
        "application_autorisee": False,
        "message": message_version(statut, version_locale, version_distante),
    }


def message_version(statut, version_locale, version_distante):
    if statut == "mise_a_jour_disponible":
        return f"Version distante {version_distante} disponible ; sauvegarde et validation nécessaires avant application."
    if statut == "version_stable_disponible":
        return f"Version stable {version_distante} disponible pour remplacer la version locale {version_locale}."
    if statut == "a_jour":
        return f"Version locale {version_locale} à jour."
    return f"Version locale {version_locale} plus récente que la version distante {version_distante}."


def analyser_manifest_version(donnees, source):
    """Valide un manifeste de version déjà chargé."""

    if not isinstance(donnees, dict):
        return {
            "disponible": False,
            "version": None,
            "source": str(source),
            "message": "Manifeste de version au format invalide.",
        }
    version = donnees.get("version")
    if not version:
        return {
            "disponible": False,
            "version": None,
            "source": str(source),
            "message": "Manifeste de version sans champ version exploitable.",
        }
    return {
        "disponible": True,
        "version": str(version),
        "source": str(source),
        "notes": str(donnees.get("notes", "")),
        "url": str(donnees.get("url", "")),
        "archive_url": str(donnees.get("archive_url", "")),
        "sha256": str(donnees.get("sha256", "")),
        "mise_a_jour_automatique": bool(donnees.get("mise_a_jour_automatique", False)),
        "message": f"Version distante déclarée : {version}",
    }


def lire_manifest_version(chemin_manifest):
    """Lit un manifeste de version local, sans accès réseau."""

    chemin = Path(chemin_manifest)
    if not chemin.exists():
        return {
            "disponible": False,
            "version": None,
            "source": str(chemin),
            "message": "Manifeste de version local absent.",
        }
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        return {
            "disponible": False,
            "version": None,
            "source": str(chemin),
            "message": f"Manifeste de version local illisible : {erreur}",
        }
    return analyser_manifest_version(donnees, chemin)


def lire_manifest_version_distant(url, timeout=TIMEOUT_MANIFEST_SECONDES, ouvreur=urlopen):
    """Lit le manifeste public GitHub avec délai court, sans télécharger d'archive."""

    if not url:
        return {
            "disponible": False,
            "version": None,
            "source": "",
            "message": "URL de manifeste distant non configurée.",
        }
    try:
        requete = Request(str(url), headers={"User-Agent": "Gruterra-update-check/1.0"})
        with ouvreur(requete, timeout=timeout) as reponse:
            contenu = reponse.read(64 * 1024).decode("utf-8")
        donnees = json.loads(contenu)
    except HTTPError as erreur:
        return {
            "disponible": False,
            "version": None,
            "source": str(url),
            "message": f"Manifeste distant indisponible : HTTP {erreur.code}.",
        }
    except (URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError) as erreur:
        return {
            "disponible": False,
            "version": None,
            "source": str(url),
            "message": f"Manifeste distant non vérifié : {erreur}",
        }
    manifest = analyser_manifest_version(donnees, url)
    if manifest.get("disponible"):
        manifest["message"] = f"Version distante GitHub déclarée : {manifest.get('version')}"
    return manifest


def construire_statut_version_depuis_manifest(version_locale, chemin_manifest):
    manifest = lire_manifest_version(chemin_manifest)
    return construire_statut_version_depuis_manifest_charge(version_locale, manifest)


def construire_statut_version_depuis_manifest_charge(version_locale, manifest):
    if not manifest.get("disponible"):
        statut = construire_statut_version_base(version_locale)
        statut["source"] = manifest.get("source")
        statut["message"] = manifest.get("message", statut.get("message"))
        return statut
    statut = comparer_versions(version_locale, manifest.get("version"))
    statut["source"] = manifest.get("source")
    statut["notes"] = manifest.get("notes", "")
    statut["url"] = manifest.get("url", "")
    statut["archive_url"] = manifest.get("archive_url", "")
    statut["sha256"] = manifest.get("sha256", "")
    statut["manifest_auto_update"] = bool(manifest.get("mise_a_jour_automatique", False))
    statut["application_autorisee"] = False
    return statut


def construire_statut_version(version_locale, version_distante=None, chemin_manifest_local=None, url_manifest_distant=None, verifier_distant=False):
    if version_distante:
        return comparer_versions(version_locale, version_distante)

    if verifier_distant and url_manifest_distant:
        manifest = lire_manifest_version_distant(url_manifest_distant)
        if manifest.get("disponible"):
            return construire_statut_version_depuis_manifest_charge(version_locale, manifest)
        if chemin_manifest_local:
            local = lire_manifest_version(chemin_manifest_local)
            statut = construire_statut_version_depuis_manifest_charge(version_locale, local)
            if local.get("disponible"):
                statut["message"] = "Manifeste GitHub non lisible ou dépôt privé ; manifeste local utilisé."
                statut["avertissement_distant"] = manifest.get("message", "vérification distante indisponible")
            else:
                statut["message"] = manifest.get("message", statut.get("message"))
            statut["source_distante"] = manifest.get("source")
            return statut
        statut = construire_statut_version_base(version_locale)
        statut["source"] = manifest.get("source")
        statut["message"] = manifest.get("message", statut.get("message"))
        return statut

    if chemin_manifest_local:
        return construire_statut_version_depuis_manifest(version_locale, chemin_manifest_local)

    return construire_statut_version_base(version_locale)


def construire_statut_version_base(version_locale):
    return {
        "version_locale": str(version_locale),
        "version_distante": None,
        "statut": "verification_non_configuree",
        "application_autorisee": False,
        "message": "Vérification distante non configurée ; aucune mise à jour automatique active.",
    }
