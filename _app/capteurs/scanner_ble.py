import asyncio

from bleak import BleakScanner


async def scanner():

    print()
    print("=" * 60)
    print("🔎 SCAN BLUETOOTH")
    print("=" * 60)
    print()

    appareils = await BleakScanner.discover(
        timeout=10
    )

    if not appareils:
        print("❌ Aucun appareil trouvé.")
        return

    for appareil in appareils:

        nom = appareil.name or "Nom inconnu"

        print("-" * 60)
        print(f"📡 Nom     : {nom}")
        print(f"🔗 Adresse : {appareil.address}")

        if hasattr(appareil, "rssi"):
            print(f"📶 Signal  : {appareil.rssi} dBm")

    print()
    print("=" * 60)
    print(f"📊 {len(appareils)} appareil(s) trouvé(s)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(scanner())