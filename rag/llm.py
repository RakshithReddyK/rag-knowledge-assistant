import os
from typing import List

from groq import Groq

from .config import GROQ_API_KEY_ENV, GROQ_MODEL_NAME


class LLMClient:
    def __init__(self):
        api_key = os.getenv(GROQ_API_KEY_ENV)
        if not api_key:
            raise RuntimeError(
                f"Missing {GROQ_API_KEY_ENV} environment variable for Groq API key."
            )
        self.client = Groq(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        messages: List[dict],
        model: str = GROQ_MODEL_NAME,
    ) -> str:
        completion = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=0.2,
        )
        return completion.choices[0].message.content
