import datetime
import locale
import random

import interactions
import pytz
import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)
from interactions.models import discord

import helper
import uwuifier
from helper import germanise

locale.setlocale(locale.LC_ALL, 'de_DE')  # Changes local to Deutsch for time display
UWUCHANCE = helper.UWUCHANCE  # D-De chance dat a commyand wesponse gets u-u-uwuified
COMPETITION_LIST = ["2. Bundesliga", "League Cup", "Frauen-WM"]  # List of League interested in
COLOUR = discord.Color.from_rgb(29, 144, 83)  # Werder Bremen Green


# Sets up this extension
def setup(bot): Football(bot)


'''
##################################################
LIVE SCORE PART
##################################################
'''


def create_schedule():
    """ Returns Schedule based on the starting time of that day's games """
    start_times = set()

    # Get data from site
    date_today = datetime.datetime.today().date()
    url = f"https://api.sport1.info/v2/de/live/soccer/liveMatchesBySport/date/{date_today}/appConfig/false"

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
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
    data = response.json()
    data = data['content']
    # Iterate over every league
    for league in data:
        # Filter by wanted leagues
        if league['matches'][0]['competition']['name'] not in COMPETITION_LIST: continue
        # Add match times to set
        for match in league['matches']:
            time = datetime.datetime.fromisoformat(match['scheduledStartTime'])
            time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
            start_times.add(time)

    start_times = sorted(start_times)
    return start_times


def get_live(content=""):
    """ Returns a list of embeds - one for every league - with an embed for every game of that league
    content -- old message's content, "" if no old message exists, otherwise the message's embeds
    """
    embeds = []
    one_game_still_live = False

    # Get data from site
    date_today = datetime.datetime.today().date()
    url = f"https://api.sport1.info/v2/de/live/soccer/liveMatchesBySport/date/{date_today}/appConfig/false"

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
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
    data = response.json()
    data = data['content']

    print("Today:" + str(datetime.datetime.today()))
    print("Data:" + str(data))
    # Iterate over every league
    for league in data:
        # Skip league if not one of the wanted ones
        league_name = league['matches'][0]['competition']['name']
        if league_name not in COMPETITION_LIST: continue
        embed = interactions.Embed(title=league_name, color=COLOUR)
        # Iterate over every match in the league
        for match in league['matches']:
            team1 = germanise(match['homeTeam']['name'])
            team2 = germanise(match['awayTeam']['name'])
            # Goals
            score1 = 0
            score2 = 0
            if 'homeScore' in match: score1 = match['homeScore']
            if 'awayScore' in match: score2 = match['awayScore']
            # Game starting time
            minute = "Startet um " + datetime.datetime.fromisoformat(match['scheduledStartTime']).strftime(
                "%H:%M") + " Uhr"
            # If match has begun, get the minutes
            if 'matchTime' in match['matchInfo']: minute = str(match['matchInfo']['matchTime']) + "' "
            # If match has ended, put in the END
            if match['period'] == "FULL_TIME": minute = "END "
            # If match has gone to the penalties, add the score after the penalties after the normal score
            penalty_score = ""
            if 'homePenaltyScore' in match and 'awayPenaltyScore' in match:
                penalty_score = f" {match['homePenaltyScore']}:{match['awayPenaltyScore']} nE"
            # Put in Values
            new_name = f"```{team1:<30} {score1:^3}:{score2:^4}{penalty_score} {team2:>30}```"
            new_value = f"```{str(minute).zfill(2)}```"
            # If the score changes in the new message, get the goalscorers and put them as the new value
            if not content == "":
                old_embed = content[0]
                for em in content[1:]:  # Get correct embed
                    if em.title == embed.title: old_embed = em
                old = old_embed.fields[0]
                for field in old_embed.fields[1:]:  # Get correct field
                    if field.name[0:20] == new_name[0:20]: old = field
                old_name = old.name
                old_value = old.value
                print("OldName:" + old_name)
                print("NewName:" + new_name)
                # Get the match's goalscorers if a goal happened (old and new names differ)
                # or the score doesn't align with the amount of goalscorers
                if new_name != old_name or (score1 + score2) != (old_value.count("'") - 1):
                    new_value = new_value.split(' ')[0] + get_match_goals(match['id'])
                else: new_value = new_value.split(' ')[0] + " " + ' '.join(old_value.split(' ')[1:])
                print("OldValue:" + old_value)
                print("NewValue:" + new_value)
                print("\n\n")
            embed.add_field(name=new_name, value=new_value)
            if match['isLive']: one_game_still_live = True

        embeds.append(embed)

    return embeds, one_game_still_live


