import datetime
import json
import traceback

from interactions.models import discord

""" Own logging class since bot runs remotely """


async def start_procedure(bot):
    """ Sends the logfile into the channel and then cleans the file """
    with open("config.json") as f: log_channel = json.load(f)['logbuch']
    channel = bot.get_channel(log_channel)
    await channel.send(file=discord.File("strunt/log.txt"))  # Send the log into a channel
    open('strunt/log.txt', 'w').close()  # Clear the log data


def write(log):
    """ Writes the parameter to the logfile with the time in front """
    print(log)
    with open("strunt/log.txt", "a") as logfile: logfile.write(f"{datetime.datetime.now()}: {log}\n")


def error(err):
    """ Writes the error to the file """
    traceback.print_exception(err)
    with open("strunt/log.txt", "a") as logfile:
        logfile.write(f"\n {datetime.datetime.now()} ERROR\n{err}\n")
