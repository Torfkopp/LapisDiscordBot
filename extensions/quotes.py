import json
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
        name="theme",
        description="Angelsächsischer Term, der im Ratschlag enthalten sein soll (Random, wenn nix gefunden)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def advice_function(self, ctx: SlashContext, theme: str = ""):
        await ctx.send(embed=get_advice(theme))

    @slash_command(name="sparkasse", description="Erhalte eine Sparkassenweisheit")
    async def sparkasse_function(self, ctx: SlashContext):
        await ctx.send(embed=get_sparkasse())

    @slash_command(name="wisdom", description="Erhalte eine Weisheit", scopes=[1134856890669613210])
    @slash_option(
        name="term",
        description="Term(e, abgetrennt durch Komma), der/die im Quote enthalten sein soll (Random, wenn nix gefunden)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def wisdom_function(self, ctx: SlashContext, term: str = ""):
        embed, file = get_wisdom(term)
        await ctx.send(embed=embed, file=file)


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
        try:
            log.write("Api-Call quotes: " + url)
            response = requests.request("GET", url, data=payload)
            response = response.json()
            rat = response['slip']['advice']
        except (KeyError, requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
            log.write("API DOWN")
            return util.get_error_embed("api_down")

    embed = interactions.Embed(title=rat, color=COLOUR)

    return util.uwuify_by_chance(embed)


def get_sparkasse():
    """ Gets a sparkassen quote"""
    with open("resources/sparkasse.json", encoding="utf-8") as f: sparkasse = json.load(f)

    embed = interactions.Embed(title="Sparkassen Hänno sagt:", color=COLOUR)
    embed.set_thumbnail(url="https://www.horizont.net/news/media/34/Hand-of-Blood-Sparkasse-336635.jpeg")
    embed.description = random.choice(sparkasse)
    return util.uwuify_by_chance(embed)


def get_wisdom(search):
    """ Gets a wise quote (https://wolfgang-naeser-marburg.lima-city.de/htm/sponti.htm) """
    with open("resources/wisdom.txt", encoding="utf-8") as f: wisdom = f.read().splitlines()

    if search:
        terms = search.split(",")
        containing = [w for w in wisdom if all(t.lower().strip() in w.lower() for t in terms)]
        quote = random.choice(containing) if containing else random.choice(wisdom)
    else: quote = random.choice(wisdom)

    file = interactions.models.discord.File("lapis_pics/lapis2.jpg", "lapis2.jpg")
    embed = interactions.Embed(title="Lapis sagt:", color=COLOUR)
    embed.set_thumbnail(url="attachment://lapis2.jpg")
    embed.description = quote

    return embed, file
