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
from core import log


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
    log.write("Request page LoLPatch: " + url)
    soup = BeautifulSoup(response.content, 'html.parser')
    latest_patch_link = soup.find('a', href=True)
    latest_patch_link = latest_patch_link['href']

    url = f"https://www.leagueoflegends.com{latest_patch_link}"
    response = requests.get(url)
    log.write("Request page LoLPatch: " + url)
    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.find('h1', class_="style__Title-sc-vd48si-5 kDFvhf").text

    patch_update = soup.find('h2', id="patch-midpatch-updates")
    patch_update = patch_update is not None
    new_patchnotes = False
    if LoLPatchnotes.url and LoLPatchnotes.url != url: new_patchnotes = True

    LoLPatchnotes.url = url
    LoLPatchnotes.soup = soup
    LoLPatchnotes.title = title

    if patch_update:
        # If a midpatch update exists in the iteration but didn't exist in the last one, call the method
        if LoLPatchnotes.patch_update is not None and not LoLPatchnotes.patch_update:
            LoLPatchnotes.patch_update = patch_update
            return get_midpatch_update()
    LoLPatchnotes.patch_update = patch_update

    if new_patchnotes: return get_patch_image()
    return None


'''
##################################################
COMMAND PART
##################################################
'''


class LoLPatchnotes(Extension):
    url = None
    soup: BeautifulSoup
    title: str
    patch_update = None

    @slash_command(name="patch", description="Erhalte die Patchzusammenfassung")
    async def patch_function(self, ctx: SlashContext): await ctx.send("Patch")

    @patch_function.subcommand(sub_cmd_name="image", sub_cmd_description="Erhalte das Patchzusammenfassungsbild", )
    async def image_function(self, ctx: SlashContext): await ctx.send(embed=get_patch_image())

    @patch_function.subcommand(sub_cmd_name="summary",
                               sub_cmd_description="Erhalte die Zusammenfassungstexte der Änderungen")
    async def summary_function(self, ctx: SlashContext): await ctx.send(embed=get_patch_summaries())

    @patch_function.subcommand(sub_cmd_name="details",
                               sub_cmd_description="Erhalte die Änderungen des Patches im Details")
    @slash_option(
        name="type_filter",
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
        name="name_filter",
        description="Namensfilterung: Namen (Teil reicht) durch Komma abtrennen",
        required=False,
        opt_type=OptionType.STRING
    )
    async def details_function(self, ctx: SlashContext, type_filter: int = 0, name_filter: str = ""):
        embeds = get_patch_details(type_filter, name_filter)
        paginator = Paginator.create_from_embeds(self.bot, *embeds)
        try: await paginator.send(ctx)
        except IndexError: await ctx.send(embed=util.get_error_embed("faulty_value"))


def _make_embed():
    embed = interactions.Embed(
        title=LoLPatchnotes.title,
        color=util.Colour.LOLESPORTS.value,
        url=LoLPatchnotes.url
    )
    embed.set_thumbnail("https://i.imgur.com/45aABYm.png")
    return embed


def get_patch_image():
    """ Returns the image that summaries every patch """
    soup = LoLPatchnotes.soup

    images = soup.find_all('div', class_="white-stone accent-before")

    for i in range(len(images)):
        try: image = images[i].find('a')['href']
        except TypeError: continue
        else:
            text = images[i].get_text()
            if len(text) > 500: text = text[:500] + "..."
            embed = _make_embed()
            embed.description = text
            embed.set_image(image)
            return embed
    return util.get_error_embed("error")


def get_patch_summaries():
    """ Returns an embed with the summary of every champion's change"""
    soup = LoLPatchnotes.soup
    champ_names = soup.find_all('h3', class_="change-title")
    champ_names = [p for p in champ_names if "champion" in p.find('a')['href']]
    champ_summaries = soup.find_all('p', class_="summary")

    embed = _make_embed()
    if len(champ_names) != len(champ_summaries): embed.add_field(name=champ_names.pop(0).text, value="Neuer Champ")
    for i in range(min(25, len(champ_summaries))):
        embed.add_field(name=champ_names[i].text, value=champ_summaries[i].text, inline=True)
    return util.uwuify_by_chance(embed)


