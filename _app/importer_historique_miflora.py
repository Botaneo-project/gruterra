"""Import ponctuel d'un export horodate, sans modification du schema.

Par defaut : verification seulement. --appliquer cree une sauvegarde SQLite
puis importe en une transaction. Les dates sont stockees en heure locale du PC,
comme les mesures existantes. Precision de l'horloge Mi Flora : quelques secondes.
"""
import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def preparer(export):
    if export.get('status') != 'complete' or export.get('reading_mode', 'count_limited') != 'count_limited':
        raise ValueError('Export incomplet ou diagnostic : import refuse.')
    epochs = []
    device_seconds = None
    for name in ('clock_before', 'clock_after'):
        clock = export[name]
        before = datetime.fromisoformat(clock['pc_before_utc'])
        after = datetime.fromisoformat(clock['pc_after_utc'])
        raw = bytes.fromhex(clock['raw_hex'])
        if before.tzinfo is None or after.tzinfo is None or len(raw) != 4:
            raise ValueError('Repere temporel invalide.')
        if not 0 <= (after-before).total_seconds() <= 2:
            raise ValueError('Lecture de l horloge trop lente.')
        seconds = int.from_bytes(raw, 'little')
        if name == 'clock_before':
            device_seconds = seconds
        elif seconds < device_seconds:
            raise ValueError('Horloge du capteur remise a zero.')
        epochs.append(before + (after-before)/2 - timedelta(seconds=seconds))
    if abs((epochs[1]-epochs[0]).total_seconds()) > 15:
        raise ValueError('Reperes temporels incoherents.')
    epoch = epochs[0]
    rows = []
    seen = set()
    for entry in export['entries']:
        raw = bytes.fromhex(entry['raw_hex'])
        if len(raw) != 16 or raw == b'\xff'*16:
            raise ValueError('Trame historique invalide.')
        seconds = int.from_bytes(raw[:4], 'little')
        temperature = int.from_bytes(raw[4:6], 'little', signed=True)/10
        light = int.from_bytes(raw[7:11], 'little')
        moisture = raw[11]
        conductivity = int.from_bytes(raw[12:14], 'little')
        if not 0 <= seconds <= device_seconds or not -20 <= temperature <= 60 or not 0 <= moisture <= 100:
            raise ValueError('Valeurs historiques invalides.')
        timestamp = (epoch + timedelta(seconds=seconds)).astimezone().replace(tzinfo=None).isoformat(timespec='seconds')
        if seconds in seen:
            raise ValueError('Plusieurs entrees pour le meme temps interne.')
        seen.add(seconds)
        rows.append((timestamp, temperature, moisture, light, conductivity, raw.hex()))
    if not rows:
        raise ValueError('Aucune mesure.')
    return sorted(rows)


def importer(export_path, db_path, appliquer=False, sauvegarder=True):
    export = export_path if isinstance(export_path, dict) else json.loads(Path(export_path).read_text(encoding='utf-8-sig'))
    rows = preparer(export)
    db_path = Path(db_path).resolve(strict=True)
    mode = 'rw' if appliquer else 'ro'
    conn = sqlite3.connect(db_path.as_uri() + '?mode=' + mode, uri=True, timeout=10)
    backup_path = None
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        if appliquer:
            if sauvegarder:
                backup_path = db_path.with_name(db_path.stem + '_avant_import_historique_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.db')
                with sqlite3.connect(backup_path) as backup:
                    conn.backup(backup)
            conn.execute('BEGIN IMMEDIATE')
        capteurs = conn.execute('SELECT id, plante_id, actif FROM capteurs WHERE UPPER(adresse_ble)=?', (export['address'].upper(),)).fetchall()
        # Pas d'inference d'affectation historique en presence de deplacements.
        if len(capteurs) != 1 or capteurs[0][1] is None:
            raise ValueError('Affectation a une plante ambigue ou absente.')
        capteur_id = capteurs[0][0]
        before = conn.execute('SELECT COUNT(*) FROM mesures').fetchone()[0]
        pending = []
        for row in rows:
            # Une meme trame a une date voisine est le meme releve. La marge
            # absorbe l'imprecision de l'horloge entre deux recuperations.
            duplicate = conn.execute('''SELECT 1 FROM mesures
                WHERE capteur_id=? AND
                ((donnees_brutes=? AND ABS(julianday(date_heure)-julianday(?))*86400 < 120)
                 OR date_heure=?) LIMIT 1''', (capteur_id,row[5],row[0],row[0])).fetchone()
            if not duplicate:
                pending.append((*row, capteur_id))
        if appliquer:
            conn.executemany('''INSERT INTO mesures
                (date_heure,temperature,humidite,luminosite,conductivite,donnees_brutes,capteur_id)
                VALUES (?,?,?,?,?,?,?)''', pending)
            if conn.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Relations de la base invalides : annulation.')
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Integrite de la base invalide : annulation.')
            conn.commit()
        return {'applique': appliquer, 'avant': before, 'ajoutees' if appliquer else 'a_importer': len(pending), 'deja_presentes': len(rows)-len(pending), 'premiere_date_locale': rows[0][0], 'derniere_date_locale': rows[-1][0], 'sauvegarde': str(backup_path) if backup_path else None}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--base', type=Path, default=Path(__file__).resolve().parent/'plantes.db')
    parser.add_argument('--appliquer', action='store_true')
    args = parser.parse_args()
    print(json.dumps(importer(args.export, args.base, args.appliquer), indent=2, ensure_ascii=False))
