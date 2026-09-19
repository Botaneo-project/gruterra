"""Adaptation pour l'interface de la lecture Mi Flora d'origine."""
import asyncio
from datetime import datetime, timezone

import database
import raspberry_sync
from historique_graphique import alimenter_graphiques
from capteurs.miflora import lire_mesure, scanner_avec_progression
from capteurs.historique import lire_historique
from bleak import BleakClient


def message_erreur_historique(erreur):
    nom = type(erreur).__name__
    texte = str(erreur)
    texte_min = texte.lower()
    if "operation was canceled" in texte_min or "opération a été annulée" in texte_min:
        return "Historique Mi Flora impossible : Windows a annulé l'accès Bluetooth. Ce n'est pas une annulation manuelle. Attendez la fin complète de la synchronisation, fermez toute autre connexion Bluetooth au capteur, puis réessayez."
    if nom == "BleakError" or "bleak" in nom.lower():
        if "not found" in texte_min or "characteristic" in texte_min:
            return "Historique Mi Flora impossible : accès aux caractéristiques historiques refusé ou pas encore prêt. Fermez toute autre lecture Bluetooth, rapprochez le capteur, puis réessayez."
        return f"Historique Mi Flora impossible : erreur Bluetooth Bleak · {texte}"
    if "not connected" in texte_min or "disconnected" in texte_min:
        return "Historique Mi Flora impossible : le capteur s'est déconnecté pendant la lecture."
    return f"Historique Mi Flora impossible : {nom} · {texte}"


async def importer_historique_capteur(capteur_id=None):
    """Lit la mémoire historique Mi Flora et conserve les entrées brutes sans effacement."""

    if capteur_id is None:
        capteur = next((c for c in database.get_capteurs() if c[8]), None)
    else:
        capteur = database.get_capteur(capteur_id)

    if capteur is None:
        return {'ok': False, 'message': 'Aucun capteur actif disponible.'}
    if not capteur[8]:
        return {'ok': False, 'message': 'Le capteur est désactivé.'}
    if not capteur[2]:
        return {'ok': False, 'message': "Le capteur n'a pas d'adresse Bluetooth."}

    if raspberry_sync.owned(capteur[2]):
        return await asyncio.to_thread(raspberry_sync.synchronize)

    try:
        appareil = None
        for tentative in range(1, 4):
            appareil = await scanner_avec_progression(capteur[2], duree=20, silencieux=True)
            if appareil is not None:
                break
            await asyncio.sleep(1.5)

        if appareil is None:
            return {'ok': False, 'message': 'Mi Flora introuvable pour lecture historique après 3 tentatives.'}

        async with BleakClient(appareil, timeout=45) as client:
            await asyncio.sleep(1.0)
            export = await lire_historique(client, capteur[2])

        import_date = datetime.now(timezone.utc).isoformat(timespec='seconds')
        resume = database.enregistrer_entrees_historique_miflora(
            capteur[0],
            export,
            import_date
        )

        message = (
            f"Historique lu : {resume['total_lues']} entrée(s), "
            f"{resume['ajoutees']} nouvelle(s), "
            f"{resume['doublons']} déjà connue(s)."
        )
        graphiques = alimenter_graphiques(export, database.DB_PATH)
        resume['graphiques'] = graphiques
        message += ' ' + graphiques['message']

        if export.get('status') == 'partial':
            erreurs = export.get('errors') or []
            if erreurs:
                message += f" Lecture interrompue à l'entrée {erreurs[0].get('index')}. Les entrées déjà lues ont été conservées."

        return {
            'ok': graphiques['ok'],
            'message': message,
            'resume': resume
        }

    except Exception as erreur:
        return {
            'ok': False,
            'message': message_erreur_historique(erreur)
        }


def importer_historique_capteur_sync(capteur_id=None):
    return asyncio.run(importer_historique_capteur(capteur_id))


async def synchroniser_capteur(capteur_id=None):
    if capteur_id is None:
        capteur = next((c for c in database.get_capteurs() if c[8]), None)
    else:
        capteur = database.get_capteur(capteur_id)
    if capteur is None:
        return {'ok': False, 'message': 'Aucun capteur actif disponible.'}
    if not capteur[8]:
        return {'ok': False, 'message': 'Le capteur est désactivé.'}
    if not capteur[2]:
        return {'ok': False, 'message': "Le capteur n'a pas d'adresse Bluetooth."}
    if raspberry_sync.owned(capteur[2]):
        return await asyncio.to_thread(raspberry_sync.synchronize)

    try:
        temperature, humidite, luminosite, conductivite, brut = await lire_mesure(
            capteur[2], silencieux=True
        )
    except Exception as erreur:
        return {'ok': False, 'message': f'Erreur Bluetooth : {erreur}'}
    date = datetime.now().isoformat(timespec='seconds')
    try:
        database.enregistrer_mesure(capteur[0], date, temperature, humidite,
                                    luminosite, conductivite, brut)
    except Exception as erreur:
        return {'ok': False, 'message': f'Enregistrement impossible : {erreur}'}
    return {
        'ok': True,
        'message': 'Mesure actuelle enregistrée.',
        'mesure': {
            'capteur_id': capteur[0], 'capteur': capteur[1], 'plante_id': capteur[3],
            'date_heure': date, 'temperature': temperature, 'humidite': humidite,
            'luminosite': luminosite, 'conductivite': conductivite,
        },
    }


