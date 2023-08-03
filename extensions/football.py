import datetime
import json
import locale

import interactions
import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)

locale.setlocale(locale.LC_ALL, 'de_DE')


def setup(bot):
    Football(bot)


leagueChoices = [
    SlashCommandChoice(name="1. Bundesliga", value="bl1"),
    SlashCommandChoice(name="2. Bundesliga", value="bl2"),
    SlashCommandChoice(name="3. Bundesliga", value="bl3"),
    SlashCommandChoice(name="DFB Pokal", value="dfb")
]
currentSaison = 2023


def liga_slash_option():  # call with @liga_option
    def wrapper(func):
        return slash_option(
            name="liga_option",
            description="Liga",
            required=False,
            opt_type=OptionType.STRING,
            choices=leagueChoices
        )(func)

    return wrapper


def saison_slash_option():  # call with @saison_option
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
    @liga_slash_option()
    @saison_slash_option()
    async def table_function(self, ctx: SlashContext, liga_option: str = "bl1", saison_option: int = currentSaison):
        await ctx.send(table(liga_option, saison_option))

    @slash_command(name="matchday", description="Gibtn Spieltag")
    @liga_slash_option()
    @saison_slash_option()
    @slash_option(
        name="day_option",
        description="Spieltag",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1
    )
    async def matchday_function(self, ctx: SlashContext, liga_option: str = "bl1", saison_option: int = currentSaison,
                                day_option: int = 0):
        await ctx.send(embed=matchday(liga_option, saison_option, day_option))

    @slash_command(name="goalgetter", description="Gibt die Topscorer zurück")
    @liga_slash_option()
    @saison_slash_option()
    async def goalgetter_funtion(self, ctx: SlashContext, liga_option: str = "bl1", saison_option: int = currentSaison):
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
        await ctx.send(embed=matches(team_option, past_option, future_option))


def table(liga, saison):
    url = f"https://api.openligadb.de/getbltable/{liga}/{saison}"
    response = requests.get(url)
    data = response.json()

    tabelle = "```"
    tabelle += "# | Team".ljust(35) + "Sp Si Un Ni Tore  Diff".center(20) + "Punkte".rjust(10) + "\n"
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
        tabelle += (f"{str(i).zfill(2)}| {name}".ljust(35)
                    + f"{played} {won} {draw} {lost} {scored_goals}:{conc_goals} {goal_diff}".center(20)
                    + f"{points}".rjust(10) + "\n")
        i += 1
    tabelle += "```"
    return tabelle


def matchday(liga, saison, spieltag):
    if spieltag == 0: spieltag = getCurrentSpieltag(liga)

    url = f"https://api.openligadb.de/getmatchdata/{liga}/{saison}/{spieltag}"
    response = requests.get(url)
    jsondata = response.json()

    embed = interactions.Embed(title=f"{germanise(jsondata[0]['leagueName'])} Spieltag {spieltag}")
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

    return embed


def goalgetter(liga, saison):
    url = f"https://api.openligadb.de/getgoalgetters/{liga}/{saison}"
    response = requests.get(url)
    data = response.json()

    embed = interactions.Embed(title=f"Torjäger der Liga {liga}")
    for i in range(0, min(len(data), 15)):
        name = germanise(data[i]['goalGetterName'])
        goals = data[i]['goalCount']
        embed.add_field(name=name, value=goals, inline=True)

    return embed


def matches(team, past, future):
    url = f"https://api.openligadb.de/getmatchesbyteam/{team}/{past}/{future}"
    response = requests.get(url)
    data = response.json()

    embed = interactions.Embed(title=f"Spiele von {team} in den letzten {past} und den nächsten {future} Wochen")

    latest_match_date = ""  # To prevent two games at the same time from making the list

    i = 1
    for match in data:
        time = datetime.datetime.fromisoformat(match['matchDateTime']).strftime("%a, %d. %b %Y %H:%M")
        if latest_match_date == time: continue
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

    return embed


def germanise(str):
    char_map = {ord('Ã'): '', ord('¼'): 'ü', ord('¶'): 'ö', ord('¤'): 'ä', ord('Ÿ'): 'ß'}
    return str.translate(char_map)


def getCurrentSpieltag(liga):
    url = f'https://api.openligadb.de/getcurrentgroup/{liga}'
    response = requests.get(url)
    data = response.json()
    return data['groupOrderID']
