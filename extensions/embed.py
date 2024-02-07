import json

import requests
from bs4 import BeautifulSoup
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType
)

from core import log


def setup(bot): Embed(bot)


class Embed(Extension):
    @slash_command(name="embed", description="Embedde deinen Link")
    @slash_option(
        name="link",
        description="Link",
        required=True,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="alt",
        description="Alternativer Embedder",
        required=False,
        opt_type=OptionType.BOOLEAN,

    )
    async def embed_function(self, ctx: SlashContext, link, alt=False):
        await ctx.send(get_embed_link(link, alt))


def get_embed_link(link, alt):
    """ Returns the link in a for discord embedable format """
    if "tiktok." in link: link = link.replace("tiktok.com", "vxtiktok.com")
    elif "instagram." in link:
        if alt: link = link.replace("instagram.com", "ddinstagram.com")
        else: link = link.replace("instagram.com", "instagramez.com")
    elif "x." in link or "twitter." in link: link = link.replace("x.com", "vxtwitter.com")
    elif "reddit." in link:
        log.write("Site-Call: " + link)
        original_link = link
        try:
            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            a = json.loads(soup.find('shreddit-player')['packaged-media-json'])
            link = a['playbackMp4s']['permutations'][0]['source']['url']
        except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError): log.write("SITE DOWN")
        except requests.exceptions.MissingSchema: log.write("Invalid URL")
        link = f"[Reddit Post-Link](<{original_link}>)\n[Video Link]({link})"

    return link
