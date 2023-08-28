import json
import random

import interactions
from interactions import (
    Extension, slash_command, SlashContext, listen, ActionRow, Button, ButtonStyle, slash_option, OptionType,
    SlashCommandChoice
)
from interactions.api.events import Component

""" Hangman based on https://github.com/Sv443/Node-Hangman#readme """


def setup(bot):
    Hangman(bot)
    bot.add_listener(on_hangman_component)


@listen()
async def on_hangman_component(event: Component):
    ctx = event.ctx
    if not ctx.custom_id.startswith("hangman"): return
    component = None
    for actionrows in Hangman.COMPONENTS:
        for comp in actionrows.components:
            if comp == ctx.component:
                component = comp
                break
        if component is not None: break

    if not build_censored_word(component.label):
        component.style = ButtonStyle.RED
        Hangman.stage += 1
    else: component.style = ButtonStyle.GREEN

    win = Hangman.word.find("_") == -1
    loss = Hangman.stage == 11
    if win or loss:
        for actionrows in Hangman.COMPONENTS:
            for comp in actionrows.components: comp.disabled = True

    component.disabled = True
    await ctx.edit_origin(embed=build_embed(win, loss), components=Hangman.COMPONENTS)


class Hangman(Extension):
    COMPONENTS: list[ActionRow]
    WORD_TO_GUESS: str
    word: str
    stage = 0

    @slash_command(name="hangman", description="Spiele Galgenmännchen")
    @slash_option(
        name="lang_option",
        description="Sprache des Wortes",
        required=False,
        opt_type=OptionType.BOOLEAN,
        choices=[
            SlashCommandChoice(name="Deutsch", value=True),
            SlashCommandChoice(name="Englisch", value=False)
        ]
    )
    @slash_option(
        name="difficulty_option",
        description="Schwierigkeit des Wortes",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Einfach", value="easy"),
            SlashCommandChoice(name="Normal", value="normal"),
            SlashCommandChoice(name="Hart", value="hard")
        ]
    )
    async def hangman_function(self, ctx: SlashContext, lang_option: bool = True, difficulty_option: str = ""):
        ar1, ar2, ar3, ar4, ar5 = ActionRow(), ActionRow(), ActionRow(), ActionRow(), ActionRow()
        for c in ['A', 'B', 'C', 'D', 'E']: ar1.add_component(
            Button(custom_id=f"hangman_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['F', 'G', 'H', 'I', 'J/Q']: ar2.add_component(
            Button(custom_id=f"hangman_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['K', 'L', 'M', 'N', 'O']: ar3.add_component(
            Button(custom_id=f"hangman_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['P', 'R', 'S', 'T', 'U']: ar4.add_component(
            Button(custom_id=f"hangman_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['V', 'W', 'X', 'Y', 'Z']: ar5.add_component(
            Button(custom_id=f"hangman_{c}", style=ButtonStyle.GREY, label=c))

        Hangman.COMPONENTS = [ar1, ar2, ar3, ar4, ar5]

        Hangman.WORD_TO_GUESS = get_word(lang_option, difficulty_option)
        build_censored_word()
        await ctx.send(embed=build_embed(False, False), components=Hangman.COMPONENTS)


def get_word(in_german, difficulty_option):
    """ Returns a random word used for the game """
    file = "resources/hangman_words-de.json" if in_german else "resources/hangman_words-en.json"
    difficulty = random.choice(["easy", "normal", "hard"]) if difficulty_option == "" else difficulty_option
    with open(file, encoding="utf-8") as f: words = json.load(f)
    word = random.choice(words[difficulty])
    return word.upper()


def build_censored_word(letter=None):
    """ Builds a censored word and changes it according to the given letter """
    if letter is None:
        Hangman.word = "_ " * len(Hangman.WORD_TO_GUESS)
        return True
    if letter in Hangman.WORD_TO_GUESS:
        indices = [i for i, ltr in enumerate(Hangman.WORD_TO_GUESS) if ltr == letter]
        word = Hangman.word.split(" ")
        for i in range(len(word)):
            if i in indices: word[i] = word[i].replace("_", letter)
        word = " ".join(word)
        Hangman.word = word
        return True
    return False


def build_embed(win, loss):
    """ Returns an embed """
    embed = interactions.Embed(title="Galgenmännchen")
    name = ""
    if win: name += "GEWONNEN\n"
    if loss: name += "VERLOREN\n"
    name += f"```{Hangman.word}```"
    value = build_stage()

    embed.add_field(name, value)
    return embed


def build_stage():
    """ Returns the game stage """
    with open("resources/hangman.json", encoding="utf-8") as f: graphic = json.load(f)
    stage = "```\n"
    stage += f"{graphic['ceiling']}\n"
    for line in graphic['stages'][Hangman.stage]:
        stage += f"{graphic['stageLinePrefix']}{graphic['stages'][Hangman.stage][line]}{graphic['stageLineSuffix']}\n"
    stage += f"{graphic['floor']}\n"
    stage += "```"
    return stage
