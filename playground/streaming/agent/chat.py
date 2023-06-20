import asyncio
import typing
from dotenv import load_dotenv
from playground.streaming.tracing_utils import make_parser_and_maybe_trace
from vocode.streaming.action.worker import ActionsWorker
from vocode.streaming.agent.action_agent import ActionAgent
from vocode.streaming.models.actions import ActionType
from vocode.streaming.models.transcript import Transcript
from vocode.streaming.utils.state_manager import ConversationStateManager

load_dotenv()

from vocode.streaming.agent import *
from vocode.streaming.agent.base_agent import (
    BaseAgent,
    AgentResponseMessage,
    AgentResponseType,
    TranscriptionAgentInput,
)
from vocode.streaming.models.agent import (
    ActionAgentConfig,
)
from vocode.streaming.transcriber.base_transcriber import Transcription
from vocode.streaming.utils import create_conversation_id


class DummyConversationManager(ConversationStateManager):
    pass


async def run_agent(agent: BaseAgent):
    ended = False
    conversation_id = create_conversation_id()

    async def receiver():
        nonlocal ended
        while not ended:
            try:
                event = await agent.get_output_queue().get()
                response = event.payload
                if response.type == AgentResponseType.FILLER_AUDIO:
                    print("Would have sent filler audio")
                elif response.type == AgentResponseType.STOP:
                    print("Agent returned stop")
                    ended = True
                    break
                elif response.type == AgentResponseType.MESSAGE:
                    agent_response = typing.cast(AgentResponseMessage, response)

                    agent.transcript.add_bot_message(
                        agent_response.message.text, conversation_id
                    )
                    print(
                        "AI: "
                        + typing.cast(AgentResponseMessage, response).message.text
                    )
            except asyncio.CancelledError:
                break

    async def sender():
        while not ended:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("Human: ")
                )
                agent.consume_nonblocking(
                    agent.interruptible_event_factory.create(
                        TranscriptionAgentInput(
                            transcription=Transcription(
                                message=message, confidence=1.0, is_final=True
                            ),
                            conversation_id=conversation_id,
                        )
                    )
                )
            except asyncio.CancelledError:
                break

    actions_worker = None
    if isinstance(agent, ActionAgent):
        actions_worker = ActionsWorker(
            input_queue=agent.actions_queue,
            output_queue=agent.get_input_queue(),
            action_factory=agent.action_factory,
        )
        actions_worker.attach_conversation_state_manager(
            agent.conversation_state_manager
        )
        actions_worker.start()

    await asyncio.gather(receiver(), sender())
    if actions_worker is not None:
        actions_worker.terminate()


async def agent_main():
    transcript = Transcript()
    # Replace with your agent!
    agent = ActionAgent(
        ActionAgentConfig(
            prompt_preamble="the assistant is ready to help you send emails",
            actions=[ActionType.NYLAS_SEND_EMAIL.value],
        )
    )
    agent.attach_conversation_state_manager(DummyConversationManager(conversation=None))
    agent.attach_transcript(transcript)
    agent.start()

    try:
        await run_agent(agent)
    except KeyboardInterrupt:
        agent.terminate()


if __name__ == "__main__":
    make_parser_and_maybe_trace()
    asyncio.run(agent_main())
