import os
from vocode.streaming.telephony.hosted.outbound_call import OutboundCall
from vocode.streaming.models.telephony import CallEntity, VonageConfig
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
import vocode

vocode.api_key = "YOUR_API_KEY"

if __name__ == "__main__":
    call = OutboundCall(
        recipient=CallEntity(phone_number="<your phone number>"),
        caller=CallEntity(
            phone_number="<your verified caller ID>",
        ),
        agent_config=ChatGPTAgentConfig(
            initial_message=BaseMessage(text="the quick fox jumped over the lazy dog "),
            prompt_preamble="respond two sentences at a time",
        ),
    )
    call.start()
    input("Press enter to end the call...")
    call.end()
