import datetime
import json
import locale
import os
import random

import fastf1
import fastf1.core
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
from extensions import lolesport, lol_patchnotes, reddit, karma, weather, tierlist
from extensions.football import football
from extensions.formula1 import formula1

TEST_MODE_ON = False

intents = Intents.DEFAULT | Intents.MESSAGES | Intents.MESSAGE_CONTENT
bot = Client(intents=intents, send_command_tracebacks=False)
prefixed_commands.setup(bot)


class LiveMessageDict(dict):
    async def init(self):
        if str(datetime.datetime.now().date()) != datetime.datetime.fromtimestamp(
                os.path.getmtime("strunt/sport_messages.json")).strftime('%Y-%m-%d'):
            self.update({"score": "", "league": "", "f1": ""})
        else:
            with open("strunt/sport_messages.json") as m: msgs = json.load(m)
            self.update({k: await bot.get_channel(util.SPORTS_CHANNEL_ID).fetch_message(v) if v else "" for k, v in
                         msgs.items()})
        log.write("Live messages initialised")

    def __setitem__(self, key, value):
        print(self)
        super().__setitem__(key, value)
        print(self)
        ids = {k: v.id if isinstance(v, interactions.Message) else v for k, v in self.items()}
        with open("strunt/sport_messages.json", "w") as lmd: json.dump(ids, lmd)


LIVE_MESSAGES = LiveMessageDict()
live_scoring_task, live_league_task, live_f1_task = None, None, None

try: locale.setlocale(locale.LC_ALL, 'de_DE')  # Changes local to Deutsch for time display
except locale.Error:
    try: locale.setlocale(locale.LC_ALL, 'de_DE.utf8')  # Tries this
    except locale.Error: pass  # Accepts defeat


class ActivityClass:
    formula1_schedule = {}
    # "GAME" (Spielt), "STREAMING" (Streamt), "LISTENING" (Hört X zu), "WATCHING" (Schaut), "COMPETING" (Tritt an in)
    activities = [
        # Bot-"Personality" stuff
        ("liest Bücher", discord.activity.ActivityType.WATCHING),
        ("lauscht Marios Gelaber", discord.activity.ActivityType.LISTENING),
        ("schaut ein paar Anime", discord.activity.ActivityType.WATCHING),
        ("schaut HdR zum X-ten Mal", discord.activity.ActivityType.WATCHING),
        ("judged deine Posts", discord.activity.ActivityType.COMPETING),
        ("hört Anime OST", discord.activity.ActivityType.LISTENING),
        ("sucht nach nützlichen APIs", discord.activity.ActivityType.WATCHING),
        # Extension related stuff
        ("schaut sich Anime an", discord.activity.ActivityType.WATCHING),
        ("sucht nach kostenlosen Spielen", discord.activity.ActivityType.WATCHING),
        ("spielt Galgenmännchen", discord.activity.ActivityType.GAME),
        ("sucht nach neuen Insults", discord.activity.ActivityType.WATCHING),
        ("liest die Witze durch", discord.activity.ActivityType.WATCHING),
        ("guckt sich die Patchnotes an", discord.activity.ActivityType.WATCHING),
        ("hört weisen Menschen zu", discord.activity.ActivityType.LISTENING),
        ("schaut sich Tierlisten an", discord.activity.ActivityType.WATCHING),
        ("tritt in einer Quizshow an", discord.activity.ActivityType.COMPETING)
    ]
    status = discord.Status.IDLE  # possible: "ONLINE", "OFFLINE", "DND", "IDLE", "INVISIBLE"

    def __init__(self, formula1_schedule): self.formula1_schedule = formula1_schedule

    async def test_mode(self):
        self.status = discord.Status.DND
        await self._change_activity("Befindet sich im Testmodus", discord.activity.ActivityType.COMPETING)

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
            if watches_football and watches_formula1 and watches_esport: name = "Fußball, F1 und LoL"

            elif watches_football and watches_formula1 and not watches_esport: name = f"Fußball und F1 {f1_session}"
            elif watches_football and not watches_formula1 and watches_esport: name = "Fußball und LoL"
            elif not watches_football and watches_formula1 and watches_esport: name = f"F1 {f1_session} und LoL"

            elif watches_football and not watches_formula1 and not watches_esport: name = "Fußball"
            elif not watches_football and watches_formula1 and not watches_esport: name = f"Formel 1 {f1_session}"
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
    await tierlist.on_message_delete(event.message)


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
    if LIVE_MESSAGES["score"] == "":
        LIVE_MESSAGES["score"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=football.get_live()[0])
    else:
        embeds, still_going = football.get_live()
        try: await LIVE_MESSAGES["score"].edit(embeds=embeds)
        except HTTPException: LIVE_MESSAGES["score"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=embeds)
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
    if LIVE_MESSAGES["league"] == "":
        LIVE_MESSAGES["league"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=lolesport.get_live()[0])
    else:
        embeds, still_going = lolesport.get_live()
        try: await LIVE_MESSAGES["league"].edit(embeds=embeds)
        except HTTPException: LIVE_MESSAGES["league"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(
            embeds=embeds)
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


async def formula1_old_result(session, time):
    """ Tries to send the session mentioned; tries every hour until data loaded """
    try:
        result = formula1.result(session)
        await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)
    except fastf1.core.DataNotLoadedError:
        Task(formula1_old_result, DateTrigger(time + datetime.timedelta(hours=1))).start(session, time)


