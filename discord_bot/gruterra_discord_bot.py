"""Bot Discord optionnel pour préparer le serveur communautaire Gruterra.

Le token doit rester dans discord_bot/.env et ne doit jamais être publié.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
COMMAND_PREFIX = "!"
SETUP_ENABLED = os.environ.get("DISCORD_SETUP_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
AUTO_RELEASE_ENABLED = os.environ.get("DISCORD_AUTO_RELEASE_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
AUTO_RELEASE_GUILD_ID = os.environ.get("DISCORD_AUTO_RELEASE_GUILD_ID", "").strip()
AUTO_RELEASE_INTERVAL_MINUTES = max(15, int(os.environ.get("DISCORD_AUTO_RELEASE_INTERVAL_MINUTES", "60") or "60"))
AUTO_RELEASE_STATE_FILE = BASE_DIR / ".release_state.json"

INTENTS = discord.Intents.default()
INTENTS.guilds = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=INTENTS)

ROLE_NAMES = [
    "Gruterra Admin",
    "Tester",
    "Contributor",
]

INVITE_CHANNEL_CANDIDATES = [
    "welcome",
    "useful-links",
    "general",
    "discussion-fr",
]

RELEASE_CHANNEL_CANDIDATES = [
    "changelog",
    "announcements",
    "useful-links",
]

CLEANUP_CHANNEL_CANDIDATES = [
    "announcements",
    "welcome",
    "changelog",
    "bot-commands",
    "bot-log",
    "useful-links",
    "general",
    "installation-help",
    "sensors-and-data",
    "discussion-fr",
    "aide-installation-fr",
    "retours-fr",
    "demo-feedback",
    "bugs-feedback",
    "ideas",
]

CLEANUP_COMMAND_PREFIXES = (
    "!setup_gruterra",
    "!invite_gruterra",
    "!clean_gruterra_messages",
    "!clean_here",
    "!post_guides_gruterra",
    "!reset_guides_gruterra",
    "!fix_bot_commands",
)

PRESENTATION_MESSAGE = """🌱 **Bienvenue sur Gruterra / Welcome to Gruterra**

Gruterra est un projet open-source né en français, autour du suivi des plantes, des capteurs Mi Flora / Flower Care, du Raspberry Pi, de Netatmo, de l'historique d'arrosage et de la lumière.

L'anglais est bienvenu pour ouvrir le projet à plus de monde, mais l'application et la documentation restent principalement en français pour l'instant. La traduction sera progressive.

Vous pouvez utiliser ce serveur pour :
- demander de l'aide à l'installation ;
- tester le mode démo ;
- parler Mi Flora, Raspberry Pi, Netatmo et données locales ;
- signaler un bug ou proposer une idée ;
- discuter plantes, arrosage et lumière.

Gruterra is an open-source plant monitoring project originally built in French. English-speaking users are welcome, but the app is not fully translated yet.

GitHub: https://github.com/Botaneo-project/gruterra
"""

CHANNEL_STARTER_MESSAGES = {
    "welcome": """🌱 **Bienvenue sur Gruterra / Welcome to Gruterra**

Gruterra est d'abord un projet francophone. Les utilisateurs anglophones sont bienvenus, mais l'application n'est pas encore entièrement traduite. Vous pouvez faire un petit coucou ici et dire ce que vous venez tester : mode démo, Mi Flora / Flower Care, Raspberry Pi, Netatmo, suivi des plantes ou simple curiosité.

Premiers pas utiles :
- #useful-links pour GitHub et les guides ;
- #installation-help pour l'aide technique générale ;
- #discussion-fr pour échanger en français ;
- #aide-installation-fr pour l'aide en français.

Gruterra is mainly built in French. English help is welcome, but translation is still in progress.
""",
    "useful-links": """🔗 **Liens utiles / Useful links**

Dépôt GitHub / GitHub repository:
https://github.com/Botaneo-project/gruterra

Pour commencer :
- `README.md` : présentation du projet ;
- `GUIDE_DEMO.md` : tester sans capteur ;
- `GUIDE_NETATMO.md` : configurer Netatmo ;
- `RASPBERRY.md` : comprendre la partie Raspberry Pi ;
- `ROADMAP.md` et `TODO.md` : suivre les prochaines étapes.

English users can start with the README and demo guide, but some parts of the app and documentation are still French-first.
""",
    "bot-commands": """⌨️ **Commandes bot / Bot commands**

Utilisez ce salon pour lancer les commandes Gruterra sans polluer le général.

Commandes utiles :
- `!post_guides_gruterra` : publier ou mettre à jour les messages d’accueil et de tutoriel ;
- `!reset_guides_gruterra` : nettoyer les anciens messages de guide et republier proprement ;
- `!fix_bot_commands` : réparer les droits du salon privé de commandes ;
- `!invite_gruterra` : générer une invitation publique ;
- `!release_gruterra` : publier manuellement une annonce de release ;
- `!auto_release_check` : tester l’annonce automatique anti-spam ;
- `!clean_here` : nettoyer les messages techniques du salon courant ;
- `!help_gruterra` ou `!aide_gruterra` : afficher l’aide.

Les résultats techniques détaillés restent envoyés dans #bot-log quand c’est possible.
""",
    "bot-log": """🤖 **Bot log**

This channel is dedicated to automated Gruterra bot messages: setup results, structure updates, invite generation notes and future maintenance messages.

Keeping bot messages here avoids mixing technical setup details with public discussion channels. Use #bot-commands to type commands manually.
""",
    "installation-help": """🛠️ **Aide installation / Installation help**

