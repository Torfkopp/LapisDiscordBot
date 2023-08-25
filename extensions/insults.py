import requests
from interactions import (
    Extension, OptionType, slash_option, slash_command, SlashContext, SlashCommandChoice
)

""" File for the insult commands """


def setup(bot): Insults(bot)


class Insults(Extension):
    @slash_command(name="insult", description="Gibt eine zufällige Beleidigung zurück")
    @slash_option(
        name="language_option",
        description="Sprache des Witzes",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Deutsch", value="de"),
            SlashCommandChoice(name="Ängelsächsisch", value="en"),
            SlashCommandChoice(name="Italienisch", value="it"),
            SlashCommandChoice(name="Spanisch", value="es"),
            SlashCommandChoice(name="Franzakisch", value="fr")]
    )
    async def insult_function(self, ctx: SlashContext, language_option: str = "en"):
        await ctx.send(get_insult(language_option))


def get_insult(lang):
    """ Return an insult in the specified language """
    url = "https://evilinsult.com/generate_insult.php"

    querystring = {"lang": lang, "type": "json"}

    payload = ""
    response = requests.request("GET", url, data=payload, params=querystring)
    print("Api-Call Insults: " + url)

    response = response.json()
    insult = response['insult']

    if lang != "en" and response['comment'] != "": insult += f" (Translation: {response['comment']}"

    return insult
