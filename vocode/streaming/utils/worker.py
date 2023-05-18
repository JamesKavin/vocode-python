from __future__ import annotations

import asyncio
import threading
import janus
from typing import Any, Optional
from typing import TypeVar, Generic
import logging

logger = logging.getLogger(__name__)


class AsyncWorker:
    def __init__(
        self,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue = asyncio.Queue(),
    ) -> None:
        self.worker_task: Optional[asyncio.Task] = None
        self.input_queue = input_queue
        self.output_queue = output_queue

    def start(self) -> asyncio.Task:
        self.worker_task = asyncio.create_task(self._run_loop())
        return self.worker_task

    def send_nonblocking(self, item):
        self.input_queue.put_nowait(item)

    async def _run_loop(self):
        raise NotImplementedError

    def terminate(self):
        if self.worker_task:
            return self.worker_task.cancel()

        return False


class ThreadAsyncWorker(AsyncWorker):
    def __init__(
        self,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue = asyncio.Queue(),
    ) -> None:
        super().__init__(input_queue, output_queue)
        self.worker_thread: Optional[threading.Thread] = None
        self.input_janus_queue: janus.Queue = janus.Queue()
        self.output_janus_queue: janus.Queue = janus.Queue()

    def start(self) -> asyncio.Task:
        self.worker_thread = threading.Thread(target=self._run_loop)
        self.worker_thread.start()
        self.worker_task = asyncio.create_task(self.run_thread_forwarding())
        return self.worker_task

    async def run_thread_forwarding(self):
        try:
            await asyncio.gather(
                self._forward_to_thread(),
                self._forward_from_thead(),
            )
        except asyncio.CancelledError:
            return

    async def _forward_to_thread(self):
        while True:
            item = await self.input_queue.get()
            self.input_janus_queue.async_q.put_nowait(item)

    async def _forward_from_thead(self):
        while True:
            item = await self.output_janus_queue.async_q.get()
            self.output_queue.put_nowait(item)

    def _run_loop(self):
        raise NotImplementedError

    def terminate(self):
        return super().terminate()


class AsyncQueueWorker(AsyncWorker):
    async def _run_loop(self):
        while True:
            try:
                item = await self.input_queue.get()
                await self.process(item)
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.exception("AsyncQueueWorker", exc_info=True)

    async def process(self, item):
        """
        Publish results onto output queue.
        Calls to async function / task should be able to handle asyncio.CancelledError gracefully and not re-raise it
        """
        raise NotImplementedError


Payload = TypeVar("Payload")


class InterruptibleEvent(Generic[Payload]):
    def __init__(
        self,
        payload: Payload,
        is_interruptible: bool = True,
        interruption_event: Optional[threading.Event] = None,
    ):
        self.interruption_event = interruption_event or threading.Event()
        self.is_interruptible = is_interruptible
        self.payload = payload

    def interrupt(self) -> bool:
        """
        Returns True if the event was interruptible and is now interrupted.
        """
        if not self.is_interruptible:
            return False
        self.interruption_event.set()
        return True

    def is_interrupted(self):
        return self.is_interruptible and self.interruption_event.is_set()


class InterruptibleWorker(AsyncWorker):
    def __init__(
        self,
        input_queue: asyncio.Queue[InterruptibleEvent],
        output_queue: asyncio.Queue = asyncio.Queue(),
        max_concurrency=2,
    ) -> None:
        super().__init__(input_queue, output_queue)
        self.input_queue = input_queue
        self.max_concurrency = max_concurrency
        self.current_task = None

    async def _run_loop(self):
        # TODO Implement concurrency with max_nb_of_thread
        while True:
            item = await self.input_queue.get()
            if item.is_interrupted():
                continue
            self.interruptible_event = item
            self.current_task = asyncio.create_task(self.process(item))
            try:
                await self.current_task
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.exception("InterruptibleWorker", exc_info=True)
            self.interruptible_event.is_interruptible = False
            self.current_task = None

    async def process(self, item: InterruptibleEvent):
        """
        Publish results onto output queue.
        Calls to async function / task should be able to handle asyncio.CancelledError gracefully:
        """
        raise NotImplementedError

    def cancel_current_task(self):
        """Free up the resources. That's useful so implementors do not have to implement this but:
        - threads tasks won't be able to be interrupted. Hopefully not too much of a big deal
            Threads will also get a reference to the interruptible event
        - asyncio tasks will still have to handle CancelledError and clean up resources
        """
        if (
            self.current_task
            and not self.current_task.done()
            and self.interruptible_event.is_interruptible
        ):
            return self.current_task.cancel()

        return False
