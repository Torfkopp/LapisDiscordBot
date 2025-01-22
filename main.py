import datetime
import locale
import random
from matplotlib import font_manager

from interactions import Client, Intents, listen, Task, IntervalTrigger, DateTrigger
from interactions.api.events import Error
from interactions.client.errors import HTTPException
from interactions.ext import prefixed_commands
from interactions.models import discord

from core import log
from core.extensions_loader import load_extensions
import secret
import util

from extensions import lolesport, lol_patchnotes, reddit, karma
from extensions.football import football
from extensions.formula1 import formula1

TEST_MODE_ON = False

intents = Intents.DEFAULT | Intents.MESSAGES | Intents.MESSAGE_CONTENT
bot = Client(intents=intents, send_command_tracebacks=False)
prefixed_commands.setup(bot)

LIVE_SCORE_MESSAGE = ""
live_scoring_task = None

LIVE_LEAGUE_MESSAGE = ""
live_league_task = None

LIVE_F1_MESSAGE = ""
live_f1_task = None

try: locale.setlocale(locale.LC_ALL, 'de_DE')  # Changes local to Deutsch for time display
except locale.Error:
    try: locale.setlocale(locale.LC_ALL, 'de_DE.utf8')  # Tries this
    except locale.Error: pass  # Accepts defeat


class ActivityClass:
    formula1_schedule = {}
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
        f1_session = ""

        # noinspection PyUnresolvedReferences
        if live_scoring_task is not None and live_scoring_task.running: watches_football = True
        # noinspection PyUnresolvedReferences
        if live_league_task is not None and live_league_task.running: watches_esport = True
        # noinspection PyUnresolvedReferences
        if live_f1_task is not None and live_f1_task.running: watches_formula1 = True

        for time in self.formula1_schedule:
            if "Practice" in self.formula1_schedule.get(time):
                if datetime.timedelta(minutes=0) < now - time < datetime.timedelta(minutes=60): watches_formula1 = True
            if datetime.timedelta(minutes=-60) < now - time < datetime.timedelta(hours=3):
                f1_session = self.formula1_schedule.get(time)  # Set f1_session variable to current session

        if watches_football or watches_formula1 or watches_esport:
            self.status = discord.Status.DND
            type_ = discord.activity.ActivityType.WATCHING
            name = ""
            if watches_football and watches_formula1 and watches_esport: name = "Fußball, Formel1 und LoL"

            elif watches_football and watches_formula1 and not watches_esport: name = f"Fußball und Formel1 {f1_session}"
            elif watches_football and not watches_formula1 and watches_esport: name = "Fußball und LoL"
            elif not watches_football and watches_formula1 and watches_esport: name = f"Formel1 {f1_session} und LoL"

            elif watches_football and not watches_formula1 and not watches_esport: name = "Fußball"
            elif not watches_football and watches_formula1 and not watches_esport: name = f"Formel1 {f1_session}"
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
async def on_message_create(event):
    await karma.on_message(event.message)


@listen()
async def on_message_delete(event):
    await karma.on_message_delete(event.message)


@listen()
async def on_message_reaction_add(event):
    await karma.on_reaction(event)


@listen()
async def on_message_reaction_remove(event):
    await karma.on_reaction_remove(event)


@Task.create(IntervalTrigger(minutes=1))
def limit_command_calls():
    """ Task to regularly call the extension's command calls reduction """
    football.limit_command_calls()
    formula1.limit_command_calls()
    lolesport.limit_command_calls()


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


async def start_live_league():
    """ When called, creates a task calling live_league and starts it
        or, if it already exits and is stopped, starts it again """
    global live_league_task
    if live_league_task is None:
        live_league_task = Task(live_league, IntervalTrigger(minutes=10))
        live_league_task.start()
        log.write("Live league begins")
        return
    if not live_league_task.running:
        live_league_task.start()
        log.write("Live league begins")


async def formula1_result():
    """ When called, sends in the result of the latest Formula1 session"""
    result, still_going = formula1.auto_result(True)
    if still_going:  # If the session is still going, try again later
        log.write("Formula1 Session not finished yet; trying again in 10 minutes")
        Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(minutes=10))).start()
    else: await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)


async def live_f1():
    """ Send the live F1 results to the channel and keeps it updated until the session has ended """
    global LIVE_F1_MESSAGE
    if LIVE_F1_MESSAGE == "":
        LIVE_F1_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(formula1.auto_result(False)[0])
    else:
        result, still_going = formula1.auto_result(False)
        try: await LIVE_F1_MESSAGE.edit(content=result)
        except HTTPException: LIVE_F1_MESSAGE = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)
        if not still_going:
            # noinspection PyUnresolvedReferences
            live_f1_task.stop()
            LIVE_F1_MESSAGE = ""  # Reset the variable to send a new message for a new session
            log.write("Live F1 stops")


async def start_live_f1():
    """ When called, creates a task calling live_f1 and starts it
        or, if it already exists and is stopped, starts it again """
    global live_f1_task
    if live_f1_task is None:
        live_f1_task = Task(live_f1, IntervalTrigger(minutes=5))
        live_f1_task.start()
        log.write("Live F1 begins")
        return
    if not live_f1_task.running:
        live_f1_task.start()
        log.write("Live F1 begins")


