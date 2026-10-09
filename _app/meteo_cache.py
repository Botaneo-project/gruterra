"""Etat prive/public independant. Une erreur ne rajeunit jamais le cache."""

from i18n import traduire_courant as _tr
from datetime import datetime, timezone
from botaneo_config import lire_json, ecrire_json


class CacheMeteo:
    def __init__(self, path):
        self.path = path
        self.sources = {key: {'data': [], 'date': None, 'cache': True, 'error': False} for key in ('privees','publiques')}
        try:
            raw = lire_json(path)
        except RuntimeError:
            raw = {}
        for key, source in self.sources.items():
            data = raw.get('stations_' + key, [])
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                source['data'] = data
            date = raw.get('dates', {}).get(key) if isinstance(raw.get('dates'), dict) else None
            try:
                if date is not None:
                    datetime.fromisoformat(date)
                    source['date'] = date
            except (TypeError, ValueError):
                pass

    def appliquer(self, resultats):
        for key, result in resultats.items():
            source = self.sources[key]
            source['error'] = result['error'] is not None
            source['cache'] = source['error']
            if not source['error']:
                source['data'] = result['data']
                source['date'] = result['date']
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            ecrire_json(self.path, {'schema': 2,
                **{'stations_'+key: val['data'] for key,val in self.sources.items()},
                'dates': {key: val['date'] for key,val in self.sources.items()}})
            return True
        except (OSError, RuntimeError):
            return False

    def libelle(self):
        lignes = []
        for key, label in [('privees',_tr('meteo_cache_text_45')),('publiques',_tr('meteo_cache_text_47'))]:
            source = self.sources[key]
            date = source['date']
            when = datetime.fromisoformat(date).astimezone().strftime('%d/%m/%Y à %H:%M:%S') if date else _tr('botaneo_email_text_192')
            if source['date'] or source['data']:
                etat = _tr('meteo_cache_text_52') if source['cache'] else _tr('meteo_cache_text_50')
                texte = f'{label} : {when} · {etat}'
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
            result[key] = {'data': data, 'date': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'error': None}
        except Exception:
            result[key] = {'data': None, 'date': None, 'error': _tr('meteo_cache_text_67')}
    return result
