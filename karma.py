import json
import sqlite3

from interactions import PartialEmoji

# TODO:
#   Get good Meh Emoji
#   Command to see ranking author
#   Command to see post ranking
#   Command to see liked posts by author? -> maybe too many

#Kiryu: 1326537645391872030
#Up: 1326537041902833768
#Down: 1326537078527496302
#Stonks: 880771373872586782
#NotStonks: 880771396412768266
#KannaPog: 880776456400142346
#KannaKMS: 880776408983552010
UPVOTE_ID = 1326537041902833768
MEH_ID = 1326537645391872030
DOWNVOTE_ID = 1326537078527496302
GREAT_ID = 880776456400142346
BAD_ID = 880776408983552010


async def on_message(msg):
    if msg.channel.id != 1134856892007583796: return
    if not (msg.attachments or msg.embeds or msg.interaction_metadata): return  # Return if not picture or embed

    #await msg.add_reaction(PartialEmoji.from_str(":arrow_up:"))
    #await msg.add_reaction(PartialEmoji.from_str(":arrow_down:"))

    #list = await msg.guild.fetch_all_custom_emojis()
    #print(list)
    #await msg.add_reaction(list[2])

    #if msg.attachments

    await msg.add_reaction(PartialEmoji(id=UPVOTE_ID))
    await msg.add_reaction(PartialEmoji(id=MEH_ID))
    await msg.add_reaction(PartialEmoji(id=DOWNVOTE_ID))


def createTable():
    import sqlite3
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()
    cur.execute("DROP TABLE posts")
    cur.execute("CREATE TABLE posts(author, id, upvotes, downvotes)")
    con.commit()
    con.close()


async def on_reaction(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    # Set the author of the message reacted to or the one making lapis embed something
    if (author := str(reac.message.author)) == "Lapis#7072":
        author = str([m async for m in reac.message.channel.history(before=reac.message, limit=1)][0].author)

    with open("strunt/karma.json", "r") as f: karma = json.load(f)

    # Add 1 Karma for a reaction to the one reacting
    if (reacter := str(reac.author)) != "Lapis#7072" and reacter != author:
        if reacter not in karma: karma[reacter] = {"karma": 0, "posts": {}}
        karma[reacter]["karma"] += 1

    if author not in karma: karma[author] = {"karma": 0, "posts": {}}

    msg_id = str(reac.message.id)
    upvotes, downvotes = set(), set()
    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    if post: upvotes, downvotes = set(post[2].split(", ")), set(post[3].split(", "))
    # Add reacter to the list of up/downvoters
    if author != reacter and reacter != "Lapis#7072":
        if reac.emoji.id == UPVOTE_ID: upvotes.add(reacter)
        elif reac.emoji.id == DOWNVOTE_ID: downvotes.add(reacter)

    up, down = ", ".join(filter(None, upvotes)), ", ".join(filter(None, downvotes))
    if post: cur.execute("UPDATE posts SET upvotes = ?, downvotes = ? WHERE id = ?", [up, down, msg_id])
    else:
        cur.execute("INSERT INTO posts VALUES(?, ?, ?, ?)", [author, msg_id, up, down])
        karma[author]["karma"] += 3  # Bonus Karma Points for every post

    con.commit()
    con.close()

    karma[author]["karma"] += len(upvotes) - len(downvotes)
    if len(upvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=GREAT_ID))
        karma[author]["karma"] += 6
    if len(downvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=BAD_ID))
        karma[author]["karma"] -= 6

    with open("strunt/karma.json", "w") as f: json.dump(karma, f, indent=4)


async def on_reactionSQLONLY(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    # Set the author of the message reacted to or the one making lapis embed something
    if (author := str(reac.message.author)) == "Lapis#7072":
        author = str([m async for m in reac.message.channel.history(before=reac.message, limit=1)][0].author)

    karma = 0

    con = sqlite3.connect("strunt/karma.db")
    #con.backup(sqlite3.connect("strunt/karma_backup.db"))
    cur = con.cursor()

    # Add 1 Karma for a reaction to the one reacting
    if (reacter := str(reac.author)) != "Lapis#7072" and reacter != author:
        x = cur.execute("SELECT karma FROM karma WHERE user = ?", [reacter]).fetchall()
        if not x:
            cur.execute("INSERT INTO karma VALUES(?, ?)", [reacter, 0])
            con.commit()
            x = 0
        cur.execute("UPDATE karma SET karma = ? WHERE user = ?", [reacter, x + 1])

    y = cur.execute("SELECT * FROM karma WHERE user = ?", [author]).fetchall()
    if not y: cur.execute("INSERT INTO karma VALUES(?, ?)", [author, 0])

    z = cur.execute("SELECT * FROM posts where id = ?", [msg_id := str(reac.message.id)]).fetchall()
    if not z:
        cur.execute("INSERT INTO posts VALUES(?, ?, ?,?)", [author, msg_id, "", ""])
        karma += 3
    con.commit()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchall()
    upvotes, downvotes = post[2], post[3]

    if author != reacter and author != "Lapis#7072":
        if reac.emoji.id == UPVOTE_ID: upvotes = set(upvotes.split(", ")).add(reacter)
        elif reac.emoji.id == DOWNVOTE_ID: downvotes = set(downvotes.split(", ")).add(reacter)

    karma += len(upvotes) - len(downvotes)
    if len(upvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=GREAT_ID))
        karma += 6
    if len(downvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=BAD_ID))
        karma -= 6

    cur.execute("UPDATE karma SET karma = ? WHERE user = ?", [karma, author])
    cur.execute("UPDATE posts SET upvotes = ?, downvotes = ? WHERE id = ?", [str(upvotes), str(downvotes), msg_id])

    con.commit()
    con.close()

