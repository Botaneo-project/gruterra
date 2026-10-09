"""Adaptation pour l'interface de la lecture Mi Flora d'origine."""

from i18n import traduire_courant as _tr
import asyncio

import database
import raspberry_sync
from botaneo_dates import iso_local, iso_utc
from historique_graphique import alimenter_graphiques
from capteurs.miflora import lire_mesure, scanner_avec_progression
from capteurs.historique import lire_historique
from bleak import BleakClient


def message_erreur_historique(erreur):
    nom = type(erreur).__name__
    texte = str(erreur)
    texte_min = texte.lower()
    if "operation was canceled" in texte_min or "opération a été annulée" in texte_min:
        return _tr('sync_miflora_text_18')
    if nom == "BleakError" or "bleak" in nom.lower():
        if "not found" in texte_min or "characteristic" in texte_min:
            return _tr('sync_miflora_text_21')
        return _tr('sync_miflora_text_22').format(v0=texte)
    if "not connected" in texte_min or "disconnected" in texte_min:
        return _tr('sync_miflora_text_24')
    return f"Historique Mi Flora impossible : {nom} · {texte}"


def message_erreur_mesure_bluetooth(erreur):
    nom = type(erreur).__name__
    texte = str(erreur).strip()
    if texte:
        return f"{nom} · {texte}"
    if nom in {"TimeoutError", "CancelledError"}:
        return _tr('sync_miflora_text_34').format(v0=nom)
    return _tr('sync_miflora_text_35').format(v0=nom)


