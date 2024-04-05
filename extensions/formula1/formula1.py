import fastf1
import interactions
from fastf1.core import DataNotLoadedError
from interactions import Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
from interactions.models import discord

import extensions.formula1._laps as laps
import extensions.formula1._no_group as no_group
import extensions.formula1._race_info as race_info
import extensions.formula1._standings as standings
import util
import extensions.formula1._live as live

""" Main file for the formula1 commands """

#  Inspiration and Similar:
#  https://docs.fastf1.dev/examples_gallery/ https://github.com/F1-Buddy/f1buddy-python/


SPORTS_CHANNEL_ID = util.SPORTS_CHANNEL_ID
COLOUR = util.Colour.FORMULA1.value

CURRENT_SEASON = util.CURRENT_F1_SEASON

COMMAND_LIMIT = 3  # Limit of consecutive calls in a short time (~60 calls per hour possible with a limit of 3)


def setup(bot): Formula1(bot)


'''
##################################################
LIVE PART
##################################################
'''


def get_current():
    """ Gets the current gp and session """
    return live.get_current()


def create_schedule():
    """ Creates a schedule for the Formula1 sessions """
    return live.create_schedule()


def auto_result(result_only: bool):
    """ Returns the result of the latest session and sets the current paras to it """
    return live.auto_result(result_only)


def auto_info():
    """ Returns some day-relevant F1 information """
    return live.f1_info()


def result(session):
    """ Returns the result of the session """
    gp, _ = get_current()
    return no_group.result(CURRENT_SEASON, gp, session)


'''
##################################################
COMMAND PART
##################################################
'''
command_calls = 0
limit_reached = False


def reduce_command_calls():
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


def get_current_and_check_input(year, gp, session):
    """ Checks if inputs are ok or gets latest session """
    temp_gp, temp_session = get_current()
    if gp == "": gp = temp_gp
    if session == "": session = temp_session
    # If only gp is given, session cause problems
    # If only session is given, try current_gp. If it fails, try the gp before that
    try:  # Try getting the session
        fastf1.get_session(year, gp, session)
        return gp, session
    except DataNotLoadedError:
        gp = temp_gp - 1
        # Try getting it again with gp before that
        fastf1.get_session(year, gp, session)
        return gp, session


def get_last_finished_gp():
    """ Gets the last gp with a finished race """
    gp, session = get_current()
    return gp if session == 5 else (gp - 1)


def year_slash_option(min_year):
    def wrapper(func):
        return slash_option(
            name="year",
            description="Jahr",
            required=False,
            opt_type=OptionType.INTEGER,
            min_value=min_year,
            max_value=2023
        )(func)

    return wrapper


def grandprix_slash_option():
    def wrapper(func):
        return slash_option(
            name="gp",
            description="Grand Prix",
            required=False,
            opt_type=OptionType.STRING
        )(func)

    return wrapper


def session_slash_option():
    def wrapper(func):
        return slash_option(
            name="session",
            description="Session",
            required=False,
            opt_type=OptionType.STRING,
            choices=[
                SlashCommandChoice(name="Rennen", value="R"),
                SlashCommandChoice(name="Qualifikation", value="Q"),
                SlashCommandChoice(name="Sprint", value="S"),
                SlashCommandChoice(name="Sprint Shootout", value="SS"),
                SlashCommandChoice(name="FP3 ", value="FP3"),
                SlashCommandChoice(name="FP2", value="FP2"),
                SlashCommandChoice(name="FP1", value="FP1")
            ]
        )(func)

    return wrapper


