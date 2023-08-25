import random

import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext
)

""" File for all quoty commands """


def setup(bot): Quotes(bot)


class Quotes(Extension):
    @slash_command(name="advice", description="Erhalte einen zufälligen Ratschlag")
    @slash_option(
        name="theme_option",
        description="Angelsächsischer Term, der im Ratschlag enthalten sein soll (Random, wenn nix gefunden)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def advice_function(self, ctx: SlashContext, theme_option: str = ""):
        await ctx.send(get_advice(theme_option))

    '''
    @slash_command(name="anime_quote", description="Erhalte ein zufälliges Anime-Zitat")
    @slash_option(
        name="title_option",
        description="Name des Anime",
        required=False,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="char_option",
        description="Name des Charakters",
        required=False,
        opt_type=OptionType.STRING
    )
    async def anime_function(self, ctx: SlashContext, title_option: str = "", char_option: str= ""):
        await ctx.send(get_anime(title_option, char_option))'''


def get_advice(term):
    """ Returns a random advice or one fitting the theme """
    url = "https://api.adviceslip.com/advice"
    payload = ""
    rat = ""

    if term != "":
        url_theme = url + f"/search/{term}"
        response = requests.request("GET", url_theme, data=payload)
        print("Api-Call quotes: " + url)
        response = response.json()

        advices = response['slips']
        if len(advices) == 0: rat = ""
        elif len(advices) == 1: rat = advices[0]['advice']
        else: rat = advices[random.randint(0, len(advices) - 1)]['advice']
    if rat == "":
        response = requests.request("GET", url, data=payload)
        print("Api-Call quotes: " + url)
        response = response.json()
        rat = response['slip']['advice']

    return rat


def get_anime(title, char):
    """ Returns an anime quote. Character is more important than title """
    url = "https://animechan.xyz/api/random"
    if char != "": url += f"character?name={char}"
    elif title != "": url += f"anime?title={title}"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print("Api-Call quotes: " + url)
    response = response.json()

    result = "Anime: " + response['anime'] + "\n"
    result += "Character: " + response['character'] + "\n"
    result += "Quote: " + response['quote']

    return result
