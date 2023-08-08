import interactions

import uwuifier

UWUCHANCE = 5  # D-De chance dat a commyand wesponse gets u-u-uwuified


def uwuify_embed(embed):
    """ Uwuifies the embed """
    if not isinstance(embed, interactions.Embed): return embed
    embed.title = uwuifier.UwUify(embed.title)
    for field in embed.fields:
        field.name = uwuifier.UwUify(field.name, False, False)
        field.value = uwuifier.UwUify(field.value, False, False)
    return embed


def germanise(msg):
    """ Fixes formatting errors concerning the German letters """
    char_map = {ord('Ã'): '', ord('¼'): 'ü', ord('¶'): 'ö', ord('¤'): 'ä', ord('Ÿ'): 'ß'}
    return msg.translate(char_map)
