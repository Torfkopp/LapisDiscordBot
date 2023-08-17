import interactions
import matplotlib
import matplotlib.pyplot as plt
from interactions.models import discord

import fastf1
from fastf1.ergast import Ergast
import fastf1.plotting

import pandas as pd
import plotly
import plotly.express as px

import util

""" All methods for the standings commands """

COLOUR = util.FORMULA1_COLOUR
CURRENT_SEASON = util.CURRENT_F1_SEASON


def get_driver_positions(year, session):
    """ Gets all positions of a driver """
    ergast = Ergast()
    races = ergast.get_race_schedule(year)

    result_map = {}  # Contains DriverCode and positions NameShort : {Race : Position}
    driver_map = {}  # Contains DriverCode and Fullname NameShort : NameLong
    team_map = {}  # Contains Team with its drivers TeamName : [NameShort]

    if session == "S":
        func = ergast.get_sprint_results
    elif session == "Q":
        func = ergast.get_qualifying_results
    else:
        func = ergast.get_race_results

    # Fill the maps
    for rnd, race in races['raceName'].items():
        temp = func(season=year, round=rnd + 1)
        try:
            temp = temp.content[0]
        except IndexError:
            break
        if rnd == 0:  # If it is the first iteration, fill driver and team map
            for i in range(0, temp.index.max()):
                driver_code = temp.at[i, 'driverCode']
                driver_name = f"{temp.at[i, 'givenName']} {temp.at[i, 'familyName']}"
                team_name = temp.at[i, 'constructorName']
                position = temp.at[i, 'position']
                # Check since Qualifying has no status
                status = temp.at[i, 'status'] if session != "qualifying" else "Finished"
                if not (status == "Finished" or status.startswith('+')): position = "DNF"

                driver_map[driver_code] = driver_name
                result_map[driver_code] = {}
                result_map.get(driver_code)[race] = position
                if team_name not in team_map: team_map[team_name] = []
                team_map.get(team_name).append(driver_code)
        else:  # For all the other iterations, just add the position
            for i in range(0, temp.index.max()):
                driver_code = temp.at[i, 'driverCode']
                position = temp.at[i, 'position']
                status = temp.at[i, 'status'] if session != "qualifying" else "Finished"
                if not (status == "Finished" or status.startswith('+')): position = "DNF"

                if driver_code in result_map:  # Check necessary to avoid AttributeError
                    result_map.get(driver_code)[race] = position
                else:
                    result_map[driver_code] = {}
                    result_map.get(driver_code)[race] = position
                    driver_map[driver_code] = f"{temp.at[i, 'givenName']} {temp.at[i, 'familyName']}"
                    team_map.get(temp.at[i, 'constructorName']).append(driver_code)

    return result_map, driver_map, team_map


def average_position(year, session):
    """ Return the average finish position"""
    fastf1.plotting.setup_mpl()
    driver_positions = get_driver_positions(year, session)
    result_map = {}

    for driver in driver_positions[0]:
        m, avg = 0, 0
        for position in driver_positions[0].get(driver).values():
            if position != "DNF":
                avg += int(position)
                m += 1
        avg /= m
        result_map[driver] = round(avg, 3)

    # Sort the map
    result_map = {k: v for k, v in sorted(result_map.items(), key=lambda item: item[1])}

    '''
    result_string = "```"
    result_string += "Platz".ljust(6) + "Name".center(30) + "Avg. Pos.".rjust(10) + "\n"

    i = 1
    for driver in result_map:
        name = driver_positions[1].get(driver)
        result_string += str(i).ljust(6) + name.center(30) + str(result_map.get(driver)).rjust(10) + "\n"
        i += 1

    result_string += "```"
    
    
    return util.uwuify_by_chance(result_string)
    '''
    team_order = list()
    team_map = driver_positions[2]
    for key in result_map:
        for team in team_map:
            if key in team_map.get(team):
                team_order.append(team)
                break

    team_colours = list()
    for team in team_order: team_colours.append(fastf1.plotting.team_color(team))

    fig, ax = plt.subplots()

    avg_positions = list(result_map.values())
    bars = ax.barh(range(len(result_map)), avg_positions, color=team_colours)

    for i in range(len(bars)):
        plt.text(bars[i].get_width() + 0.5, bars[i].get_y() + (bars[i].get_height()/2), avg_positions[i],
                 color="white", va="center")

    ax.set_ylim(-0.8, len(result_map) - 0.25)
    ax.set_yticks(range(len(result_map)))
    ax.set_yticklabels(result_map.keys())

    ax.invert_yaxis()
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))

    fig.set_facecolor('black')
    ax.set_facecolor('black')

    # remove all lines, bar the x-axis grid lines
    ax.yaxis.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.minorticks_off()

    ax.set_xlabel("Position")
    match session:
        case "R": session = "Race"
        case "Q": session = "Qualifying"
        case "S": session = "Sprint"
    plt.title(f"Average {session} Finish Position {year}")

    plt.savefig("Resources/averagefin.png")
    file = discord.File("Resources/averagefin.png", file_name="image.png")

    return file


