import discord
import pymongo
from decouple import config
from server import *

pretty = 0xE34666

client = pymongo.MongoClient(config("CLUSTER_URL"))
collection = client.tasketh.guilds

cache = {}


def getServerConfigs(serverid):
    """returns the dictionary that contains server configuration"""

    result = collection.find_one({"Server": serverid})
    cache[result["Server"]] = result["Prefix"]

    server = Server(serverid)
    server.prefix = result["Prefix"]
    server.syntaxDelimiter = result["syntaxDelimiter"]
    server.bufferUsers = result["Buffer"]
    server.logo = result["Logo"]
    server.taskschannel = result["TasksChannel"]
    server.reportschannel = result["ReportsChannel"]
    server.taskMention = result["TaskMention"]
    server.permitted = result["Permitted"]
    server.reactEmoji = result["Emoji"]

    return server


def updateServerConfigs(server):
    """Updates the server configuration"""
    ind = {"Server": server.id}
    dic = {
        "$set": {
            "Prefix": server.prefix,
            "syntaxDelimiter": server.syntaxDelimiter,
            "Buffer": server.bufferUsers,
            "Logo": server.logo,
            "TasksChannel": server.taskschannel,
            "ReportsChannel": server.reportschannel,
            "TaskMention": server.taskMention,
            "Permitted": server.permitted,
            "Emoji": server.reactEmoji,
        }
    }

    collection.update_one(ind, dic, upsert=True)


permission = lambda author, server: (
    author.guild_permissions.administrator
) or (server.permitted in [role.id for role in author.roles])


async def check(message, server, func):
    roles = [role.id for role in message.author.roles]
    if permission(message.author, server):
        await func(message, server)
    else:
        await permDenied(message, server)


async def setPrefix(message, server):
    """Changes prefix of tasketh in a particular server
    Syntax: <current prefix>prefix <oldprefix>"""
    value = message.content.split()[-1]
    if 3 > len(value) >= 1:
        server.prefix = value
        updateServerConfigs(server)
        cache[server.id] = value
        prefixEmbed = discord.Embed(
            title="Success",
            description=f"Prefix changed to {server.prefix}",
            color=pretty,
        )
        prefixEmbed.set_footer(text="Settings saved", icon_url=server.logo)
        await message.channel.send(
            embed=prefixEmbed, reference=message, mention_author=False
        )
    else:
        prefixEmbed = discord.Embed(
            title="Error",
            description="Prefix cannot be longer than 2 characters",
            color=pretty,
        )
        prefixEmbed.set_footer(text="Error encountered", icon_url=server.logo)
        await message.channel.send(
            embed=prefixEmbed, reference=message, mention_author=False
        )


async def setTasksChannel(message, server):
    """Sets the channel to send tasks in"""
    server.taskschannel = message.channel.id
    updateServerConfigs(server)
    alert = discord.Embed(
        title="Task channel configured",
        description=f"Task channel set to <#{message.channel.id}>",
        color=pretty,
    )
    alert.set_footer(text="Settings saved", icon_url=server.logo)
    await message.channel.send(embed=alert, reference=message, mention_author=False)


async def setReportsChannel(message, server):
    """Sets the channel to send reports in"""
    server.reportschannel = message.channel.id
    updateServerConfigs(server)
    alert = discord.Embed(
        title="Report channel configured",
        description=f"Report channel set to <#{message.channel.id}>",
        color=pretty,
    )
    alert.set_footer(text="Settings saved", icon_url=server.logo)
    await message.channel.send(embed=alert, reference=message, mention_author=False)


async def setBuffer(message, server):
    """Sets the number of buffer reactions taken into account"""
    try:
        value = int(message.content.split()[-1])
        if value >= 0:
            server.bufferUsers = value
            updateServerConfigs(server)
            alert = discord.Embed(
                title="Number of buffer users configured",
                description=f"Number of buffer users is now set to {value}",
                color=pretty,
            )
            alert.set_footer(text="Settings saved", icon_url=server.logo)
            await message.channel.send(
                embed=alert, reference=message, mention_author=False
            )

        else:
            alert = discord.Embed(
                title="Error",
                description="Number of buffer users has to be a non-negative integer",
                color=pretty,
            )
            alert.set_footer(text="Error encountered", icon_url=server.logo)
            await message.channel.send(
                embed=alert, reference=message, mention_author=False
            )

    except NameError:
        alert = discord.Embed(title="Error", description="Invalid input", color=pretty)
        alert.set_footer(icon_url=server.logo)
        await message.channel.send(embed=alert, reference=message, mention_author=False)

