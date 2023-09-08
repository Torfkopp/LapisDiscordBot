import fastf1
import fastf1.plotting
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from fastf1.core import Laps
from interactions.models import discord
from timple.timedelta import strftimedelta

import util
from core import log

""" All methods for the fastest command"""
matplotlib.rcParams['font.family'] = 'Formula1'


def overview_fastest_laps(year, gp, session):
    """ Returns an overview of the fastest laps """
    # We only want support for timedelta plotting in this
    # noinspection PyTypeChecker
    fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None, misc_mpl_mods=False)

    # Load session
    session = fastf1.get_session(year, gp, session)
    log.write("FastF1: " + session)
    session.load(weather=False, messages=False)

    # Get array of all drivers
    drivers = pd.unique(session.laps['Driver'])

    # Get each driver's fastest lap, create new laps object from these, sort them by lap time,
    # and have pandas reindex them to number them nicely by starting position
    list_fastest_laps = list()
    for drv in drivers:
        drvs_fastest_lap = session.laps.pick_driver(drv).pick_fastest()
        # It can happen that a driver has no fastest lap; this prevents the resulting error
        if drvs_fastest_lap.isnull().sum() == len(drvs_fastest_lap.values): continue
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
    bars = ax.barh(fastest_laps.index, fastest_laps['LapTimeDelta'], color=team_colours)
    # Put Delta on the right side of the graph
    max_width = 0
    for bar in bars:
        if bar.get_width() > max_width: max_width = bar.get_width()
    text_position = max_width + 0.000001
    for i in range(len(bars)):
        string = strftimedelta(fastest_laps['LapTimeDelta'][i], '+%s.%ms')
        if string == "+00.000": string = "Pole"
        plt.text(text_position, bars[i].get_y() + (bars[i].get_height() / 2), string, color="white", va="center")

    ax.set_yticks(fastest_laps.index)
    ax.set_yticklabels(fastest_laps['Driver'])
    ax.minorticks_off()
    # show fastest at the top
    ax.invert_yaxis()

    # draw vertical lines behind the bars
    # ax.set_axisbelow(True)
    # ax.xaxis.grid(True, which='major', linestyle='--', color='black', zorder=-1000)
    fig.set_facecolor('black')
    ax.set_facecolor('black')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Give meaningful title
    lap_time_string = strftimedelta(pole_lap['LapTime'], '%m:%s.%ms')
    plt.xlabel("Delta")
    plt.suptitle(f"{session.event['EventName']} {session.event.year} {session.name}\n"
                 f"Fastest Lap: {lap_time_string} ({pole_lap['Driver']})")

    # Save the figure and let Discord load it
    plt.savefig('formula1/overview.png', bbox_inches='tight')
    file = discord.File("formula1/overview.png", file_name="image.png")

    return file


def compare_laps(year, gp, session, driver1, driver2):
    """ Returns an overlaying of the two driver's fastest laps """
    # enable some matplotlib patches for plotting timedelta values and load
    # FastF1's default color scheme
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    # Load a session and its telemetry data
    session = fastf1.get_session(year, gp, session)
    log.write("FastF1: " + session)
    session.load(weather=False, messages=False)

    # Select the two laps to compare
    dr1_lap = session.laps.pick_driver(driver1).pick_fastest()
    dr2_lap = session.laps.pick_driver(driver2).pick_fastest()

    # Get telemetry data for each lap. Add 'Distance' column for easier comparison
    dr1_tel = dr1_lap.get_car_data().add_distance()
    dr2_tel = dr2_lap.get_car_data().add_distance()

    # Create plot and plot both speed traces. Colour lines according to the driver's team colours
    try: dr1_color = fastf1.plotting.driver_color(driver1)
    except KeyError: dr1_color = util.random_colour_generator()
    try: dr2_color = fastf1.plotting.driver_color(driver2)
    except KeyError: dr2_color = util.random_colour_generator()

    if dr1_color == dr2_color:
        table = str.maketrans("0123456789abcdef", "fedcba987654321")
        dr2_color = dr2_color.translate(table)

    fig, ax = plt.subplots()
    dr1_lap_time = strftimedelta(dr1_lap['LapTime'], '%m:%s.%ms')
    dr2_lap_time = strftimedelta(dr2_lap['LapTime'], '%m:%s.%ms')
    ax.plot(dr1_tel['Distance'], dr1_tel['Speed'], color=dr1_color, label=f"{driver1} {dr1_lap_time: >10}")
    ax.plot(dr2_tel['Distance'], dr2_tel['Speed'], color=dr2_color, label=f"{driver2} {dr2_lap_time: >10}")

    ax.set_xlabel('Distance in m')
    ax.set_ylabel('Speed in km/h')

    ax.legend()
    plt.suptitle(f"Fastest Lap Comparison \n "
                 f"{session.event['EventName']} {session.event.year} {session.name}")
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    # Save the figure and let Discord load it
    plt.savefig('formula1/compare.png')
    file = discord.File("formula1/compare.png", file_name="image.png")

    return file


