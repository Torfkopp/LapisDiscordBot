import datetime

import interactions
import requests

import util
from core import log
from util import germanise

""" All methods for the football commands"""

COLOUR = util.Colour.FOOTBALL.value


def goalgetter(liga, saison):
    """ Method for the goalgetter command """
    url = f"https://api.openligadb.de/getgoalgetters/{liga}/{saison}"
    try:
        log.write("Api-Call Football: " + url)
        response = requests.get(url)
        data = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    embed = interactions.Embed(title=f"Torjäger der Liga {liga}", color=COLOUR)
    for i in range(0, min(len(data), 15)):  # Limit shown scorers to 15
        name = germanise(data[i]['goalGetterName'])
        goals = data[i]['goalCount']
        embed.add_field(name=name, value=goals, inline=True)

    return util.uwuify_by_chance(embed)


def get_current_spieltag(liga):
    """ Gets the current Spieltag """
    url = f'https://api.openligadb.de/getcurrentgroup/{liga}'
    log.write("Api-Call Football: " + url)
    response = requests.get(url)
    data = response.json()
    return data['groupOrderID']


def matchday(liga, saison, spieltag):
    """ Method for the matchday command """
    if spieltag == 0:
        try: spieltag = get_current_spieltag(liga)
        except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
            log.write("API DOWN")
            return util.get_error_embed("api_down")

    url = f"https://api.openligadb.de/getmatchdata/{liga}/{saison}/{spieltag}"
    try:
        log.write("Api-Call Football: " + url)
        response = requests.get(url)
        jsondata = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    embed = interactions.Embed(title=f"{germanise(jsondata[0]['leagueName'])} Spieltag {spieltag}", color=COLOUR)
    i = 1
    for match in jsondata:
        time = datetime.datetime.fromisoformat(match['matchDateTime'].replace("Z", "+00:00")).strftime(
            "%A, %d. %B %Y %H:%M")
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

    return util.uwuify_by_chance(embed)


def matches(team, past, future):
    """ Method for the matches command """
    url = f"https://api.openligadb.de/getmatchesbyteam/{team}/{past}/{future}"
    try:
        log.write("Api-Call Football: " + url)
        response = requests.get(url)
        data = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    embed = interactions.Embed(title=f"Spiele von {team} in den letzten {past} und den nächsten {future} Wochen",
                               color=COLOUR)

    latest_match_date = ""  # To prevent two games at the same time from making the list

    i = 1
    for match in data:
        time = datetime.datetime.fromisoformat(match['matchDateTime'].replace("Z", "+00:00")).strftime(
            "%a, %d. %b %Y %H:%M")
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

    return util.uwuify_by_chance(embed)


def table(liga, saison):
    """ Method for the table command """
    url = f"https://api.openligadb.de/getbltable/{liga}/{saison}"
    try:
        log.write("Api-Call Football: " + url)
        response = requests.get(url)
        data = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    tabelle = "```"
    tabelle += "# | Team".ljust(30) + "Sp Si Un Ni Tore  TD".center(20) + "Pkt".rjust(10) + "\n"
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

    embed = interactions.Embed(title="Tabelle", description=tabelle, color=COLOUR)

    return util.uwuify_by_chance(embed)
