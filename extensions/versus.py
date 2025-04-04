import json
import random
import sqlite3
import warnings
from datetime import datetime

import interactions
import numpy as np
from interactions import (
    Extension, slash_command, slash_option, SlashContext, OptionType, SlashCommandChoice, ActionRow, Button,
    ButtonStyle, listen
)
from interactions.api.events import Component
from interactions.models import discord
from matplotlib import pyplot as plt

import util


def setup(bot):
    Versus(bot)
    bot.add_listener(on_versus_component)


COLOUR = util.Colour.VERSUS.value

game_dict = {
    "League": "lol",
}

title_options = {
    "lol": [
        "Brückenschlägerei",
        "Brücke sehen ... und sterben?",
        "Fliegende Fäuste: Freljord",
        "Hitparade: die besten Deutschen Schläger",
    ]
}


@listen()
async def on_versus_component(event: Component):
    ctx = event.ctx
    if not (str(ctx.author_id) == util.AUTHOR_ID or str(ctx.author_id) == util.SECOND_VERSUS_ID): return
    if not ctx.custom_id.startswith("versus"): return

    for component in Versus.components.components: component.disabled = True
    winning_side = ctx.component.custom_id
    if ctx.message.content != "": return

    if "blue" in winning_side:
        winning_side = "BLAUE"
        post_match(Versus.one)
    elif "red" in winning_side:
        winning_side = "ROTE"
        post_match(Versus.two)
    else:
        return await ctx.message.delete()

    Versus.match_embed.description = f"Die {winning_side} Seite hat gewonnen!"
    await ctx.edit_origin(embed=util.uwuify_by_chance(Versus.match_embed), components=[])


class Versus(Extension):
    components = ActionRow()
    match_embed = None
    participants = {}
    champs = ()
    one, two = [], []
    game = ""

    @slash_command(name="versus", description="Teile deinen jetzigen Channel in Teams auf und kämpfe um Elo")
    @slash_option(
        name="partition",
        description="Wie die Teams aufgeteilt werden sollen",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Random", value="Random"),
            SlashCommandChoice(name="Nach Elo", value="Elo"),
        ]
    )
    @slash_option(
        name="excludee",
        description="Personen, die nicht in die Teambildung aufgenommen werden sollen",
        required=False,
        opt_type=OptionType.USER,
    )
    @slash_option(
        name="game",
        description="Um welches Game es sich handelt",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(k, game_dict[k]) for k in game_dict],
    )
    async def versus_function(self, ctx: SlashContext, partition="Random", excludee="",
                              game=list(game_dict.values())[0]):
        await ctx.defer()
        Versus.game = game
        Versus.participants = get_participants(ctx.guild.channels, ctx.user, excludee)
        if len(Versus.participants) < 2:
            return await ctx.send(
                embed=util.get_error_embed(
                    "custom",
                    [
                        "Zu wenige Mitstreiter",
                        "Ein Kampf gegen dich alleine ist schön und ich denke, du würdest gewinnen, "
                        "aber Elo kannst du so nicht sammeln.\nSuch dir ein paar Freunde und versuche es erneut!",
                        "lonely"
                    ])
            )

        Versus.match_embed, Versus.one, Versus.two, file = pre_match(partition)

        Versus.components = ActionRow(
            Button(
                custom_id="versus_blue",
                style=ButtonStyle.BLUE,
                label="BLUE WIN"
            ),
            Button(
                custom_id="versus_abort",
                style=ButtonStyle.GREY,
                label="ABORT"
            ),
            Button(
                custom_id="versus_red",
                style=ButtonStyle.RED,
                label="RED WIN"
            ),
        )

        await ctx.send(embed=Versus.match_embed, components=Versus.components, file=file)

    @slash_command(name="versus_elo_graph", description="Zeige den Elo-Graphen an")
    @slash_option(
        name="game",
        description="Um welches Game es sich handelt",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(k, game_dict[k]) for k in game_dict]
    )
    @slash_option(
        name="people",
        description="Die zu anzeigenden Personen (@Person)",
        required=False,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="timeframe",
        description="Der Zeitraum [von, bis). Schranken optional, Format: DD.MM.YY",
        required=False,
        opt_type=OptionType.STRING,
    )
    async def elo_graph_function(self, ctx: SlashContext, people="", game=list(game_dict.values())[0], timeframe=","):
        await ctx.defer()
        embed, file = get_elo_graph(mention_to_people(people, game), game, timeframe)
        await ctx.send(embed=embed, file=file)

    @slash_command(name="versus_win_rate", description="Zeige die Winrate der Spieler an")
    @slash_option(
        name="game",
        description="Um welches Game es sich handelt",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(k, game_dict[k]) for k in game_dict]
    )
    @slash_option(
        name="people",
        description="Die zu anzeigenden Personen (@Person)",
        required=False,
        opt_type=OptionType.STRING,
    )
    async def win_rate_function(self, ctx: SlashContext, people="", game=list(game_dict.values())[0]):
        await ctx.defer()
        embed = get_win_rates(mention_to_people(people, game), game)
        await ctx.send(embed=embed)


