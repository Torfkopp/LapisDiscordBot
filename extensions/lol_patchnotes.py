import datetime

import interactions
import pytz
import requests
from bs4 import BeautifulSoup
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType,
    SlashCommandChoice
)
from interactions.ext.paginators import Paginator

import util


def setup(bot): LoLPatchnotes(bot)


PATCH_LANGUAGE = "de-de"

'''
##################################################
AUTOMATIC PART
##################################################
'''


def update():
    """ Updates the url and soup to the newest patch notes """
    url = f"https://www.leagueoflegends.com/{PATCH_LANGUAGE}/news/tags/patch-notes/"
    response = requests.get(url)
    print("Request page LoLPatch: " + url)
    soup = BeautifulSoup(response.content, 'html.parser')
    latest_patch_link = soup.find('a', href=True)
    latest_patch_link = latest_patch_link['href']

    url = f"https://www.leagueoflegends.com{latest_patch_link}"
    response = requests.get(url)
    print("Request page LoLPatch: " + url)
    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.find('h1', class_="style__Title-sc-vd48si-5 kDFvhf").text
    time = soup.find('time')['datetime']
    time = datetime.datetime.fromisoformat(time)
    time = time.astimezone(pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
    patch_update = soup.find('h2', id="patch-midpatch-updates")
    patch_update = patch_update is not None

    LoLPatchnotes.url = url
    LoLPatchnotes.soup = soup
    LoLPatchnotes.title = title

    if patch_update:
        try:  # If a midpatch update exists in the iteration but didn't exist in the last one, call the method
            if not LoLPatchnotes.patch_update: return get_midpatch_update()
        except NameError: pass
    LoLPatchnotes.patch_update = patch_update

    if datetime.datetime.now() - time < datetime.timedelta(hours=2): return get_patch_image()
    return None


'''
##################################################
COMMAND PART
##################################################
'''


class LoLPatchnotes(Extension):
    url: str
    soup: BeautifulSoup
    title: str
    patch_update: bool

    @slash_command(name="patch", description="Erhalte die Patchzusammenfassung")
    async def patch_function(self, ctx: SlashContext): await ctx.send("Patch")

    @patch_function.subcommand(sub_cmd_name="image", sub_cmd_description="Erhalte das Patchzusammenfassungsbild", )
    async def image_function(self, ctx: SlashContext):
        await ctx.send(embed=get_patch_image())

    @patch_function.subcommand(sub_cmd_name="summary",
                               sub_cmd_description="Erhalte die Zusammenfassungen der Änderungen")
    async def summary_function(self, ctx: SlashContext):
        await ctx.send(embed=get_patch_summaries())

    @patch_function.subcommand(sub_cmd_name="details", sub_cmd_description="Erhalte die Details des Patches")
    @slash_option(
        name="type_filter_option",
        description="Filterung nach Kategorie",
        required=False,
        opt_type=OptionType.INTEGER,
        choices=[
            SlashCommandChoice(name="Alles", value=0),
            SlashCommandChoice(name="Nur Champions", value=1),
            SlashCommandChoice(name="Nur System", value=2),
        ]
    )
    @slash_option(
        name="name_filter_option",
        description="Namensfilterung: Namen (Teil reicht) durch Komma abtrennen",
        required=False,
        opt_type=OptionType.STRING
    )
    async def details_function(self, ctx: SlashContext, type_filter_option: int = 0, name_filter_option: str = ""):
        embeds = get_patch_details(type_filter_option, name_filter_option)
        paginator = Paginator.create_from_embeds(self.bot, *embeds, timeout=300)
        await paginator.send(ctx)


def _make_embed():
    embed = interactions.Embed(
        title=LoLPatchnotes.title,
        color=util.LOLESPORTS_COLOUR,
        url=LoLPatchnotes.url
    )
    embed.set_thumbnail("https://i.imgur.com/45aABYm.png")
    return embed


def get_patch_image():
    """ Returns the image that summaries every patch """
    soup = LoLPatchnotes.soup
    images = soup.find_all('img')
    image_url = [image['src'] for image in images if "Patch-Highlights" in image['src']]
    description = soup.find_all('blockquote', class_="blockquote context")[0]
    description = description.get_text("\n")
    description = description[:500] + "..."
    embed = _make_embed()
    embed.description = description
    embed.set_image(image_url[0])

    return embed


def get_patch_summaries():
    """ Returns an embed with the summary of every champion's change"""
    soup = LoLPatchnotes.soup
    champ_names = soup.find_all('h3', class_="change-title")
    champ_summaries = soup.find_all('p', class_="summary")

    embed = _make_embed()
    for i in range(min(25, len(champ_summaries))):
        embed.add_field(name=champ_names[i].text, value=champ_summaries[i].text, inline=True)
    return embed


def get_midpatch_update():
    """ Returns the midpatch updates """
    soup = LoLPatchnotes.soup
    if not soup.find('h2', id="patch-midpatch-updates"): return None
    embed = _make_embed()
    patch_updates = soup.find_all('div', class_="white-stone accent-before")
    embed.title = "Patch-Aktualisierungen"
    for patch_update in patch_updates:
        if patch_update.find('h4') is None or patch_update.find('ul') is None: continue
        titles = patch_update.find_all('h4')
        uls = patch_update.find_all('ul')
        quote = patch_update.find('blockquote')
        description = f"“{patch_update.find('blockquote').text}”" if quote else None

        embed.add_field(
            name=titles[0].text,
            value=description if description else "\u200b"
        )

        for i in range(len(uls)):
            name = titles[i + 1].text
            value = ""
            for li in uls[i].find_all['li']: value += li.text
            embed.add_field(name=name, value=value)

    return embed


def _is_not_in_filter(name, name_filter):
    """ Returns whether the name is *not* in the filter """
    if name_filter == "": return False
    name_filter = name_filter.split(",")
    name_filter = [name.lower().strip().replace("'", "") for name in name_filter]
    is_in = True
    for filter_name in name_filter:
        if filter_name in name.lower().replace("’", ""): is_in = False

    return is_in


def _get_champion_embeds(champion_changes, name_filter):
    """ Helper method to get all champion embed fields """
    embed_fields = []
    for champ_change in champion_changes:
        name = champ_change.find('h3', class_="change-title").text
        if _is_not_in_filter(name, name_filter): continue
        change_name = champ_change.find_all('h4')
        change_numbers = champ_change.find_all('ul')
        change_text = ""
        for j in range(len(change_name)): change_text += f"- {change_name[j].text}: {change_numbers[j].text}"
        change_text = (change_text
                       .replace("Fähigkeitsstärke", "AP")
                       .replace("Angriffsschaden", "AD"))
        embed_fields.append(interactions.EmbedField(name=name, value=change_text))

    return embed_fields


def _get_system_embeds(system_changes, name_filter):
    """ Helper method to get all system embed fields """
    embed_fields = []
    for system_change in system_changes:
        title = system_change.find('h3', class_="change-title")
        if not title:
            name = system_change.find('p').text
            if _is_not_in_filter(name, name_filter): continue
            value = ""
            for li in system_change.find_all('li'): value += f"- {li.text}"
            if value == "": value = system_change.find('blockquote').text
            embed_fields.append(interactions.EmbedField(name=name, value=value))
            continue
        name = title.text
        if _is_not_in_filter(name, name_filter): continue
        change_text = ""
        changes = system_change.find_all('li')
        for li in changes: change_text += f"- {li.text}"
        embed_fields.append(interactions.EmbedField(name=name, value=change_text))

    return embed_fields


def get_patch_details(type_filter, name_filter):
    """ Returns embeds with the detailed change of every champion """
    soup = LoLPatchnotes.soup
    changes = soup.find_all('div', class_="patch-change-block white-stone accent-before")
    champ_amount = 0
    for change in changes:
        if change.find('p'): champ_amount += 1
        else: break
    champion_changes = changes[:champ_amount]
    item_changes = changes[champ_amount:]

    def make_embeds(fields, text):
        """ Converts the fields to one or more embeds """
        result = []
        if len(fields) == 0: return result
        page_amount = max(round(len(fields) / 10), 1)
        fields_per_page = round(len(fields) / page_amount)
        for i in range(page_amount):
            result.append(_make_embed())
            result[i].description = f"{text} Seite: {i + 1}"
            start, end = i * fields_per_page, (i + 1) * fields_per_page
            if i == page_amount - 1: end += 1
            result[i].add_fields(*fields[start:end])
        return result

    embeds = []
    midpatch_update = get_midpatch_update()
    print(midpatch_update)
    if midpatch_update: embeds.append(midpatch_update)
    if type_filter < 2:  # true for 0 and 1 (all and champions only)
        embeds += make_embeds(_get_champion_embeds(champion_changes, name_filter), "Championänderungen")
    if type_filter % 2 == 0:  # true for 0 and 2 (all and system only)
        embeds += make_embeds(_get_system_embeds(item_changes, name_filter), "Systemänderungen")

    return embeds
