import logging
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from vocode.streaming.action.utils import exclude_keys_recursive
from vocode.streaming.models.actions import (
    ActionInput,
    ActionOutput,
    ActionType,
    ParametersType,
    ResponseType,
)


class BaseAction(Generic[ParametersType, ResponseType]):
    description: str = ""
    action_type: str = ActionType.BASE.value

    def __init__(self, should_respond: bool = False):
        self.should_respond = should_respond

    async def run(
        self, action_input: ActionInput[ParametersType]
    ) -> ActionOutput[ResponseType]:
        raise NotImplementedError

    @property
    def parameters_type(self) -> Type[ParametersType]:
        raise NotImplementedError

    @property
    def response_type(self) -> Type[ResponseType]:
        raise NotImplementedError

    def get_openai_function(self):
        parameters_schema = self.parameters_type.schema()
        parameters_schema = exclude_keys_recursive(parameters_schema, {"title"})
        if self.should_respond:
            parameters_schema["properties"][
                "user_message"
            ] = self._user_message_param_info()
            parameters_schema["required"].append("user_message")

        return {
            "name": self.action_type,
            "description": self.description,
            "parameters": parameters_schema,
        }

    def create_action_input(
        self,
        conversation_id: str,
        params: Dict[str, Any],
    ) -> ActionInput[ParametersType]:
        if "user_message" in params:
            del params["user_message"]
        return ActionInput(
            action_type=self.action_type,
            conversation_id=conversation_id,
            params=self.parameters_type(**params),
        )

    def _user_message_param_info(self):
        return {
            "type": "string",
            "description": """A message to reply to the user with BEFORE we make the function call. 
                    Essentially a live response informing them that the function is about to happen.
                    Eg Let me check the weather in San Francisco CA for you """,
        }
