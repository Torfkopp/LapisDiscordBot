import collections
import csv
import datetime
import random
from collections import defaultdict
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice, Embed
)
from interactions.models import discord

import util

COLOUR = util.Colour.JOJO.value
CSV_PATH = 'strunt/jojo-history.csv'

PARTS = [
    "Phantom Blood",
    "Battle Tendency",
    "Stardust Crusaders - Road to Egypt",
    "Stardust Crusaders - Battle in Egypt",
    "Diamond is Unbreakable",
    "Golden Wind",
    "Stone Ocean"
]
PARTS_SHORT = {
    "Phantom Blood": "PB",
    "Battle Tendency": "BT",
    "Stardust Crusaders - Road to Egypt": "SC1",
    "Stardust Crusaders - Battle in Egypt": "SC2",
    "Diamond is Unbreakable": "DIU",
    "Golden Wind": "GW",
    "Stone Ocean": "SO",
}


class JoJoWatch(Extension):
    @slash_command(name="jojo", description="JoJo Watch-Arc")
    async def jojo_function(self, ctx: SlashContext): await ctx.send("JoJo")

    @jojo_function.subcommand(sub_cmd_name="info", sub_cmd_description="Info")
    async def info_function(self, ctx: SlashContext):
        await ctx.defer()
        await ctx.send(embed=get_info())

    @jojo_function.subcommand(sub_cmd_name="when", sub_cmd_description="Guckdatum einer Folge")
    @slash_option(
        name="episode",
        description="Nummer der Episode",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=190,
    )
    @slash_option(
        name="part",
        description="Part",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(k, k) for k in PARTS],
    )
    @slash_option(
        name="part_episode",
        description="Nummer der Episode im Part",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=39,
    )
    async def when_function(self, ctx: SlashContext, episode=0, part=None, part_episode=0):
        await ctx.defer()
        embed = get_when(episode, part, part_episode)
        if isinstance(embed, Embed): await ctx.send(embed=embed)
        else: await ctx.send(embed)

    @jojo_function.subcommand(sub_cmd_name="table", sub_cmd_description="Tabellarische Zusammenfassung")
    async def table_function(self, ctx: SlashContext):
        await ctx.defer()
        await ctx.send(get_table())

    @jojo_function.subcommand(sub_cmd_name="graph", sub_cmd_description="Graphische Zusammenfassung")
    @slash_option(
        name="parts",
        description=f"Kürzel der gewünschten Parts ({','.join(PARTS_SHORT.values())})",
        required=False,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="compare",
        description="Direkter Vergleich",
        required=False,
        opt_type=OptionType.BOOLEAN
    )
    async def graph_function(self, ctx: SlashContext, parts=None, compare=False):
        await ctx.defer()
        embed, file = get_graph(parts, compare)
        await ctx.send(embed=embed, file=file)


def get_info():
    embed = Embed(title="JoJo Watchdauer", color=COLOUR)
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        episodes = list(reader)

    start_date = datetime.strptime(episodes[0]['Date'], "%Y-%m-%d")
    end_date = datetime.strptime(episodes[-1]['Date'], "%Y-%m-%d")
    gif = random.choice(
        ["https://c.tenor.com/L7rMSFzEJq4AAAAC/tenor.gif", "https://c.tenor.com/i-yPjO4lTG0AAAAd/tenor.gif",
         "https://c.tenor.com/cwYk-FiyaLgAAAAd/tenor.gif"])

    duration = (end_date - start_date).days

    embed.description = f"Jakob hat {duration} Tage (665 vom Bot gezählt) für JoJo gebraucht."
    embed.set_image(gif)
    return embed


def get_when(episode_number, part, part_episode_number):
    data = when_data(episode_number, part, part_episode_number)
    if not data:
        return util.get_error_embed("faulty_value")
    desc = "Wann welche Episode?\n"
    desc += "```m\n"
    desc += f"{'Datum':<8} |{'Ep':<3}| {'P':<3} |{'PE':<2}| {'Titel'}\n"
    # desc += f"{'-' * 9}|{'-' * 5}|{'-' * 5}|{'-' * 4}|{'-' * 6}\n" # Sadly Too long with it
    for d in data:
        title = d[1][:26] + "…" if len(d[1]) > 27 else d[1]
        desc += f"{d[0][2:]:<8} |{d[2]:<3}| {PARTS_SHORT.get(d[3]) :<4}|{d[4]:<2}| {title}\n"
    desc += "```"
    # embed.description = desc
    print(len(desc))
    return desc


def when_data(episode_number, part, part_episode_number):
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        episodes = list(reader)

    if episode_number > 0:
        # episode_number is 1-based index in the CSV
        idx = int(episode_number)
        ep = episodes[idx]
        # Return: date, title, total episode number, part, episode number in part
        return [(ep['Date'], ep['Title'], idx, ep['Part'], ep['Episode'])]

    if part:
        if part_episode_number == 0:
            episode_list = []
            for idx, ep in enumerate(episodes):
                if ep['Part'] != part:
                    if len(episode_list) == 0: continue
                    else: break
                episode_list.append((ep['Date'], ep['Title'], idx + 1, ep['Part'], ep['Episode']))
            return episode_list
        else:
            for idx, ep in enumerate(episodes):
                if ep['Part'] == part and ep['Episode'] == str(part_episode_number):
                    return [(ep['Date'], ep['Title'], idx + 1, ep['Part'], ep['Episode'])]
            return None
    else:
        if part_episode_number == 0: return None
        episode_list = []
        for idx, ep in enumerate(episodes):
            if ep['Episode'] == str(part_episode_number):
                episode_list.append((ep['Date'], ep['Title'], idx + 1, ep['Part'], ep['Episode']))
        return episode_list


