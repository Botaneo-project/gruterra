"""Promote only complete, time-validated exports; raw archive is kept upstream."""
from importer_historique_miflora import importer


def alimenter_graphiques(export, db_path):
    if export.get('status') == 'complete' and export.get('history_count') == 0 and not export.get('entries'):
        return {'ok': True, 'message': 'Aucun historique à ajouter aux graphiques.'}
    try:
        result = importer(export, db_path, appliquer=True, sauvegarder=False)
    except Exception:
        return {'ok': False, 'message': 'Historique conservé dans l’archive ; ajout aux graphiques non validé (lecture incomplète, dates, affectation ou stockage à vérifier).'}
    return {'ok': True, 'message': f"Graphiques : {result['ajoutees']} mesure(s) ajoutée(s), {result['deja_presentes']} déjà présente(s)."}