def compare_positions(driver1_positions, driver2_positions):
    driver1_points, driver2_points = 0, 0
    for race in driver1_positions.keys() & driver2_positions.keys():
        if driver1_positions.get(race) == "DNF" or driver2_positions.get(race) == "DNF": continue
        if driver1_positions.get(race) < driver2_positions.get(race):
            driver1_points += 1
        else:
            driver2_points += 1
    return driver1_points, driver2_points


def h2h(year, session):
    """ Return all the Head2Head Results"""
    race_positions = get_driver_positions(year, session)

    match session:
        case "R": sess = "Renn"
        case "Q": sess = "Qualifikations"
        case _: sess = "Sprint"
    result_string = f"```Head2Head-{sess}-Vergleich der Fahrer im Jahr {year}\n\n"

    def add_to_string(team_str, driver1, points1, points2, driver2):
        string = team_str.ljust(16)
        string += str(driver1).ljust(20)
        string += f"{points1}:{points2}"
        string += str(driver2).rjust(20)
        string += "\n"
        return string

    for team in race_positions[2]:
        drivers = race_positions[2].get(team)
        if len(drivers) < 2:
            result_string += team.ljust(16)
            result_string += "Zu wenige Fahrer fürs Vergleichen ?:O" + "\n"
        elif len(drivers) == 2:
            driver1_positions, driver2_positions = race_positions[0].get(drivers[0]), race_positions[0].get(drivers[1])
            driver1_points, driver2_points = compare_positions(driver1_positions, driver2_positions)
            result_string += add_to_string(team, race_positions[1].get(drivers[0]), driver1_points,
                                           driver2_points, race_positions[1].get(drivers[1]))
        elif len(drivers) == 3:
            # Drivers getting added into race_positions in order of appearance
            driver1_positions = race_positions[0].get(drivers[0])  # driver 1
            driver2_positions = race_positions[0].get(drivers[1])  # driver 2
            driver3_positions = race_positions[0].get(drivers[2])  # driver 3
            # driver 1 vs driver 2 and then driver 3 vs driver 1 or 2
            # driver 1 vs driver 2 until one gets sacked
            driver1a_points, driver2a_points = compare_positions(driver1_positions, driver2_positions)
            # driver 3 vs driver 1/2 to the end
            if len(driver1_positions) > len(driver2_positions):
                driver_1or2 = drivers[0]
                driver1b_points, driver2b_points = compare_positions(driver1_positions, driver3_positions)
            else:
                driver_1or2 = drivers[1]
                driver1b_points, driver2b_points = compare_positions(driver2_positions, driver3_positions)
            result_string += add_to_string(team, race_positions[1].get(drivers[0]), driver1a_points,
                                           driver2a_points, race_positions[1].get(drivers[0]))
            result_string += add_to_string(" ", race_positions[1].get(driver_1or2), driver1b_points,
                                           driver2b_points, race_positions[1].get(drivers[2]))
        else:
            driver1_positions, driver2_positions = race_positions[0].get(drivers[0]), race_positions[0].get(drivers[1])
            driver1_points, driver2_points = compare_positions(driver1_positions, driver2_positions)
            result_string += add_to_string(team, race_positions[1].get(drivers[0]), driver1_points,
                                           driver2_points, race_positions[1].get(drivers[1]))
            result_string += " ".ljust(16)
            result_string += "Rest unvergleichbar aufgrund Wecheselfiesta" + "\n"

    result_string += "```"
    return util.uwuify_by_chance(result_string)


