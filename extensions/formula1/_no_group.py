import fastf1
import interactions
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup
from fastf1.core import Laps

import util
from core import log

""" All methods for commands without group"""

COLOUR = util.Colour.FORMULA1.value
CURRENT_SEASON = util.CURRENT_F1_SEASON


def result(year, gp, session):
    """ Returns the result of the specified session """
    sess = fastf1.get_session(year, gp, session)
    log.write("FastF1: " + str(sess))
    sess.load(weather=False)
    results = sess.results
    ranking = f"Results {year} {sess.event['EventName']} {sess.name}\n".center(30)
    ranking += "\n"
    ranking += "#".ljust(6) + "Name".center(20)
    if sess.name == "Qualifying":
        ranking += "Zeit".center(12) + "QX".rjust(6) + "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            try: position = int(place['Position'])
            except ValueError: position = int(i) + 1
            ranking += str(position).ljust(6)
            ranking += place['FullName'].center(20)
            q = "Q3"
            if position > 10: q = "Q2"
            if position > 15: q = "Q1"
            time = place[q]
            ranking += str(time)[11:19].center(12)
            ranking += q.rjust(6)
            ranking += "\n"
    elif sess.name == "Race" or sess.name == "Sprint":
        ranking += "Zeit".center(12) + "Punkte".rjust(8) + "\n"
        for i, _ in enumerate(results.iterrows()):
            place = results.iloc[i]
            try: position = int(place['Position'])
            except ValueError: position = int(i) + 1
            ranking += str(position).ljust(6)
            ranking += place['FullName'].center(20)
            time = place['Time']
            if time is pd.NaT: time = place['Status']
            else: time = str(time)[7:15]
            ranking += time.center(12)
            ranking += str(place['Points']).rjust(8)
            ranking += "\n"
    else:
        ranking += "Zeit".center(12) + "Mischung".rjust(8) + "\n"

        driver_map = {results.iloc[i]['Abbreviation']: results.iloc[i]['FullName'] for i, _ in
                      enumerate(results.iterrows())}
        list_fastest_laps = list()
        for drv in pd.unique(sess.laps['Driver']):
            drvs_fastest_lap = sess.laps.pick_driver(drv).pick_fastest()
            # It can happen that a driver has no fastest lap; this prevents the resulting error
            if drvs_fastest_lap.isnull().sum() == len(drvs_fastest_lap.values): continue
            list_fastest_laps.append(drvs_fastest_lap)
        fastest_laps = Laps(list_fastest_laps).sort_values(by='LapTime').reset_index(drop=True)

        for i in fastest_laps.itertuples():
            ranking += str(i[0] + 1).ljust(6)
            ranking += driver_map.get(i.Driver).center(20)
            ranking += str(i.LapTime)[11:19].center(12)
            ranking += i.Compound.rjust(8)
            ranking += "\n"

    ranking = "```python\n" + ranking + "```"
    return util.uwuify_by_chance(ranking)


def next_race():
    event_schedule = fastf1.get_events_remaining()
    log.write("FastF1: Remaining events")
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

    sessions = "```\n"
    for i in range(0, len(session_list)):
        session = str(session_list[i]).split()  # Split to get the date and time separately
        sessions += ((next_event[f"Session{i + 1}"] + ":").ljust(16)
                     + session[0].center(12) + session[1].rjust(12)) + "\n"

    sessions += "```"

    embed.add_field(name="Sessions", value=sessions)
    try:
        url = f"https://www.formula1.com/en/racing/{CURRENT_SEASON}.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        image = soup.find_all("img", {"class": "f1-c-image h-full w-full object-contain"})
        image_url = image[0]["src"]
        image_url = image_url.replace(" ", "%20")
        embed.set_image(url=image_url)
    except: ...

    return util.uwuify_by_chance(embed)


def remaining_races():
    """ Returns the seasons remaining races """
    event_schedule = fastf1.get_events_remaining()
    log.write("FastF1: Remaining Events")
    events = "```"
    events += "R#".ljust(3) + "Land".center(15) + "Ort".center(15) + "Uhrzeit".rjust(20) + "\n"
    for i, _ in enumerate(event_schedule.iterrows()):
        event = event_schedule.iloc[i]
        events += str(event['RoundNumber']).ljust(3)
        events += event['Country'].center(15)
        events += event['Location'].center(15)
        time = event['Session5Date']
        time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
        events += str(time).rjust(20)
        events += "\n"

    events += "```"
    return util.uwuify_by_chance(events)
