import asyncio
import datetime
import json
import os
from functools import partial

import interactions
from interactions import Task, IntervalTrigger, DateTrigger
from interactions.client.errors import HTTPException, NotFound

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
                log.write(f"Loaded saved message: {self.key} {self.message.id}")
            except Exception:
                self.message = None
                log.write(f"Failed to load saved message for {self.key}")

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
        league_schedule, last_game_time = lolesport.create_schedule()
        if len(league_schedule) > 0 and sorted(league_schedule)[-1] < now < last_game_time:
            await self._live()
        log.write("Starting times of today's lol esport matches: " + str(league_schedule))
        for start_time in league_schedule:
            Task(self._start_live, DateTrigger(start_time)).start()


class Formula1Live(BaseLive):
    def __init__(self, *args):
        super().__init__(*args)
        self.sessions = self.manager.msgs.setdefault("f1_sessions", {})
        self.scheduled = set()
        self.lock = asyncio.Lock()
        self.live_session = None

    async def create_schedule(self, formula1_schedule, now):
        log.write("Today's formula1 sessions: " + str(formula1_schedule))
        for start_time, session in sorted(formula1_schedule.items()):
            key = start_time.isoformat()
            if key in self.scheduled or self.sessions.get(key, {}).get("finished"):
                continue
            self.scheduled.add(key)
            practice = "Practice" in session
            post_time = start_time + datetime.timedelta(hours=1) if practice else start_time
            callback = self._post_result if practice else self._start_live
            if post_time > now:
                Task(callback, DateTrigger(post_time)).start(start_time, session)
            elif not practice and now < start_time + datetime.timedelta(hours=2):
                await self._start_live(start_time, session)
            else:
                await self._post_result(start_time, session)

    async def _start_live(self, start_time, session):
        if self.task:
            self.task.stop()
        self.live_session = start_time
        self.task = Task(partial(self._post_result, start_time, session, True), IntervalTrigger(minutes=5))
        self.task.start()
        await self._post_result(start_time, session, True)

    async def _post_result(self, start_time, session, live=False):
        async with self.lock:
            key = start_time.isoformat()
            saved = self.sessions.get(key, {})
            if saved.get("finished"):
                if live and self.task and self.live_session == start_time:
                    self.task.stop()
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
                    self.sessions[key] = {"message_id": message.id, "finished": not still_going}
                    self.manager.msgs[self.key] = message.id if still_going else ""
                    self.manager._write_msgs()
                    log.write(f"F1 {session} at {start_time}: updated message {message.id}, finished={not still_going}")
                else:
                    still_going = True
            except Exception as error:
                log.error(error)
                still_going = True
            if not still_going:
                if live and self.task and self.live_session == start_time:
                    self.task.stop()
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
        # create today's schedules for all three
        log.write("Creating today's schedules")
        now = datetime.datetime.now()

        await self.football.create_schedule(now)
        await self.football.load_saved()

        await self.lolesport.create_schedule(now)
        await self.lolesport.load_saved()

        f1_schedule = await asyncio.to_thread(formula1.create_schedule)
        await self.formula1.create_schedule(f1_schedule, datetime.datetime.now())
        await self.formula1.load_saved()

        # clean up saved message ids that are not associated with running tasks
        for instance in (self.football, self.lolesport, self.formula1):
            if not (instance.task and getattr(instance.task, "running", False)):
                self.update_msg(instance.key, "")
        if not (self.football.task and self.football.task.running):
            football.clear_old_matches()

        # schedule next day's creator at next 00:01
        next_mid = now.replace(hour=0, minute=1, second=0, microsecond=0) + datetime.timedelta(
            days=1
        )
        Task(self._create_and_schedule_today, DateTrigger(next_mid)).start()

    async def start(self):
        await self._create_and_schedule_today()
        log.write("Live manager started")

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
        football.clear_old_matches()
        log.write("Live results cleaned up")


def create_manager(bot):
    return LiveManager(bot)
