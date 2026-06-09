from datetime import datetime

import interactions
import requests
from bs4 import BeautifulSoup

import util
from core import log
from util import germanise
from tabulate import tabulate

""" All methods for the football commands"""

COLOUR = util.Colour.FOOTBALL.value


def goalgetter(liga, saison):
    """Method for the goalgetter command"""
    url = f"https://api.openligadb.de/getgoalgetters/{liga}/{saison}"
    try:
        log.write("Api-Call Football: " + url)
        response = requests.get(url)
        data = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    embed = interactions.Embed(title=f"Torjäger der Liga {liga}", color=COLOUR)
    for i in range(min(len(data), 15)):  # Limit shown scorers to 15
        name = germanise(data[i]["goalGetterName"])
        goals = data[i]["goalCount"]
        embed.add_field(name=name, value=goals, inline=True)

    return util.uwuify_by_chance(embed)


def get_current_spieltag(liga):
    """Gets the current Spieltag"""
    url = f"https://api.openligadb.de/getcurrentgroup/{liga}"
    log.write("Api-Call Football: " + url)
    response = requests.get(url)
    data = response.json()
    return data["groupOrderID"]


def matchday(liga, saison, spieltag):
    """Method for the matchday command"""
    if spieltag == 0:
        try:
            spieltag = get_current_spieltag(liga)
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

    embed = interactions.Embed(
        title=f"{germanise(jsondata[0]['leagueName'])} Spieltag {spieltag}", color=COLOUR
    )
    i = 1
    for match in jsondata:
        time = datetime.fromisoformat(
            match["matchDateTime"].replace("Z", "+00:00")
        ).strftime("%A, %d. %B %Y %H:%M")
        team1 = germanise(match["team1"]["teamName"])
        team2 = germanise(match["team2"]["teamName"])
        goals1 = "-"
        goals2 = "-"
        if len(match["matchResults"]) > 0:
            goals1 = match["matchResults"][0]["pointsTeam1"]
            goals2 = match["matchResults"][0]["pointsTeam2"]
        embed.add_field(
            name=f"Spiel {i}: {time}",
            value=f"`{team1: <25}{goals1: ^3} : {goals2: ^4}{team2: >25}`",
        )
        i += 1

    return util.uwuify_by_chance(embed)


def matches(team, past, future):
    """Method for the matches command"""
    url = f"https://api.openligadb.de/getmatchesbyteam/{team}/{past}/{future}"
    try:
        log.write("Api-Call Football: " + url)
        response = requests.get(url)
        data = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    embed = interactions.Embed(
        title=f"Spiele von {team} in den letzten {past} und den nächsten {future} Wochen",
        color=COLOUR,
    )

    latest_match_date = ""  # To prevent two games at the same time from making the list

    i = 1
    for match in data:
        time = datetime.fromisoformat(
            match["matchDateTime"].replace("Z", "+00:00")
        ).strftime("%a, %d. %b %Y %H:%M")
        if latest_match_date == time:
            continue  # Go to next match if match already exists
        latest_match_date = time

        team1 = germanise(match["team1"]["teamName"])
        team2 = germanise(match["team2"]["teamName"])
        goals1 = "-"
        goals2 = "-"
        if len(match["matchResults"]) > 0:
            goals1 = match["matchResults"][0]["pointsTeam1"]
            goals2 = match["matchResults"][0]["pointsTeam2"]
        embed.add_field(
            name=f"{match['leagueName']}, {match['group']['groupName']}: {time}",
            value=f"`{team1: <25}{goals1: ^3} : {goals2: ^4}{team2: >25}`",
        )
        i += 1

    return util.uwuify_by_chance(embed)


def shorten_name(name):
    """Hardcoding the shorter names of some clubs"""
    if "Mönchengladbach" in name:
        return "Borussia M'Gladbach"
    if "Heidenheim" in name:
        return "1. FC Heidenheim"
    if len(name) > 19:
        return name[:19]  # Not pretty, but effective
    return name


