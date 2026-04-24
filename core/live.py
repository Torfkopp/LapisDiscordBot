import json
import datetime

import interactions
from interactions import Task, IntervalTrigger, DateTrigger
from interactions.client.errors import HTTPException

import util
from core import log
from extensions import lolesport
from extensions.football import football
from extensions.formula1 import formula1


MSG_FILE = "variable/sport_messages.json"


class BaseLive:
    def __init__(self, bot, manager, key, channel_id):
        self.bot = bot
        self.manager = manager
        self.key = key  # one of 'score', 'league', 'f1'
        self.channel_id = channel_id
        self.message = None
        self.task = None

    async def load_saved(self):
        saved = self.manager.msgs.get(self.key)
        if saved:
            try:
                channel = self.bot.get_channel(self.channel_id)
                self.message = await channel.fetch_message(saved)
            except Exception:
                self.message = None

    def save_message_id(self):
        if isinstance(self.message, interactions.Message):
            self.manager.update_msg(self.key, self.message.id)
        else:
            self.manager.update_msg(self.key, "")

    def clear_saved_if_not_running(self):
        if not (self.task and getattr(self.task, "running", False)):
            self.manager.update_msg(self.key, "")


class FootballLive(BaseLive):
    async def _live(self):
        embeds, still_going = football.get_live()
        channel = self.bot.get_channel(self.channel_id)
        if not self.message:
            try:
                self.message = await channel.send(embeds=embeds)
            except Exception:
                self.message = None
            self.save_message_id()
            return

        try:
            await self.message.edit(embeds=embeds)
        except HTTPException:
            # message may have been deleted; send a new one
            try:
                self.message = await channel.send(embeds=embeds)
            except Exception:
                self.message = None
        self.save_message_id()

        if not still_going:
            if self.task is not None:
                self.task.stop()
            log.write("Live scoring stops")
            # clear id after task stops
            self.manager.update_msg(self.key, "")

    async def _start_live(self):
        if self.task is None:
            self.task = Task(self._live, IntervalTrigger(minutes=2))
            self.task.start()
            log.write("Live scoring begins")
            return
        if not self.task.running:
            self.task.start()
            log.write("Live scoring begins")

    async def create_schedule(self, now):
        football_schedule = football.create_schedule()
        log.write("Starting times of today's games: " + str(football_schedule))
        for start_time in football_schedule:
            # if already live
            if datetime.timedelta(minutes=0) < (now - start_time) < datetime.timedelta(minutes=90):
                await self._start_live()
            # schedule a start at game time
            Task(self._start_live, DateTrigger(start_time)).start()


class LolesportLive(BaseLive):
    async def _live(self):
        embeds, still_going = lolesport.get_live()
        channel = self.bot.get_channel(self.channel_id)
        if not self.message:
            try:
                self.message = await channel.send(embeds=embeds)
            except Exception:
                self.message = None
            self.save_message_id()
            return

        try:
            await self.message.edit(embeds=embeds)
        except HTTPException:
            try:
                self.message = await channel.send(embeds=embeds)
            except Exception:
                self.message = None
        self.save_message_id()

        if not still_going:
            if self.task is not None:
                self.task.stop()
            log.write("Live league stops")
            self.manager.update_msg(self.key, "")

    async def _start_live(self):
        if self.task is None:
            self.task = Task(self._live, IntervalTrigger(minutes=10))
            self.task.start()
            log.write("Live league begins")
            return
        if not self.task.running:
            self.task.start()
            log.write("Live league begins")

    async def create_schedule(self, now):
        league_schedule = lolesport.create_schedule()
        if len(league_schedule) > 0 and sorted(league_schedule)[-1] < now:
            await self._live()
        log.write("Starting times of today's lol esport matches: " + str(league_schedule))
        for start_time in league_schedule:
            Task(self._start_live, DateTrigger(start_time)).start()


