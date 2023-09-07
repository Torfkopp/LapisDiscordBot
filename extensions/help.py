import interactions
from interactions import (
    Extension, slash_command, SlashContext
)
from interactions.ext.paginators import Paginator

import util


def setup(bot): Help(bot)


COLOUR = util.Colour.HELP.value


class Help(Extension):

    @slash_command(name="help", description="Auflistung der Befehle")
    async def help_function(self, ctx: SlashContext):
        embeds = [get_help(), _formula1_help()]
        paginator = Paginator.create_from_embeds(self.bot, *embeds)
        await paginator.send(ctx)


# noinspection PyTypeChecker
def get_help():
    embed = interactions.Embed(title="Hilfe", color=COLOUR,
                               thumbnail="https://raw.githubusercontent.com/Torfkopp/LapisDiscordBot/master/resources"
                                         "/Lapis2.jpg")
    embed.description = "Lapis hilft dir gerne! :)\nHier die Auflistung aller Befehle"
    embed.add_field(name="Fußball",
                    value="/football goalgetter: Gibt die Topscorer der Liga zurück\n"
                          "/football matchday: Gibtn Spieltag der Liga in der Saison\n"
                          "/football matches: Alle Spiele des Teams von vor y und bis in x Wochen\n"
                          "/football table: Tabelle der Liga in der Saison")
    embed.add_field(name="Anime",
                    value="/anime action: Tue einer Person eine Animeaktion an"
                          "/anime quote: Zufälliges Anime Zitat\n"
                          "/anime reaction: Zufällige Anime Bewegtbildreaktion")
    embed.add_field(name="Free Games", value="/freegames: Erhalte momentan kostenlos erhaltbare PC-Spiele")
    embed.add_field(name="Hangman", value="/hangman: Spiele Galgenmännchen")
    embed.add_field(name="Help", value="/help: Siehste selber")
    embed.add_field(name="Insults",
                    value="/insult: Erhalte eine zufällige Beleidigung\n"
                          "/yomomma: Erhalte eine zufällige Beschreibung deiner Mutter")
    embed.add_field(name="Joke",
                    value="/joke dad_joke: Erhalte einen zufälligen Dad Joke\n"
                          "/joke joke: joke\n"
                          "/joke stammrunde: Erhalte einen zufälligen Fakt über ein Stammrundenmitglied")
    embed.add_field(name="LoLPatchnotes",
                    value="/patch image: Erhalte das Patchzusammenfassungsbild\n"
                          "/patch summary: Erhalte die Zusammenfassungstexte der Änderungen\n"
                          "/patch details: Erhalte die Änderungen des Patches im Details")
    embed.add_field(name="LoLEsports",
                    value="/lol results: Die Ergebnisse der letzten Matches\n"
                          "/lol standings: Die Standings der Liga\n"
                          "/lol upcoming: Die nächsten Matches")
    embed.add_field(name="Quotes", value="/advice: Erhalte einen zufälligen Ratschlag")
    embed.add_field(name="Trivia", value="/trivia: Erhalte eine Trivia-Frage")

    return util.uwuify_by_chance(embed)


def _formula1_help():
    # noinspection PyTypeChecker
    embed = interactions.Embed(title="Formel 1 Hilfe", color=COLOUR,
                               description="Hier die Auflistung aller Formel1 Befehle",
                               thumbnail="https://raw.githubusercontent.com/Torfkopp/LapisDiscordBot/master/resources"
                                         "/Lapis2.jpg")
    embed.add_field(name="Formel 1",
                    value="/result: Ergebnis der Session\n"
                          "/next: Das nächstes Rennwochenende oder alle verbleibenden Rennen"
                    )
    embed.add_field(name="Formel 1 - LAPS",
                    value="/laps overview: Übersicht der schnellsten Runden der Session\n"
                          "/laps compare: Vergleicht die schnellsten Runden der beiden Fahrer (km/h pro Meter)\n"
                          "/laps scatterplot: Scatterplot der Runden des Fahrers\n"
                          "/laps telemetry: Telemetriedaten der schnellsten Runden der beiden Fahrer\n"
                          "/laps track_dominance: Vergleicht schnellste Runden der beiden Fahrer (Telemetrie)"
                    )
    embed.add_field(name="Formel 1 - RACEINFO",
                    value="/raceinfo position: Positionsveränderungen während des Rennens\n"
                          "/raceinfo ltd: Lap Time Distribution der ersten 10 Fahrer für das Rennen\n"
                          "/raceinfo tyre: Reifenstrategieübersicht für das Rennen"
                    )
    embed.add_field(name="Formel 1 - STANDINGS",
                    value="/standings table: Rangliste der Saison\n"
                          "/standings average: Durchschnittliche Position im Sessiontyp\n"
                          "/standings h2h: Head2Head-Vergleich im Sessiontyp\n"
                          "/standings heatmap: Heatmap für die Rennen aller Fahrer in der Saison\n"
                          "/standings winnable: Für welchen Fahrer ist die Meisterschaft noch winnable?"
                    )
    return util.uwuify_by_chance(embed)