def heatmap(year):
    """ Returns a heatmap of all results in a season """
    ergast = Ergast()
    races = ergast.get_race_schedule(year)  # Races in year
    results = []

    # For each race in the season
    for rnd, race in races['raceName'].items():

        # Get results. Note that we use the round no. + 1, because the round no.
        # starts from one (1) instead of zero (0)
        temp = ergast.get_race_results(season=year, round=rnd + 1)
        try:
            temp = temp.content[0]
        except IndexError:
            break

        # If there is a sprint, get the results as well
        sprint = ergast.get_sprint_results(season=year, round=rnd + 1)
        if sprint.content and sprint.description['round'][0] == rnd + 1:
            temp = pd.merge(temp, sprint.content[0], on='driverCode', how='left')
            # Add sprint points and race points to get the total
            temp['points'] = temp['points_x'] + temp['points_y']
            temp.drop(columns=['points_x', 'points_y'], inplace=True)

        # Add round no. and grand prix name
        temp['round'] = rnd + 1
        temp['race'] = race.removesuffix(' Grand Prix')
        temp = temp[['round', 'race', 'driverCode', 'points']]  # Keep useful cols.
        results.append(temp)

    # Append all races into a single dataframe
    results = pd.concat(results)
    races = results['race'].drop_duplicates()

    results = results.pivot(index='driverCode', columns='round', values='points')
    # Here we have a 22-by-22 matrix (22 races and 22 drivers, incl. DEV and HUL)

    # Rank the drivers by their total points
    results['total_points'] = results.sum(axis=1)
    results = results.sort_values(by='total_points', ascending=False)
    results.drop(columns='total_points', inplace=True)

    # Use race name, instead of round no., as column names
    results.columns = races

    fig = px.imshow(
        results,
        text_auto=True,
        aspect='auto',  # Automatically adjust the aspect ratio
        # https://plotly.com/python/builtin-colorscales/
        color_continuous_scale=px.colors.sequential.Hot,
        labels={'x': 'Race',
                'y': 'Driver',
                'color': 'Points'}  # Change hover texts
    )
    fig.update_xaxes(title_text=f"Heatmap of {year}")  # Remove axis titles
    fig.update_yaxes(title_text='')

    fig.update_yaxes(tickmode='linear')  # Show all ticks, i.e. driver names
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='White',
                     showline=False, tickson='boundaries')  # Show horizontal grid only
    fig.update_xaxes(showgrid=False, showline=False)  # And remove vertical grid
    fig.update_layout(plot_bgcolor='black')  # Black plot background
    fig.update_layout(coloraxis_showscale=False)  # Remove legend
    fig.update_layout(xaxis=dict(side='top'))  # x-axis on top
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))  # Remove border margins
    fig.update_layout(paper_bgcolor="black")  # Black background
    fig.update_layout(font_color="White")

    with open("Resources/plot.png", 'wb') as f:
        f.write(plotly.io.to_image(fig, format="png"))

    file = discord.File("Resources/plot.png", file_name="image.png")

    return file


def table(year, driver_champ):
    """ Returns a table of the driver or constructor standings"""
    tabelle = "```"
    tabelle += "#".ljust(3) + "Name".center(20) + "Punkte".rjust(5) + "\n"
    ergast = Ergast()
    if driver_champ:
        driver_standings = ergast.get_driver_standings(season=year).content[0]
        for i, _ in enumerate(driver_standings.iterrows()):
            driver = driver_standings.loc[i]
            tabelle += str(driver['position']).ljust(3)
            tabelle += f"{driver['givenName']} {driver['familyName']}".center(20)
            tabelle += str(driver['points']).rjust(5)
            tabelle += "\n"
    else:
        constructor_standings = ergast.get_constructor_standings(season=year).content[0]
        for i, _ in enumerate(constructor_standings.iterrows()):
            team = constructor_standings.loc[i]
            tabelle += str(team['position']).ljust(3)
            tabelle += str(team['constructorName']).center(20)
            tabelle += str(team['points']).rjust(5)
            tabelle += "\n"

    tabelle += "```"

    return util.uwuify_by_chance(tabelle)


def whocanwin():
    """ Returns standings and if driver can still win championship """
    embed = interactions.Embed(title="Kann Fahrer x noch gewinnen?", color=COLOUR)
    ergast = Ergast()
    driver_standings = ergast.get_driver_standings(CURRENT_SEASON).content[0]
    # Calculate max points for remaining season
    points_for_sprint = 8 + 25 + 1  # Winning the sprint, race and fastest lap
    points_for_conventional = 25 + 1  # Winning the race and fastest lap

    events = fastf1.events.get_events_remaining(backend="ergast")
    # Count how many sprints and conventional races are left
    sprint_events = len(events.loc[events["EventFormat"] == "sprint"])
    conventional_events = len(events.loc[events["EventFormat"] == "conventional"])

    # Calculate points for each
    sprint_points = sprint_events * points_for_sprint
    conventional_points = conventional_events * points_for_conventional

    max_points = sprint_points + conventional_points
    # Calculate who can win
    leader_points = int(driver_standings.loc[0]['points'])

    for i, _ in enumerate(driver_standings.iterrows()):
        driver = driver_standings.loc[i]
        driver_max_points = int(driver["points"]) + max_points
        can_win = "Nope" if driver_max_points < leader_points else "Ja"

        embed.add_field(name=f"{driver['position']}: {driver['givenName'] + ' ' + driver['familyName']}, "
                             f"Momentane Punkte: {driver['points']}",
                        value=f"Maximal erreichbare Punkte: {driver_max_points}, "
                              f"Can win: {can_win}")

    return util.uwuify_by_chance(embed)
