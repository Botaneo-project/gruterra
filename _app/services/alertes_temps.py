"""Local time checks for alerts; no network, configuration or database access."""
from datetime import datetime
from botaneo_dates import vers_local_naif


def minutes_depuis(value, reference=None):
    at = vers_local_naif(value)
    now = vers_local_naif(reference) if reference is not None else datetime.now()
    if at is None or now is None:
        return None
    minutes = (now - at).total_seconds() / 60
    # Small clock skew is tolerated; a clearly future reading is not fresh data.
    return max(0, int(minutes)) if minutes >= -5 else None


def jours_avant(value, reference=None):
    at = vers_local_naif(value)
    now = vers_local_naif(reference) if reference is not None else datetime.now()
    return (at.date() - now.date()).days if at is not None and now is not None else None


def etat_prevision(data, reference=None):
    if not isinstance(data, dict) or not data:
        return 'absent'
    age = minutes_depuis(data.get('date'), reference)
    if age is None:
        return 'unknown'
    if age >= 120:
        return 'expired'
    return 'current'


def trier_alertes(alertes):
    order = {'danger': 0, 'attention': 1, 'info': 2, 'ok': 3}
    return sorted(alertes, key=lambda item: order.get(item.get('niveau'), 2))