def mention_to_people(people, game):
    if people == "": return people
    with open("strunt/elo.json") as f: elo = json.load(f)[game]
    numbers = people.split("@")
    peops = ""
    for n in numbers:
        n = n.replace("<", "").replace(",", "").replace(">", "").strip()
        if n in elo: peops += elo[n]["name"][0] + ", "
    return peops


def get_participants(channels, invoker, excludee):
    """
    Gets: The channel list, the command's invoker
    Returns: Dictionary of (id: display_name)
    """
    id_name_dict = {}
    voice_channels = [channel for channel in channels if channel.type == 2]
    for channel in voice_channels:
        if invoker in (members := channel.voice_members):
            for member in members:
                if member == excludee: continue
                id_name_dict[str(member.id)] = member.display_name

    return id_name_dict


def pre_match(partition):
    """ The procedure before the embed is sent """
    change = False
    elo_dict = {}
    with open("strunt/elo.json", "r") as f: elo_json = json.load(f)
    if Versus.game not in elo_json: change = True; elo_json[Versus.game] = {}
    player_elos = elo_json[Versus.game]

    for p in Versus.participants:
        if str(p) not in player_elos.keys():
            change = True
            player_elos[str(p)] = {
                "name": [Versus.participants[p]],
                "elo": 1000,
                "wins": 0,
                "losses": 0,
                "history": {
                    datetime.fromisocalendar(2001, 1, 1).strftime("%Y-%m-%d %H:%M"): 1000,
                }
            }
        if Versus.participants[p] not in player_elos[str(p)]["name"]: player_elos[str(p)]["name"].append(
            Versus.participants[p])
        elo_dict[p] = player_elos[str(p)]["elo"]

    if change:
        with open("strunt/elo.json", "w") as f: json.dump(elo_json, f, indent=4)

    one, two = random_teams() if partition == "Random" else elo_teams(player_elos)
    if Versus.game == "lol": Versus.champs = random_champions(one)

    embed, file = build_pre_game_embed(elo_dict, one, two)

    return embed, one, two, file


