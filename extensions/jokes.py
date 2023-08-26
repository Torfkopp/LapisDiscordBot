import random

import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext
)

import util

""" File for the joke commands """


def setup(bot): Jokes(bot)


class Jokes(Extension):
    @slash_command(name="dad_joke", description="Gibt einen zufälligen Dad Joke zurück")
    @slash_option(
        name="theme_option",
        description="Thema des Witzes auf Angelsächsisch (Random, wenn nix gefunden)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def dad_joke_function(self, ctx: SlashContext, theme_option: str = ""):
        await ctx.send(get_dad_joke(theme_option))


def get_dad_joke(term):
    """ Returns a random dad joke or one fitting the theme """
    url = "https://icanhazdadjoke.com/"
    payload = ""
    headers = {"Accept": "application/json"}
    joke = ""

    if term != "":
        url_term = url + f"search?term={term}"
        response = requests.request("GET", url_term, data=payload, headers=headers)
        print("Api-Call Jokes: " + url)
        response = response.json()

        jokes = response['results']
        if len(jokes) == 0: joke = ""
        elif len(jokes) == 1: joke = jokes[0]['joke']
        else: joke = jokes[random.randint(0, len(jokes) - 1)]['joke']

    if joke == "":
        response = requests.request("GET", url, data=payload, headers=headers)
        print("Api-Call Jokes: " + url)

        joke = response.json()
        joke = joke["joke"]

    return util.uwuify_by_chance(joke)
