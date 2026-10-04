"""Traductions simples pour l’interface Gruterra.

Ce module ne traduit pas encore toute l’application. Il fournit une base stable
pour brancher progressivement les textes visibles sur une préférence locale.
"""

LANGUES = {"fr", "en"}
LANGUE_DEFAUT = "fr"

TRADUCTIONS = {
    "app_title": {"fr": "Gruterra", "en": "Gruterra"},
    "system_active": {"fr": "● Système actif", "en": "● System active"},
    "no_sync": {"fr": "Aucune synchronisation effectuée", "en": "No synchronization yet"},
    "refresh": {"fr": "⟳ Actualiser", "en": "⟳ Refresh"},
    "sync": {"fr": "🔄 Synchroniser", "en": "🔄 Sync"},
    "add_plant": {"fr": "＋ Ajouter une plante", "en": "＋ Add plant"},
    "add_sensor": {"fr": "＋ Ajouter un capteur", "en": "＋ Add sensor"},
    "plants": {"fr": "🌱 Plantes", "en": "🌱 Plants"},
    "settings": {"fr": "⚙ Paramètres", "en": "⚙ Settings"},
    "about": {"fr": "ℹ À propos", "en": "ℹ About"},
    "health": {"fr": "🩺 État Gruterra", "en": "🩺 Gruterra status"},
    "maintenance": {"fr": "🧰 Base & synthèses", "en": "🧰 Database & summaries"},
    "light_mode": {"fr": "☀️ Mode clair", "en": "☀️ Light mode"},
    "dark_mode": {"fr": "🌙 Mode sombre", "en": "🌙 Dark mode"},
    "settings_title": {"fr": "Paramètres Gruterra", "en": "Gruterra settings"},
    "settings_header": {"fr": "⚙ Paramètres", "en": "⚙ Settings"},
    "display": {"fr": "Affichage", "en": "Display"},
    "language": {"fr": "Langue", "en": "Language"},
    "language_note": {"fr": "Traduction progressive : certains écrans restent en français.", "en": "Progressive translation: some screens are still in French."},
    "save": {"fr": "Enregistrer", "en": "Save"},
    "cancel": {"fr": "Annuler", "en": "Cancel"},
    "settings_saved": {"fr": "Paramètres enregistrés.", "en": "Settings saved."},
    "close": {"fr": "Fermer", "en": "Close"},
    "copy": {"fr": "📋 Copier", "en": "📋 Copy"},
    "copy_update_json": {"fr": "Copier diagnostic update JSON", "en": "Copy update diagnostic JSON"},
    "check_updates": {"fr": "🔎 Vérifier les mises à jour", "en": "🔎 Check updates"},
    "update": {"fr": "⬇ Update", "en": "⬇ Update"},
    "apply_update": {"fr": "⚠ Appliquer update", "en": "⚠ Apply update"},
    "about_copied": {"fr": "Informations À propos copiées dans le presse-papiers", "en": "About information copied to clipboard"},
    "update_json_copied": {"fr": "Diagnostic mise à jour JSON copié dans le presse-papiers", "en": "Update diagnostic JSON copied to clipboard"},
    "update_checking": {"fr": "Vérification des mises à jour Gruterra…", "en": "Checking Gruterra updates…"},
    "update_check_done": {"fr": "Vérification des mises à jour terminée", "en": "Update check finished"},
    "update_sim_running": {"fr": "Simulation update Gruterra en cours…", "en": "Running Gruterra update simulation…"},
    "update_sim_done": {"fr": "Simulation update terminée", "en": "Update simulation finished"},
    "update_apply_title": {"fr": "Appliquer update Gruterra", "en": "Apply Gruterra update"},
    "update_apply_confirm": {"fr": "Gruterra va tenter d’appliquer l’archive officielle après contrôle SHA256 et sauvegarde locale. Continuer ?", "en": "Gruterra will try to apply the official archive after SHA256 verification and local backup. Continue?"},
    "update_apply_running": {"fr": "Application update Gruterra en cours…", "en": "Applying Gruterra update…"},
    "update_apply_done": {"fr": "Assistant update terminé", "en": "Update assistant finished"},
    "sync_status_copied": {"fr": "Statut de synchronisation copié dans le presse-papiers", "en": "Synchronization status copied to clipboard"},
    "auto_sync_running": {"fr": "📡 Synchronisation automatique en cours", "en": "📡 Automatic synchronization running"},
    "theme_applied_unsaved": {"fr": "Thème appliqué · préférence non enregistrée", "en": "Theme applied · preference not saved"},
    "watering": {"fr": "💧 Arrosage", "en": "💧 Watering"},
    "balcony_out": {"fr": "☀️ Sortie balcon", "en": "☀️ Balcony time"},
    "back_inside": {"fr": "🏠 Retour intérieur", "en": "🏠 Back inside"},
    "past_exposure": {"fr": "🕘 Exposition passée", "en": "🕘 Past exposure"},
    "analysis": {"fr": "🔎 Analyse", "en": "🔎 Analysis"},
    "copy_plant_analysis": {"fr": "📋 Copier analyse", "en": "📋 Copy analysis"},
    "history": {"fr": "📈 Historique", "en": "📈 History"},
    "history_analysis": {"fr": "📈 Historique / analyse", "en": "📈 History / analysis"},
    "import_simple_history": {"fr": "📥 Importer historique simplifié", "en": "📥 Import simplified history"},
    "associate_sensor": {"fr": "＋ Associer un capteur", "en": "＋ Link sensor"},
    "add_plant_title": {"fr": "Ajouter une plante", "en": "Add plant"},
    "plant_name": {"fr": "Nom de la plante", "en": "Plant name"},
    "known_needs": {"fr": "Besoins connus", "en": "Known needs"},
    "location": {"fr": "Emplacement", "en": "Location"},
    "add": {"fr": "Ajouter", "en": "Add"},
    "search_plants": {"fr": "🔎 Filtrer les plantes", "en": "🔎 Filter plants"},
    "reset": {"fr": "Réinitialiser", "en": "Reset"},
    "plants_view_title": {"fr": "Plantes — Gruterra", "en": "Plants — Gruterra"},
    "refresh_plain": {"fr": "Actualiser", "en": "Refresh"},
    "no_plant_filters": {"fr": "Aucune plante ne correspond aux filtres actuels.", "en": "No plant matches the current filters."},
    "open_plants_view": {"fr": "Ouvrir la vue Plantes", "en": "Open plants view"},
    "plants_hidden_home": {"fr": "Les plantes sont masquées sur l'accueil. Vous pouvez les consulter dans une vue dédiée ou les réafficher depuis Paramètres > Affichage.", "en": "Plants are hidden from the home screen. You can open the dedicated view or show them again from Settings > Display."},
    "no_plants": {"fr": "🌱 Aucune plante dans Gruterra", "en": "🌱 No plants in Gruterra"},
    "syncing": {"fr": "⏳ Synchronisation...", "en": "⏳ Synchronizing..."},
    "sync_plain": {"fr": "📡 Synchroniser", "en": "📡 Sync"},
    "copy_status": {"fr": "📋 Copier le statut", "en": "📋 Copy status"},
    "copyable_status": {"fr": "Statut copiable", "en": "Copyable status"},
    "update_available_title": {"fr": "Mise à jour Gruterra disponible", "en": "Gruterra update available"},
    "update_ignored": {"fr": "Mise à jour disponible ignorée pour cette session", "en": "Available update ignored for this session"},
    "update_downloading": {"fr": "Téléchargement et application de la mise à jour Gruterra…", "en": "Downloading and applying Gruterra update…"},
    "update_restart_advised": {"fr": "Mise à jour terminée · redémarrage manuel conseillé", "en": "Update finished · manual restart recommended"},
}


def normaliser_langue(langue):
    code = str(langue or "").strip().lower()
    return code if code in LANGUES else LANGUE_DEFAUT


def traduire(cle, langue="fr"):
    code = normaliser_langue(langue)
    entree = TRADUCTIONS.get(cle, {})
    return entree.get(code) or entree.get(LANGUE_DEFAUT) or cle
