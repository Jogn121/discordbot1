import discord
from discord.ext import commands, tasks
import aiohttp
import time

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    shard_id=1,       # Change to 1 for second instance
    shard_count=2     # Total shards
)

user_tracking = {}
tracked_users = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.roblox.com/"
}

OWNER_ID = 1020441624381239438

@bot.event
async def on_ready():
    print(f"✅ Shard {bot.shard_id} connected as {bot.user}")
    await update_presence()  # Update presence when the bot is ready

async def update_presence():
    await bot.wait_until_ready()

    # Only update presence for shard 1
    if bot.shard_id == 0:
        ping = round(bot.latency * 1000)  # Convert latency to milliseconds
        print(f"Ping for Shard 1: {ping}ms")  # Debug print to ensure it's correct
        try:
            await bot.change_presence(
                activity=discord.Game(name=f"Ping: {ping}ms")  # Set the status as Ping: Xms
            )
            print(f"✅ Shard 1 status updated with Ping: {ping}ms")
        except Exception as e:
            print(f"❌ Error updating presence: {e}")

@bot.event
async def send_dm_on_shard_0(user, content=None, embed=None):
    if bot.shard_id == 0:
        try:
            await user.send(content=content, embed=embed)
        except discord.errors.Forbidden:
            print(f"❌ Can't DM {user.id}")
        except Exception as e:
            print(f"❌ DM Error: {e}")

@bot.command()
async def ping(ctx):
    if bot.shard_id == 1:  # Show the ping only for shard 1
        ping = round(bot.latency * 1000)  # Convert latency to milliseconds
        await ctx.send(f"🏓 Shard 1 Ping: {ping}ms")

@bot.command()
async def test(ctx):
    if ctx.guild is None and bot.shard_id != 0:
        return

    if ctx.author.id != OWNER_ID and bot.shard_id == 0:
        await ctx.send("❌ You do not have permission to use this command.")
        return

    start_time = time.time()
    ping = bot.latency * 1000
    end_time = time.time()
    ping_time = round(ping, 2)
    latency_time = round((end_time - start_time) * 1000, 2)

    try:
        async with aiohttp.ClientSession() as session:
            download_start = time.time()
            async with session.get("http://ipv4.download.thinkbroadband.com/5MB.zip") as r:
                await r.read()
            download_end = time.time()
            download_speed = 5 * 1024 / (download_end - download_start)
            download_speed = round(download_speed, 2)

            upload_start = time.time()
            async with session.post("https://httpbin.org/post", json={"test": "upload"}):
                upload_end = time.time()
            upload_speed = 1 / (upload_end - upload_start)
            upload_speed = round(upload_speed, 2)

            await ctx.send(f"🏓 Ping: {ping_time}ms\n⚡ Latency: {latency_time}ms\n🌐 Download: {download_speed} KB/s\n📤 Upload: {upload_speed} KB/s")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")


@bot.command()
async def add(ctx, roblox_id: str):
    if ctx.guild is None and bot.shard_id != 0:
        return

    discord_id = ctx.author.id
    if discord_id not in user_tracking:
        user_tracking[discord_id] = []

    if roblox_id not in user_tracking[discord_id]:
        user_tracking[discord_id].append(roblox_id)
        await ctx.send(f"✅ Now tracking Roblox ID {roblox_id} for you.")
    else:
        await ctx.send(f"⚠️ Already tracking {roblox_id}.")

    if roblox_id not in tracked_users:
        tracked_users[roblox_id] = {"status": "UNKNOWN", "discord_users": set()}
    tracked_users[roblox_id]["discord_users"].add(discord_id)

@bot.command()
async def unadd(ctx, roblox_id: str):
    if ctx.guild is None and bot.shard_id != 0:
        return

    discord_id = ctx.author.id
    if discord_id in user_tracking and roblox_id in user_tracking[discord_id]:
        user_tracking[discord_id].remove(roblox_id)
        tracked_users[roblox_id]["discord_users"].discard(discord_id)
        if not tracked_users[roblox_id]["discord_users"]:
            del tracked_users[roblox_id]
        await ctx.send(f"🗑️ Stopped tracking {roblox_id}.")
    else:
        await ctx.send("❌ You aren't tracking that user.")

@bot.command()
async def list(ctx):
    if ctx.guild is None and bot.shard_id != 0:
        return

    discord_id = ctx.author.id
    tracked = user_tracking.get(discord_id, [])
    if not tracked:
        await ctx.send("You're not tracking anyone.")
    else:
        await ctx.send("Tracking: " + ", ".join(tracked))

