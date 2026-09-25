"""Collecte passive Mi Flora / Flower Care via annonces BLE MiBeacon.

Prototype Raspberry : aucune connexion GATT, aucune lecture historique, aucun effacement.
Le capteur diffuse les objets un par un dans les service data FE95. Ce module écoute
ces annonces, agrège les dernières valeurs reçues et peut enregistrer une mesure
complète dans la table `measurements` existante.
"""
import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakScanner

BASE = Path.home() / "botaneo"

SERVICE_MIBEACON = "0000fe95-0000-1000-8000-00805f9b34fb"
SERVICE_MIBEACON_SHORT = "0000fe95"
PRODUCT_FLOWER_CARE = 0x0098

OBJECT_TEMPERATURE = 0x1004
OBJECT_LIGHT = 0x1007
OBJECT_MOISTURE = 0x1008
OBJECT_CONDUCTIVITY = 0x1009
OBJECT_BATTERY = 0x100A


def normalize_address(address):
    return (address or "").strip().upper()


def hex_bytes(data):
    return bytes(data).hex(" ")


def uint_le(data):
    return int.from_bytes(bytes(data), byteorder="little", signed=False)


def decode_mibeacon(data):
    """Decode les objets utiles d'une trame MiBeacon Flower Care."""
    raw = bytes(data)
    if len(raw) < 12:
        return None
    frame_control = uint_le(raw[0:2])
    product_id = uint_le(raw[2:4])
    if product_id != PRODUCT_FLOWER_CARE:
        return None
    counter = raw[4]
    mac = ":".join(f"{byte:02X}" for byte in reversed(raw[5:11]))
    capability = raw[11]
    values = {}
    objects = []
    position = 12
    while position + 3 <= len(raw):
        object_type = uint_le(raw[position:position + 2])
        length = raw[position + 2]
        start = position + 3
        end = start + length
        if end > len(raw):
            break
        value = raw[start:end]
        decoded = None
        if object_type == OBJECT_TEMPERATURE and length >= 2:
            decoded = ("temperature_c", uint_le(value[:2]) / 10)
        elif object_type == OBJECT_LIGHT and length >= 3:
            decoded = ("illuminance_lux", uint_le(value[:3]))
        elif object_type == OBJECT_MOISTURE and length >= 1:
            decoded = ("moisture_percent", int(value[0]))
        elif object_type == OBJECT_CONDUCTIVITY and length >= 2:
            decoded = ("conductivity_us_cm", uint_le(value[:2]))
        elif object_type == OBJECT_BATTERY and length >= 1:
            decoded = ("battery_percent", int(value[0]))
        if decoded:
            values[decoded[0]] = decoded[1]
        objects.append({
            "type": f"0x{object_type:04x}",
            "length": length,
            "raw": hex_bytes(value),
            "decoded": decoded[0] if decoded else None,
        })
        position = end
    return {
        "frame_control": f"0x{frame_control:04x}",
        "product_id": f"0x{product_id:04x}",
        "counter": counter,
        "mac": mac,
        "capability": f"0x{capability:02x}",
        "values": values,
        "objects": objects,
        "raw": hex_bytes(raw),
    }


class PassiveCollector:
    def __init__(self, sensors):
        self.sensors = {normalize_address(sensor) for sensor in sensors}
        self.snapshots = {
            sensor: {
                "sensor_id": sensor,
                "received_at": None,
                "values": {},
                "raw_packets": [],
                "rssi": None,
                "complete": False,
            }
            for sensor in self.sensors
        }

    def accept(self, device, advertisement_data):
        address = normalize_address(getattr(device, "address", ""))
        if address not in self.sensors:
            return
        service_data = getattr(advertisement_data, "service_data", {}) or {}
        for uuid, data in service_data.items():
            if uuid.lower() not in (SERVICE_MIBEACON, SERVICE_MIBEACON_SHORT):
                continue
            decoded = decode_mibeacon(data)
            if not decoded:
                continue
            snapshot = self.snapshots[address]
            snapshot["received_at"] = datetime.now(timezone.utc).isoformat()
            snapshot["rssi"] = getattr(advertisement_data, "rssi", None)
            snapshot["values"].update(decoded["values"])
            snapshot["raw_packets"].append(decoded["raw"])
            snapshot["raw_packets"] = snapshot["raw_packets"][-20:]
            snapshot["complete"] = self.is_complete(snapshot)
            logging.info("Annonce passive %s : %s", address, decoded["values"])

    @staticmethod
    def is_complete(snapshot):
        values = snapshot["values"]
        return all(key in values for key in (
            "temperature_c",
            "moisture_percent",
            "illuminance_lux",
            "conductivity_us_cm",
        ))

    def results(self):
        return list(self.snapshots.values())


async def listen(sensors, duration):
    collector = PassiveCollector(sensors)
    scanner = BleakScanner(collector.accept)
    await scanner.start()
    try:
        await asyncio.sleep(duration)
    finally:
        await scanner.stop()
    return collector.results()


def store_complete(path, device_id, snapshots):
    from collector import initialize, record

    initialize(path)
    stored = []
    for snapshot in snapshots:
        if not snapshot.get("complete"):
            continue
        values = snapshot["values"]
        raw = json.dumps({
            "source": "passive_mibeacon",
            "received_at": snapshot.get("received_at"),
            "rssi": snapshot.get("rssi"),
            "raw_packets": snapshot.get("raw_packets", []),
            "values": values,
        }, sort_keys=True, separators=(",", ":"))
        measurement_id = record(path, device_id, snapshot["sensor_id"], values=(
            float(values["temperature_c"]),
            int(values["moisture_percent"]),
            int(values["illuminance_lux"]),
            int(values["conductivity_us_cm"]),
            raw,
        ))
        stored.append({"sensor_id": snapshot["sensor_id"], "measurement_id": measurement_id})
    return stored


def load_config():
    return json.loads((BASE / "config/collector.json").read_text())


async def main_async(args):
    config = load_config()
    sensors = args.sensor or config.get("sensors", [])
    if not sensors:
        raise ValueError("Aucun capteur configuré")
    results = await listen(sensors, args.duration)
    stored = []
    if args.store:
        stored = store_complete(BASE / "data/collector.sqlite3", config["device_id"], results)
    print(json.dumps({
        "ok": True,
        "duration": args.duration,
        "stored": stored,
        "results": results,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Collecte passive Mi Flora par annonces BLE, sans connexion au capteur.")
    parser.add_argument("--duration", type=int, default=120, help="Durée d'écoute en secondes")
    parser.add_argument("--sensor", action="append", help="Adresse d'un capteur à écouter ; par défaut, capteurs de collector.json")
    parser.add_argument("--store", action="store_true", help="Enregistrer les mesures complètes dans la base Raspberry")
    parser.add_argument("--verbose", action="store_true", help="Afficher les annonces décodées pendant l'écoute")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