async def importer_historique_capteur_direct_pc(capteur, on_progress=None):
    """Lit la mémoire historique Mi Flora depuis le Bluetooth du PC, sans effacement.

    La lecture est faite en plusieurs passes courtes. Certains Mi Flora ou Windows BLE
    coupent après une vingtaine d'entrées ; on conserve alors ce qui est lu, on attend,
    puis on reprend à l'index suivant.
    """
    try:
        export = {
            'address': capteur[2],
            'entries': [],
            'reading_mode': 'count_limited',
            'status': 'partial',
            'errors': [],
            'passes': []
        }
        vus = set()
        index_depart = 0
        history_count = None
        clock_reference = None
        derniere_erreur = None
        max_passes = 5

        for passe in range(1, max_passes + 1):
            if on_progress:
                on_progress({
                    'phase': 'historique_scan',
                    'passe': passe,
                    'max_passes': max_passes,
                    'index_depart': index_depart,
                    'total_lues': len(export['entries']),
                    'history_count': history_count,
                })
            appareil = None
            for tentative in range(1, 4):
                if on_progress:
                    on_progress({
                        'phase': 'historique_scan_tentative',
                        'passe': passe,
                        'max_passes': max_passes,
                        'tentative': tentative,
                        'tentatives': 3,
                        'index_depart': index_depart,
                        'total_lues': len(export['entries']),
                        'history_count': history_count,
                    })
                appareil = await scanner_avec_progression(capteur[2], duree=20, silencieux=True)
                if appareil is not None:
                    break
                await asyncio.sleep(1.5)

            if appareil is None:
                derniere_erreur = {
                    'index': index_depart,
                    'type': 'Bluetooth',
                    'message': _tr('sync_miflora_text_93')
                }
                break

            if on_progress:
                on_progress({
                    'phase': 'historique_connexion',
                    'passe': passe,
                    'max_passes': max_passes,
                    'index_depart': index_depart,
                    'total_lues': len(export['entries']),
                    'history_count': history_count,
                })

            async with BleakClient(appareil, timeout=45) as client:
                await asyncio.sleep(1.2)
                if on_progress:
                    on_progress({
                        'phase': 'historique_lecture',
                        'passe': passe,
                        'max_passes': max_passes,
                        'index_depart': index_depart,
                        'total_lues': len(export['entries']),
                        'history_count': history_count,
                    })
                part = await lire_historique(
                    client,
                    capteur[2],
                    start_index=index_depart,
                    max_entries=12,
                    history_count=history_count,
                    clock_reference=clock_reference
                )

            if history_count is None:
                history_count = part.get('history_count')
                export['history_count'] = history_count
            if on_progress:
                on_progress({
                    'phase': 'historique_passe_finie',
                    'passe': passe,
                    'max_passes': max_passes,
                    'index_depart': index_depart,
                    'total_lues': len(export['entries']) + len(part.get('entries', [])),
                    'history_count': history_count,
                    'entries_passe': len(part.get('entries', [])),
                    'status': part.get('status'),
                })
            if clock_reference is None:
                clock_reference = part.get('clock_before')
                export['clock_before'] = clock_reference
            if part.get('clock_after'):
                export['clock_after'] = part.get('clock_after')
            if part.get('clock_after_error'):
                export['clock_after_error'] = part.get('clock_after_error')

            nouvelles_passe = 0
            for entree in part.get('entries', []):
                cle = entree.get('raw_hex') or entree.get('index')
                if cle in vus:
                    continue
                vus.add(cle)
                export['entries'].append(entree)
                nouvelles_passe += 1

            erreurs = part.get('errors') or []
            export['passes'].append({
                'passe': passe,
                'start_index': index_depart,
                'entries': len(part.get('entries', [])),
                'new_entries': nouvelles_passe,
                'status': part.get('status'),
                'errors': erreurs
            })

            if part.get('status') == 'complete' or len(export['entries']) >= (history_count or 0):
                export['status'] = 'complete'
                derniere_erreur = None
                break

            if erreurs:
                derniere_erreur = erreurs[0]
                prochain_index = int(erreurs[0].get('index', index_depart)) + 1
            else:
                dernier_index_lu = max((int(e.get('index', index_depart)) for e in part.get('entries', [])), default=index_depart - 1)
                prochain_index = dernier_index_lu + 1

            if prochain_index <= index_depart or prochain_index >= (history_count or prochain_index + 1):
                break
            index_depart = prochain_index
            await asyncio.sleep(5.0)

        export['entries'] = sorted(export['entries'], key=lambda entree: entree.get('index', 0))
        if derniere_erreur:
            export['errors'] = [derniere_erreur]
        elif export.get('status') != 'complete':
            export['errors'] = []
        else:
            export['errors'] = []

        if on_progress:
            on_progress({
                'phase': 'historique_enregistrement',
                'total_lues': len(export['entries']),
                'history_count': history_count,
                'passes': len(export.get('passes', [])),
            })
        import_date = iso_utc()
        resume = database.enregistrer_entrees_historique_miflora(
            capteur[0],
            export,
            import_date
        )

        total_lues = resume['total_lues']
        total_annonce = export.get('history_count') or 0
        passes_txt = f", {len(export.get('passes', []))} passe(s)"
        couverture_txt = _tr('sync_miflora_text_210').format(v0=total_lues, v1=total_annonce) if total_annonce else ""
        message = (
            _tr('sync_miflora_text_212').format(v0=total_lues, v1=passes_txt, v2=couverture_txt, v3=resume['ajoutees'], v4=resume['doublons'])
        )
        graphiques = alimenter_graphiques(export, database.DB_PATH)
        resume['graphiques'] = graphiques
        resume['passes'] = export.get('passes', [])
        message += ' ' + graphiques['message']

        manque = max((total_annonce or 0) - total_lues, 0)
        historique_complet = bool(total_annonce) and manque == 0 and export.get('status') == 'complete'
        historique_etat = 'complet' if historique_complet else 'incomplet'
        if historique_complet:
            message += _tr('sync_miflora_text_225').format(v0=total_lues, v1=total_annonce)
        elif total_annonce:
            message += _tr('sync_miflora_text_227').format(v0=total_lues, v1=total_annonce, v2=manque)
        else:
            message += _tr('sync_miflora_text_229')

        if export.get('status') == 'partial':
            erreurs = export.get('errors') or []
            if erreurs:
                message += _tr('sync_miflora_text_234').format(v0=erreurs[0].get('index'))
            else:
                message += _tr('sync_miflora_text_236')

        return {
            'ok': graphiques['ok'],
            'message': message,
            'resume': resume,
            'collecteur': 'pc',
            'historique_etat': historique_etat,
            'historique_complet': historique_complet,
            'historique_total_lues': total_lues,
            'historique_total_annonce': total_annonce,
            'historique_manque': manque,
            'historique_passes': len(export.get('passes', [])),
            'historique_passes_max': max_passes,
        }

    except Exception as erreur:
        return {
            'ok': False,
            'message': message_erreur_historique(erreur),
            'collecteur': 'pc'
        }


