import asyncio
import threading
import janus
from typing import Any


class AsyncWorker:
    def __init__(
        self,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
    ) -> None:
        self.worker_task: None | asyncio.Task = None
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


# class InterruptibleEvent:
#     def __init__(
#         self,
#         is_interruptible: bool,
#         payload: Any = None,
#     ):
#         self.interruption_event = threading.Event()
#         self.is_interruptible = is_interruptible
#         self.payload = payload

#     def interrupt(self):
#         if not self.is_interruptible:
#             raise Exception("This event is not interruptible")
#         self.interruption_event.set()

#     def is_interrupted(self):
#         return self.is_interruptible and self.interruption_event.is_set()


# class InterruptibleWorker(AsyncWorker):
#     def __init__(
#         self,
#         input_queue: asyncio.Queue[InterruptibleEvent],
#         output_queue: asyncio.Queue[InterruptibleEvent],
#         max_concurrency=2,
#     ) -> None:
#         super().__init__(input_queue, output_queue)
#         self.max_concurrency = max_concurrency

#     async def _run_loop(self):
#         # TODO Implement concurrency with max_nb_of_thread
#         try:
#             while True:
#                 item = await self.input_queue.get()
#                 if isinstance(item, InterruptibleEvent) and item.is_interrupted():
#                     continue
#                 self.interruptible_event = item
#                 self.current_task = asyncio.create_task(self.process(item))
#                 await self.current_task
#                 self.current_task = None
#         except asyncio.CancelledError:
#             pass

#     async def process(self, item):
#         """
#         Publish results onto output queue.
#         Calls to async function / task should be able to handle asyncio.CancelledError gracefully:
#         """
#         raise NotImplementedError

#     def cancel_current_task(self):
#         """Free up the resources. That's useful so implementors do not have to implement this but:
#         - threads tasks won't be able to be interrupted. Hopefully not too much of a big deal
#             Threads will also get a reference to the interuptible event
#         - asyncio tasks will still have to handle CancelledError and clean up resources
#         """
#         if self.current_task and self.interruptible_event.is_interruptible:
#             return self.current_task.cancel()

#         return False


# class ThreadAsyncWorker(InterruptibleWorker):
#     """
#     This would be the synthesizer
#     """

#     _EOQ = object()

#     def __init__(
#         self,
#         input_queue: asyncio.Queue,
#         output_queue: asyncio.Queue,
#         blocking_task: function,
#         max_nb_of_thread=2,
#     ) -> None:
#         super().__init__(input_queue, output_queue)
#         self.max_nb_of_thread = max_nb_of_thread
#         self.blocking_task = blocking_task

#     async def process(self, item):
#         output_janus_queue = janus.Queue()
#         thread_task = asyncio.to_thread(
#             self.blocking_task, output_janus_queue.sync_q, *item
#         )
#         forward_task = asyncio.create_task(
#             self._forward_from_thead(output_janus_queue, self.output_queue)
#         )
#         await thread_task
#         output_janus_queue.async_q.put_nowait(self._EOQ)
#         await forward_task

#     async def _forward_from_thead(
#         self, output_janus_queue: janus.Queue, output_queue: asyncio.Queue
#     ):
#         while True:
#             thread_item = await output_janus_queue.async_q.get()
#             if self._EOQ:
#                 return
#             output_queue.put_nowait(thread_item)

#     def blocking_task(self, output_queue, *args):
#         raise NotImplementedError
