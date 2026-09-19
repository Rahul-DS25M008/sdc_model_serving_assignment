import logging
from typing import List, Dict
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class FlaggedResponse(BaseModel):
    flagged: bool = False

class GPTService:
    def __init__(self, openai_api_key: str, profanity_prompt: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.aclient = AsyncOpenAI(api_key=openai_api_key)
        self.profanity_prompt = profanity_prompt

    async def aquery_gpt(self, message_history: list,
                         query: str, model="gpt-4o"):
        return await (self.aclient.chat.
                      completions.
                      create(model=model,
                             messages=message_history + [
                                 {"role": "user", "content": query}],
                             stream=True))

    def query_gpt(self, message_history: List[ChatCompletionMessageParam],
                  query: str, model="gpt-4o"):
        message_history_req = message_history + [{"role": "user", "content": query}]
        return (self.client.chat.completions.create(model=model,messages=message_history_req, ))

    def get_ai_response(self, message_history, user_message: str) -> str:
        gpt_response = self.query_gpt(message_history, user_message, model="gpt-4o-mini")
        return gpt_response.choices[0].message.content or ""

    def contains_profanity(self, user_input: str) -> bool:
        response = self.client.chat.completions.parse(
            model="gpt-4o-mini",
            response_format=FlaggedResponse,
            messages=[
                {
                    "role": "system",
                    "content": self.profanity_prompt
                },
                {
                    "role": "user",
                    "content": user_input
                },
            ])
        response = response.choices[0].message.parsed
        if response is None:
            logging.error("Failed to parse profanity response")
            return False
        return response.flagged