Vous pouvez demander de l'aide ici en français ou en anglais.

Pour faciliter le diagnostic, indiquez si possible :
- Windows, Raspberry Pi ou autre ;
- comment vous lancez Gruterra ;
- le message d'erreur exact ou une capture ;
- si vous utilisez le mode démo, Mi Flora, Raspberry Pi ou Netatmo.

Never share private tokens, passwords, refresh tokens or API secrets.
""",
    "sensors-and-data": """📡 **Capteurs et données / Sensors and data**

Salon pour Mi Flora / Flower Care, Raspberry Pi, Netatmo, Bluetooth, historique capteur et qualité des données.

Infos utiles en cas de souci :
- type de capteur ;
- collecte PC ou Raspberry Pi ;
- dernière synchronisation réussie ;
- import historique réussi ou non ;
- valeurs suspectes : dates manquantes, mesures à zéro, trous dans l'historique.
""",
    "demo-feedback": """🧪 **Retours mode démo / Demo feedback**

Utilisez ce salon si vous testez Gruterra sans capteur réel. Retours utiles :
- ce qui est clair ou confus ;
- si les captures et données démo aident ;
- où vous avez eu envie de cliquer en premier ;
- ce qui manque pour comprendre le projet.
""",
    "bugs-feedback": """🐛 **Bugs / Bug reports**

Quand c'est possible, indiquez :
- ce que vous avez cliqué ou lancé ;
- ce que vous attendiez ;
- ce qui s'est passé ;
- le message d'erreur exact ;
- si le problème se reproduit.

Please avoid posting secrets or private configuration files.
""",
    "ideas": """💡 **Idées / Ideas**

Partagez vos idées pour l'analyse des plantes, les cycles d'arrosage, la lumière, le Raspberry Pi, Netatmo, l'interface ou la documentation.

Les petites idées pratiques sont aussi les bienvenues.
""",
    "discussion-fr": """🇫🇷 **Bienvenue dans l'espace français**

Vous pouvez faire un petit coucou ici, poser vos questions en français et dire ce que vous testez : mode démo, Mi Flora, Raspberry Pi, Netatmo ou suivi des plantes.
""",
    "aide-installation-fr": """🛠️ **Aide installation en français**

Pour demander de l'aide, indiquez si possible :
- Windows ou Raspberry Pi ;
- comment vous lancez Gruterra ;
- le message d'erreur exact ;
- si vous utilisez le mode démo, Mi Flora, Raspberry Pi ou Netatmo.

Ne partagez jamais vos tokens, mots de passe ou secrets API.
""",
    "retours-fr": """💬 **Retours en français**

