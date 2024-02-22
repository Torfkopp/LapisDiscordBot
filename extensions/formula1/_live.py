import datetime
import random

import fastf1
import interactions
import pytz
import requests

import extensions.formula1._no_group as no_group
import util
from core import log

COLOUR = util.Colour.FORMULA1.value
payload = ""  # Payload for the sport1 api
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
}  # Headers for the sport1 api
result_url = None  # Is set when auto_result is called but the session isn't finished yet


def get_current():
    """ Gets the current gp and session """
    event_schedule = fastf1.get_events_remaining()
    if len(event_schedule) == 0:  # If no remaining races, set next_event to last race
        next_event = fastf1.get_event(util.CURRENT_F1_SEASON,
                                      len(fastf1.get_event_schedule(util.CURRENT_F1_SEASON))-1)
    else:
        next_event = event_schedule.iloc[0]
        if next_event['RoundNumber'] == 0: next_event = event_schedule.iloc[1]
    date_today = datetime.datetime.today()

    # FastF1's remaining events removes an event somewhere between Saturday and Sunday during the race weekend
    # If today is Sat/Sun and the next event's date is further away than 3 days, then
    if date_today.weekday() >= 4 and next_event['EventDate'] > date_today + datetime.timedelta(days=3):
        temp_event = fastf1.get_event(date_today.year, next_event['RoundNumber'] - 1)
        # If the event before the first remaining event is within two days, set it as current event
        if (temp_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
            < date_today + datetime.timedelta(days=3)): next_event = temp_event

    session_list = [next_event['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session2Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session3Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session4Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
                    next_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)]

    latest_finished_session = 0
    for i in range(0, len(session_list)):  # A session should be finished 1.5 hours after the start
        if session_list[i] + datetime.timedelta(hours=1.5) <= date_today: latest_finished_session = i + 1

    # Set current_gp and session to the latest race
    current_gp = next_event['RoundNumber'] - 1
    current_session = 5

    # If one session of the 'next event' has finished,
    # set the next_event as current_gp and the finished session as current_session
    if latest_finished_session > 0:
        current_gp = next_event['RoundNumber']
        current_session = latest_finished_session

    return current_gp, current_session


def f1_info():
    """ Returns an embed with additional info """
    embed = None

    date_today = datetime.datetime.today()
    event_schedule = fastf1.get_events_remaining()
    if len(event_schedule) == 0: return embed
    first_session_date = event_schedule.iloc[0]['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(
        tzinfo=None)

    # When it's monday on a race week, send bad meme
    if (date_today.weekday() == 0) and ((first_session_date - date_today).days < 7):
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
    if (date_today.weekday() == 4) and ((first_session_date.date() - date_today.date()) == datetime.timedelta(days=0)):
        embed = no_group.next_race()

    return embed


