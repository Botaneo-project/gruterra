
from i18n import traduire_courant as _tr
import asyncio
import os
import sys

from bleak import BleakScanner


ADRESSE_MIFLORA = os.environ.get("BOTANEO_MIFLORA_ADDRESS", "AA:BB:CC:DD:EE:FF")


async def scanner():

    print()
    print("=" * 60)
    print(_tr('scanner_ble_text_17'))
    print("=" * 60)
    print()

    if ADRESSE_MIFLORA == "AA:BB:CC:DD:EE:FF":
        print(_tr('scanner_ble_text_20'))
        print(_tr('scanner_ble_text_21'))
        print(_tr('scanner_ble_text_22'))
        print()
        print(_tr('scanner_ble_text_26'))
        return 2

    print(_tr('scanner_ble_text_27'))
    print(_tr('scanner_ble_text_28').format(v0=ADRESSE_MIFLORA))
    print(_tr('scanner_ble_text_29'))
    print()

    appareils = await BleakScanner.discover(timeout=10)

    for appareil in appareils:

        adresse = appareil.address

        if adresse.upper() == ADRESSE_MIFLORA.upper():

            nom = appareil.name or _tr('scanner_ble_text_24')

            print(_tr('scanner_ble_text_42'))
            print(f"   Nom     : {nom}")
            print(f"   Adresse : {adresse}")

            if hasattr(appareil, "rssi"):
                print(f"   Signal  : {appareil.rssi} dBm")

            print()
            print(_tr('scanner_ble_text_52'))
            print()

            return 0

    print(_tr('scanner_ble_text_55'))
    print()
    print(_tr('scanner_ble_text_59'))
    print()

    return 3


if __name__ == "__main__":
    code = asyncio.run(scanner())
    sys.exit(code)
