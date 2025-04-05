import datetime
from collections import defaultdict

import interactions
import pytz
import requests

import util
from core import log
from util import germanise

""" All methods for the football live scoring """

# List of Leagues fully interested in
UNFILTERED_COMPETITIONS = ["Bundesliga", "2. Bundesliga", "DFB-Pokal", "Supercup", "EM 2024"]
# List of Leagues partially interested in
FILTERED_COMPETITIONS = ["Champions League", "Europa League", "Europa Conference League", "Länderspiele"]
COMPETITION_LIST = UNFILTERED_COMPETITIONS + FILTERED_COMPETITIONS  # List of all Leagues with at least some interest in

COLOUR = util.Colour.FOOTBALL.value

league_matches = defaultdict(list)
matches = {}

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


class Game:
    start_time: datetime.date
    team1: str
    team2: str
    team1_short: str
    team2_short: str
    minute: int = -1
    done: bool = False
    score: tuple[int, int] = (0, 0)
    penalty_score: tuple = ()
    goals1: list[tuple[int, str, str]] = []
    goals2: list[tuple[int, str, str]] = []

    def __init__(self, start_time, team1, team2, team1_short, team2_short):
        self.start_time = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        self.team1, self.team2 = germanise(team1), germanise(team2)
        self.team1_short, self.team2_short = team1_short, team2_short

    def set_goals(self, h: int, a: int):
        if self.score[0] == h and self.score[1] == a:
            return False
        self.score = (h, a)
        return True


def match_interested_in(match):
    """ Returns whether there's interest in the match
    :return True if interest exists, else False """
    # Conditions for interest:
    #   1. Competition is in UNFILTERED_COMPETITIONS
    #   2. Competition is in FILTERED_COMPETITIONS and
    #       2.1 has either one German team participating or 2.2 is late enough in the tournament to be interesting
    if match['competition']['name'] in UNFILTERED_COMPETITIONS: return True
    elif match['competition']['name'] in FILTERED_COMPETITIONS:
        if match['homeTeam']['country'] == "Deutschland" or match['awayTeam']['country'] == "Deutschland": return True
        if match['homeTeam']['country'] == "Germany" or match['awayTeam']['country'] == "Germany": return True
        match match['competition']['name']:
            case "Champions League": return match["roundType"] in ["ROUND_OF_16", "QUARTER_FINALS", "SEMI_FINALS",
                                                                   "FINAL"]
            case "Europa League": return match["roundType"] in ["QUARTER_FINALS", "SEMI_FINALS", "FINAL"]
            case "Conference League": return match["roundType"] in ["SEMI_FINALS", "FINAL"]
    else: return False


def create_schedule():
    """ Returns Schedule based on the starting time of that day's games """
    start_times = set()

    # Get data from site
    date_today = datetime.datetime.today().date()
    url = f"https://api.sport1.info/v2/de/live/soccer/liveMatchesBySport/date/{date_today}/appConfig/false"

    response = requests.request("GET", url, data=payload, headers=headers)
    log.write("Api-Call Football: " + url)
    try: data = response.json()
    except: return list(start_times)
    data = data['content']
    # Iterate over every league
    for league in data:
        # Filter by wanted leagues
        if league['matches'][0]['competition']['name'] not in COMPETITION_LIST: continue
        # Add match times to set
        for match in league['matches']:
            if not match_interested_in(match): continue
            time = datetime.datetime.fromisoformat(match['scheduledStartTime'].replace("Z", "+00:00"))
            time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
            start_times.add(time)

    start_times = sorted(start_times)
    return list(start_times)


