import nextcord
from nextcord.ext import commands
import asyncio
import aiohttp
import datetime
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

intents = nextcord.Intents.default()
intents.presences = True
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents)


async def update_user_presence(user_id):
    guild = client.get_guild(int(os.getenv("GUILD_ID")))
    user = nextcord.utils.get(guild.members, id=int(user_id))
    fetch_user = await client.fetch_user(user_id)
    role_ids = [role.id for role in user.roles]
    print(user.activities)
    if 1360265497454838016 in role_ids:
        print("User has hidden their username and avatar")
        useractivity = {
            "username": False,
            "avatar": False,
            "banner": fetch_user.banner.url if fetch_user.banner else None,
            "hidden": True,
            "status": str(user.status),
            "custom_status": None,
            "custom_status_emoji": None,
            "activities": []
        }
    else:
        useractivity = {
            "username": user.name,
            "avatar": user.avatar.url if user.avatar else None,
            "banner": fetch_user.banner.url if fetch_user.banner else None,
            "status": str(user.status),
            "custom_status": None,
            "custom_status_emoji": None,
            "activities": []
        }

    for activity in user.activities:
        print(f"Processing activity: {activity}")
        activity_dict = {
            "name": activity.name if hasattr(activity, 'name') else None,
            "type": str(activity.type) if hasattr(activity, 'type') else None,
            "details": getattr(activity, 'details', None),
            "state": getattr(activity, 'state', None),
            "timestamps": {
                "start": str(activity.start) if hasattr(activity, 'start') and activity.start else None,
                "end": str(activity.end) if hasattr(activity, 'end') and activity.end else None
            },
            "assets": {
                "large_image_url": None,
                "large_image_text": None,
                "small_image_url": None,
                "small_image_text": None
            }
        }

        if isinstance(activity, nextcord.activity.CustomActivity):
            useractivity["custom_status"] = activity.name
            useractivity["custom_status_emoji"] = activity.emoji.url if activity.emoji else None
            continue

        # **Fixing Spotify activity handling**
        if isinstance(activity, nextcord.activity.Spotify):
            print("listening to Spotify")
            activity_dict["name"] = activity.title
            activity_dict["url"] = f"https://open.spotify.com/track/{activity.track_id}"
            activity_dict["details"] = activity.artist
            activity_dict["state"] = f"{activity.album}"
            activity_dict["timestamps"]["start"] = str(activity.start)
            activity_dict["timestamps"]["end"] = str(activity.end)
            activity_dict["assets"]["large_image_url"] = activity.album_cover_url
        else:
            if activity.name:
                activity_dict["name"] = activity.name
            if activity.type:
                activity_dict["type"] = str(activity.type)
            if hasattr(activity, 'details') and activity.details:
                activity_dict["details"] = activity.details
            if hasattr(activity, 'state') and activity.state:
                activity_dict["state"] = activity.state
            if hasattr(activity, 'start') and activity.start:
                activity_dict["timestamps"]["start"] = str(activity.start)
            if hasattr(activity, 'end') and activity.end: 
                activity_dict["timestamps"]["end"] = str(activity.end)
            if hasattr(activity, 'large_image_url') and activity.large_image_url:
                activity_dict["assets"]["large_image_url"] = activity.large_image_url
            if hasattr(activity, 'large_image_text') and activity.large_image_text:
                activity_dict["assets"]["large_image_text"] = activity.large_image_text
            if hasattr(activity, 'small_image_url') and activity.small_image_url:
                activity_dict["assets"]["small_image_url"] = activity.small_image_url
            if hasattr(activity, 'small_image_text') and activity.small_image_text:
                activity_dict["assets"]["small_image_text"] = activity.small_image_text
        useractivity["activities"].append(activity_dict)

        for activity in useractivity["activities"]:
            if activity["assets"]["large_image_url"]:
                print(activity["assets"]["large_image_url"])
                if "mp:external" in activity["assets"]["large_image_url"]:
                    activity["assets"]["large_image_url"] = "https://" + activity["assets"]["large_image_url"].split("https/")[-1]
                if ".jpg.png" in activity["assets"]["large_image_url"]:
                    large_image_url_parts = activity["assets"]["large_image_url"].rsplit('.', 1)
                    if len(large_image_url_parts) > 1:
                        activity["assets"]["large_image_url"] = large_image_url_parts[0]
                if ".png.png" in activity["assets"]["large_image_url"]:
                    large_image_url_parts = activity["assets"]["large_image_url"].rsplit('.', 1)
                    if len(large_image_url_parts) > 1:
                        activity["assets"]["large_image_url"] = large_image_url_parts[0]

            if activity["assets"]["small_image_url"]:
                if "mp:external" in activity["assets"]["small_image_url"]:
                    activity["assets"]["small_image_url"] = "https://" + activity["assets"]["small_image_url"].split("https/")[-1]
                if ".jpg.png" in activity["assets"]["small_image_url"]:
                    small_image_url_parts = activity["assets"]["small_image_url"].rsplit('.', 1)
                    if len(small_image_url_parts) > 1:
                        activity["assets"]["small_image_url"] = small_image_url_parts[0]
                if ".png.png" in activity["assets"]["small_image_url"]:
                    small_image_url_parts = activity["assets"]["small_image_url"].rsplit('.', 1)
                    if len(small_image_url_parts) > 1:
                        activity["assets"]["small_image_url"] = small_image_url_parts[0]
    
    print(useractivity)            
    # **Send data to API**
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{os.getenv('API_URL')}/presence/{user_id}", json=useractivity) as response:
                print(await response.text())
    except Exception as e:
        traceback.print_exc()
        print(f"Error sending data: {e}")



async def update_user_presences():
    guild = client.get_guild(int(os.getenv("GUILD_ID")))
    for member in guild.members:
        if member.id == int(os.getenv("BOT_ID")):
            continue
        await update_user_presence(member.id)
        print("Refreshed user presence of " + str(member.id))
        await asyncio.sleep(1)  # To avoid hitting the rate limit

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    for user in client.users:
        await update_user_presence(user.id)
        print("Initial presence update for " + str(user.id))
        # await asyncio.sleep(1)  # To avoid hitting the rate limit

@client.event
async def on_message(message):
    if message.channel.id == int(os.getenv("REFRESH_CHANNEL_ID")):
        if message.content.startswith("refresh"):
            await update_user_presence(message.content.split(" ")[1])
            print("Refreshed user presence of " + message.content.split(" ")[1])

last_sent = None

@client.event
async def on_presence_update(before, after):
    print(f"Presence of {after.id} updated")
    await update_user_presence(after.id)
    last_sent = datetime.datetime.now()
    



client.run(os.getenv("BOT_TOKEN"))