quotes = client.tasketh.iconic_quotes

async def llama(message):
    test = quotes.aggregate([{"$sample":{"size":1}}])
    embed = discord.Embed(
        description=list(test)[0]['quote'],
        color=pretty,
    )
    await message.channel.send(embed=embed, reference=message, mention_author=False)


async def permit(message, server):
    """Changes the role that has permission to create tasks and change setting.
    Syntax: <prefix>taskmention <role>
    Default role mentioned is everyone."""
    value = message.content.split()[-1]  # this wont work if role has spaces
    if value == "everyone":
        value = "@everyone"
    """roles = {}
    for role in message.guild.roles:
        roles[role.name] = role.id"""
    roles = {role.name: role.id for role in message.guild.roles}
    try:
        server.permitted = roles[value]
        updateServerConfigs(server)
        alert = discord.Embed(
            title="Permission role configured",
            description=f"Permission role set to <@&{server.permitted}>",
            color=pretty,
        )
        alert.set_footer(text="Settings saved", icon_url=server.logo)
        await message.channel.send(embed=alert, reference=message, mention_author=False)
    except KeyError:
        alert = discord.Embed(
            title="Error", description="That role doesn't exist", color=pretty
        )
        alert.set_footer(text="Error encountered", icon_url=server.logo)
        await message.channel.send(embed=alert, reference=message, mention_author=False)


async def setMentionRole(message, server):
    """Changes the role thats mentioned in task embeds
    Syntax: <prefix>taskmention <role>
    Default role mentioned is everyone."""
    value = message.content.split()[-1]  # this wont work if role has spaces
    if value == "everyone":
        value = "@everyone"
    roles = {}
    for role in message.guild.roles:
        roles[role.name] = role.id
    try:
        server.taskMention = f"<@&{roles[value]}>"
        updateServerConfigs(server)
        alert = discord.Embed(
            title="Mention role configured",
            description=f"Mention role set to {server.taskMention}",
            color=pretty,
        )
        alert.set_footer(text="Settings saved", icon_url=server.logo)
        await message.channel.send(embed=alert, reference=message, mention_author=False)
    except KeyError:
        alert = discord.Embed(
            title="Error", description="That role doesn't exist", color=pretty
        )
        alert.set_footer(text="Error encountered", icon_url=server.logo)
        await message.channel.send(embed=alert, reference=message, mention_author=False)


async def permDenied(message, server):
    desc = "BECAUSE I DON'T WANT TO. PERMISSION DENIED. I REFUSE TO ANSWER. BECAUSE I DONT WANT TO. NEXT. YOU HAVE BEEN STOPPED."
    alert = discord.Embed(
        title="PERMISSION DENIED",
        description=desc,
        url="https://youtu.be/tA8LjcpjjKQ",
        color=pretty,
    )
    alert.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/944164645818744922/947864753026506812/gowk6neidu831.png"
    )
    alert.set_footer(text="NO", icon_url=server.logo)
    await message.channel.send(embed=alert, reference=message, mention_author=False)


async def invalidSyntax(message, server):
    alert = discord.Embed(
        title="Error",
        description="Invalid syntax",
        color=pretty,
    )
    alert.set_footer(text="Error encountered", icon_url=server.logo)
    await message.channel.send(embed=alert, reference=message, mention_author=False)


async def channelnt(message, server):

    if not (server.taskschannel or server.reportschannel):
        desc = "Channel ID for tasks and reports haven't been configured. Please use the help command and configure them"
    elif server.taskschannel and (not server.reportschannel):
        desc = "Channel ID for reports haven't been configured. Please use the help command and configure them"
    elif (not server.taskschannel) and server.reportschannel:
        desc = "Channel ID for tasks haven't been configured. Please use the help command and configure them"
    else:
        return

    alert = discord.Embed(title="Alert", description=desc, color=pretty)
    await message.channel.send(embed=alert, reference=message, mention_author=False)