def get_live():
    """ Returns a list of embeds - one for every league - with an embed for every game of that league """
    embeds = []
    one_game_still_live = False

    # Get data from site
    date_today = datetime.datetime.today().date()
    url = f"https://api.sport1.info/v2/de/live/soccer/liveMatchesBySport/date/{date_today}/appConfig/false"

    response = requests.request("GET", url, data=payload, headers=headers)
    log.write("Api-Call Football: " + url)
    data = response.json()
    data = data['content']

    # Iterate over every league
    for league in data:
        # Skip league if not one of the wanted ones
        league_name = league['matches'][0]['competition']['name']
        if league_name not in COMPETITION_LIST: continue
        # Iterate over every match in the league
        for match in league['matches']:
            if not match_interested_in(match): continue
            new = False
            # create Match if not in dict
            if (home := match["homeTeam"]["name"]) not in matches:
                game = Game(
                    start_time=match["scheduledStartTime"],
                    team1=home,
                    team2=match["awayTeam"]["name"],
                    team1_short=match["homeTeam"]["code"],
                    team2_short=match["awayTeam"]["code"]
                )
                league_matches[league_name].append(home)
                matches[home] = game
                new = True
            else: game = matches.get(home)

            score_change = game.set_goals(match.get("homeScore", 0), match.get("awayScore", 0))

            if "matchTime" in match["matchInfo"]: game.minute = match["matchInfo"]["matchTime"]
            if match["period"] == "FULL_TIME": game.done = True

            if "homePenaltyScore" in match and "awayPenaltyScore" in match:
                game.penalty_score = (match["homePenaltyScore"], match["awayPenaltyScore"])

            if (game.minute >= 0 and score_change) or (game.done and new):
                game.goals1, game.goals2 = get_match_goals(match["id"])

            if (match["isLive"] or (datetime.timedelta(minutes=0) < (datetime.datetime.now(pytz.utc) - game.start_time)
                                    < datetime.timedelta(minutes=45))): one_game_still_live = True

        embed = build_embed(league_name, league["matches"][0]["roundTitle"])
        if len(embed.fields) > 0: embeds.append(embed)

    return embeds, one_game_still_live


def get_match_goals(match_id):
    """ Get the match's goalscorers """
    # Get data from site
    url = f"https://api.sport1.info/v2/de/soccer/ticker/{match_id}"

    response = requests.request("GET", url, data=payload, headers=headers)
    log.write("Api-Call Football: " + url)
    match_info = response.json()

    goals1, goals2 = [], []

    id_home = match_info["match"]["homeTeam"]["id"]

    for goal in match_info["matchGoals"]:
        scorer = goal["player"].get("nickName", "") or goal["player"]["lastName"]
        goal_type = ""
        if goal['penalty']: goal_type = " (P)"
        elif goal['ownGoal']: goal_type = " (OG)"
        elif goal['soloRun']: goal_type = " (SR)"
        if goal['failed']: goal_type = " (F)"
        g_tuple = (goal["minute"], scorer, goal_type)

        if goal["teamId"] == id_home: goals1.append(g_tuple)
        else: goals2.append(g_tuple)

    return goals1, goals2


def build_embed(league_name, round_title):
    """ Returns an embed with all matches for the league """
    embed = interactions.Embed(title=f"{league_name} - {round_title}", color=COLOUR)

    def goals(g: tuple, v: str):
        return ("," if len(v) != 0 else "") + f" {g[0]}' {g[1]}" + (g[2] if g[2] else "")

    for m in league_matches[league_name]:
        game = matches[m]
        ...
        penalty_score = f" {game.penalty_score[0]}:{game.penalty_score[1]} nE" if game.penalty_score else ""
        name = f"{game.team1:<20} {game.score[0]:^3}:{game.score[1]:^4}{penalty_score} {game.team2:>20}"
        name = "`" + name + "`"  # "```cs\n" + name + "\n```"
        if game.minute < 0 and not game.done:
            value = "Startet um " + game.start_time.astimezone(pytz.timezone('Europe/Berlin')).replace(
                tzinfo=None).strftime("%H:%M") + " Uhr"
        else: value = "END " if game.done else f"{str(game.minute).zfill(2)}' "

        goals_home, goals_away = "", ""

        for g in game.goals1: goals_home += goals(g, goals_home)
        for g in game.goals2: goals_away += goals(g, goals_away)

        if not goals_home == "": goals_home = game.team1_short + ":" + goals_home
        if not goals_away == "": goals_away = game.team2_short + ":" + goals_away

        if goals_home == "" or goals_away == "": value += goals_home + goals_away
        else: value += goals_home + "\n" + " " * 4 + goals_away

        value = "```cs\n" + value + "\n```"

        embed.add_field(name, value)

    return embed
