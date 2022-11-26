from blizzardapi import BlizzardApi
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from sqlite3 import Error
import os

from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    def create_connection(self):
        conn = None
        try:
            conn = sqlite3.connect('pythonsqlite.db')
        except Error as e:
            print(e)

        SQLStatement = """   
        CREATE TABLE IF NOT EXISTS discordServers (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        serverId integer NOT NULL,
                                        defaultRegion text,
                                        defaultRealm text,
                                        isVip bool
                                    );
        """
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(SQLStatement)
            except Error as e:
                print(e)
        else:
            print("Error! cannot create the database connection.")
    def execute_command(command):
        conn = None
        try:
            conn = sqlite3.connect('pythonsqlite.db')
        except Error as e:
            print(e)
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(command)
                conn.commit()
                return c.lastrowid
            except Error as e:
                print(e)
        else:
            print("Error! cannot create the database connection.")
        

    def getRowNumber(command):
        conn = None
        try:
            conn = sqlite3.connect('pythonsqlite.db')
        except Error as e:
            print(e)
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(command)
                return len(c.fetchall())
            except Error as e:
                print(e)
        else:
            print("Error! cannot create the database connection.")
    def selectFromDataBase(command):
        conn = None
        try:
            conn = sqlite3.connect('pythonsqlite.db')
        except Error as e:
            print(e)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(command)

            rows = cur.fetchall()
            return rows

class developerInstance:

    _server: str
    _realm: str
    _namespace: str
    _locale: str

    def __init__(self, clientId, clientSecret):
        self._clientId: str = clientId
        self._clientSecret: str = clientSecret
        self._apiClient : any = BlizzardApi(clientId, clientSecret)

    @property
    def server(self):
        return self._server

    @property
    def realm(self):
        return self._realm

    @property
    def namespace(self):
        return self._namespace

    @property
    def locale(self):
        return self._locale

    @server.setter
    def server(self, server):
        self.server = server
    
    def getPlayerInfo(self, playerNickname:str, region:str, realm:str):
        playerInfo = self._apiClient.wow.profile.get_character_profile_summary(region,"en_GB",realm,playerNickname)
        #nazwa, level, ilvl, rasa, klasa, spec, guild
        return [
            playerInfo["name"],
            playerInfo["guild"]["name"],
            playerInfo["level"],
            playerInfo["race"]["name"],
            playerInfo["character_class"]["name"],
            playerInfo["active_spec"]["name"],
            playerInfo["average_item_level"]
            
            ]

    def getPlayerAchivPoints(self, playerNickname:str, region:str, realm:str):
        playerInfo = self._apiClient.wow.profile.get_character_achievements_summary(region,"en_GB",realm,playerNickname)
        #nazwa, level, ilvl, rasa, klasa, spec, guild
        return playerInfo["total_points"]

    def getPlayerRenders(self, playerNickname:str, region:str, realm:str):
        playerInfo = self._apiClient.wow.profile.get_character_media_summary(region,"en_GB",realm,playerNickname)
        return playerInfo["assets"][0]["value"]

    def getPlayerMythicPlusInfo(self, playerNickname:str, region:str, realm:str):
        playerInfo = self._apiClient.wow.profile.get_character_mythic_keystone_profile_index(region,"en_GB",realm,playerNickname)
        try:
            return playerInfo["current_mythic_rating"]["rating"]
        except:
            return 0


    def getPlayerMythicPlusDetailsInfo(self, playerNickname:str, region:str, realm:str):
        #Informacje powinny być pobierane z Raider.IO w celu zachowania aktualności
        pass

class discordClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        if not self.synced:
            await tree.sync()
            self.synced = True
        if self.synced == True:
            print("We are logged in")

DatabaseService.create_connection(r"pythonsqlite.db")
instance = developerInstance(os.getenv("WOWAPICLIENT"), os.getenv("WOWAPISECRET"))


client = discordClient()
tree = app_commands.CommandTree(client)


