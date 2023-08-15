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
    sess.load()
    results = sess.results

    ranking = "```"
    ranking += "#".ljust(3) + "Name".center(20)
    if session == "Q" or "SS":
        ranking += "Zeit".rjust(10) + "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            position = int(place['Position'])
            ranking += str(position).ljust(3)
            ranking += place['FullName'].center(20)
            time = place['Q3']
            if position > 10: time = place['Q2']
            elif position > 15: time = place['Q1']
            ranking += str(time)[11:19].rjust(10)
            ranking += "\n"
    elif session == "R" or "S":
        ranking += "Punkte".rjust(10) + "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            ranking += str(int(place['Position'])).ljust(3)
            ranking += place['FullName'].center(20)
            ranking += place['Points'].rjust(10)
            ranking += "\n"
    else:
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            ranking += str(int(place['Position'])).ljust(3)
            ranking += place['FullName'].center(20)
            ranking += "\n"

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
                               description=f"Round {round_number}: {official_name}\nin {location}, {country}")
    sessions = ""
    sessions += ((next_event['Session1'] + ":").ljust(20) + str(
        next_event['Session1Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)).rjust(20)) + "\n"
    sessions += ((next_event['Session2'] + ":").ljust(20) + str(
        next_event['Session2Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)).rjust(20)) + "\n"
    sessions += ((next_event['Session3'] + ":").ljust(20) + str(
        next_event['Session3Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)).rjust(20)) + "\n"
    sessions += ((next_event['Session4'] + ":").ljust(20) + str(
        next_event['Session4Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)).rjust(20)) + "\n"
    sessions += ((next_event['Session5'] + ":").ljust(20) + str(
        next_event['Session5Date'].astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)).rjust(20)) + "\n"

    embed.add_field(name="Sessions", value=sessions)

    url = f"https://www.formula1.com/en/racing/{CURRENT_SEASON}.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    image = soup.find_all('picture', {'class': 'track'})
    image_url = image[next_event].find('img')['data-src']

    embed.set_image(url=image_url)

    return util.uwuify_by_chance(embed)


def remaining_races():
    """ Returns the seasons remaining races """
    event_schedule = fastf1.get_events_remaining()
    events = "```"
    events += "Rennen".ljust(3) + "Land".center(20) + "Ort".center(20) + "Uhrzeit".rjust(20)
    for i, _ in enumerate(event_schedule.iterrows()):
        event = event_schedule.iloc[i]
        events += str(event['RoundNumber']).ljust(3)
        events += event['Country'].center(20)
        events += event['Location'].center(20)
        time = datetime.datetime.fromisoformat(str(event['Session5Date']))
        time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        events += str(time).rjust(20)
        events += "\n"

    events += "```"
    return util.uwuify_by_chance(events)
