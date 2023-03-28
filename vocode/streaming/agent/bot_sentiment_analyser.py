from typing import Optional
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel

TEMPLATE = """
Read the following conversation classify the final emotion of the Bot as one of [{emotions}].
Output the degree of emotion as a value between 0 and 1 in the format EMOTION,DEGREE: ex. {example_emotion},0.5
            
<start>
{{transcript}}
<end>
"""


class BotSentiment(BaseModel):
    emotion: Optional[str] = None
    degree: float = 0.0


class BotSentimentAnalyser:
    def __init__(self, emotions: list[str], model_name: str = "text-davinci-003"):
        self.model_name = model_name
        self.llm = OpenAI(
            model_name=self.model_name,
        )
        assert len(emotions) > 0
        self.emotions = [e.lower() for e in emotions]
        self.prompt = PromptTemplate(
            input_variables=["transcript"],
            template=TEMPLATE.format(
                emotions=",".join(self.emotions), example_emotion=self.emotions[0]
            ),
        )

    def analyse(self, transcript: str) -> BotSentiment:
        prompt = self.prompt.format(transcript=transcript)
        response = self.llm(prompt).strip()
        tokens = response.split(",")
        if len(tokens) != 2:
            return BotSentiment(emotion=None, degree=0.0)
        emotion, degree = tokens
        emotion = emotion.strip().lower()
        if emotion.lower() not in self.emotions:
            return BotSentiment(emotion=None, degree=0.0)
        try:
            degree = float(degree.strip())
        except ValueError:
            return BotSentiment(emotion=emotion, degree=0.5)
        return BotSentiment(emotion=emotion, degree=degree)
