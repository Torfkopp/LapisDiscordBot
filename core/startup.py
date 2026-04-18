import datetime

from interactions import Task, IntervalTrigger, DateTrigger, TimeTrigger, listen

from core import log
from core.live import LIVE_MESSAGES
from core import live as live_mod
from core.activity import ActivityClass
from extensions import lolesport, lol_patchnotes, reddit
from extensions.football import football
from extensions.formula1 import formula1
from extensions import weather
import util


async def startup_football_scoring(now):
    football_schedule = football.create_schedule()
    log.write("Starting times of today's games: " + str(football_schedule))
    for start_time in football_schedule:
        if datetime.timedelta(minutes=0) < (now - start_time) < datetime.timedelta(minutes=90):
            await live_mod.start_live_scoring()
        task = Task(live_mod.start_live_scoring, DateTrigger(start_time))
        task.start()


async def startup_formula1_results(formula1_schedule, now):
    log.write("Today's formula1 sessions: " + str(formula1_schedule))
    if len(formula1_schedule) == 1:
        start_time = list(formula1_schedule)[0]
        if start_time > now:
            Task(live_mod.start_live_f1, DateTrigger(start_time)).start()
        elif datetime.timedelta(minutes=0) < (now - start_time) < datetime.timedelta(minutes=60):
            await live_mod.start_live_f1()
        else:
            await live_mod.formula1_result()
    elif len(formula1_schedule) > 1:
        start_times = list(formula1_schedule)
        if start_times[0] >= now:
            for start_time in start_times:
                if "Practice" in formula1_schedule.get(start_time):
                    Task(live_mod.formula1_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()
                else:
                    Task(live_mod.start_live_f1, DateTrigger(start_time)).start()

        elif start_times[1] > now or (start_times[1] + datetime.timedelta(hours=1)) > now:
            await live_mod.formula1_old_result(formula1_schedule.get(start_times[0]), start_times[0])
            start_time = start_times[1]
            if "Practice" in formula1_schedule.get(start_time):
                Task(live_mod.formula1_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()
            else:
                Task(live_mod.start_live_f1, DateTrigger(start_time)).start()

        else:
            await live_mod.formula1_old_result(formula1_schedule.get(start_times[0]), start_times[0])
            await live_mod.formula1_result()


async def startup_formula1_info(now):
    embed = formula1.auto_info()
    if embed is not None:
        if ((now.weekday() == 0 and not util.message_sent("rawe_ceek")) or
                (now.weekday() == 3 and not util.message_sent("race_schedule"))):
            from main import bot
            await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embed=embed)


async def startup_lolesports_results(now):
    league_schedule = lolesport.create_schedule()
    if len(league_schedule) > 0 and sorted(league_schedule)[-1] < now:
        await live_mod.live_league()
    log.write("Starting times of today's lol esport matches: " + str(league_schedule))
    for start_time in league_schedule:
        Task(live_mod.start_live_league, DateTrigger(start_time)).start()


async def startup_patchnotes(now):
    try:
        await update_patchnotes()
        if now.weekday() == 1:
            for i in range(4):
                Task(update_patchnotes, DateTrigger(now.replace(hour=(20 + i), minute=20))).start()
        Task(update_patchnotes, IntervalTrigger(hours=3.25)).start()
    except Exception as e:
        log.error(e)


async def update_patchnotes():
    embed = lol_patchnotes.update()
    if embed:
        from main import bot
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed)


async def startup_day_dependent():
    from main import bot
    if datetime.datetime.now().weekday() == 4 and not util.message_sent("friday_krabs"):
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(file="resources/congratssailer.mp4")
    elif datetime.datetime.now().weekday() == 0 and not util.message_sent("monday_krabs"):
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(file="resources/risesailer.mp4")


async def startup_daily_meme():
    from main import bot
    sent_already, day_count = util.day_counter()
    if not sent_already:
        message = (f"Jeden Tag ein Meme senden bis ich fertig oder tot bin.\nTag {day_count}\n"
                   + reddit.get_reddit_link("LeagueOfMemes"))
        await bot.get_channel(util.COMEDY_CHANNEL_ID).send(message)


async def startup_temperature(now):
    from main import bot
    if now.time() < datetime.time(hour=9):
        embed, file = weather.is_sun_killing(now)
        if embed:
            await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed, file=file)