Vous pouvez poster ici vos retours, idées, bugs, captures d'écran non sensibles et remarques sur l'interface.
""",
}

GUIDE_MESSAGE_MARKERS = [
    "Bienvenue sur Gruterra",
    "Welcome to Gruterra",
    "Liens utiles",
    "Useful links",
    "Commandes bot",
    "Bot commands",
    "Bot log",
    "Aide installation",
    "Installation help",
    "Capteurs et données",
    "Sensors and data",
    "Retours mode démo",
    "Demo feedback",
    "Bugs / Bug reports",
    "Idées / Ideas",
    "Bienvenue dans l'espace français",
    "Aide installation en français",
    "Retours en français",
]

GUIDE_CHANNEL_NAMES = sorted(CHANNEL_STARTER_MESSAGES.keys())



SERVER_STRUCTURE = [
    (
        "📢 INFORMATION",
        [
            ("announcements", "Project announcements and important updates."),
            ("welcome", "Welcome message and first steps for new members."),
            ("changelog", "Visible changes, releases and notable fixes."),
            ("bot-log", "Automated setup notes and bot messages."),
            ("useful-links", "GitHub, demo guide, documentation and community links."),
        ],
        "read_only",
    ),
    (
        "🌱 GRUTERRA",
        [
            ("general", "General discussion about Gruterra."),
            ("plant-tracking", "Plant care, watering logs and observations."),
            ("sensors-and-data", "Mi Flora, Raspberry Pi, Netatmo and local data."),
            ("installation-help", "Help installing or running Gruterra."),
        ],
        "public",
    ),
    (
        "🇫🇷 FRANÇAIS",
        [
            ("discussion-fr", "Discussion en français autour de Gruterra."),
            ("aide-installation-fr", "Aide en français pour installer ou lancer Gruterra."),
            ("retours-fr", "Retours, idées et bugs en français."),
        ],
        "public",
    ),
    (
        "🧪 TESTS & FEEDBACK",
        [
            ("demo-feedback", "Feedback from the demo mode."),
            ("bugs-feedback", "Bug reports and unexpected behavior."),
            ("ideas", "Feature ideas and improvements."),
        ],
        "public",
    ),
    (
        "🔒 TEAM",
        [
            ("bot-commands", "Private manual bot commands for Gruterra admins."),
            ("admin-notes", "Private notes for server/project admins."),
            ("dev-follow-up", "Private development follow-up."),
        ],
        "private_admin",
    ),
]


def find_role(guild: discord.Guild, name: str) -> discord.Role | None:
    return discord.utils.get(guild.roles, name=name)


async def get_or_create_role(guild: discord.Guild, name: str) -> discord.Role:
    role = find_role(guild, name)
    if role is not None:
        return role
    return await guild.create_role(name=name, reason="Gruterra setup")


async def get_or_create_category(
    guild: discord.Guild,
    name: str,
    overwrites: dict | None = None,
) -> tuple[discord.CategoryChannel, str | None]:
    category = discord.utils.get(guild.categories, name=name)
    if category is not None:
        if overwrites is not None:
            try:
                await category.edit(overwrites=overwrites, reason="Gruterra setup")
            except discord.Forbidden:
                return category, f"Accès insuffisant pour mettre à jour la catégorie {category.name}."
        return category, None
    try:
        return await guild.create_category(name=name, overwrites=overwrites, reason="Gruterra setup"), None
    except discord.Forbidden:
        raise commands.CommandError(
            "Le bot n'a pas la permission de créer ou modifier les catégories. "
            "Vérifiez ses permissions Discord : Gérer les salons, Voir les salons, Envoyer des messages."
        )


async def get_or_create_text_channel(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    name: str,
    topic: str,
) -> tuple[discord.TextChannel, str | None]:
    existing = discord.utils.get(guild.text_channels, name=name)
    if existing is not None:
        if existing.category_id != category.id or existing.topic != topic:
            try:
                await existing.edit(category=category, topic=topic, reason="Gruterra setup")
            except discord.Forbidden:
                return existing, f"Accès insuffisant pour mettre à jour #{existing.name}."
        return existing, None
    try:
        return await guild.create_text_channel(name=name, category=category, topic=topic, reason="Gruterra setup"), None
    except discord.Forbidden:
        raise commands.CommandError(
            f"Le bot n'a pas la permission de créer le salon #{name}. "
            "Vérifiez ses permissions Discord : Gérer les salons, Voir les salons, Envoyer des messages."
        )


async def find_invite_channel(guild: discord.Guild) -> discord.TextChannel | None:
    for name in INVITE_CHANNEL_CANDIDATES:
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel is not None:
            return channel
    for channel in guild.text_channels:
        permissions = channel.permissions_for(guild.default_role)
        if permissions.view_channel:
            return channel
    return None


async def find_release_channel(guild: discord.Guild) -> discord.TextChannel | None:
    for name in RELEASE_CHANNEL_CANDIDATES:
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel is not None:
            return channel
    return await find_invite_channel(guild)


def load_release_manifest() -> dict:
    manifest_path = BASE_DIR.parent / "version_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def release_key_from_manifest(manifest: dict) -> str:
    version = str(manifest.get("version") or "").strip()
    sha256 = str(manifest.get("sha256") or "").strip()
    return f"{version}|{sha256}"


def manifest_release_annonceable(manifest: dict) -> bool:
    version = str(manifest.get("version") or "").strip()
    archive_url = str(manifest.get("archive_url") or "").strip()
    sha256 = str(manifest.get("sha256") or "").strip()
    auto_update = bool(manifest.get("mise_a_jour_automatique", False))
    return bool(version and archive_url and len(sha256) == 64 and auto_update)


def load_release_state() -> dict:
    if not AUTO_RELEASE_STATE_FILE.exists():
        return {}
    try:
        return json.loads(AUTO_RELEASE_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_release_state(state: dict) -> None:
    AUTO_RELEASE_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_release_changelog(version: str) -> str:
    chemin = BASE_DIR.parent / "_dist" / f"gruterra-{version}-changelog.md"
    if not chemin.exists():
        return ""
    try:
        return chemin.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def build_release_message(version_arg: str | None = None) -> str:
    manifest = load_release_manifest()
    version = str(version_arg or manifest.get("version") or "version à préciser").strip()
    notes = str(manifest.get("notes") or "Release Gruterra disponible.").strip()
    github_url = str(manifest.get("url") or "https://github.com/Botaneo-project/gruterra").strip()
    archive_url = str(manifest.get("archive_url") or "").strip()
    sha256 = str(manifest.get("sha256") or "").strip()
    tag = version if version.startswith("v") else f"v{version}"
    release_url = f"https://github.com/Botaneo-project/gruterra/releases/tag/{tag}"
    changelog = load_release_changelog(version)
    if changelog:
        notes = changelog[:1200]

    lignes = [
        f"🌿 **Gruterra {version}**",
        "",
        notes,
        "",
        f"GitHub: {github_url}",
        f"Release: {release_url}",
    ]
    if archive_url:
        lignes.append(f"Archive update: {archive_url}")
    if sha256:
        lignes.append(f"SHA256: `{sha256}`")
    lignes.extend([
        "",
        "Before updating, keep your local data folder and private config safe. The Gruterra updater verifies the archive hash before applying changes.",
        "",
        "FR : pensez à garder vos données locales et votre configuration privée. L’updater Gruterra vérifie le SHA256 avant application.",
    ])
    return "\n".join(lignes)


async def safe_reply(ctx: commands.Context, content: str) -> bool:
    """Répond à une commande sans faire planter le bot si le salon refuse l'écriture."""

    try:
        await ctx.reply(content[:1900])
        return True
    except discord.Forbidden:
        try:
            await ctx.author.send(
                "Je n’ai pas le droit d’écrire dans le salon où la commande a été lancée. "
                "Ajoutez au bot les permissions Voir le salon, Envoyer des messages et Voir les anciens messages, "
                "ou relancez la commande dans #bot-commands."
            )
            return True
        except discord.Forbidden:
            return False


async def safe_send_channel(channel: discord.TextChannel, content: str) -> bool:
    """Envoie un message dans un salon sans lever Forbidden vers les commandes."""

    try:
        await channel.send(content[:1900])
        return True
    except discord.Forbidden:
        return False