def get_match_goals(match_id):
    """ Get the match's goalscorers """
    print("Goal Match is called")
    # Get data from site
    url = f"https://api.sport1.info/v2/de/soccer/ticker/{match_id}"

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
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
        "If-None-Match": "W/0b32f50f11c4909718a882e15de834109",
        "TE": "trailers"
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    match_info = response.json()

    return_string = " "

    id_home = match_info['match']['homeTeam']['id']
    # id_away = match_info['match']['awayTeam']['id']
    goals_home = ""
    goals_away = ""
    # Iterate over every goal in the match
    for goal in match_info['matchGoals']:
        # if goal['failed']: continue
        team = goal['teamId']
        time = goal['minute']
        scorer = goal['player']['lastName']
        goal_type = ""
        if goal['penalty']:
            goal_type = " (P)"
        elif goal['ownGoal']:
            goal_type = " (OG)"
        elif goal['soloRun']:
            goal_type = " (SR)"
        if goal['failed']: goal_type = " (F)"
        if 'nickName' in goal['player']: scorer = goal['player']['nickName']
        score = f" {time}' {scorer}" + goal_type
        # Add Goal to the correct team
        if team == id_home:
            if not goals_home == "": goals_home += ','
            goals_home += score
        else:
            if not goals_away == "": goals_away += ','
            goals_away += score
    # Add the team's shortname if they scored at least one goal
    if not goals_home == "": goals_home = match_info['match']['homeTeam']['code'] + ":" + goals_home
    if not goals_away == "": goals_away = match_info['match']['awayTeam']['code'] + ":" + goals_away
    # Add the two team's goals to the return string
    if goals_home == "": return_string += goals_away
    elif goals_away == "": return_string += goals_home
    else: return_string += goals_home + "\n" + " " * 4 + goals_away
    return_string += "```"
    print("GoalsReturn:" + return_string)
    return return_string


'''
##################################################
COMMAND PART
##################################################
'''

SPORTS_CHANNEL_ID = open('./config.txt').readlines()[1]

WRONG_CHANNEL_MESSAGE = "Falscher Channel, Bro"
LIMIT_REACHED_MESSAGE = "Zu viele Commands, Bro"

LEAGUE_CHOICES = [
    SlashCommandChoice(name="1. Bundesliga", value="bl1"),
    SlashCommandChoice(name="2. Bundesliga", value="bl2"),
    SlashCommandChoice(name="3. Bundesliga", value="bl3"),
    SlashCommandChoice(name="DFB Pokal", value="dfb")
]
CURRENT_SEASON = 2023

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
    @slash_command(name="table", description="Gibt ne Tabelle")
    @league_slash_option()
    @season_slash_option()
    async def table_function(self, ctx: SlashContext, liga_option: str = "bl1", saison_option: int = CURRENT_SEASON):
        if ctx.channel_id != SPORTS_CHANNEL_ID:
            msg = WRONG_CHANNEL_MESSAGE
        elif limit_reached:
            msg = LIMIT_REACHED_MESSAGE
        else:
            msg = table(liga_option, saison_option)
            increment_command_calls()
        await ctx.send(msg)

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
    async def matchday_function(self, ctx: SlashContext, liga_option: str = "bl1", saison_option: int = CURRENT_SEASON,
                                day_option: int = 0):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(embed=matchday(liga_option, saison_option, day_option))

    @slash_command(name="goalgetter", description="Gibt die Topscorer zurück")
    @league_slash_option()
    @season_slash_option()
    async def goalgetter_funtion(self, ctx: SlashContext, liga_option: str = "bl1",
                                 saison_option: int = CURRENT_SEASON):
        if str(ctx.channel_id) != SPORTS_CHANNEL_ID:
            await ctx.send(WRONG_CHANNEL_MESSAGE)
            return
        elif limit_reached:
            await ctx.send(LIMIT_REACHED_MESSAGE)
            return
        increment_command_calls()
        await ctx.send(embed=goalgetter(liga_option, saison_option))

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
        await ctx.send(embed=matches(team_option, past_option, future_option))


