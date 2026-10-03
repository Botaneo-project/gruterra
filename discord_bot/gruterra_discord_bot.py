"""Bot Discord optionnel pour préparer le serveur communautaire Gruterra.

Le token doit rester dans discord_bot/.env et ne doit jamais être publié.
"""

from __future__ import annotations

import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
COMMAND_PREFIX = "!"
SETUP_ENABLED = os.environ.get("DISCORD_SETUP_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}

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
    "general",
    "discussion-fr",
    "useful-links",
]

CLEANUP_CHANNEL_CANDIDATES = [
    "announcements",
    "welcome",
    "changelog",
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
)

PRESENTATION_MESSAGE = """🌱 **Welcome to Gruterra**

Gruterra is an open-source plant tracking app focused on real measurements, watering history, light exposure and practical plant care decisions.

What you can find here:
- installation help and demo feedback;
- Mi Flora / Flower Care, Raspberry Pi and Netatmo discussions;
- watering cycle analysis and plant observations;
- ideas, bugs and roadmap suggestions.

GitHub: https://github.com/Botaneo-project/gruterra

French-speaking users are welcome in the French channels.
"""

CHANNEL_STARTER_MESSAGES = {
    "welcome": """🌱 **Welcome to Gruterra**

Say hi here when you join. You can tell us what brought you here: demo mode, Mi Flora / Flower Care, Raspberry Pi, Netatmo, plant care tracking, or curiosity.

A few useful first steps:
- try the demo mode if you do not have sensors yet;
- check #useful-links for GitHub and documentation;
- use #installation-help if the app does not start;
- use #discussion-fr if you prefer French.
""",
    "useful-links": """🔗 **Useful links**

GitHub repository:
https://github.com/Botaneo-project/gruterra

Start here:
- README for the project overview;
- GUIDE_DEMO for testing without real sensors;
- GUIDE_NETATMO for Netatmo setup;
- ROADMAP and TODO for upcoming work.
""",
    "bot-log": """🤖 **Bot log**

This channel is dedicated to automated Gruterra bot messages: setup results, structure updates, invite generation notes and future maintenance messages.

Keeping bot messages here avoids mixing technical setup details with public discussion channels.
""",
    "installation-help": """🛠️ **Installation help**

If you need help, please include:
- Windows / Raspberry Pi / other;
- how you launched Gruterra;
- the exact error message or a screenshot;
- whether you use demo mode, Mi Flora, Raspberry Pi or Netatmo.

Never share private tokens, passwords, refresh tokens or API secrets.
""",
    "sensors-and-data": """📡 **Sensors and data**

This channel is for Mi Flora / Flower Care, Raspberry Pi collection, Netatmo data, Bluetooth issues and data quality.

Helpful details when reporting a problem:
- sensor type;
- PC or Raspberry Pi collection;
- last successful sync time;
- whether history import worked;
- suspicious values such as missing dates or all-zero measurements.
""",
    "demo-feedback": """🧪 **Demo feedback**

Use this channel if you tested Gruterra without real sensors. Useful feedback:
- what was clear or confusing;
- whether the screenshots and demo data helped;
- what you expected to click first;
- what information was missing.
""",
    "bugs-feedback": """🐛 **Bug reports**

When possible, include:
- what you clicked;
- what you expected;
- what happened instead;
- the visible error message;
- whether the issue is reproducible.

Please avoid posting secrets or private configuration files.
""",
    "ideas": """💡 **Ideas**

Share ideas for plant analysis, watering cycles, light tracking, Raspberry Pi collection, Netatmo, UI improvements or documentation.

Small practical ideas are welcome too.
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


async def publish_channel_starter_messages(guild: discord.Guild) -> list[str]:
    results = []
    for channel_name, content in CHANNEL_STARTER_MESSAGES.items():
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            results.append(f"#{channel_name} introuvable : message non publié.")
            continue
        marker = content.splitlines()[0].replace("**", "")
        try:
            async for message in channel.history(limit=30):
                if message.author == guild.me and marker in message.content:
                    await message.edit(content=content)
                    results.append(f"#{channel.name} : message mis à jour.")
                    break
            else:
                await channel.send(content)
                results.append(f"#{channel.name} : message publié.")
        except discord.Forbidden:
            results.append(f"#{channel.name} : accès insuffisant pour publier le message.")
    return results


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
        return {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
        }
    return {
        everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
    }


@bot.event
async def on_ready() -> None:
    print(f"Gruterra Discord bot connecté : {bot.user}")


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

    presentation_status = await publish_presentation_message(guild)
    starter_statuses = await publish_channel_starter_messages(guild)

    message = (
        "Structure Gruterra prête. Rôles et salons vérifiés :\n"
        + "\n".join(f"- {item}" for item in created_or_checked)
        + f"\n\n{presentation_status}"
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
    ]
    if warnings:
        log_lines.extend(warnings)
    bot_log_status = await publish_bot_log(guild, "🤖 **Setup Gruterra exécuté**", log_lines)
    message += f"\n\n{bot_log_status}"
    await ctx.reply(message[:1900])


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
        try:
            deleted = await channel.purge(
                limit=limit,
                check=lambda message: (
                    message.author == guild.me
                    or (
                        not message.author.bot
                        and any(message.content.startswith(prefix) for prefix in CLEANUP_COMMAND_PREFIXES)
                    )
                ),
                reason="Nettoyage des messages techniques Gruterra",
                bulk=True,
            )
        except discord.Forbidden:
            continue
        deleted_total += len(deleted)

    bot_log_status = await publish_bot_log(
        guild,
        "🤖 **Nettoyage des messages Gruterra exécuté**",
        [
            f"{checked_channels} salon(s) vérifié(s).",
            f"{deleted_total} message(s) technique(s) supprimé(s).",
            "Messages ciblés : messages du bot et commandes Gruterra visibles.",
        ],
    )
    await ctx.reply(
        f"Nettoyage terminé : {deleted_total} message(s) technique(s) supprimé(s).\n"
        f"{bot_log_status}"
    )


@setup_gruterra.error
async def setup_gruterra_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer le serveur pour lancer cette commande.")
        return
    await ctx.reply(f"Erreur pendant le setup Gruterra : {error}")


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