def create_schedule():
    """ Returns today's formula1 sessions """
    date_today = datetime.datetime.today()
    event_schedule = fastf1.get_events_remaining()
    if len(event_schedule) == 0:  # If no remaining races, set next_event to last race
        next_event = fastf1.get_event(util.CURRENT_F1_SEASON,
                                      len(fastf1.get_event_schedule(util.CURRENT_F1_SEASON)) - 1)
    else:
        next_event = event_schedule.iloc[0]
        if next_event['RoundNumber'] == 0: next_event = event_schedule.iloc[1]

    # FastF1's remaining events removes an event somewhere between Saturday and Sunday during the race weekend
    # If today is Sat/Sun and the next event's date is further away than 3 days, then
    if date_today.weekday() >= 4 and next_event['EventDate'] > date_today + datetime.timedelta(days=3):
        temp_event = fastf1.get_event(date_today.year, next_event['RoundNumber'] - 1)
        # If the event before the first remaining event is within two days, set it as current event
        if (temp_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
            < date_today + datetime.timedelta(days=3)): next_event = temp_event

    session_map = {
        next_event['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None):
            next_event['Session1'],
        next_event['Session2Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None):
            next_event['Session2'],
        next_event['Session3Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None):
            next_event['Session3'],
        next_event['Session4Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None):
            next_event['Session4'],
        next_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None):
            next_event['Session5']}

    return {date: session_map.get(date) for date in session_map.keys() if date.date() == date_today.date()}


def _get_result_url():
    """ Gets the url for the session to get the result from """
    url = ("https://api.sport1.info/v2/de/motorsport/sport/sr:stage:7668/season/sr:stage:1031201"
           "/minSportEventsWithSessions")
    try:
        log.write("API Call Formula1: " + url)
        response = requests.request("GET", url, data=payload, headers=headers)
        response = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("JSONDecodeError; API may be down")
        return

    current_comp_id = response['currentCompetitionId']
    current_match_id = ""
    for compo in response['competitions']:
        if compo['id'] == current_comp_id: current_match_id = compo['currentMatchId']

    url = f"https://api.sport1.info/v2/de/motorsport/sport/sr:stage:7668/match/{current_match_id}"
    return url


def _make_result(response):
    """
    :param response: The response of the api
    :return: The result
    """
    result = "```"
    live = "Live" if response['isLive'] else "Ergebnis"
    result += f"{live} - {util.germanise(response['competition']['name'])} - {response['roundTitle']}" + "\n"
    result += "\n"
    result += "#".ljust(6) + "Name".center(20)
    if response['roundType'] == "RACE" or response['roundType'] == "SPRINT":
        result += "Gesamt".center(14) + "Schnellste".center(14) + "P".rjust(3) + "\n"
        for position in response['results']:
            if 'position' not in position: continue
            result += str(position['position']).ljust(6)
            result += f"{position['person']['firstName']} {position['person']['lastName']}".center(20)

            if 'status' in position and position['status'] != "FINISHED": result += position['status'].center(14)
            else:
                if 'time' in position:
                    result += str(position['time']).center(14)

            if 'fastestLap' in position: result += str(position['fastestLap']).center(14)
            else: result += " ".center(14)

            result += str(position['pitStopCount']).rjust(3) if 'pitStopCount' in position else " "
            result += "\n"
    elif response['roundType'] == "QUALIFYING" or response['roundType'] == "SPRINT_SHOOTOUT":
        result += "Schnellste".center(20) + "\n"
        for position in response['results']:
            if 'position' not in position: continue
            result += str(position['position']).ljust(6)
            result += f"{position['person']['firstName']} {position['person']['lastName']}".center(20)
            result += str(position['fastestLap']).center(20) if 'fastestLap' in position else " "
            result += "\n"
    else:
        result += "Schnellste".center(20) + "Stops".rjust(3) + "\n"
        for position in response['results']:
            if 'position' not in position: continue
            result += str(position['position']).ljust(6)
            result += f"{position['person']['firstName']} {position['person']['lastName']}".center(20)
            result += str(position['fastestLap']).center(20) if 'fastestLap' in position else " "
            result += str(position['pitStopCount']).rjust(3) if 'pitStopCount' in position else " "
            result += "\n"

    result += "```"
    result = "||" + result + "||"  # Make Spoiler
    return result


def auto_result(result_only: bool):
    """ Returns the result of the latest session and sets the current paras to it """
    global result_url  # If result_url is set, use it, else get the url of the current session
    url = result_url if result_url else _get_result_url()
    try:
        log.write("API Call Formula1: " + url)
        response = requests.request("GET", url, data=payload, headers=headers)
        response = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("JSONDecodeError; API may be down")
        return None, False  #

    result_url = url  # set result_url since the current_match pointer gets set immediately after session finish

    # If only the result is wanted and the session is still in progress, don't create the result text
    if result_only and response['period'] != "FULL_TIME": return None, True
    if response['period'] == "FULL_TIME": result_url = None  # Reset the result_url if a session ends

    return util.uwuify_by_chance(_make_result(response)), response['period'] != "FULL_TIME"
