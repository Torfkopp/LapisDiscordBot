import html
import random

import interactions
import requests
from interactions import (
    Extension, slash_command, SlashContext, listen, ActionRow, Button, ButtonStyle, slash_option, OptionType,
    SlashCommandChoice
)
from interactions.api.events import Component

import util
import uwuifier
from core import log


def setup(bot):
    Trivia(bot)
    bot.add_listener(on_trivia_component)


CATEGORY_OPTIONS = {
    "General Knowledge": "9",
    "Books": "10",
    "Films": "11",
    "Music": "12",
    "Musicals & Theatres": "13",
    "Television": "14",
    "Video Games": "15",
    "Board Games": "16",
    "Science & Nature": "17",
    "Computers": "18",
    "Mathematics": "19",
    "Mythology": "20",
    "Sports": "21",
    "Geography": "22",
    "History": "23",
    "Politics": "24",
    "Art": "25",
    "Celebrities": "26",
    "Animals": "27",
    "Vehicles": "28",
    "Comics": "29",
    "Science Gadgets": "30",
    "Anime & Manga": "31",
    "Cartoon & Animations": "32",
}


@listen()
async def on_trivia_component(event: Component):
    ctx = event.ctx
    if not ctx.custom_id.startswith("trivia"): return
    # Uncomment (and remove content parameter) if only author should be able to answer
    # if ctx.author_id != Trivia.author_id: return
    for component in Trivia.components.components:
        component.disabled = True
        if component == ctx.component: component.style = ButtonStyle.RED
        # noinspection PyUnresolvedReferences
        if component.label == Trivia.right: component.style = ButtonStyle.GREEN  # warning ignorable
    if ctx.message.content != "": return  # To prevent an overwriting when two answer contemporaneously
    await ctx.edit_origin(components=Trivia.components, content=f"Beantwortet von: {ctx.author.display_name}")


class Trivia(Extension):
    components = ActionRow()
    right: str
    author_id = None

    @slash_command(name="trivia", description="Erhalte eine Trivia-Frage")
    @slash_option(
        name="category",
        description="Kategorie der Frage",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k, value=CATEGORY_OPTIONS.get(k)) for k in
                 dict(sorted(CATEGORY_OPTIONS.items()))]  # sorted by alphabet
    )
    @slash_option(
        name="difficulty",
        description="Schwierigkeitsgrad",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Easy", value="easy"),
            SlashCommandChoice(name="Medium", value="medium"),
            SlashCommandChoice(name="Hard", value="hard")
        ]
    )
    async def trivia_function(self, ctx: SlashContext, category: str = "", difficulty: str = ""):
        Trivia.author_id = ctx.author_id
        question, choices, Trivia.right = get_trivia(category, difficulty)
        Trivia.components = ActionRow(
            Button(
                custom_id="trivia_A",
                style=ButtonStyle.GREY,
                label=choices[0],
            ),
            Button(
                custom_id="trivia_B",
                style=ButtonStyle.GREY,
                label=choices[1]
            ),
        )
        if len(choices) > 2:
            Trivia.components.add_component(
                Button(
                    custom_id="trivia_C",
                    style=ButtonStyle.GREY,
                    label=choices[2]
                ),
                Button(
                    custom_id="trivia_D",
                    style=ButtonStyle.GREY,
                    label=choices[3]
                )
            )

        embed = interactions.Embed(title="Trivia", description=question, color=util.Colour.TRIVIA.value)

        await ctx.send(embed=embed, components=Trivia.components)


def get_trivia(category, difficulty):
    """ Gets a trivia question, answers and the correct answer """
    url = "https://opentdb.com/api.php?amount=1"
    if category != "": url += f"&category={category}"
    if difficulty != "": url += f"&difficulty={difficulty}"
    payload = ""

    try:
        log.write("Api-Call Trivia: " + url)
        response = requests.request("GET", url, data=payload)
        response = response.json()
        trivia = response['results'][0]
    except (KeyError, requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError):
        log.write("API DOWN")
        return util.get_error_embed("api_down")

    question = f"Category: {trivia['category']}\n"
    question += f"Difficulty: {trivia['difficulty']}\n"
    question += "\n"
    question += f"Question: {trivia['question']}"
    question = html.unescape(question)

    answers = trivia['incorrect_answers']
    correct = trivia['correct_answer']
    answers.append(correct)
    answers = [html.unescape(x) for x in answers]
    random.shuffle(answers)

    if util.get_if_uwuify():
        question = uwuifier.UwUify(question)
        answers = [uwuifier.UwUifyWords(k) for k in answers]
        correct = uwuifier.UwUifyWords(correct)

    return question, answers, correct
