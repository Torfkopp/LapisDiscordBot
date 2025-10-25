import json

import interactions
from interactions import (
    Extension, slash_command, SlashContext, slash_option, OptionType
)
from interactions.ext.prefixed_commands import prefixed_command, PrefixedContext

import util


def setup(bot): Tierlist(bot)


async def function(ctx, entry_function, *args):
    await ctx.message.delete()
    entry_function(*args)
    try: await Tierlist.message.edit(embed=Tierlist.embed)
    except AttributeError: pass


async def on_message_delete(msg):
    with open("strunt/tierlist.json", "r", encoding="utf-8") as f: j = json.load(f)
    x = j.pop(str(msg.id), None)
    if x:
        with open("strunt/tierlist.json", "w", encoding="utf-8") as f: json.dump(j, f, indent=4)


class Tierlist(Extension):
    message: interactions.models.discord.message
    file: interactions.models.discord.File
    embed: interactions.Embed

    @slash_command(name="tierlist", description="Erstelle eine Tierlist")
    @slash_option(
        name="name",
        description="Name/Thema der Tierlist",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="tiers",
        description="Tiers mit Komma abgetrennt ('S' für S-D Liste, '0-10' für 0 bis 10 Liste)",
        required=False,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="description",
        description="Erklärung der Einordnung (z. B. 0 (Gut) -> 10 (Schlecht))",
        required=False,
        opt_type=OptionType.STRING
    )
    async def tierlist_function(self, ctx: SlashContext, name, tiers: str = "S", description: str = ""):
        Tierlist.embed, Tierlist.file = create_tierlist(name, tiers, description)
        Tierlist.message = await ctx.send(file=Tierlist.file, embed=Tierlist.embed)
        save_tierlist(name, Tierlist.message.id, ctx.guild_id, ctx.channel_id)

    @slash_command(name="tierlistlist", description="Get list of Tierlists")
    async def tierlistlist_function(self, ctx: SlashContext):
        embed = get_tierlistlist()
        await ctx.send(embed=embed)

    @prefixed_command()
    async def c(self, ctx: PrefixedContext, arg1, arg2): await function(ctx, create_entry, arg1, arg2)

    @prefixed_command()
    async def d(self, ctx: PrefixedContext, arg1, arg2): await function(ctx, delete_entry, arg1, arg2)

    @prefixed_command()
    async def m(self, ctx: PrefixedContext, arg1, arg2, arg3): await function(ctx, move_entry, arg1, arg2, arg3)

    # Just alternative naming
    @prefixed_command()
    async def create(self, ctx: PrefixedContext, arg1, arg2): await function(ctx, create_entry, arg1, arg2)

    @prefixed_command()
    async def delete(self, ctx: PrefixedContext, arg1, arg2): await function(ctx, delete_entry, arg1, arg2)

    @prefixed_command()
    async def move(self, ctx: PrefixedContext, arg1, arg2, arg3): await function(ctx, move_entry, arg1, arg2, arg3)


def create_tierlist(theme, tiers, description):
    if tiers == "0-10": tiers = "0,1,2,3,4,5,6,7,8,9,10"
    elif tiers == "S" or tiers.count(",") == 0: tiers = "S,A,B,C,D,E,F"

    tiers = tiers.split(",")

    if description == "":
        description = f"{tiers[0]} (Bestes) -> {tiers[len(tiers) - 1]} (Schlechtestes)"

    embed = interactions.Embed(title=f"{theme} Tierlist",
                               description=f"Ordnung: {description}",
                               color=util.Colour.TIERLIST.value)
    embed.set_footer("@Lapis + (c/create {Tier} {Name} | d/delete {Tier} {Name} | m/move {Tier1} {Tier2} {Name})")
    file = interactions.models.discord.File("lapis_pics/LapisTier.jpg", "LapisTier.jpg")
    embed.set_thumbnail(url="attachment://LapisTier.jpg")

    for tier in tiers:
        tier = tier.strip()
        if tier == "": continue
        embed.add_field(name=tier, value="\u200b")

    return embed, file


def create_entry(tier, name):
    tier = tier.upper()
    name = name.title()
    tier_field = [field for field in Tierlist.embed.fields if field.name == tier]
    for field in tier_field: field.value = f"{field.value} {name},"


def delete_entry(tier, name):
    tier = tier.upper()
    name = name.title()
    tier_field = [field for field in Tierlist.embed.fields if field.name == tier]
    for field in tier_field: field.value = field.value.replace(f"{name},", "")


def move_entry(tier1, tier2, name):
    delete_entry(tier1, name)
    create_entry(tier2, name)


def save_tierlist(name, message_id, guild, channel):
    with open("strunt/tierlist.json", "r", encoding="utf-8") as f: j = json.load(f)
    j[message_id] = {"name": name, "guild": guild, "channel": channel}
    with open("strunt/tierlist.json", "w", encoding="utf-8") as f: json.dump(j, f, indent=4)


def get_tierlistlist():
    with open("strunt/tierlist.json", "r", encoding="utf-8") as f: tierlists = json.load(f)
    description = ""
    for l_key, l_values in tierlists.items():
        link = f"https://discord.com/channels/{l_values['guild']}/{l_values['channel']}/{l_key}"
        description += f"{l_values['name']}: {link}\n"
    embed = interactions.Embed(title="Tierlistlist", description=description)
    return embed