async def importer_historique_capteur(capteur_id=None, force_pc=False, on_progress=None):
    """Lit la mémoire historique Mi Flora et conserve les entrées brutes sans effacement."""

    if capteur_id is None:
        capteur = next((c for c in database.get_capteurs() if c[8]), None)
    else:
        capteur = database.get_capteur(capteur_id)

    if capteur is None:
        return {'ok': False, 'message': _tr('sync_miflora_text_269')}
    if not capteur[8]:
        return {'ok': False, 'message': _tr('sync_miflora_text_271')}
    if not capteur[2]:
        return {'ok': False, 'message': _tr('sync_miflora_text_273')}

    if raspberry_sync.owned(capteur[2]) and not force_pc:
        if on_progress:
            on_progress({'phase': 'historique_raspberry', 'message': _tr('sync_miflora_text_277')})
        resultat = await asyncio.to_thread(raspberry_sync.replay_recent_history)
        resultat.setdefault('historique_etat', 'raspberry_replay')
        if resultat.get('ok') and not resultat.get('history_added', 0):
            export_resultat = await asyncio.to_thread(raspberry_sync.synchronize)
            resultat['message'] = resultat.get('message', '') + ' ' + export_resultat.get('message', '')
            for cle in ('history_added', 'history_duplicates', 'history_undated'):
                resultat[cle] = (resultat.get(cle, 0) or 0) + (export_resultat.get(cle, 0) or 0)
        history_added = resultat.get('history_added', 0) or 0
        history_duplicates = resultat.get('history_duplicates', 0) or 0
        history_undated = resultat.get('history_undated', 0) or 0
        if history_added or history_duplicates or history_undated:
            resultat['historique_message_simplifie'] = (
                _tr('sync_miflora_text_290').format(v0=history_added, v1=history_duplicates, v2=history_undated)
            )
            resultat['message'] = resultat['historique_message_simplifie'] + ' ' + resultat.get('message', '')
            resultat['historique_action'] = 'donnees_recues'
        else:
            resultat['historique_message_simplifie'] = (
                _tr('sync_miflora_text_298')
            )
            resultat['message'] = resultat['historique_message_simplifie'] + ' ' + resultat.get('message', '')
            resultat['historique_action'] = 'rien_de_nouveau'
        return resultat

    return await importer_historique_capteur_direct_pc(capteur, on_progress=on_progress)


def importer_historique_capteur_sync(capteur_id=None, force_pc=False, on_progress=None):
    return asyncio.run(importer_historique_capteur(capteur_id, force_pc=force_pc, on_progress=on_progress))


async def synchroniser_capteur(capteur_id=None):
    if capteur_id is None:
        capteur = next((c for c in database.get_capteurs() if c[8]), None)
    else:
        capteur = database.get_capteur(capteur_id)
    if capteur is None:
        return {'ok': False, 'message': _tr('sync_miflora_text_269')}
    if not capteur[8]:
        return {'ok': False, 'message': _tr('sync_miflora_text_271')}
    if not capteur[2]:
        return {'ok': False, 'message': _tr('sync_miflora_text_273')}
    if raspberry_sync.owned(capteur[2]):
        return await asyncio.to_thread(raspberry_sync.synchronize)

    try:
        temperature, humidite, luminosite, conductivite, brut = await lire_mesure(
            capteur[2], silencieux=True
        )
    except Exception as erreur:
        return {'ok': False, 'message': _tr('sync_miflora_text_332').format(v0=message_erreur_mesure_bluetooth(erreur))}
    date = iso_local()
    try:
        database.enregistrer_mesure(capteur[0], date, temperature, humidite,
                                    luminosite, conductivite, brut)
    except Exception as erreur:
        return {'ok': False, 'message': f'Enregistrement impossible : {erreur}'}
    return {
        'ok': True,
        'message': _tr('sync_miflora_text_341'),
        'mesure': {
            'capteur_id': capteur[0], 'capteur': capteur[1], 'plante_id': capteur[3],
            'date_heure': date, 'temperature': temperature, 'humidite': humidite,
            'luminosite': luminosite, 'conductivite': conductivite,
        },
    }


async def synchroniser_capteur_direct_pc(capteur):
    """Lit le capteur en Bluetooth depuis le PC, même s'il est normalement attribué au Raspberry."""
    try:
        temperature, humidite, luminosite, conductivite, brut = await lire_mesure(
            capteur[2], silencieux=True
        )
    except Exception as erreur:
        return {'ok': False, 'message': _tr('sync_miflora_text_357').format(v0=message_erreur_mesure_bluetooth(erreur))}
    date = iso_local()
    try:
        database.enregistrer_mesure(capteur[0], date, temperature, humidite,
                                    luminosite, conductivite, brut)
    except Exception as erreur:
        return {'ok': False, 'message': _tr('sync_miflora_text_363').format(v0=erreur)}
    return {
        'ok': True,
        'message': _tr('sync_miflora_text_366').format(v0=date, v1=humidite, v2=luminosite),
        'mesure': {
            'capteur_id': capteur[0], 'capteur': capteur[1], 'plante_id': capteur[3],
            'date_heure': date, 'temperature': temperature, 'humidite': humidite,
            'luminosite': luminosite, 'conductivite': conductivite,
        },
    }