def scatterplot(year, gp, session, driver):
    """ Returns a scatter plot of the driver's laps during the session """
    # The misc_mpl_mods option enables minor grid lines which clutter the plot
    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    # Load session
    race = fastf1.get_session(year, gp, 'R')
    log.write("FastF1: " + session)
    race.load(weather=False, messages=False)

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
    plt.suptitle(f"{driver} Laptimes in the {year} {race.event['EventName']}")

    # Turn on major grid lines
    plt.grid(color='w', which='major', axis='both')
    sns.despine(left=True, bottom=True)

    plt.tight_layout()
    # Save the figure and let Discord load it
    plt.savefig('formula1/sp.png')
    file = discord.File("formula1/sp.png", file_name="image.png")

    return file


def telemetry(year, gp, session, driver1, driver2):
    """ Return a file with telemetry graphs """
    # pyplot setup
    fastf1.plotting.setup_mpl()

    fig, ax = plt.subplots(3, figsize=(13, 9))
    fig.set_facecolor('black')
    plt.xlabel('Lap Percentage', weight='bold', labelpad=10)
    ax[1].set_ylim([0, 105])
    # ax[0].set_ylim([0, 360])
    ax[2].set_ylim([0, 1.1])
    ax[0].set_facecolor('black')
    ax[1].set_facecolor('black')
    ax[2].set_facecolor('black')
    plt.subplots_adjust(left=0.07, right=0.98, top=0.89, hspace=0.8)

    race = fastf1.get_session(year, gp, session)
    log.write("FastF1: " + session)
    race.load(laps=True, telemetry=True, weather=False, messages=False)

    d1_laps = race.laps.pick_driver(driver1)
    d1_fastest = d1_laps.pick_fastest()
    d1_number = d1_laps.iloc[0].loc['DriverNumber']
    d1_name = driver1

    d2_laps = race.laps.pick_driver(driver2)
    d2_fastest = d2_laps.pick_fastest()
    d2_number = d2_laps.iloc[0].loc['DriverNumber']
    d2_name = driver2
    d1_fl = (race.laps.pick_driver(d1_number).pick_fastest()["LapTime"])
    d2_fl = (race.laps.pick_driver(d2_number).pick_fastest()["LapTime"])

    throttle_string = ""
    brake_string = ""

    # get lap telemetry
    d1_tel = d1_fastest.get_telemetry()
    d2_tel = d2_fastest.get_telemetry()

    # set graph limit based on data
    ax[0].set_ylim([0, max(max(d1_tel['Speed']), max(d2_tel['Speed'])) + 10])

    # get maximum index of dataframe
    d1_max_index = max(d1_tel.index)
    d2_max_index = max(d2_tel.index)

    # convert (probably) mismatched dataframe indices to a scale of 0 to 1
    d1_index_list = (d1_tel.index / d1_max_index).to_list()
    d2_index_list = (d2_tel.index / d2_max_index).to_list()

    # get speed, throttle, and brake data
    d1_speed_list = d1_tel['Speed'].to_list()
    d2_speed_list = d2_tel['Speed'].to_list()

    d1_throttle_list = d1_tel['Throttle'].to_list()
    d2_throttle_list = d2_tel['Throttle'].to_list()

    d1_brake_list = d1_tel['Brake'].to_list()
    d2_brake_list = d2_tel['Brake'].to_list()

    # get driver color
    if year == util.CURRENT_F1_SEASON:
        try: d1_color = fastf1.plotting.driver_color(d1_name)
        except KeyError: d1_color = util.random_colour_generator()
        try: d2_color = fastf1.plotting.driver_color(d2_name)
        except KeyError: d2_color = util.random_colour_generator()
    else:
        d1_color = f"#{race.results.loc[str(d1_number), 'TeamColor']}"
        d2_color = f"#{race.results.loc[str(d2_number), 'TeamColor']}"

    if d1_color == d2_color:
        table = str.maketrans("0123456789abcdef", "fedcba987654321")  # Colour switcheroo
        d2_color = d2_color.translate(table)
        # d2_color = 'white'

    # graph labelling
    ax[2].set_yticks(ticks=[0, 1], labels=['Off', 'On'])
    ax[0].set_ylabel('Speed (km/h)', labelpad=8)
    ax[0].set_title("Speed", weight='bold', fontsize=15)
    ax[1].set_ylabel('Throttle %', labelpad=8)
    ax[1].set_title("Throttle", weight='bold', fontsize=15)
    ax[2].set_title("Brake", weight='bold', fontsize=15)

    # plot the data
    ax[0].plot(d1_index_list, d1_speed_list, color=d1_color)
    ax[0].plot(d2_index_list, d2_speed_list, color=d2_color)

    ax[1].plot(d1_index_list, d1_throttle_list, color=d1_color)
    ax[1].plot(d2_index_list, d2_throttle_list, color=d2_color)

    ax[2].plot(d1_index_list, d1_brake_list, color=d1_color)
    ax[2].plot(d2_index_list, d2_brake_list, color=d2_color)

    total = len(d1_tel)
    for i in range(3):
        ax[i].xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1, decimals=0))
        ax[i].xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(base=0.1))
        ax[i].set_xlim([0, 1])
        # for label in ax[i].get_xticklabels(): label.set_fontproperties('normal')
        for label in ax[i].get_yticklabels(): label.set_weight('bold')

    d1_throttle_percent = 0
    d2_throttle_percent = 0
    d1_brake_percent = 0
    d2_brake_percent = 0

    for c in (set(d1_tel.index) | set(d2_tel.index)):
        if c in d1_tel.index:
            if d1_tel.loc[c, 'Throttle'] >= 99: d1_throttle_percent += 1
            if d1_tel.loc[c, 'Brake'] == 1: d1_brake_percent += 1
        if c in d2_tel.index:
            if d2_tel.loc[c, 'Throttle'] >= 99: d2_throttle_percent += 1
            if d2_tel.loc[c, 'Brake'] == 1: d2_brake_percent += 1

    d1_throttle_percent = d1_throttle_percent / total * 100
    d2_throttle_percent = d2_throttle_percent / total * 100
    d1_brake_percent = d1_brake_percent / total * 100
    d2_brake_percent = d2_brake_percent / total * 100

    throttle_string += f"{d1_name} was on full throttle for {d1_throttle_percent:.2f}% of the lap\n"
    throttle_string += f"{d2_name} was on full throttle for {d2_throttle_percent:.2f}% of the lap\n"
    brake_string += f"{d1_name} was on brakes for {d1_brake_percent:.2f}% of the lap\n"
    brake_string += f"{d2_name} was on brakes for {d2_brake_percent:.2f}% of the lap\n"

    ax[1].annotate(throttle_string, xy=(1.0, -0.4), xycoords='axes fraction', ha='right', va='center')
    ax[2].annotate(brake_string, xy=(1.0, -0.4), xycoords='axes fraction', ha='right', va='center')

    plt.suptitle(f"Lap Telemetry\n{year} {str(race.event.EventName)}\n{d1_name} vs {d2_name}", x=0.1, ha="left")
    plt.grid(visible=False, which='both')
    # set up legend
    d1_lap_time = strftimedelta(d1_fl, '%m:%s.%ms')
    d2_lap_time = strftimedelta(d2_fl, '%m:%s.%ms')
    d1_patch = matplotlib.patches.Patch(color=d1_color, label=f"{d1_name} {d1_lap_time}")
    d2_patch = matplotlib.patches.Patch(color=d2_color, label=f"{d2_name} {d2_lap_time}")
    plt.legend(handles=[d1_patch, d2_patch], bbox_to_anchor=(1.01, 5.2), loc='upper right')

    plt.rcParams['savefig.dpi'] = 300
    plt.savefig("formula1/telemetry.png")
    file = discord.File("formula1/telemetry.png", file_name="image.png")

    return file


