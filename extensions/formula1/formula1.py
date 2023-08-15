import datetime
import random

import fastf1
import interactions
import pytz
from fastf1.core import DataNotLoadedError
from interactions import Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice

import util
from extensions.formula1 import _standings, _race_info, _laps, _no_group

""" Main method for the formula1 commands """

#  Inspiration and Similar:
#  https://docs.fastf1.dev/examples_gallery/ https://github.com/F1-Buddy/f1buddy-python/


SPORTS_CHANNEL_ID = util.SPORTS_CHANNEL_ID
WRONG_CHANNEL_MESSAGE = util.WRONG_CHANNEL_MESSAGE
LIMIT_REACHED_MESSAGE = util.LIMIT_REACHED_MESSAGE
FAULTY_VALUE_MESSAGE = util.FAULTY_VALUE_MESSAGE
COLOUR = util.FORMULA1_COLOUR

CURRENT_SEASON = util.CURRENT_F1_SEASON

COMMAND_LIMIT = 3


def setup(bot): Formula1(bot)


'''
##################################################
COMMAND PART
##################################################
'''

# The last finished session and its Grand Prix
global current_gp, current_session


def create_schedule():
    """ Creates a schedule for the Formula1 sessions """
    start_times = set()
    embed = ""
    date_today = datetime.datetime.today()

    event_schedule = fastf1.get_events_remaining()
    next_event = event_schedule.iloc[0]

    session_list = [next_event['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session2Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session3Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session4Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)]

    # When it's monday on a race week, send bad meme
    if (date_today.weekday() == 0) and ((session_list[1] - date_today).days < 7):
        embed = interactions.Embed(title="Es ist Rawe Ceek!", color=COLOUR)
        rand_numb = random.randint(0, 100)
        if 0 < rand_numb < 16:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/084/695/e13.jpg"
        elif 17 < rand_numb < 33:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/085/358/310.jpg"
        elif 34 < rand_numb < 50:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/085/351/0be.jpg"
        elif 51 < rand_numb < 67:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/085/357/38a.jpg"
        elif 68 < rand_numb < 84:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/085/361/7bd.jpg"
        elif 65 < rand_numb < 100:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/085/360/27f.jpg"
        else:
            image_url = "https://i.kym-cdn.com/photos/images/original/002/085/367/32f.jpg"
        embed.set_image(url=image_url)

    # On friday of every race weekend, send the schedule to the channel
    if (date_today.weekday() == 4) and ((session_list[1] - date_today).days == 0): embed = _no_group.next_race()

    # Set current gp and session to the last race
    global current_gp, current_session
    current_gp = next_event['RoundNumber'] - 1
    current_session = 5

    latest_finished_session = 5
    for i in range(0, len(session_list)):
        session = session_list[i]  # A session should be finished 2 hours after the start
        if session.date() == date_today.date(): start_times.add(session + datetime.timedelta(hours=2))
        if session >= (date_today + datetime.timedelta(hours=2)): latest_finished_session = i + 1

    # If a session of the 'next event' has finished,
    # set the next_event as current_gp and the finished session as current_session
    if latest_finished_session < 5:
        current_gp = next_event['RoundNumber']
        current_session = latest_finished_session

    return start_times, embed


def auto_result():
    """ Returns the result of the latest session and sets the current paras to it """
    global current_gp, current_session
    result_gp, result_session = current_gp, (current_session + 1)

    if result_session > 5:
        result_gp += 1
        result_session = 1

    try:
        result_string = _no_group.result(CURRENT_SEASON, result_gp, result_session)
        current_gp = result_gp
        current_session = result_session
    except DataNotLoadedError: result_string = ""

    return util.uwuify_by_chance(result_string)


'''
##################################################
COMMAND PART
##################################################
'''
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


async def check_if_restricted(ctx):
    """ Checks if the command is restricted (returns True) due to limit or wrong channel
        or good to go (False)"""
    if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
        await ctx.send(WRONG_CHANNEL_MESSAGE)
        return True
    elif limit_reached:
        await ctx.send(LIMIT_REACHED_MESSAGE)
        return True

    increment_command_calls()
    return False


def session_get_current(year, gp, session):
    """ Checks if sessions are ok or gets latest session """
    temp_gp, temp_session = current_gp, current_session
    if gp == "": gp = temp_gp
    if session == "": session = temp_session

    # If only gp is given, session cause problems
    # If only session is given, try current_gp. If it fails, try the gp before that
    try:  # Try getting the session
        session = fastf1.get_session(year, gp, session)
        return gp, session
    except DataNotLoadedError:
        gp = temp_gp - 1
        # Try getting it again with gp before that
        session = fastf1.get_session(year, gp, session)
        return gp, session


def get_last_finished_gp():
    """ Gets the last gp with a finished race """
    return current_gp if current_session == 5 else (current_gp - 1)


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


def session_slash_option(all_sessions):
    def wrapper(func):
        choices = [
            SlashCommandChoice(name="Rennen", value="R"),
            SlashCommandChoice(name="Qualifikation", value="Q"),
            SlashCommandChoice(name="Sprint", value="S"),

        ]
        if all_sessions:
            choices.append([
                SlashCommandChoice(name="Sprint Shootout", value="SS"),
                SlashCommandChoice(name="FP3 ", value="FP3"),
                SlashCommandChoice(name="FP2", value="FP2"),
                SlashCommandChoice(name="FP1", value="FP1")])

        return slash_option(
            name="session_option",
            description="Session",
            required=False,
            opt_type=OptionType.STRING,
            choices=choices
        )(func)

    return wrapper


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
    @session_slash_option(True)
    async def result_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON,
                              gp_option: int = current_gp, session_option: int = current_session):
        if check_if_restricted(ctx): return
        try: await ctx.send(_no_group.result(year_option, gp_option, session_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @f1_function.subcommand(
        sub_cmd_name="next",
        sub_cmd_description="Das nächstes Event oder alle verbleibenden Rennen (Standard: nur nächstes)"
    )
    @slash_option(
        name="allnext_option",
        description="Alle?",
        opt_type=OptionType.BOOLEAN,
        required=False
    )
    async def next_function(self, ctx: SlashContext, allnext_option: bool = False):
        if check_if_restricted(ctx): return
        if allnext_option: await ctx.send(_no_group.remaining_races())
        else: await ctx.send(embed=_no_group.next_race())

    ''' ######################
    Commands in LAPS group
    ####################### '''

    # TODO Track Dominance https://github.com/F1-Buddy/f1buddy-python/blob/main/images/trackdominance.png
    #                      https://github.com/F1-Buddy/f1buddy-python/blob/main/cogs/speed.py
    # TODO Telemetry https://github.com/F1-Buddy/f1buddy-python/blob/main/images/telemetry.png
    #                https://github.com/F1-Buddy/f1buddy-python/blob/main/cogs/telemetry.py
    @f1_function.subcommand(
        group_name="laps",
        group_description="Alle Befehle, die mit einzelnen Runden zu tun haben",
        sub_cmd_name="overview",
        sub_cmd_description="Übersicht der schnellsten Runden der Session (Standard: zuletzt gefahrene Session)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option(True)
    async def laps_function(self, ctx: SlashContext,
                            year_option: int = CURRENT_SEASON, gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = session_get_current(year_option, gp_option, session_option)
        except DataNotLoadedError:
            await ctx.send(FAULTY_VALUE_MESSAGE)
            return
        if check_if_restricted(ctx): return
        await ctx.defer()
        await ctx.send(file=_laps.overview_fastest_laps(year_option, gp_option, session_option))

    @laps_function.subcommand(
        sub_cmd_name="compare",
        sub_cmd_description="Vergleiche die schnellste Runde der beiden Fahrer in der Session miteinander "
                            "(Standard: Zuletzt gefahrene Session)"
    )
    @slash_option(
        name="driver1_option",
        description="Erster Fahrer (Kürzel)",
        required=True,
        opt_type=OptionType.STRING,
        min_length=3,
        max_length=3
    )
    @slash_option(
        name="driver2_option",
        description="Zweiter Fahrer (Kürzel)",
        required=True,
        opt_type=OptionType.STRING,
        min_length=3,
        max_length=3
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option(True)
    async def compare_function(self, ctx: SlashContext, driver1_option, driver2_option,
                               year_option: int = CURRENT_SEASON, gp_option: str = "", session_option: str = "race"):
        try: gp_option, session_option = session_get_current(year_option, gp_option, session_option)
        except DataNotLoadedError:
            await ctx.send(FAULTY_VALUE_MESSAGE)
            return
        if check_if_restricted(ctx): return
        await ctx.defer()
        await ctx.send(file=_laps.compare_laps(year_option, gp_option, session_option, driver1_option, driver2_option))

    @laps_function.subcommand(
        sub_cmd_name="scatterplot",
        sub_cmd_description="Erstellt ein Scatterplot der Runden des Fahrers "
                            "(Standard: Zuletzt gefahrene Session (S,Q,R))"
    )
    @slash_option(
        name="driver_option",
        description="Fahrerkürzel",
        required=False,
        opt_type=OptionType.STRING,
        min_length=3,
        max_length=3
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option(True)
    async def scatterplot_function(self, ctx: SlashContext, driver1_option, year_option: int = CURRENT_SEASON,
                                   gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = session_get_current(year_option, gp_option, session_option)
        except DataNotLoadedError:
            await ctx.send(FAULTY_VALUE_MESSAGE)
            return
        if check_if_restricted(ctx): return
        await ctx.defer()
        await ctx.send(file=_laps.scatterplot(year_option, gp_option, session_option, driver1_option))

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
    async def raceinfo_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON,
                                gp_option: int = get_last_finished_gp()):
        if check_if_restricted(ctx): return
        await ctx.defer()
        try: await ctx.send(file=_race_info.position_change(year_option, gp_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @raceinfo_function.subcommand(
        sub_cmd_name="ltd",
        sub_cmd_description="Lap Time Distribution der Fahrer für das Rennen (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def ltd_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON,
                           gp_option: int = get_last_finished_gp()):
        if check_if_restricted(ctx): return
        await ctx.defer()
        try: await ctx.send(file=_race_info.lap_time_distribution(year_option, gp_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @raceinfo_function.subcommand(
        sub_cmd_name="tyre",
        sub_cmd_description="Reifenstrategieübersicht für das Rennen (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def tyre_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON,
                            gp_option: int = get_last_finished_gp()):
        if check_if_restricted(ctx): return
        await ctx.defer()
        try: await ctx.send(file=_race_info.strategy(year_option, gp_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

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
        name="championship_option",
        description="Meisterschaftsart",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Fahrer-WM", value=True),
            SlashCommandChoice(name="Konstrukteurs-WM", value=False)
        ]
    )
    async def standings_function(self, ctx: SlashContext,
                                 year_option: int = CURRENT_SEASON, championship_option: bool = True):
        if check_if_restricted(ctx): return
        try: await ctx.send(_standings.table(year_option, championship_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @standings_function.subcommand(
        sub_cmd_name="average",
        sub_cmd_description="Durschnittliche Position im Sessiontyp (Standard: Derzeitige Situation in den Rennen)"
    )
    @year_slash_option(1950)
    @session_slash_option(False)
    async def average_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, session_option: str = "R"):
        if check_if_restricted(ctx): return
        await ctx.defer()
        try: await ctx.send(file=_standings.average_position(year_option, session_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @standings_function.subcommand(
        sub_cmd_name="h2h",
        sub_cmd_description="Head2Head-Vergleich im Sessiontyp (Standard: Derzeitige Situation in den Rennen)"
    )
    @year_slash_option(1950)
    @session_slash_option(False)
    async def h2h_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, session_option: str = "R"):
        if check_if_restricted(ctx): return
        await ctx.defer()
        try: await ctx.send(embed=_standings.h2h(year_option, session_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @standings_function.subcommand(
        sub_cmd_name="heatmap",
        sub_cmd_description="Heatmap für die Positionen aller Fahrer in der Saison (Standard: Momentane Saison)"
    )
    @year_slash_option(1950)
    async def heatmap_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON):
        if check_if_restricted(ctx): return
        await ctx.defer()
        try: await ctx.send(file=_standings.heatmap(year_option))
        except DataNotLoadedError: await ctx.send(FAULTY_VALUE_MESSAGE)

    @standings_function.subcommand(
        sub_cmd_name="winnable",
        sub_cmd_description="Für welchen Fahrer ist die Meisterschaft noch gewinnbar?"
    )
    async def winnable_function(self, ctx: SlashContext):
        if check_if_restricted(ctx): return
        await ctx.defer()
        await ctx.send(embed=_standings.whocanwin())
