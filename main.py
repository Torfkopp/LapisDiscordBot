import datetime

import interactions
from interactions import Client, Intents, listen, Task, IntervalTrigger, DateTrigger
from interactions.client.errors import HTTPException
from interactions.models import discord
from matplotlib import font_manager

import util
from core.extensions_loader import load_extensions
from extensions import freegames, lolesport
from extensions.football import football
from extensions.formula1 import formula1

bot = Client(intents=Intents.DEFAULT)
global SPORT_CHANNEL
LIVE_SCORE_MESSAGE = ""
current_task = None

LIVE_SCORING_ON = True
FORMULA1_AUTO_RESULT_ON = True
FREE_GAMES_AUTO_ON = True


async def change_activity(activity):
    """ Changes the bot's presence accordingly
    activity: the activity the Bot should do (note "Watching" comes before the string) """
    await bot.change_presence(status=discord.Status.IDLE,
                              activity=discord.activity.Activity.create(name=activity,
                                                                        type=discord.activity.ActivityType.WATCHING))


@Task.create(IntervalTrigger(minutes=1))
def reduce_command_calls():
    """ Task to regularly call the extension's command calls reduction """
    football.reduce_command_calls()
    formula1.reduce_command_calls()
    lolesport.reduce_command_calls()


# noinspection PyUnresolvedReferences
async def live_scoring():
    """ Sends the live scoring to the channel and keeps it updated until all live games have ended """
    await change_activity("sich Fußball an")
    global LIVE_SCORE_MESSAGE
    if LIVE_SCORE_MESSAGE == "":
        LIVE_SCORE_MESSAGE = await SPORT_CHANNEL.send(embeds=football.get_live()[0])
    else:
        embeds, still_going = football.get_live(LIVE_SCORE_MESSAGE.embeds)
        try:
            await LIVE_SCORE_MESSAGE.edit(embeds=embeds)
        except HTTPException:
            LIVE_SCORE_MESSAGE = await SPORT_CHANNEL.send(embeds=embeds)
        if not still_going:
            current_task.stop()  # current_task is a task when this is called, thus PyUnresolvedReferences ignorable
            print("Live scoring stops")
            await change_activity("sich wieder Bücher an")


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
    await change_activity("sich Formel1 Highlights an")
    result = formula1.auto_result()
    # If getting result fails, try again in an hour
    if result == "": Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(hours=1))).start()
    await SPORT_CHANNEL.send(result)


@listen()
async def on_ready():
    """ Is called when the bot is ready """
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    await change_activity("sich Bücher an")
    global SPORT_CHANNEL
    SPORT_CHANNEL = bot.get_channel(util.SPORTS_CHANNEL_ID)
    # Loads the Formula1 font
    for font in font_manager.findSystemFonts(["formula1/font"]): font_manager.fontManager.addfont(font)


@listen()
async def on_startup():
    """ Is called when the bot starts up (used for schedule things) """
    reduce_command_calls.start()

    # FOOTBALL LIVE SCORING PART
    if LIVE_SCORING_ON:
        football_schedule = football.create_schedule()
        print("Starting times of today's games: " + str(football_schedule))
        for start_time in football_schedule:
            # When the start time was less than 90 minutes ago, start the live scoring automatically
            if start_time - datetime.datetime.now() > datetime.timedelta(minutes=-90): await start_gip()
            task = Task(start_gip, DateTrigger(start_time))
            task.start()

    # FORMULA 1 AUTOMATIC RESULTS PART
    if FORMULA1_AUTO_RESULT_ON:
        formula1_schedule, embed = formula1.create_schedule()
        if isinstance(embed, interactions.Embed): await SPORT_CHANNEL.send(embed=embed)
        print("Today's formula1 sessions: " + str(formula1_schedule))
        for start_time in formula1_schedule:
            task = Task(formula1_result, DateTrigger(start_time))
            task.start()

    # AUTOMATIC FREE GAMES PART
    if FREE_GAMES_AUTO_ON:
        if datetime.datetime.now().weekday() == 4:
            await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=freegames.get_giveaways())


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

bot.start(util.TOKEN)
