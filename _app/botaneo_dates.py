"""Utilitaires centralisés pour les dates Botaneo.

Botaneo mélange des mesures locales affichées à l'utilisateur et des données
Raspberry souvent horodatées en UTC. Ce module fournit des conversions simples
pour éviter de réimplémenter le parsing ISO dans chaque écran.
"""

from __future__ import annotations

from datetime import datetime, timezone


def maintenant_local() -> datetime:
    """Retourne l'heure locale sous forme naïve, compatible avec les dates historiques Botaneo."""
    return datetime.now().astimezone().replace(tzinfo=None)


def maintenant_utc() -> datetime:
    """Retourne l'heure UTC avec fuseau."""
    return datetime.now(timezone.utc)


def iso_local(timespec: str = "seconds") -> str:
    """Date locale ISO sans fuseau, format utilisé par les mesures et événements locaux."""
    return maintenant_local().isoformat(timespec=timespec)


def iso_utc(timespec: str = "seconds") -> str:
    """Date UTC ISO avec fuseau, utile pour les échanges Raspberry/API."""
    return maintenant_utc().isoformat(timespec=timespec)


def parse_iso(valeur) -> datetime | None:
    """Parse une date ISO, avec prise en charge du suffixe Z."""
    if not isinstance(valeur, str) or not valeur.strip():
        return None
    texte = valeur.strip()
    try:
        return datetime.fromisoformat(texte.replace("Z", "+00:00"))
    except ValueError:
        return None


def vers_local_naif(valeur) -> datetime | None:
    """Convertit une date ISO ou datetime vers une date locale naïve comparable."""
    if isinstance(valeur, datetime):
        date = valeur
    else:
        date = parse_iso(valeur)
    if date is None:
        return None
    if date.tzinfo:
        return date.astimezone().replace(tzinfo=None)
    return date


def vers_utc(valeur) -> datetime | None:
    """Convertit une date ISO ou datetime vers UTC avec fuseau."""
    if isinstance(valeur, datetime):
        date = valeur
    else:
        date = parse_iso(valeur)
    if date is None:
        return None
    if date.tzinfo:
        return date.astimezone(timezone.utc)
    return date.astimezone().astimezone(timezone.utc)


def iso_depuis_local(valeur, timespec: str = "seconds") -> str | None:
    """Normalise une date vers ISO local naïf."""
    date = vers_local_naif(valeur)
    return date.isoformat(timespec=timespec) if date else None


def formater_local(valeur, defaut: str = "date inconnue") -> str:
    """Formate une date pour l'interface utilisateur."""
    date = vers_local_naif(valeur)
    if not date:
        return defaut
    return date.strftime("%d/%m/%Y à %H:%M:%S")
