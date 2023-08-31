import os
import random
import time

import interactions
import requests
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)

import util


def setup(bot): Anime(bot)


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
        await ctx.send(get_quote())

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
    response = response['apiResult'][0]

    result = "Anime: " + response['anime'] + "\n"
    result += "Character: " + response['character'] + "\n"
    result += "Quote: " + response['english']

    return util.uwuify_by_chance(result)


def get_image(theme):
    """ Gets a random image """
    url = f"https://kyoko.rei.my.id/api/{theme}.php"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print(response)
    print("Api-Call Anime: " + url)
    response = response.json()
    response = response['apiResult']

    image = response['url'][0]

    embed = interactions.Embed(title=theme.title())
    embed.set_image(url=image)
    embed.set_footer(image)
    time.sleep(5)  # Very slow loading gifs, so this hopefully helps with it
    return embed