async def update_patchnotes():
    """ When called, updates the lol_patchnotes and, if need be, sends in the patchnotes """
    embed = lol_patchnotes.update()
    if embed: await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed)


async def startup_football_scoring(now):
    # FOOTBALL LIVE SCORING
    football_schedule = football.create_schedule()
    log.write("Starting times of today's games: " + str(football_schedule))
    for start_time in football_schedule:
        # When the start time was less than 90 minutes ago, start the live scoring manually
        if datetime.timedelta(minutes=0) < (now - start_time) < datetime.timedelta(minutes=90):
            await start_live_scoring()
        task = Task(start_live_scoring, DateTrigger(start_time))
        task.start()


async def startup_formula1_results(formula1_schedule, now):
    # FORMULA 1 AUTOMATIC RESULTS
    log.write("Today's formula1 sessions: " + str(formula1_schedule))
    if len(formula1_schedule) == 1:  # Race
        start_time = list(formula1_schedule)[0]
        if start_time > now: Task(start_live_f1, DateTrigger(start_time)).start()
        elif datetime.timedelta(minutes=0) < (now - start_time) < datetime.timedelta(minutes=60): await start_live_f1()
        else: await formula1_result()
    elif len(formula1_schedule) > 1:  # Non Race Days
        start_times = list(formula1_schedule)
        if start_times[0] > now and start_times[1] > now:  # Both in future
            for start_time in start_times:
                if "Practice" in formula1_schedule.get(start_time):  # If practice session, send result 1 h after start
                    Task(formula1_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()
                else: Task(start_live_f1, DateTrigger(start_time)).start()  # Else, start live tracker at given time
        elif start_times[0] < now < start_times[1]:  # First session gone and second to be
            await formula1_result()
            start_time = start_times[1]
            if "Practice" in formula1_schedule.get(start_time):
                Task(formula1_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()
            else: Task(start_live_f1, DateTrigger(start_time)).start()
        else:  # Both Gone
            start_time = start_times[0]
            result_first_session = formula1.result(formula1_schedule.get(start_time))
            await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result_first_session)  # First sessions result
            await formula1_result()  # Second sessions result


async def startup_formula1_info(now):
    # FORMULA 1 AUTOMATIC INFO
    embed = formula1.auto_info()
    if embed is not None:
        if ((now.weekday() == 0 and not util.message_sent("rawe_ceek")) or
                (now.weekday() == 3 and not util.message_sent("race_schedule"))):
            await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embed=embed)


async def startup_lolesports_results(now):
    # AUTOMATIC LOLESPORTS RESULTS
    league_schedule = lolesport.create_schedule()
    if len(league_schedule) > 0 and sorted(league_schedule)[-1] < now:
        await live_league()  # When every start time has already passed, start live league once to get results
    log.write("Starting times of today's lol esport matches: " + str(league_schedule))
    for start_time in league_schedule: Task(start_live_league, DateTrigger(start_time)).start()


async def startup_patchnotes(now):
    # AUTOMATIC LOL_PATCHNOTES
    try:
        await update_patchnotes()
        if now.weekday() == 1:  # Patchnotes are (normally) posted on tuesday at 20:00
            for i in range(4): Task(update_patchnotes, DateTrigger(now.replace(hour=(20 + i), minute=20))).start()
        Task(update_patchnotes, IntervalTrigger(hours=3.25)).start()
    except Exception as e: log.error(e)


async def startup_day_dependent():
    # AUTOMATIC ACTIONS DEPENDING ON SPECIAL DAYS
    if datetime.datetime.now().weekday() == 4 and not util.message_sent("friday_krabs"):
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(file="resources/congratssailer.mp4")
    elif datetime.datetime.now().weekday() == 0 and not util.message_sent("monday_krabs"):
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(file="resources/risesailer.mp4")


async def startup_daily_meme():
    # AUTOMATIC JOJO MEME
    sent_already, day_count = util.day_counter()
    if not sent_already:
        message = (f"Jeden Tag ein JoJo-Meme senden bis Jakob mit JoJo fertig ist. Tag {day_count}\n"
                   + reddit.get_reddit_link("ShitPostCrusaders"))
        await bot.get_channel(util.COMEDY_CHANNEL_ID).send(message)


@listen()
async def on_startup():
    """ Is called when the bot starts up (used for schedule things) """
    if TEST_MODE_ON:
        activity = ActivityClass([])
        await activity.test_mode()
        return
    now = datetime.datetime.now()
    limit_command_calls.start()
    await log.start_procedure(bot)
    if now.weekday() == 1: util.reset_message_tracker()  # Reset on Tuesday

    await startup_football_scoring(now)
    formula1_schedule = formula1.create_schedule()
    await startup_formula1_results(formula1_schedule, now)
    await startup_formula1_info(now)
    await startup_lolesports_results(now)
    await startup_patchnotes(now)
    await startup_day_dependent()
    await startup_daily_meme()

    # AUTOMATIC ACTIVITY CHANGE PART
    activity = ActivityClass(formula1_schedule)
    await activity.rotate_activity()
    Task(activity.rotate_activity, IntervalTrigger(minutes=2)).start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
