import datetime
import random

from interactions.models import discord

from core import live as live_mod


class ActivityClass:
    formula1_schedule = {}
    activities = [
        ("liest Bücher", discord.activity.ActivityType.WATCHING),
        ("lauscht Marios Gelaber", discord.activity.ActivityType.LISTENING),
        ("schaut ein paar Anime", discord.activity.ActivityType.WATCHING),
        ("schaut HdR zum X-ten Mal", discord.activity.ActivityType.WATCHING),
        ("judged deine Posts", discord.activity.ActivityType.COMPETING),
        ("hört Anime OST", discord.activity.ActivityType.LISTENING),
        ("sucht nach nützlichen APIs", discord.activity.ActivityType.WATCHING),
        ("schaut sich Anime an", discord.activity.ActivityType.WATCHING),
        ("sucht nach kostenlosen Spielen", discord.activity.ActivityType.WATCHING),
        ("spielt Galgenmännchen", discord.activity.ActivityType.GAME),
        ("sucht nach neuen Insults", discord.activity.ActivityType.WATCHING),
        ("liest die Witze durch", discord.activity.ActivityType.WATCHING),
        ("guckt sich die Patchnotes an", discord.activity.ActivityType.WATCHING),
        ("hört weisen Menschen zu", discord.activity.ActivityType.LISTENING),
        ("schaut sich Tierlisten an", discord.activity.ActivityType.WATCHING),
        ("tritt in einer Quizshow an", discord.activity.ActivityType.COMPETING),
        ("studiert das Wetter", discord.activity.ActivityType.WATCHING),
        ("hat die höchste Elo", discord.activity.ActivityType.COMPETING),
    ]
    status = discord.Status.IDLE

    def __init__(self, bot, formula1_schedule):
        self.bot = bot
        self.formula1_schedule = formula1_schedule

    async def test_mode(self):
        self.status = discord.Status.DND
        await self._change_activity(
            "Befindet sich im Testmodus", discord.activity.ActivityType.COMPETING
        )

    async def rotate_activity(self):
        now = datetime.datetime.now()
        watches_football, watches_formula1, watches_esport = False, False, False
        f1_session = ""

        lm = getattr(live_mod, "live_manager", None)
        if lm:
            if lm.football.task and getattr(lm.football.task, "running", False):
                watches_football = True
            if lm.lolesport.task and getattr(lm.lolesport.task, "running", False):
                watches_esport = True
            if lm.formula1.task and getattr(lm.formula1.task, "running", False):
                watches_formula1 = True

        for time in self.formula1_schedule:
            if "Practice" in self.formula1_schedule.get(time):
                if datetime.timedelta(minutes=0) < now - time < datetime.timedelta(minutes=60):
                    watches_formula1 = True
            if datetime.timedelta(minutes=-60) < now - time < datetime.timedelta(hours=3):
                f1_session = self.formula1_schedule.get(time)

        if watches_football or watches_formula1 or watches_esport:
            self.status = discord.Status.DND
            type_ = discord.activity.ActivityType.WATCHING
            name = ""
            if watches_football and watches_formula1 and watches_esport:
                name = "Fußball, F1 und LoL"
            elif watches_football and watches_formula1 and not watches_esport:
                name = f"Fußball und F1 {f1_session}"
            elif watches_football and not watches_formula1 and watches_esport:
                name = "Fußball und LoL"
            elif not watches_football and watches_formula1 and watches_esport:
                name = f"F1 {f1_session} und LoL"
            elif watches_football and not watches_formula1 and not watches_esport:
                name = "Fußball"
            elif not watches_football and watches_formula1 and not watches_esport:
                name = f"Formel 1 {f1_session}"
            elif not watches_football and not watches_formula1 and watches_esport:
                name = "LoL"
        else:
            self.status = discord.Status.IDLE
            activity = random.choice(self.activities)
            name = activity[0]
            type_ = activity[1]

        await self._change_activity(name, type_)

    async def _change_activity(self, activity_name, activity_type):
        activity = discord.activity.Activity.create(name=activity_name, type=activity_type)
        await self.bot.change_presence(status=self.status, activity=activity)
