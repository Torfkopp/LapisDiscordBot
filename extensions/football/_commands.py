import datetime

import interactions
import requests
from bs4 import BeautifulSoup

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


def shorten_name(name):
    """ Hardcoding the shorter names of some clubs """
    if "Mönchengladbach" in name: return "Borussia M'Gladbach"
    if "Heidenheim" in name: return "1. FC Heidenheim"
    if len(name) > 19: return name[:19]  # Not pretty, but effective
    return name


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

    tabelle = "# | " + "Team".ljust(20) + "|Pk|Sp|S |U |N |Tore | TD" + "\n"

    def row_builder(nr, na, po, ga, w, d, lo, go, gd):
        return "|".join(
            [str(nr).zfill(2), " " + na.ljust(20),
             str(po).zfill(2), str(ga).zfill(2),
             str(w).zfill(2), str(d).zfill(2), str(lo).zfill(2),
             go, str(gd).zfill(2).rjust(3)]
        ) + "\n"

    tabelle += row_builder("--", "-" * 19, "--", "--", "--", "--", "--", "-" * 5, "---")

    for i, team in enumerate(data):
        name = shorten_name(germanise(team["teamName"]))
        tabelle += row_builder(
            i + 1, name, team["points"], team['matches'], team['won'], team['draw'], team['lost'],
            f"{team['goals']}:{team['opponentGoals']}", team['goalDiff']
        )
    tabelle = "```glsl\n" + tabelle + "```"

    embed = interactions.Embed(title="Tabelle", description=tabelle, color=COLOUR)

    return util.uwuify_by_chance(embed)


def euro_where():
    url = (
        "https://www.sportschau.de/fussball/uefa-euro-2024/euro-2024-spielplan-"
        "und-sendezeiten,uefa-euro24-spielplan-100.html"
    )
    log.write("API-Call Euro: " + url)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    games = soup.findAll('tr')

    next_games = ""
    counter = 0
    for game in games:
        subs = game.findAll('td')
        if len(subs) == 0: continue
        num4 = subs[4].text.strip()
        if ":" in num4 or len(num4) == 0: continue
        counter += 1

        next_games += f"`{subs[0].text.strip()} {subs[1].text.strip()} {subs[3].text.strip()}".ljust(30)
        next_games += f"{subs[2].text.strip()}".ljust(30)
        next_games += f"{num4}"
        next_games += "`\n"

    embed = interactions.Embed(title="Nächste Europameisterschaftsspiele", description=next_games, color=COLOUR)

    return util.uwuify_by_chance(embed)