class Formula1Live(BaseLive):
    async def _live(self):
        result, still_going = formula1.auto_result(False)
        channel = self.bot.get_channel(self.channel_id)
        if not self.message:
            try:
                self.message = await channel.send(result)
            except Exception:
                self.message = None
            self.save_message_id()
            return

        try:
            await self.message.edit(content=result)
        except HTTPException:
            try:
                self.message = await channel.send(result)
            except Exception:
                self.message = None
        self.save_message_id()

        if not still_going:
            if self.task is not None:
                self.task.stop()
            self.manager.update_msg(self.key, "")
            log.write("Live F1 stops")

    async def _start_live(self):
        if self.task is None:
            self.task = Task(self._live, IntervalTrigger(minutes=5))
            self.task.start()
            log.write("Live F1 begins")
            return
        if not self.task.running:
            self.task.start()
            log.write("Live F1 begins")

    async def create_schedule(self, formula1_schedule, now):
        log.write("Today's formula1 sessions: " + str(formula1_schedule))
        # follow original behavior but schedule using the manager
        if len(formula1_schedule) == 1:
            start_time = list(formula1_schedule)[0]
            if start_time > now:
                Task(self._start_live, DateTrigger(start_time)).start()
            elif (
                datetime.timedelta(minutes=0) < (now - start_time) < datetime.timedelta(minutes=60)
            ):
                await self._start_live()
            else:
                # session finished already - post old result
                result = formula1.result(formula1_schedule.get(start_time))
                await self.bot.get_channel(self.channel_id).send(result)

        elif len(formula1_schedule) > 1:
            start_times = list(formula1_schedule)
            if start_times[0] >= now:
                for start_time in start_times:
                    if "Practice" in formula1_schedule.get(start_time, ""):
                        Task(self._post_result_after_hour, DateTrigger(start_time)).start(
                            start_time
                        )
                    else:
                        Task(self._start_live, DateTrigger(start_time)).start()

            elif start_times[1] > now or (start_times[1] + datetime.timedelta(hours=1)) > now:
                # post old result for session 0
                await self._post_old_result(start_times[0], formula1_schedule.get(start_times[0]))
                start_time = start_times[1]
                if "Practice" in formula1_schedule.get(start_time, ""):
                    Task(self._post_result_after_hour, DateTrigger(start_time)).start(start_time)
                else:
                    Task(self._start_live, DateTrigger(start_time)).start()

            else:
                await self._post_old_result(start_times[0], formula1_schedule.get(start_times[0]))
                result, still = formula1.auto_result(True)
                await self.bot.get_channel(self.channel_id).send(result)

    async def _post_old_result(self, session, session_info):
        try:
            result = formula1.result(session)
            await self.bot.get_channel(self.channel_id).send(result)
        except Exception:
            Task(
                self._post_old_result,
                DateTrigger(datetime.datetime.now() + datetime.timedelta(hours=1)),
            ).start(session, session_info)

    async def _post_result_after_hour(self, start_time):
        Task(self._post_old_result, DateTrigger(start_time + datetime.timedelta(hours=1))).start()


class LiveManager:
    def __init__(self, bot):
        self.bot = bot
        self.msgs = {"score": "", "league": "", "f1": ""}
        try:
            with open(MSG_FILE) as f:
                self.msgs.update(json.load(f))
        except Exception:
            pass

        self.football = FootballLive(bot, self, "score", util.SPORTS_CHANNEL_ID)
        self.lolesport = LolesportLive(bot, self, "league", util.SPORTS_CHANNEL_ID)
        self.formula1 = Formula1Live(bot, self, "f1", util.SPORTS_CHANNEL_ID)

        # schedule the daily schedule creator at next 00:00
        self._schedule_daily_creator()

    def _write_msgs(self):
        try:
            with open(MSG_FILE, "w") as f:
                json.dump(self.msgs, f)
        except Exception:
            log.write("Failed to write sport messages file")

    def update_msg(self, key, value):
        self.msgs[key] = value
        self._write_msgs()

    def _schedule_daily_creator(self):
        now = datetime.datetime.now()
        today_mid = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= today_mid:
            # schedule for tomorrow
            next_mid = today_mid + datetime.timedelta(days=1)
        else:
            next_mid = today_mid
        Task(self._create_and_schedule_today, DateTrigger(next_mid)).start()

    async def _create_and_schedule_today(self):
        # create today's schedules for all three
        now = datetime.datetime.now()
        # always refresh saved messages into instances
        await self.football.load_saved()
        await self.lolesport.load_saved()
        await self.formula1.load_saved()

        # create schedules
        await self.football.create_schedule(now)
        await self.lolesport.create_schedule(now)

        f1_schedule = formula1.create_schedule()
        await self.formula1.create_schedule(f1_schedule, now)

        # clean up saved message ids that are not associated with running tasks
        self.clean_up()
        for instance in (self.football, self.lolesport, self.formula1):
            if not (instance.task and getattr(instance.task, "running", False)):
                self.update_msg(instance.key, "")

        # schedule next day's creator at next 00:00
        next_mid = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=1
        )
        Task(self._create_and_schedule_today, DateTrigger(next_mid)).start()

    async def start(self):
        # on manager start, if it's after midnight create today's schedule immediately
        now = datetime.datetime.now()
        today_mid = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= today_mid:
            await self._create_and_schedule_today()

    def clean_up(self):
        # Stop tasks and clear saved ids
        for inst in (self.football, self.lolesport, self.formula1):
            if inst.task is not None:
                try:
                    inst.task.stop()
                except Exception:
                    pass
            inst.message = None
            self.update_msg(inst.key, "")
        log.write("Live results cleaned up")


def create_manager(bot):
    return LiveManager(bot)
