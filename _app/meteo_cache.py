"""Etat prive/public independant. Une erreur ne rajeunit jamais le cache."""

from i18n import traduire_courant as _tr
from datetime import datetime, timezone
from botaneo_dates import parse_iso
from botaneo_config import lire_json, ecrire_json


class CacheMeteo:
    def __init__(self, path):
        self.path = path
        self.sources = {key: {'data': [], 'date': None, 'cache': True, 'error': False} for key in ('privees','publiques')}
        try:
            raw = lire_json(path)
        except RuntimeError:
            raw = {}
        if not isinstance(raw, dict):
            raw = {}
        for key, source in self.sources.items():
            data = raw.get('stations_' + key, [])
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                source['data'] = data
            date = raw.get('dates', {}).get(key) if isinstance(raw.get('dates'), dict) else None
            if parse_iso(date) is not None:
                source['date'] = date

    def appliquer(self, resultats, *, archiver_pluie=False):
        for key, result in resultats.items():
            source = self.sources[key]
            data = result.get('data') if isinstance(result, dict) else None
            valid = isinstance(data, list) and all(isinstance(item, dict) for item in data)
            source['error'] = not valid or result.get('error') is not None
            source['cache'] = source['error']
            if not source['error']:
                source['data'] = data
                date = result.get('date')
                source['date'] = date if parse_iso(date) is not None else None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            ecrire_json(self.path, {'schema': 2,
                **{'stations_'+key: val['data'] for key,val in self.sources.items()},
                'dates': {key: val['date'] for key,val in self.sources.items()}})
            if archiver_pluie:
                from meteo_pluie import enregistrer
                import sqlite3
                try:
                    enregistrer(self.path.with_name('netatmo_pluie.sqlite3'), resultats)
                except (OSError, sqlite3.Error):
                    import logging
                    logging.getLogger(__name__).warning('Historique pluie local indisponible')
            return True
        except (OSError, RuntimeError):
            return False

    def libelle(self):
        lignes = []
        for key, label in [('privees',_tr('meteo_cache_text_45')),('publiques',_tr('meteo_cache_text_47'))]:
            source = self.sources[key]
            date = source['date']
            parsed = parse_iso(date)
            when = parsed.astimezone().strftime('%d/%m/%Y %H:%M:%S') if parsed else _tr('weather_source_date_unknown')
            if source['date'] or source['data']:
                etat = _tr('meteo_cache_text_52') if source['cache'] else _tr('meteo_cache_text_50')
                texte = _tr('weather_source_retrieval').format(source=label,date=when,state=etat)
                if not source['data']:
                    texte += ' · ' + _tr('weather_source_no_stations')
            else:
                texte = label + _tr('meteo_cache_text_55')
            if source['error']:
                texte += _tr('meteo_cache_text_57')
            lignes.append(texte)
        return '\n'.join(lignes)


def recuperer_sources(api):
    result = {}
    for key, function in [('privees',api.recuperer_netatmo),('publiques',api.recuperer_stations_publiques)]:
        try:
            data = function()
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                raise ValueError('invalid station response')
            result[key] = {'data': data, 'date': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'error': None}
        except Exception:
            result[key] = {'data': None, 'date': None, 'error': _tr('meteo_cache_text_67')}
    return result
