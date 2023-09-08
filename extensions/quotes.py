import random

import interactions
import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext
)

import util
from core import log

""" File for all quoty commands """


def setup(bot): Quotes(bot)


COLOUR = util.Colour.QUOTES.value


class Quotes(Extension):
    @slash_command(name="advice", description="Erhalte einen zufälligen Ratschlag")
    @slash_option(
        name="theme_option",
        description="Angelsächsischer Term, der im Ratschlag enthalten sein soll (Random, wenn nix gefunden)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def advice_function(self, ctx: SlashContext, theme_option: str = ""):
        await ctx.send(embed=get_advice(theme_option))


def get_advice(term):
    """ Returns a random advice or one fitting the theme """
    url = "https://api.adviceslip.com/advice"
    payload = ""
    rat = ""

    if term != "":
        url_theme = url + f"/search/{term}"
        response = requests.request("GET", url_theme, data=payload)
        log.write("Api-Call quotes: " + url_theme)
        try:
            response = response.json()
            advices = response['slips']
        except KeyError or requests.exceptions.JSONDecodeError: rat = ""
        else:
            if len(advices) == 1: rat = advices[0]['advice']
            else: rat = advices[random.randint(0, len(advices) - 1)]['advice']
    if rat == "":
        response = requests.request("GET", url, data=payload)
        log.write("Api-Call quotes: " + url)
        try:
            response = response.json()
            rat = response['slip']['advice']
        except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")

    embed = interactions.Embed(title=rat, color=COLOUR)

    return util.uwuify_by_chance(embed)
