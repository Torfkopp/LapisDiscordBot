import re
import sqlite3

import interactions
from interactions import (PartialEmoji, Extension, slash_command, slash_option, OptionType, SlashContext)
from interactions.models import discord
from matplotlib import pyplot as plt

import util

UPVOTE_ID = 1326537041902833768
MEH_ID = 1327292833874444299
DOWNVOTE_ID = 1326537078527496302
GREAT_ID = 880776456400142346
BAD_ID = 880776408983552010

COLOUR = util.Colour.KARMA.value

POST_KARMA = 2
LIKES_FOR_BONUS = 4
BONUS, PENALTY = 6, -6
UPVOTE_KARMA, MEHVOTE_KARMA, DOWNVOTE_KARMA = 1, 0, -1
VOTING_KARMA = 1


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
    async def post_ranking_function(self, ctx: SlashContext, reverse=False):
        await ctx.send(embed=get_post_ranking(reverse))

    @karma_function.subcommand(sub_cmd_name="karma_graph", sub_cmd_description="Die Karmahistorie")
    async def karma_graph_function(self, ctx: SlashContext):
        await ctx.defer()
        await ctx.send(embed=None, file=get_karma_graph())


async def on_message(msg):
    if str(msg.channel.id) != util.COMEDY_CHANNEL_ID: return
    regex = re.search(
        "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})",
        msg.content)  # Allow Links
    if not (msg.attachments or msg.embeds or msg.interaction_metadata or regex): return  # Return if not pic or embed

    await msg.add_reaction(PartialEmoji(id=UPVOTE_ID))
    await msg.add_reaction(PartialEmoji(id=MEH_ID))
    await msg.add_reaction(PartialEmoji(id=DOWNVOTE_ID))


async def on_message_delete(msg):
    if str(msg.channel.id) != util.COMEDY_CHANNEL_ID: return
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()
    cur.execute("DELETE FROM posts WHERE id == ?", [str(msg.id)])
    con.commit()
    con.close()


