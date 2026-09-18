import asyncio

# Conserve aussi la possibilite d'execution directe du module.
if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capteur_infos import enregistrer_infos

from bleak import BleakClient, BleakScanner
from capteurs.historique import lire_historique


COMMANDE = "00001a00-0000-1000-8000-00805f9b34fb"
MESURES = "00001a01-0000-1000-8000-00805f9b34fb"
BATTERIE = "00001a02-0000-1000-8000-00805f9b34fb"

TRAME_INVALIDE = bytes.fromhex(
    "aabbccddeeff99887766000000000000"
)


class MiFloraIntrouvable(Exception):
    """Le Mi Flora n'a pas été trouvé lors du scan Bluetooth."""

    code = 3


async def scanner_avec_progression(
    adresse,
    duree=20,
    silencieux=False
):

    tache_scan = asyncio.create_task(
        BleakScanner.find_device_by_address(
            adresse,
            timeout=duree
        )
    )

    debut = asyncio.get_running_loop().time()
    dernier_pourcentage = -1

    while not tache_scan.done():

        elapsed = asyncio.get_running_loop().time() - debut
        pourcentage = min(
            99,
            int((elapsed / duree) * 100)
        )

        if not silencieux and pourcentage != dernier_pourcentage:
            barre_complete = int(pourcentage / 5)

            barre = (
                "█" * barre_complete
                + "░" * (20 - barre_complete)
            )

            print(
                f"\r   [{barre}] {pourcentage:3d} %",
                end="",
                flush=True
            )

            dernier_pourcentage = pourcentage

        await asyncio.sleep(0.1)

    appareil = await tache_scan

    if not silencieux:
        print(
            "\r   [████████████████████] 100 %"
        )

    return appareil


def decoder_mesure_directe(data):
    """Décode la trame de mesure directe Mi Flora."""

    if len(data) < 10:
        raise ValueError("Réponse Mi Flora trop courte.")

    if data == TRAME_INVALIDE:
        raise ValueError(
            "Le Mi Flora a renvoyé une trame invalide "
            "(AA BB CC...)."
        )

    temperature = (
        int.from_bytes(
            data[0:2],
            "little",
            signed=True
        ) / 10
    )

    luminosite = int.from_bytes(
        data[3:7],
        "little",
        signed=False
    )

    humidite = data[7]

    conductivite = int.from_bytes(
        data[8:10],
        "little",
        signed=False
    )

    if not 0 <= humidite <= 100:
        raise ValueError(
            f"Humidité Mi Flora invalide : {humidite} %"
        )

    if not -20 <= temperature <= 60:
        raise ValueError(
            f"Température Mi Flora invalide : {temperature} C"
        )

    return (
        temperature,
        humidite,
        luminosite,
        conductivite,
        data.hex()
    )


async def lire_mesure_et_historique(
    adresse,
    silencieux=False
):
    """Lit mesure directe puis historique dans une seule connexion Bluetooth."""

    appareil = None

    for tentative in range(1, 4):

        if not silencieux:
            print()
            print(
                f"Recherche du Mi Flora "
                f"(tentative {tentative}/3)..."
            )

        appareil = await scanner_avec_progression(
            adresse,
            duree=20,
            silencieux=silencieux
        )

        if appareil is not None:

            if not silencieux:
                print(
                    f"Mi Flora trouvé à la tentative "
                    f"{tentative}/3."
                )

            break

        await asyncio.sleep(1.5)

    if appareil is None:
        raise MiFloraIntrouvable(
            f"Mi Flora introuvable après 3 tentatives : {adresse}"
        )

    async with BleakClient(
        appareil,
        timeout=35
    ) as client:

        await asyncio.sleep(2.0)

        donnees_batterie = b""
        try:
            donnees_batterie = await client.read_gatt_char(
                BATTERIE
            )
        except Exception:
            donnees_batterie = b""

        try:
            services_observes = [service.uuid for service in client.services]
        except Exception:
            services_observes = None

        enregistrer_infos(
            adresse,
            donnees_batterie,
            nom=getattr(appareil, "name", None),
            services=services_observes
        )

        await client.write_gatt_char(
            COMMANDE,
            bytearray([0xA0, 0x1F]),
            response=True
        )

        data = await client.read_gatt_char(
            MESURES
        )

        mesure = decoder_mesure_directe(data)

        await asyncio.sleep(1.0)
        historique = await lire_historique(client, adresse)

        return mesure, historique


