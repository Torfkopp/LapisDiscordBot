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
    try:
        response = response.json()
        test = response[0]['id']  # tests if keys exist
    except KeyError or requests.exceptions.JSONDecodeError: return util.get_error_embed("api_down")
    embed = interactions.Embed(title="Free Games", color=util.Colour.FREE_GAMES.value)

    for i in range(min(len(response), 10)):
        game = response[i]
        embed.add_field(
            name=f"{game['platforms']} | {game['title']} | {game['worth']}",
            value=game['open_giveaway']
        )

    embed.set_footer(f"Für mehr: {url}")

    return embed
