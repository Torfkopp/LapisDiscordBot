import json
import re
import sqlite3

import interactions
from interactions import (PartialEmoji, Extension, slash_command, slash_option, OptionType, SlashContext)

import util

UPVOTE_ID = 1326537041902833768
MEH_ID = 1327292833874444299
DOWNVOTE_ID = 1326537078527496302
GREAT_ID = 880776456400142346
BAD_ID = 880776408983552010

COLOUR = util.Colour.KARMA.value


def setup(bot):
    Karma(bot)


class Karma(Extension):

    @slash_command(name="karma", description="Karma Stuff")
    async def karma_function(self, ctx: SlashContext): await ctx.send("Karma")

    @karma_function.subcommand(sub_cmd_name="author_ranking", sub_cmd_description="Ein Ranking aller Komödianten hier")
    async def author_ranking_function(self, ctx: SlashContext):
        await ctx.send(embed=get_author_ranking())

    @karma_function.subcommand(sub_cmd_name="post_ranking", sub_cmd_description="Die besten Posts")
    @slash_option(
        name="reverse",
        description="Zeige die schlechtesten anstatt der besten an",
        required=False,
        opt_type=OptionType.BOOLEAN,
    )
    async def post_ranking_function(self, ctx: SlashContext, reverse: False):
        await ctx.send(embed=get_post_ranking(reverse))


async def on_message(msg):
    if str(msg.channel.id) != util.COMEDY_CHANNEL_ID: return
    regex = re.match(
        "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$",
        msg.content)  # Allow YouTube Links
    if not (msg.attachments or msg.embeds or msg.interaction_metadata or regex): return  # Return if not pic or embed

    await msg.add_reaction(PartialEmoji(id=UPVOTE_ID))
    await msg.add_reaction(PartialEmoji(id=MEH_ID))
    await msg.add_reaction(PartialEmoji(id=DOWNVOTE_ID))


async def on_reaction(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    # Set the author of the message reacted to or the one making lapis embed something
    if (author := str(reac.message.author)) == "Lapis#7072":
        try: author = "@" + reac.message.interaction_metadata.user.username
        except: pass  # Author is reac.message.author

    with open("strunt/karma.json", "r") as f: karma = json.load(f)

    if author not in karma: karma[author] = 0

    msg_id = str(reac.message.id)
    upvotes, mehvotes, downvotes = set(), set(), set()
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    if post: upvotes, mehvotes, downvotes = set(post[2].split(", ")), set(post[4].split(", ")), set(post[6].split(", "))
    # Add reacter to the list of up/downvoters
    if author != (reacter := str(reac.author)) and reacter != "Lapis#7072":
        if reacter not in upvotes | mehvotes | downvotes:  # Add 1 Karma for a reaction to the one reacting
            if reacter not in karma: karma[reacter] = 0
            karma[reacter] += 1
        if reac.emoji.id == UPVOTE_ID: upvotes.add(reacter)
        elif reac.emoji.id == MEH_ID: mehvotes.add(reacter)
        elif reac.emoji.id == DOWNVOTE_ID: downvotes.add(reacter)

    up, meh, down = ", ".join(filter(None, upvotes)), ", ".join(filter(None, mehvotes)), ", ".join(
        filter(None, downvotes))
    if post: cur.execute(
        "UPDATE posts SET upvoters = ?, upvotes = ?, mehvoters = ?, mehvotes = ?, downvoters = ?, downvotes = ? WHERE id = ?",
        [up, len(upvotes), meh, len(mehvotes), down, len(downvotes), msg_id])
    else:
        cur.execute("INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                    [author, msg_id, up, len(upvotes), meh, len(mehvotes), down, len(downvotes)])
        karma[author] += 3  # Bonus Karma Points for every post

    con.commit()
    con.close()

    karma[author] += len(upvotes) - len(downvotes)
    if len(upvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=GREAT_ID))
        karma[author] += 6
    if len(downvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=BAD_ID))
        karma[author] -= 6

    with open("strunt/karma.json", "w") as f: json.dump(karma, f, indent=4)


