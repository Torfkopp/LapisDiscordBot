import datetime

import interactions
from interactions import Client, Intents, listen, Task, IntervalTrigger, DateTrigger
from interactions.client.errors import HTTPException

from core.extensions_loader import load_extensions
from extensions.football import football
from extensions.formula1 import formula1

bot = Client(intents=Intents.DEFAULT)
global SPORT_CHANNEL
LIVE_SCORE_MESSAGE = ""
current_task = None


@Task.create(IntervalTrigger(minutes=1))
def command_call_limit():
    """ Task to regularly call the extension's handling of command limiting"""
    football.reduce_command_calls()
    formula1.reduce_command_calls()


async def live_scoring():
    """ Sends the live scoring to the channel and keeps it updated until all live games have ended """
    global LIVE_SCORE_MESSAGE
    if LIVE_SCORE_MESSAGE == "":
        LIVE_SCORE_MESSAGE = await SPORT_CHANNEL.send(embeds=football.get_live()[0])
    else:
        embeds, still_going = football.get_live(LIVE_SCORE_MESSAGE.embeds)
        try:
            await LIVE_SCORE_MESSAGE.edit(embeds=embeds)
        except HTTPException:
            LIVE_SCORE_MESSAGE = await SPORT_CHANNEL.send(embeds=embeds)
        if not still_going: current_task.stop()  # current_task is a task when this is called, thus ignorable


async def start_gip():
    """ When called, creates a task calling live_scoring and starts it
    or, if it already exits and is stopped, starts it again """
    global current_task
    if current_task is None:
        current_task = Task(live_scoring, IntervalTrigger(minutes=2))
        current_task.start()
        return
    if not current_task.running:
        current_task.start()


async def formula1_result():
    """ When called, sends in the result of the latest Formula1 session"""
    result = formula1.auto_result()
    # If getting result fails, try again in an hour
    if result == "": Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(hours=1))).start()
    await SPORT_CHANNEL.send(result)


@listen()
async def on_ready():
    """ Is called when the bot is ready """
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    global SPORT_CHANNEL
    SPORT_CHANNEL = bot.get_channel(open('config.txt').readlines()[1])


@listen()
async def on_startup():
    """ Is called when the bot starts up """
    command_call_limit.start()
    # football_schedule = football.create_schedule()
    formula1_schedule, embed = formula1.create_schedule()
    if isinstance(embed, interactions.Embed): await SPORT_CHANNEL.send(embed=embed)
    # print("Starting times of today's games: " + str(football_schedule))
    # print("Today's formula1 sessions: " + str(formula1_schedule))
    # for start_time in football_schedule:
    #    task = Task(start_gip, DateTrigger(start_time))
    #    task.start()
    for start_time in formula1_schedule:
        task = Task(formula1_result, DateTrigger(start_time))
        task.start()

    # games_in_progress.start()  # For testing purposes


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

with open('config.txt') as f: token = f.readline()

bot.start(token)
