import datetime
import traceback

from interactions.models import discord

import util

""" Own logging class since bot runs remotely """


async def start_procedure(bot):
    """ Sends the logfile into the channel and then cleans the file """
    channel = bot.get_channel(util.LOGBUCH_ID)
    if datetime.datetime.now().weekday() == 0:
        await delete_old_messages(channel)
        await backup(channel)
    await channel.send(file=discord.File("strunt/log.txt"))  # Send the log into a channel
    open('strunt/log.txt', 'w').close()  # Clear the log data
    print("LOG CLEARED")


async def delete_old_messages(channel):
    async for m in channel.history(limit=20):
        await m.delete()


async def backup(channel):
    await channel.send(file=discord.File("strunt/karma.db"))
    await channel.send(file=discord.File("strunt/elo.db"))
    await channel.send(file=discord.File("strunt/elo.json"))


def write(log):
    """ Writes the parameter to the logfile with the time in front """
    print(log)
    with open("strunt/log.txt", "a") as logfile: logfile.write(f"{datetime.datetime.now()}: {log}\n")


def error(err):
    """ Writes the error to the file """
    traceback.print_exception(err)
    error_message = traceback.format_exception(err)
    with open("strunt/log.txt", "a") as logfile:
        logfile.write(f"\n {datetime.datetime.now()} ERROR\n")
        for line in error_message: logfile.write(line)
        logfile.write("\n")
