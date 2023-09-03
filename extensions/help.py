import interactions
from interactions import Extension, slash_command, SlashContext


def setup(bot): Help(bot)


class Help(Extension):
    @slash_command(name="help", description="Hilft dir", scopes=[1134856890669613210])
    async def help_function(self, ctx: SlashContext):
        await ctx.send(embed=get_help())


def get_help():
    # TODO hier ne Help/ Beschreibung
    embed = interactions.Embed(title="Help")
    embed.description = "Hi, ich bin Lapis"
    embed.add_field(name="", value="")
    return embed
