import random
import time

import interactions
import requests
from bs4 import BeautifulSoup
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)

import util


def setup(bot): Anime(bot)


COLOUR = util.Colour.ANIME.value

THEME_OPTIONS = ["airkiss", "angrystare", "bite", "bleh", "blush", "brofist", "celebrate", "cheers", "clap", "confused",
                 "cool", "cry", "cuddle", "dance", "drool", "evillaugh", "facepalm", "handhold", "happy", "headbang",
                 "hug", "kiss", "laugh", "lick", "love", "mad", "nervous", "no", "nom", "nosebleed", "nuzzle", "nyah",
                 "pat", "peek", "pinch", "poke", "pout", "punch", "roll", "run", "sad", "scared", "shrug", "shy",
                 "sigh", "sip", "slap", "sleep", "slowclap", "smack", "smile", "smug", "sneeze", "sorry", "stare",
                 "stop", "surprised", "sweat", "thumbsup", "tickle", "tired", "wave", "wink", "woah", "yawn", "yay",
                 "yes"]


class Anime(Extension):
    @slash_command(name="anime", description="Anime Stuff")
    async def anime_function(self, ctx: SlashContext): await ctx.send("Anime")

    @anime_function.subcommand(sub_cmd_name="quote", sub_cmd_description="Zufälliges Anime Zitat")
    async def quote_function(self, ctx: SlashContext):
        await ctx.defer()
        await ctx.send(embed=get_quote())

    @anime_function.subcommand(sub_cmd_name="reaction", sub_cmd_description="Zufälliges Anime (Bewegt-)Reaktion")
    @slash_option(
        name="theme_option1",
        description="Thema (A-L)",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in THEME_OPTIONS[:25]]
    )
    @slash_option(
        name="theme_option2",
        description="Thema (M-Si)",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in THEME_OPTIONS[25:46]]
    )
    @slash_option(
        name="theme_option3",
        description="Thema (Sl-Z)",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in THEME_OPTIONS[46:]]
    )
    async def reaction_function(self, ctx: SlashContext,
                                theme_option1: str= None, theme_option2:str= None, theme_option3:str= None):
        theme_option = theme_option1 or theme_option2 or theme_option3 or random.choice(THEME_OPTIONS)
        await ctx.defer()
        await ctx.send(embed=get_reaction(theme_option))


def get_quote():
    """ Gets a random anime quote """
    url = "https://kyoko.rei.my.id/api/quotes.php"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print("Api-Call Anime: " + url)
    try:
        response = response.json()
        response = response['apiResult'][0]
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")

    character = response['character']
    result = "Anime: " + response['anime'] + "\n"
    result += "Character: " + character  # + "\n\n"
    # result += "Quote: " + response['english']
    quote = "„" + response['english'] + "“"

    url = f"https://myanimelist.net/search/all?cat=all&q={character}"
    response = requests.get(url)
    print("Site-Call: " + url)
    soup = BeautifulSoup(response.content, 'html.parser')
    character_url = soup.find('div', class_="picSurround di-tc thumb").find('a')['href']

    response = requests.get(character_url)
    print("Site-Call: " + character_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    picture_url = soup.find('td', class_="borderClass").find('img')['data-src']

    # noinspection PyTypeChecker
    embed = interactions.Embed(title="Anime Quote", description=result, color=COLOUR, thumbnail=picture_url)
    embed.add_field(name=quote, value="\u200b")

    return util.uwuify_by_chance(embed)


def get_reaction(theme):
    """ Gets a random anime reaction depending on the theme """
    url = f"https://api.otakugifs.xyz/gif?reaction={theme}"
    response = requests.request("GET", url, data="")
    print("Api-Call Anime: " + url)
    try: url = response.json()['url']
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")

    embed = interactions.Embed(title=f"{theme.title()} Reaction", color=COLOUR)
    embed.set_image(url=url)

    return embed
