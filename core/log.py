import datetime
import traceback
import asyncio
from functools import wraps

from interactions.models import discord

import util

""" Own logging class since bot runs remotely """


async def start_procedure(bot):
    """Sends the logfile into the channel and then cleans the file"""
    channel = bot.get_channel(util.LOGBUCH_ID)
    if datetime.datetime.now().weekday() == 0:
        await delete_old_messages(channel)
        await backup(channel)
    await channel.send(file=discord.File("variable/log.txt"))  # Send the log into a channel
    open("variable/log.txt", "w").close()  # Clear the log data
    print("LOG CLEARED")


async def delete_old_messages(channel):
    async for m in channel.history(limit=20):
        await m.delete()


async def backup(channel):
    await channel.send(file=discord.File("variable/karma.db"))
    await channel.send(file=discord.File("variable/elo.db"))
    await channel.send(file=discord.File("variable/elo.json"))


def write(log, to_print=True):
    """Writes the parameter to the logfile with the time in front"""
    if to_print:
        print(f"{datetime.datetime.now()}: {log}")
    with open("variable/log.txt", "a") as logfile:
        logfile.write(f"{datetime.datetime.now()}: {log}\n")


def error(err, prevented=False):
    """Writes the error to the file"""
    traceback.print_exception(err)
    error_message = traceback.format_exception(err)
    with open("variable/log.txt", "a") as logfile:
        logfile.write("-" * 20)
        logfile.write(f"\n {datetime.datetime.now()} ERROR{(' PREVENTED') if prevented else ''}\n")
        for line in error_message:
            logfile.write(line)
        logfile.write("\n" + "-" * 20 + "\n")


def safe_call(func):
    """Decorator that catches exceptions, logs them and prevents propagation.

    Works for both async and sync functions. Uses `core.log.error` to record
    the exception details.
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error(e, True)
                return None

        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error(e, True)
                return None

        return sync_wrapper


def safe_request(url, log_message=None, to_print=True, json_response=True, headers="", payload="", querystring=""):
    """Performs a requests.request, logs the action, and safely catches exceptions.

    Returns the parsed JSON dictionary/list (if json_response is True) or the response object itself.
    Returns None on any exception.
    """
    import requests

    if log_message:
        write(f"API Call {log_message}: {url} {querystring}", to_print)
    try:
        response = requests.get(url, headers=headers, params=querystring, data=payload)
        if json_response: return response.json()
        return response
    except Exception as e:
        write(f"ERROR: {e}")
        return None
