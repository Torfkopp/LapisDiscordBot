import datetime
import io
import math
import random

import interactions
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import requests
from PIL import Image
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)
from interactions.models import discord

import secret
import util
from core import log


def setup(bot): Weather(bot)


COLOUR = util.Colour.WEATHER.value
API_KEY = util.WEATHER_KEY
LOCATIONS = secret.LOCATIONS


def is_sun_killing(now):
    """ Returns an embed (and sometimes also a file) if it is very hot (or cold) """
    weather_dic = {}

    for location, code in LOCATIONS.items():
        lat, lon = code[0], code[1]

        log.write(f"Api-Call Weather Forecast {location.title()}")
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast?",
            params={
                "lat": lat,
                "lon": lon,
                "APPID": API_KEY,
                "units": "metric"
            }
        )

        data = response.json()
        temperatures = []

        for w in data["list"]:
            date = w["dt_txt"]
            if datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date() != now.date(): continue
            temperatures.append((w["main"]["feels_like"], w["main"]["temp"]))

        weather_dic[location] = temperatures

    max_temps, min_temps = {}, {}
    for location, temps in weather_dic.items():
        max_temps[location], min_temps[location] = max(temps, key=lambda t: t[0]), min(temps, key=lambda t: t[0])
    avg_heat = sum(i for i, _ in max_temps.values()) / len(max_temps.values())
    avg_cold = sum(i for i, _ in max_temps.values()) / len(max_temps.values())

    gif, title = None, None
    if avg_heat > 27.0:
        title = f"\"Pretty much everywhere, it's gonna be hot\""
        gif = util.get_gif("hot")

    elif avg_cold < 2.0:
        title = random.choice([
            "\"It's the perfect texture for running\"",
            "I’m an untrained meteorologist... reporting on the snow... it’s in the streets"
        ])
        gif = util.get_gif("cold")

    if not title or not gif: return None, None

    embed = interactions.Embed(title=title)
    description = f"Heute erreichen wir (gefühlte):\n```python\n"
    for loc, temp in max_temps.items():
        real, felt = f"{temp[1]:.2f}".rjust(5), f"({temp[0]:.2f})".rjust(7)
        description += f"{loc.title()}:".ljust(15) + f"{real} {felt} °C\n"
    embed.description = description + "```"

    if gif == "killing_sun.png":
        file = discord.File("resources/killing_sun.png", file_name="killing_sun.png")
        embed.image = 'attachment://killing_sun.png'
    else:
        embed.image = gif
        file = None

    return embed, file


def location_slash_option():
    def wrapper(func):
        return slash_option(
            name="location",
            description="Ort",
            required=False,
            opt_type=OptionType.STRING,
            choices=[SlashCommandChoice(name=k.title(), value=k) for k in LOCATIONS]
        )(func)

    return wrapper


class Weather(Extension):
    @slash_command(name="weather", description="Wetter")
    async def weather_function(self, ctx: SlashContext): await ctx.send("Weather")

    @weather_function.subcommand(sub_cmd_name="forecast", sub_cmd_description="Wetter für die nächsten 5 Tage")
    @slash_option(
        name="location",
        description=f"Ort(e) (Komma getrennt) [{','.join(LOCATIONS.keys())}]",
        required=False,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="time",
        description="Zeitbegrenzung (in h)",
        required=False,
        opt_type=OptionType.INTEGER,
        min_value=1,
        max_value=120
    )
    async def forecast_function(self, ctx: SlashContext, location="leer", time=None):
        await ctx.defer()
        embed, file = get_five(location, time)
        await ctx.send(embed=embed, file=file)

    @weather_function.subcommand(sub_cmd_name="now", sub_cmd_description="Wetter jetzt gerade")
    @location_slash_option()
    async def now_function(self, ctx: SlashContext, location="leer"):
        await ctx.defer()
        embed = get_now(location)
        await ctx.send(embed=embed)

    @weather_function.subcommand(sub_cmd_name="map", sub_cmd_description="Temperaturkarte Deutschlands")
    async def map_function(self, ctx: SlashContext):
        await ctx.defer()
        embed, file = get_germany()
        await ctx.send(embed=embed, file=file)


