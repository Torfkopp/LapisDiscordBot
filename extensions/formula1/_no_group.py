import datetime

import fastf1
import interactions
import pytz
import requests
from bs4 import BeautifulSoup

import util

""" All methods for commands without group"""

COLOUR = util.FORMULA1_COLOUR
CURRENT_SEASON = util.CURRENT_F1_SEASON


def result(year, gp, session):
    """ Returns the result of the specified session """
    sess = fastf1.get_session(year, gp, session)
    sess.load(laps=False, telemetry=False, weather=False, messages=False, livedata=None)
    results = sess.results

    ranking = "```"
    ranking += f"Results {year} {sess.event['EventName']} {sess.name}\n".center(30)
    ranking += "\n"
    ranking += "#".ljust(6) + "Name".center(20)
    if sess.name == "Qualifying":
        ranking += "Zeit".rjust(12) + "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            position = int(place['Position'])
            ranking += str(position).ljust(6)
            ranking += place['FullName'].center(20)
            time = place['Q3']
            if position > 10: time = place['Q2']
            if position > 15: time = place['Q1']
            ranking += str(time)[11:19].rjust(12)
            ranking += "\n"
    elif sess == "Race" or sess == "Sprint":
        ranking += "Punkte".rjust(8) + "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            ranking += str(int(place['Position'])).ljust(6)
            ranking += place['FullName'].center(20)
            ranking += str(place['Points']).rjust(8)
            ranking += "\n"
    else:
        ranking += "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            ranking += str(i).ljust(6)
            ranking += place['FullName'].center(20)
            ranking += "\n"

    ranking += "```"
    return util.uwuify_by_chance(ranking)


def next_race():
    event_schedule = fastf1.get_events_remaining()
    next_event = event_schedule.iloc[0]

    round_number = next_event['RoundNumber']
    official_name = next_event['OfficialEventName']
    event_name = next_event['EventName']
    country = next_event['Country']
    location = next_event['Location']

    embed = interactions.Embed(title=f"Race Schedule {event_name}", color=COLOUR,
                               description=f"Round {round_number}:\n {official_name}\nin {location}, {country}")

    session_list = [
        next_event['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
        next_event['Session2Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
        next_event['Session3Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
        next_event['Session4Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None),
        next_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
    ]

    sessions = "```"
    for i in range(0, len(session_list)):
        session = str(session_list[i]).split()  # Split to get the date and time separately
        sessions += ((next_event[f"Session{i + 1}"] + ":").ljust(16)
                     + session[0].center(12) + session[1].rjust(12)) + "\n"

    sessions += "```"

    embed.add_field(name="Sessions", value=sessions)

    url = f"https://www.formula1.com/en/racing/{CURRENT_SEASON}.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    image = soup.find_all('picture', {'class': 'track'})
    image_url = image[round_number].find('img')['data-src']

    embed.set_image(url=image_url)

    return util.uwuify_by_chance(embed)


def remaining_races():
    """ Returns the seasons remaining races """
    event_schedule = fastf1.get_events_remaining()
    events = "```"
    events += "R#".ljust(3) + "Land".center(15) + "Ort".center(15) + "Uhrzeit".rjust(20) + "\n"
    for i, _ in enumerate(event_schedule.iterrows()):
        event = event_schedule.iloc[i]
        events += str(event['RoundNumber']).ljust(3)
        events += event['Country'].center(15)
        events += event['Location'].center(15)
        time = datetime.datetime.fromisoformat(str(event['Session5Date']))
        time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        events += str(time).rjust(20)
        events += "\n"

    events += "```"
    return util.uwuify_by_chance(events)
