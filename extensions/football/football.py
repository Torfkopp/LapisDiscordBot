import locale

from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)

import util
from extensions.football import _live, _commands

""" Main method for the football commands """


locale.setlocale(locale.LC_ALL, 'de_DE')  # Changes local to Deutsch for time display


# Sets up this extension
def setup(bot): Football(bot)


'''
##################################################
LIVE SCORE PART
##################################################
'''


def create_schedule():
    """ Returns Schedule based on the starting time of that day's games """
    return _live.create_schedule()


def get_live(content=""):
    """ Returns a list of embeds - one for every league - with an embed for every game of that league
        content -- old message's content, "" if no old message exists, otherwise the message's embeds """
    return _live.get_live(content)


def get_match_goals(match_id):
    """ Get the match's goalscorers """
    return _live.get_match_goals(match_id)


'''
##################################################
COMMAND PART
##################################################
'''

SPORTS_CHANNEL_ID = util.SPORTS_CHANNEL_ID

WRONG_CHANNEL_MESSAGE = util.WRONG_CHANNEL_MESSAGE
LIMIT_REACHED_MESSAGE = util.LIMIT_REACHED_MESSAGE

LEAGUE_CHOICES = [
    SlashCommandChoice(name="1. Bundesliga", value="bl1"),
    SlashCommandChoice(name="2. Bundesliga", value="bl2"),
    SlashCommandChoice(name="3. Bundesliga", value="bl3"),
    SlashCommandChoice(name="DFB Pokal", value="dfb")
]
CURRENT_SEASON = util.CURRENT_FOOTBALL_SEASON

COMMAND_LIMIT = 3

command_calls = 0
limit_reached = False


def reduce_command_calls():
    """ Used to reduce the command_calls counter """
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
            name="liga_option",
            description="Liga",
            required=False,
            opt_type=OptionType.STRING,
            choices=LEAGUE_CHOICES
        )(func)

    return wrapper


def season_slash_option():  # call with @season_option
    def wrapper(func):
        return slash_option(
            name="saison_option",
            description="Saison",
            required=False,
            opt_type=OptionType.INTEGER,
            min_value=2003,
            max_value=2023
        )(func)

    return wrapper


class Football(Extension):
    @slash_command(name="goalgetter", description="Gibt die Topscorer zurück")
    @league_slash_option()
    @season_slash_option()
    async def goalgetter_funtion(self, ctx: SlashContext, liga_option: str = LEAGUE_CHOICES[0].value,
                                 saison_option: int = CURRENT_SEASON):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(embed=_commands.goalgetter(liga_option, saison_option))

    @slash_command(name="matchday", description="Gibtn Spieltag")
    @league_slash_option()
    @season_slash_option()
    @slash_option(
        name="day_option",
        description="Spieltag",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1
    )
    async def matchday_function(self, ctx: SlashContext, liga_option: str = LEAGUE_CHOICES[0].value,
                                saison_option: int = CURRENT_SEASON,
                                day_option: int = 0):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(embed=_commands.matchday(liga_option, saison_option, day_option))

    @slash_command(name="matches", description="Spiele des Teams")
    @slash_option(
        name="team_option",
        description="Teamname",
        required=False,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="past_option",
        description="Von",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=50
    )
    @slash_option(
        name="future_option",
        description="bis",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=50
    )
    async def matches_function(self, ctx: SlashContext, team_option: str = "Werder Bremen", past_option: int = 2,
                               future_option: int = 2):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(embed=_commands.matches(team_option, past_option, future_option))

    @slash_command(name="table", description="Gibt ne Tabelle")
    @league_slash_option()
    @season_slash_option()
    async def table_function(self, ctx: SlashContext, liga_option: str = LEAGUE_CHOICES[0].value,
                             saison_option: int = CURRENT_SEASON):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            msg = WRONG_CHANNEL_MESSAGE
        elif limit_reached:
            msg = LIMIT_REACHED_MESSAGE
        else:
            msg = _commands.table(liga_option, saison_option)
            increment_command_calls()
        await ctx.send(msg)
