import random

import interactions
import requests
from interactions import (
    Extension,
    slash_command,
    SlashContext,
    slash_option,
    OptionType,
    SlashCommandChoice,
)

import util
from core import log
from extensions.embed import get_embed_link


def setup(bot):
    Reddit(bot)


SUBBREDDITS = {
    "Anime Memes": "goodanimemes",
    "Anti Meme": "antimeme",
    "Birds aren't real": "BirdsArentReal",
    "Dank Memes": "dankmemes",
    "Football Circlejerk": "soccercirclejerk",
    "Formula Dank": "formuladank",
    "ich_iel": "ich_iel",
    "JoJo": "ShitPostCrusaders",
    "Kopiernudeln": "kopiernudeln",
    "LeagueOfMemes": "leagueofmemes",
    "OK Brudi Mongo": "okbrudimongo",
    "Pferde sind Kacke": "pferdesindkacke",
    "Scientific Shitpost": "ScienceShitposts",
    "Vexillology Circlejerk": "vexillologycirclejerk",
    "Wortwitzkasse": "wortwitzkasse",
    "You don't surf": "youdontsurf",
}


class Reddit(Extension):
    @slash_command(name="reddit", description="Zufälliges Reddit Meme")
    @slash_option(
        name="subreddit",
        description="Subreddit",
        required=True,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=name, value=value) for name, value in SUBBREDDITS.items()],
    )
    async def reddit_function(self, ctx: SlashContext, subreddit):
        await ctx.defer()
        link = get_reddit_link(subreddit)
        if link is None:
            await ctx.send(util.get_error_embed("api_down"))
            return
        await ctx.send(link)


def get_reddit_link(subreddit):
    def get_reddit_link(subreddit):
    url = f"https://meme-api.com/gimme/{subreddit}"

    try:
        log.write("API-Call Meme-Api (Reddit): " + url)
        response = requests.request("GET", url)
        response = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API may be down")
        return None

    title = response["title"]
    link = response["postLink"]
    picture_link = response["preview"][-1]

    return f"[`{title}`](<{link}>) | [Bild Link]({picture_link})"
