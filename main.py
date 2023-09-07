import datetime
import random
import traceback

import interactions
from interactions import Client, Intents, listen, Task, IntervalTrigger, DateTrigger
from interactions.api.events import Error
from interactions.client.errors import HTTPException
from interactions.ext import prefixed_commands
from interactions.models import discord
from matplotlib import font_manager

import secret
import util
from core.extensions_loader import load_extensions
from extensions import freegames, lolesport, lol_patchnotes
from extensions.football import football
from extensions.formula1 import formula1

bot = Client(intents=Intents.DEFAULT, send_command_tracebacks=False)
prefixed_commands.setup(bot)

LIVE_SCORE_MESSAGE = ""
current_task = None

TEST_MODE_ON = False


class ActivityClass:
    football_schedule = []
    formula1_schedule = []
    # "GAME" (Spielt), "STREAMING" (Streamt), "LISTENING" (Hört X zu), "WATCHING" (Schaut), "COMPETING" (Tritt an in)
    activities = [
        # Bot-"Personality" stuff
        ("sich Bücher an", discord.activity.ActivityType.WATCHING),
        ("Marios Gelaber", discord.activity.ActivityType.LISTENING),
        ("ein paar Anime", discord.activity.ActivityType.WATCHING),
        ("HdR zum X-ten Mal", discord.activity.ActivityType.WATCHING),
        ("und tritt aus", discord.activity.ActivityType.COMPETING),
        ("Anime OST", discord.activity.ActivityType.LISTENING),
        ("nach nützlichen APIs", discord.activity.ActivityType.WATCHING),
        # Extension related stuff
        ("sich Anime an", discord.activity.ActivityType.WATCHING),
        ("nach kostenlosen Spielen", discord.activity.ActivityType.WATCHING),
        ("Galgenmännchen", discord.activity.ActivityType.GAME),
        ("nach neuen Insults", discord.activity.ActivityType.WATCHING),
        ("die Witze durch", discord.activity.ActivityType.WATCHING),
        ("sich die Patchnotes an", discord.activity.ActivityType.WATCHING),
        ("LoL-Esport", discord.activity.ActivityType.WATCHING),
        ("weisen Menschen", discord.activity.ActivityType.LISTENING),
        ("einer Quizshow", discord.activity.ActivityType.COMPETING)
    ]
    status = discord.Status.IDLE  # possible: "ONLINE", "OFFLINE", "DND", "IDLE", "INVISIBLE"

    def __init__(self, football_schedule, formula1_schedule):
        self.football_schedule = football_schedule
        self.formula1_schedule = formula1_schedule

    async def test_mode(self):
        self.status = discord.Status.DND
        await self._change_activity("nem Test Modus", discord.activity.ActivityType.COMPETING)

    async def rotate_activity(self):
        """ Changes the activity depending on the situation """
        now = datetime.datetime.now()
        watches_football, watches_formula1 = False, False
        for time in self.football_schedule:
            if datetime.timedelta(minutes=0) < now - time < datetime.timedelta(minutes=100): watches_football = True
        for time in self.formula1_schedule:
            if datetime.timedelta(minutes=0) < now - time < datetime.timedelta(minutes=100): watches_formula1 = True

        if watches_football and watches_formula1:
            self.status = discord.Status.DND
            name = "Fußball und Formel 1"
            type_ = discord.activity.ActivityType.WATCHING
        elif watches_football:
            self.status = discord.Status.DND
            name = "sich Fußball an"
            type_ = discord.activity.ActivityType.WATCHING
        elif watches_formula1:
            self.status = discord.Status.DND
            name = "sich Formel 1 an"
            type_ = discord.activity.ActivityType.WATCHING
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
        try:
            await LIVE_SCORE_MESSAGE.edit(embeds=embeds)
        except HTTPException:
            LIVE_SCORE_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=embeds)
        if not still_going:
            # noinspection PyUnresolvedReferences
            current_task.stop()  # current_task is a task when this is called, thus PyUnresolvedReferences ignorable
            print("Live scoring stops")


async def start_gip():
    """ When called, creates a task calling live_scoring and starts it
    or, if it already exits and is stopped, starts it again """
    global current_task
    if current_task is None:
        current_task = Task(live_scoring, IntervalTrigger(minutes=2))
        current_task.start()
        print("Live scoring begins")
        return
    if not current_task.running:
        current_task.start()
        print("Live scoring begins")


async def formula1_result():
    """ When called, sends in the result of the latest Formula1 session"""
    result = formula1.auto_result()
    # If getting result fails, try again in an hour
    if result == "": Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(hours=0.5))).start()
    else: await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)


async def update_patchnotes():
    """ When called, updates the lol_patchnotes and, if need be, sends in the patchnotes """
    embed = lol_patchnotes.update()
    if embed: await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed)


@listen(Error, disable_default_listeners=True)
async def on_error(event: Error):
    traceback.print_exception(event.error)
    await event.ctx.send(embed=util.get_error_embed("error"))


@listen()
async def on_ready():
    """ Is called when the bot is ready """
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    await secret.main(bot)
    # Loads the Formula1 font
    for font in font_manager.findSystemFonts(["formula1/font"]): font_manager.fontManager.addfont(font)


@listen()
async def on_startup():
    """ Is called when the bot starts up (used for schedule things) """
    if TEST_MODE_ON:
        activity = ActivityClass([], [])
        await activity.test_mode()
        return
    reduce_command_calls.start()

    # FOOTBALL LIVE SCORING PART
    football_schedule = football.create_schedule()
    print("Starting times of today's games: " + str(football_schedule))
    for start_time in football_schedule:
        # When the start time was less than 90 minutes ago, start the live scoring automatically
        if datetime.timedelta(minutes=0) < (datetime.datetime.now() - start_time) < datetime.timedelta(minutes=90):
            await start_gip()
        task = Task(start_gip, DateTrigger(start_time))
        task.start()

    # FORMULA 1 AUTOMATIC RESULTS PART
    formula1_schedule, embed = formula1.create_schedule()
    if isinstance(embed, interactions.Embed): await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embed=embed)
    print("Today's formula1 sessions: " + str(formula1_schedule))
    for start_time in formula1_schedule: Task(formula1_result, DateTrigger(start_time)).start()

    # AUTOMATIC ACTIVITY CHANGE PART
    activity = ActivityClass(football_schedule, formula1_schedule)
    await activity.rotate_activity()
    Task(activity.rotate_activity, IntervalTrigger(minutes=2)).start()

    # AUTOMATIC FREE GAMES PART
    if datetime.datetime.now().weekday() == 4:
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=freegames.get_giveaways())

    # AUTOMATIC LOL_PATCHNOTES PART
    await update_patchnotes()
    Task(update_patchnotes, IntervalTrigger(hours=2)).start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
