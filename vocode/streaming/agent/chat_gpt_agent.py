import logging

from typing import Any, Dict, List, Optional, Tuple, Union

import openai
from typing import AsyncGenerator, Optional, Tuple

import logging
from pydantic import BaseModel

from vocode import getenv
from vocode.streaming.action.factory import ActionFactory
from vocode.streaming.agent.base_agent import RespondAgent
from vocode.streaming.models.actions import FunctionCall, FunctionFragment
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.agent.utils import (
    format_openai_chat_messages_from_transcript,
    collate_response_async,
    openai_get_tokens,
)
from vocode.streaming.models.events import Sender
from vocode.streaming.models.transcript import Transcript
from vocode.streaming.vector_db.factory import VectorDBFactory


class ChatGPTAgent(RespondAgent[ChatGPTAgentConfig]):
    def __init__(
        self,
        agent_config: ChatGPTAgentConfig,
        action_factory: ActionFactory = ActionFactory(),
        logger: Optional[logging.Logger] = None,
        openai_api_key: Optional[str] = None,
        vector_db_factory=VectorDBFactory(),
    ):
        super().__init__(
            agent_config=agent_config, action_factory=action_factory, logger=logger
        )
        if agent_config.azure_params:
            openai.api_type = agent_config.azure_params.api_type
            openai.api_base = getenv("AZURE_OPENAI_API_BASE")
            openai.api_version = agent_config.azure_params.api_version
            openai.api_key = getenv("AZURE_OPENAI_API_KEY")
        else:
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = None
            openai.api_key = openai_api_key or getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment or passed in")
        self.first_response = (
            self.create_first_response(agent_config.expected_first_prompt)
            if agent_config.expected_first_prompt
            else None
        )
        self.is_first_response = True

        if self.agent_config.vector_db_config:
            self.vector_db = vector_db_factory.create_vector_db(
                self.agent_config.vector_db_config
            )

    def get_functions(self):
        assert self.agent_config.actions
        if not self.action_factory:
            return None
        return [
            self.action_factory.create_action(action_type).get_openai_function()
            for action_type in self.agent_config.actions
        ]

    def get_chat_parameters(self, messages: Optional[List] = None):
        assert self.transcript is not None
        messages = messages or format_openai_chat_messages_from_transcript(
            self.transcript, self.agent_config.prompt_preamble
        )

        parameters: Dict[str, Any] = {
            "messages": messages,
            "max_tokens": self.agent_config.max_tokens,
            "temperature": self.agent_config.temperature,
        }

        if self.agent_config.azure_params is not None:
            parameters["engine"] = self.agent_config.azure_params.engine
        else:
            parameters["model"] = self.agent_config.model_name

        if self.functions:
            parameters["functions"] = self.functions

        return parameters

    def create_first_response(self, first_prompt):
        messages = [
            (
                [{"role": "system", "content": self.agent_config.prompt_preamble}]
                if self.agent_config.prompt_preamble
                else []
            )
            + [{"role": "user", "content": first_prompt}]
        ]

        parameters = self.get_chat_parameters(messages)
        return openai.ChatCompletion.create(**parameters)

    def attach_transcript(self, transcript: Transcript):
        self.transcript = transcript

    async def respond(
        self,
        human_input,
        conversation_id: str,
        is_interrupt: bool = False,
    ) -> Tuple[str, bool]:
        assert self.transcript is not None
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            return cut_off_response, False
        self.logger.debug("LLM responding to human input")
        if self.is_first_response and self.first_response:
            self.logger.debug("First response is cached")
            self.is_first_response = False
            text = self.first_response
        else:
            chat_parameters = self.get_chat_parameters()
            chat_completion = await openai.ChatCompletion.acreate(**chat_parameters)
            text = chat_completion.choices[0].message.content
        self.logger.debug(f"LLM response: {text}")
        return text, False

    async def generate_response(
        self,
        human_input: str,
        conversation_id: str,
        is_interrupt: bool = False,
    ) -> AsyncGenerator[Union[str, FunctionCall], None]:
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            yield cut_off_response
            return
        assert self.transcript is not None

        if self.agent_config.vector_db_config:
            docs_with_scores = await self.vector_db.similarity_search_with_score(
                self.transcript.get_last_user_message()[1]
            )
            docs_with_scores_str = "\n\n".join(
                [
                    "Document: "
                    + doc[0].metadata["source"]
                    + f" (Confidence: {doc[1]})\n"
                    + doc[0].lc_kwargs["page_content"].replace(r"\n", "\n")
                    for doc in docs_with_scores
                ]
            )
            self.transcript.add_vector_db_results(
                f"Found {len(docs_with_scores)} similar documents:\n{docs_with_scores_str}",
                conversation_id,
            )
            messages = format_openai_chat_messages_from_transcript(
                self.transcript, self.agent_config.prompt_preamble
            )
            chat_parameters = self.get_chat_parameters(messages)
            self.transcript.remove_last_vector_db_log()
        else:
            chat_parameters = self.get_chat_parameters()
        chat_parameters["stream"] = True
        stream = await openai.ChatCompletion.acreate(**chat_parameters)
        async for message in collate_response_async(
            openai_get_tokens(stream), get_functions=True
        ):
            yield message
