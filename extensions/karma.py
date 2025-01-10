import json
import sqlite3

import interactions
from interactions import (PartialEmoji, Extension, slash_command, SlashContext)

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

    @slash_command(name="karma", description="Karma Stuff", scopes=[1134856890669613210])
    async def karma_function(self, ctx: SlashContext): await ctx.send("Karma")

    @karma_function.subcommand(sub_cmd_name="author_ranking", sub_cmd_description="Ein Ranking aller Komödianten hier")
    async def author_ranking_function(self, ctx: SlashContext):
        await ctx.send(embed=get_author_ranking())

    @karma_function.subcommand(sub_cmd_name="post_ranking", sub_cmd_description="Die besten Posts")
    async def post_ranking_function(self, ctx: SlashContext):
        await ctx.send(embed=get_post_ranking())


async def on_message(msg):
    if str(msg.channel.id) != util.COMEDY_CHANNEL_ID: return
    if not (msg.attachments or msg.embeds or msg.interaction_metadata): return  # Return if not picture or embed

    await msg.add_reaction(PartialEmoji(id=UPVOTE_ID))
    await msg.add_reaction(PartialEmoji(id=MEH_ID))
    await msg.add_reaction(PartialEmoji(id=DOWNVOTE_ID))


async def on_reaction(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    # Set the author of the message reacted to or the one making lapis embed something
    if (author := str(reac.message.author)) == "Lapis#7072":
        try: author = "@" + reac.message.interaction_metadata.user.username
        except: ...  # Author is reac.message.author

    with open("strunt/karma.json", "r") as f: karma = json.load(f)

    # Add 1 Karma for a reaction to the one reacting
    if (reacter := str(reac.author)) != "Lapis#7072" and reacter != author:
        if reacter not in karma: karma[reacter] = 0
        karma[reacter] += 1

    if author not in karma: karma[author] = 0

    msg_id = str(reac.message.id)
    upvotes, downvotes = set(), set()
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    if post: upvotes, downvotes = set(post[2].split(", ")), set(post[4].split(", "))
    # Add reacter to the list of up/downvoters
    if author != reacter and reacter != "Lapis#7072":
        if reac.emoji.id == UPVOTE_ID: upvotes.add(reacter)
        elif reac.emoji.id == DOWNVOTE_ID: downvotes.add(reacter)

    up, down = ", ".join(filter(None, upvotes)), ", ".join(filter(None, downvotes))
    if post: cur.execute("UPDATE posts SET upvoters = ?, upvotes = ?, downvoters = ?, downvotes = ? WHERE id = ?",
                         [up, len(upvotes), down, len(downvotes), msg_id])
    else:
        cur.execute("INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?)",
                    [author, msg_id, up, len(upvotes), down, len(downvotes)])
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
        except: ...

    if (reacter := str(reac.author)) != author: karma[reacter] -= 1

    msg_id = str(reac.message.id)

    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    upvotes, downvotes = set(post[2].split(", ")), set(post[4].split(", "))

    if reac.emoji.id == UPVOTE_ID: upvotes.discard(reacter)
    elif reac.emoji.id == DOWNVOTE_ID: downvotes.discard(reacter)

    up, down = ", ".join(filter(None, upvotes)), ", ".join(filter(None, downvotes))
    cur.execute("UPDATE posts SET upvotes = ?, downvotes = ? WHERE id = ?", [up, down, msg_id])

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

    def rowmaker(u, k, p, up, d):
        return "| ".join(["", u.ljust(10), str(k).ljust(5), str(p).ljust(5), str(up).ljust(5), str(d).ljust(5)]) + "|\n"

    table = rowmaker("Komödiant", "Karma", "Posts", "Ups", "Downs")
    table += "|".join(["", "-" * 11, "-" * 6, "-" * 6, "-" * 6, "-" * 6]) + "|\n"

    for user, posts in post_dict.items():
        table += rowmaker(user, karma[user], len(posts), sum(x[3] for x in posts), sum(x[5] for x in posts))

    embed = interactions.Embed(title="Karmatabelle", color=COLOUR)
    embed.description = "```markdown\n" + table + "```"

    return embed


def get_post_ranking():
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()
    posts = cur.execute(
        "SELECT author, id, upvotes, downvotes FROM posts ORDER BY upvotes DESC, downvotes ASC;").fetchall()
    con.close()

    embed = interactions.Embed(title="Postranking", color=COLOUR)

    server_id, channel_id = util.SERVER_ID, util.COMEDY_CHANNEL_ID

    for i, p in enumerate(posts[:12]):
        link = "https://discord.com/channels/" + "/".join([server_id, channel_id, p[1]])
        name = f"{i + 1}. {p[0]} | {p[2]} {PartialEmoji(id=UPVOTE_ID)}| {p[3]} {PartialEmoji(id=DOWNVOTE_ID)}"
        embed.add_field(name=name, value=link, inline=True)

    return embed
