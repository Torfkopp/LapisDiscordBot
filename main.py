from apscheduler.schedulers.background import BackgroundScheduler
from interactions import Client, Intents, listen, Task, IntervalTrigger
from interactions.client.errors import HTTPException

from core.extensions_loader import load_extensions
from extensions import football

bot = Client(intents=Intents.DEFAULT)
global SPORT_CHANNEL
LIVE_SCORE_MESSAGE = ""


@Task.create(IntervalTrigger(minutes=2))
async def games_in_progress():
    global LIVE_SCORE_MESSAGE
    if LIVE_SCORE_MESSAGE == "": LIVE_SCORE_MESSAGE = await SPORT_CHANNEL.send(embeds=football.get_live()[0])
    else:
        embeds, still_going = football.get_live(LIVE_SCORE_MESSAGE.embeds)
        try: await LIVE_SCORE_MESSAGE.edit(embeds=embeds)
        except HTTPException: LIVE_SCORE_MESSAGE = await SPORT_CHANNEL.send(embeds=embeds)
        if not still_going: games_in_progress.stop()


@Task.create(IntervalTrigger(minutes=1))
def command_call_limit(): football.reduce_command_calls()


def start_gip():
    games_in_progress.start()


@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    global SPORT_CHANNEL
    SPORT_CHANNEL = bot.get_channel(open('config.txt').readlines()[1])


@listen()
async def on_startup():
    command_call_limit.start()
    #scheduler = BackgroundScheduler()
    #jobs = football.create_schedule()
    #for job in jobs: scheduler.add_job(start_gip, 'date', run_date=job)
    #scheduler.start()
    games_in_progress.start()


# load all extensions in the ./extensions folder
load_extensions(bot=bot)

with open('config.txt') as f: token = f.readline()

bot.start(token)