def track_dominance(year, gp, session, driver1, driver2):
    """ Returns a trackdominace graph """
    # pyplot setup
    fastf1.plotting.setup_mpl()
    fig, ax = plt.subplots(figsize=(7.5, 6))
    fig.set_facecolor('black')
    ax.set_facecolor('black')
    ax.axis('equal')
    ax.axis('off')
    # get session using given args
    race = fastf1.get_session(year, gp, session)
    log.write("FastF1: " + session)
    race.load(laps=True, telemetry=True, weather=False, messages=False)
    # get driver data for their fastest lap during the session
    d1_laps = race.laps.pick_driver(driver1)
    d1_fastest = d1_laps.pick_fastest()
    d1_number = d1_laps.iloc[0].loc['DriverNumber']
    d1_name = driver1

    d2_laps = race.laps.pick_driver(driver2)
    d2_fastest = d2_laps.pick_fastest()
    d2_number = d2_laps.iloc[0].loc['DriverNumber']
    d2_name = driver2
    # get driver telemetry
    d1_telemetry_data = d1_fastest.get_telemetry()
    d2_telemetry_data = d2_fastest.get_telemetry()

    # get driver color
    if year == util.CURRENT_F1_SEASON:
        # fastf1.plotting.driver_color() only supports current season
        try: d1_color = fastf1.plotting.driver_color(d1_name)
        except KeyError: d1_color = util.random_colour_generator()
        try: d2_color = fastf1.plotting.driver_color(d2_name)
        except KeyError: d2_color = util.random_colour_generator()
    else:
        # otherwise use team color
        d1_color = f"#{race.results.loc[str(d1_number), 'TeamColor']}"
        d2_color = f"#{race.results.loc[str(d2_number), 'TeamColor']}"
    if d1_color == d2_color:
        # if comparing teammates, reverse colour (if resulting colour is black, change it to grey)
        table = str.maketrans("0123456789abcdef", "fedcba987654321")
        d2_color = d2_color.translate(table)
        if d2_color == '#000000': d2_color = 'grey'

    # We want 25 mini-sectors
    num_minisectors = 25

    # What is the total distance of a lap?
    total_distance = max(d1_telemetry_data['Distance'])

    # Generate equally sized mini-sectors
    minisector_length = total_distance / num_minisectors

    minisectors = [0]

    for i in range(0, (num_minisectors - 1)):
        minisectors.append(minisector_length * (i + 1))

    # add columns for minisector number and minisector average speed
    d1_telemetry_data['Minisector'] = d1_telemetry_data['Distance'].apply(
        lambda z: (
                minisectors.index(
                    min(minisectors, key=lambda x: abs(x - z))) + 1
        )
    )
    avg_speeds1 = d1_telemetry_data.groupby("Minisector")["Speed"].mean()
    d1_telemetry_data["Minisector_Speed"] = d1_telemetry_data["Minisector"].map(avg_speeds1)

    d2_telemetry_data['Minisector'] = d2_telemetry_data['Distance'].apply(
        lambda z: (
                minisectors.index(
                    min(minisectors, key=lambda x: abs(x - z))) + 1
        )
    )
    avg_speeds2 = d2_telemetry_data.groupby("Minisector")["Speed"].mean()
    d2_telemetry_data["Minisector_Speed"] = d2_telemetry_data["Minisector"].map(avg_speeds2)

    # add another column for driver color
    d1_telemetry_data['Driver_Color'] = d1_color
    d2_telemetry_data['Driver_Color'] = d2_color

    # get the greatest average speed per minisector
    d1_avg_speeds = d1_telemetry_data.groupby("Minisector")["Minisector_Speed"].max()
    d2_avg_speeds = d2_telemetry_data.groupby("Minisector")["Minisector_Speed"].max()
    max_avg_speeds = []
    for i in d1_avg_speeds.index:
        if d1_avg_speeds[i] >= d2_avg_speeds[i]: max_avg_speeds.append(d1_avg_speeds[i])
        else: max_avg_speeds.append(d2_avg_speeds[i])
    # Create a new dataframe combining the "X", "Y", "Minisector", and "Minisector_Speed" columns from both dataframes
    combined_data = pd.concat([d1_telemetry_data[['X', 'Y', 'Minisector', 'Minisector_Speed', 'Driver_Color']],
                               d2_telemetry_data[['X', 'Y', 'Minisector', 'Minisector_Speed', 'Driver_Color']]])
    df_list = []
    for i in range(25):
        df_list.append(combined_data.loc[combined_data['Minisector_Speed'] == max_avg_speeds[i]])
    filtered_df = pd.concat(df_list)
    # remove duplicate rows
    filtered_df = filtered_df.loc[filtered_df.groupby(filtered_df.index)['Minisector_Speed'].idxmax()]

    # create color array for each segment of line
    color_array = []

    # compare speed in each sector and add faster driver's color to color_array
    x = filtered_df["X"].to_list()
    y = filtered_df["Y"].to_list()
    x = d1_telemetry_data["X"].to_list()
    y = d1_telemetry_data["Y"].to_list()
    for i in filtered_df.index:
        try:
            row_color = filtered_df.loc[i, "Driver_Color"]
            # use faster driver's color
            if (type(row_color)) == str:
                if row_color == d1_color: color_array.append(1)
                elif row_color == d2_color: color_array.append(2)
        # when there is no data for either driver for a sector, make the color black
        except Exception as e:
            # traceback.print_exc()
            color_array.append(None)

    # some numpy fuckery to turn x and y lists to coords, IDK how this works
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # colormap
    cmap = matplotlib.colors.ListedColormap([d1_color, d2_color])
    # setup LineCollection
    lc = matplotlib.collections.LineCollection(segments, cmap=cmap)
    lc.set_array(color_array)
    lc.set_linewidth(2)
    # plot line
    plt.gca().add_collection(lc)
    plt.gca().axis('equal')
    # more plot setup
    plt.title(
        f"{d1_name} vs {d2_name}\n{str(race.date.year)} {str(race.event.EventName)} {race.name.capitalize()}\n"
        f"Track Dominance on Fastest Lap", weight='bold')
    plt.grid(visible=False, which='both')
    # set up legend
    d1_lap_time = strftimedelta(d1_fastest['LapTime'], '%m:%s.%ms')
    d2_lap_time = strftimedelta(d2_fastest['LapTime'], '%m:%s.%ms')
    d1_patch = matplotlib.patches.Patch(color=d1_color, label=f"{d1_name} {d1_lap_time}")
    d2_patch = matplotlib.patches.Patch(color=d2_color, label=f"{d2_name} {d2_lap_time}")
    plt.legend(handles=[d1_patch, d2_patch])
    # save plot
    plt.rcParams['savefig.dpi'] = 300

    plt.savefig("formula1/trackdom.png", bbox_inches='tight')
    file = discord.File("formula1/trackdom.png", file_name="image.png")

    return file
