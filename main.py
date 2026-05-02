import datetime
import locale

from interactions import Client, Intents, listen, Task, IntervalTrigger, TimeTrigger
from interactions.api.events import Error
from interactions.ext import prefixed_commands
from matplotlib import font_manager

import util
from core import log, daily, activity, live
from core.extensions_loader import load_extensions

from extensions import karma, tierlist
from extensions.formula1 import formula1


TEST_MODE_ON = False

intents = Intents.DEFAULT | Intents.MESSAGES | Intents.MESSAGE_CONTENT
bot = Client(intents=intents, send_command_tracebacks=False)
prefixed_commands.setup(bot)


try:
    locale.setlocale(locale.LC_ALL, "de_DE")  # Changes local to Deutsch for time display
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, "de_DE.utf8")  # Tries this
    except locale.Error:
        pass  # Accepts defeat


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


@Task.create(TimeTrigger(hour=8, minute=0, utc=False))
async def daily_procedure():
    if datetime.datetime.now().weekday() == 1:
        util.reset_message_tracker()
    await log.start_procedure(bot)
    await daily.daily_messages(bot)


@listen()
async def on_ready():
    """Is called when the bot is ready"""
    log.write("Ready")
    log.write(f"This bot is owned by {bot.owner}")
    # Loads the Formula1 font
    for font in font_manager.findSystemFonts(["resources/formula1/font"]):
        font_manager.fontManager.addfont(font)


@listen()
async def on_startup():
    """Startup procedure"""
    # If test mode set, run test-mode activity and return
    if TEST_MODE_ON:
        act = activity.ActivityClass(bot, [])
        await act.test_mode()
        return

    # create live manager and expose it on the module for other modules to inspect
    live_manager = live.create_manager(bot)
    live.live_manager = live_manager

    if datetime.datetime.now().hour >= 8:
        await daily_procedure()
    daily_procedure.start()

    await live_manager.start()

    act = activity.ActivityClass(bot, formula1.create_schedule())
    await act.rotate_activity()
    Task(act.rotate_activity, IntervalTrigger(minutes=2)).start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