def table(liga, saison):
    """Method for the table command"""
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
        return (
            "|".join(
                [
                    str(nr).zfill(2),
                    " " + na.ljust(20),
                    str(po).zfill(2),
                    str(ga).zfill(2),
                    str(w).zfill(2),
                    str(d).zfill(2),
                    str(lo).zfill(2),
                    go,
                    str(gd).zfill(2).rjust(3),
                ],
            )
            + "\n"
        )

    tabelle += row_builder("--", "-" * 19, "--", "--", "--", "--", "--", "-" * 5, "---")

    for i, team in enumerate(data):
        name = shorten_name(germanise(team["teamName"]))
        tabelle += row_builder(
            i + 1,
            name,
            team["points"],
            team["matches"],
            team["won"],
            team["draw"],
            team["lost"],
            f"{team['goals']}:{team['opponentGoals']}",
            team["goalDiff"],
        )
    tabelle = "```glsl\n" + tabelle + "```"

    embed = interactions.Embed(title="Tabelle", description=tabelle, color=COLOUR)

    return util.uwuify_by_chance(embed)


def wm_where(num_games=10):
    """Returns the next games of the WM"""

    def parse_game_datetime(date_str, time_str):
        """Parses date and time strings into a datetime object."""
        date_str = date_str.strip().lower()
        time_str = time_str.strip()
        
        if ":" in time_str: hour, minute = map(int, time_str.split(":"))
        else: hour, minute = 0, 0
            
        if date_str.endswith("."):
            parts = date_str.rstrip(".").split(".")
            if len(parts) == 2:
                day = int(parts[0])
                month = int(parts[1])
                return datetime(2026, month, day, hour, minute)

    url = "https://www.sportschau.de/fussball/fifa-wm-2026/der-spielplan-der-fussball-wm-2026,fifawm-spielplan-100.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    log.write(f"API Call WM: {url}\n")
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"  # Ensure proper decoding of German characters
        response.raise_for_status()
    except Exception as e:
        log.write(f"Error fetching the page: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
        
    games = []
    
    for idx, table in enumerate(tables):
        rows = table.find_all("tr")
        if not rows:
            continue
            
        # Check if the first row is a header row
        headers_in_row = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        has_header = "datum" in headers_in_row or "begegnung" in headers_in_row
        
        start_row_idx = 1 if has_header else 0
        
        for row in rows[start_row_idx:]:
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) >= 3:
                date_str = cells[0]
                time_str = cells[1]
                match_str = cells[2]
                sender_str = cells[3] if len(cells) > 3 else ""

                if not sender_str or sender_str.strip() == "": sender_str = "-"
                
                parsed_dt = parse_game_datetime(date_str, time_str)
                
                games.append({
                    "date_str": date_str,
                    "time_str": time_str,
                    "match": match_str,
                    "sender": sender_str,
                    "datetime": parsed_dt
                })

    games.sort(key=lambda g: g["datetime"] if g["datetime"] else datetime.max)
    
    now = datetime.now()
    
    future_games = [g for g in games if g["datetime"] and g["datetime"] >= now]
    display_games = future_games[:num_games]
    title = f"Die nächsten {num_games} Spiele der FIFA WM 2026 (ab {now.strftime('%d.%m.%Y %H:%M')}):"

    # Prepare data for tabulate
    table_data = []
    for g in display_games:
        table_data.append([
            g['date_str'],
            g['time_str'],
            g['match'],
            g['sender']
        ])
        
    headers = ["Datum", "Zeit", "Begegnung", "Sender"]
    
    table = tabulate(table_data, headers=headers, tablefmt="fancy_grid", maxcolwidth=[8,7,25,9])
    table = "```\n" + table + "\n```"
    
    embed = interactions.Embed(
        title=title, description=table, color=COLOUR
    )

    return util.uwuify_by_chance(embed)
    
