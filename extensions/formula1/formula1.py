import datetime
import random

import fastf1
import interactions
import pytz
import requests
from fastf1.core import DataNotLoadedError
from interactions import Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
from interactions.models import discord

import extensions.formula1._laps as laps
import extensions.formula1._no_group as no_group
import extensions.formula1._race_info as race_info
import extensions.formula1._standings as standings
import util

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
    event_schedule = fastf1.get_events_remaining()
    next_event = event_schedule.iloc[0]
    date_today = datetime.datetime.today()

    session_list = [next_event['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session2Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session3Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session4Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)]

    latest_finished_session = 5
    for i in range(0, len(session_list)):  # A session should be finished 1.5 hours after the start
        if session_list[i] + datetime.timedelta(hours=1.5) <= date_today: latest_finished_session = i + 1

    current_gp = next_event['RoundNumber'] - 1
    current_session = 5

    # If a session of the 'next event' has finished,
    # set the next_event as current_gp and the finished session as current_session
    if latest_finished_session < 5:
        current_gp = next_event['RoundNumber']
        current_session = latest_finished_session

    return current_gp, current_session


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
    if (date_today.weekday() == 4) and (
            (session_list[1] - date_today).days == 0): embed = no_group.next_race()

    for i in range(0, len(session_list)):  # A session should be finished 1.5 hours after the start
        if session_list[i].date() == date_today.date(): start_times.add(session_list[i] + datetime.timedelta(hours=1.5))

    return list(start_times), embed


def auto_result():
    """ Returns the result of the latest session and sets the current paras to it """
    url = "https://api.sport1.info/v2/de/motorsport/sport/sr:stage:7668/season/sr:stage:1031201/minSportEventsWithSessions"
    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
        "Accept": "*/*",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.sport1.de",
        "Connection": "keep-alive",
        "Referer": "https://www.sport1.de/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "DNT": "1",
        "Sec-GPC": "1",
        "TE": "trailers"
    }
    response = requests.request("GET", url, data=payload, headers=headers)
    print("API Call Formula1: " + url)
    response = response.json()

    current_comp_id = response['currentCompetitionId']
    current_match_id = ""
    for compo in response['competitions']:
        if compo['id'] == current_comp_id: current_match_id = compo['currentMatchId']

    url = f"https://api.sport1.info/v2/de/motorsport/sport/sr:stage:7668/match/{current_match_id}"
    response = requests.request("GET", url, data=payload, headers=headers)
    print("API Call Formula1: " + url)
    response = response.json()

    result = "```"
    result += f"Ergebnis {util.germanise(response['competition']['name'])} {response['roundTitle']}" + "\n"
    result += "\n"
    result += "#".ljust(6) + "Name".center(20)
    if response['roundType'] == "RACE" or response['roundType'] == "SPRINT":
        result += "Gesamt".center(14) + "Schnellste".center(14) + "P".rjust(3) + "\n"
        for position in response['results']:
            result += str(position['position']).ljust(6)
            result += f"{position['person']['firstName']} {position['person']['lastName']}".center(20)

            if position['status'] != "FINISHED": result += position['status'].center(14)
            else: result += str(position['time']).center(14)

            if 'fastestLap' in position: result += str(position['fastestLap']).center(14)
            else: result += " ".center(14)

            result += str(position['pitStopCount']).rjust(3)
            result += "\n"
    elif response['roundType'] == "QUALIFYING" or response['roundType'] == "SPRINT_SHOOTOUT":
        result += "Schnellste".center(20) + "\n"
        for position in response['results']:
            result += str(position['position']).ljust(6)
            result += f"{position['person']['firstName']} {position['person']['lastName']}".center(20)
            result += str(position['fastestLap']).center(20)
            result += "\n"
    else:
        result += "Schnellste".center(20) + "Stops".rjust(3) + "\n"
        for position in response['results']:
            result += str(position['position']).ljust(6)
            result += f"{position['person']['firstName']} {position['person']['lastName']}".center(20)
            result += str(position['fastestLap']).center(20)
            result += str(position['pitStopCount']).rjust(3)
            result += "\n"

    result += "```"
    result = "||" + result + "||"  # Make Spoiler

    return util.uwuify_by_chance(result)


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
            name=f"driver{number}_option",
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
    async def result_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON,
                              gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = get_current_and_check_input(year_option, gp_option, session_option)
        except DataNotLoadedError:
            await ctx.send(embed=util.get_error_embed("faulty_value"))
            return
        await command_function(ctx, no_group.result, year_option, gp_option, session_option)

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
        if allnext_option: await command_function(ctx, no_group.remaining_races)
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
    async def laps_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON,
                            gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = get_current_and_check_input(year_option, gp_option, session_option)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.overview_fastest_laps, year_option, gp_option,
                               session_option)

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
    async def compare_function(self, ctx: SlashContext, driver1_option, driver2_option,
                               year_option: int = CURRENT_SEASON,
                               gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = get_current_and_check_input(year_option, gp_option, session_option)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.compare_laps, year_option, gp_option, session_option,
                               driver1_option.upper(), driver2_option.upper())

    @laps_function.subcommand(
        sub_cmd_name="scatterplot",
        sub_cmd_description="Zeigt Scatterplot der Runden des Fahrers (Standard: Zuletzt gefahrene Session)"
    )
    @driver_slash_option()
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def scatterplot_function(self, ctx: SlashContext, driver1_option, year_option: int = CURRENT_SEASON,
                                   gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = get_current_and_check_input(year_option, gp_option, session_option)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.scatterplot, year_option, gp_option, session_option,
                               str.upper(driver1_option))

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
    async def telemetry_function(self, ctx: SlashContext, driver1_option, driver2_option,
                                 year_option: int = CURRENT_SEASON,
                                 gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = get_current_and_check_input(year_option, gp_option, session_option)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.telemetry, year_option, gp_option, session_option,
                               driver1_option.upper(), driver2_option.upper())

    @laps_function.subcommand(
        sub_cmd_name="track_dominance",
        sub_cmd_description="Vergleicht Streckendominanz der Fahrer (Standard: Zuletzt gefahrene Session)"
    )
    @driver_slash_option(1)
    @driver_slash_option(2)
    @year_slash_option(2018)
    @grandprix_slash_option()
    @session_slash_option()
    async def track_dominance_function(self, ctx: SlashContext, driver1_option, driver2_option,
                                       year_option: int = CURRENT_SEASON,
                                       gp_option: str = "", session_option: str = ""):
        try: gp_option, session_option = get_current_and_check_input(year_option, gp_option, session_option)
        except DataNotLoadedError: return await ctx.send(embed=util.get_error_embed("faulty_value"))
        await command_function(ctx, laps.track_dominance, year_option, gp_option, session_option,
                               driver1_option.upper(), driver2_option.upper())

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
    async def raceinfo_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, gp_option: int = 0):
        if gp_option == 0: gp_option = get_last_finished_gp()
        await command_function(ctx, race_info.position_change, year_option, gp_option)

    @raceinfo_function.subcommand(
        sub_cmd_name="ltd",
        sub_cmd_description="Lap Time Distribution der Fahrer für das Rennen (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def ltd_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, gp_option: int = 0):
        if gp_option == 0: gp_option = get_last_finished_gp()
        await command_function(ctx, race_info.lap_time_distribution, year_option, gp_option)

    @raceinfo_function.subcommand(
        sub_cmd_name="tyre",
        sub_cmd_description="Reifenstrategieübersicht für das Rennen (Standard: Letztes Rennen)"
    )
    @year_slash_option(2018)
    @grandprix_slash_option()
    async def tyre_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, gp_option: int = 0):
        if gp_option == 0: gp_option = get_last_finished_gp()
        await command_function(ctx, race_info.strategy, year_option, gp_option)

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
        opt_type=OptionType.BOOLEAN,
        choices=[
            SlashCommandChoice(name="Fahrer-WM", value=True),
            SlashCommandChoice(name="Konstrukteurs-WM", value=False)
        ]
    )
    async def standings_function(self, ctx: SlashContext,
                                 year_option: int = CURRENT_SEASON, championship_option: bool = True):
        await command_function(ctx, standings.table, year_option, championship_option)

    @standings_function.subcommand(
        sub_cmd_name="average",
        sub_cmd_description="Durchschnittliche Position im Sessiontyp (Standard: Derzeitige Situation in den Rennen)"
    )
    @year_slash_option(1950)
    @slash_option(
        name="session_option",
        description="Session",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Rennen", value="R"),
            SlashCommandChoice(name="Qualifikation", value="Q"),
            SlashCommandChoice(name="Sprint", value="S")
        ]
    )
    async def average_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, session_option: str = "R"):
        await command_function(ctx, standings.average_position, year_option, session_option)

    @standings_function.subcommand(
        sub_cmd_name="h2h",
        sub_cmd_description="Head2Head-Vergleich im Sessiontyp (Standard: Derzeitige Situation in den Rennen)"
    )
    @year_slash_option(1950)
    @slash_option(
        name="session_option",
        description="Session",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Rennen", value="R"),
            SlashCommandChoice(name="Qualifikation", value="Q"),
            SlashCommandChoice(name="Sprint", value="S")
        ]
    )
    async def h2h_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON, session_option: str = "R"):
        await command_function(ctx, standings.h2h, year_option, session_option)

    @standings_function.subcommand(
        sub_cmd_name="heatmap",
        sub_cmd_description="Heatmap für die Positionen aller Fahrer in der Saison (Standard: Momentane Saison)"
    )
    @year_slash_option(1950)
    async def heatmap_function(self, ctx: SlashContext, year_option: int = CURRENT_SEASON):
        await command_function(ctx, standings.heatmap, year_option)

    @standings_function.subcommand(
        sub_cmd_name="winnable",
        sub_cmd_description="Für welchen Fahrer ist die Meisterschaft noch gewinnbar?"
    )
    async def winnable_function(self, ctx: SlashContext):
        await command_function(ctx, standings.whocanwin())