def get_table():
    table = "```python\n"
    parts = defaultdict(list)
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            part = row['Part']
            date = row['Date']
            parts[part].append(date)
    table += f"{'Part':<4} | {'Start':<8} | {'End':<8} | {'Days':<4} | {'Ep/D':<5} | {'D/Ep':<5}\n"
    table += '-' * 5 + "|" + '-' * 10 + "|" + '-' * 10 + "|" + '-' * 6 + "|" + '-' * 7 + "|" + '-' * 6 + "\n"
    for part, dates in parts.items():
        dates_dt = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        start = min(dates_dt)
        end = max(dates_dt)
        total_days = (end - start).days + 1
        episodes = len(dates)
        episodes_per_day = episodes / total_days if total_days else 0
        days_per_episode = total_days / episodes if episodes else 0
        day_format = "%d.%m.%y"
        part = PARTS_SHORT.get(part)
        table += f"{part:<4} | {start.date().strftime(day_format):>8} | {end.date().strftime(day_format):>8} | {total_days:<4} | {episodes_per_day:<5.2f} | {days_per_episode:<5.2f}\n"

    table += "```"
    return table


def get_graph(wanted_parts, compare):
    jojo_dict = []
    # Parse CSV
    with open("strunt/jojo-history.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jojo_dict.append(
                {'part': row['Part'], 'episode': row['Episode'], 'title': row['Title'], 'date': row['Date']})

    dates = []
    parts = []
    for row in jojo_dict:
        part = row['part']
        date = datetime.strptime(row['date'], "%Y-%m-%d")
        dates.append(date)
        parts.append(part)

    # Find part change indices
    part_indices = [0]
    for i in range(1, len(parts)):
        if parts[i] != parts[i - 1]:
            part_indices.append(i)
    part_indices.append(len(parts))

    # Assign colors to parts
    unique_parts = list(collections.OrderedDict.fromkeys(parts))

    # User-defined colors for each part (edit as desired)
    user_colors = {
        'Phantom Blood': '#3055A1',
        'Battle Tendency': '#952F58',
        'Stardust Crusaders - Road to Egypt': '#57508F',
        'Stardust Crusaders - Battle in Egypt': '#B7A972',
        'Diamond is Unbreakable': '#5E8CB8',
        'Golden Wind': '#E15FB6',
        'Stone Ocean': '#2F93AD',
    }
    # Fallback to tab10 if part not in user_colors
    colors = plt.cm.get_cmap('tab10', len(unique_parts))
    part_color_map = {p: user_colors.get(p, colors(i)) for i, p in enumerate(unique_parts)}

    # Filter data for selected parts
    show_parts = []
    if wanted_parts:
        part_short = wanted_parts.split(",")
        for p in part_short:
            show_parts.extend([k for k, v in PARTS_SHORT.items() if v == p.strip()])
    else:
        show_parts = list(PARTS_SHORT.keys())

    if compare:
        get_comparison(dates, parts, show_parts, part_color_map)
    else:
        get_timeline(dates, parts, show_parts, part_color_map)

    file = discord.File("strunt/jojo.png", file_name="jojo.png")
    return None, file


def get_comparison(dates, parts, show_parts, part_color_map):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))

    # For each part, plot episode count vs. days since part start
    part_progression = {}
    for part in show_parts:
        part_dates = [date for date, p in zip(dates, parts) if p == part]
        if part_dates:
            start_date = part_dates[0]
            days_since_start = [(d - start_date).days for d in part_dates]
            episode_count = list(range(1, len(part_dates) + 1))
            part_progression[part] = (days_since_start, episode_count)

    for part, (days_since_start, episode_count) in part_progression.items():
        ax.plot(days_since_start, episode_count, color=part_color_map.get(part, 'white'), label=part)
    ax.set_xlabel('Days since part start')
    ax.set_ylabel('Episode Count')
    ax.set_title('JoJo Episode Progression Comparison')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.xaxis.set_minor_locator(plt.AutoLocator())
    ax.tick_params(axis='x', which='minor', length=8, color='gray')

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())
    plt.tight_layout()
    plt.grid(color='dimgrey')
    # plt.show()
    plt.savefig('strunt/jojo.png', bbox_inches="tight", dpi=300)


def get_timeline(dates, parts, show_parts, part_color_map):
    # Set dark mode style
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))

    # Timeline progression (default)
    filtered_dates = []
    filtered_parts = []
    filtered_counts = []
    count = 0
    for i, (date, part) in enumerate(zip(dates, parts)):
        if part in show_parts:
            count += 1
            filtered_dates.append(date)
            filtered_parts.append(part)
            filtered_counts.append(count)
    # Find part change indices for filtered data
    filtered_part_indices = [0]
    for i in range(1, len(filtered_parts)):
        if filtered_parts[i] != filtered_parts[i - 1]:
            filtered_part_indices.append(i)
    filtered_part_indices.append(len(filtered_parts))
    for idx in range(len(filtered_part_indices) - 1):
        start, end = filtered_part_indices[idx], filtered_part_indices[idx + 1]
        part = filtered_parts[start]
        ax.plot(filtered_dates[start:end], filtered_counts[start:end], color=part_color_map.get(part, 'white'),
                label=part if idx == 0 or part != filtered_parts[start - 1] else "")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=24, maxticks=48))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.tick_params(axis='x', which='minor', length=8, color='gray')
    for label in ax.get_xticklabels(which='minor'):
        label.set_rotation(90)
    for label in ax.get_xticklabels(which='major'):
        label.set_rotation(90)
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Episode Count')
    ax.set_title('JoJo Episode Progression')
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())
    plt.tight_layout()
    plt.grid(color='dimgrey')
    # plt.show()
    plt.savefig('strunt/jojo.png', bbox_inches="tight", dpi=300)
