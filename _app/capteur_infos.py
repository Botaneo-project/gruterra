"""Informations observees pendant la connexion existante; aucune operation BLE."""

from i18n import traduire_courant as _tr
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
        logging.getLogger('botaneo.capteurs').warning(_tr('capteur_infos_text_76'))
        return False


def resume_infos(info):
    batterie = str(info['batterie']) + ' %' if info.get('batterie') is not None else _tr('capteur_infos_text_83')
    firmware = info.get('firmware') or _tr('capteur_infos_text_84')
    texte = f'Batterie : {batterie}  ·  Firmware : {firmware}'
    if len(info.get('versions', [])) > 1:
        texte += _tr('capteur_infos_text_85')
    return texte


def details_infos(info):
    def date(key):
        value = info.get(key)
        try:
            return datetime.fromisoformat(value).astimezone().strftime('%d/%m/%Y à %H:%M:%S')
        except (ValueError, TypeError):
            return _tr('capteur_infos_text_97_more')
    lignes = [resume_infos(info), '', _tr('capteur_infos_text_98_more') + (info.get('nom_ble') or _tr('capteur_infos_text_84')),
              _tr('capteur_infos_text_97') + date('batterie_lue_le'),
              _tr('capteur_infos_text_98') + date('firmware_lu_le'),
              _tr('capteur_infos_text_99') + date('derniere_tentative'), '',
              _tr('capteur_infos_text_100')]
    for version in info.get('versions', []):
        lignes.append(version['version'] + ' — ' + version['observe_le'])
    if not info.get('versions'):
        lignes.append(_tr('capteur_infos_text_104'))
    lignes.extend(['', _tr('capteur_infos_text_105'), *info.get('services', []), '',
                   _tr('capteur_infos_text_106'),
                   _tr('capteur_infos_text_107'),
                   _tr('capteur_infos_text_108')])
    return '\n'.join(lignes)
