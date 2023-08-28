import random

# Pewcentage >w< of appeawance (onwy onye c-c-can appeaw a-a-at a timye) *twerks*
FACES_CHANCE = 5
ACTION_CHANCE = 10
STUTTEWS_CHANCE = 20
FACES_WIST = ["(・`ω´・)", ";;w;;", "OwO", "UwU", ">w<", "^w^", "ÚwÚ", "^-^", ":3", "x3"]
ACTION_WIST = ["*blushes*", "*whispers to self*", "*cries*", "*screams*", "*sweats*", "*twerks*", "*runs away*",
               "*screeches*", "*walks away*", "*sees bulge*", "*looks at you*", "*notices buldge*",
               "*starts twerking*", "*huggles tightly*", "*boops your nose*"]
HAWDCOWE_MYODE = False


def UwUify(msg, uwu_excl: bool = True, uwu_spaces: bool = True):
    """ Function to fuwwy UwUify a myessage """
    msg = UwUifyWords(msg)
    if uwu_excl: msg = UwUifyExclamations(msg)
    if uwu_spaces: msg = UwUifySpaces(msg)
    return msg


def UwUifyWords(wowd):
    """ UwUify aww de wowds """
    # t + h at de beginnying bad >w<
    if wowd[0:2] == "th": wowd = wowd.replace("th", "d", 1)
    elif wowd[0:2] == "Th": wowd = wowd.replace("Th", "D", 1)
    elif wowd[0:2] == "TH": wowd = wowd.replace("TH", "D", 1)

    # Wepwace de unpwonyounceabwe *whispers to self* pawts OwO of de wowd
    uwu_dic = {" th": " d", " TH": " D", " Th": " D", "r": "w", "l": "w", "th": "ff", "R": "W", "L": "W", "TH": "FF"}
    for key in uwu_dic: wowd = wowd.replace(key, uwu_dic.get(key))

    # Add a *starts twerking* cute sound to de pwonyunciation
    for consonyant in {'n', 'm', 'N', 'M'}:
        for vocaw in {'a', 'e', 'i', 'o', 'u'}:
            wowd = wowd.replace(f"{consonyant}{vocaw}", f"{consonyant}y{vocaw}")

    # Sound cute e-e-even whiwst ÚwÚ s-scweamying  ;;w;;
    for consonyant in {'N', 'M'}:
        for vocaw in {'A', 'E', 'I', 'O', 'U'}:
            wowd = wowd.replace(f"{consonyant}{vocaw}", f"{consonyant}Y{vocaw}")

    # If yowouwu awe hawdcowowe enowouwugh x3
    if HAWDCOWE_MYODE:
        wowd = wowd.replace("u", "uwu")
        wowd = wowd.replace("o", "owo")
        wowd = wowd.replace("U", "UWU")
        wowd = wowd.replace("O", "OWO")

    # Nyegations UwU m-m-myust be myet wiff a sad face and *blushes* a *blushes* nya~ shouwd *looks at you* be w-wong
    uwu_speciaw_dic = {" nyo ": " nyo UnU ", " nyot ": " nyot UnU ", "n't ": "nyot UnU ", "nya ": "nya~ ",
                       " NYO ": " NYO UnU ", " NYOT ": " NYOT UnU ", "N'T ": "NYOT UnU ", "NYA ": "NYA~ "}
    for key in uwu_speciaw_dic: wowd = wowd.replace(key, uwu_speciaw_dic.get(key))

    return wowd


def UwUifyExclamations(msg):
    """ UwUify de exwamation mawks """
    excwamyation = ""
    for excl in msg.split("!"):
        if len(excl) < 1: break
        rnd = random.randint(1, 6)
        if rnd == 1:
            excl = excl.replace("!", "!?")
        elif rnd == 2:
            excl = excl.replace("!", "?!!")
        elif rnd == 3:
            excl = excl.replace("!", "?!?1")
        elif rnd == 4:
            excl = excl.replace("!", "!!11")
        elif rnd == 5:
            excl = excl.replace("!", "?!?!")
        elif rnd == 6:
            excl = excl.replace("!", "!!?!!")
        excwamyation += excl + " "
    return excwamyation


def UwUifySpaces(msg):
    """ UwUify wiff wandom faces/actions/stuttews between de wowds """
    wowds = ""

    for wowd in msg.split(" "):
        rnd_pewcent = random.randint(1, 100)

        # Add wandom face aftew de wowds
        if 0 <= rnd_pewcent <= FACES_CHANCE: wowd += " " + random.choice(FACES_WIST)

        # Add  wandom action aftew de wowds
        elif FACES_CHANCE < rnd_pewcent <= (FACES_CHANCE + ACTION_CHANCE): wowd += " " + random.choice(ACTION_WIST)

        # Add stuttew wiff a lengff between 0 and 2
        elif (FACES_CHANCE + ACTION_CHANCE) < rnd_pewcent <= (ACTION_CHANCE + STUTTEWS_CHANCE):
            rand = random.randint(0, 2)
            if wowd != "" and "[" not in wowd and "(" not in wowd:
                wowd = (wowd[0] + "-") * rand + wowd

        wowds += wowd + " "

    return wowds.strip()