async def publish_presentation_message(guild: discord.Guild) -> str:
    channel = discord.utils.get(guild.text_channels, name="useful-links")
    if channel is None:
        channel = await find_invite_channel(guild)
    if channel is None:
        return "Message de présentation non publié : aucun salon public trouvé."

    try:
        async for message in channel.history(limit=30):
            if message.author == guild.me and "Welcome to Gruterra" in message.content:
                await message.edit(content=PRESENTATION_MESSAGE)
                return f"Message de présentation mis à jour dans #{channel.name}."

        await channel.send(PRESENTATION_MESSAGE)
    except discord.Forbidden:
        return f"Message de présentation non publié : accès insuffisant à #{channel.name}."
    return f"Message de présentation publié dans #{channel.name}."


async def is_guide_message(message: discord.Message) -> bool:
    if message.author != message.guild.me:
        return False
    return any(marker in message.content for marker in GUIDE_MESSAGE_MARKERS)


async def publish_channel_starter_messages(guild: discord.Guild) -> list[str]:
    results = []
    for channel_name, content in CHANNEL_STARTER_MESSAGES.items():
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            results.append(f"#{channel_name} introuvable : message non publié.")
            continue

        marker = content.splitlines()[0].replace("**", "")
        try:
            matching_messages = []
            async for message in channel.history(limit=80):
                if message.author == guild.me and (marker in message.content or await is_guide_message(message)):
                    matching_messages.append(message)

            target_message = None
            for message in matching_messages:
                if marker in message.content:
                    target_message = message
                    break
            if target_message is None and matching_messages:
                target_message = matching_messages[0]

            if target_message is None:
                await channel.send(content)
                results.append(f"#{channel.name} : message publié.")
                continue

            if target_message.content != content:
                await target_message.edit(content=content)
            deleted_duplicates = 0
            for message in matching_messages:
                if message.id == target_message.id or message.pinned:
                    continue
                try:
                    await message.delete()
                    deleted_duplicates += 1
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
            if deleted_duplicates:
                results.append(f"#{channel.name} : message mis à jour, {deleted_duplicates} doublon(s) supprimé(s).")
            else:
                results.append(f"#{channel.name} : message mis à jour.")
        except discord.Forbidden:
            results.append(f"#{channel.name} : accès insuffisant pour publier le message.")
    return results

async def ensure_bot_commands_permissions(
    guild: discord.Guild,
    admin_role: discord.Role,
    command_author: discord.abc.User | None = None,
) -> str:
    """Force les droits utiles sur #bot-commands, même si le salon existait déjà."""

    channel = discord.utils.get(guild.text_channels, name="bot-commands")
    if channel is None:
        return "#bot-commands introuvable : permissions non vérifiées."

    try:
        await channel.set_permissions(
            guild.default_role,
            view_channel=False,
            send_messages=False,
            read_message_history=False,
            reason="Gruterra bot-commands private setup",
        )
        await channel.set_permissions(
            admin_role,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_messages=True,
            reason="Gruterra bot-commands admin access",
        )
        if guild.me is not None:
            await channel.set_permissions(
                guild.me,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                reason="Gruterra bot-commands bot access",
            )
        if isinstance(command_author, discord.Member):
            await channel.set_permissions(
                command_author,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                reason="Gruterra bot-commands command author access",
            )
        return "#bot-commands : permissions privées vérifiées pour admin, bot et lanceur de commande."
    except discord.Forbidden:
        return "#bot-commands : permissions non modifiées, accès insuffisant pour le bot."
    except discord.HTTPException as exc:
        return f"#bot-commands : permissions non modifiées ({exc})."


async def ensure_pinned_bot_commands_message(guild: discord.Guild) -> str:
    channel = discord.utils.get(guild.text_channels, name="bot-commands")
    if channel is None:
        return "#bot-commands introuvable : mémo des commandes non épinglé."

    content = CHANNEL_STARTER_MESSAGES.get("bot-commands", "").strip()
    if not content:
        return "Mémo des commandes vide : rien à épingler."

    marker = "Commandes bot / Bot commands"
    try:
        target_message = None
        async for message in channel.history(limit=50):
            if message.author == guild.me and marker in message.content:
                target_message = message
                if message.content != content:
                    await message.edit(content=content)
                break
        if target_message is None:
            target_message = await channel.send(content)

        if not target_message.pinned:
            await target_message.pin(reason="Mémo des commandes Gruterra")
        return "Mémo des commandes épinglé dans #bot-commands."
    except discord.Forbidden:
        return "#bot-commands : accès insuffisant pour publier ou épingler le mémo des commandes."
    except discord.HTTPException as exc:
        return f"#bot-commands : épinglage impossible ({exc})."


def is_cleanup_target(message: discord.Message, guild: discord.Guild) -> bool:
    if message.pinned:
        return False
    return (
        message.author == guild.me
        or (
            not message.author.bot
            and any(message.content.startswith(prefix) for prefix in CLEANUP_COMMAND_PREFIXES)
        )
    )


async def cleanup_channel_messages(
    channel: discord.TextChannel,
    guild: discord.Guild,
    limit: int,
) -> tuple[int, str | None]:
    try:
        deleted = await channel.purge(
            limit=limit,
            check=lambda message: is_cleanup_target(message, guild),
            reason="Nettoyage des messages techniques Gruterra",
            bulk=True,
        )
    except discord.Forbidden:
        return 0, f"#{channel.name} : accès insuffisant pour supprimer les messages."
    except discord.HTTPException as exc:
        return 0, f"#{channel.name} : nettoyage impossible ({exc})."
    return len(deleted), None


