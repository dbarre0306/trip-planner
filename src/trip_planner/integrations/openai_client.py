import os
from functools import lru_cache

from openai import OpenAI


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


@lru_cache(maxsize=1)
def get_model() -> str:
    model = os.environ.get("MODEL")
    if not model:
        raise RuntimeError("MODEL environment variable is not set")
    return model


def chat_completion(messages: list[dict[str, str]]) -> str:
    client = get_client()
    model = get_model()
    response = client.chat.completions.create(model=model, messages=messages)  # type: ignore[arg-type]
    return response.choices[0].message.content or ""
