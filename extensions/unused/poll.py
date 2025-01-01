import random

import interactions
from interactions import (
    Extension, slash_command, SlashContext, listen, ActionRow, Button, ButtonStyle, slash_option, OptionType
)
from interactions.api.events import Component

import util

loading_bar = {
    0: "▱",
    1: "▰",
}


def setup(bot):
    Poll(bot)
    bot.add_listener(on_poll_component)


@listen()
async def on_poll_component(event: Component):
    ctx = event.ctx
    if not ctx.custom_id.startswith("poll"): return
    # noinspection PyUnresolvedReferences
    embed = Poll.pollClasses.get(ctx.component.custom_id.split("_")[1]).make_embed(ctx.component.label, ctx.author)
    await ctx.edit_origin(embed=embed)


class PollClass:
    def __init__(self, question, with_names, answers):
        self.question = question
        self.with_names = with_names
        self.id = self.create_id()
        answer_components = answers.split(",")
        # Maybe make more rows for more answer possibilities
        self.answers = [a.strip() for a in answer_components][:5]
        components = []
        for com in self.answers:
            components.append(
                Button(
                    custom_id=f"poll_{self.id}_{com}",
                    style=ButtonStyle.GREY,
                    label=com
                )
            )
        self.components = ActionRow(*components)
        self.answer_user_dict = {a: set() for a in self.answers}

    def create_id(self):
        return str(hash(self.question + str(random.randrange(10))))

    def make_embed(self, component, author):
        amount = 0
        if component is not None and author is not None:
            for answer in self.answers:
                answer_list = self.answer_user_dict.get(answer)
                amount += len(answer_list)
                if author in answer_list:
                    amount -= 1
                    answer_list.remove(author)
            self.answer_user_dict.get(component).add(author)
            amount += 1

        embed = interactions.Embed(title=self.question, color=util.Colour.POLL.value)

        for answer in self.answers:
            answer_amount = len(self.answer_user_dict.get(answer))
            pertenth = (0 if amount == 0 else answer_amount / amount) * 10
            percent = str(int(pertenth * 10))
            pertenth = int(pertenth)
            bar = f"{loading_bar.get(1) * pertenth}{loading_bar.get(0) * (10 - pertenth)}"
            percentage = ('\u00A0' * (4 - len(percent)) + percent)
            value = f"{bar} `{percentage}` %  | `{answer_amount}`"
            if self.with_names: value += "\n" + ', '.join(a.display_name for a in self.answer_user_dict.get(answer))
            embed.add_field(name=answer, value=value)

        return embed

    def sent(self):
        return self.make_embed(None, None), self.components


class Poll(Extension):
    pollClasses = {}

    @slash_command(name="poll", description="Erstelle eine Umfrage")
    @slash_option(
        name="question",
        description="Umfragefrage",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="with_names",
        description="Ob Namen angezeigt werden sollen",
        required=False,
        opt_type=OptionType.BOOLEAN
    )
    @slash_option(
        name="answers",
        description="Antwortmöglichkeiten mit Komma (Zwischen 1 und 5)",
        required=False,
        opt_type=OptionType.STRING
    )
    async def poll_function(self, ctx: SlashContext, question, with_names: bool = True, answers: str = "Ja, Nein"):
        pc = PollClass(question, with_names, answers)
        Poll.pollClasses[pc.id] = pc
        await ctx.send(embed=pc.make_embed(None, None), components=pc.components)