def table(liga, saison):
    """ Method for the table command """
    url = f"https://api.openligadb.de/getbltable/{liga}/{saison}"
    response = requests.get(url)
    data = response.json()

    tabelle = "```"
    tabelle += "# | Team".ljust(30) + "Sp Si Un Ni Tore  Diff".center(20) + "Punkte".rjust(10) + "\n"
    i = 1
    for team in data:
        name = germanise(team['teamName'])
        points = str(team['points']).zfill(2) + " "
        scored_goals = str(team['goals']).zfill(2)
        conc_goals = str(team['opponentGoals']).zfill(2)
        goal_diff = (team['goalDiff'])
        if goal_diff > -10: goal_diff = str(goal_diff).zfill(2) + " "
        played = str(team['matches']).zfill(2)
        won = str(team['won']).zfill(2)
        lost = str(team['lost']).zfill(2)
        draw = str(team['draw']).zfill(2)
        tabelle += (f"{str(i).zfill(2)}| {name}".ljust(30)
                    + f"{played} {won} {draw} {lost} {scored_goals}:{conc_goals} {goal_diff}".center(20)
                    + f"{points}".rjust(10) + "\n")
        i += 1
    tabelle += "```"

    if random.randint(0, 100) < UWUCHANCE: tabelle = uwuifier.UwUify(tabelle, False, False)

    return tabelle


def matchday(liga, saison, spieltag):
    """ Method for the matchday command """
    if spieltag == 0: spieltag = get_current_spieltag(liga)

    url = f"https://api.openligadb.de/getmatchdata/{liga}/{saison}/{spieltag}"
    response = requests.get(url)
    jsondata = response.json()

    embed = interactions.Embed(title=f"{germanise(jsondata[0]['leagueName'])} Spieltag {spieltag}", color=COLOUR)
    i = 1
    for match in jsondata:
        time = datetime.datetime.fromisoformat(match['matchDateTime']).strftime("%A, %d. %B %Y %H:%M")
        team1 = germanise(match['team1']['teamName'])
        team2 = germanise(match['team2']['teamName'])
        goals1 = "-"
        goals2 = "-"
        if len(match['matchResults']) > 0:
            goals1 = match['matchResults'][0]['pointsTeam1']
            goals2 = match['matchResults'][0]['pointsTeam2']
        embed.add_field(name=f"Spiel {i}: {time}",
                        value=f"`{team1: <25}" f"{goals1: ^3} : {goals2: ^4}" f"{team2: >25}`")
        i += 1

    if random.randint(0, 100) < UWUCHANCE: embed = helper.uwuify_embed(embed)

    return embed


def goalgetter(liga, saison):
    """ Method for the goalgetter command """
    url = f"https://api.openligadb.de/getgoalgetters/{liga}/{saison}"
    response = requests.get(url)
    data = response.json()

    embed = interactions.Embed(title=f"Torjäger der Liga {liga}", color=COLOUR)
    for i in range(0, min(len(data), 15)):  # Limit shown scorers to 15
        name = germanise(data[i]['goalGetterName'])
        goals = data[i]['goalCount']
        embed.add_field(name=name, value=goals, inline=True)

    if random.randint(0, 100) < UWUCHANCE: embed = helper.uwuify_embed(embed)

    return embed


def matches(team, past, future):
    """ Method for the matches command """
    url = f"https://api.openligadb.de/getmatchesbyteam/{team}/{past}/{future}"
    response = requests.get(url)
    data = response.json()

    embed = interactions.Embed(title=f"Spiele von {team} in den letzten {past} und den nächsten {future} Wochen",
                               color=COLOUR)

    latest_match_date = ""  # To prevent two games at the same time from making the list

    i = 1
    for match in data:
        time = datetime.datetime.fromisoformat(match['matchDateTime']).strftime("%a, %d. %b %Y %H:%M")
        if latest_match_date == time: continue  # Go to next match if match already exists
        latest_match_date = time

        team1 = germanise(match['team1']['teamName'])
        team2 = germanise(match['team2']['teamName'])
        goals1 = "-"
        goals2 = "-"
        if len(match['matchResults']) > 0:
            goals1 = match['matchResults'][0]['pointsTeam1']
            goals2 = match['matchResults'][0]['pointsTeam2']
        embed.add_field(name=f"{match['leagueName']}, {match['group']['groupName']}: {time}",
                        value=f"`{team1: <25}" f"{goals1: ^3} : {goals2: ^4}" f"{team2: >25}`")
        i += 1

    if random.randint(0, 100) < UWUCHANCE: embed = helper.uwuify_embed(embed)

    return embed


def get_current_spieltag(liga):
    """ Gets the current Spieltag """
    url = f'https://api.openligadb.de/getcurrentgroup/{liga}'
    response = requests.get(url)
    data = response.json()
    return data['groupOrderID']