async def on_reactionJSONONLY(reac):
    #if msg.channel.id != 1134856892007583796: return

    #print(reac)  # MessageReactionAdd()
    #print(reac.reaction_count)  # 2
    #print(reac.emoji)  # <a:KiryuThumbsUp:1326537645391872030>
    #print(reac.message)  # Message(id=1326546884084633780)
    #print(reac.author)  # @torfkopp
    #print(reac.reaction)  # Reaction()
    #print(reac.emoji.id)

    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    with open("strunt/karma.json", "r") as f: karma = json.load(f)

    # Set the author of the message reacted to or the one making lapis embed something
    if (author := str(reac.message.author)) == "Lapis#7072":
        author = str([m async for m in reac.message.channel.history(before=reac.message, limit=1)][0].author)

    # Add 1 Karma for a reaction to the one reacting
    if (reacter := str(reac.author)) != "Lapis#7072" and reacter != author:
        if reacter not in karma: karma[reacter] = {"karma": 0, "posts": {}}
        karma[reacter]["karma"] += 1

    if author not in karma: karma[author] = {"karma": 0, "posts": {}}
    if (msg_id := str(reac.message.id)) not in karma[author]["posts"]:
        karma[author]["posts"][msg_id] = {"upvotes": (), "downvotes": ()}
        karma[author]["karma"] += 3  # Add 3 Karma for a post

    upvotes = karma[author]["posts"][msg_id]["downvotes"]
    downvotes = karma[author]["posts"][msg_id]["downvotes"]

    def set_add(t, e):
        t = set(t)
        t.add(e)
        return tuple(t)

    if author != reacter and author != "Lapis#7072":
        if reac.emoji.id == UPVOTE_ID: upvotes = set_add(upvotes, reacter)
        elif reac.emoji.id == DOWNVOTE_ID: downvotes = set_add(upvotes, reacter)

    karma[author]["karma"] += len(upvotes) - len(downvotes)
    if len(upvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=GREAT_ID))
        karma[author]["karma"] += 6
    if len(downvotes) >= 4:
        await reac.message.add_reaction(PartialEmoji(id=BAD_ID))
        karma[author]["karma"] -= 6

    with open("strunt/karma.json", "w") as f: json.dump(karma, f, indent=4)

async def on_reaction_remove(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    with open("strunt/karma.json", "r") as f: karma = json.load(f)
    if (author := str(reac.message.author)) == "Lapis#7072":
        author = str([m async for m in reac.message.channel.history(before=reac.message, limit=1)][0].author)

    if (reacter := str(reac.author)) != author: karma[reacter]["karma"] -= 1

    msg_id = str(reac.message.id)
    upvotes, downvotes = set(), set()

    con = sqlite3.connect("strunt/karma.db")
    cur = con.cursor()

    post = cur.execute("SELECT * FROM posts WHERE id = ?", [msg_id]).fetchone()
    upvotes, downvotes = set(post[2].split(", ")), set(post[3].split(", "))

    if reac.emoji.id == UPVOTE_ID: upvotes.discard(reacter)
    elif reac.emoji.id == DOWNVOTE_ID: downvotes.discard(reacter)

    up, down = ", ".join(filter(None, upvotes)), ", ".join(filter(None, downvotes))
    cur.execute("UPDATE posts SET upvotes = ?, downvotes = ? WHERE id = ?", [up, down, msg_id])

    con.commit()
    con.close()

    karma[author]["karma"] += len(upvotes) - len(downvotes)

    # Remove benefits again if threshold vote is removed
    if len(upvotes) < 4 and GREAT_ID in reac.msg.reactions():
        await reac.msg.remove_reaction(PartialEmoji(id=GREAT_ID))
        karma[author]["karma"] -= 6
    if len(downvotes) < 4 and BAD_ID in reac.msg.reactions():
        await reac.msg.remove_reaction(PartialEmoji(id=BAD_ID))
        karma[author]["karma"] += 6

    with open("strunt/karma.json", "w") as f: json.dump(karma, f, indent=4)


async def on_reaction_removeJSON(reac):
    if reac.emoji.id not in [UPVOTE_ID, MEH_ID, DOWNVOTE_ID]: return

    with open("strunt/karma.json", "r") as f: karma = json.load(f)

    if (author := str(reac.message.author)) == "Lapis#7072":
        author = str([m async for m in reac.message.channel.history(before=reac.message, limit=1)][0].author)
    msg_id = str(reac.message.id)
    upvotes = karma[author]["posts"][msg_id]["downvotes"]
    downvotes = karma[author]["posts"][msg_id]["downvotes"]

    def set_discard(t, e):
        t = set(t)
        t.discard(e)
        return tuple(t)

    if reac.emoji.id == UPVOTE_ID: upvotes = set_discard(upvotes, author)
    elif reac.emoji.id == DOWNVOTE_ID: downvotes = set_discard(downvotes, author)

    karma[author]["karma"] += len(upvotes) - len(downvotes)

    # Remove benefits again if threshold vote is removed
    if len(upvotes) < 4 and GREAT_ID in reac.msg.reactions():
        await reac.msg.remove_reaction(PartialEmoji(id=GREAT_ID))
        karma[author]["karma"] -= 6
    if len(downvotes) < 4 and BAD_ID in reac.msg.reactions():
        await reac.msg.remove_reaction(PartialEmoji(id=BAD_ID))
        karma[author]["karma"] += 6

    with open("strunt/karma.json", "w") as f: json.dump(karma, f, indent=4)

