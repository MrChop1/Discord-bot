#importing discord
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

# Change the id's with your roles and stuff like that
WELCOME_CHANNEL_ID = 1402696156433223912
DIVISION1_ROLE_ID = 1410734604867993721
DIVISION2_ROLE_ID = 1410734861144031262
DIVISION3_ROLE_ID = 1410734981361172631
DIVISION4_ROLE_ID =1410735078925144145

# This is the default bot perfix but you can add whatever you want
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"🎉 Welcome to the server, {member.mention}! We're glad to have you here.")
    
    # Optional: Send a DM to the new member
    try:
        await member.send(
            f"👋 Hi {member.name}, welcome to **{member.guild.name}**!\n"
            "We're excited to have you join us. If you have any questions or need help, feel free to ask!"
        )
    except discord.Forbidden:
        print(f"Couldn't DM {member.name}.")

@bot.command(name='welcome_event')
@commands.has_permissions(administrator=True)  # Optional: limit who can trigger this
async def welcome_event(ctx):
    await ctx.send(
        "**🎉 Welcome Aboard! Meet & Greet 🎉**\n"
        "We're thrilled to welcome all our new members!\n\n"
        "**👤 Introductions** – Tell us a bit about yourself!\n"
        "**❓ Q&A** – Got questions? Ask away!\n"
        "**🧊 Icebreaker** – What's your favorite movie or game?\n"
        "\nLet’s make some awesome memories together. 💬"
    )

@bot.command()
async def add(ctx, member: discord.Member, *, role_name: str):
    # Replace with your actual Permit role ID (as an integer)
    PERMIT_ROLE_ID = 1410758236436693002  # <-- change this

    # Check if the command author has the Permit role
    permit_role = discord.utils.get(ctx.author.roles, id=PERMIT_ROLE_ID)
    if permit_role is None:
        await ctx.send("❌ You don't have permission to use this command.")
        return

    # Get the target role from the server (case-insensitive match)
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
    if role is None:
        await ctx.send(f"❌ The role `{role_name}` does not exist.")
        return

    # Add or remove the role from the target member
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"➖ Removed role `{role.name}` from {member.mention}.")
    else:
        await member.add_roles(role)
        await ctx.send(f"✅ Added role `{role.name}` to {member.mention}.")

# Store temporary user data
bot.cached_logs = {}

