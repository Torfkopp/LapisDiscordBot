import datetime
import locale
import random

import interactions
from interactions import Client, Intents, listen, Task, IntervalTrigger, DateTrigger
from interactions.api.events import Error
from interactions.client.errors import HTTPException
from interactions.ext import prefixed_commands
from interactions.models import discord
from matplotlib import font_manager

import secret
import util
from core import log
from core.extensions_loader import load_extensions
from extensions import lolesport, lol_patchnotes, freegames
from extensions.football import football
from extensions.formula1 import formula1

bot = Client(intents=Intents.DEFAULT, send_command_tracebacks=False)
prefixed_commands.setup(bot)

LIVE_SCORE_MESSAGE = ""
live_scoring_task = None

LIVE_LEAGUE_MESSAGE = ""
live_league_task = None

TEST_MODE_ON = False

try: locale.setlocale(locale.LC_ALL, 'de_DE')  # Changes local to Deutsch for time display
except locale.Error:
    try: locale.setlocale(locale.LC_ALL, 'de_DE.utf8')  # Tries this
    except locale.Error: pass  # Accepts defeat


class ActivityClass:
    formula1_schedule = []
    # "GAME" (Spielt), "STREAMING" (Streamt), "LISTENING" (Hört X zu), "WATCHING" (Schaut), "COMPETING" (Tritt an in)
    activities = [
        # Bot-"Personality" stuff
        ("sich Bücher an", discord.activity.ActivityType.WATCHING),
        ("Marios Gelaber", discord.activity.ActivityType.LISTENING),
        ("ein paar Anime", discord.activity.ActivityType.WATCHING),
        ("HdR zum X-ten Mal", discord.activity.ActivityType.WATCHING),
        ("und tritt aus in", discord.activity.ActivityType.COMPETING),
        ("Anime OST", discord.activity.ActivityType.LISTENING),
        ("nach nützlichen APIs", discord.activity.ActivityType.WATCHING),
        # Extension related stuff
        ("sich Anime an", discord.activity.ActivityType.WATCHING),
        ("nach kostenlosen Spielen", discord.activity.ActivityType.WATCHING),
        ("Galgenmännchen", discord.activity.ActivityType.GAME),
        ("nach neuen Insults", discord.activity.ActivityType.WATCHING),
        ("die Witze durch", discord.activity.ActivityType.WATCHING),
        ("sich die Patchnotes an", discord.activity.ActivityType.WATCHING),
        ("weisen Menschen", discord.activity.ActivityType.LISTENING),
        ("sich Tierlisten an", discord.activity.ActivityType.WATCHING),
        ("einer Quizshow", discord.activity.ActivityType.COMPETING)
    ]
    status = discord.Status.IDLE  # possible: "ONLINE", "OFFLINE", "DND", "IDLE", "INVISIBLE"

    def __init__(self, formula1_schedule): self.formula1_schedule = formula1_schedule

    async def test_mode(self):
        self.status = discord.Status.DND
        await self._change_activity("nem Test Modus", discord.activity.ActivityType.COMPETING)

    async def rotate_activity(self):
        """ Changes the activity depending on the situation """
        now = datetime.datetime.now()
        watches_football, watches_formula1, watches_esport = False, False, False

        # noinspection PyUnresolvedReferences
        if live_scoring_task is not None and live_scoring_task.running: watches_football = True
        # noinspection PyUnresolvedReferences
        if live_league_task is not None and live_league_task.running: watches_esport = True
        for time in self.formula1_schedule:
            if datetime.timedelta(minutes=0) < now - (time - datetime.timedelta(hours=1.5)) < datetime.timedelta(
                    minutes=100): watches_formula1 = True

        if watches_football or watches_formula1 or watches_esport:
            self.status = discord.Status.DND
            type_ = discord.activity.ActivityType.WATCHING
            name = ""
            if watches_football and watches_formula1 and watches_esport: name = "Fußball, Formel1 und LoL"

            elif watches_football and watches_formula1 and not watches_esport: name = "Fußball und Formel1"
            elif watches_football and not watches_formula1 and watches_esport: name = "Fußball und LoL"
            elif not watches_football and watches_formula1 and watches_esport: name = "Formel1 und LoL"

            elif watches_football and not watches_formula1 and not watches_esport: name = "Fußball"
            elif not watches_football and watches_formula1 and not watches_esport: name = "Formel1"
            elif not watches_football and not watches_formula1 and watches_esport: name = "LoL"
        else:
            self.status = discord.Status.IDLE
            # activity = self.activities.pop()  # Take first element and put it at the end
            # self.activities.insert(0, activity)
            activity = random.choice(self.activities)  # Takes a random element
            name = activity[0]
            type_ = activity[1]

        await self._change_activity(name, type_)
        return

    async def _change_activity(self, activity_name, activity_type):
        """ Internal method to chance the activity"""
        activity = discord.activity.Activity.create(name=activity_name, type=activity_type)
        await bot.change_presence(status=self.status, activity=activity)
        return


@Task.create(IntervalTrigger(minutes=1))
def reduce_command_calls():
    """ Task to regularly call the extension's command calls reduction """
    football.reduce_command_calls()
    formula1.reduce_command_calls()
    lolesport.reduce_command_calls()


