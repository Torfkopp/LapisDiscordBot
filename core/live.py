import datetime
import json
import os

import interactions
from interactions import Task, IntervalTrigger, DateTrigger
from interactions.client.errors import HTTPException

import util
from core import log
from extensions import lolesport
from extensions.football import football
from extensions.formula1 import formula1


class LiveMessageDict(dict):
    async def init(self):
        if str(datetime.datetime.now().date()) != datetime.datetime.fromtimestamp(
                os.path.getmtime("variable/sport_messages.json")).strftime('%Y-%m-%d'):
            self.update({"score": "", "league": "", "f1": ""})
        else:
            with open("variable/sport_messages.json") as m: msgs = json.load(m)
            for k, v in msgs.items():
                if k not in ["score", "league", "f1"]: continue
                # import bot lazily to avoid circular imports at module import time
                from main import bot
                message = await bot.get_channel(util.SPORTS_CHANNEL_ID).fetch_message(v) if v else ""
                self[k] = message if message else ""
        log.write("Live messages initialised")

    def __getitem__(self, key):
        return super().get(key, "")

    def __setitem__(self, key, value):
        if not value: value = ""
        super().__setitem__(key, value)
        ids = {k: v.id if isinstance(v, interactions.Message) else v for k, v in self.items()}
        with open("variable/sport_messages.json", "w") as lmd: json.dump(ids, lmd)

# Module-level shared state
LIVE_MESSAGES = LiveMessageDict()
live_scoring_task = None
live_league_task = None
live_f1_task = None

async def live_scoring():
    from main import bot
    if LIVE_MESSAGES["score"] == "":
        LIVE_MESSAGES["score"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=football.get_live()[0])
    else:
        embeds, still_going = football.get_live()
        try:
            await LIVE_MESSAGES["score"].edit(embeds=embeds)
        except HTTPException:
            LIVE_MESSAGES["score"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=embeds)
        if not still_going:
            global live_scoring_task
            if live_scoring_task is not None:
                live_scoring_task.stop()
            log.write("Live scoring stops")


async def start_live_scoring():
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
    from main import bot
    if LIVE_MESSAGES["league"] == "":
        LIVE_MESSAGES["league"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=lolesport.get_live()[0])
    else:
        embeds, still_going = lolesport.get_live()
        try:
            await LIVE_MESSAGES["league"].edit(embeds=embeds)
        except HTTPException:
            LIVE_MESSAGES["league"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embeds=embeds)
        if not still_going:
            global live_league_task
            if live_league_task is not None:
                live_league_task.stop()
            log.write("Live league stops")


async def start_live_league():
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
    from main import bot
    try:
        result = formula1.result(session)
        await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)
    except Exception as e:
        # fastf1.exceptions.DataNotLoadedError may be raised by formula1.result
        Task(formula1_old_result, DateTrigger(time + datetime.timedelta(hours=1))).start(session, time)


async def formula1_result():
    from main import bot
    result, still_going = formula1.auto_result(True)
    if still_going:
        log.write("Formula1 Session not finished yet; trying again in 10 minutes")
        Task(formula1_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(minutes=10))).start()
    else:
        await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)


async def live_f1():
    from main import bot
    if LIVE_MESSAGES["f1"] == "":
        LIVE_MESSAGES["f1"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(formula1.auto_result(False)[0])
    else:
        result, still_going = formula1.auto_result(False)
        try:
            await LIVE_MESSAGES["f1"].edit(content=result)
        except HTTPException:
            LIVE_MESSAGES["f1"] = await bot.get_channel(util.SPORTS_CHANNEL_ID).send(result)
        if not still_going:
            global live_f1_task
            if live_f1_task is not None:
                live_f1_task.stop()
            LIVE_MESSAGES["f1"] = ""
            log.write("Live F1 stops")


async def start_live_f1():
    global live_f1_task
    if live_f1_task is None:
        live_f1_task = Task(live_f1, IntervalTrigger(minutes=5))
        live_f1_task.start()
        log.write("Live F1 begins")
        return
    if not live_f1_task.running:
        live_f1_task.start()
        log.write("Live F1 begins")