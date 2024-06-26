import datetime

import interactions
import pytz
import requests
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)
from interactions.client.utils import underline, bold

import util
from core import log

COLOUR = util.Colour.LOLESPORTS.value
COMMAND_LIMIT = 3  # Limit of consecutive calls in a short time (~60 calls per hour possible with a limit of 3)

LEAGUE_DICT = {
    "WORLDS": "98767975604431411",
    # "WORLDS QUALI SERIES": "110988878756156222",
    "MSI": "98767991325878492",
    # "ALL-STAR": "98767991295297326",
    "LEC": "98767991302996019",
    "PRIME": "105266091639104326",
    "LCK": "98767991310872058",
    # "EMEA": "100695891328981122",
    "LPL": "98767991314006698",
    "LCS": "98767991299243165",
}
LIVE_LEAGUES = "98767975604431411,98767991325878492,98767991302996019,105266091639104326"
STANDARD = LEAGUE_DICT.get("LEC")


def setup(bot): LoLesports(bot)


'''
##################################################
LIVE PART
##################################################
'''


def create_schedule():
    start_times = set()
    events = get_schedule(LIVE_LEAGUES)  # Embed gets returned if faulty
    if isinstance(events, interactions.Embed): return list(start_times)

    now = datetime.datetime.now()
    for event in events:
        time = datetime.datetime.fromisoformat(event['startTime'].replace("Z", "+00:00"))
        time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        if event['state'] == "inProgress": time = now + datetime.timedelta(minutes=1)
        elif not time.date() == now.date(): continue
        start_times.add(time)

    return list(start_times)


def get_live():
    embeds = {}
    one_game_still_live = False

    events = get_schedule(LIVE_LEAGUES)
    today = datetime.datetime.now().date()

    for event in events:
        if event['type'] != 'match': continue
        time = datetime.datetime.fromisoformat(event['startTime'].replace("Z", "+00:00"))
        time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        if not time.date() == today: continue

        league = event['league']['name']
        if embeds.get(league) is None: embeds[league] = interactions.Embed(title=league, color=COLOUR)
        embed = embeds[league]

        team1 = event['match']['teams'][0]
        team2 = event['match']['teams'][1]
        record1 = f"{team1['record']['wins']}-{team1['record']['losses']}"
        record2 = f"{team2['record']['wins']}-{team2['record']['losses']}"
        wins1 = team1['result']['gameWins']
        wins2 = team2['result']['gameWins']

        if event['state'] == 'completed': time = "END"
        elif event['state'] == 'inProgress':
            time = "LIVE"
            one_game_still_live = True
        else: time = f"Startet um: {datetime.datetime.strftime(time, '%d.%m %H:%M')}"

        bo_format = f"{(event['match']['strategy']['type']).capitalize()} {event['match']['strategy']['count']}"
        # name: (W-L) Team1 X:Y Team2 (W-L), value: Startzeit (oder END), Format
        embed.add_field(name=f"({record1}) {team1['name']} {wins1}:{wins2} {team2['name']} ({record2})",
                        value=f"{time}, {bo_format}",
                        inline=True)  # See how inlining looks

    embeds = list(embeds.values())
    return embeds, one_game_still_live


'''
##################################################
COMMAND PART
##################################################
'''
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


async def command_function(ctx, func, *args):
    """ Function for the commands """
    if str(ctx.channel_id) != util.SPORTS_CHANNEL_ID:
        await ctx.send(embed=util.get_error_embed("wrong_channel"))
        return
    elif limit_reached:
        await ctx.send(embed=util.get_error_embed("limit_reached"))
        return
    increment_command_calls()
    result = func(*args)
    if isinstance(result, interactions.Embed): await ctx.send(embed=result)
    else: await ctx.send(result)


def league_slash_option():
    def wrapper(func):
        choices = []
        for key in LEAGUE_DICT: choices.append(SlashCommandChoice(name=key, value=LEAGUE_DICT.get(key)))
        return slash_option(
            name="league",
            description="Name der Liga",
            required=False,
            opt_type=OptionType.STRING,
            choices=choices
        )(func)

    return wrapper


class LoLesports(Extension):
    @slash_command(name="lol", description="LoL-Esports Befehle")
    async def lol_function(self, ctx: SlashContext): await ctx.send("LoL")

    @lol_function.subcommand(sub_cmd_name="results", sub_cmd_description="Die Ergebnisse der letzten Matches")
    @league_slash_option()
    async def results_function(self, ctx: SlashContext, league: str = STANDARD):
        await command_function(ctx, get_results, league)

    @lol_function.subcommand(sub_cmd_name="standings", sub_cmd_description="Die Standings der Liga")
    @league_slash_option()
    async def standings_function(self, ctx: SlashContext, league: str = STANDARD):
        await command_function(ctx, get_standings, league)

    @lol_function.subcommand(sub_cmd_name="upcoming", sub_cmd_description="Die nächsten Matches")
    @league_slash_option()
    async def upcoming_function(self, ctx: SlashContext, league: str = STANDARD):
        await command_function(ctx, get_upcoming, league)


