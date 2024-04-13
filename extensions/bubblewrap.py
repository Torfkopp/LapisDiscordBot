from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType
)


def setup(bot): BubbleWrap(bot)


class BubbleWrap(Extension):
    @slash_command(name="bubblewrap", description="Mach Luftpolsterfolie kaputt!")
    @slash_option(name="amount", description="Anzahl an Blasen", required=False, opt_type=OptionType.INTEGER,
                  min_value=1, max_value=250)
    async def bubble_function(self, ctx: SlashContext, amount=80):
        await ctx.send(get_bubble_wraps(amount))


def get_bubble_wraps(amount):
    return "||pop|| " * amount