async def publish_bot_log(guild: discord.Guild, title: str, lines: list[str]) -> str:
    channel = discord.utils.get(guild.text_channels, name="bot-log")
    if channel is None:
        return "Journal bot non publié : #bot-log introuvable."
    content = title + "\n" + "\n".join(f"- {line}" for line in lines)
    try:
        await channel.send(content[:1900])
    except discord.Forbidden:
        return "Journal bot non publié : accès insuffisant à #bot-log."
    return "Journal bot publié dans #bot-log."


async def announce_release_if_needed(guild: discord.Guild, *, force: bool = False) -> str:
    manifest = load_release_manifest()
    if not manifest_release_annonceable(manifest):
        return "Aucune release annonceable : manifeste incomplet ou auto-update désactivé."

    release_key = release_key_from_manifest(manifest)
    state = load_release_state()
    if not force and state.get("last_announced_release") == release_key:
        return "Release déjà annoncée, aucun message publié."

    channel = await find_release_channel(guild)
    if channel is None:
        return "Aucun salon disponible pour publier la release."

    await channel.send(build_release_message()[:1900])
    state["last_announced_release"] = release_key
    state["last_announced_version"] = str(manifest.get("version") or "")
    save_release_state(state)
    await publish_bot_log(
        guild,
        "🤖 **Release Gruterra annoncée automatiquement**",
        [
            f"Salon utilisé : #{channel.name}.",
            f"Version : {manifest.get('version')}.",
            "Annonce automatique anti-spam : cette version ne sera pas republiée.",
        ],
    )
    return f"Release publiée dans #{channel.name}."


def overwrites_for(guild: discord.Guild, mode: str, admin_role: discord.Role) -> dict:
    everyone = guild.default_role
    if mode == "private_admin":
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False),
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
        }
        if guild.me is not None:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            )
        return overwrites
    if mode == "read_only":
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
        }
        if guild.me is not None:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
            )
        return overwrites
    overwrites = {
        everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
    }
    if guild.me is not None:
        overwrites[guild.me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )
    return overwrites


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await safe_reply(ctx, "Commande refusée : votre compte n’a pas la permission Discord nécessaire.")
        return
    if isinstance(error, commands.BotMissingPermissions):
        await safe_reply(ctx, "Commande impossible : il manque une permission Discord au bot sur ce salon.")
        return
    if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
        await safe_reply(
            ctx,
            "Commande interrompue : Discord refuse une action du bot. "
            "Vérifiez ses permissions sur ce salon : Voir le salon, Envoyer des messages, Voir les anciens messages, "
            "Gérer les messages si nettoyage, Créer une invitation si invitation."
        )
        return
    raise error


@bot.event
async def on_ready() -> None:
    print(f"Gruterra Discord bot connecté : {bot.user}")
    if AUTO_RELEASE_ENABLED and not auto_release_watcher.is_running():
        auto_release_watcher.change_interval(minutes=AUTO_RELEASE_INTERVAL_MINUTES)
        auto_release_watcher.start()


@tasks.loop(minutes=AUTO_RELEASE_INTERVAL_MINUTES)
async def auto_release_watcher() -> None:
    if not AUTO_RELEASE_ENABLED:
        return
    guilds = list(bot.guilds)
    if AUTO_RELEASE_GUILD_ID:
        guild = bot.get_guild(int(AUTO_RELEASE_GUILD_ID)) if AUTO_RELEASE_GUILD_ID.isdigit() else None
        guilds = [guild] if guild is not None else []
    for guild in guilds:
        try:
            result = await announce_release_if_needed(guild)
            if "publiée" in result:
                print(result)
        except Exception as exc:
            print(f"Annonce release automatique impossible pour {guild.name}: {exc}")


@bot.command(name="setup_gruterra")
@commands.has_permissions(manage_guild=True)
async def setup_gruterra(ctx: commands.Context) -> None:
    """Crée la structure Discord Gruterra sans supprimer l'existant."""

    if not SETUP_ENABLED:
        await ctx.reply("La commande de setup Gruterra est désactivée. Réactivez-la temporairement dans discord_bot/.env si nécessaire.")
        return

    guild = ctx.guild
    if guild is None:
        await ctx.reply("Cette commande doit être lancée dans un serveur Discord.")
        return

    await ctx.reply("Préparation du serveur Gruterra en cours…")

    roles = {name: await get_or_create_role(guild, name) for name in ROLE_NAMES}
    admin_role = roles["Gruterra Admin"]

    created_or_checked = []
    warnings = []
    for category_name, channels, mode in SERVER_STRUCTURE:
        category, warning = await get_or_create_category(
            guild,
            category_name,
            overwrites_for(guild, mode, admin_role),
        )
        if warning:
            warnings.append(warning)
        created_or_checked.append(category.name)
        for channel_name, topic in channels:
            channel, warning = await get_or_create_text_channel(guild, category, channel_name, topic)
            if warning:
                warnings.append(warning)
            created_or_checked.append(f"#{channel.name}")

    bot_commands_perm_status = await ensure_bot_commands_permissions(guild, admin_role, ctx.author)
    presentation_status = await publish_presentation_message(guild)
    starter_statuses = await publish_channel_starter_messages(guild)
    commands_pin_status = await ensure_pinned_bot_commands_message(guild)

    message = (
        "Structure Gruterra prête. Rôles et salons vérifiés :\n"
        + "\n".join(f"- {item}" for item in created_or_checked)
        + f"\n\n{presentation_status}"
        + f"\n{bot_commands_perm_status}"
        + f"\n{commands_pin_status}"
    )
    if starter_statuses:
        message += "\n\nMessages d'accueil et d'aide :\n" + "\n".join(f"- {item}" for item in starter_statuses[:8])
        if len(starter_statuses) > 8:
            message += f"\n- {len(starter_statuses) - 8} autre(s) message(s) vérifié(s)."
    if warnings:
        message += "\n\nPoints à vérifier manuellement :\n" + "\n".join(f"- {item}" for item in warnings)

    log_lines = [
        f"{len(created_or_checked)} rôle(s), catégorie(s) ou salon(s) vérifié(s).",
        presentation_status,
        f"{len(starter_statuses)} message(s) d'accueil ou d'aide vérifié(s).",
        bot_commands_perm_status,
        commands_pin_status,
    ]
    if warnings:
        log_lines.extend(warnings)
    bot_log_status = await publish_bot_log(guild, "🤖 **Setup Gruterra exécuté**", log_lines)
    message += f"\n\n{bot_log_status}"
    await ctx.reply(message[:1900])