def synchroniser_capteur_sync(capteur_id=None):
    return asyncio.run(synchroniser_capteur(capteur_id))


async def synchroniser_capteur_prioritaire(capteur_id=None, reason="post_arrosage"):
    """Mesure prioritaire demandée depuis le PC.

    Si le Raspberry gère normalement le capteur, on lui demande d'abord une collecte.
    Mais une action manuelle depuis le PC doit rester prioritaire : si le Pi ne fournit
    pas tout de suite une nouvelle mesure, le PC tente aussi une lecture Bluetooth directe.
    """
    if capteur_id is None:
        capteur = next((c for c in database.get_capteurs() if c[8]), None)
    else:
        capteur = database.get_capteur(capteur_id)
    if capteur is None:
        return {'ok': False, 'message': _tr('sync_miflora_text_269')}
    if not capteur[8]:
        return {'ok': False, 'message': _tr('sync_miflora_text_271')}
    if not capteur[2]:
        return {'ok': False, 'message': _tr('sync_miflora_text_273')}

    raspberry_resultat = None
    doit_tenter_pc = True
    if raspberry_sync.owned(capteur[2]):
        raspberry_resultat = await asyncio.to_thread(
            raspberry_sync.synchronize,
            None,
            raspberry_sync.transport,
            None,
            True,
            reason
        )
        ajoutees = raspberry_resultat.get('added', 0) or 0
        collect_accepted = raspberry_resultat.get('collect_accepted')
        collect_status = raspberry_resultat.get('collect_status')
        # Si le Pi a déjà fourni au moins une nouvelle mesure, inutile de relire en Bluetooth PC.
        # Sinon, l'action manuelle PC prend la priorité et tente une mesure directe.
        doit_tenter_pc = ajoutees <= 0 or collect_accepted is not True
        if not doit_tenter_pc:
            return {**raspberry_resultat, 'capteur_id': capteur[0], 'nom': capteur[1], 'collecteur': 'raspberry'}

    resultat_pc = await synchroniser_capteur_direct_pc(capteur)
    if raspberry_resultat is None:
        return {**resultat_pc, 'capteur_id': capteur[0], 'nom': capteur[1], 'collecteur': 'pc'}

    message_pi = raspberry_resultat.get('message', _tr('sync_miflora_text_417'))
    message_pc = resultat_pc.get('message', _tr('sync_miflora_text_418'))
    ok = bool(resultat_pc.get('ok')) or bool(raspberry_resultat.get('ok'))
    collecteur = 'pc' if resultat_pc.get('ok') else 'raspberry'
    retour = {**raspberry_resultat, **resultat_pc}
    retour.update({
        'ok': ok,
        'capteur_id': capteur[0],
        'nom': capteur[1],
        'collecteur': collecteur,
        'message': _tr('sync_miflora_text_431').format(v0=message_pi, v1=message_pc),
        'raspberry_result': raspberry_resultat,
        'pc_result': resultat_pc,
    })
    return retour


def synchroniser_capteur_prioritaire_sync(capteur_id=None, reason="post_arrosage"):
    return asyncio.run(synchroniser_capteur_prioritaire(capteur_id, reason))


async def synchroniser_tous(on_progress=None):
    capteurs = [c for c in database.get_capteurs() if c[8]]
    resultats = []
    for index, capteur in enumerate(capteurs, 1):
        if on_progress:
            on_progress(index, len(capteurs), capteur[1])
        try:
            if raspberry_sync.owned(capteur[2]):
                resultat = await synchroniser_capteur_prioritaire(capteur[0], reason="sync_manuelle_pc")
            else:
                resultat = await synchroniser_capteur(capteur[0])
        except Exception:
            resultat = {'ok': False, 'message': _tr('sync_miflora_text_454')}
        resultat.update(capteur_id=capteur[0], nom=capteur[1])
        resultats.append(resultat)
        if index < len(capteurs):
            await asyncio.sleep(2)
    succes = sum(bool(r['ok']) for r in resultats)
    detail = "\n".join(('✓ ' if r['ok'] else '⚠ ') + str(r['nom']) + ' : ' + r['message'] for r in resultats)
    message = _tr('sync_miflora_text_461').format(v0=succes, v1=len(resultats))
    if not capteurs:
        message = _tr('sync_miflora_text_463')
    return {'ok': bool(resultats) and succes == len(resultats),
            'message': message, 'resultats': resultats, 'detail': detail}


def synchroniser_tous_sync(on_progress=None):
    return asyncio.run(synchroniser_tous(on_progress))


