import asyncio
from typing import List

from vocode.streaming.models.events import Event, EventType


class EventsManager:
    def __init__(self, subscriptions: List[EventType] = []):
        self.queue = asyncio.Queue()
        self.subscriptions = set(subscriptions)
        self.active = False

    def publish_event(self, event: Event):
        if event.type in self.subscriptions:
            self.queue.put_nowait(event)

    async def start(self):
        self.active = True
        while self.active:
            try:
                event: Event = await self.queue.get()
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
            self.handle_event(event)

    def handle_event(self, event: Event):
        pass

    def end(self):
        self.active = False
        while True:
            try:
                event: Event = self.queue.get_nowait()
                self.handle_event(event)
            except asyncio.QueueEmpty:
                break
