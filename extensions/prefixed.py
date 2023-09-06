import interactions
from interactions import Extension
from interactions.ext.prefixed_commands import prefixed_command, PrefixedContext

import util


def setup(bot): Prefixed(bot)


COLOUR = util.Colour.PREFIXED.value


class Prefixed(Extension):
    @prefixed_command()
    async def hello(self, ctx: PrefixedContext): await ctx.reply(embed=hello())

    @prefixed_command()
    async def hallo(self, ctx: PrefixedContext): await ctx.reply(embed=hello())

    @prefixed_command()
    async def moin(self, ctx: PrefixedContext): await ctx.reply(embed=hello())


def hello():
    embed = interactions.Embed(title="Hallo zurück!", color=COLOUR)
    embed.set_image(url=util.get_gif("hello"))
    return embed
