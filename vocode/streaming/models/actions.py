from enum import Enum
from typing import Generic, TypeVar
from pydantic import BaseModel


class ActionType(str, Enum):
    BASE = "action_base"
    NYLAS_SEND_EMAIL = "action_nylas_send_email"


ParametersType = TypeVar("ParametersType", bound=BaseModel)


class ActionInput(BaseModel, Generic[ParametersType]):
    action_type: str
    conversation_id: str
    params: ParametersType


class VonagePhoneCallActionInput(ActionInput):
    vonage_uuid: str


class TwilioPhoneCallActionInput(ActionInput):
    twilio_sid: str


ResponseType = TypeVar("ResponseType", bound=BaseModel)


class ActionOutput(BaseModel, Generic[ResponseType]):
    action_type: str
    response: ResponseType