@client.event
async def on_guild_join(guild):
    guildId = guild.id
    sqlValid = f"""
    SELECT * FROM discordServers WHERE serverId = {guildId}
    """
    print(DatabaseService.getRowNumber(sqlValid))
    if DatabaseService.getRowNumber(sqlValid) == 0:
        sqlInsert = f"""
        INSERT INTO discordServers(serverId, defaultRegion, defaultRealm, isVip) 
        VALUES ({guildId}, 'eu', 'burning-legion', 0)
        """
        DatabaseService.execute_command(sqlInsert)
    return

@client.event
async def on_guild_leave(guild):
    guildId = guild.id
    sqlInsert = f"""
    DELETE FROM discordServers WHERE serverId = {guildId}
    """
    DatabaseService.execute_command(sqlInsert)
    return

@tree.command(name="wow", description="Display player information")
async def self(interaction: discord.Interaction, name : str):
    discordServerId = interaction.guild_id
    sql = f"""
        SELECT * FROM discordServers WHERE serverId = {discordServerId}
    """
    result = DatabaseService.selectFromDataBase(sql)
    realmIndex = 3
    regionIndex = 2
    #Get a server realm
    serverDefaultRealm = result[0][realmIndex]
    #Get a server region
    serverDefaultRegion = result[0][regionIndex]
    name = name.lower()
    try:
        playerCardInfo = instance.getPlayerInfo(name, serverDefaultRegion, serverDefaultRealm)
        playerRenderInfo = instance.getPlayerRenders(name, serverDefaultRegion, serverDefaultRealm)
        playerAchivPoints = instance.getPlayerAchivPoints(name, serverDefaultRegion, serverDefaultRealm)
        playerMythicPlus = round(instance.getPlayerMythicPlusInfo(name, serverDefaultRegion, serverDefaultRealm),0)
    except:
        await interaction.response.send_message(f"Something went wrong",ephemeral=True)
    

    embed = discord.Embed(title=f"{playerCardInfo[0]} - {playerCardInfo[1]} - {serverDefaultRealm.capitalize()}", \
    description=f"{playerCardInfo[2]} {playerCardInfo[3]} {playerCardInfo[4]} {playerCardInfo[5]}", color=0x00eeff)
    embed.set_thumbnail(url=f'{playerRenderInfo}')
    #embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="Achivement Points", value=f"{playerAchivPoints}", inline=False)
    embed.add_field(name="Mythic+ Score", value=f"{playerMythicPlus}", inline=False)
    #embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.set_footer(text="Bot author - Tilttoo#3425")



    await interaction.response.send_message(embed=embed)

@tree.command(name="setregion", description="Configure bot settings - REGION")
@app_commands.default_permissions(manage_roles = True)
async def self(interaction: discord.Interaction, region : str="eu"):
    guildid = interaction.guild_id
    validRegion = region.lower()
    sqlUpdate = f"""
    UPDATE discordServers SET defaultRegion = '{validRegion}' WHERE serverId = {guildid}
    """
    DatabaseService.execute_command(sqlUpdate)
    await interaction.response.send_message(f"You set {region} as your server default region",ephemeral=True)

@tree.command(name="setrealm", description="Configure bot settings - REALM")
@app_commands.default_permissions(manage_roles = True)
async def self(interaction: discord.Interaction, realm :str):
    guildid = interaction.guild_id
    validRealm = realm.lower()
    sqlUpdate = f"""
    UPDATE discordServers SET defaultRealm = '{validRealm}' WHERE serverId = {guildid}
    """
    DatabaseService.execute_command(sqlUpdate)
    await interaction.response.send_message(f"You set {realm} as your server default realm",ephemeral=True)



client.run(os.getenv("DISCORDAPI"))

"""
TO-DO

Pobieranie servera, realmu z bazy danych ✅
Możliwość dla użytkownika ustawienia sobie innego default niż ma server
Validacja wprowadzonych regionów
Validacja wprowadzonych realmow
Dodanie integracji z API Raiderio
Dodanie ile na ile raid
Dodanie stopki do informacji o graczu z linkami do: Armory, RaiderIO, Warcraftlogs

"""