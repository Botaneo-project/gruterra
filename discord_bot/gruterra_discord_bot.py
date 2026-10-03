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

SERVER_STRUCTURE = [
    (
        "📢 INFORMATION",
        [
            ("announcements", "Project announcements and important updates."),
            ("changelog", "Visible changes, releases and notable fixes."),
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
) -> discord.CategoryChannel:
    category = discord.utils.get(guild.categories, name=name)
    if category is not None:
        if overwrites is not None:
            await category.edit(overwrites=overwrites, reason="Gruterra setup")
        return category
    return await guild.create_category(name=name, overwrites=overwrites, reason="Gruterra setup")


async def get_or_create_text_channel(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    name: str,
    topic: str,
) -> discord.TextChannel:
    existing = discord.utils.get(guild.text_channels, name=name)
    if existing is not None:
        if existing.category_id != category.id or existing.topic != topic:
            await existing.edit(category=category, topic=topic, reason="Gruterra setup")
        return existing
    return await guild.create_text_channel(name=name, category=category, topic=topic, reason="Gruterra setup")


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
    for category_name, channels, mode in SERVER_STRUCTURE:
        category = await get_or_create_category(
            guild,
            category_name,
            overwrites_for(guild, mode, admin_role),
        )
        created_or_checked.append(category.name)
        for channel_name, topic in channels:
            channel = await get_or_create_text_channel(guild, category, channel_name, topic)
            created_or_checked.append(f"#{channel.name}")

    await ctx.reply(
        "Structure Gruterra prête. Rôles et salons vérifiés :\n"
        + "\n".join(f"- {item}" for item in created_or_checked)
    )


@setup_gruterra.error
async def setup_gruterra_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Il faut la permission de gérer le serveur pour lancer cette commande.")
        return
    await ctx.reply(f"Erreur pendant le setup Gruterra : {error}")


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "Token Discord absent. Créez discord_bot/.env à partir de discord_bot/.env.example."
        )
    bot.run(TOKEN)


if __name__ == "__main__":
    main()