def get_midpatch_update():
    """ Returns the midpatch updates """
    soup = LoLPatchnotes.soup
    midpatch = soup.find('h2', id="patch-mid-patch-updates") or soup.find('h2', id="patch-midpatch-updates")
    if midpatch is None: return None
    embed = _make_embed()
    midpatch_update = soup.find('div', class_="white-stone accent-before")
    embed.title = "Patch-Aktualisierungen"

    titles = midpatch_update.find_all('h4')
    uls = midpatch_update.find_all('ul')
    quote = midpatch_update.find('blockquote')
    description = f"“{midpatch_update.find('blockquote').text.strip()}”" if quote else None

    embed.add_field(
        name=titles[0].text,
        value=description if description else "\u200b"
    )

    for i in range(len(uls)):
        name = titles[i + 1].text
        value = ""
        for li in uls[i].find_all('li'): value += f"- {li.text}\n"
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
        change_names = champ_change.find_all('h4')
        change_numbers = champ_change.find_all('ul')
        change_text = ""
        for j in range(len(change_names)): change_text += f"- {change_names[j].text}: {change_numbers[j].text}"
        change_text = (change_text
                       .replace("Fähigkeitsstärke", "AP")
                       .replace("Angriffsschaden", "AD"))

        if len(change_text) > 1023:
            change_text = ""
            for j in range(len(change_names)):
                numbers = change_numbers[j].text
                numbers = numbers.replace("Fähigkeitsstärke", "AP").replace("Angriffsschaden", "AD")
                if len(numbers) > 1024:
                    embed_fields.append(interactions.EmbedField(name=name, value=change_text))
                    change_text = f"- {change_names[j].text}: "
                    for li in change_numbers[j].find_all('li'):
                        li_text = li.text
                        li_text = li_text.replace("Fähigkeitsstärke", "AP").replace("Angriffsschaden", "AD")
                        if len(change_text) + len(li.text) > 1024:
                            embed_fields.append(interactions.EmbedField(name=name, value=change_text))
                            change_text = f"- {change_names[j].text}: "
                        change_text += li_text
                    continue
                if len(change_text) + len(change_names[j].text) + len(numbers) > 1024:
                    embed_fields.append(interactions.EmbedField(name=name, value=change_text))
                    change_text = f"- {change_names[j].text}: {numbers}"
                    continue
                change_text += f"- {change_names[j].text}: {numbers}"

        if change_text == "": change_text = f"“{champ_change.find('blockquote').text.strip()}”"
        embed_fields.append(interactions.EmbedField(name=name, value=change_text))

    return embed_fields


def _get_system_embeds(system_changes, name_filter):
    """ Helper method to get all system embed fields """
    embed_fields = []
    for system_change in system_changes:
        title = system_change.find('h3', class_="change-title")
        if not title:
            if system_change.find('p'): name = system_change.find('p').text
            elif system_change.find('h4'): name = system_change.find('h4').text
            else: name = system_change.parent.find_previous_sibling('header').find('h2').text
            if _is_not_in_filter(name, name_filter): continue
            value = ""
            for li in system_change.find_all('li'):
                if len(value) + len(li.text) > 1023:
                    embed_fields.append(interactions.EmbedField(name=name, value=value))
                    value = f"- {li.text}"
                    continue
                value += f"- {li.text}"
            if value == "": value = system_change.find('blockquote').text
            embed_fields.append(interactions.EmbedField(name=name, value=value))
            continue
        name = title.text
        if _is_not_in_filter(name, name_filter): continue
        change_text = ""
        changes = system_change.find_all('li')
        for li in changes: change_text += f"- {li.text}"
        if len(change_text) > 1023:
            change_text = ""
            for li in changes:
                text = li.text
                text = text.replace("Fähigkeitsstärke", "AP").replace("Angriffsschaden", "AD")
                if len(change_text) + len(text) > 1023:
                    embed_fields.append(interactions.EmbedField(name=name, value=change_text))
                    change_text = f"- {text}"
                    continue
                change_text += f"- {text}"
        embed_fields.append(interactions.EmbedField(name=name, value=change_text))

    return embed_fields


def get_patch_details(type_filter, name_filter):
    """ Returns embeds with the detailed change of every champion """
    soup = LoLPatchnotes.soup
    changes = soup.find_all('div', class_="patch-change-block white-stone accent-before")
    other_changes, champion_changes, system_changes = [], [], []
    for change in changes:
        category_id = change.parent.find_previous_sibling('header', class_='header-primary').find('h2')['id']
        if category_id == "patch-champions": champion_changes.append(change)
        elif category_id in ["patch-items", "patch-runes"]: system_changes.append(change)
        else: system_changes.append(change)  # other_changes.append(change)

    def make_embeds(fields, text):
        """ Converts the fields to one or more embeds """
        result = []
        if len(fields) == 0: return result

        total_length = sum(len(field.value) for field in fields)
        page_amount = int(total_length / 4000) + 1
        field_counter = 0
        for j in range(page_amount):
            embed = _make_embed()
            embed.description = f"{text} Seite: {j + 1}"
            while field_counter < len(fields):
                embed.add_fields(fields[field_counter])
                field_counter += 1
                if sum(len(field.value) for field in embed.fields) > 4000: break
            result.append(embed)
        return result

    embeds = []
    midpatch_update = get_midpatch_update()
    if midpatch_update: embeds.append(midpatch_update)
    if type_filter < 2:  # true for 0 and 1 (all and champions only)
        embeds += make_embeds(_get_champion_embeds(champion_changes, name_filter), "Championänderungen")
    if type_filter % 2 == 0:  # true for 0 and 2 (all and system only)
        embeds += make_embeds(_get_system_embeds(system_changes, name_filter), "Systemänderungen")

    if util.get_if_uwuify():
        for i in range(len(embeds)): embeds[i] = util.uwuify_embed(embeds[i])

    return embeds
