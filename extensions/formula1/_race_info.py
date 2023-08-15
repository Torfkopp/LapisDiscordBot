import fastf1.plotting
import matplotlib.pyplot as plt
import seaborn as sns
from interactions.models import discord

""" Methods for the race info command"""
# all three methods part of the fastf1 docs examples

# enabling misc_mpl_mods will turn on minor grid lines that clutters the plot
fastf1.plotting.setup_mpl(mpl_timedelta_support=False, misc_mpl_mods=False)


def position_change(year, gp):
    """ Returns the place changes during the race"""
    # Load the session
    session = fastf1.get_session(year, gp, 'R')
    session.load(telemetry=False, weather=False)

    # Create plot
    fig, ax = plt.subplots(figsize=(8.0, 4.9))

    # Change colour
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    # For each driver, get their three letters, get their colour,
    # and then plot their position over the number of laps
    for drv in session.drivers:
        drv_laps = session.laps.pick_driver(drv)

        abb = drv_laps['Driver'].iloc[0]
        color = fastf1.plotting.driver_color(abb)

        ax.plot(drv_laps['LapNumber'], drv_laps['Position'],
                label=abb, color=color)

    # Finalise the plot by setting y-limits that invert the y-axis
    # so that position one is at the top, set custom tick positions and axis labels.
    ax.set_ylim([20.5, 0.5])
    ax.set_yticks([1, 5, 10, 15, 20])
    ax.set_xlabel('Lap')
    ax.set_ylabel('Position')

    # Add the legend outside the plot area
    ax.legend(bbox_to_anchor=(1.0, 1.02))
    plt.tight_layout()

    # Add title
    plt.title(f"{session.event['EventName']} Position Changes")

    # Save the figure and let Discord load it
    plt.savefig('Resources/pc.png')
    file = discord.File("Resources/pc.png", file_name="image.png")

    return file


def lap_time_distribution(year, gp):
    """ Returns the drivers' lap time distribution during the race """
    # Load the race session
    race = fastf1.get_session(year, gp, 'R')
    race.load()

    # Get all laps for point finishers only. Filter out slow laps
    point_finishers = race.drivers[:10]
    driver_laps = race.laps.pick_drivers(point_finishers).pick_quicklaps()
    driver_laps = driver_laps.reset_index()

    # To plot by finishing order, get abbreviations in finishing order
    finishing_order = [race.get_driver(i)["Abbreviation"] for i in point_finishers]

    # Modify Driver_colors palette. For that, change key from full name to Abbreviation.
    driver_colors = {abv: fastf1.plotting.DRIVER_COLORS[driver] for abv, driver in
                     fastf1.plotting.DRIVER_TRANSLATE.items()}

    # create the figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Seaborn doesn't have proper timedelta support,
    # so we have to convert timedelta to float (in seconds)
    driver_laps["LapTime(s)"] = driver_laps["LapTime"].dt.total_seconds()

    sns.violinplot(data=driver_laps,
                   x="Driver",
                   y="LapTime(s)",
                   inner=None,
                   scale="area",
                   order=finishing_order,
                   palette=driver_colors
                   )

    sns.swarmplot(data=driver_laps,
                  x="Driver",
                  y="LapTime(s)",
                  order=finishing_order,
                  hue="Compound",
                  palette=fastf1.plotting.COMPOUND_COLORS,
                  hue_order=["SOFT", "MEDIUM", "HARD"],
                  linewidth=0,
                  size=5,
                  )

    # make plot more aestetic
    ax.set_xlabel("Driver")
    ax.set_ylabel("Lap Time (s)")
    plt.suptitle(f"{year} {race.event['EventName']} Lap Time Distributions")
    sns.despine(left=True, bottom=True)
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    plt.tight_layout()

    # Save the figure and let Discord load it
    plt.savefig('Resources/ltd.png')
    file = discord.File("Resources/ltd.png", file_name="image.png")

    return file


def strategy(year, gp):
    """ Returns the tyre strategies during the race """
    # Load the race session
    session = fastf1.get_session(year, gp, 'R')
    session.load()
    laps = session.laps

    # Get the list of driver numbers
    drivers = session.drivers

    # Convert the driver numbers to three letter abbreviations
    drivers = [session.get_driver(driver)["Abbreviation"] for driver in drivers]

    # Find sting length and compound for every driver;
    # group laps, sting number, and compound. Then count number of laps in each
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
    stints = stints.groupby(["Driver", "Stint", "Compound"])
    stints = stints.count().reset_index()

    # Number in LapNumber now stands for the stint length
    stints = stints.rename(columns={"LapNumber": "StintLength"})

    # Plot the strategies for each driver
    fig, ax = plt.subplots(figsize=(5, 10))

    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]

        previous_stint_end = 0
        for idx, row in driver_stints.iterrows():
            # each row contains the compound name and stint length
            # we can use these information to draw horizontal bars
            plt.barh(
                y=driver,
                width=row["StintLength"],
                left=previous_stint_end,
                color=fastf1.plotting.COMPOUND_COLORS[row["Compound"]],
                edgecolor="black",
                fill=True
            )

            previous_stint_end += row["StintLength"]

    # Make plot more readable and intuitive ('OfficialEventName' possible as well)
    plt.title(f"{year} {session.event['EventName']} Strategies")
    plt.xlabel("Lap Number")
    plt.grid(False)

    # invert the y-axis so drivers that finish higher are closer to the top
    ax.invert_yaxis()

    # plot aesthetics
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    fig.set_facecolor('black')
    ax.set_facecolor('black')

    plt.tight_layout()

    # Save the figure and let Discord load it
    plt.savefig('Resources/strat.png')
    file = discord.File("Resources/strat.png", file_name="image.png")

    return file
