import json
import random

import interactions
import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)

import util
from core import log

""" File for the insult commands """


def setup(bot): Insults(bot)


COLOUR = util.Colour.INSULTS.value


class Insults(Extension):
    @slash_command(name="insult", description="Erhalte eine zufällige Beleidigung")
    @slash_option(
        name="language",
        description="Sprache des Witzes",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Deutsch", value="de"),
            SlashCommandChoice(name="Ängelsächsisch", value="en"),
            SlashCommandChoice(name="Italienisch", value="it"),
            SlashCommandChoice(name="Spanisch", value="es"),
            SlashCommandChoice(name="Franzakisch", value="fr")]
    )
    async def insult_function(self, ctx: SlashContext, language: str = "en"):
        await ctx.send(embed=get_insult(language))

    @slash_command(name="yomomma", description="Erhalte eine zufällige Beschreibung deiner Mutter")
    async def yomomma_function(self, ctx: SlashContext):
        await ctx.send(embed=get_yomomma())


def get_insult(lang):
    """ Return an insult in the specified language """
    url = "https://evilinsult.com/generate_insult.php"
    querystring = {"lang": lang, "type": "json"}
    payload = ""

    try:
        log.write("Api-Call Insults: " + url)
        response = requests.request("GET", url, data=payload, params=querystring)
        response = response.json()
        insult = response['insult']
    except Exception:  # Very broad, but should be fine ¯\_(ツ)_/¯
        log.write("API DOWN")
        return get_insult_from_resources()

    if lang != "en" and response['comment'] != "": insult += f" (Translation: {response['comment']}"

    embed = interactions.Embed(title=insult, color=COLOUR)
    return util.uwuify_by_chance(embed)


def get_insult_from_resources():
    # Thanks to: https://gist.github.com/HBIDamian/7791dcbbf3f92e0ce252a9ca3bcb7800
    with open("resources/insult.json", encoding="utf-8") as f: insult = json.load(f)
    embed = interactions.Embed(title=random.choice(insult), color=COLOUR)
    return util.uwuify_by_chance(embed)


def get_yomomma():
    """ Gets a random yo mamma joke """
    # Thanks to: https://github.com/beanboi7/yomomma-apiv2/blob/master/jokes.json
    with open("resources/yomomma.json", encoding="utf-8") as f: yomomma = json.load(f)

    embed = interactions.Embed(title=random.choice(yomomma), color=COLOUR)
    return util.uwuify_by_chance(embed)
