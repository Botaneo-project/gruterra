"""Préparation des mises à jour Gruterra, sans application automatique.

Ce module ne télécharge rien et ne modifie pas le programme. Il sert à préparer
un futur auto-upgrade en listant clairement ce qui doit être préservé avant
toute mise à jour : base locale, configuration privée, secrets, préférences et
sauvegardes.
"""
from __future__ import annotations

from i18n import traduire_courant as _tr, traduire_texte_courant as _texte

import json
import os
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


def detecter_contexte_execution(racine) -> dict:
    racine = Path(racine)
    demo_db = racine / "_app" / "data" / "demo" / "plantes_demo.db"
    mode_demo = os.environ.get("BOTANEO_DEMO") == "1" or demo_db.exists()
    return {
        "mode": "démo" if mode_demo else "réel",
        "mode_demo": mode_demo,
        "base_demo": str(demo_db),
        "base_demo_detectee": demo_db.is_file(),
    }


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
        "plantes.db": _tr('personal_sqlite'),
        "_config": _tr('botaneo_update_text_69'),
        "_security_backups": _tr('botaneo_update_text_70'),
        "_historique": _tr('botaneo_update_text_71'),
        "_app/data": _tr('botaneo_update_text_72'),
    }
    return ElementPersonnel(
        chemin=chemin_relatif,
        existe=chemin.exists(),
        type=type_element,
        raison=raisons.get(chemin_relatif, _tr('botaneo_update_text_80')),
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
            _tr('botaneo_update_text_95'),
            _tr('botaneo_update_text_96'),
            _tr('botaneo_update_text_97'),
            _tr('botaneo_update_text_100'),
            _tr('botaneo_update_text_99'),
            _tr('botaneo_update_text_102_more'),
        ],
        "principe": _tr('botaneo_update_text_102'),
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
    contexte = detecter_contexte_execution(racine)
    exemples = [str(item) for item in FICHIERS_CONFIG_EXEMPLE if (racine / item).exists()]
    plan = {
        "mode": "démo" if contexte.get("mode_demo") else "préparation uniquement",
        "contexte_execution": contexte,
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
            _tr('canonical_close_app'),
            _tr('botaneo_update_text_141'),
            _tr('botaneo_update_text_142'),
            _tr('botaneo_update_text_143'),
            _tr('botaneo_update_text_144'),
        ],
        "actions_interdites_sans_validation": [
            _tr('botaneo_update_text_147'),
            _tr('botaneo_update_text_148'),
            _tr('botaneo_update_text_149'),
            _tr('botaneo_update_text_152'),
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
        bloquants.append(_tr('botaneo_update_text_172'))
    else:
        donnees_attendues = set(ELEMENTS_PERSONNELS)
        donnees_plan = set(separation.get("donnees_utilisateur_actuelles", []))
        manquantes = sorted(donnees_attendues - donnees_plan)
        if manquantes:
            bloquants.append(_tr('botaneo_update_text_178') + ", ".join(manquantes))

    contexte = plan.get("contexte_execution", {})
    mode_demo = bool(contexte.get("mode_demo"))

    base = elements.get("plantes.db")
    if mode_demo:
        if not contexte.get("base_demo_detectee"):
            bloquants.append(_tr('botaneo_update_text_186'))
    elif not base or not base.existe or base.type != "fichier":
        avertissements.append(_tr('botaneo_update_text_188'))

    config = elements.get("_config")
    if not config or not config.existe or config.type != "dossier":
        avertissements.append(_tr('botaneo_update_text_192'))

    sauvegardes = elements.get("_security_backups")
    if not mode_demo and (not sauvegardes or not sauvegardes.existe):
        avertissements.append(_tr('botaneo_update_text_196'))

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
        return _tr('botaneo_update_text_216')
    if statut == "bloque":
        return _tr('botaneo_update_text_218') + ", ".join(bloquants)
    return _tr('botaneo_update_text_219') + ", ".join(avertissements)


def resume_court_mise_a_jour(plan) -> str:
    verification = plan.get("verification", {})
    elements = plan.get("elements_personnels", [])
    presents = [element.chemin for element in elements if element.existe]
    absents = [element.chemin for element in elements if not element.existe]
    statut = verification.get("statut", "inconnu")
    contexte = plan.get("contexte_execution", {})

    statut_version = plan.get("statut_version", {})
    lignes = [
        _tr('botaneo_update_text_232') + (_tr('botaneo_update_text_232_more') if contexte.get("mode_demo") else _tr('botaneo_update_text_232_more_more')),
        _tr('botaneo_update_text_233').format(v0=statut),
        _tr('botaneo_update_text_234').format(v0=verification.get('message', _tr('botaneo_update_text_236'))),
        _tr('botaneo_update_text_237').format(v0=statut_version.get('message', _tr('botaneo_update_text_237_more'))),
    ]
    if statut_version.get("notes"):
        lignes.append(_tr('botaneo_update_text_238').format(v0=statut_version.get('notes')))
    if statut_version.get("url"):
        lignes.append(_tr('botaneo_update_text_240').format(v0=statut_version.get('url')))
    if contexte.get("mode_demo"):
        lignes.append(_tr('botaneo_update_text_242') + ("plantes_demo.db" if contexte.get("base_demo_detectee") else _texte("absente")))
    lignes.extend([
        _tr('botaneo_update_text_244'),
        _tr('botaneo_update_text_245'),
        _tr('botaneo_update_text_246'),
        _tr('botaneo_update_text_365') + (", ".join(presents) if presents else _tr('botaneo_update_text_247')),
    ])
    if absents:
        if contexte.get("mode_demo"):
            absents_affiches = [item for item in absents if item not in {"plantes.db", "_security_backups", "_historique"}]
        else:
            absents_affiches = absents
        if absents_affiches:
            lignes.append(_tr('botaneo_update_text_255') + ", ".join(absents_affiches))
    lignes.append(_tr('botaneo_update_text_256'))
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
        _tr('botaneo_update_text_281'),
        _tr('botaneo_update_text_282'),
        _tr('botaneo_update_text_283'),
        _tr('botaneo_update_text_284'),
    ]
    if statut_global == "bloque":
        prochaines_actions.insert(0, _tr('botaneo_update_text_287'))
    elif statut_global == "prudence":
        prochaines_actions.insert(0, _tr('botaneo_update_text_289'))

    return {
        "statut_global": statut_global,
        "application_autorisee": False,
        "mode": plan.get("mode", "préparation uniquement"),
        "racine": plan.get("racine"),
        "version": statut_version,
        "verification": verification,
        "contexte_execution": plan.get("contexte_execution", {}),
        "elements_presents": presents,
        "elements_absents": absents,
        "prochaines_actions": prochaines_actions,
        "resume": resume_court_mise_a_jour(plan),
    }


