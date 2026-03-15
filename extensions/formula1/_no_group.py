import fastf1
import interactions
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup
from fastf1.core import Laps
from tabulate import tabulate

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
    ranking = f"Results {year} {sess.event['EventName']} {sess.name}\n".center(30)


    if sess.name == "Qualifying":
        results = sess.results[[
            "Position",
            "BroadcastName",
            "Q1",
            "Q2",
            "Q3",
        ]]

        def format_time(td):
            return f"{td.seconds//60}:{(td.seconds%60 + td.microseconds/1e6):06.3f}" if not pd.isnull(td) else ""

        results["Q1"] = results["Q1"].apply(format_time)
        results["Q2"] = results["Q2"].apply(format_time)
        results["Q3"] = results["Q3"].apply(format_time)

        table = tabulate(
            results.values,
            headers=["#", "Name", "Q1", "Q2", "Q3"],
            tablefmt="mixed_outline"
        )
    elif sess.name == "Race" or sess.name == "Sprint":
        results = sess.results[[
            "Position",
            "BroadcastName",
            "Time",
            "Status",
            "Points"
        ]]

        def format_time(td):
            if pd.isna(td): return ""
            c = td.components
            if td >= pd.Timedelta(hours=1): return f"{c.hours}:{c.minutes:02d}:{c.seconds:02d}.{c.milliseconds:03d}"
            return f"+{c.minutes:02d}:{c.seconds:02d}.{c.milliseconds:03d}"

        results["Time"] = results["Time"].apply(format_time)

        table = tabulate(
            results.values,
            headers=["#", "Name", "Time", "Status", "P"],
            tablefmt="mixed_outline",
            colalign=["right", "left", "right", "center", "right"],
            headersglobalalign="center"
        )
    else:
        def format_time(td):
            return f"{td.seconds//60}:{(td.seconds%60 + td.microseconds/1e6):06.3f}" if not pd.isnull(td) else ""

        results = sess.results[[
            "Position",
            "Abbreviation",
            "BroadcastName",
        ]]
        
        table = []

        for i, v in enumerate(results.itertuples(), 1):
            d = [i]
            d.append(v[3])
            fastest_lap = sess.laps.pick_drivers(v[2]).pick_fastest()
            if not fastest_lap.isnull().sum() == len(fastest_lap.values):
                d.append(format_time(fastest_lap.LapTime))
                d.append(fastest_lap.Compound)
            else:
                d.append("")
                d.append("")
            table.append(d)
        
        table = tabulate(
            table,
            headers=["#", "Name", "Time", "Tyre"],
            tablefmt="mixed_outline",
            colalign=["right", "center", "left", "right", "center"],
            headersglobalalign="center"
        )

    ranking = "```python\n" + ranking + table + "\n```"

    return ranking


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
        url = f"https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/{country}_Circuit.webp"
        response = requests.get(url)
        if not response.ok:
            url = f"https://www.formula1.com/en/racing/{CURRENT_SEASON}.html"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            div = soup.find("div", attrs={
                "class": "relative z-0 w-full min-h-[300px] @[738px]/cards:min-h-[230px] rounded-m overflow-hidden bg-accent-bright-blue-50 flex items-stretch"})
            circuit = div.find("p").text
            if circuit == "Azerbaijan": circuit = "Baku"
            elif circuit == "United States": circuit = "USA"
            else: circuit = circuit.replace(" ", "_").replace("-", "_")
            url = f"https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/{circuit}_Circuit.webp"
        embed.set_image(url)
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