def driver_slash_option(number=1):
    """ Number: A number if more than one driver is needed in the command """

    def wrapper(func):
        return slash_option(
            name=f"driver_{number}",
            description=f"Fahrerkürzel des {number}. Fahrers",
            required=True,
            opt_type=OptionType.STRING,
            min_length=3,
            max_length=3
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
    await ctx.defer()
    try:
        result = func(*args)
        if isinstance(result, interactions.Embed): await ctx.send(embed=result)
        elif isinstance(result, discord.File): await ctx.send(file=result)
        else: await ctx.send(result)
    except DataNotLoadedError: await ctx.send(embed=util.get_error_embed("faulty_value"))
    return


class Formula1(Extension):
    """ Formula1 Commands"""

    ''' Base '''

    @slash_command(name="f1", description="Formel 1 Befehle")
    async def f1_function(self, ctx: SlashContext):
        await ctx.send("Formel 1, Baby")

    ''' ######################
    Commands without group
    ####################### '''

    @f1_function.subcommand(
        sub_cmd_name="result",
        sub_cmd_description="Ergebnis der Session (Standard: Zuletzt gefahrene Session)"
    )
    @year_slash_option(1950)
    @grandprix_slash_option()
    @session_slash_option()
    async def result_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, gp: str = "", session: str = ""):
        try: gp, session = get_current_and_check_input(year, gp, session)
        except DataNotLoadedError:
            await ctx.send(embed=util.get_error_embed("faulty_value"))
            return
        await command_function(ctx, no_group.result, year, gp, session)

    @f1_function.subcommand(
        sub_cmd_name="next",
        sub_cmd_description="Das nächstes Rennwochenende oder alle verbleibenden Rennen (Standard: nur nächstes)"
    )
    @slash_option(
        name="allnext",
        description="Alle?",
        opt_type=OptionType.BOOLEAN,
        required=False
    )
    async def next_function(self, ctx: SlashContext, allnext: bool = False):
        if allnext: await command_function(ctx, no_group.remaining_races)
        else: await command_function(ctx, no_group.next_race)

    ''' ######################
    Commands in LAPS group
    ####################### '''

    @f1_function.subcommand(
        group_name="laps",
        group_description="Alle Befehle, die mit einzelnen Runden zu tun haben",
        sub_cmd_name="overview",
        sub_cmd_description="Übersicht der schnellsten Runden der Session (Standard: Zuletzt gefahrene Session)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def laps_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, gp: str = "", session: str = ""):
        try: gp, session = get_current_and_check_input(year, gp, session)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.overview_fastest_laps, year, gp, session)

    @laps_function.subcommand(
        sub_cmd_name="compare",
        sub_cmd_description="Vergleicht die schnellsten Runden der Fahrer in der Session (Standard: Zuletzt gefahrene "
                            "Session)"
    )
    @driver_slash_option(1)
    @driver_slash_option(2)
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def compare_function(self, ctx: SlashContext, driver_1, driver_2,
                               year: int = CURRENT_SEASON, gp: str = "", session: str = ""):
        try: gp, session = get_current_and_check_input(year, gp, session)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.compare_laps, year, gp, session, driver_1.upper(), driver_2.upper())

    @laps_function.subcommand(
        sub_cmd_name="scatterplot",
        sub_cmd_description="Zeigt Scatterplot der Runden des Fahrers (Standard: Zuletzt gefahrene Session)"
    )
    @driver_slash_option()
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def scatterplot_function(self, ctx: SlashContext, driver_1,
                                   year: int = CURRENT_SEASON, gp: str = "", session: str = ""):
        try: gp, session = get_current_and_check_input(year, gp, session)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.scatterplot, year, gp, session, str.upper(driver_1))

    @laps_function.subcommand(
        sub_cmd_name="telemetry",
        sub_cmd_description="Zeigt Telemetriedaten der schnellsten Runden der Fahrer (Standard: Zuletzt gefahrene "
                            "Session)"
    )
    @driver_slash_option(1)
    @driver_slash_option(2)
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def telemetry_function(self, ctx: SlashContext, driver_1, driver_2,
                                 year: int = CURRENT_SEASON, gp: str = "", session: str = ""):
        try: gp, session = get_current_and_check_input(year, gp, session)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.telemetry, year, gp, session, driver_1.upper(), driver_2.upper())

    @laps_function.subcommand(
        sub_cmd_name="track_dominance",
        sub_cmd_description="Vergleicht Streckendominanz der Fahrer (Standard: Zuletzt gefahrene Session)"
    )
    @driver_slash_option(1)
    @driver_slash_option(2)
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def track_dominance_function(self, ctx: SlashContext, driver_1, driver_2,
                                       year: int = CURRENT_SEASON, gp: str = "", session: str = ""):
        try: gp, session = get_current_and_check_input(year, gp, session)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.track_dominance, year, gp, session, driver_1.upper(), driver_2.upper())

    ''' ######################
    Commands in RACEINFO group
    ####################### '''

    @f1_function.subcommand(
        group_name="raceinfo",
        group_description="Alle Befehle mit Informationen zum Rennen",
        sub_cmd_name="position",
        sub_cmd_description="Positionsveränderungen während des Rennens (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def raceinfo_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, gp: int = 0):
        if gp == 0: gp = get_last_finished_gp()
        await command_function(ctx, race_info.position_change, year, gp)

    @raceinfo_function.subcommand(
        sub_cmd_name="ltd",
        sub_cmd_description="Lap Time Distribution der ersten 10 Fahrer für das Rennen (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def ltd_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, gp: int = 0):
        if gp == 0: gp = get_last_finished_gp()
        await command_function(ctx, race_info.lap_time_distribution, year, gp)

    @raceinfo_function.subcommand(
        sub_cmd_name="tyre",
        sub_cmd_description="Reifenstrategieübersicht für das Rennen (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def tyre_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, gp: int = 0):
        if gp == 0: gp = get_last_finished_gp()
        await command_function(ctx, race_info.strategy, year, gp)

    ''' #######################
    Commands in STANDINGS group
    ####################### '''

    @f1_function.subcommand(
        group_name="standings",
        group_description="Alle Befehle für Informationen zu Standings",
        sub_cmd_name="table",
        sub_cmd_description="Rangliste der Saison (Standard: Derzeitige Fahrer-WM)"
    )
    @year_slash_option(1950)
    @slash_option(
        name="championship",
        description="Meisterschaftsart",
        required=False,
        opt_type=OptionType.BOOLEAN,
        choices=[
            SlashCommandChoice(name="Fahrer-WM", value=True),
            SlashCommandChoice(name="Konstrukteurs-WM", value=False)
        ]
    )
    async def standings_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, championship: bool = True):
        await command_function(ctx, standings.table, year, championship)

    @standings_function.subcommand(
        sub_cmd_name="average",
        sub_cmd_description="Durchschnittliche Position im Sessiontyp (Standard: Derzeitige Situation in den Rennen)"
    )
    @year_slash_option(1950)
    @slash_option(
        name="session",
        description="Session",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Rennen", value="R"),
            SlashCommandChoice(name="Qualifikation", value="Q"),
            SlashCommandChoice(name="Sprint", value="S")
        ]
    )
    async def average_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, session: str = "R"):
        await command_function(ctx, standings.average_position, year, session)

    @standings_function.subcommand(
        sub_cmd_name="h2h",
        sub_cmd_description="Head2Head-Vergleich im Sessiontyp (Standard: Derzeitige Situation in den Rennen)"
    )
    @year_slash_option(1950)
    @slash_option(
        name="session",
        description="Session",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Rennen", value="R"),
            SlashCommandChoice(name="Qualifikation", value="Q"),
            SlashCommandChoice(name="Sprint", value="S")
        ]
    )
    async def h2h_function(self, ctx: SlashContext, year: int = CURRENT_SEASON, session: str = "R"):
        await command_function(ctx, standings.h2h, year, session)

    @standings_function.subcommand(
        sub_cmd_name="heatmap",
        sub_cmd_description="Heatmap für die Positionen aller Fahrer in der Saison (Standard: Momentane Saison)"
    )
    @year_slash_option(1950)
    async def heatmap_function(self, ctx: SlashContext, year: int = CURRENT_SEASON):
        await command_function(ctx, standings.heatmap, year)

    @standings_function.subcommand(
        sub_cmd_name="winnable",
        sub_cmd_description="Für welchen Fahrer ist die Meisterschaft noch winnable?"
    )
    async def winnable_function(self, ctx: SlashContext):
        await command_function(ctx, standings.whocanwin())