def libelle_statut_global(statut) -> str:
    libelles = {
        "pret_a_verifier": _tr('botaneo_update_text_308'),
        "prudence": _tr('botaneo_update_text_309'),
        "bloque": _tr('botaneo_update_text_310'),
    }
    return libelles.get(statut, _tr('botaneo_update_text_314'))


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
        _tr('update_apply_result_title'),
        _tr('interface_text_5653').format(v0=libelle_statut_global(statut_global)),
        _tr('botaneo_update_text_337').format(v0=statut_global),
        _tr("mode_value").format(mode=_texte(diagnostic.get("mode", "préparation uniquement"))),
    ]
    contexte = diagnostic.get("contexte_execution", {})
    if contexte.get("mode_demo"):
        lignes.append(_tr('botaneo_update_text_342') + ("plantes_demo.db" if contexte.get("base_demo_detectee") else _texte("absente")))
    lignes.extend([
        _tr('botaneo_update_text_344').format(v0=_tr('botaneo_update_text_346') if diagnostic.get('application_autorisee') else _tr('botaneo_update_text_346_more')),
        "",
        diagnostic.get("resume", _tr('botaneo_update_text_348')),
        "",
        _tr("next_actions"),
    ])
    lignes.extend(f"- {action}" for action in diagnostic.get("prochaines_actions", []))
    return "\n".join(lignes)


