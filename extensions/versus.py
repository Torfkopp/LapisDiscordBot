import json
import random
import warnings
from datetime import datetime

import interactions
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
    participants, one, two = {}, {}, {}
    game = ""

    @slash_command(name="versus", description="Teile deinen jetzigen Channel in Teams auf und kämpfe um Elo",
                   scopes=[1134856890669613210])
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
        name="game",
        description="Um welches Game es sich handelt",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(k, game_dict[k]) for k in game_dict],

    )
    async def versus_function(self, ctx: SlashContext, partition="Random", game=list(game_dict.values())[0]):
        await ctx.defer()
        Versus.game = game
        Versus.participants = get_participants(ctx.guild.channels, ctx.user)
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
        name="people",
        description="Die zu anzeigenden Personen (Komma getrennt)",
        required=False,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="game",
        description="Um welches Game es sich handelt",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(k, game_dict[k]) for k in game_dict]
    )
    @slash_option(
        name="timeframe",
        description="Der Zeitraum [von, bis). Schranken optional, Format: DD.MM.YY",
        required=False,
        opt_type=OptionType.STRING,
    )
    async def elo_graph_function(self, ctx: SlashContext, people="", game=list(game_dict.values())[0], timeframe=","):
        await ctx.defer()
        embed, file = get_elo_graph(people, game, timeframe)
        await ctx.send(embed=embed, file=file)


def pre_match(partition):
    file = interactions.models.discord.File("lapis_pics/boxing.png", "boxing.png")
    embed = interactions.Embed(title=random.choice(title_options[Versus.game]), color=COLOUR)
    embed.set_thumbnail(url="attachment://boxing.png")
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
                "history": {
                    str(datetime.min.strftime("%Y-%m-%d %H:%M:%S.%f")): 1000,
                }
            }
        if Versus.participants[p] not in player_elos[str(p)]["name"]: player_elos[str(p)]["name"].append(
            Versus.participants[p])
        elo_dict[p] = player_elos[str(p)]["elo"]

    if change:
        with open("strunt/elo.json", "w") as f: json.dump(elo_json, f, indent=4)

    def field_text(team):
        team_elo, string = 0, ""
        for player in team:
            team_elo += elo_dict[player]
            string += f"`- {Versus.participants[player]:<15} {elo_dict[player]:>4} `\n"
        return string, team_elo

    one, two = random_teams() if partition == "Random" else elo_teams(player_elos)

    value, name = field_text(one)
    embed.add_field(name=f"Blue Side ({name})", value=value, inline=False)
    value, name = field_text(two)
    embed.add_field(name=f"Red Side ({name})", value=value, inline=False)
    return util.uwuify_by_chance(embed), one, two, file


def post_match(winner):
    fields = Versus.match_embed.fields

    elo_dict = get_elo_dict(winner)

    def field_text(team):
        team_elo = 0
        string = ""
        for player in team:
            team_elo += elo_dict[player][0]
            string += (
                f"`- {Versus.participants[player]:<15} {elo_dict[player][0]:>4} "
                f"({'+' + str(e) if (e := elo_dict[player][1]) > 0 else e:>3})`\n"
            )
        return string, team_elo

    blue_side, blue_elo = field_text(Versus.one)
    red_side, red_elo = field_text(Versus.two)

    fields[0].value, fields[1].value = blue_side, red_side
    fields[0].name = f"Blue Side ({blue_elo})"
    fields[1].name = f"Red Side ({red_elo})"


def get_elo_dict(winner):
    elo_dict = {}

    with open("strunt/elo.json", "r") as f: elo_json = json.load(f)
    player_elos = elo_json[Versus.game]
    elo_gains = calculate_elo(player_elos, winner)
    for p in Versus.participants:
        x = round(elo_gains[str(p)])
        elo_dict[p] = (elo := player_elos[str(p)]["elo"] + x), x
        player_elos[str(p)]["elo"] = elo
        player_elos[str(p)]["history"][str(datetime.now())] = elo

    with open("strunt/elo.json", "w") as f: json.dump(elo_json, f, indent=4)

    return elo_dict


def calculate_elo(player_elos, winner):
    # Based on https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
    elo_gains = {}
    team_ratings = {'one': 0, 'two': 0}
    team_elos = {'one': {}, 'two': {}}
    # Separate players into teams and calculate total ratings
    for p, data in player_elos.items():
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
            k = 32 if elo < 2100 else 24 if elo < 2400 else 16
            elo_gains[p] = (k * (s - expectation))

    return elo_gains


def get_elo_graph(people, game, timeframe):
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

    for p in ids:
        history = player_elos[p]["history"]
        # Put the key-value-pair into the dictionary when date is between the two boundaries
        history = {
            k: v for k, v in history.items()
            if (no_low or datetime.strptime(start_date, "%d.%m.%y") < datetime.strptime(k, "%Y-%m-%d %H:%M:%S.%f"))
               and (no_high or datetime.strptime(k, "%Y-%m-%d %H:%M:%S.%f") < datetime.strptime(end_date, "%d.%m.%y"))
        }

        ax.plot(list(history.keys()), list(history.values()), label=player_elos[p]["name"][0])

    ax.set_xlabel("Date")
    ax.set_ylabel("Elo")

    labels = [item.get_text() for item in ax.get_xticklabels()]
    labels = [lab[:10] for lab in labels]
    with warnings.catch_warnings(action="ignore"):
        ax.set_xticklabels(labels)

    ax.legend()
    plt.suptitle("Elo Distribution")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('strunt/elo.png')
    file = discord.File('strunt/elo.png', file_name="elo.png")

    return None, file


def get_participants(channels, invoker):
    """
    Gets: The channel list, the command's invoker
    Returns: Dictionary of (id: display_name)
    """
    id_name_dict = {}
    voice_channels = [channel for channel in channels if
                      channel.category is not None and channel.category.name == "Sprachkanäle"]
    for channel in voice_channels:
        if invoker in (members := channel.voice_members):
            for member in members:
                id_name_dict[str(member.id)] = member.display_name

    return id_name_dict


def random_teams():
    names = list(Versus.participants.keys())
    random.shuffle(names)
    one = names[len(names) // 2:]
    two = names[:len(names) // 2]

    return one, two


def elo_teams(player_elos):
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
