import interactions
import requests
from interactions import (
    Extension, slash_command, SlashContext
)

import util


def setup(bot): FreeGames(bot)


class FreeGames(Extension):
    @slash_command(name="free_games", description="Erhalte momentan kostenlos erhaltbare PC-Spiele")
    async def free_games_function(self, ctx: SlashContext):
        await ctx.send(embed=get_giveaways())


def get_giveaways():
    url = "https://www.gamerpower.com/api/giveaways?platform=pc&type=game&sort-by=value"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print("Api-Call Freegames: " + url)
    response = response.json()

    embed = interactions.Embed(title="Free Games", color=util.FREE_GAMES_COLOUR)

    for i in range(10):
        game = response[i]
        embed.add_field(
            name=f"{game['platforms']} | {game['title']} | {game['worth']}",
            value=game['open_giveaway']
        )

    embed.set_footer(f"Für mehr: {url}")

    return embed
