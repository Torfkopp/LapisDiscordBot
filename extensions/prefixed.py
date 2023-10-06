import subprocess

import interactions
from interactions import Extension
from interactions.ext.prefixed_commands import prefixed_command, PrefixedContext
from interactions.models import discord

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

    @prefixed_command()
    async def Hello(self, ctx: PrefixedContext): await ctx.reply(embed=hello())

    @prefixed_command()
    async def Hallo(self, ctx: PrefixedContext): await ctx.reply(embed=hello())

    @prefixed_command()
    async def Moin(self, ctx: PrefixedContext): await ctx.reply(embed=hello())

    @prefixed_command()
    async def goodbye(self, ctx: PrefixedContext):
        """ Shuts down the bot"""
        if ctx.author_id not in self.bot.owner_ids: return
        embed = interactions.Embed(title="Auf Wiedersehen!", color=COLOUR)
        embed.set_image(url=util.get_gif("goodbye"))

        await self.bot.change_presence(status=discord.Status.DND,
                                       activity=discord.activity.Activity.create(
                                           name="zu, dass sie herunterfährt",
                                           type=discord.activity.ActivityType.WATCHING))

        await ctx.send(embed=embed)
        await self.bot.stop()

    @prefixed_command()
    async def update(self, ctx: PrefixedContext):
        """ Function to update the bot remotely;
        shuts down the bot and calls a script that pulls the git changes and restarts the bot """
        if ctx.author_id not in self.bot.owner_ids: return
        embed = interactions.Embed(title="UPGRADE!", color=COLOUR)
        embed.set_image(url=util.get_gif("update"))
        await self.bot.change_presence(status=discord.Status.DND,
                                       activity=discord.activity.Activity.create(
                                           name="Updates auf",
                                           type=discord.activity.ActivityType.GAME))
        await ctx.send(embed=embed)
        await self.bot.stop()
        subprocess.call(["bash", "./strunt/update.sh"])  # Adapt to os


def hello():
    embed = interactions.Embed(title="Hallo zurück!", color=COLOUR)
    embed.set_image(url=util.get_gif("hello"))
    return embed
