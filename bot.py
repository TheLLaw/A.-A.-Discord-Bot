import json
import discord
import asyncio
import datetime
from discord.ext import commands
from discord.ext import tasks
from aiohttp import ClientSession
from discord import Option
law = 465946367622381578 # DevID
api_key = "ratio" # API KEY from bungie.net's api
client_id = int("ratio") # Application Client Id
client_secret = "ratio" # Application Client Secret

root = "https://www.bungie.net/Platform" # Root url for bungie.net's api
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all()) # Bot setup prefix = ! & all intents enabled


async def refresh_token(user): # This function refreshes the token if the time has past.
    with open("logs.json", "r") as f:
        data = json.load(f) # Data Structure: {"discordId": ["refreshToken", "ExpiresIn", "accessToken"]}
    try:
        token = data[str(user.id)][2]
        refresh = data[str(user.id)][0]
        date = datetime.datetime.strptime(data[str(user.id)][1], "%m/%d/%Y, %H:%M:%S")
        now = datetime.datetime.now()
        time = now - datetime.timedelta(microseconds=now.microsecond)
        if time < date: # Checking if the token is expired.
            return token
    except KeyError:
        return False # Member did not do the setup intended.
    async with ClientSession() as session:
        r = await session.post(url="https://www.bungie.net/platform/app/oauth/token/", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret
        }) # If expired refreshing a token
        refresh = await r.json()
    try:
        data[str(user.id)][0] = refresh["refresh_token"] # Logging the refresh token list[0]
        data[str(user.id)][2] = refresh["access_token"] # Logging the access token list[2]
        now = datetime.datetime.now()
        time = now - datetime.timedelta(microseconds=now.microsecond)
        future = time + datetime.timedelta(seconds=refresh["expires_in"])
        data[str(user.id)][1] = future.strftime("%m/%d/%Y, %H:%M:%S") # Logging the expiring time list[1]
        with open("logs.json", "w") as f:
            json.dump(data, f, indent=4) # Dumping
    except KeyError as error:
        member = bot.get_user(law) # Debugging
        await member.send(error)
        return
    else:
        return refresh["access_token"] # New access token
    
@bot.event
async def on_ready():
    print("Howdy hey!") # Howdy hey!

@bot.command()
async def setup(ctx): # Setup command
    with open("logs.json", "r") as f:
        data = json.load(f)
    if str(ctx.author.id) in data: # Checking if the member has already used this command.
        await ctx.send("You are all done!")
        return
    await ctx.send(f"https://www.bungie.net/en/oauth/authorize?client_id={client_id}&response_type=code&state=6i0mkLx79Hp91nzWVeHrzHG4")
    await ctx.send("Please send the code!") # Sending the url to get the code
    code = await bot.wait_for("message", check=lambda m: m.author and m.channel, timeout=5*60) # waiting for the code
    await code.delete()
    async with ClientSession() as session: # Getting the token
        r = await session.post(url="https://www.bungie.net/platform/app/oauth/token/", data={
            "grant_type": f"authorization_code",
            "code": code.content,
            "client_id": client_id,
            "client_secret": client_secret
            #"client_secret": client_secret
        })
        jdata = await r.json()
    try: # Logging everything
        now = datetime.datetime.now()
        time = now - datetime.timedelta(microseconds=now.microsecond)
        future = time + datetime.timedelta(seconds=jdata["expires_in"])
        data[str(ctx.author.id)] = []
        data[str(ctx.author.id)].append(jdata["refresh_token"])
        data[str(ctx.author.id)].append(future.strftime("%m/%d/%Y, %H:%M:%S"))
        data[str(ctx.author.id)].append(jdata["access_token"])
        with open("logs.json", "w") as f:
            json.dump(data, f, indent=4)
    except Exception as error: # Debugging
        member = bot.get_user(law)
        await member.send(error)
        return
    await ctx.send("ur on the list kid") # He do be on the list tho

playing = [] # Tracking player list


async def check(token, membershipType: int, membershipId: int): # Checks if the member has chosen a character Hunter/Warlock/Titan
    counter = 0
    while True:
        try:
            async with ClientSession() as session: # Profile/CharacterData more importantly CharacterActivities
                r = await session.get(url=root + f"/Destiny2/{membershipType}/Profile/{membershipId}/?components=200,204", headers={
                    "X-API-Key": api_key,
                    "Authorization": "Bearer " + token
                })
                characterdata = await r.json()
            for character_id in characterdata["Response"]["characterActivities"]["data"]:
                if characterdata["Response"]["characterActivities"]["data"][character_id]["currentActivityHash"] != 0: # Checking activity hashes
                    return character_id
            counter += 1
            if counter == 5:
                return False
            else:
                continue
        except Exception as error: # Debugging
            member = bot.get_user(law)
            await member.send(error)
            await member.send(characterdata)
            pass
        await asyncio.sleep(180) # Sleeping

async def get_item_dict(): # Loading weapon dictionary (weapons.json)
    with open("weapons.json", "r") as f:
        item_dict = json.load(f)
    return item_dict