def get_five(location, time):
    weather_dic = {}
    if time: time = math.ceil(time / 3) + 1

    locations = LOCATIONS.keys() if location == "all" else [l.strip() for l in location.lower().split(",")]

    for loca in locations:
        if loca not in LOCATIONS: continue
        coords = LOCATIONS.get(loca)

        log.write(f"Api-Call Weather Forecast {loca.title()}")
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast?",
            params={
                "lat": coords[0],
                "lon": coords[1],
                "APPID": API_KEY,
                "units": "metric"
            }
        )

        data = response.json()
        temperatures = {}

        for w in data["list"]:
            date = w["dt_txt"]
            date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            temperatures[date] = w["main"]["temp"]

        weather_dic[loca] = temperatures

    plt.style.use('dark_background')
    fig, ax = plt.subplots()

    for loc, temps in weather_dic.items():
        ax.plot(list(temps.keys())[:time], list(temps.values())[:time], label=loc.title())

    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature in °C")

    # Set major ticks to daily
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%A'))
    # Set minor ticks to hourly
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
    # Rotate and align tick labels
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='center', fontsize=10)
    plt.setp(ax.xaxis.get_minorticklabels(), rotation=90, ha='center', fontsize=4)

    ax.tick_params(axis='x', which='minor', labelsize=6)

    ax.legend()
    plt.suptitle(f"Wetter in {location.title()}")
    plt.xticks(rotation=90)
    plt.tight_layout()

    plt.savefig("strunt/weather.png")
    file = discord.File('strunt/weather.png', file_name="weather.png")

    return None, file


def get_now(location):
    lat, lon = LOCATIONS.get(location)
    log.write("Api-Call Weather Now")
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather?",
        params={
            "lat": lat,
            "lon": lon,
            "APPID": API_KEY,
            "units": "metric"
        }
    )
    data = response.json()

    weather = f"**Uhrzeit**: {datetime.datetime.fromtimestamp(data['dt'])}\n"
    weather += f"\n**Wetter**: {data['weather'][0]['main']} ({data['weather'][0]['description']})\n"
    weather += f"**Temperatur**: {data['main']['temp']}° (gefühlt {data['main']['feels_like']}°)\n"
    weather += f"**Luftfeuchtigkeit**: {data['main']['humidity']} %\n"

    weather += f"\n**Sichtbarkeit**: {data['visibility']} m\n"
    weather += f"**Wind**: {data['wind']['speed']} km/h von {data['wind']['deg']}°\n"
    weather += f"**Bewölkung**: {data['clouds']['all']} %\n"

    if 'rain' in data: weather += f"**Regen**: {data['rain']['1h']} mm/h\n"
    if 'snow' in data: weather += f"**Schnee** {data['snow']['1h']} mm/h\n"

    weather += f"\n**Sonnenaufgang**: {datetime.datetime.fromtimestamp(data['sys']['sunrise']).time()} Uhr\n"
    weather += f"**Sonnenuntergang**: {datetime.datetime.fromtimestamp(data['sys']['sunset']).time()} Uhr\n"

    embed = interactions.Embed(title=f"Wetter in {location.title()}", color=COLOUR)
    embed.description = weather

    return util.uwuify_by_chance(embed)


def get_germany():
    r = requests.get(f"https://tile.openweathermap.org/map/temp_new/4/8/5.png?appid={API_KEY}")
    log.write("Api-Call Temperature Map")
    overlay = Image.open(io.BytesIO(r.content))
    background = Image.open("resources/germany.png")

    background = background.convert("RGBA")
    overlay = overlay.convert("RGBA")

    new_img = Image.blend(background, overlay, alpha=0.5)
    new_img.save("strunt/temperature.png", "PNG")

    file = discord.File("strunt/temperature.png", file_name="temperature.png")

    return None, file
