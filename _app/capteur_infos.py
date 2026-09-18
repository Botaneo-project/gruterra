"""Informations observees pendant la connexion existante; aucune operation BLE."""
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import re
from threading import Lock
from botaneo_config import lire_json, ecrire_json

DOSSIER = Path(__file__).resolve().parent / 'data' / 'capteurs'
_lock = Lock()


def chemin(adresse):
    key = hashlib.sha256(str(adresse).strip().upper().encode()).hexdigest()
    return DOSSIER / (key + '.json')


def lire_infos(adresse):
    try:
        info = lire_json(chemin(adresse))
        if info.get('schema') != 1:
            return {}
        for key in ('batterie_lue_le', 'firmware', 'firmware_lu_le', 'derniere_tentative', 'nom_ble'):
            if key in info and not isinstance(info[key], str):
                return {}
        if info.get('batterie') is not None and (type(info['batterie']) is not int or not 0 <= info['batterie'] <= 100):
            return {}
        if not isinstance(info.get('versions', []), list) or not all(isinstance(x, dict) and all(isinstance(x.get(k), str) for k in ('version','observe_le')) for x in info.get('versions', [])):
            return {}
        if not isinstance(info.get('services', []), list) or not all(isinstance(x, str) for x in info.get('services', [])):
            return {}
        return info
    except (RuntimeError, OSError):
        return {}


def decoder_identite(data):
    batterie = data[0] if data and 0 <= data[0] <= 100 else None
    firmware = None
    if len(data) >= 7:
        try:
            version = bytes(data[2:7]).decode('ascii').strip('\x00 ')
            if re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', version):
                firmware = version
        except UnicodeDecodeError:
            pass
    return batterie, firmware


def enregistrer_infos(adresse, data, nom=None, services=None):
    """Une panne du cache ne doit jamais empecher l'acquisition des mesures."""
    try:
        batterie, firmware = decoder_identite(data)
        maintenant = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with _lock:
            info = lire_infos(adresse)
            info.update(schema=1, derniere_tentative=maintenant,
                        lecture_complete=batterie is not None and firmware is not None)
            if batterie is not None:
                info.update(batterie=batterie, batterie_lue_le=maintenant)
            if firmware is not None:
                versions = info.setdefault('versions', [])
                if not versions or versions[-1]['version'] != firmware:
                    versions.append({'version': firmware, 'observe_le': maintenant})
                info['versions'] = versions[-50:]
                info.update(firmware=firmware, firmware_lu_le=maintenant)
            if isinstance(nom, str):
                info['nom_ble'] = ''.join(c for c in nom if c.isprintable())[:80]
            if services is not None:
                info['services'] = sorted(set(str(s) for s in services))
            DOSSIER.mkdir(parents=True, exist_ok=True)
            ecrire_json(chemin(adresse), info)
        return True
    except (OSError, RuntimeError, ValueError, TypeError):
        logging.getLogger('botaneo.capteurs').warning('Cache des informations capteur indisponible.')
        return False


def resume_infos(info):
    batterie = str(info['batterie']) + ' %' if info.get('batterie') is not None else 'non lue'
    firmware = info.get('firmware') or 'non lu'
    texte = f'Batterie : {batterie}  ·  Firmware : {firmware}'
    if len(info.get('versions', [])) > 1:
        texte += '  ·  Changement de version observé'
    return texte


def details_infos(info):
    def date(key):
        value = info.get(key)
        try:
            return datetime.fromisoformat(value).astimezone().strftime('%d/%m/%Y à %H:%M:%S')
        except (ValueError, TypeError):
            return 'jamais'
    lignes = [resume_infos(info), '', 'Nom Bluetooth : ' + (info.get('nom_ble') or 'non lu'),
              'Batterie lue le : ' + date('batterie_lue_le'),
              'Firmware lu le : ' + date('firmware_lu_le'),
              'Dernière tentative : ' + date('derniere_tentative'), '',
              'Versions observées (50 derniers changements au maximum) :']
    for version in info.get('versions', []):
        lignes.append(version['version'] + ' — ' + version['observe_le'])
    if not info.get('versions'):
        lignes.append('Aucune version lue pour le moment.')
    lignes.extend(['', 'Services Bluetooth observés :', *info.get('services', []), '',
                   'Ces informations sont conservées depuis la dernière lecture réussie.',
                   'Une version identique ne garantit pas que le contenu du firmware est identique.',
                   'Aucune recherche de mise à jour ni modification du firmware automatique.'])
    return '\n'.join(lignes)
