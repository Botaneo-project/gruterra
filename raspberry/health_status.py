"""Diagnostic santé Raspberry pour Botaneo.

Retourne un JSON lisible par le PC : température, disque, mémoire,
uptime, état lecture/écriture et erreurs disque récentes.
"""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def cpu_temperature_c():
    raw = read_text("/sys/class/thermal/thermal_zone0/temp")
    if raw is None:
        return None
    try:
        return round(int(raw) / 1000, 1)
    except ValueError:
        return None


def memory_info():
    info = {}
    raw = read_text("/proc/meminfo") or ""
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parts = value.strip().split()
        if parts and parts[0].isdigit():
            info[key] = int(parts[0]) * 1024
    total = info.get("MemTotal")
    available = info.get("MemAvailable")
    return {
        "total_bytes": total,
        "available_bytes": available,
        "available_percent": round((available / total) * 100, 1) if total and available is not None else None,
    }


def disk_info(path):
    usage = shutil.disk_usage(path)
    return {
        "path": str(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_percent": round((usage.free / usage.total) * 100, 1) if usage.total else None,
    }


def uptime_seconds():
    raw = read_text("/proc/uptime")
    if raw is None:
        return None
    try:
        return int(float(raw.split()[0]))
    except (ValueError, IndexError):
        return None


def load_average():
    try:
        one, five, fifteen = os.getloadavg()
        return {"1m": round(one, 2), "5m": round(five, 2), "15m": round(fifteen, 2)}
    except OSError:
        return None


def filesystem_writable(path):
    target = Path(path) / ".botaneo_write_test"
    try:
        target.write_text("ok", encoding="utf-8")
        target.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def recent_disk_errors():
    patterns = ("i/o error", "ext4-fs error", "mmc", "read-only file system")
    commands = [
        ["journalctl", "-k", "--since", "24 hours ago", "--no-pager"],
        ["dmesg", "--ctime"],
    ]
    for command in commands:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=8)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue
        matches = []
        for line in result.stdout.splitlines():
            lower = line.lower()
            if any(pattern in lower for pattern in patterns):
                matches.append(line[-300:])
        return matches[-20:]
    return []


def backup_count():
    backup_dir = Path.home() / "botaneo/backups"
    if not backup_dir.exists():
        return 0
    return sum(1 for item in backup_dir.rglob("*") if item.is_file())


def status_level(payload):
    warnings = []
    if payload["disk"].get("free_percent") is not None and payload["disk"]["free_percent"] < 15:
        warnings.append("disque presque plein")
    if payload.get("temperature_c") is not None and payload["temperature_c"] >= 75:
        warnings.append("température élevée")
    if payload["memory"].get("available_percent") is not None and payload["memory"]["available_percent"] < 10:
        warnings.append("mémoire faible")
    if not payload.get("writable"):
        warnings.append("système non inscriptible")
    if payload.get("disk_errors"):
        warnings.append("erreurs disque récentes")
    if warnings:
        return "warning", warnings
    return "ok", []


def main_payload():
    base = Path.home() / "botaneo"
    payload = {
        "ok": True,
        "timestamp": int(time.time()),
        "hostname": os.uname().nodename if hasattr(os, "uname") else None,
        "temperature_c": cpu_temperature_c(),
        "disk": disk_info(base),
        "memory": memory_info(),
        "uptime_seconds": uptime_seconds(),
        "load_average": load_average(),
        "writable": filesystem_writable(base),
        "backup_files": backup_count(),
        "disk_errors": recent_disk_errors(),
    }
    level, warnings = status_level(payload)
    payload["status"] = level
    payload["warnings"] = warnings
    return payload


def main():
    print(json.dumps(main_payload(), ensure_ascii=False))


if __name__ == "__main__":
    main()