def formater_plan_mise_a_jour(plan) -> str:
    lignes = [
        _tr('botaneo_update_text_356'),
        _tr("mode_value").format(mode=_texte(plan.get("mode", "préparation"))),
        _tr("root_value").format(root=plan.get("racine", _texte("inconnue"))),
        plan.get("statut_version", {}).get("message", _tr('botaneo_update_text_361')),
        plan.get("verification", {}).get("message", _tr('botaneo_update_text_362_more')),
        "",
        _tr('botaneo_update_text_362'),
        _tr('botaneo_update_text_365_more').format(v0=plan.get('separation_programme_donnees', {}).get('principe', _tr('botaneo_update_text_365_more_more'))),
        _tr('botaneo_update_text_364') + ", ".join(plan.get("separation_programme_donnees", {}).get("programme_actuel", [])),
        _tr('botaneo_update_text_365') + ", ".join(plan.get("separation_programme_donnees", {}).get("donnees_utilisateur_actuelles", [])),
        "",
        _tr('botaneo_update_text_367'),
    ]
    for element in plan.get("elements_personnels", []):
        etat = _tr('botaneo_update_text_370') if element.existe else _texte("absent")
        lignes.append(f"- {element.chemin} · {etat} · {element.raison}")
    lignes.extend(["", _tr('botaneo_update_text_372')])
    lignes.extend(f"- {action}" for action in plan.get("actions_avant_update", []))
    lignes.extend(["", _tr('botaneo_update_text_374')])
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
        return _tr('botaneo_update_text_419').format(v0=version_distante)
    if statut == "version_stable_disponible":
        return _tr('botaneo_update_text_421').format(v0=version_distante, v1=version_locale)
    if statut == "a_jour":
        return _tr('botaneo_update_text_423').format(v0=version_locale)
    return _tr('botaneo_update_text_424').format(v0=version_locale, v1=version_distante)


def analyser_manifest_version(donnees, source):
    """Valide un manifeste de version déjà chargé."""

    if not isinstance(donnees, dict):
        return {
            "disponible": False,
            "version": None,
            "source": str(source),
            "message": _tr('botaneo_update_text_435'),
        }
    version = donnees.get("version")
    if not version:
        return {
            "disponible": False,
            "version": None,
            "source": str(source),
            "message": _tr('botaneo_update_text_443'),
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
        "message": _tr('botaneo_update_text_454').format(v0=version),
    }


def lire_manifest_version(chemin_manifest):
    """Lit un manifeste de version local, sans accès réseau."""

    chemin = Path(chemin_manifest)
    if not chemin.exists():
        return {
            "disponible": False,
            "version": None,
            "source": str(chemin),
            "message": _tr('botaneo_update_text_467'),
        }
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        return {
            "disponible": False,
            "version": None,
            "source": str(chemin),
            "message": _tr('botaneo_update_text_476').format(v0=erreur),
        }
    return analyser_manifest_version(donnees, chemin)


def lire_manifest_version_distant(url, timeout=TIMEOUT_MANIFEST_SECONDES, ouvreur=urlopen):
    """Lit le manifeste public GitHub avec délai court, sans télécharger d'archive."""

    if not url:
        return {
            "disponible": False,
            "version": None,
            "source": "",
            "message": _tr('botaneo_update_text_489'),
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
            "message": _tr('botaneo_update_text_501').format(v0=erreur.code),
        }
    except (URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError) as erreur:
        return {
            "disponible": False,
            "version": None,
            "source": str(url),
            "message": _tr('botaneo_update_text_508').format(v0=erreur),
        }
    manifest = analyser_manifest_version(donnees, url)
    if manifest.get("disponible"):
        manifest["message"] = _tr('botaneo_update_text_512').format(v0=manifest.get('version'))
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
                statut["message"] = _tr('botaneo_update_text_550')
                statut["avertissement_distant"] = manifest.get("message", _tr('botaneo_update_text_553'))
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
        "message": _tr('botaneo_update_text_573'),
    }
