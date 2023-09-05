import random

import interactions
import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)

import util
from strunt import secret

""" File for the joke commands """


def setup(bot): Jokes(bot)


COLOUR = util.Colour.JOKES.value


class Jokes(Extension):
    @slash_command(name="joke", description="Joke")
    async def joke_function(self, ctx: SlashContext): await ctx.send("Joke")

    @joke_function.subcommand(sub_cmd_name="dad_joke", sub_cmd_description="Erhalte einen zufälligen Dad Joke")
    @slash_option(
        name="theme_option",
        description="Thema des Witzes auf Angelsächsisch (Random, wenn nix gefunden)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def dad_joke_function(self, ctx: SlashContext, theme_option: str = ""):
        await ctx.send(embed=get_dad_joke(theme_option))

    @joke_function.subcommand(sub_cmd_name="joke", sub_cmd_description="Erhalte einen zufälligen Witz")
    @slash_option(
        name="theme_option",
        description="Thema des Witzes",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Verschiedenes", value="Miscellaneous"),
            SlashCommandChoice(name="Programmieren", value="Programming"),
            SlashCommandChoice(name="Dark", value="Dark"),
            SlashCommandChoice(name="Pun", value="Pun"),
            SlashCommandChoice(name="Spooky", value="Spooky"),
            SlashCommandChoice(name="Weihnachten", value="Christmas")
        ]
    )
    @slash_option(
        name="lang_option",
        description="Die Sprache des Witzes",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Deutsch", value="?lang=de"),
            SlashCommandChoice(name="Englisch", value="")
        ]
    )
    async def jokejoke_function(self, ctx: SlashContext, theme_option: str = "any", lang_option: str = "?lang=de"):
        await ctx.send(embed=get_joke(theme_option, lang_option))

    @joke_function.subcommand(sub_cmd_name="stammrunde",
                              sub_cmd_description="Erhalte einen zufälligen Stammrunden-Witz")
    async def norris_function(self, ctx: SlashContext):
        await ctx.send(embed=get_norris())


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
        try:
            response = response.json()
            jokes = response['results']
        except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")
        if len(jokes) == 0: joke = ""
        elif len(jokes) == 1: joke = jokes[0]['joke']
        else: joke = jokes[random.randint(0, len(jokes) - 1)]['joke']

    if joke == "":
        response = requests.request("GET", url, data=payload, headers=headers)
        print("Api-Call Jokes: " + url)

        try:
            joke = response.json()
            joke = joke["joke"]
        except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")

    embed = interactions.Embed(title=joke, color=COLOUR)

    return util.uwuify_by_chance(embed)


def get_joke(theme, lang):
    """ Returns a random joke considering the theme and language """
    url = f"https://v2.jokeapi.dev/joke/{theme}{lang}"
    payload = ""
    response = requests.request("GET", url, data=payload)
    print("Api-Call Jokes: " + url)
    try:
        response = response.json()
        joke = f"Category: {response['category']}\n"
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")
    if response['type'] == "single":
        joke += f"Joke: {response['joke']}"
    elif response['type'] == "twopart":
        joke += (f"Setup: {response['setup']}\n"
                 f"Delivery: ||{response['delivery']}||")
    else: joke += "I don't know how this could happen"

    embed = interactions.Embed(title=joke, color=COLOUR)

    return util.uwuify_by_chance(embed)


def get_norris():
    """ Returns a random Chuck Norris joke with Chuck's name replaced by owner's friend's names """
    name_list = secret.name_list
    url = "https://api.chucknorris.io/jokes/random"
    payload = ""
    response = requests.request("GET", url, data=payload)
    print("Api-Call Jokes: " + url)
    try:
        response = response.json()
        joke = response['value']
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")
    joke = joke.replace("Chuck Norris", random.choice(name_list))
    joke = joke.replace("' ", "'s ")

    embed = interactions.Embed(title=joke, color=COLOUR)

    return util.uwuify_by_chance(embed)
