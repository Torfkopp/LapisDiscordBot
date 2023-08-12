from interactions import Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice

import util
from extensions.formula1 import _standings

""" Main method for the formula1 commands """


def setup(bot): Formula1(bot)


#  TODO automatic Result message

'''
##################################################
COMMAND PART
##################################################
'''

SPORTS_CHANNEL_ID = util.SPORTS_CHANNEL_ID
WRONG_CHANNEL_MESSAGE = util.WRONG_CHANNEL_MESSAGE
LIMIT_REACHED_MESSAGE = util.LIMIT_REACHED_MESSAGE

CURRENT_SEASON = util.CURRENT_F1_SEASON

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


def year_slash_option(min_year):
    def wrapper(func):
        return slash_option(
            name="year_option",
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
            name="gp_option",
            description="Grand Prix",
            required=False,
            opt_type=OptionType.STRING
        )(func)

    return wrapper


def session_slash_option():
    def wrapper(func):
        return slash_option(
            name="session_option",
            description="Session",
            required=False,
            opt_type=OptionType.STRING,
            choices=[
                SlashCommandChoice(name="Race", value="R"),
                SlashCommandChoice(name="Qualifying", value="Q"),
                SlashCommandChoice(name="Sprint", value="S"),
                SlashCommandChoice(name="Sprint Shootout", value="SS"),
                SlashCommandChoice(name="FP3", value="FP3"),
                SlashCommandChoice(name="FP2", value="FP2"),
                SlashCommandChoice(name="FP1", value="FP1")
            ]
        )(func)

    return wrapper


# TODO IMPROVE THE INPUTS COMMANDS (E.G. AUTOCOMPLETE)
class Formula1(Extension):
    @slash_command(name="f1_laps",
                   description="Vergleich aller schnellsten Runden, Streudiagramm, oder Rundenvergleich")
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    @slash_option(
        name="driver1_option",
        description="Erster Fahrer",
        required=False,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="driver2_option",
        description="Zweiter Fahrer",
        required=False,
        opt_type=OptionType.STRING
    )
    async def laps_function(self, ctx: SlashContext,
                            year_option: int = CURRENT_SEASON, gp_option: str = "", session_option: str = "race",
                            driver1_option: str = "", driver2_option: str = ""):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        if driver1_option == "" and driver2_option == "":
            await ctx.send(fastest_overview_fastest_laps(year_option, gp_option, session_option))
            return
        elif driver1_option == "" or driver2_option == "":
            await ctx.send(fastest_sp(year_option, gp_option, session_option,
                                      (driver1_option if driver1_option != "" else driver2_option)))
            return
        else:
            await ctx.send(fastest_compare_laps(year_option, gp_option, session_option, driver1_option, driver2_option))

    @slash_command(name="f1_raceinfo", description="Renninformationen")
    @slash_option(
        name="form_option",
        description="Informationsform",
        opt_type=OptionType.STRING,
        required=True,
        choices=[
            SlashCommandChoice(name="Strategie", value="S"),
            SlashCommandChoice(name="LapTimeDistribution", value="LTD"),
            SlashCommandChoice(name="PositionChange", value="PC")
        ]
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def raceinfo_function(self, ctx: SlashContext, form_option, year_option: int = CURRENT_SEASON,
                                gp_option: str = "", ):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        match form_option:
            case "S":
                await ctx.send(race_info_strategy(year_option, gp_option))
                return
            case "LTD":
                await ctx.send(race_info_ltd(year_option, gp_option))
                return
            case "PC":
                await ctx.send(race_info_pc(year_option, gp_option))
                return

    @slash_command(name="f1_result", description="Ergebnis der Session")
    @year_slash_option(1950)
    @grandprix_slash_option()
    @session_slash_option()
    async def result_function(self, ctx: SlashContext,
                              year_option: int = CURRENT_SEASON, gp_option: str = "", session_option: str = "race"):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(result(year_option, gp_option, session_option))

    @slash_command(name="f1_next", description="Nächstes Event")
    @slash_option(
        name="allnext_option",
        description="Alle?",
        opt_type=OptionType.BOOLEAN,
        required=False
    )
    async def next_function(self, ctx: SlashContext, allnext_option: bool = False):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(season_info(allnext_option))

    @slash_command(name="f1_standings", description="Formel 1 Standings")
    @slash_option(
        name="form_option",
        description="Darstellungsart",
        opt_type=OptionType.STRING,
        required=True,
        choices=[
            SlashCommandChoice(name="Durschnittliche Position", value="avg"),
            SlashCommandChoice(name="Head2Head", value="h2h"),
            SlashCommandChoice(name="Heatmap", value="heatmap"),
            SlashCommandChoice(name="Tabelle", value="table"),
            SlashCommandChoice(name="Still winnable", value="winnable")
        ],
    )
    @year_slash_option(1950)
    async def standings_function(self, ctx: SlashContext, form_option, year_option: int = CURRENT_SEASON):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        match form_option:
            case "avg":
                await ctx.defer()
                await ctx.send(_standings.avg(year_option))
                return
            case "h2h":
                await ctx.defer()
                await ctx.send(embed=_standings.h2h(year_option))
                return
            case "heatmap":
                await ctx.defer()
                await ctx.send(file=_standings.heatmap(year_option))
                return
            case "table":
                await ctx.send(_standings.table(year_option))
                return
            case "winnable":
                await ctx.send(embed=_standings.whocanwin())
                return


#  https://docs.fastf1.dev/examples_gallery/
#  https://github.com/F1-Buddy/f1buddy-python/
''' METHODS FOR FASTEST_LAP_COMPARE COMMAND '''


#  TODO FastestLapCompare(Year, GP, Session, driver1, driver2): With d1/d2: Overlaying, otherwise plot
def fastest_overview_fastest_laps(year, gp, session):
    """ Returns an overview of the fastest laps """
    return


def fastest_compare_laps(year, gp, session, driver1, driver2):
    """ Returns an overlaying of the two driver's fastest laps """
    return


def fastest_sp(year, gp, session, driver):
    """ Returns a scatter plot of the driver's laps during the session """
    return "Test"


''' METHODS FOR RACE_INFO COMMAND '''


#  TODO RaceInfo (Year, Grand Prix, Required Form| Standard: current):
#   Tyre Stategies, LapTimeDistribution, PositionChange, ScatterPlot
def race_info_strategy(year, gp):
    """ Returns the tyre strategies during the race """
    return "Test"


def race_info_ltd(year, gp):
    """ Returns the drivers' lap time distribution during the race """
    return "Test"


def race_info_pc(year, gp):
    """ Returns the place changes during the race"""
    return "Test"


''' METHODS FOR RESULTS COMMAND '''


#  TODO Results (Year, Grand Prix, Session): Results of Session
def result(year, gp, session):
    """ Returns the result of the specified session """
    return "Test"


''' METHODS FOR SEASON_INFO COMMAND '''


#  TODO season_info(year): normal = current
def season_info(all_next):
    """ Returns the seasons next event or all next event if all_next is true """
    return "Test"


''' METHODS FOR STANDINGS COMMAND '''


#  TODO Standings (Year, Form| Standard: current, normal):
#  Normal, Heatmap, Who Can still win Championship, H2H, Average Race Finish

