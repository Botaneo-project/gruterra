"""Promote only complete, time-validated exports; raw archive is kept upstream."""
from importer_historique_miflora import importer


def alimenter_graphiques(export, db_path):
    if export.get('status') == 'complete' and export.get('history_count') == 0 and not export.get('entries'):
        return {'ok': True, 'message': 'Aucun historique à ajouter aux graphiques.'}
    try:
        result = importer(export, db_path, appliquer=True, sauvegarder=False)
    except Exception as erreur:
        return {'ok': False, 'message': f'Historique conservé dans l’archive ; ajout aux graphiques non validé : {erreur}'}
    prefixe = 'Graphiques'
    if export.get('status') == 'partial':
        prefixe = 'Graphiques depuis lecture partielle'
    return {'ok': True, 'message': f"{prefixe} : {result['ajoutees']} mesure(s) ajoutée(s), {result['deja_presentes']} déjà présente(s)."}