@bot.command(name="fix_bot_commands")
@commands.has_permissions(manage_guild=True)
async def fix_bot_commands(ctx: commands.Context) -> None:
    """Répare les droits du salon privé #bot-commands."""

    guild = ctx.guild
    if guild is None:
        await safe_reply(ctx, "Cette commande doit être lancée dans un serveur Discord.")
        return

    admin_role = find_role(guild, "Gruterra Admin")
    if admin_role is None:
        admin_role = await get_or_create_role(guild, "Gruterra Admin")

    perm_status = await ensure_bot_commands_permissions(guild, admin_role, ctx.author)
    pin_status = await ensure_pinned_bot_commands_message(guild)
    await safe_reply(ctx, f"Réparation #bot-commands terminée.\n- {perm_status}\n- {pin_status}")


@bot.command(name="reset_guides_gruterra")
@commands.has_permissions(manage_messages=True)
async def reset_guides_gruterra(ctx: commands.Context, limit: int = 120) -> None:
    """Supprime les anciens messages de guide du bot puis les republie proprement."""

    guild = ctx.guild
    if guild is None:
        await safe_reply(ctx, "Cette commande doit être lancée dans un serveur Discord.")
        return

    limit = max(30, min(limit, 300))
    await safe_reply(ctx, f"Reset des guides Gruterra en cours sur les {limit} derniers messages des salons connus…")

    deleted_total = 0
    warnings = []
    for channel_name in GUIDE_CHANNEL_NAMES:
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            continue
        try:
            deleted = await channel.purge(
                limit=limit,
                check=lambda message: (
                    message.author == guild.me
                    and not message.pinned
                    and any(marker in message.content for marker in GUIDE_MESSAGE_MARKERS)
                ),
                reason="Reset des guides Gruterra",
                bulk=True,
            )
            deleted_total += len(deleted)
        except discord.Forbidden:
            warnings.append(f"#{channel.name} : accès insuffisant pour nettoyer.")
        except discord.HTTPException as exc:
            warnings.append(f"#{channel.name} : nettoyage impossible ({exc}).")

    presentation_status = await publish_presentation_message(guild)
    starter_statuses = await publish_channel_starter_messages(guild)
    commands_pin_status = await ensure_pinned_bot_commands_message(guild)

    lines = [
        f"{deleted_total} ancien(s) message(s) de guide supprimé(s).",
        presentation_status,
        commands_pin_status,
        *starter_statuses,
        *warnings,
    ]
    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Reset des guides Gruterra exécuté**",
        lines[:12],
    )

    message = "Reset guides terminé :\n" + "\n".join(f"- {line}" for line in lines[:12])
    if len(lines) > 12:
        message += f"\n- {len(lines) - 12} autre(s) résultat(s)."
    message += f"\n\n{bot_log_status}"
    await safe_reply(ctx, message)


@bot.command(name="post_guides_gruterra")
@commands.has_permissions(manage_guild=True)
async def post_guides_gruterra(ctx: commands.Context) -> None:
    """Publie ou met à jour les messages d'accueil et de tutoriel dans les bons salons."""

    guild = ctx.guild
    if guild is None:
        await ctx.reply("Cette commande doit être lancée dans un serveur Discord.")
        return

    await safe_reply(ctx, "Publication ou mise à jour des guides Gruterra en cours…")

    presentation_status = await publish_presentation_message(guild)
    starter_statuses = await publish_channel_starter_messages(guild)
    commands_pin_status = await ensure_pinned_bot_commands_message(guild)

    lines = [presentation_status, commands_pin_status, *starter_statuses]
    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Guides Gruterra publiés**",
        [
            presentation_status,
            f"{len(starter_statuses)} salon(s) de guide vérifié(s).",
            commands_pin_status,
            "Commande utilisée : !post_guides_gruterra.",
        ],
    )

    message = "Guides Gruterra vérifiés :\n" + "\n".join(f"- {line}" for line in lines[:12])
    if len(lines) > 12:
        message += f"\n- {len(lines) - 12} autre(s) résultat(s)."
    message += f"\n\n{bot_log_status}"
    await safe_reply(ctx, message)


