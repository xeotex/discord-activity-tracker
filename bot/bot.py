import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import init_db
from voice_tracking import start_session, end_open_session
from stats import get_total_seconds, format_duration
from discord import app_commands
from stats import get_total_seconds, get_total_seconds_since, start_of_week, start_of_month, format_duration
from stats import get_total_seconds, get_total_seconds_since, start_of_week, start_of_month, format_duration, get_channel_leaderboard
from stats import get_total_seconds, get_total_seconds_since, start_of_week, start_of_month, format_duration, get_channel_leaderboard, get_overlap_leaderboard
from stats import get_total_seconds, get_total_seconds_since, start_of_week, start_of_month, format_duration, get_channel_leaderboard, get_overlap_leaderboard, get_server_leaderboard
from voice_tracking import start_session, end_open_session, reconcile_sessions
from discord.ext import tasks
from archive import archive_old_sessions

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)



@bot.event
async def on_ready():
    init_db()

    guild = bot.get_guild(GUILD_ID)
    if guild is not None:
        reconcile_sessions(guild)
        print("Voice-Sessions mit aktuellem Status abgeglichen.")

    synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{len(synced)} Slash-Commands synchronisiert.")
    print(f"Eingeloggt als {bot.user} (ID: {bot.user.id})")

    if not daily_archive_task.is_running():
        daily_archive_task.start()
 

# User aktivitäten im Voice Channel
@bot.event
async def on_voice_state_update(member, before, after):
   
    if before.channel is not None:
        end_open_session(member.id)

    if after.channel is not None:
        start_session(member.guild.id, member.id, after.channel.id)


@bot.tree.command(name="vping", description="Testet, ob der Voice-Stats-Bot reagiert", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")        


@bot.tree.command(name="vstats", description="Zeigt die Voice-Zeit eines Users", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Welcher User (leer = du selbst)", zeitraum="Welcher Zeitraum")
@app_commands.choices(zeitraum=[
    app_commands.Choice(name="Gesamt", value="all"),
    app_commands.Choice(name="Diese Woche", value="week"),
    app_commands.Choice(name="Diesen Monat", value="month"),
])
async def vstats(interaction: discord.Interaction, user: discord.Member = None, zeitraum: app_commands.Choice[str] = None):
    target = user or interaction.user
    period = zeitraum.value if zeitraum is not None else "all"

    if period == "week":
        seconds = get_total_seconds_since(target.id, start_of_week())
        label = "Diese Woche"
    elif period == "month":
        seconds = get_total_seconds_since(target.id, start_of_month())
        label = "Diesen Monat"
    else:
        seconds = get_total_seconds(target.id)
        label = "Gesamt"

    embed = discord.Embed(
        title=f"🎙️ Voice-Zeit von {target.display_name}",
        description=f"**{label}:** {format_duration(seconds)}",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=target.display_avatar.url)

    await interaction.response.send_message(embed=embed)
    

@bot.tree.command(name="vchannelstats", description="Zeigt, wer wie lange in einem Voice-Channel war", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="Welcher Voice-Channel")
async def vchannelstats(interaction: discord.Interaction, channel: discord.VoiceChannel):
    leaderboard = get_channel_leaderboard(channel.id)

    embed = discord.Embed(
        title=f"🔊 Stats für #{channel.name}",
        color=discord.Color.green()
    )

    if not leaderboard:
        embed.description = "Für diesen Channel liegen noch keine Daten vor."
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, seconds) in enumerate(leaderboard[:10]):
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member is not None else f"Unbekannt ({user_id})"
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{prefix} **{name}** — {format_duration(seconds)}")
        embed.description = "\n".join(lines)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="vwithme", description="Zeigt, mit wem ein User am meisten gemeinsame Voice-Zeit hatte", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Welcher User (leer = du selbst)")
async def vwithme(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    leaderboard = get_overlap_leaderboard(target.id)

    embed = discord.Embed(
        title=f"👥 Gemeinsame Voice-Zeit mit {target.display_name}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=target.display_avatar.url)

    if not leaderboard:
        embed.description = "Noch keine gemeinsamen Zeiten vorhanden."
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (other_id, seconds) in enumerate(leaderboard[:10]):
            member = interaction.guild.get_member(int(other_id))
            name = member.display_name if member is not None else f"Unbekannt ({other_id})"
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{prefix} **{name}** — {format_duration(seconds)}")
        embed.description = "\n".join(lines)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="vleaderboard", description="Server-weites Voice-Ranking", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(zeitraum="Welcher Zeitraum")
@app_commands.choices(zeitraum=[
    app_commands.Choice(name="Gesamt", value="all"),
    app_commands.Choice(name="Diese Woche", value="week"),
    app_commands.Choice(name="Diesen Monat", value="month"),
])
async def vleaderboard(interaction: discord.Interaction, zeitraum: app_commands.Choice[str] = None):
    period = zeitraum.value if zeitraum is not None else "all"

    if period == "week":
        leaderboard = get_server_leaderboard(interaction.guild.id, start_of_week())
        label = "Diese Woche"
    elif period == "month":
        leaderboard = get_server_leaderboard(interaction.guild.id, start_of_month())
        label = "Diesen Monat"
    else:
        leaderboard = get_server_leaderboard(interaction.guild.id)
        label = "Gesamt"

    embed = discord.Embed(
        title=f"🏆 Voice-Ranking — {label}",
        color=discord.Color.orange()
    )

    if not leaderboard:
        embed.description = "Für diesen Zeitraum liegen noch keine Daten vor."
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, seconds) in enumerate(leaderboard[:10]):
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member is not None else f"Unbekannt ({user_id})"
            prefix = medals[i] if i < 3 else f"{i + 1}."
            lines.append(f"{prefix} **{name}** — {format_duration(seconds)}")
        embed.description = "\n".join(lines)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vhelp", description="Zeigt alle Befehle des Bots", guild=discord.Object(id=GUILD_ID))
async def vhelp(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Voice-Stats-Bot – Befehle",
        color=discord.Color.blurple()
    )
    embed.add_field(name="/vstats", value="Voice-Zeit eines Users (Gesamt/Woche/Monat)", inline=False)
    embed.add_field(name="/vchannelstats", value="Ranking der User in einem Channel", inline=False)
    embed.add_field(name="/vwithme", value="Wer war am meisten gleichzeitig mit dir da", inline=False)
    embed.add_field(name="/vleaderboard", value="Server-weites Ranking (Gesamt/Woche/Monat)", inline=False)
    embed.add_field(name="/vhelp", value="Zeigt diese Übersicht", inline=False)

    await interaction.response.send_message(embed=embed)


@tasks.loop(hours=24)
async def daily_archive_task():
    count = archive_old_sessions()
    if count > 0:
        print(f"Archivierung: {count} alte Sessions archiviert und gelöscht.")


bot.run(TOKEN)