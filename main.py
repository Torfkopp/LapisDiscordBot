import datetime
import json
import locale
import os
import random

import fastf1
import fastf1.exceptions
import interactions
from interactions import Client, Intents, listen, Task, IntervalTrigger, DateTrigger, TimeTrigger
from interactions.api.events import Error
from interactions.client.errors import HTTPException
from interactions.ext import prefixed_commands
from interactions.models import discord
from matplotlib import font_manager

import secret
import util
from core import log
from core.extensions_loader import load_extensions
from extensions import lolesport, lol_patchnotes, reddit, karma, weather, tierlist
from extensions.football import football
from extensions.formula1 import formula1

TEST_MODE_ON = True

intents = Intents.DEFAULT | Intents.MESSAGES | Intents.MESSAGE_CONTENT
bot = Client(intents=intents, send_command_tracebacks=False)
prefixed_commands.setup(bot)

# core modules moved out of main for clarity
from core import live as core_live
from core.live import LIVE_MESSAGES
from core import activity as core_activity
from core import startup as core_startup


@listen(Error, disable_default_listeners=True)
async def on_error(event: Error):
    log.error(event.error)
    await event.ctx.send(embed=util.get_error_embed("error"))


@listen()
async def on_message_create(event):
    await karma.on_message(event.message)


@listen()
async def on_message_delete(event):
    await karma.on_message_delete(event.message)
    await tierlist.on_message_delete(event.message)


@listen()
async def on_message_reaction_add(event):
    await karma.on_reaction(event)


@listen()
async def on_message_reaction_remove(event):
    await karma.on_reaction_remove(event)


@Task.create(TimeTrigger(hour=8, minute=0, utc=False)):
async def daily_startup():
    await on_startup()


@listen()
async def on_ready():
    """ Is called when the bot is ready """
    log.write("Ready")
    log.write(f"This bot is owned by {bot.owner}")
    await secret.main(bot)
    # Loads the Formula1 font
    for font in font_manager.findSystemFonts(["resources/formula1/font"]): font_manager.fontManager.addfont(font)

# TODO:
# - Naming
# - secret into startup
# - live as class?
# - aufräumen
# - Reihenfolge gewährleisten
# - 

@listen()
async def on_startup():
    """ Startup procedure """
    # If test mode set, run test-mode activity and return
    core_startup.startup_mock.start()
    if TEST_MODE_ON:
        activity = core_activity.ActivityClass(bot, [])
        await activity.test_mode()
        return

    # reset live task references in the live module
    core_live.live_scoring_task = None
    core_live.live_league_task = None
    core_live.live_f1_task = None

    now = datetime.datetime.now()
    await log.start_procedure(bot)
    await LIVE_MESSAGES.init()
    if now.weekday() == 1:
        util.reset_message_tracker()

    await core_startup.startup_football_scoring(now)
    formula1_schedule = formula1.create_schedule()
    await core_startup.startup_formula1_results(formula1_schedule, now)
    await core_startup.startup_formula1_info(now)
    await core_startup.startup_lolesports_results(now)
    await core_startup.startup_patchnotes(now)
    await core_startup.startup_day_dependent()
    await core_startup.startup_daily_meme()
    await core_startup.startup_temperature(now)

    activity = core_activity.ActivityClass(formula1_schedule)
    await activity.rotate_activity()
    Task(activity.rotate_activity, IntervalTrigger(minutes=2)).start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
