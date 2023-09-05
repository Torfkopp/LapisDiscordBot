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

    @prefixed_command(name="help")
    async def help(self, ctx: PrefixedContext): await ctx.reply(embed=help_())

    @prefixed_command()
    async def hilfe(self, ctx: PrefixedContext): await ctx.reply(embed=help_())


def hello():
    embed = interactions.Embed(title="Hallo zurück!", color=COLOUR)
    embed.set_image(url=util.get_gif("hello"))
    return embed


def help_():
    embed = interactions.Embed(title="Lapis hilft dir gerne! :)", color=COLOUR,
                               thumbnail="https://raw.githubusercontent.com/Torfkopp/LapisDiscordBot/master/resources/Lapis2.jpg")
    embed.description = ("Für eine Auflistung all meiner Befehle einfach / in den Chat und durchscrollen.\n"
                         "Ansonsten gibt es hier nicht viel aufzuführen;\n"
                         "Fragen einfach an meinen Erschaffer richten!\n\n"
                         "Viel Spaß!")

    return util.uwuify_by_chance(embed)
