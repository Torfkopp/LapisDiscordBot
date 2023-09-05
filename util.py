import datetime
import json
import random
from enum import Enum

import interactions
from interactions.models import discord

import uwuifier

# CHANNELS
with open("config.json") as f: lines = json.load(f)
TOKEN = lines['token']
SPORTS_CHANNEL_ID = lines['sport_channel_id']
LABAR_CHANNEL_ID = lines['labar_channel_id']
STAMMRUNDEN_CHANNEL_ID = lines['stammrunden_channel_id']

# Todo Make them cooler and gifs
WRONG_CHANNEL_MESSAGE = "Falscher Channel, Bro"
LIMIT_REACHED_MESSAGE = "Zu viele Commands, Bro"
FAULTY_VALUE_MESSAGE = "Deine Werte passen iwie nicht, Bro"

# COLOURS
class Colour(Enum):
    FOOTBALL = discord.Color.from_rgb(29, 144, 83)  # Werder Bremen Green
    FORMULA1 = discord.Color.from_rgb(255, 24, 1)  # Formula1 Red
    LOLESPORTS = discord.Color.from_rgb(200, 155, 60)  # League Gold

    ANIME = discord.BrandColors.FUCHSIA
    FREE_GAMES = discord.BrandColors.WHITE
    HANGMAN = discord.BrandColors.BLACK
    INSULTS = discord.MaterialColors.BROWN
    JOKES = discord.MaterialColors.YELLOW
    PREFIXED = discord.BrandColors.BLURPLE
    QUOTES = discord.FlatUIColors.ASBESTOS
    SECRET = discord.MaterialColors.DEEP_PURPLE
    TRIVIA = discord.MaterialColors.LIGHT_BLUE

    ERROR = discord.BrandColors.RED


# Other settings
CURRENT_F1_SEASON = datetime.datetime.now().year  # An F1 Season starts and ends within one year
CURRENT_FOOTBALL_SEASON = 2023  # 2023/2024 -> 2023

UWUCHANCE = 5  # D-De chance dat a commyand wesponse gets u-u-uwuified


def random_colour_generator():
    """ Generates a random colour that is distinguishable from black """
    while True:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        greyscale = r * 0.299 + g * 0.587 + b * 0.114  # NTSC Formula
        if greyscale > 10: break

    return f"#{r:02x}{g:02x}{b:02x}"


def get_gif(term: str):
    """ Returns a gif with the term
    Returns a standard gif, when the term is not found """
    with open("Resources/gifs.json") as g: gif_db = json.load(g)

    try: gifs = gif_db[term]
    except KeyError: return gif_db['standard']

    if isinstance(gifs, dict): return random.choice(list(gifs.values()))
    return gifs


def get_error_embed(term: str):
    embed = interactions.Embed()
    match term:
        case "error":
            embed.title = "Fehler aufgetreten"
            # embed.description = "Irgendwas ist irgendwo schiefgelaufen"
            # TODO verbessern
            embed.set_image(url=get_gif("error"))
        case _:
            embed.title = "Standard"
            embed.description = "Standard"
            embed.set_image(url=get_gif("standard"))

    return embed


def get_if_uwuify():
    """ Returns if you should uwuify"""
    return not random.randint(0, 100) < UWUCHANCE


def uwuify_by_chance(obj):
    """ UwUifies only by chance """
    if not random.randint(0, 100) < UWUCHANCE: return obj
    if isinstance(obj, interactions.Embed): return uwuify_embed(obj)
    return uwuifier.UwUify(obj, False, False)


def uwuify_embed(embed):
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
