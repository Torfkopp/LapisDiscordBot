import interactions
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType
)

import util
from uwuifier import UwUify


def setup(bot): UwU(bot)


COLOUR = util.Colour.UWU.value


class UwU(Extension):

    @slash_command(name="uwu", description="UwU")
    @slash_option(
        name="text",
        description="UwU-Texy-Wexy",
        required=True,
        opt_type=OptionType.STRING
    )
    async def anime_function(self, ctx: SlashContext, text):
        await ctx.defer()
        await ctx.send(embed=get_uwu(text))


def get_uwu(text: str):
    embed = interactions.Embed(title="\u200b", color=COLOUR)
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Stylized_uwu_emoticon.svg/1280px-Stylized_uwu_emoticon.svg.png")
    embed.description = UwUify(text)
    return embed
