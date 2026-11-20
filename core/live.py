import asyncio
import datetime
import json
import os
from functools import partial

from interactions import Task, IntervalTrigger, DateTrigger, TimeTrigger
from interactions.client.errors import NotFound

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
        self.tasks = {}

    def stop_task(self, key):
        task = self.tasks.pop(key, None)
        if task:
            task.stop()
        self.task = next(iter(self.tasks.values()), None)


class DailyLive(BaseLive):
    """Each starting date keeps its own updater and message until it finishes."""

    def __init__(self, *args):
        super().__init__(*args)
        self.days = self.manager.msgs.setdefault(self.key + "_days", {})
        self.scheduled = set()
        self.lock = asyncio.Lock()

    async def _live(self, day):
        async with self.lock:
            try:
                embeds, still_going = await asyncio.to_thread(self.source.get_live, day)
                saved = self.days[day.isoformat()]
                if embeds:
                    channel = self.bot.get_channel(self.channel_id)
                    message = None
                    if saved.get("message_id"):
                        try:
                            message = await channel.fetch_message(saved["message_id"])
                        except NotFound:
                            pass
                    if message:
                        await message.edit(embeds=embeds)
                    else:
                        message = await channel.send(embeds=embeds)
                    saved["message_id"] = message.id
                saved["finished"] = not still_going
                self.manager._write_msgs()
                if not still_going:
                    self.stop_task(day)
                    log.write(f"Live {self.key} for {day} stops")
                    if self.key == "score" and not self.tasks:
                        football.clear_old_matches()
            except Exception as error:
                log.error(error)

    async def _start_live(self, day):
        if day in self.tasks:
            return
        self.days.setdefault(day.isoformat(), {})["finished"] = False
        self.manager._write_msgs()
        self.task = Task(partial(self._live, day), IntervalTrigger(minutes=self.interval))
        self.tasks[day] = self.task
        self.task.start()
        await self._live(day)

    async def create_schedule(self, now=None):
        today = (now or datetime.datetime.now()).date()
        days = {today, today - datetime.timedelta(days=1)}
        for key, saved in list(self.days.items()):
            if not saved.get("finished"):
                day = datetime.date.fromisoformat(key)
                days.add(day)
                await self._start_live(day)
        for day in sorted(days):
            try:
                start_times = await asyncio.to_thread(self.get_start_times, day)
            except Exception as error:
                log.error(error)
                continue
            log.write(f"Starting times for {self.key} on {day}: {start_times}")
            for start_time in start_times:
                current = now or datetime.datetime.now()
                key = (day, start_time)
                if key in self.scheduled:
                    continue
                self.scheduled.add(key)
                if start_time > current:
                    Task(self._start_live, DateTrigger(start_time)).start(day)
                elif current - start_time < datetime.timedelta(hours=3):
                    await self._start_live(day)


class FootballLive(DailyLive):
    source = football
    interval = 2

    def get_start_times(self, day):
        return football.create_schedule(day)


class LolesportLive(DailyLive):
    source = lolesport
    interval = 10

    def get_start_times(self, day):
        return lolesport.create_schedule(day)[0]