async def synchroniser_tous_avec_historique(on_progress=None):
    """Synchronise les capteurs en important d'abord l'historique Mi Flora."""

    capteurs = [c for c in database.get_capteurs() if c[8]]
    resultats = []

    for index, capteur in enumerate(capteurs, 1):
        if on_progress:
            on_progress(index, len(capteurs), capteur[1], "historique")

        try:
            def historique_progress(info, capteur=capteur, index=index, total=len(capteurs)):
                if on_progress:
                    on_progress(index, total, capteur[1], "historique_detail", info)

            historique = await importer_historique_capteur(
                capteur[0],
                force_pc=False,
                on_progress=historique_progress
            )
        except Exception as erreur:
            historique = {
                'ok': False,
                'message': f'Historique Mi Flora impossible : {erreur}'
            }

        await asyncio.sleep(2.5)

        if on_progress:
            on_progress(index, len(capteurs), capteur[1], "mesure")

        try:
            if raspberry_sync.owned(capteur[2]):
                mesure = await synchroniser_capteur_prioritaire(capteur[0], reason="sync_manuelle_pc")
            else:
                mesure = await synchroniser_capteur(capteur[0])
        except Exception:
            mesure = {
                'ok': False,
                'message': _tr('sync_miflora_text_454')
            }

        resultat = {
            'ok': bool(mesure.get('ok')),
            'message': mesure.get('message', _tr('sync_miflora_text_512')),
            'historique_ok': bool(historique.get('ok')),
            'historique_message': historique.get('message', ''),
            'historique_resume': historique.get('resume'),
            'historique_etat': historique.get('historique_etat'),
            'historique_complet': historique.get('historique_complet'),
            'historique_total_lues': historique.get('historique_total_lues'),
            'historique_total_annonce': historique.get('historique_total_annonce'),
            'historique_manque': historique.get('historique_manque'),
            'historique_passes': historique.get('historique_passes'),
            'historique_passes_max': historique.get('historique_passes_max'),
            'mesure': mesure.get('mesure'),
            'collecteur': mesure.get('collecteur'),
            'raspberry_current_added': mesure.get('current_added', 0) or 0,
            'raspberry_current_duplicates': mesure.get('current_duplicates', 0) or 0,
            'raspberry_added': mesure.get('added', 0) or 0,
            'raspberry_duplicates': mesure.get('duplicates', 0) or 0,
            'collect_accepted': mesure.get('collect_accepted'),
            'pending_remaining': mesure.get('pending_remaining'),
            'capteur_id': capteur[0],
            'nom': capteur[1]
        }
        resultats.append(resultat)

        if index < len(capteurs):
            await asyncio.sleep(2)

    succes_mesures = sum(bool(r['ok']) for r in resultats)
    succes_historiques = sum(bool(r.get('historique_ok')) for r in resultats)
    historiques_incomplets = [
        r for r in resultats
        if r.get('historique_total_annonce') and r.get('historique_manque', 0) > 0
    ]
    historiques_complets = [
        r for r in resultats
        if r.get('historique_total_annonce') and r.get('historique_manque', 0) == 0
    ]

    lignes = []
    for resultat in resultats:
        prefixe = '✓ ' if resultat['ok'] else '⚠ '
        lignes.append(prefixe + str(resultat['nom']) + ' : ' + resultat['message'])
        if resultat.get('historique_message'):
            prefixe_historique = '✓ ' if resultat.get('historique_ok') else '⚠ '
            lignes.append(prefixe_historique + str(resultat['nom']) + _tr('sync_miflora_text_556') + resultat['historique_message'])

    if not capteurs:
        message = _tr('sync_miflora_text_463')
    else:
        message = (
            _tr('sync_miflora_text_566').format(v0=succes_mesures, v1=len(resultats), v2=succes_historiques, v3=len(resultats))
        )
        if historiques_incomplets:
            morceaux = []
            for resultat in historiques_incomplets:
                morceaux.append(
                    _tr('sync_miflora_text_573').format(v0=resultat['nom'], v1=resultat.get('historique_total_lues', 0), v2=resultat.get('historique_total_annonce', '?'), v3=resultat.get('historique_manque', 0))
                )
            message += _tr('sync_miflora_text_576') + ' ; '.join(morceaux) + '.'
        elif historiques_complets:
            message += ' Historique complet.'

    return {
        'ok': bool(resultats) and succes_mesures == len(resultats),
        'message': message,
        'resultats': resultats,
        'detail': "\n".join(lignes),
        'historiques_incomplets': historiques_incomplets,
        'historiques_complets': historiques_complets,
    }


def synchroniser_tous_avec_historique_sync(on_progress=None):
    return asyncio.run(synchroniser_tous_avec_historique(on_progress))


