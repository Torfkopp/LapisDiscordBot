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

THEME_OPTIONS = [
    "bite", "blush", "bonk", "bully",
    "cuddle", "cry", "dance", "glomp",
    "handhold", "happy", "highfive", "hug",
    "kick", "kill", "kiss",
    "lick", "nom", "pat", "poke",
    "slap", "smile", "smug",
    "wave", "wink", "yeet",
]


class Anime(Extension):
    @slash_command(name="anime", description="Anime Stuff")
    async def anime_function(self, ctx: SlashContext): await ctx.send("Anime")

    @anime_function.subcommand(sub_cmd_name="quote", sub_cmd_description="Zufälliges Anime Zitat")
    async def quote_function(self, ctx: SlashContext):
        await ctx.defer()
        await ctx.send(embed=get_quote())

    @anime_function.subcommand(sub_cmd_name="reaction", sub_cmd_description="Zufälliges Anime (Bewegt-)Reaktion")
    @slash_option(
        name="theme_option",
        description="Thema der Reaktion",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k.title(), value=k) for k in THEME_OPTIONS]
    )
    async def reaction_function(self, ctx: SlashContext, theme_option: str = ""):
        if theme_option == "": theme_option = random.choice(THEME_OPTIONS)
        await ctx.defer()
        await ctx.send(embed=get_image(theme_option))

    @anime_function.subcommand(sub_cmd_name="image", sub_cmd_description="Zufälliges Anime Bild")
    @slash_option(
        name="theme_option",
        description="Thema des Bilds",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name="Waifu", value="sfw"),
                 SlashCommandChoice(name="Awoo", value="awoo"),
                 SlashCommandChoice(name="Neko", value="sfwNeko"),
                 ]
    )
    async def image_function(self, ctx: SlashContext, theme_option: str = "sfw"):
        await ctx.defer()
        await ctx.send(embed=get_image(theme_option))


def get_quote():
    """ Gets a random anime quote """
    url = "https://kyoko.rei.my.id/api/quotes.php"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print("Api-Call Anime: " + url)
    response = response.json()
    try: response = response['apiResult'][0]
    except KeyError: return util.get_error_embed("api_down")

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


def get_image(theme):
    """ Gets a random image """
    url = f"https://kyoko.rei.my.id/api/{theme}.php"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print(response)
    print("Api-Call Anime: " + url)
    response = response.json()
    try: response = response['apiResult']
    except KeyError: return util.get_error_embed("api_down")

    image = response['url'][0]

    embed = interactions.Embed(title="Anime Image", description=theme.title(), color=COLOUR)
    embed.set_image(url=image)
    embed.set_footer(image)
    time.sleep(10)  # Very slow loading gifs, so this hopefully helps with it
    return embed
