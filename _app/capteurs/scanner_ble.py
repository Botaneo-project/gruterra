
if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from i18n import traduire_courant as _tr
import asyncio

from bleak import BleakScanner


async def scanner():

    print()
    print("=" * 60)
    print(_tr('scanner_ble_text_12'))
    print("=" * 60)
    print()

    appareils = await BleakScanner.discover(
        timeout=10
    )

    if not appareils:
        print(_tr('scanner_ble_text_19'))
        return

    for appareil in appareils:

        nom = appareil.name or _tr('scanner_ble_text_24')

        print("-" * 60)
        print(f"📡 Nom     : {nom}")
        print(f"🔗 Adresse : {appareil.address}")

        if hasattr(appareil, "rssi"):
            print(f"📶 Signal  : {appareil.rssi} dBm")

    print()
    print("=" * 60)
    print(_tr('scanner_ble_text_35').format(v0=len(appareils)))
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(scanner())