@bot.command()
async def getuserid(ctx, *, username: str):
    if ctx.guild is None and bot.shard_id != 0:
        return

    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS) as resp:
                data = await resp.json()
                if "data" in data and data["data"]:
                    roblox_user = data["data"][0]
                    await ctx.send(f"🔍 {username} → ID: {roblox_user['id']}")
                else:
                    await ctx.send("❌ User not found.")
    except Exception as e:
        await ctx.send("⚠️ Error occurred.")

@bot.command(name="commands")
async def show_commands(ctx):
    if ctx.guild is None and bot.shard_id != 0:
        return

    embed = discord.Embed(title="📜 Commands", color=discord.Color.blurple())
    embed.add_field(name="!add <roblox_id>", value="Track a user", inline=False)
    embed.add_field(name="!unadd <roblox_id>", value="Untrack a user", inline=False)
    embed.add_field(name="!list", value="Show tracked users", inline=False)
    embed.add_field(name="!getuserid <username>", value="Get user ID", inline=False)
    embed.add_field(name="!commands", value="Show all commands", inline=False)
    embed.add_field(name="!joins <roblox_id>", value="Check if joins are on (experimental)", inline=False)
    embed.add_field(name="!info <roblox_id>", value="User info", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def joins(ctx, roblox_id: str):
    if ctx.guild is None and bot.shard_id != 0:
        return

    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [int(roblox_id)]}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS) as resp:
                data = await resp.json()
                if "userPresences" in data and data["userPresences"]:
                    presence = data["userPresences"][0]
                    embed = discord.Embed(
                        title=f"🎮 Join Status for {roblox_id}",
                        color=discord.Color.blurple()
                    )
                    if presence.get("userPresenceType", 0) != 2:
                        embed.description = "❌ Not in-game."
                    else:
                        join_status = "✅ Joins are ON" if presence.get("isJoinable", False) else "❌ Joins are OFF"
                        embed.description = "🔍 In game"
                        embed.add_field(name="Join Status", value=join_status)
                    embed.add_field(name="Profile", value=f"[Link](https://www.roblox.com/users/{roblox_id}/profile)")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ User not found.")
    except Exception as e:
        await ctx.send("⚠️ Error checking join status.")

@bot.command()
async def info(ctx, roblox_id: int):
    if ctx.guild is None and bot.shard_id != 0:
        return

    url = f"https://users.roblox.com/v1/users/{roblox_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(
                        title=f"Info for {data['name']}",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Username", value=data["name"], inline=False)
                    embed.add_field(name="Display Name", value=data.get("displayName", ""), inline=False)
                    embed.add_field(name="Bio", value=data.get("description", "None"), inline=False)
                    embed.add_field(name="Created", value=data.get("created", "N/A"), inline=False)
                    embed.add_field(name="Profile", value=f"[Link](https://www.roblox.com/users/{roblox_id}/profile)", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Couldn't fetch user info.")
    except Exception:
        await ctx.send("⚠️ Error retrieving info.")

async def get_user_status(user_id):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": [int(user_id)]}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS) as resp:
                data = await resp.json()
                if "userPresences" in data:
                    presence = data["userPresences"][0]
                    return presence["userPresenceType"]
    except Exception as e:
        print(f"Error for {user_id}: {e}")
    return None

@tasks.loop(seconds=10)
async def status_checker():
    for user_id, info in tracked_users.items():
        presence_type = await get_user_status(user_id)
        if presence_type is None:
            continue

        new_status = ["OFFLINE", "ONLINE", "IN_GAME"][presence_type]
        if new_status != info["status"]:
            info["status"] = new_status
            for discord_user_id in info["discord_users"]:
                try:
                    user = await bot.fetch_user(discord_user_id)
                    embed = discord.Embed(
                        title=f"Roblox User {user_id} is now {new_status.replace('_', ' ')}",
                        color=discord.Color.green() if new_status == "ONLINE" else
                              discord.Color.red() if new_status == "OFFLINE" else
                              discord.Color.blue()
                    )
                    if new_status == "IN_GAME":
                        embed.add_field(name="In Game", value=f"[Profile](https://www.roblox.com/users/{user_id}/profile)")
                    if bot.shard_id == 0:
                        await send_dm_on_shard_0(user, embed=embed)  # Use the shard 0 DM sending function
                except discord.errors.Forbidden:
                    print(f"❌ Can't DM {discord_user_id}")
                except Exception as e:
                    print(f"❌ DM Error: {e}")

bot.run("MTM1ODk1MjgyMTgxMDEzNTA1Mw.GiwPLf.-dYXpDK0BAXQf_6O3Uk9SvmyOyo3ErmiOol06U")  # Make sure to replace this with your token!
