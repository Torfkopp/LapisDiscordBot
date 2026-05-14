import datetime
from functools import partial

from interactions import Task, IntervalTrigger, DateTrigger

from core import log
from extensions import lol_patchnotes, reddit
from extensions import weather
from extensions.formula1 import formula1

import util
import secret


@log.safe_call
async def formula1_info(bot, now):
    """If it's Monday or Thursday and the corresponding message hasn't been sent, send a message with f1 info"""
    embed = formula1.auto_info()
    if embed is not None:
        if (now.weekday() == 0 and not util.message_sent("rawe_ceek")) or (
            now.weekday() == 3 and not util.message_sent("race_schedule")
        ):
            await bot.get_channel(util.SPORTS_CHANNEL_ID).send(embed=embed)


@log.safe_call
async def update_patchnotes(bot):
    """Updates the patchnotes if there are new ones and sends them to the channel"""
    embed = lol_patchnotes.update()
    if embed:
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed)


@log.safe_call
async def patchnotes(bot, now):
    """Check for new patchnotes and send them if they exist"""
    try:
        await update_patchnotes(bot)
        g = partial(update_patchnotes, bot)
        if now.weekday() == 1:
            for i in range(4):
                Task(g, DateTrigger(now.replace(hour=(20 + i), minute=20))).start()
        Task(g, IntervalTrigger(hours=8)).start()
    except Exception as e:
        log.error(e)


@log.safe_call
async def day_dependent(bot):
    """Send a message on certain days of the week"""
    if datetime.datetime.now().weekday() == 4 and not util.message_sent("friday_krabs"):
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(file="resources/congratssailer.mp4")
    elif datetime.datetime.now().weekday() == 0 and not util.message_sent("monday_krabs"):
        await bot.get_channel(util.LABAR_CHANNEL_ID).send(file="resources/risesailer.mp4")


@log.safe_call
async def daily_meme(bot):
    """Every day, send a meme until the bot is finished or dead"""
    sent_already, day_count = util.day_counter()
    if not sent_already:
        message = (
            f"Jeden Tag ein Meme senden bis ich fertig oder tot bin.\nTag {day_count}\n"
            + reddit.get_reddit_link("LeagueOfMemes")
        )
        await bot.get_channel(util.COMEDY_CHANNEL_ID).send(message)


@log.safe_call
async def temperature(bot, now):
    """If it's before 9 am, check if the sun is killing people and send a message if so"""
    if now.time() < datetime.time(hour=9):
        embed, file = weather.is_sun_killing(now)
        if embed:
            await bot.get_channel(util.LABAR_CHANNEL_ID).send(embed=embed, file=file)


async def daily_messages(bot):
    """Daily procedure"""
    log.write("Running daily procedure")
    
    now = datetime.datetime.now()
    await formula1_info(bot, now)
    await patchnotes(bot, now)

    await day_dependent(bot)
    await daily_meme(bot)
    await temperature(bot, now)

    await secret.main(bot)
