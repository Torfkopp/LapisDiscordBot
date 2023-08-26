import datetime
import random

import interactions
from interactions.models import discord

import uwuifier

UWUCHANCE = 5  # D-De chance dat a commyand wesponse gets u-u-uwuified

FORMULA1_COLOUR = discord.Color.from_rgb(255, 24, 1)  # Formula1 Red
FOOTBALL_COLOUR = discord.Color.from_rgb(29, 144, 83)  # Werder Bremen Green
LOLESPORTS_COLOUR = discord.Color.from_rgb(200, 155, 60)  # League Gold
FREE_GAMES_COLOUR = discord.BrandColors.WHITE

SPORTS_CHANNEL_ID = open('./config.txt').readlines()[1]
LABAR_CHANNEL_ID = open('./config.txt').readlines()[2]

# Todo Make them cooler
WRONG_CHANNEL_MESSAGE = "Falscher Channel, Bro"
LIMIT_REACHED_MESSAGE = "Zu viele Commands, Bro"
FAULTY_VALUE_MESSAGE = "Deine Werte passen iwie nicht, Bro"

CURRENT_F1_SEASON = datetime.datetime.now().year  # An F1 Season starts and ends within one year
CURRENT_FOOTBALL_SEASON = 2023  # 2023/2024 -> 2023


def uwuify_by_chance(obj):
    """ UwUifies words only by chance """
    if not random.randint(0, 100) < UWUCHANCE: return obj
    if isinstance(obj, interactions.Embed): return _uwuify_embed(obj)
    return uwuifier.UwUify(obj, False, False)


def _uwuify_embed(embed):
    """ Uwuifies an embed """
    embed.title = uwuifier.UwUify(embed.title)
    for field in embed.fields:
        field.name = uwuifier.UwUify(field.name, False, False)
        field.value = uwuifier.UwUify(field.value, False, False)
    return embed


def germanise(msg):
    """ Fixes formatting errors concerning the German letters and makes string unbreakable"""
    char_map = {ord('Ã'): '', ord('¼'): 'ü', ord('¶'): 'ö', ord('¤'): 'ä', ord('Ÿ'): 'ß'}
    msg = msg.translate(char_map)
    msg = msg.replace(" ", "\u00A0")
    return msg
