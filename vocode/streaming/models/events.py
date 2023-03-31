from enum import Enum
from vocode.streaming.models.model import TypedModel


class Sender(str, Enum):
    HUMAN = "human"
    BOT = "bot"


class EventType(str, Enum):
    TRANSCRIPT = "event_transcript"
    PHONE_CALL_CONNECTED = "event_phone_call_connected"


class Event(TypedModel):
    conversation_id: str


class TranscriptEvent(Event, type=EventType.TRANSCRIPT):
    text: str
    sender: Sender
    timestamp: float

    def to_string(self, include_timestamp: bool = False) -> str:
        if include_timestamp:
            return f"{self.sender.name}: {self.text} ({self.timestamp})"
        return f"{self.sender.name}: {self.text}"


class PhoneCallConnectedEvent(Event, type=EventType.PHONE_CALL_CONNECTED):
    pass
