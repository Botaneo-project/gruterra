"""Promote only complete, time-validated exports; raw archive is kept upstream."""

from i18n import traduire_courant as _tr
from importer_historique_miflora import importer


def alimenter_graphiques(export, db_path):
    if export.get('status') == 'complete' and export.get('history_count') == 0 and not export.get('entries'):
        return {'ok': True, 'message': _tr('historique_graphique_text_7')}
    try:
        result = importer(export, db_path, appliquer=True, sauvegarder=False)
    except Exception as erreur:
        return {'ok': False, 'message': _tr('historique_graphique_text_11').format(v0=erreur)}
    prefixe = _tr('historique_graphique_text_14_more')
    if export.get('status') == 'partial':
        prefixe = _tr('historique_graphique_text_14')
    return {'ok': True, 'message': _tr('historique_graphique_text_15').format(v0=prefixe, v1=result['ajoutees'], v2=result['deja_presentes'])}