@bot.command(name="invite_gruterra")
@commands.has_permissions(manage_guild=True)
async def invite_gruterra(ctx: commands.Context) -> None:
    """Crée une invitation pour des utilisateurs de base."""

    guild = ctx.guild
    if guild is None:
        await ctx.reply("Cette commande doit être lancée dans un serveur Discord.")
        return

    channel = await find_invite_channel(guild)
    if channel is None:
        await ctx.reply("Aucun salon public disponible pour créer une invitation.")
        return

    try:
        invite = await channel.create_invite(
            max_age=0,
            max_uses=0,
            unique=False,
            reason="Invitation publique Gruterra",
        )
    except discord.Forbidden:
        await ctx.reply(
            f"Impossible de créer une invitation dans #{channel.name}. "
            "Ajoutez au bot la permission Créer une invitation instantanée sur ce salon."
        )
        return
    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Invitation Gruterra générée**",
        [
            f"Salon utilisé : #{channel.name}.",
            "Invitation pour utilisateurs de base, sans rôle administrateur automatique.",
        ],
    )
    await ctx.reply(
        "Invitation Gruterra pour utilisateurs de base :\n"
        f"{invite.url}\n\n"
        "Elle donne accès au serveur avec les droits normaux du rôle @everyone. "
        "Les droits administrateur restent séparés.\n\n"
        f"{bot_log_status}"
    )


@bot.command(name="clean_gruterra_messages")
@commands.has_permissions(manage_messages=True)
async def clean_gruterra_messages(ctx: commands.Context, limit: int = 100) -> None:
    """Nettoie les anciens messages techniques du bot et les commandes de setup."""

    guild = ctx.guild
    if guild is None:
        await ctx.reply("Cette commande doit être lancée dans un serveur Discord.")
        return

    limit = max(10, min(limit, 300))
    deleted_total = 0
    checked_channels = 0

    await ctx.reply(f"Nettoyage Gruterra en cours sur les {limit} derniers messages des salons connus…")

    for channel_name in CLEANUP_CHANNEL_CANDIDATES:
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            continue
        checked_channels += 1
        deleted_count, warning = await cleanup_channel_messages(channel, guild, limit)
        deleted_total += deleted_count

    commands_pin_status = await ensure_pinned_bot_commands_message(guild)
    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Nettoyage des messages Gruterra exécuté**",
        [
            f"{checked_channels} salon(s) vérifié(s).",
            f"{deleted_total} message(s) technique(s) supprimé(s).",
            "Messages ciblés : messages du bot et commandes Gruterra visibles non épinglées.",
            commands_pin_status,
        ],
    )
    await ctx.reply(
        f"Nettoyage terminé : {deleted_total} message(s) technique(s) supprimé(s).\n"
        f"{bot_log_status}"
    )


@bot.command(name="clean_here")
@commands.has_permissions(manage_messages=True)
async def clean_here(ctx: commands.Context, limit: int = 100) -> None:
    """Nettoie les messages techniques Gruterra seulement dans le salon actuel."""

    guild = ctx.guild
    channel = ctx.channel
    if guild is None or not isinstance(channel, discord.TextChannel):
        await ctx.reply("Cette commande doit être lancée dans un salon texte Discord.")
        return

    limit = max(10, min(limit, 300))
    deleted_count, warning = await cleanup_channel_messages(channel, guild, limit)
    if warning:
        await ctx.reply(warning)
        return

    commands_pin_status = await ensure_pinned_bot_commands_message(guild)
    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Nettoyage local Gruterra exécuté**",
        [
            f"Salon nettoyé : #{channel.name}.",
            f"{deleted_count} message(s) technique(s) supprimé(s).",
            "Les messages épinglés sont conservés.",
            commands_pin_status,
        ],
    )
    await ctx.send(
        f"Nettoyage de #{channel.name} terminé : {deleted_count} message(s) supprimé(s).\n"
        f"{bot_log_status}"
    )


@bot.command(name="release_gruterra")
@commands.has_permissions(manage_guild=True)
async def release_gruterra(ctx: commands.Context, version: str | None = None) -> None:
    """Publie un message de release Gruterra dans le salon changelog."""

    guild = ctx.guild
    if guild is None:
        await ctx.reply("Cette commande doit être lancée dans un serveur Discord.")
        return

    channel = await find_release_channel(guild)
    if channel is None:
        await ctx.reply("Aucun salon disponible pour publier la release Gruterra.")
        return

    message = build_release_message(version)
    try:
        await channel.send(message[:1900])
    except discord.Forbidden:
        await ctx.reply(f"Impossible de publier la release dans #{channel.name} : accès insuffisant.")
        return

    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Release Gruterra annoncée**",
        [
            f"Salon utilisé : #{channel.name}.",
            f"Version annoncée : {version or load_release_manifest().get('version') or 'non précisée'}.",
        ],
    )
    await ctx.reply(f"Message de release publié dans #{channel.name}.\n{bot_log_status}")


@bot.command(name="auto_release_check")
@commands.has_permissions(manage_guild=True)
async def auto_release_check(ctx: commands.Context, force: str = "") -> None:
    """Vérifie la logique d’annonce automatique de release."""

    guild = ctx.guild
    if guild is None:
        await ctx.reply("Cette commande doit être lancée dans un serveur Discord.")
        return
    result = await announce_release_if_needed(guild, force=force.lower() in {"force", "forcer", "1"})
    await ctx.reply(result)


