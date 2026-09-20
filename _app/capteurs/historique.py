"""Lecture historique Mi Flora sans effacement.

Ce module ne lance aucune commande de suppression. Il lit le compteur,
récupère les entrées annoncées par le capteur et décode les mesures quand
la trame est exploitable.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import struct

CONTROL = '00001a10-0000-1000-8000-00805f9b34fb'
DATA = '00001a11-0000-1000-8000-00805f9b34fb'
TIME = '00001a12-0000-1000-8000-00805f9b34fb'


def decoder_entree_historique(raw):
    """Décode une entrée historique brute de 16 octets."""

    if len(raw) != 16:
        raise ValueError('Entrée historique trop courte ou trop longue')

    if raw == bytes([0xff]) * 16:
        raise ValueError('Entrée historique vide')

    timestamp_capteur = struct.unpack('<I', raw[0:4])[0]
    temperature = struct.unpack('<h', raw[4:6])[0] / 10
    luminosite = struct.unpack('<I', raw[7:11])[0]
    humidite = raw[11]
    conductivite = struct.unpack('<H', raw[12:14])[0]

    if not -20 <= temperature <= 60:
        raise ValueError(f'Température historique invalide : {temperature}')

    if not 0 <= humidite <= 100:
        raise ValueError(f'Humidité historique invalide : {humidite}')

    return {
        'timestamp_capteur': timestamp_capteur,
        'temperature': temperature,
        'luminosite': luminosite,
        'humidite': humidite,
        'conductivite': conductivite,
        'raw_hex': raw.hex(),
        'raw_length': len(raw)
    }


def reconstruire_date_mesure(timestamp_capteur, horloge_reference):
    """Reconstruit une date UTC à partir de l'horloge interne du capteur."""

    if not horloge_reference:
        return None

    secondes_capteur = horloge_reference.get('device_seconds')
    pc_apres = horloge_reference.get('pc_after_utc')

    if secondes_capteur is None or not pc_apres:
        return None

    try:
        pc_dt = datetime.fromisoformat(pc_apres)
        if pc_dt.tzinfo is None:
            pc_dt = pc_dt.replace(tzinfo=timezone.utc)
        age_secondes = int(secondes_capteur) - int(timestamp_capteur)
    except Exception:
        return None

    if age_secondes < 0:
        return None

    return (pc_dt - timedelta(seconds=age_secondes)).astimezone(timezone.utc).isoformat(timespec='seconds')


async def lire_historique(client, adresse, start_index=0, max_entries=None, history_count=None, clock_reference=None):
    # A appeler au début d'une connexion, avant la mesure directe.
    async def horloge():
        before = datetime.now(timezone.utc).isoformat(timespec='seconds')
        raw = await client.read_gatt_char(TIME)
        after = datetime.now(timezone.utc).isoformat(timespec='seconds')
        secondes = None
        if len(raw) >= 4:
            secondes = struct.unpack('<I', raw[:4])[0]
        return {
            'pc_before_utc': before,
            'pc_after_utc': after,
            'raw_hex': raw.hex(),
            'device_seconds': secondes
        }

    export = {
        'address': adresse,
        'entries': [],
        'reading_mode': 'count_limited',
        'batch_size': 10,
        'start_index': start_index,
        'max_entries': max_entries
    }
    export['clock_before'] = clock_reference or await horloge()

    count = history_count
    if count is None:
        await client.write_gatt_char(CONTROL, bytes([0xA0, 0, 0]), response=True)
        await asyncio.sleep(.5)
        raw_count = await client.read_gatt_char(DATA)
        if len(raw_count) < 2:
            raise ValueError('Compteur historique invalide')
        count = int.from_bytes(raw_count[:2], 'little')
    if count > 2000:
        raise ValueError('Compteur historique inattendu')
    export['history_count'] = count

    end_index = count
    if max_entries is not None:
        end_index = min(count, start_index + max_entries)
    export['end_index'] = end_index

    erreurs = []
    for index in range(start_index, end_index):
        try:
            if index > start_index and (index - start_index) % 10 == 0:
                await asyncio.sleep(1.5)
            await client.write_gatt_char(CONTROL, bytes([0xA1, index & 255, index >> 8]), response=True)
            await asyncio.sleep(.35)
            raw = await client.read_gatt_char(DATA)
            if len(raw) != 16 or raw == bytes([0xff]) * 16:
                raise ValueError(f'Entrée historique {index} invalide')
            entree = decoder_entree_historique(raw)
            entree['index'] = index
            entree['date_heure_utc'] = reconstruire_date_mesure(
                entree['timestamp_capteur'],
                export.get('clock_before')
            )
            export['entries'].append(entree)
        except Exception as erreur:
            erreurs.append({
                'index': index,
                'type': type(erreur).__name__,
                'message': str(erreur)
            })
            break

    try:
        export['clock_after'] = await horloge()
    except Exception as erreur:
        export['clock_after_error'] = {
            'type': type(erreur).__name__,
            'message': str(erreur)
        }

    export['errors'] = erreurs
    export['status'] = 'complete' if not erreurs and end_index >= count else 'partial'
    return export