def random_teams():
    """ Returns two random teams """
    names = list(Versus.participants.keys())
    random.shuffle(names)
    one = names[len(names) // 2:]
    two = names[:len(names) // 2]

    return one, two


def elo_teams(player_elos):
    """ Returns two teams with minimal elo difference """
    import itertools
    elo_dict = {}
    for p in Versus.participants: elo_dict[p] = player_elos[str(p)]["elo"]

    dicc = {}

    for combi in itertools.combinations(list(elo_dict.keys()), len(elo_dict) // 2):
        one, two = [], []
        one_elo, two_elo = 0, 0
        for t in elo_dict:
            if t in combi:
                one.append(t)
                one_elo += elo_dict[t]
            else:
                two.append(t)
                two_elo += elo_dict[t]

        dicc[(tuple(one), tuple(two))] = abs(one_elo - two_elo)

    lowest = 10000
    partition = []
    for k, v in dicc.items():
        if v < lowest:
            lowest = v
            partition = [k]
        elif v == lowest: partition.append(k)

    one, two = random.choice(partition)

    return one, two


def random_champions(one):
    """ Returns a tuple of random champs for both teams """
    with open("resources/champions.txt") as f: champions = f.read().splitlines()

    champs = random.sample(champions, len(Versus.participants))
    return champs[:len(one)], champs[len(one):]


def build_pre_game_embed(elo_dict, one, two):
    """ Build the embed """
    file = interactions.models.discord.File("lapis_pics/boxing.png", "boxing.png")
    embed = interactions.Embed(title=random.choice(title_options[Versus.game]), color=COLOUR)
    embed.set_thumbnail(url="attachment://boxing.png")

    def field_text(team):
        team_elo, string = 0, ""
        for player in team:
            team_elo += elo_dict[player]
            string += f"`- {Versus.participants[player]:<15} {elo_dict[player]:>4} `\n"
        if Versus.game == "lol": string += "Champs: " + ", ".join(Versus.champs[0 if team == one else 1]) + ""
        return string, team_elo

    value, name = field_text(one)
    embed.add_field(name=f"Blue Side ({name})", value=value, inline=False)
    value, name = field_text(two)
    embed.add_field(name=f"Red Side ({name})", value=value, inline=False)

    return util.uwuify_by_chance(embed), file


def post_match(winner):
    """ After the game is finished and the button was pressed """
    fields = Versus.match_embed.fields

    elo_dict, player_elos = get_elo_dict(winner)
    if Versus.champs: update_database(player_elos, winner)

    def field_text(team):
        team_elo = 0
        string = ""
        for player in team:
            team_elo += elo_dict[player][0]
            string += (
                f"`- {Versus.participants[player]:<15} {elo_dict[player][0]:>4} "
                f"({'+' + str(e) if (e := elo_dict[player][1]) > 0 else e:>3})`\n"
            )
        if Versus.game: string += "`Champs: " + ", ".join(Versus.champs[0 if team == Versus.one else 1]) + "`"
        return string, team_elo

    blue_side, blue_elo = field_text(Versus.one)
    red_side, red_elo = field_text(Versus.two)

    fields[0].value, fields[1].value = blue_side, red_side
    fields[0].name = f"Blue Side ({blue_elo})"
    fields[1].name = f"Red Side ({red_elo})"


def get_elo_dict(winner):
    """ Updates the elo, wins etc. of every player """
    elo_dict = {}

    with open("strunt/elo.json", "r") as f: elo_json = json.load(f)
    player_elos = elo_json[Versus.game]
    elo_gains = calculate_elo(player_elos, winner)
    for p in Versus.participants:
        player = player_elos[str(p)]
        x = round(elo_gains[str(p)])
        elo_dict[p] = (elo := player["elo"] + x), x
        player["elo"] = elo
        player["history"][str(datetime.now().isoformat(sep=" ", timespec="minutes"))] = elo
        win = 1 if p in winner else 0
        player["wins"] += win
        player["losses"] += abs(win - 1)

    with open("strunt/elo.json", "w") as f: json.dump(elo_json, f, indent=4)

    return elo_dict, player_elos


def calculate_elo(player_elos, winner):
    """ Calculates the elo gained of every player based on:
        https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details

        returns: dict{ player: gained_elo }
    """

    elo_gains = {}
    team_ratings = {'one': 0, 'two': 0}
    team_elos = {'one': {}, 'two': {}}
    # Separate players into teams and calculate total ratings
    for p, data in player_elos.items():
        if p not in Versus.one + Versus.two: continue
        team = 'one' if p in Versus.one else 'two'
        team_elos[team][p] = data["elo"]
        team_ratings[team] += data["elo"]

    # Total team elo divided by the opponent's size in case of number advantage
    team_ratings['one'] /= len(Versus.two)
    team_ratings['two'] /= len(Versus.one)

    # Calculate expected scores for each team
    e_one = 1 / (1 + 10 ** ((team_ratings['two'] - team_ratings['one']) / 480))
    e_two = 1 / (1 + 10 ** ((team_ratings['one'] - team_ratings['two']) / 480))
    team_expectations = {'one': e_one, 'two': e_two}

    # Calculate elo gains for each player
    for team, players in team_elos.items():
        expectation = team_expectations[team]
        for p, elo in players.items():
            s = 1 if p in winner else 0
            k = 60 if elo < 1900 else 45 if elo < 2400 else 30
            elo_gains[p] = (k * (s - expectation))

    return elo_gains


def update_database(player_elos, winner):
    """ Puts the game into the database and updates the champions' stats"""
    con = sqlite3.connect("strunt/elo.db")
    cur = con.cursor()

    def get_names(li): return ", ".join([player_elos[x]["name"][0] for x in li])

    cur.execute(
        "INSERT INTO games VALUES(?, ?, ?, ?, ?, ?, ?)",
        [
            str(datetime.now().isoformat(sep=" ", timespec="minutes")),
            f"{len(Versus.one)}v{len(Versus.two)}",
            get_names(Versus.one),
            ", ".join((Versus.champs[0])),
            get_names(Versus.two),
            ", ".join(Versus.champs[1]),
            get_names(winner),
        ]
    )

    for team, result in [(Versus.champs[0], winner == Versus.one), (Versus.champs[1], winner == Versus.two)]:
        for champ in team:
            cur.execute(
                f"UPDATE champs SET picks=picks+1, {'wins=wins+1' if result else 'losses=losses+1'} WHERE champ = ?",
                [champ]
            )

    con.commit()
    con.close()


#####################################################
#  COMMANDS
#####################################################


def get_elo_graph(people, game, timeframe):
    """ Method for the elo_graph function """
    with open("strunt/elo.json", "r") as f: player_elos = json.load(f)
    player_elos = player_elos[game]
    people = [p.strip() for p in people.split(",")] if people != "" else ""

    # Create variables for lower and upper boundary
    start_date = (time := timeframe.split(","))[0].strip()
    end_date = time[1].strip()
    # Create a variable that equals True when the boundary is not set
    no_low, no_high = not bool(start_date), not bool(end_date)

    plt.style.use('dark_background')
    fig, ax = plt.subplots()

    ids = []
    if people != "":
        ids.extend(x for p in people for x in player_elos if p in player_elos[x]["name"])
    if len(ids) == 0: ids = player_elos.keys()

    game_set = set()
    for x in player_elos:
        if x not in ids: continue
        history = player_elos[x]["history"]
        for k in history.keys(): game_set.add(k)

    game_set = sorted(list(game_set), key=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M"))
    if not (no_low and no_high):
        game_set = [x for x in game_set if
                    (no_low or datetime.strptime(start_date, "%d.%m.%y") < datetime.strptime(x, "%Y-%m-%d %H:%M"))
                    and (no_high or datetime.strptime(x, "%Y-%m-%d %H:%M") < datetime.strptime(end_date, "%d.%m.%y"))]
    dict_of_games = {d: i for i, d in enumerate(game_set)}
    x_axis = set()

    for p in ids:
        history = player_elos[p]["history"]
        history = {dict_of_games[k]: v for k, v in history.items() if k in dict_of_games}
        x_axis.update(list(history.keys()))
        ax.plot(list(history.keys()), list(history.values()), label=player_elos[p]["name"][0])

    ax.set_xlabel("Date")
    ax.set_ylabel("Elo")

    x_axis = sorted(list(x_axis))
    labels = [{v: k for k, v in dict_of_games.items()}[lab][:10] for lab in x_axis]
    labels[0] = "1000 Elo"
    ax.set_xticks(np.arange(0, len(x_axis)))
    with warnings.catch_warnings(action="ignore"): ax.set_xticklabels(labels)

    ax.legend()
    plt.suptitle("Elo Distribution")
    plt.xticks(rotation=90)
    plt.tight_layout()

    plt.savefig('strunt/elo.png')
    file = discord.File('strunt/elo.png', file_name="elo.png")

    return None, file


def get_win_rates(people, game):
    """ Method for the win_rate-table command"""
    with open("strunt/elo.json", "r") as f: player_elos = json.load(f)
    player_elos = player_elos[game]
    people = [p.strip() for p in people.split(",")] if people != "" else ""

    ids = []
    if people != "":
        ids.extend(x for p in people for x in player_elos if p in player_elos[x]["name"])
    if len(ids) == 0: ids = list(player_elos.keys())

    ids.sort(reverse=True, key=lambda x: player_elos[x]["elo"])

    def linemaker(player, elo, w, l, wr):
        return "| ".join(
            ["", player.ljust(10), str(elo).ljust(5), str(w).ljust(4), str(l).ljust(4), str(wr).ljust(8)]) + "|\n"

    string = linemaker("Spieler", "Elo", " W", " L", "WR in % ")
    string += "|".join(["", "-" * 11, "-" * 6, "-" * 5, "-" * 5, "-" * 9]) + "|\n"

    for p in ids:
        string += linemaker(
            player_elos[p]["name"][0],
            player_elos[p]["elo"],
            w := player_elos[p]["wins"],
            l := player_elos[p]["losses"],
            round(w / (w + l) * 100, 3)
        )

    embed = interactions.Embed(title="Siegesratentabelle für " + [k for k, v in game_dict.items() if v == game][0],
                               color=COLOUR)
    embed.description = "```markdown\n" + string + "\n```"

    return embed
