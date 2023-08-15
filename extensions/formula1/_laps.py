import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from fastf1.core import Laps
from interactions.models import discord
from timple.timedelta import strftimedelta

""" All methods for the fastest command"""


# TODO Track Dominance https://github.com/F1-Buddy/f1buddy-python/blob/main/images/trackdominance.png
#                      https://github.com/F1-Buddy/f1buddy-python/blob/main/cogs/speed.py
# TODO Telemetry https://github.com/F1-Buddy/f1buddy-python/blob/main/images/telemetry.png
#                https://github.com/F1-Buddy/f1buddy-python/blob/main/cogs/telemetry.py

def overview_fastest_laps(year, gp, session):
    """ Returns an overview of the fastest laps """
    # We only want support for timedelta plotting in this
    fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None, misc_mpl_mods=False)

    # Load session
    session = fastf1.get_session(year, gp, session)
    session.load()

    # Get array of all drivers
    drivers = pd.unique(session.laps['Driver'])

    # Get each driver's fastest lap, create new laps object from these, sort them by lap time,
    # and have pandas reindex them to number them nicely by starting position
    list_fastest_laps = list()
    for drv in drivers:
        drvs_fastest_lap = session.laps.pick_driver(drv).pick_fastest()
        list_fastest_laps.append(drvs_fastest_lap)
    fastest_laps = Laps(list_fastest_laps).sort_values(by='LapTime').reset_index(drop=True)

    # More understandable if only time differences get plotted
    pole_lap = fastest_laps.pick_fastest()
    fastest_laps['LapTimeDelta'] = fastest_laps['LapTime'] - pole_lap['LapTime']

    # Create a list of team colours per lap to colour our plot
    team_colours = list()
    for index, lap in fastest_laps.iterlaps():
        colour = fastf1.plotting.team_color(lap['Team'])
        team_colours.append(colour)

    # Plot the data
    fig, ax = plt.subplots()
    ax.barh(fastest_laps.index, fastest_laps['LapTimeDelta'],
            color=team_colours, edgecolor='grey')
    ax.set_yticks(fastest_laps.index)
    ax.set_yticklabels(fastest_laps['Driver'])

    # show fastest at the top
    ax.invert_yaxis()

    # draw vertical lines behind the bars
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, which='major', linestyle='--', color='black', zorder=-1000)
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    # Give meaningful title
    lap_time_string = strftimedelta(pole_lap['LapTime'], '%m:%s.%ms')
    plt.suptitle(f"{session.event['EventName']} {session.event.year} Qualifying\n"
                 f"Fastest Lap: {lap_time_string} ({pole_lap['Driver']})")

    # Save the figure and let Discord load it
    plt.savefig('Resources/overview.png')
    file = discord.File("Resources/overview.png", file_name="image.png")

    return file


def compare_laps(year, gp, session, driver1, driver2):
    """ Returns an overlaying of the two driver's fastest laps """
    # enable some matplotlib patches for plotting timedelta values and load
    # FastF1's default color scheme
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    # Load a session and its telemetry data
    session = fastf1.get_session(year, gp, session)
    session.load()

    # Select the two laps to compare
    dr1_lap = session.laps.pick_driver(driver1).pick_fastest()
    dr2_lap = session.laps.pick_driver(driver2).pick_fastest()

    # Get telemetry data for each lap. Add 'Distance' column for easier comparison
    dr1_tel = dr1_lap.get_car_data().add_distance()
    dr2_tel = dr2_lap.get_car_data().add_distance()

    # Create plot and plot both speed traces. Colour lines according to the driver's team colours
    dr1_color = fastf1.plotting.driver_color(driver1)
    dr2_color = fastf1.plotting.driver_color(driver2)

    if dr1_color == dr2_color:
        table = str.maketrans("0123456789abcdef", "fedcba987654321")
        dr2_color = dr2_color.translate(table)

    fig, ax = plt.subplots()
    ax.plot(dr1_tel['Distance'], dr1_tel['Speed'], color=dr1_color, label=driver1)
    ax.plot(dr2_tel['Distance'], dr2_tel['Speed'], color=dr2_color, label=driver2)

    ax.set_xlabel('Distance in m')
    ax.set_ylabel('Speed in km/h')

    ax.legend()
    plt.suptitle(f"Fastest Lap Comparison \n "
                 f"{session.event['EventName']} {session.event.year} Qualifying")
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    # Save the figure and let Discord load it
    plt.savefig('Resources/compare.png')
    file = discord.File("Resources/compare.png", file_name="image.png")

    return file


def scatterplot(year, gp, session, driver):
    """ Returns a scatter plot of the driver's laps during the session """
    # The misc_mpl_mods option enables minor grid lines which clutter the plot
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    # Load session
    race = fastf1.get_session(year, gp, 'R')
    race.load()

    # Get all laps of a single driver. Filter out slow laps
    driver_laps = race.laps.pick_driver(driver).pick_quicklaps().reset_index()

    # Make scatterplot using lap number as x-axis and lap time as y-axis.
    # Marker colours correspond to the compound.
    fig, ax = plt.subplots(figsize=(8, 8))

    sns.scatterplot(data=driver_laps,
                    x="LapNumber",
                    y="LapTime",
                    ax=ax,
                    hue="Compound",
                    palette=fastf1.plotting.COMPOUND_COLORS,
                    s=80,
                    linewidth=0,
                    legend='auto')

    # Make it more aesthetic
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time")
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    # The y-axis increases from bottom to top by default
    # Since we are plotting time, it makes sense to invert the axis
    ax.invert_yaxis()
    plt.suptitle(f"{driver} Laptimes in the {year} {session.event['EventName']}")

    # Turn on major grid lines
    plt.grid(color='w', which='major', axis='both')
    sns.despine(left=True, bottom=True)

    plt.tight_layout()
    # Save the figure and let Discord load it
    plt.savefig('Resources/sp.png')
    file = discord.File("Resources/sp.png", file_name="image.png")

    return file