# -------- Modal 1 --------
class TryoutModal(discord.ui.Modal, title="Tryout Log Form"):
    player_name = discord.ui.TextInput(
        label="User ID or display name",
        placeholder="Enter the player's ID or display name"
    )
    tryout_result = discord.ui.TextInput(
        label="Perks",
        placeholder="Add match results with perks ex. 0-5",
        required=True
    )
    tryout_result2 = discord.ui.TextInput(
        label="No perks",
        placeholder="Add match results without perks ex. 2-5",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Save responses
        bot.cached_logs[interaction.user.id] = {
            "player_name": self.player_name.value,
            "result_perks": self.tryout_result.value,
            "result_no_perks": self.tryout_result2.value
        }
    
        # Send DM with Continue / Cancel buttons
        try:
            view = ContinueOrCancelView()
            await interaction.user.send("✅ Step 1 complete. Would you like to continue to Step 2 or cancel?", view=view)
            await interaction.response.send_message("📨 Please check your DMs to continue or cancel the log.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I couldn't DM you. Please enable DMs and try again.", ephemeral=True)

# -------- Modal 2 --------

class TryoutModalStep2(discord.ui.Modal, title="Tryout Log - Step 2"):
    aim = discord.ui.TextInput(label="Aim", placeholder="e.g. 9/10", required=True)
    movement = discord.ui.TextInput(label="Movement", placeholder="e.g. 10/10", required=True)
    cover = discord.ui.TextInput(label="Cover", placeholder="e.g. 6/10", required=True)
    faking = discord.ui.TextInput(label="Faking", placeholder="e.g. 1/10", required=True)
    juking = discord.ui.TextInput(label="Juking", placeholder="e.g. 0/10", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        def extract_score(value):
            try:
                parts = value.strip().split("/")
                score = int(parts[0])
                return min(max(score, 0), 10)
            except:
                return 0

        # Extract scores
        scores = {
            "Aim": extract_score(self.aim.value),
            "Movement": extract_score(self.movement.value),
            "Cover": extract_score(self.cover.value),
            "Faking": extract_score(self.faking.value),
            "Juking": extract_score(self.juking.value)
        }

        # Total & average
        total_score = sum(scores.values())
        max_score = 5 * 10
        average_score = round((total_score / max_score) * 100, 1)

        # Retrieve Step 1 data
        data = bot.cached_logs.get(interaction.user.id, {})
        data.update(scores)
        data["results"] = f"{total_score}/50 ({average_score}%)"

        try:
            player_id = int(data.get("player_name"))
            guild = interaction.guild or interaction.client.get_guild(1402441634792083468)  # <- Replace if needed
            member = guild.get_member(player_id)
        except (ValueError, TypeError):
            member = None

        if not member:
            await interaction.response.send_message("❌ Couldn't find the player in this server. Make sure the Discord ID is valid.", ephemeral=True)
            return

        # Create embed
        embed = discord.Embed(
            title="📝 Tryout Log Summary",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 Player", value=f"`{data.get('player_name')}`", inline=True)
        embed.add_field(name="🎮 Match (Perks)", value=f"`{data.get('result_perks')}`", inline=True)
        embed.add_field(name="🎮 Match (No Perks)", value=f"`{data.get('result_no_perks')}`", inline=True)
        embed.add_field(name="📊 Aim", value=f"`{scores['Aim']}/10`", inline=True)
        embed.add_field(name="🧍 Movement", value=f"`{scores['Movement']}/10`", inline=True)
        embed.add_field(name="🛡️ Cover", value=f"`{scores['Cover']}/10`", inline=True)
        embed.add_field(name="🤡 Faking", value=f"`{scores['Faking']}/10`", inline=True)
        embed.add_field(name="🕺 Juking", value=f"`{scores['Juking']}/10`", inline=True)
        embed.add_field(name="✅ Total Score", value=f"`{data['results']}`", inline=True)
        embed.set_footer(text=f"Logged by {interaction.user.name}")

        # Send to log channel
        log_channel_id = 1402441636738498704  # 🔁 Replace with your channel ID
        log_channel = bot.get_channel(log_channel_id)

        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message("✅ Tryout log submitted to the log channel.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Could not find the log channel. Please check the ID.", ephemeral=True)

        bot.cached_logs.pop(interaction.user.id, None)

        # after you've determined `member`, `average_score`, and `guild` inside on_submit:
        # remove old division roles and assign new one
        roles_to_remove = [
            guild.get_role(DIVISION1_ROLE_ID),
            guild.get_role(DIVISION2_ROLE_ID),
            guild.get_role(DIVISION3_ROLE_ID),
            guild.get_role(DIVISION4_ROLE_ID),
        ]
        try:
            await member.remove_roles(*[r for r in roles_to_remove if r and r in member.roles])
        except Exception:
            logging.exception("Failed removing existing division roles")

        if average_score >= 80:
            new_role = guild.get_role(DIVISION1_ROLE_ID)
        elif average_score >= 70:
            new_role = guild.get_role(DIVISION2_ROLE_ID)
        elif average_score >= 60:
            new_role = guild.get_role(DIVISION3_ROLE_ID)
        else:
            new_role = guild.get_role(DIVISION4_ROLE_ID)

        if new_role:
            try:
                await member.add_roles(new_role)
            except Exception:
                logging.exception("Failed adding new division role")

# -------- Continue/Cancel View --------
class ContinueOrCancelView(discord.ui.View):
    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TryoutModalStep2())

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.cached_logs.pop(interaction.user.id, None)
        await interaction.response.send_message("❌ Tryout log has been canceled.", ephemeral=True)

# -------- View with Start Button --------
class TryoutView(discord.ui.View):
    @discord.ui.button(label="Make the tryout log", style=discord.ButtonStyle.blurple)
    async def tryout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TryoutModal())

# -------- Command to trigger --------
@bot.command()
async def tryout(ctx):
    view = TryoutView(timeout=None)
    await ctx.send("Press the button to make the tryout log:", view=view)

@bot.event
async def on_ready():
    print(f'The bot is starting, {bot.user.name}')


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