async def formula1_result():
    """ When called, sends in the result of the latest Formula1 session"""
    result, still_going = formula1.auto_result(True)
    if still_going:  # If the session is still going, try again later
        log.write("Formula1 Session not finished yet; trying again in 10 minutes")
        Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(minutes=10))).start()
    else: await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)


async def live_f1():
    """ Send the live F1 results to the channel and keeps it updated until the session has ended """
    if LIVE_MESSAGES["f1"] == "":
        LIVE_MESSAGES["f1"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(formula1.auto_result(False)[0])
    else:
        result, still_going = formula1.auto_result(False)
        try: await LIVE_MESSAGES["f1"].edit(content=result)
        except HTTPException: LIVE_MESSAGES["f1"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)
        if not still_going:
            # noinspection PyUnresolvedReferences
            live_f1_task.stop()
            LIVE_MESSAGES["f1"] = ""  # Reset the variable to send a new message for a new session
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
        if start_times[0] >= now:  # Both sessions in future
            for start_time in start_times:
                if "Practice" in formula1_schedule.get(start_time):  # If practice session, send result 1 h after start
                    Task(formula1_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()
                else: Task(start_live_f1, DateTrigger(start_time)).start()  # Else, start live tracker at given time

        elif start_times[1] > now or (start_times[1] + datetime.timedelta(hours=1)) > now:  # First gone, second to be
            await formula1_old_result(formula1_schedule.get(start_times[0]), start_times[0])  # First session result
            start_time = start_times[1]
            if "Practice" in formula1_schedule.get(start_time):  # Schedule second session
                Task(formula1_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()
            else: Task(start_live_f1, DateTrigger(start_time)).start()

        else:  # Both Gone
            await formula1_old_result(formula1_schedule.get(start_times[0]), start_times[0])  # First session
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
        message = (f"Jeden Tag ein Meme senden bis ich fertig oder tot bin.\nTag {day_count}\n"
                   + reddit.get_reddit_link("LeagueOfMemes"))
        await bot.get_channel(util.COMEDY_CHANNEL_ID).send(message)


async def startup_temperature(now):
    # AUTOMATIC TEMPERATURE RELATED MEME
    if now.time() < datetime.time(hour=9):  # Doesn't prevent double sends when restarting before 9, but whatever
        embed, file = weather.is_sun_killing(now)
        if embed: await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed, file=file)


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
    await LIVE_MESSAGES.init()
    if now.weekday() == 1: util.reset_message_tracker()  # Reset on Tuesday

    await startup_football_scoring(now)
    formula1_schedule = formula1.create_schedule()
    await startup_formula1_results(formula1_schedule, now)
    await startup_formula1_info(now)
    await startup_lolesports_results(now)
    await startup_patchnotes(now)
    await startup_day_dependent()
    await startup_daily_meme()
    await startup_temperature(now)

    # AUTOMATIC ACTIVITY CHANGE PART
    activity = ActivityClass(formula1_schedule)
    await activity.rotate_activity()
    Task(activity.rotate_activity, IntervalTrigger(minutes=2)).start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