async def lire_mesure(
    adresse,
    silencieux=False
):

    appareil = None

    for tentative in range(1, 4):

        if not silencieux:
            print()
            print(
                f"Recherche du Mi Flora "
                f"(tentative {tentative}/3)..."
            )

        appareil = await scanner_avec_progression(
            adresse,
            duree=20,
            silencieux=silencieux
        )

        if appareil is not None:

            if not silencieux:
                print(
                    f"Mi Flora trouvé à la tentative "
                    f"{tentative}/3."
                )

            break

        if not silencieux:
            print(
                f"Mi Flora introuvable "
                f"(tentative {tentative}/3)."
            )

    if appareil is None:

        if not silencieux:
            print()
            print("Mi Flora introuvable après 3 tentatives.")
            print("Code retour : 3")

        raise MiFloraIntrouvable(
            f"Mi Flora introuvable après 3 tentatives : {adresse}"
        )

    if not silencieux:
        print(f"Mi Flora trouvé : {appareil.address}")
        print("Connexion...")

    async with BleakClient(
        appareil,
        timeout=20
    ) as client:

        if not silencieux:
            print("Connecté !")

        # Lecture batterie et firmware
        donnees_batterie = b""
        try:
            donnees_batterie = await client.read_gatt_char(
                BATTERIE
            )

            if len(donnees_batterie) >= 1:

                batterie = donnees_batterie[0]

                if 0 <= batterie <= 100:

                    if not silencieux:
                        print(
                            f"🔋 Batterie : {batterie} %"
                        )

                else:

                    if not silencieux:
                        print(
                            "🔋 Batterie : valeur invalide"
                        )

                if len(donnees_batterie) >= 7:
                    firmware = donnees_batterie[2:7].decode(
                        "ascii",
                        errors="ignore"
                    )

                    if firmware and not silencieux:
                        print(
                            f"📦 Firmware : {firmware}"
                        )

        except Exception as erreur:

            if not silencieux:
                print(
                    f"⚠️ Batterie indisponible : {erreur}"
                )

        # Reutilise la meme lecture et les services deja decouverts par Bleak.
        try:
            services_observes = [service.uuid for service in client.services]
        except Exception:
            services_observes = None
        enregistrer_infos(adresse, donnees_batterie,
                          nom=getattr(appareil, "name", None),
                          services=services_observes)

        if not silencieux:
            print("Demande de mesure...")

        await client.write_gatt_char(
            COMMANDE,
            bytearray([0xA0, 0x1F]),
            response=True
        )

        data = await client.read_gatt_char(
            MESURES
        )

        if len(data) < 10:
            raise ValueError(
                "Réponse Mi Flora trop courte."
            )

        if data == TRAME_INVALIDE:
            raise ValueError(
                "Le Mi Flora a renvoyé une trame invalide "
                "(AA BB CC...)."
            )

        temperature = (
            int.from_bytes(
                data[0:2],
                "little",
                signed=True
            ) / 10
        )

        luminosite = int.from_bytes(
            data[3:7],
            "little",
            signed=False
        )

        humidite = data[7]

        conductivite = int.from_bytes(
            data[8:10],
            "little",
            signed=False
        )

        if not 0 <= humidite <= 100:
            raise ValueError(
                f"Humidité Mi Flora invalide : {humidite} %"
            )

        if not -20 <= temperature <= 60:
            raise ValueError(
                f"Température Mi Flora invalide : {temperature} C"
            )

        if not silencieux:
            print("Mesure reçue.")

        return (
            temperature,
            humidite,
            luminosite,
            conductivite,
            data.hex()
        )