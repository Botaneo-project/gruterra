import asyncio
import os
import sys

from bleak import BleakScanner


ADRESSE_MIFLORA = os.environ.get("BOTANEO_MIFLORA_ADDRESS", "AA:BB:CC:DD:EE:FF")


async def scanner():

    print()
    print("=" * 60)
    print("SCAN BLUETOOTH - MI FLORA")
    print("=" * 60)
    print()

    if ADRESSE_MIFLORA == "AA:BB:CC:DD:EE:FF":
        print("Aucune adresse Mi Flora réelle configurée.")
        print("Définissez BOTANEO_MIFLORA_ADDRESS pour chercher un capteur précis,")
        print("ou utilisez capteurs/scanner_ble.py pour afficher tous les appareils proches.")
        print()
        print("CODE RETOUR : 2")
        return 2

    print("Recherche du Mi Flora...")
    print(f"   Adresse recherchée : {ADRESSE_MIFLORA}")
    print("   Durée : 10 secondes")
    print()

    appareils = await BleakScanner.discover(timeout=10)

    for appareil in appareils:

        adresse = appareil.address

        if adresse.upper() == ADRESSE_MIFLORA.upper():

            nom = appareil.name or "Nom inconnu"

            print("MI FLORA TROUVÉ")
            print(f"   Nom     : {nom}")
            print(f"   Adresse : {adresse}")

            if hasattr(appareil, "rssi"):
                print(f"   Signal  : {appareil.rssi} dBm")

            print()
            print("CODE RETOUR : 0")
            print()

            return 0

    print("MI FLORA NON TROUVÉ")
    print()
    print("CODE RETOUR : 3")
    print()

    return 3


if __name__ == "__main__":
    code = asyncio.run(scanner())
    sys.exit(code)
