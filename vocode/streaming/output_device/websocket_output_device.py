from __future__ import annotations

import asyncio
from fastapi import WebSocket
from vocode.streaming.models.audio_encoding import AudioEncoding
from vocode.streaming.output_device.base_output_device import BaseOutputDevice
from vocode.streaming.models.websocket import AudioMessage


class WebsocketOutputDevice(BaseOutputDevice):
    def __init__(
        self, ws: WebSocket, sampling_rate: int, audio_encoding: AudioEncoding
    ):
        super().__init__(sampling_rate, audio_encoding)
        self.ws = ws
        self.active = True
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.process_task = asyncio.create_task(self.process())

    def mark_closed(self):
        self.active = False

    async def process(self):
        while self.active:
            message = await self.queue.get()
            await self.ws.send_text(message)

    def send_nonblocking(self, chunk: bytes):
        if self.active:
            audio_message = AudioMessage.from_bytes(chunk)
            self.queue.put_nowait(audio_message.json())

    def terminate(self):
        self.process_task.cancel()
