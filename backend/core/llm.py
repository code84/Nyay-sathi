import json
import signal
from typing import Iterator, Type, TypeVar
from pydantic import BaseModel, ValidationError
from .config import settings

T = TypeVar("T", bound=BaseModel)

LLM_TIMEOUT = 20   # seconds per LLM call


class LLMTimeoutError(RuntimeError):
    pass


class LLM:
    """Every provider implements ask() and stream().
    Nothing else in the app knows which model is running."""

    def ask(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        raise NotImplementedError

    def stream(self, prompt: str, system: str = "") -> Iterator[str]:
        raise NotImplementedError

    def ask_json(self, prompt: str, model_cls: Type[T], system: str = "", retries: int = 1) -> T:
        """Ask for JSON and validate it against a schema.
        If it fails, retry once and tell the model what was wrong."""
        last_err = ""
        for _ in range(retries + 1):
            p = prompt
            if last_err:
                p += f"\n\nYour last reply was invalid: {last_err}. Return valid JSON only."
            raw = self.ask(p, system, json_mode=True)
            try:
                return model_cls.model_validate(json.loads(raw))
            except (json.JSONDecodeError, ValidationError) as e:
                last_err = str(e)[:300]
        raise ValueError(f"Model did not return valid {model_cls.__name__}: {last_err}")


class GeminiLLM(LLM):
    def __init__(self):
        from google import genai
        from google.genai import types
        self._types = types
        self.client = genai.Client(api_key=settings.api_key)

    def _cfg(self, system, json_mode):
        return self._types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=0.2,
            response_mime_type="application/json" if json_mode else None,
        )

    def ask(self, prompt, system="", json_mode=False):
        r = self.client.models.generate_content(
            model=settings.model, contents=prompt, config=self._cfg(system, json_mode),
            http_options=self._types.HttpOptions(timeout=30000))
        return r.text or ""

    def stream(self, prompt, system=""):
        for chunk in self.client.models.generate_content_stream(
                model=settings.model, contents=prompt, config=self._cfg(system, False),
                http_options=self._types.HttpOptions(timeout=30000)):
            if chunk.text:
                yield chunk.text


class GroqLLM(LLM):
    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=settings.api_key, timeout=LLM_TIMEOUT, max_retries=0)

    def _msgs(self, prompt, system):
        m = [{"role": "system", "content": system}] if system else []
        return m + [{"role": "user", "content": prompt}]

    def ask(self, prompt, system="", json_mode=False):
        kw = {"response_format": {"type": "json_object"}} if json_mode else {}
        try:
            r = self.client.chat.completions.create(
                model=settings.model, messages=self._msgs(prompt, system),
                temperature=0.2, max_tokens=4096, **kw)
            return r.choices[0].message.content or ""
        except Exception as e:
            raise LLMTimeoutError(f"Groq call failed: {e}") from e

    def stream(self, prompt, system=""):
        try:
            s = self.client.chat.completions.create(
                model=settings.model, messages=self._msgs(prompt, system),
                temperature=0.2, stream=True)
            for chunk in s:
                t = chunk.choices[0].delta.content
                if t:
                    yield t
        except Exception as e:
            raise LLMTimeoutError(f"Groq stream failed: {e}") from e


class FakeLLM(LLM):
    """For tests: returns canned replies and remembers the prompts it received."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.prompts = []

    def ask(self, prompt, system="", json_mode=False):
        self.prompts.append(prompt)
        return self.replies.pop(0)

    def stream(self, prompt, system=""):
        self.prompts.append(prompt)
        yield self.replies.pop(0)


def get_llm() -> LLM:
    if settings.provider == "gemini":
        return GeminiLLM()
    if settings.provider == "groq":
        return GroqLLM()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.provider}")