async def on_reaction_remove(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    with open("strunt/karma.json", "r") as f: karma = json.load(f)
    if (author := str(reac.message.author)) == "Lapis#7072":
        try: author = "@" + reac.message.interaction_metadata.user.username
        except: pass

    msg_id = str(reac.message.id)

    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    upvotes, mehvotes, downvotes = set(post[2].split(", ")), set(post[4].split(", ")), set(post[6].split(", "))

    if (reacter := str(reac.author)) != author: karma[reacter] -= 1
    if reac.emoji.id == UPVOTE_ID: upvotes.discard(reacter)
    elif reac.emoji.id == MEH_ID: mehvotes.discard(reacter)
    elif reac.emoji.id == DOWNVOTE_ID: downvotes.discard(reacter)

    up, meh, down = ", ".join(filter(None, upvotes)), ", ".join(filter(None, mehvotes)), ", ".join(
        filter(None, downvotes))
    cur.execute(
        "UPDATE posts SET upvoters = ?, upvotes = ?, mehvoters = ?, mehvotes = ?, downvoters = ?, downvotes = ? WHERE id = ?",
        [up, len(upvotes), meh, len(mehvotes), down, len(downvotes), msg_id]
    )

    con.commit()
    con.close()

    karma[author] += len(upvotes) - len(downvotes)

    # Remove benefits again if threshold vote is removed
    if len(upvotes) < 4 and GREAT_ID in reac.msg.reactions():
        await reac.msg.remove_reaction(PartialEmoji(id=GREAT_ID))
        karma[author] -= 6
    if len(downvotes) < 4 and BAD_ID in reac.msg.reactions():
        await reac.msg.remove_reaction(PartialEmoji(id=BAD_ID))
        karma[author] += 6

    with open("strunt/karma.json", "w") as f: json.dump(karma, f, indent=4)


def get_author_ranking():
    with open("strunt/karma.json", "r") as f: karma = json.load(f)

    post_dict = {}

    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    for user in karma.keys():
        post_dict[user] = cur.execute("SELECT * FROM posts WHERE author = ?", [user]).fetchall()

    con.close()

    users = list(post_dict.keys())
    users.sort(reverse=True, key=lambda x: karma[x])

    def rowmaker(u, k, p, up, m, d):
        return "| ".join(["", u.ljust(13), str(k).ljust(6), str(p).ljust(5), str(up).ljust(5), str(m).ljust(5),
                          str(d).ljust(5)]) + "|\n"

    table = rowmaker("Komödiant", "Karma", "Posts", "Up", "Meh", "Down")
    table += "|".join(["", "-" * 14, "-" * 7, "-" * 6, "-" * 6, "-" * 6, "-" * 6]) + "|\n"

    for user in users:
        posts = post_dict[user]
        table += rowmaker(user.replace("@", ""), karma[user], len(posts), sum(x[3] for x in posts),
                          sum(x[5] for x in posts),
                          sum(x[7] for x in posts))

    embed = interactions.Embed(title="Karmatabelle", color=COLOUR)
    embed.description = "```markdown\n" + table + "```"

    return embed


def get_post_ranking(reverse):
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()
    statement = "SELECT author, id, upvotes, mehvotes, downvotes FROM posts ORDER BY " + (
        "upvotes DESC, downvotes ASC, mehvotes DESC;" if not reverse else "downvotes DESC, upvotes ASC, mehvotes ASC;")
    posts = cur.execute(statement).fetchall()
    con.close()

    embed = interactions.Embed(title="Postranking", color=COLOUR)

    server_id, channel_id = util.SERVER_ID, util.COMEDY_CHANNEL_ID

    for i, p in enumerate(posts[:10]):
        link = "https://discord.com/channels/" + "/".join([server_id, channel_id, p[1]])
        name = (f"{i + 1}. {p[0]} {PartialEmoji(id=UPVOTE_ID)} {p[2]} " +
                f"{PartialEmoji(id=MEH_ID)} {p[3]} {PartialEmoji(id=DOWNVOTE_ID)} {p[4]}")
        embed.add_field(name=name, value=link, inline=False)

    return embed
