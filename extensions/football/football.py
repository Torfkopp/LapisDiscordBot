import interactions
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)

import extensions.football._commands as commands
import extensions.football._live as live
import util

""" Main file for the football commands """

SPORTS_CHANNEL_ID = util.SPORTS_CHANNEL_ID

CURRENT_SEASON = util.CURRENT_FOOTBALL_SEASON

COMMAND_LIMIT = 3  # Limit of consecutive calls in a short time (~60 calls per hour possible with a limit of 3)


# Sets up this extension
def setup(bot): Football(bot)


'''
##################################################
LIVE SCORE PART
##################################################
'''


def create_schedule():
    """ Returns Schedule based on the starting time of that day's games """
    return live.create_schedule()


def get_live():
    """ Returns a list of embeds - one for every league - with an embed for every game of that league """
    return live.get_live()


'''def get_match_goals(match_id):
    """ Get the match's goalscorers """
    return live.get_match_goals(match_id)'''

'''
##################################################
COMMAND PART
##################################################
'''

LEAGUE_CHOICES = [
    SlashCommandChoice(name="1. Bundesliga", value="bl1"),
    SlashCommandChoice(name="2. Bundesliga", value="bl2"),
    SlashCommandChoice(name="3. Bundesliga", value="bl3"),
    SlashCommandChoice(name="DFB Pokal", value="dfb")
]

command_calls = 0
limit_reached = False


def limit_command_calls():
    """ Used to reduce the command_calls counter
    Called regularly in main """
    global command_calls, limit_reached
    if command_calls > 0: command_calls -= 1
    if command_calls == 0: limit_reached = False


def increment_command_calls():
    """ Used to increment the command_calls counter """
    global command_calls, limit_reached
    command_calls += 1
    if command_calls > COMMAND_LIMIT: limit_reached = True


def league_slash_option():  # call with @league_option
    def wrapper(func):
        return slash_option(
            name="liga",
            description="Liga",
            required=False,
            opt_type=OptionType.STRING,
            choices=LEAGUE_CHOICES
        )(func)

    return wrapper


def season_slash_option():  # call with @season_option
    def wrapper(func):
        return slash_option(
            name="saison",
            description="Saison",
            required=False,
            opt_type=OptionType.INTEGER,
            min_value=2003,
            max_value=2023
        )(func)

    return wrapper


async def command_function(ctx, func, *args):
    """ Function for the commands """
    if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
        await ctx.send(embed=util.get_error_embed("wrong_channel"))
        return
    elif limit_reached:
        await ctx.send(embed=util.get_error_embed("limit_reached"))
        return
    increment_command_calls()
    result = func(*args)
    if isinstance(result, interactions.Embed): await ctx.send(embed=result)
    else: await ctx.send(result)


class Football(Extension):
    @slash_command(name="football", description="Football command base",
                   sub_cmd_name="goalgetter",
                   sub_cmd_description="Gibt die Topscorer der Liga zurück (Standard: Bundesliga")
    @league_slash_option()
    @season_slash_option()
    async def goalgetter_function(self, ctx: SlashContext, liga: str = LEAGUE_CHOICES[0].value,
                                  saison: int = CURRENT_SEASON):
        await command_function(ctx, commands.goalgetter, liga, saison)

    @goalgetter_function.subcommand(sub_cmd_name="matchday",
                                    sub_cmd_description="Gibtn Spieltag der Liga in der Saison "
                                                        "(Standard: Momentaner Bundesliga Spieltag")
    @league_slash_option()
    @season_slash_option()
    @slash_option(
        name="day",
        description="Spieltag",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1
    )
    async def matchday_function(self, ctx: SlashContext, liga: str = LEAGUE_CHOICES[0].value,
                                saison: int = CURRENT_SEASON, day: int = 0):
        await command_function(ctx, commands.matchday, liga, saison, day)

    @goalgetter_function.subcommand(sub_cmd_name="matches",
                                    sub_cmd_description="Alle Spiele des Teams von vor y und bis in x Wochen"
                                                        "(Standard: SVW, vor 2 und in 2 Wochen)")
    @slash_option(
        name="team",
        description="Teamname",
        required=False,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="past",
        description="Von",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=50
    )
    @slash_option(
        name="future",
        description="bis",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=50
    )
    async def matches_function(self, ctx: SlashContext, team: str = "Werder Bremen", past: int = 2,
                               future: int = 2):
        await command_function(ctx, commands.matches, team, past, future)

    @goalgetter_function.subcommand(sub_cmd_name="table",
                                    sub_cmd_description="Tabelle der Liga in der Saison (Standard: Jetzige Bundesliga)")
    @league_slash_option()
    @season_slash_option()
    async def table_function(self, ctx: SlashContext, liga: str = LEAGUE_CHOICES[0].value,
                             saison: int = CURRENT_SEASON):
        await command_function(ctx, commands.table, liga, saison)

    # @goalgetter_function.subcommand(
    #    sub_cmd_name="euro_where",
    #    sub_cmd_description="Sagt, wo die nächsten Spiele übertragen werden"
    # )
    # async def euro_where(self, ctx: SlashContext):
    #    await command_function(ctx, commands.euro_where)
