import datetime
import json
import random
from enum import Enum

import interactions
from interactions.models import discord

import uwuifier

# CHANNELS
with open("config.json") as f: config = json.load(f)
TOKEN = config['token']
SERVER_ID = config['server_id']
SPORTS_CHANNEL_ID = config['sport_channel_id']
LABAR_CHANNEL_ID = config['labar_channel_id']
STAMMRUNDEN_CHANNEL_ID = config['stammrunden_channel_id']
MODERATOREN_CHANNEL_ID = config['moderatoren_channel_id']
COMEDY_CHANNEL_ID = config['comedy_channel_id']
LOGBUCH_ID = config['logbuch']
AUTHOR_ID = config['bot_author_id']
SECOND_VERSUS_ID = config['second_versus_id']
WEATHER_KEY = config['weather_key']


# COLOURS
class Colour(Enum):
    FOOTBALL = discord.Color.from_rgb(29, 144, 83)  # Werder Bremen Green
    FORMULA1 = discord.Color.from_rgb(255, 24, 1)  # Formula1 Red
    LOLESPORTS = discord.Color.from_rgb(200, 155, 60)  # League Gold

    ANIME = discord.BrandColors.FUCHSIA
    FREE_GAMES = discord.BrandColors.WHITE
    HANGMAN = discord.BrandColors.BLACK
    HELP = discord.BrandColors.BLURPLE
    INSULTS = discord.MaterialColors.BROWN
    JOKES = discord.MaterialColors.YELLOW
    KARMA = discord.FlatUIColors.WETASPHALT
    MODMAIL = discord.MaterialColors.GREY
    POLL = discord.MaterialColors.AMBER
    PREFIXED = discord.BrandColors.BLURPLE
    QUOTES = discord.FlatUIColors.ASBESTOS
    SECRET = discord.MaterialColors.DEEP_PURPLE
    TIERLIST = discord.FlatUIColors.SILVER
    TRIVIA = discord.MaterialColors.LIGHT_BLUE
    UWU = discord.MaterialColors.PINK
    VERSUS = discord.MaterialColors.DEEP_ORANGE
    WEATHER = discord.MaterialColors.TEAL

    ERROR = discord.BrandColors.RED


# Other settings
CURRENT_F1_SEASON = now.year if (now := datetime.datetime.now()).month > 1 else now.year - 1  # F1 Season end of Feb
CURRENT_FOOTBALL_SEASON = now.year if now.month > 7 else now.year - 1  # 2023/2024 -> 2023

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
    with open("resources/gifs.json") as g: gif_db = json.load(g)

    try: gifs = gif_db[term]
    except KeyError: return gif_db['standard']

    if isinstance(gifs, dict): return random.choice(list(gifs.values()))
    return gifs


def get_error_embed(term: str, add_text: str | list[str] = ""):
    """ Gets an error embed
    :parameter "error", "wrong_channel", "limit_reached", "faulty_value", "api_down", "too_big", "custom"
    """
    embed = interactions.Embed(color=Colour.ERROR.value)
    match term:
        case "error":
            embed.title = "Fehler aufgetreten"
            embed.description = "Irgendwas ist irgendwo schiefgelaufen. Gomenasorry! (≧﹏ ≦)"
            embed.set_image(url=get_gif(term))
        case "wrong_channel":
            embed.title = "Falscher Channel"
            embed.description = ("Die Antwort auf diesen Befehl kann ich dir leider "
                                 "nur in dem passenden Channel geben! \n"
                                 "Bitte versuche es dort erneut. ^_-")
            embed.set_image(url=get_gif(term))
        case "limit_reached":
            embed.title = "Zu viele Anfragen"
            embed.description = ("Die angefragte API wurde leider in kürzester Zeit mit "
                                 "zu vielen Anfragen bombadiert （＞人＜；）, "
                                 "bitte warte ein paar Minuten, bis sie sich wieder erholt hat.")
            embed.set_image(url=get_gif(term))
        case "faulty_value":
            embed.title = "Fehlerhafte Werte"
            embed.description = ("Deine eingegeben Werte stehen nicht in meiner Liste <(＿　＿)>. "
                                 "Sicher, dass es die richtigen sind?")
            embed.set_image(url=get_gif(term))
        case "api_down":
            embed.title = "API down"
            embed.description = "Die angefragte API ist momentan down und ich kann nix dagegen tun. （；´д｀）ゞ"
            embed.set_image(url=get_gif(term))
        case "too_big":
            embed.title = "Too big"
            embed.description = f"Das Video oder Datei ist zu groß (´。＿。｀){add_text}"
            embed.set_image(url=get_gif(term))
        case "custom":
            embed.title = add_text[0]
            embed.description = add_text[1]
            embed.set_image(url=get_gif(add_text[2]))
        case _:
            embed.title = "Öhm"
            embed.description = "Ähm"
            embed.set_image(url=get_gif("standard"))

    return uwuify_by_chance(embed)


def message_sent(message: str):
    """ Returns whether the message was already sent, and if it wasn't, sets the tracker to true
    :param 'rawe_ceek', 'race_schedule', 'friday_krabs', 'monday_krabs', or 'temperature' """
    with open("strunt/message_tracker.json", "r") as message_tracker: trackers = json.load(message_tracker)
    if trackers[message]: return True
    else:
        trackers[message] = True
        with open("strunt/message_tracker.json", "w") as message_tracker: json.dump(trackers, message_tracker)
        return False


def reset_message_tracker():
    """ Resets the message trackers"""
    with open("strunt/message_tracker.json", "r") as message_tracker: trackers = json.load(message_tracker)
    for tracker in trackers: trackers[tracker] = False
    with open("strunt/message_tracker.json", "w") as message_tracker: json.dump(trackers, message_tracker)
    return


def day_counter():
    """ Returns whether it was already updated and the day counter (0 when it was already updated)
    and increases the day count by one, as well as setting today as the last_updated """
    with open("strunt/day_counter.json", "r") as dc: counter_file = json.load(dc)
    today = datetime.datetime.now().date()
    if today == datetime.date.fromisoformat(counter_file['last_updated']): return True, 0
    counter_file['last_updated'] = str(today)
    counter_file['day_counter'] += 1
    with open("strunt/day_counter.json", "w") as dc: json.dump(counter_file, dc)
    return False, counter_file['day_counter']


def get_if_uwuify():
    """ Returns if you should uwuify"""
    return random.randint(0, 100) < UWUCHANCE


def uwuify_by_chance(obj):
    """ UwUifies only by chance """
    if not random.randint(0, 100) < UWUCHANCE: return obj
    if isinstance(obj, interactions.Embed): return uwuify_embed(obj)
    return uwuifier.UwUify(obj, False, False)


def uwuify_embed(embed):
    """ Uwuifies an embed """
    embed.title = uwuifier.UwUify(embed.title)
    if embed.description is not None: embed.description = uwuifier.UwUify(embed.description)
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
