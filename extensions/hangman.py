import json
import random

import interactions
from interactions import (
    Extension, slash_command, SlashContext, listen, ActionRow, Button, ButtonStyle, slash_option, OptionType,
    SlashCommandChoice
)
from interactions.api.events import Component

import util

""" Hangman based on https://github.com/Sv443/Node-Hangman """


def setup(bot):
    Hangman(bot)
    bot.add_listener(on_hangman_component)


@listen()
async def on_hangman_component(event: Component):
    ctx = event.ctx
    if not ctx.custom_id.startswith("hangman"): return
    # noinspection PyUnresolvedReferences
    hangmanclass = Hangman.hangmanClasses.get(ctx.component.custom_id.split("_")[1])
    embed, component = hangmanclass.on_component(ctx)
    await ctx.edit_origin(embed=embed, components=component)


class HangmanClass:
    def __init__(self, word, author):
        self.word_to_guess = word
        self.word = "_ " * len(self.word_to_guess)
        self.stage = 0
        self.id = self.create_id()
        self.participants: set = {author}

        ar1, ar2, ar3, ar4, ar5 = ActionRow(), ActionRow(), ActionRow(), ActionRow(), ActionRow()
        for c in ['A', 'B', 'C', 'D', 'E']: ar1.add_component(
            Button(custom_id=f"hangman_{self.id}_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['F', 'G', 'H', 'I', 'J/Q']: ar2.add_component(
            Button(custom_id=f"hangman_{self.id}_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['K', 'L', 'M', 'N', 'O']: ar3.add_component(
            Button(custom_id=f"hangman_{self.id}_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['P', 'R', 'S', 'T', 'U']: ar4.add_component(
            Button(custom_id=f"hangman_{self.id}_{c}", style=ButtonStyle.GREY, label=c))
        for c in ['V', 'W', 'X', 'Y', 'Z']: ar5.add_component(
            Button(custom_id=f"hangman_{self.id}_{c}", style=ButtonStyle.GREY, label=c))

        self.components = [ar1, ar2, ar3, ar4, ar5]

    def create_id(self):
        return str(hash(self.word_to_guess + str(random.randrange(10))))

    def build_censored_word(self, letter=None):
        """ Builds a censored word and changes it according to the given letter """
        if letter is None:
            self.word = "_ " * len(self.word_to_guess)
            return True
        if letter in self.word_to_guess:
            indices = [i for i, ltr in enumerate(self.word_to_guess) if ltr == letter]
            word = self.word.split(" ")
            for i in range(len(word)):
                if i in indices: word[i] = word[i].replace("_", letter)
            word = " ".join(word)
            self.word = word
            return True
        return False

    def build_embed(self, win, loss):
        """ Returns an embed """
        embed = interactions.Embed(title="Galgenmännchen", color=util.Colour.HANGMAN.value)
        name = ""
        if win: name += "GEWONNEN\n"
        if loss:
            name += "VERLOREN\n"
            name += f"Wort: {self.word_to_guess}\n"
        name += f"```{self.word}```"
        value = build_stage(self.stage)
        embed.add_field(name, value)
        embed.add_field("An diesem Galgenmännchen beteiligte Personen:", ', '.join(self.participants))
        return embed, self.components

    def on_component(self, ctx):
        component = None
        self.participants.add(ctx.author.display_name)
        for actionrows in self.components:
            for comp in actionrows.components:
                if comp == ctx.component:
                    component = comp
                    break
            if component is not None: break

        # noinspection PyUnresolvedReferences
        if not self.build_censored_word(component.label):
            component.style = ButtonStyle.RED
            self.stage += 1
        else: component.style = ButtonStyle.GREEN

        win = self.word.find("_") == -1
        loss = self.stage == 11
        embed, _ = self.build_embed(win, loss)
        if win or loss:
            for actionrows in self.components:
                for comp in actionrows.components: comp.disabled = True
                self.stage = 0

        component.disabled = True

        return embed, self.components

    async def sent(self, ctx):
        embed, components = self.build_embed(False, False)
        await ctx.send(embed=embed, components=components)


class Hangman(Extension):
    hangmanClasses = {}

    @slash_command(name="hangman", description="Spiele Galgenmännchen")
    @slash_option(
        name="language",
        description="Sprache ist Deutsch (alt. Englisch)",
        required=False,
        opt_type=OptionType.BOOLEAN,
        choices=[
            SlashCommandChoice(name="Deutsch", value=True),
            SlashCommandChoice(name="Englisch", value=False)
        ]
    )
    @slash_option(
        name="difficulty",
        description="Schwierigkeit des Wortes",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Einfach", value="easy"),
            SlashCommandChoice(name="Normal", value="normal"),
            SlashCommandChoice(name="Hart", value="hard")
        ]
    )
    async def hangman_function(self, ctx: SlashContext, language: bool = True, difficulty: str = ""):
        hc = HangmanClass(get_word(language, difficulty), ctx.author.display_name)
        Hangman.hangmanClasses[hc.id] = hc
        await hc.sent(ctx)


def get_word(in_german, difficulty_option):
    """ Returns a random word used for the game """
    file = "resources/hangman_words-de.json" if in_german else "resources/hangman_words-en.json"
    difficulty = random.choice(["easy", "normal", "hard"]) if difficulty_option == "" else difficulty_option
    with open(file, encoding="utf-8") as f: words = json.load(f)
    word = random.choice(words[difficulty])
    return word.upper()


def build_stage(current_stage):
    """ Returns the game stage """
    with open("resources/hangman.json", encoding="utf-8") as f: graphic = json.load(f)
    stage = "```\n"
    stage += f"{graphic['ceiling']}\n"
    for line in graphic['stages'][current_stage]:
        stage += f"{graphic['stageLinePrefix']}{graphic['stages'][current_stage][line]}{graphic['stageLineSuffix']}\n"
    stage += f"{graphic['floor']}\n"
    stage += "```"
    return stage
