"""Ajout explicite par l'interface, avec sauvegarde SQLite avant insertion."""

from i18n import traduire_courant as _tr
from datetime import datetime
from contextlib import closing
import re
import sqlite3
import database


def ajouter(nom, adresse, plante_id):
    nom = nom.strip()
    adresse = adresse.strip().upper().replace('-', ':')
    if not nom or len(nom) > 80:
        raise ValueError(_tr('ajout_capteur_text_13'))
    if not re.fullmatch(r'(?:[0-9A-F]{2}:){5}[0-9A-F]{2}', adresse):
        raise ValueError('Adresse Bluetooth attendue : AA:BB:CC:DD:EE:FF.')
    if database.get_plante(plante_id) is None:
        raise ValueError(_tr('ajout_capteur_text_17'))
    for capteur in database.get_capteurs():
        if capteur[8] and capteur[2] and capteur[2].upper().replace('-', ':') == adresse:
            raise ValueError(_tr('ajout_capteur_text_20'))
        if capteur[8] and capteur[3] == plante_id:
            raise ValueError(_tr('ajout_capteur_text_22'))
    dossier = database.DB_PATH.parent.parent / '_security_backups' / 'ajouts_capteurs'
    dossier.mkdir(parents=True, exist_ok=True)
    sauvegarde = dossier / ('plantes_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.db')
    with closing(sqlite3.connect(database.DB_PATH.as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(sauvegarde)) as cible:
        source.backup(cible)
        if cible.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError(_tr('ajout_capteur_text_29'))
    return database.ajouter_capteur(nom, adresse, plante_id)
