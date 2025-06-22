import datetime
import io
import random

import interactions
import matplotlib.pyplot as plt
import requests
from PIL import Image
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice
)
from interactions.models import discord

import util
from core import log


def setup(bot): Weather(bot)


COLOUR = util.Colour.WEATHER.value
API_KEY = util.WEATHER_KEY


def is_sun_killing(now):
    lat, lon = LOCATIONS.get("leer")
    log.write("Api-Call Weather Forecast")
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

    weather_dic = {}

    for w in data["list"]:
        date = w["dt_txt"]
        if datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date() != now.date(): continue
        weather_dic[date] = w["main"]["feels_like"]

    max_temp = max(weather_dic.values())
    min_temp = min(weather_dic.values())

    if max_temp > 28.0:
        title = f"\"Pretty much everywhere, it's gonna be hot\""
        gif = util.get_gif("hot")

        embed = interactions.Embed(title=title)
        embed.description = f"Heute erreichen wir gefühlte {max_temp}°"

        if gif == "killing_sun.png":
            file = discord.File("resources/killing_sun.png", file_name="killing_sun.png")
            embed.image = 'attachment://killing_sun.png'
        else:
            embed.image = gif
            file = None
        return embed, file
    elif min_temp < 2.0:
        title = random.choice([
            "\nIt's the perfect texture for running\"",
            "I’m an untrained meteorologist... reporting on the snow... it’s in the streets"
        ])
        gif = util.get_gif("cold")

        embed = interactions.Embed(title=title)
        embed.description = f"Heute erreichen wir gefühlte {min_temp}°"
        embed.image = gif
        return embed, None

    return None, None


LOCATIONS = {
    "leer": (53.226125, 7.455963)
}


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
    @location_slash_option()
    async def forecast_function(self, ctx: SlashContext, location="leer"):
        await ctx.defer()
        embed, file = get_five(location)
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


def get_five(location):
    lat, lon = LOCATIONS.get(location)
    log.write("Api-Call Weather Forecast")
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
    weather_dic = {}

    for w in data["list"]:
        date = w["dt_txt"]
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%d. %H:00")
        weather_dic[date] = w["main"]["temp"]

    plt.style.use('dark_background')
    fig, ax = plt.subplots()
    plt.plot(list(weather_dic.keys()), list(weather_dic.values()))
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature in C°")
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
    weather += f"**Temperature**: {data['main']['temp']}° (gefühlt {data['main']['feels_like']}°)\n"
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
