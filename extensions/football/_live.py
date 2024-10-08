import datetime

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
    log.write("Api-Call Football: " + url)
    data = response.json()
    data = data['content']

    # Iterate over every league
    for league in data:
        # Skip league if not one of the wanted ones
        league_name = league['matches'][0]['competition']['name']
        if league_name not in COMPETITION_LIST: continue
        embed = interactions.Embed(title=f"{league_name} - {league['matches'][0]['roundTitle']}", color=COLOUR)
        # Iterate over every match in the league
        for match in league['matches']:
            if not match_interested_in(match): continue
            team1 = germanise(match['homeTeam']['name'])
            team2 = germanise(match['awayTeam']['name'])
            # Goals
            score1 = 0
            score2 = 0
            if 'homeScore' in match: score1 = match['homeScore']
            if 'awayScore' in match: score2 = match['awayScore']
            # Game starting time
            start_time = datetime.datetime.fromisoformat(match['scheduledStartTime'].replace("Z", "+00:00"))
            time = start_time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None).strftime("%H:%M")
            minute = "Startet um " + time + " Uhr"
            # If match has begun, get the minutes
            if 'matchTime' in match['matchInfo'] and match['isLive']:
                minute = str(match['matchInfo']['matchTime']) + "' "
            # If match has ended, put in the END
            if match['period'] == "FULL_TIME": minute = "END "
            # If match has gone to the penalties, add the score after the penalties after the normal score
            penalty_score = ""
            if 'homePenaltyScore' in match and 'awayPenaltyScore' in match:
                penalty_score = f" {match['homePenaltyScore']}:{match['awayPenaltyScore']} nE"
            # Put in Values
            new_name = f"```{team1:<20} {score1:^3}:{score2:^4}{penalty_score} {team2:>20}```"
            new_value = f"```{str(minute).zfill(2)}```"
            # If the score changes in the new message, get the goalscorers and put them as the new value
            if not content == "" and not minute.startswith("Startet"):
                old_embed = content[0]
                for em in content[1:]:  # Get correct embed
                    if em.title == embed.title: old_embed = em
                old = old_embed.fields[0]
                for field in old_embed.fields[1:]:  # Get correct field
                    if field.name[0:20] == new_name[0:20]: old = field
                # Get the match's goalscorers if a goal happened (old and new names differ)
                # or the score doesn't align with the amount of goalscorers
                count = old.value.count("'")  # Counts amount of ' to get the amount of goals
                if "'" in minute: count -= 1  # Reduce count by one if the game time has one '
                if new_name != old.name or (score1 + score2) != count:
                    new_value = new_value.split(' ')[0] + get_match_goals(match['id'])
                else:
                    new_value = new_value.split(' ')[0] + " " + ' '.join(old.value.split(' ')[1:])
            embed.add_field(name=new_name, value=new_value)
            # To ensure a delayed start (max 45 min) won't turn off the live games
            if (match['isLive'] or (datetime.timedelta(minutes=0) < (datetime.datetime.now(pytz.utc) - start_time)
                                    < datetime.timedelta(minutes=45))): one_game_still_live = True
        if len(embed.fields) > 0: embeds.append(embed)  # Add to list if not empty

    return embeds, one_game_still_live


def get_match_goals(match_id):
    """ Get the match's goalscorers """
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
    log.write("Api-Call Football: " + url)
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
    if goals_home == "":
        return_string += goals_away
    elif goals_away == "":
        return_string += goals_home
    else:
        return_string += goals_home + "\n" + " " * 4 + goals_away
    return_string += "```"
    return return_string
