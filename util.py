import random

import interactions
from interactions.models import discord

import uwuifier

UWUCHANCE = 5  # D-De chance dat a commyand wesponse gets u-u-uwuified
FORMULA1_COLOUR = discord.Color.from_rgb(255, 24, 1)  # Formula1 Red
FOOTBALL_COLOUR = discord.Color.from_rgb(29, 144, 83)  # Werder Bremen Green
SPORTS_CHANNEL_ID = open('./config.txt').readlines()[1]
WRONG_CHANNEL_MESSAGE = "Falscher Channel, Bro"
LIMIT_REACHED_MESSAGE = "Zu viele Commands, Bro"
CURRENT_F1_SEASON = 2023
CURRENT_FOOTBALL_SEASON = 2023
COMPETITION_LIST = ["2. Bundesliga", "League Cup", "Frauen-WM"]  # List of League interested in


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
    """ Fixes formatting errors concerning the German letters """
    char_map = {ord('Ã'): '', ord('¼'): 'ü', ord('¶'): 'ö', ord('¤'): 'ä', ord('Ÿ'): 'ß'}
    return msg.translate(char_map)