async def live_scoring():
    """ Sends the live scoring to the channel and keeps it updated until all live games have ended """
    global LIVE_SCORE_MESSAGE
    if LIVE_SCORE_MESSAGE == "":
        LIVE_SCORE_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=football.get_live()[0])
    else:
        embeds, still_going = football.get_live(LIVE_SCORE_MESSAGE.embeds)
        try: await LIVE_SCORE_MESSAGE.edit(embeds=embeds)
        except HTTPException: LIVE_SCORE_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=embeds)
        if not still_going:
            # noinspection PyUnresolvedReferences
            live_scoring_task.stop()  # live_scoring_task is a task, thus PyUnresolvedReferences ignorable
            log.write("Live scoring stops")


async def start_live_scoring():
    """ When called, creates a task calling live_scoring and starts it
    or, if it already exits and is stopped, starts it again """
    global live_scoring_task
    if live_scoring_task is None:
        live_scoring_task = Task(live_scoring, IntervalTrigger(minutes=2))
        live_scoring_task.start()
        log.write("Live scoring begins")
        return
    if not live_scoring_task.running:
        live_scoring_task.start()
        log.write("Live scoring begins")


async def live_league():
    """ Sends the live league results to the channel and keeps it updated until all live games have ended """
    global LIVE_LEAGUE_MESSAGE
    if LIVE_LEAGUE_MESSAGE == "":
        LIVE_LEAGUE_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=lolesport.get_live()[0])
    else:
        embeds, still_going = lolesport.get_live()
        try: await LIVE_LEAGUE_MESSAGE.edit(embeds=embeds)
        except HTTPException: LIVE_LEAGUE_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=embeds)
        if not still_going:
            # noinspection PyUnresolvedReferences
            live_league_task.stop()
            log.write("Live league stops")
    return


async def start_live_league():
    """ When called, creates a task calling live_league and starts it
        or, if it already exits and is stopped, starts it again """
    global live_league_task
    if live_league_task is None:
        live_league_task = Task(live_league, IntervalTrigger(minutes=30))
        live_league_task.start()
        log.write("Live league begins")
        return
    if not live_league_task.running:
        live_league_task.start()
        log.write("Live league begins")


async def formula1_result():
    """ When called, sends in the result of the latest Formula1 session"""
    result = formula1.auto_result()
    # If getting result fails, try again in an hour
    if result is None:
        log.write("Formula1 Session not finished yet; trying again in 10 minutes")
        Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(hours=0.1))).start()
    else: await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)


async def update_patchnotes():
    """ When called, updates the lol_patchnotes and, if need be, sends in the patchnotes """
    embed = lol_patchnotes.update()
    if embed: await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed)


async def pseudo_restart():
    """ Resets the variables for automatic results and calls on_startup again """
    global LIVE_SCORE_MESSAGE, LIVE_LEAGUE_MESSAGE, live_scoring_task, live_league_task
    LIVE_SCORE_MESSAGE = ""
    live_scoring_task = None

    LIVE_LEAGUE_MESSAGE = ""
    live_league_task = None
    await on_startup()


@listen(Error, disable_default_listeners=True)
async def on_error(event: Error):
    log.error(event.error)
    await event.ctx.send(embed=util.get_error_embed("error"))


@listen()
async def on_ready():
    """ Is called when the bot is ready """
    log.write("Ready")
    log.write(f"This bot is owned by {bot.owner}")
    await secret.main(bot)
    # Loads the Formula1 font
    for font in font_manager.findSystemFonts(["formula1/font"]): font_manager.fontManager.addfont(font)


@listen()
async def on_startup():
    """ Is called when the bot starts up (used for schedule things) """
    if TEST_MODE_ON:
        activity = ActivityClass([])
        await activity.test_mode()
        return
    reduce_command_calls.start()
    await log.start_procedure(bot)

    # FOOTBALL LIVE SCORING PART
    football_schedule = football.create_schedule()
    log.write("Starting times of today's games: " + str(football_schedule))
    for start_time in football_schedule:
        # When the start time was less than 90 minutes ago, start the live scoring automatically
        if datetime.timedelta(minutes=0) < (datetime.datetime.now() - start_time) < datetime.timedelta(minutes=90):
            await start_live_scoring()
        task = Task(start_live_scoring, DateTrigger(start_time))
        task.start()

    # FORMULA 1 AUTOMATIC RESULTS PART
    formula1_schedule, embed = formula1.create_schedule()
    if isinstance(embed, interactions.Embed): await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embed=embed)
    log.write("Today's formula1 sessions (ending times): " + str(formula1_schedule))
    for start_time in formula1_schedule: Task(formula1_result, DateTrigger(start_time)).start()

    # AUTOMATIC LOLESPORTS RESULTS PART
    league_schedule = lolesport.create_schedule()
    # When every start time has already past, start live league manually
    if len(league_schedule) > 0 and league_schedule[len(league_schedule) - 1] < datetime.datetime.now():
        await start_live_league()
    log.write("Starting times of today's lol esport matches: " + str(league_schedule))
    for start_time in league_schedule: Task(start_live_league, DateTrigger(start_time)).start()

    # AUTOMATIC ACTIVITY CHANGE PART
    activity = ActivityClass(formula1_schedule)
    await activity.rotate_activity()
    Task(activity.rotate_activity, IntervalTrigger(minutes=2)).start()

    # AUTOMATIC FREE GAMES PART
    if datetime.datetime.now().weekday() == 4:
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=freegames.get_giveaways())

    # AUTOMATIC LOL_PATCHNOTES PART
    await update_patchnotes()
    Task(update_patchnotes, IntervalTrigger(hours=2)).start()

    # AUTOMATIC PSEUDO RESTART PART
    # Only important when the bot runs 24/7
    # Task(pseudo_restart, IntervalTrigger(hours=24)).start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