@bot.command()
async def check_list(ctx): # Debugging
    await ctx.send(playing) 

@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if before.guild.id == 849673187222224936: # Checking for the test guild
        if len(after.activities) != 0 and len(before.activities) != 0: # If was playing something and is still playing something
            if "Destiny 2" in str(after.activities[0]) and "Destiny 2" in str(before.activities[0]):
                return # If was playing D2 and is still playing D2 (D2D)
            if "Destiny 2" not in str(before.activities[0]) and "Destiny 2" in str(after.activities[0]):
                playing.append(after.id) # If wasn't playing D2 and now is playing D2 (?2D)
            if "Destiny 2" in str(after.activities[0]) and not "Destiny 2" in str(before.activities[0]):
                playing.remove(after.id) # If was playing D2 and now is playing something else (D2?)
                return
        if len(before.activities) == 0 and len(after.activities) != 0: # If wasn't playing anything and now is
            if "Destiny 2" in str(after.activities[0]): # If is now playing D2 (02D)
                playing.append(after.id)
            else:
                return # If is now playing something that isn't D2 (02?)
        if len(before.activities) == 0 and len(after.activities) == 0:
            return # If wasn't playing anything and still isn't (0?0)
        if len(before.activities) != 0 and len(after.activities) == 0: # If was playing something and now isn't.
            if "Destiny 2" in str(before.activities[0]): # If was playing D2 (D20)
                playing.remove(after.id)
                return
            else: # If wasn't playing D2 (?20)
                return
        token = await refresh_token(after) # Getting token.
        if not token: # If returned False
            playing.remove(after.id)
            return
        async with ClientSession() as session:
            membershipdata = await session.get(root + "/User/GetMembershipsForCurrentUser/", headers={
                "X-API-Key": api_key,
                "Authorization": "Bearer " + token
            })
            jmembershipdata = await membershipdata.json()
        try: # Getting membership Data
            membershipType = jmembershipdata["Response"]["destinyMemberships"][0]["membershipType"]
            membershipId = jmembershipdata["Response"]["destinyMemberships"][0]["membershipId"]
        except KeyError as error: # Debugging
            member = bot.get_user(law)
            await member.send(error)
            return
        character_id = await check(token, membershipType, membershipId) # Checking
        if not character_id: # If returned False (took too long to select)
            playing.remove(after.id)
            return
        item_dict = await get_item_dict() # Gets weapons.json's data
        while True: # MAIN FUNCTION. REMOVAL PROCESS
            if after.id not in playing: # In case he stopped playing D2 (D20, D2?)
                return
            token = await refresh_token(after) # Always getting a new/old token
            async with ClientSession() as session: # Character Data more importantly inventory data (postmaster mainly)
                response = await session.get(root + f"/Destiny2/{membershipType}/Profile/{membershipId}/Character/{character_id}/?components=201", headers={
                "X-API-Key": api_key,
                "Authorization": "Bearer " + token
                })
                data = await response.json()
            postmaster = [] # Postmaster List
            for obj in data["Response"]["inventory"]["data"]["items"]:

                if obj["bucketHash"] == 215593132: # If object is in the Postmaster
                    postmaster.append(obj) # Append it to the postmaster list
            if len(postmaster) >= 16: # If postmaster reaches 16 items (Close to full)
                for obj in postmaster: # REMOVAL PROCESS
                    try: # Checking with the manifest (weapons.json) if the rarity is Blue or Rare
                        id = obj["itemInstanceId"]
                        instance = int(obj["itemHash"])		
                        tier = item_dict[str(instance)]["tierTypeName"]
                        if tier == "Rare": # REMOVING ITEMS (Sending to Vault)
                            async with ClientSession() as session: # Pulling from postmaster if Blue rarity.
                                data = { 
                                "itemReferenceHash": instance,
                                "stackSize": 1,
                                "itemId": id,
                                "characterId": character_id,
                                "membershipType": membershipType
                                }
                                r = await session.post(root + "/Destiny2/Actions/Items/PullFromPostmaster/", headers={
                                    "X-API-Key": api_key,
                                    "Authorization": "Bearer " + token
                                    }, json=data)
                                await asyncio.sleep(3)
                                data = {
                                    "itemReferenceHash": instance,
                                    "stackSize": 1,
                                    "transferToVault": True,
                                    "itemId": id,
                                    "characterId": character_id,
                                    "membershipType": membershipType
                                } # Transfering to Vault the blue items.
                                r = await session.post(root + "/Destiny2/Actions/Items/TransferItem/", headers={
                                    "X-API-Key": api_key,
                                    "Authorization": "Bearer " + token
                                    }, json=data)
                        else:
                            pass
                    except KeyError as error:
                        pass # If keyerror that means there's an item without instance Id (e.g. Shards and Prisms also essence)
            else:
                pass # If not blue rarity ignore it.
            await asyncio.sleep(120) # Sleep for 2 minutes THIS MIGHT BE CHANGED IN THE FUTURE.


bot.run("uwu") # uwu bot token
