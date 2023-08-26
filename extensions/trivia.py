import random

import requests
from interactions import (
    Extension, slash_command, SlashContext, listen, ActionRow, Button, ButtonStyle, slash_option, OptionType,
    SlashCommandChoice
)
from interactions.api.events import Component

import util
import uwuifier


def setup(bot):
    Trivia(bot)
    bot.add_listener(on_component)


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
async def on_component(event: Component):
    ctx = event.ctx
    for component in Trivia.components.components:
        component.disabled = True
        if component == ctx.component: component.style = ButtonStyle.RED
        if component.label == Trivia.right: component.style = ButtonStyle.GREEN  # warning ignorable

    await ctx.edit_origin(components=Trivia.components)


class Trivia(Extension):
    components = ActionRow()
    right = ""

    @slash_command(name="trivia", description="Erhalte eine Trivia Frage", scopes=[1134856890669613210])
    @slash_option(
        name="category_option",
        description="Kategorie der Frage",
        required=False,
        opt_type=OptionType.STRING,
        choices=[SlashCommandChoice(name=k, value=CATEGORY_OPTIONS.get(k)) for k in
                 dict(sorted(CATEGORY_OPTIONS.items()))]
    )
    @slash_option(
        name="difficulty_option",
        description="Schwierigkeitsgrad",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Easy", value="easy"),
            SlashCommandChoice(name="Medium", value="medium"),
            SlashCommandChoice(name="Hard", value="hard")
        ]
    )
    async def trivia_function(self, ctx: SlashContext, category_option: str = "", difficulty_option: str = ""):
        question, choices, Trivia.right = get_trivia(category_option, difficulty_option)
        Trivia.components = ActionRow(
            Button(
                custom_id="A",
                style=ButtonStyle.GREY,
                label=choices[0],
            ),
            Button(
                custom_id="B",
                style=ButtonStyle.GREY,
                label=choices[1]
            ),
        )
        if len(choices) > 2:
            Trivia.components.add_component(
                Button(
                    custom_id="C",
                    style=ButtonStyle.GREY,
                    label=choices[2]
                ),
                Button(
                    custom_id="D",
                    style=ButtonStyle.GREY,
                    label=choices[3]
                )
            )

        await ctx.send(question, components=Trivia.components)


def get_trivia(category, difficulty):
    """ Gets a trivia question, answers and the correct answer """
    url = "https://opentdb.com/api.php?amount=1"
    if category != "": url += f"&category={category}"
    if difficulty != "": url += f"&difficulty={difficulty}"
    payload = ""

    response = requests.request("GET", url, data=payload)
    print("Api-Call Trivia: " + url)
    response = response.json()
    trivia = response['results'][0]

    question = f"Category: {trivia['category']}\n"
    question += f"Difficulty: {trivia['difficulty']}\n"
    question += f"Question: {trivia['question']}"
    question = question.replace("&quot;", '"')

    answers = trivia['incorrect_answers']
    correct = trivia['correct_answer']
    answers.append(correct)
    random.shuffle(answers)

    if random.randint(0, 5) < util.UWUCHANCE:
        question = uwuifier.UwUify(question)
        answers = [uwuifier.UwUifyWords(k) for k in answers]
        correct = uwuifier.UwUifyWords(correct)

    return question, answers, correct
