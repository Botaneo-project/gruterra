"""Journal ferme: aucun message libre, token, URL ou corps de reponse."""
import logging

_logger = logging.getLogger("botaneo.securite")
_logger.addHandler(logging.NullHandler())
_EVENTS = {"netatmo_refresh_ok", "netatmo_http_error", "netatmo_network_error"}


def evenement(event, status=None):
    if event not in _EVENTS:
        raise ValueError("Evenement non autorise")
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError("Statut HTTP invalide")
    _logger.info("event=%s status=%s", event, status if status is not None else "-")
