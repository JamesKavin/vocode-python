
from typing import Optional, Tuple
from vocode.streaming.agent.base_agent import BaseAgent
from vocode.streaming.models.agent import GPT4AllAgentConfig
from vocode.turn_based.agent.gpt4all_agent import GPT4AllAgent as TurnBasedGPT4AllAgent

class GPT4AllAgent(BaseAgent):

    def __init__(self, agent_config: GPT4AllAgentConfig):
        super().__init__(agent_config=agent_config)
        self.turn_based_agent = TurnBasedGPT4AllAgent(
            model_path=agent_config.model_path,
            system_prompt=agent_config.prompt_preamble,
            initial_message=agent_config.initial_message.text
        )

    def respond(
        self,
        human_input,
        is_interrupt: bool = False,
        conversation_id: Optional[str] = None,
    ) -> Tuple[Optional[str], bool]:
        return self.turn_based_agent.respond(human_input), False