def get_schedule(league):
    url = "https://esports-api.lolesports.com/persisted/gw/getSchedule"
    querystring = {"hl": "de-DE", "leagueId": league}

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
        "Accept": "*/*",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://lolesports.com/",
        "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
        "Origin": "https://lolesports.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "DNT": "1",
        "Sec-GPC": "1",
        "TE": "trailers"
    }

    try:
        log.write(f"Api-Call lolesports: {url} {querystring}")
        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
        response = response.json()
        events = response['data']['schedule']['events']
    except (KeyError, requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    return events


def get_upcoming(league):
    """ Get the upcoming matches """
    events = get_schedule(league)
    embed = interactions.Embed(title="Zeitplan", color=COLOUR)

    upcoming = []
    for event in reversed(events):
        if event['state'] != "unstarted": break  # after seeing a "not unstarted" game, every game will be completed
        upcoming.insert(0, event)  # since events is reversed, insert at beginning

    upcoming = upcoming[0:25]  # Slice it since embed can only take 25 fields

    for event in upcoming:
        team1 = event['match']['teams'][0]
        team2 = event['match']['teams'][1]
        record1 = f"{team1['record']['wins']}-{team1['record']['losses']}" if team1['record'] is not None else ""
        record2 = f"{team2['record']['wins']}-{team2['record']['losses']}" if team2['record'] is not None else ""
        start_time = datetime.datetime.fromisoformat(event['startTime'].replace("Z", "+00:00"))
        start_time = start_time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        start_time = datetime.datetime.strftime(start_time, "%d.%m %H:%M")
        league = event['league']['name']
        block = event['blockName']
        bo_format = f"{(event['match']['strategy']['type']).capitalize()} {event['match']['strategy']['count']}"
        embed.add_field(name=f"({record1}) {team1['name']} gegen {team2['name']} ({record2})",
                        value=f"{start_time} | {league} {block} {bo_format}")

    embed.set_footer(f"Für mehr: https://lolesports.com/schedule?leagues={events[0]['league']['slug']}")

    return util.uwuify_by_chance(embed)


def get_results(league):
    """ Get the last results """
    events = get_schedule(league)
    embed = interactions.Embed(title="Resultate", color=COLOUR)

    completed = []
    i = 0
    match_amount = 15
    for event in reversed(events):
        if event['state'] == "unstarted": continue
        if i >= match_amount: break
        completed.insert(0, event)
        i += 1

    for event in completed:
        team1 = event['match']['teams'][0]
        team2 = event['match']['teams'][1]
        record1 = f"{team1['record']['wins']}-{team1['record']['losses']}"
        record2 = f"{team2['record']['wins']}-{team2['record']['losses']}"
        wins1 = team1['result']['gameWins']
        wins2 = team2['result']['gameWins']
        start_time = datetime.datetime.fromisoformat(event['startTime'].replace("Z", "+00:00"))
        start_time = start_time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        start_time = datetime.datetime.strftime(start_time, "%d.%m %H:%M")
        league = event['league']['name']
        block = event['blockName']
        embed.add_field(name=f"({record1}) {team1['name']} {wins1}:{wins2} {team2['name']} ({record2})",
                        value=f"{start_time} | {league} {block}", inline=True)

    embed.set_footer(f"Für mehr: https://lolesports.com/schedule?leagues={events[0]['league']['slug']}")

    return util.uwuify_by_chance(embed)


def get_standings(league):
    """ Get the standings """
    url = "https://esports-api.lolesports.com/persisted/gw/getTournamentsForLeague"
    querystring = {"hl": "de-DE", "leagueId": league}

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
        "Accept": "*/*",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://lolesports.com/",
        "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
        "Origin": "https://lolesports.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
        "DNT": "1",
        "Sec-GPC": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }

    try:
        log.write("Api-Call lolesports: " + url)
        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
        response = response.json()
        response = response['data']['leagues'][0]['tournaments'][0]
    except (KeyError, requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    tournament_id = response['id']

    url = "https://esports-api.lolesports.com/persisted/gw/getStandingsV3"
    querystring = {"hl": "de-DE", "tournamentId": tournament_id}

    try:
        log.write("Api-Call lolesports: " + url)
        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
        response = response.json()
        standings = response['data']['standings'][0]
    except (KeyError, requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    standings_name = standings['slug'].replace("_", " ").title()
    embed = interactions.Embed(title=f"Standings für {standings_name}", color=COLOUR)

    for stage in standings['stages']:
        embed.add_field(name="\u200b", value=bold(underline(stage['name'])))
        for section in stage['sections']:
            if len(section['rankings']) > 0:
                title = section['name'].replace("\\xa0", " ")
                value = ""
                for ranking in section['rankings']:
                    for team in ranking['teams']:
                        value += (f"{ranking['ordinal']}. {team['name']} "
                                  f"{team['record']['wins']}-{team['record']['losses']}")
                        value += "\n"
                embed.add_field(title, value, True)

            elif len(section['columns']) > 0:
                for columns in section['columns']:
                    for cell in columns['cells']:
                        title = cell['name']
                        value = ""
                        for match in cell['matches']:
                            teams = match['teams']
                            team1 = teams[0]['code']
                            team2 = teams[1]['code']
                            try: wins1 = teams[0]['result']['gameWins']
                            except TypeError: wins1 = 0
                            try: wins2 = teams[1]['result']['gameWins']
                            except TypeError: wins2 = 0
                            value += f"{team1} {wins1}:{wins2} {team2}"
                            value += "\n"
                        embed.add_field(title, value, True)

    embed.set_footer(f"Für mehr: https://lolesports.com/standings/{league}")

    return util.uwuify_by_chance(embed)