async def on_reaction(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    # Set the author of the message reacted to or the one making lapis embed something
    if (author := str(reac.message.author)) == "Lapis#7072":
        try: author = "@" + reac.message.interaction_metadata.user.username
        except: pass  # Author is reac.message.author

    msg_id = str(reac.message.id)
    upvoters, mehvoters, downvoters = set(), set(), set()
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    if post: upvoters, mehvoters, downvoters = set(post[2].split(", ")), set(post[3].split(", ")), set(
        post[4].split(", "))
    # Add reacter to the list of up/downvoters
    if author != (reacter := str(reac.author)) and reacter != "Lapis#7072":
        if reac.emoji.id == UPVOTE_ID: upvoters.add(reacter)
        elif reac.emoji.id == MEH_ID: mehvoters.add(reacter)
        elif reac.emoji.id == DOWNVOTE_ID: downvoters.add(reacter)

    up, meh, down = ", ".join(filter(None, upvoters)), ", ".join(filter(None, mehvoters)), ", ".join(
        filter(None, downvoters))
    if post: cur.execute(
        "UPDATE posts SET upvoters = ?, mehvoters = ?, downvoters = ? WHERE id = ?", [up, meh, down, msg_id])
    else:
        cur.execute("INSERT INTO posts VALUES(?, ?, ?, ?, ?)", [author, msg_id, up, meh, down])

    con.commit()
    con.close()


async def on_reaction_remove(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    msg_id = str(reac.message.id)

    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    upvoters, mehvoters, downvoters = set(post[2].split(", ")), set(post[3].split(", ")), set(post[4].split(", "))

    reacter = str(reac.author)
    if reac.emoji.id == UPVOTE_ID: upvoters.discard(reacter)
    elif reac.emoji.id == MEH_ID: mehvoters.discard(reacter)
    elif reac.emoji.id == DOWNVOTE_ID: downvoters.discard(reacter)

    up, meh, down = ", ".join(filter(None, upvoters)), ", ".join(filter(None, mehvoters)), ", ".join(
        filter(None, downvoters))
    cur.execute(
        "UPDATE posts SET upvoters = ?, mehvoters = ?, downvoters = ? WHERE id = ?", [up, meh, down, msg_id]
    )

    con.commit()
    con.close()


def get_author_ranking():
    class User:
        posts = 0
        votings = 0
        upvotes = 0
        mehvotes = 0
        downvotes = 0
        karma = 0

        def calc_karma(self):
            self.karma = self.posts * POST_KARMA + self.votings * VOTING_KARMA + self.upvotes * UPVOTE_KARMA + self.mehvotes * MEHVOTE_KARMA + self.downvotes * DOWNVOTE_KARMA
            return self.karma

    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    user_set, users = set(), {}
    for author, up, meh, down in cur.execute("SELECT author, upvoters, mehvoters, downvoters FROM posts").fetchall():
        user_set.update(
            [author] +
            list(filter(None, up.split(", "))) +
            list(filter(None, meh.split(", "))) +
            list(filter(None, down.split(", ")))
        )

    for user in user_set: users[user] = User()

    posts = cur.execute("SELECT * FROM posts").fetchall()

    con.close()

    for post in posts:
        up, meh, down = list(filter(None, post[2].split(", "))), list(filter(None, post[3].split(", "))), list(
            filter(None, post[4].split(", ")))
        author = users[post[0]]
        author.posts += 1
        author.upvotes += len(up)
        author.mehvotes += len(meh)
        author.downvotes += len(down)
        for u in set(up + meh + down): users[u].votings += 1

    def rowmaker(a, k, p, v, upv, m, d):
        return "| ".join(
            ["", a.ljust(13), str(k).ljust(5), str(p).ljust(5), str(v).ljust(5), str(upv).ljust(4), str(m).ljust(4),
             str(d).ljust(4)]) + "|\n"

    table = rowmaker("Komödiant", "Karma", "Posts", "Votes", "Up", "Meh", "Down")
    table += "|".join(["", "-" * 14, "-" * 6, "-" * 6, "-" * 6, "-" * 5, "-" * 5, "-" * 5]) + "|\n"

    sorted_users = list(users.keys())
    sorted_users.sort(reverse=True, key=lambda x: users[x].calc_karma())
    for user in sorted_users:
        u = users[user]
        table += rowmaker(user.replace("@", ""), u.karma, u.posts, u.votings, u.upvotes, u.mehvotes, u.downvotes)

    embed = interactions.Embed(title="Karmatabelle", color=COLOUR)
    embed.description = "```markdown\n" + table + "```"

    return embed


def get_post_ranking(reverse):
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()
    posts = cur.execute("SELECT author, id, upvoters, mehvoters, downvoters FROM posts").fetchall()
    con.close()

    embed = interactions.Embed(title="Postranking", color=COLOUR)

    server_id, channel_id = util.SERVER_ID, util.COMEDY_CHANNEL_ID

    sorted_posts = []
    for p in posts:
        up, meh, down = len(list(filter(None, p[2].split(", ")))), len(list(filter(None, p[3].split(", ")))), len(
            list(filter(None, p[4].split(", "))))
        sorted_posts.append((p[0], p[1], up, meh, down))

    if not reverse: sorted_posts = sorted(sorted_posts, reverse=True, key=lambda x: (x[2], x[3]))
    else: sorted_posts = sorted(sorted_posts, reverse=True, key=lambda x: (x[4], -x[3]))

    for i, p in enumerate(sorted_posts[:10]):
        link = "https://discord.com/channels/" + "/".join([server_id, channel_id, p[1]])
        name = (f"{i + 1}. {p[0]} {PartialEmoji(id=UPVOTE_ID)} {p[2]} " +
                f"{PartialEmoji(id=MEH_ID)} {p[3]} {PartialEmoji(id=DOWNVOTE_ID)} {p[4]}")
        embed.add_field(name=name, value=link, inline=False)

    return embed


def get_karma_graph():
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    user_set, users = set(), {}
    for author, up, meh, down in cur.execute("SELECT author, upvoters, mehvoters, downvoters FROM posts").fetchall():
        user_set.update(
            [author] +
            list(filter(None, up.split(", "))) +
            list(filter(None, meh.split(", "))) +
            list(filter(None, down.split(", ")))
        )

    for user in user_set: users[user] = [0]

    x_axis = cur.execute("SELECT DISTINCT id FROM posts").fetchall()
    x_axis = ["Start"] + [x[0] for x in x_axis]
    posts = cur.execute("SELECT * FROM posts ORDER BY id ASC").fetchall()

    for post in posts:
        up, meh, down = list(filter(None, post[2].split(", "))), list(filter(None, post[3].split(", "))), list(
            filter(None, post[4].split(", ")))
        users[post[0]][-1] += POST_KARMA + len(up) * UPVOTE_KARMA + len(down) * DOWNVOTE_KARMA
        if len(up) >= LIKES_FOR_BONUS: users[post[0]][-1] += BONUS
        if len(down) >= LIKES_FOR_BONUS: users[post[0]][-1] += PENALTY
        for u in set(up + meh + down): users[u][-1] += VOTING_KARMA
        for u in users: users[u].append(users[u][-1])

    plt.style.use('dark_background')
    fig, ax = plt.subplots()

    for u, v in users.items():
        ax.plot(x_axis, list(v), label=u)

    ax.set_xlabel("POST")
    ax.set_ylabel("KARMA")
    ax.set_xticklabels([])
    ax.legend()
    plt.suptitle("KARMA HISTORY")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('strunt/karma.png')
    file = discord.File('strunt/karma.png', file_name="karma.png")

    return file
