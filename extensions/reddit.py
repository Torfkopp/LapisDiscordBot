import random

import interactions
import requests
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)

import util
from core import log
from extensions.embed import get_embed_link


def setup(bot): Reddit(bot)


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
        choices=[SlashCommandChoice(name=name, value=value) for name, value in SUBBREDDITS.items()]
    )
    async def reddit_function(self, ctx: SlashContext, subreddit):
        await ctx.defer()
        link = get_reddit_link(subreddit)
        if link is None:
            await ctx.send(util.get_error_embed("api_down"))
            return
        await ctx.send(link)


def get_reddit_link(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}.json"
    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "TE": "trailers"
    }

    try:
        log.write("API Call Reddit: " + url)
        response = requests.request("GET", url, data=payload, headers=headers)
        response = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API may be down")
        return None

    data = response['data']['children']
    number = random.randrange(len(data))
    post = data[number]['data']
    loop_prevent = 0
    while post['distinguished'] and loop_prevent < len(data):
        loop_prevent += 1
        number = random.randrange(len(data))
        post = data[number]['data']

    link, is_video = f"https://www.reddit.com{post['permalink']}", post['is_video']
    if is_video:
        link = get_embed_link(link, False)
        return link if not isinstance(link, interactions.Embed) else get_reddit_link(subreddit)
    return f"[`{post['title']}`](<{link}>) | [Bild Link]({post['url']})"
