import interactions
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType,
    SlashCommandChoice
)

import util


def setup(bot): Modmail(bot)


class Modmail(Extension):
    @slash_command(name="modmail", description="Sende dein Anliegen an die Mods")
    @slash_option(
        name="name",
        description="Dein Name",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="category",
        description="Kategorie des Anliegens",
        required=True,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Antrag", value="Antrag"),
            SlashCommandChoice(name="Hilfe", value="Hilfe"),
            SlashCommandChoice(name="Bot Feature Request", value="Bot Feature Request"),
            SlashCommandChoice(name="Server Feature Request", value="Server Feature Request"),
            SlashCommandChoice(name="Rechte", value="Rechte"),
            SlashCommandChoice(name="Beschwerde", value="Beschwerde"),
            SlashCommandChoice(name="Wüste Beschimpfung", value="Beschimpfung"),
            SlashCommandChoice(name="Sonstiges", value="Sonstiges"),
        ]
    )
    @slash_option(
        name="short_form",
        description="Anliegen in Kurzform",
        required=True,
        opt_type=OptionType.STRING,
        max_length=50
    )
    @slash_option(
        name="long_form",
        description="Weitere Ausführungen",
        required=False,
        opt_type=OptionType.STRING
    )
    async def modmail_function(self, ctx: SlashContext, name, category, short_form, long_form: str = ""):
        file = interactions.models.discord.File("lapis_pics/Lapis2.jpg", "Lapis2.jpg")
        # noinspection PyTypeChecker
        embed = interactions.Embed(title="Modmail", color=util.Colour.MODMAIL.value,
                                   thumbnail="attachment://Lapis2.jpg")
        embed.add_field(name="Antragsteller", value=name)
        embed.add_field(name="Kategorie", value=category)
        embed.add_field(name="Kurzform", value=short_form)
        embed.add_field(name="Ausführungen", value=long_form)
        '''message = f"Antragssteller: {name}\n"
        message += f"Kategorie: {category}\n"
        message += f"Kurzform: {short_form}\n"
        message += f"Ausführungen: {long_form}"'''
        await ctx.send("Anliegen versendet")
        await self.bot.get_channel(util.MODERATOREN_CHANNEL_ID).send(file=file, embed=embed)
        await ctx.delete()
