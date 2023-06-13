from fastapi import WebSocket
import base64
from enum import Enum
import json
import logging
from typing import Optional
from vocode import getenv
from vocode.streaming.agent.base_agent import BaseAgent
from vocode.streaming.agent.factory import AgentFactory
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.models.events import PhoneCallConnectedEvent, PhoneCallEndedEvent

from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.models.telephony import BaseCallConfig, TwilioConfig
from vocode.streaming.output_device.twilio_output_device import TwilioOutputDevice
from vocode.streaming.models.synthesizer import (
    AzureSynthesizerConfig,
    SynthesizerConfig,
)
from vocode.streaming.models.transcriber import (
    DeepgramTranscriberConfig,
    PunctuationEndpointingConfig,
    TranscriberConfig,
)
from vocode.streaming.synthesizer.azure_synthesizer import AzureSynthesizer
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer
from vocode.streaming.synthesizer.factory import SynthesizerFactory
from vocode.streaming.telephony.client.twilio_client import TwilioClient
from vocode.streaming.telephony.config_manager.base_config_manager import (
    BaseConfigManager,
)
from vocode.streaming.telephony.constants import DEFAULT_SAMPLING_RATE
from vocode.streaming.models.audio_encoding import AudioEncoding
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.telephony.conversation.call import Call
from vocode.streaming.transcriber.base_transcriber import BaseTranscriber
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber
from vocode.streaming.transcriber.factory import TranscriberFactory
from vocode.streaming.utils.events_manager import EventsManager


class PhoneCallAction(Enum):
    CLOSE_WEBSOCKET = 1


class TwilioCall(Call[TwilioOutputDevice]):
    def __init__(
        self,
        from_phone: str,
        to_phone: str,
        base_url: str,
        config_manager: BaseConfigManager,
        agent_config: AgentConfig,
        transcriber_config: TranscriberConfig,
        synthesizer_config: SynthesizerConfig,
        twilio_config: Optional[TwilioConfig] = None,
        twilio_sid: Optional[str] = None,
        conversation_id: Optional[str] = None,
        transcriber_factory: TranscriberFactory = TranscriberFactory(),
        agent_factory: AgentFactory = AgentFactory(),
        synthesizer_factory: SynthesizerFactory = SynthesizerFactory(),
        events_manager: Optional[EventsManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(
            from_phone,
            to_phone,
            base_url,
            config_manager,
            TwilioOutputDevice(),
            agent_config,
            transcriber_config,
            synthesizer_config,
            conversation_id=conversation_id,
            events_manager=events_manager,
            transcriber_factory=transcriber_factory,
            agent_factory=agent_factory,
            synthesizer_factory=synthesizer_factory,
            logger=logger,
        )
        self.base_url = base_url
        self.config_manager = config_manager
        self.twilio_config = twilio_config or TwilioConfig(
            account_sid=getenv("TWILIO_ACCOUNT_SID"),
            auth_token=getenv("TWILIO_AUTH_TOKEN"),
        )
        self.telephony_client = TwilioClient(
            base_url=base_url, twilio_config=self.twilio_config
        )
        self.twilio_sid = twilio_sid
        self.latest_media_timestamp = 0

    async def attach_ws_and_start(self, ws: WebSocket):
        super().attach_ws(ws)

        twilio_call = self.telephony_client.twilio_client.calls(self.twilio_sid).fetch()

        if twilio_call.answered_by in ("machine_start", "fax"):
            self.logger.info(f"Call answered by {twilio_call.answered_by}")
            twilio_call.update(status="completed")
        else:
            await self.wait_for_twilio_start(ws)
            await super().start()
            self.events_manager.publish_event(
                PhoneCallConnectedEvent(
                    conversation_id=self.id,
                    to_phone_number=self.to_phone,
                    from_phone_number=self.from_phone,
                )
            )
            while self.active:
                message = await ws.receive_text()
                response = await self.handle_ws_message(message)
                if response == PhoneCallAction.CLOSE_WEBSOCKET:
                    break
        await self.config_manager.delete_config(self.id)
        self.tear_down()

    async def wait_for_twilio_start(self, ws: WebSocket):
        assert isinstance(self.output_device, TwilioOutputDevice)
        while True:
            message = await ws.receive_text()
            if not message:
                continue
            data = json.loads(message)
            if data["event"] == "start":
                self.logger.debug(
                    f"Media WS: Received event '{data['event']}': {message}"
                )
                self.output_device.stream_sid = data["start"]["streamSid"]
                break

    async def handle_ws_message(self, message) -> Optional[PhoneCallAction]:
        if message is None:
            return PhoneCallAction.CLOSE_WEBSOCKET

        data = json.loads(message)
        if data["event"] == "media":
            media = data["media"]
            chunk = base64.b64decode(media["payload"])
            if self.latest_media_timestamp + 20 < int(media["timestamp"]):
                bytes_to_fill = 8 * (
                    int(media["timestamp"]) - (self.latest_media_timestamp + 20)
                )
                self.logger.debug(f"Filling {bytes_to_fill} bytes of silence")
                # NOTE: 0xff is silence for mulaw audio
                self.receive_audio(b"\xff" * bytes_to_fill)
            self.latest_media_timestamp = int(media["timestamp"])
            self.receive_audio(chunk)
        elif data["event"] == "stop":
            self.logger.debug(f"Media WS: Received event 'stop': {message}")
            self.logger.debug("Stopping...")
            return PhoneCallAction.CLOSE_WEBSOCKET
        return None

    def mark_terminated(self):
        super().mark_terminated()
        self.telephony_client.end_call(self.twilio_sid)