@bot.command(name="help_gruterra", aliases=["aide_gruterra"])
async def help_gruterra(ctx: commands.Context) -> None:
    """Affiche les premières commandes utiles du serveur Gruterra."""

    await ctx.reply(
        "🌱 **Gruterra — aide rapide / quick help**\n"
        "Projet francophone ouvert aux échanges en anglais.\n\n"
        "- `!github_gruterra` : liens GitHub et guides.\n"
        "- `!release_gruterra` : annoncer une release, réservé aux personnes pouvant gérer le serveur.\n"
        "- `!auto_release_check` : tester l’annonce automatique anti-spam d’une release.\n"
        "- `!report_bug` ou `!bug` : modèle pour signaler un bug.\n"
        "- `!idea` ou `!idee` : modèle pour proposer une idée.\n"
        "- `!netatmo_help` ou `!aide_netatmo` : aide connexion Netatmo.\n"
        "- `!raspberry_help` ou `!aide_raspberry` : aide Raspberry Pi.\n"
        "- `!invite_gruterra` : générer une invitation, réservé aux personnes pouvant gérer le serveur.\n"
        "- `!clean_here` : nettoyer les messages techniques du salon, réservé à la modération.\n\n"
        "Commencez par #welcome, #useful-links, #discussion-fr ou #installation-help."
    )


@bot.command(name="github_gruterra")
async def github_gruterra(ctx: commands.Context) -> None:
    """Affiche les liens utiles du projet Gruterra."""

    await ctx.reply(
        "🔗 **Gruterra links**\n"
        "GitHub: https://github.com/Botaneo-project/gruterra\n\n"
        "Useful files to start with:\n"
        "- `README.md` : project overview.\n"
        "- `GUIDE_DEMO.md` : try Gruterra without sensors.\n"
        "- `GUIDE_NETATMO.md` : Netatmo setup.\n"
        "- `ROADMAP.md` and `TODO.md` : upcoming work."
    )


@bot.command(name="report_bug", aliases=["bug"])
async def report_bug(ctx: commands.Context) -> None:
    """Donne un modèle simple de signalement de bug."""

    await ctx.reply(
        "🐛 **Bug report template**\n"
        "Please include:\n"
        "1. What you clicked or launched.\n"
        "2. What you expected.\n"
        "3. What happened instead.\n"
        "4. Screenshot or exact error message.\n"
        "5. Setup: demo / Mi Flora / Raspberry Pi / Netatmo / Windows.\n\n"
        "Do not share tokens, passwords, refresh tokens or private config files."
    )


@bot.command(name="idea", aliases=["idee"])
async def idea(ctx: commands.Context) -> None:
    """Donne un modèle simple pour proposer une idée."""

    await ctx.reply(
        "💡 **Idea template**\n"
        "You can describe:\n"
        "1. The problem or need.\n"
        "2. Your proposed feature.\n"
        "3. Why it would help plant tracking.\n"
        "4. Whether it concerns UI, sensors, Raspberry Pi, Netatmo, alerts or analysis."
    )


@bot.command(name="netatmo_help", aliases=["aide_netatmo"])
async def netatmo_help(ctx: commands.Context) -> None:
    """Rappelle les bases de la configuration Netatmo."""

    await ctx.reply(
        "🌦️ **Netatmo setup help**\n"
        "Gruterra can use Netatmo data when you configure your own API access locally.\n\n"
        "Start with `GUIDE_NETATMO.md` in the GitHub repository.\n"
        "Keep credentials only in your private local `_config` folder.\n"
        "Never post client secrets, access tokens or refresh tokens on Discord, GitHub or Reddit."
    )


@bot.command(name="raspberry_help", aliases=["aide_raspberry"])
async def raspberry_help(ctx: commands.Context) -> None:
    """Rappelle les bases de la configuration Raspberry Pi."""

    await ctx.reply(
        "🍓 **Raspberry Pi help**\n"
        "The Raspberry Pi collector is meant to collect Mi Flora / Flower Care data regularly and let the PC app import it later.\n\n"
        "Useful details when asking for help:\n"
        "- Raspberry Pi model and OS.\n"
        "- Bluetooth status.\n"
        "- Sensor address if relevant.\n"
        "- Last sync message from Gruterra.\n"
        "- Whether the PC app can reach the Raspberry Pi on the local network."
    )


@help_gruterra.error
@github_gruterra.error
@report_bug.error
@idea.error
@netatmo_help.error
@raspberry_help.error
async def public_help_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    await ctx.reply(f"Erreur pendant l'aide Gruterra : {error}")


@auto_release_check.error
async def auto_release_check_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer le serveur pour tester l’annonce automatique de release.")
        return
    await ctx.reply(f"Erreur pendant le contrôle d’annonce automatique : {error}")


@release_gruterra.error
async def release_gruterra_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer le serveur pour annoncer une release Gruterra.")
        return
    await ctx.reply(f"Erreur pendant l’annonce de release Gruterra : {error}")


@setup_gruterra.error
async def setup_gruterra_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer le serveur pour lancer cette commande.")
        return
    await ctx.reply(f"Erreur pendant le setup Gruterra : {error}")


@clean_here.error
async def clean_here_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer les messages pour nettoyer ce salon.")
        return
    await ctx.reply(f"Erreur pendant le nettoyage de ce salon : {error}")


@clean_gruterra_messages.error
async def clean_gruterra_messages_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer les messages pour nettoyer les messages Gruterra.")
        return
    await ctx.reply(f"Erreur pendant le nettoyage des messages Gruterra : {error}")


@invite_gruterra.error
async def invite_gruterra_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer le serveur pour créer une invitation Gruterra.")
        return
    await ctx.reply(f"Erreur pendant la création de l'invitation Gruterra : {error}")


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "Token Discord absent. Créez discord_bot/.env à partir de discord_bot/.env.example."
        )
    bot.run(TOKEN)


if __name__ == "__main__":
    main()