def synchroniser_capteur_sync(capteur_id=None):
    return asyncio.run(synchroniser_capteur(capteur_id))


async def synchroniser_tous(on_progress=None):
    capteurs = [c for c in database.get_capteurs() if c[8]]
    resultats = []
    pi_result = None
    if any(raspberry_sync.owned(c[2]) for c in capteurs):
        pi_result = await asyncio.to_thread(raspberry_sync.synchronize)
    for index, capteur in enumerate(capteurs, 1):
        if raspberry_sync.owned(capteur[2]):
            resultats.append({**pi_result, 'capteur_id': capteur[0], 'nom': capteur[1],
                              'historique_ok': pi_result['ok'], 'historique_message': pi_result['message']})
            continue
        if on_progress:
            on_progress(index, len(capteurs), capteur[1])
        try:
            resultat = await synchroniser_capteur(capteur[0])
        except Exception:
            resultat = {'ok': False, 'message': 'Synchronisation du capteur impossible.'}
        resultat.update(capteur_id=capteur[0], nom=capteur[1])
        resultats.append(resultat)
        if index < len(capteurs):
            await asyncio.sleep(2)
    succes = sum(bool(r['ok']) for r in resultats)
    detail = "\n".join(('✓ ' if r['ok'] else '⚠ ') + str(r['nom']) + ' : ' + r['message'] for r in resultats)
    message = f'{succes}/{len(resultats)} capteur(s) synchronisé(s).'
    if not capteurs:
        message = 'Aucun capteur actif. Utilisez Ajouter un capteur.'
    return {'ok': bool(resultats) and succes == len(resultats),
            'message': message, 'resultats': resultats, 'detail': detail}


def synchroniser_tous_sync(on_progress=None):
    return asyncio.run(synchroniser_tous(on_progress))


async def synchroniser_tous_avec_historique(on_progress=None):
    """Synchronise les capteurs en important d'abord l'historique Mi Flora."""

    capteurs = [c for c in database.get_capteurs() if c[8]]
    resultats = []
    pi_result = None
    if any(raspberry_sync.owned(c[2]) for c in capteurs):
        pi_result = await asyncio.to_thread(raspberry_sync.synchronize)

    for index, capteur in enumerate(capteurs, 1):
        if raspberry_sync.owned(capteur[2]):
            resultats.append({**pi_result, 'capteur_id': capteur[0], 'nom': capteur[1],
                              'historique_ok': pi_result['ok'], 'historique_message': pi_result['message']})
            continue
        if on_progress:
            on_progress(index, len(capteurs), capteur[1], "historique")

        try:
            historique = await importer_historique_capteur(capteur[0])
        except Exception as erreur:
            historique = {
                'ok': False,
                'message': f'Historique Mi Flora impossible : {erreur}'
            }

        await asyncio.sleep(2.5)

        if on_progress:
            on_progress(index, len(capteurs), capteur[1], "mesure")

        try:
            mesure = await synchroniser_capteur(capteur[0])
        except Exception:
            mesure = {
                'ok': False,
                'message': 'Synchronisation du capteur impossible.'
            }

        resultat = {
            'ok': bool(mesure.get('ok')),
            'message': mesure.get('message', 'Mesure terminée.'),
            'historique_ok': bool(historique.get('ok')),
            'historique_message': historique.get('message', ''),
            'historique_resume': historique.get('resume'),
            'mesure': mesure.get('mesure'),
            'capteur_id': capteur[0],
            'nom': capteur[1]
        }
        resultats.append(resultat)

        if index < len(capteurs):
            await asyncio.sleep(2)

    succes_mesures = sum(bool(r['ok']) for r in resultats)
    succes_historiques = sum(bool(r.get('historique_ok')) for r in resultats)

    lignes = []
    for resultat in resultats:
        prefixe = '✓ ' if resultat['ok'] else '⚠ '
        lignes.append(prefixe + str(resultat['nom']) + ' : ' + resultat['message'])
        if resultat.get('historique_message'):
            prefixe_historique = '✓ ' if resultat.get('historique_ok') else '⚠ '
            lignes.append(prefixe_historique + str(resultat['nom']) + ' historique : ' + resultat['historique_message'])

    if not capteurs:
        message = 'Aucun capteur actif. Utilisez Ajouter un capteur.'
    else:
        message = (
            f'{succes_mesures}/{len(resultats)} capteur(s) synchronisé(s), '
            f'{succes_historiques}/{len(resultats)} historique(s) importé(s).'
        )

    return {
        'ok': bool(resultats) and succes_mesures == len(resultats),
        'message': message,
        'resultats': resultats,
        'detail': "\n".join(lignes)
    }


def synchroniser_tous_avec_historique_sync(on_progress=None):
    return asyncio.run(synchroniser_tous_avec_historique(on_progress))