class Formula1Live(BaseLive):
    def __init__(self, *args):
        super().__init__(*args)
        self.sessions = self.manager.msgs.setdefault("f1_sessions", {})
        self.schedule = {}
        self.scheduled = set()
        self.lock = asyncio.Lock()

    async def create_schedule(self, formula1_schedule, now=None):
        formula1_schedule = {
            **{datetime.datetime.fromisoformat(key): saved["session"]
               for key, saved in self.sessions.items()
               if not saved.get("finished") and saved.get("session")},
            **formula1_schedule,
        }
        self.schedule.update(formula1_schedule)
        log.write("Today's formula1 sessions: " + str(formula1_schedule))
        for start_time, session in sorted(formula1_schedule.items()):
            current = now or datetime.datetime.now()
            key = start_time.isoformat()
            if key in self.scheduled or self.sessions.get(key, {}).get("finished"):
                continue
            self.scheduled.add(key)
            self.sessions.setdefault(key, {})["session"] = session
            self.manager._write_msgs()
            practice = "Practice" in session
            post_time = start_time + datetime.timedelta(hours=1) if practice else start_time
            callback = self._post_result if practice else self._start_live
            if post_time > current:
                Task(callback, DateTrigger(post_time)).start(start_time, session)
            elif not practice and current < start_time + datetime.timedelta(hours=2):
                await self._start_live(start_time, session)
            else:
                await self._post_result(start_time, session)

    async def _start_live(self, start_time, session):
        if start_time in self.tasks:
            return
        self.task = Task(partial(self._post_result, start_time, session, True), IntervalTrigger(minutes=5))
        self.tasks[start_time] = self.task
        self.task.start()
        await self._post_result(start_time, session, True)

    async def _post_result(self, start_time, session, live=False):
        async with self.lock:
            key = start_time.isoformat()
            saved = self.sessions.get(key, {})
            if saved.get("finished"):
                if live:
                    self.stop_task(start_time)
                return
            still_going = True
            try:
                result, still_going = await asyncio.to_thread(
                    formula1.auto_result, not live, start_time, session
                )
                if result:
                    channel = self.bot.get_channel(self.channel_id)
                    message = None
                    if saved.get("message_id"):
                        try:
                            message = await channel.fetch_message(saved["message_id"])
                        except NotFound:
                            pass
                    if message:
                        await message.edit(content=result)
                    else:
                        message = await channel.send(result)
                    self.message = message if still_going else None
                    self.sessions[key] = {"session": session, "message_id": message.id, "finished": not still_going}
                    self.manager.msgs[self.key] = message.id if still_going else ""
                    self.manager._write_msgs()
                    log.write(f"F1 {session} at {start_time}: updated message {message.id}, finished={not still_going}")
                else:
                    still_going = True
            except Exception as error:
                log.error(error)
                still_going = True
            if not still_going:
                if live:
                    self.stop_task(start_time)
            elif not live:
                log.write(f"F1 {session} at {start_time}: retrying in 10 minutes")
                Task(self._post_result, DateTrigger(datetime.datetime.now() + datetime.timedelta(minutes=10))).start(start_time, session)


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
        self.schedule_task = None

    def _write_msgs(self):
        try:
            with open(MSG_FILE + ".tmp", "w") as f:
                json.dump(self.msgs, f)
            os.replace(MSG_FILE + ".tmp", MSG_FILE)
            log.write("Saved sport messages file", False)
        except Exception:
            log.write("Failed to write sport messages file")

    def update_msg(self, key, value):
        self.msgs[key] = value
        self._write_msgs()

    async def _create_and_schedule_today(self):
        log.write("Creating today's schedules")
        results = await asyncio.gather(
            self.football.create_schedule(),
            self.lolesport.create_schedule(),
            self._create_formula1_schedule(),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                log.error(result)

    async def _create_formula1_schedule(self):
        await self.formula1.create_schedule({})
        f1_schedule = await asyncio.to_thread(formula1.create_schedule)
        await self.formula1.create_schedule(f1_schedule)

    async def start(self):
        if self.schedule_task is None:
            self.schedule_task = Task(self._create_and_schedule_today, TimeTrigger(hour=0, minute=1, utc=False))
        if not self.schedule_task.running:
            self.schedule_task.start()
        await self._create_and_schedule_today()
        log.write("Live manager started")

    def clean_up(self):
        # Stop tasks and clear saved ids
        for inst in (self.football, self.lolesport, self.formula1):
            for key in list(inst.tasks):
                inst.stop_task(key)
            inst.message = None
            self.update_msg(inst.key, "")
        football.clear_old_matches()
        log.write("Live results cleaned up")


def create_manager(bot):
    return LiveManager(bot)
