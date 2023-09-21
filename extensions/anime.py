import random

import interactions
import requests
from bs4 import BeautifulSoup
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)

import util
from core import log


def setup(bot): Anime(bot)


COLOUR = util.Colour.ANIME.value

THEME_OPTIONS = ["angrystare", "bleh", "blush", "celebrate", "clap", "confused",
                 "cool", "cry", "dance", "drool", "evillaugh", "facepalm", "happy", "headbang",
                 "laugh", "love", "mad", "nervous", "no", "nom", "nosebleed", "nyah",
                 "peek", "pout", "punch", "roll", "run", "sad", "scared", "shrug", "shy",
                 "sigh", "sip", "sleep", "slowclap", "smile", "smug", "sneeze", "sorry", "stare",
                 "surprised", "sweat", "thumbsup", "tired", "wave", "wink", "woah", "yawn", "yay",
                 "yes"]

ACTION_OPTIONS = {
    "airkiss": "luftküsst", "bite": "beißt", "brofist": "brofisted", "cheers": "prostet",
    "cuddle": "kuschelt mit", "handhold": "hält Händchen mit", "hug": "umarmt", "kiss": "küsst",
    "lick": "leckt", "nuzzle": "nuzzlet", "pat": "streichelt", "pinch": "kneift", "poke": "stubst",
    "punch": "schlägt", "slap": "ohrfeigt", "smack": "klatscht", "stop": "stoppt", "tickle": "kitzelt"
}


class Anime(Extension):
    @slash_command(name="anime", description="Anime Stuff")
    async def anime_function(self, ctx: SlashContext): await ctx.send("Anime")

    @anime_function.subcommand(sub_cmd_name="action", sub_cmd_description="Mach was Animeliches zu jemanden")
    @slash_option(
        name="action",
        description="Aktion",
        required=True,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in ACTION_OPTIONS]
    )
    @slash_option(
        name="user",
        description="Ziel",
        required=True,
        opt_type=OptionType.USER
    )
    async def action_function(self, ctx: SlashContext, action, user):
        await ctx.defer()
        ping = f"{ctx.author.mention} {ACTION_OPTIONS.get(action)} {user.mention}"
        embed = get_reaction(action)
        embed.title = None
        await ctx.send(ping, embed=embed)

    @anime_function.subcommand(sub_cmd_name="quote", sub_cmd_description="Zufälliges Anime Zitat")
    async def quote_function(self, ctx: SlashContext):
        await ctx.defer()
        await ctx.send(embed=get_quote())

    @anime_function.subcommand(sub_cmd_name="reaction", sub_cmd_description="Zufällige Anime Bewegtbildreaktion")
    @slash_option(
        name="theme_1",
        description="Thema (A-Q)",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in THEME_OPTIONS[:25]]
    )
    @slash_option(
        name="theme_2",
        description="Thema (R-Z)",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in THEME_OPTIONS[25:]]
    )
    async def reaction_function(self, ctx: SlashContext, theme_1: str = None, theme_2: str = None):
        theme_option = theme_1 or theme_2 or random.choice(THEME_OPTIONS)
        await ctx.defer()
        await ctx.send(embed=get_reaction(theme_option))


def get_quote():
    """ Gets a random anime quote """
    url = "https://kyoko.rei.my.id/api/quotes.php"
    payload = ""

    response = requests.request("GET", url, data=payload)
    log.write("Api-Call Anime: " + url)
    try:
        response = response.json()
        response = response['apiResult'][0]
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")

    character = response['character']
    result = "Anime: " + response['anime'] + "\n"
    result += "Character: " + character  # + "\n\n"
    # result += "Quote: " + response['english']
    quote = "**„" + response['english'] + "“**"

    url = f"https://myanimelist.net/search/all?cat=all&q={character}"
    response = requests.get(url)
    log.write("Site-Call: " + url)
    soup = BeautifulSoup(response.content, 'html.parser')
    character_url = soup.find('div', class_="picSurround di-tc thumb").find('a')['href']

    response = requests.get(character_url)
    log.write("Site-Call: " + character_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    picture_url = soup.find('td', class_="borderClass").find('img')['data-src']

    # noinspection PyTypeChecker
    embed = interactions.Embed(title="Anime Quote", description=result, color=COLOUR, thumbnail=picture_url)
    embed.add_field(value=quote, name="\u200b")

    return util.uwuify_by_chance(embed)


def get_reaction(theme):
    """ Gets a random anime reaction depending on the theme """
    url = f"https://api.otakugifs.xyz/gif?reaction={theme}"
    response = requests.request("GET", url, data="")
    log.write("Api-Call Anime: " + url)
    try: url = response.json()['url']
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")

    embed = interactions.Embed(title=f"{theme.title()} Reaction", color=COLOUR)
    embed.set_image(url=url)

    return embed
