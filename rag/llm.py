"""Bounded Groq generation; no implicit retries or unbounded token usage."""

import os

from .config import GROQ_API_KEY_ENV, GROQ_MODEL_NAME


class ProviderUnavailable(RuntimeError):
    pass


class LLMClient:
    def __init__(self):
        from groq import Groq

        api_key = os.getenv(GROQ_API_KEY_ENV)
        if not api_key or api_key == "your_groq_api_key_here":
            raise ProviderUnavailable("Generation requires a configured GROQ_API_KEY")
        self.client = Groq(api_key=api_key, timeout=15.0, max_retries=0)
        self.model = os.getenv("GROQ_MODEL_NAME", GROQ_MODEL_NAME)

    def generate(self, system_prompt, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, *messages],
                temperature=0,
                max_completion_tokens=500,
            )
            text = response.choices[0].message.content
            if not text:
                raise ValueError("Empty provider response")
            usage = response.usage
            return {
                "text": text,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                }
                if usage
                else {},
            }
        except Exception as exc:
            raise ProviderUnavailable("Generation provider unavailable; retry later") from exc
