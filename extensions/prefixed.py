import interactions
from interactions import Extension
from interactions.ext.prefixed_commands import prefixed_command, PrefixedContext


def setup(bot): Prefixed(bot)


COLOUR = util.Colour.PREFIXED.value


class Prefixed(Extension):
    @prefixed_command(name="hello")
    async def hello_function(self, ctx: PrefixedContext):
        await ctx.reply(embed=answers())


def answers():
    #  TODO hier Krams
    gif = "https://media.giphy.com/media/s1tAtvJLIYiVWNaCqy/giphy-downsized-large.gif"
    text = "Gomenasorry, something wrong"
    embed = interactions.Embed(title=text)
    embed.set_image(url=gif)
    return embed
