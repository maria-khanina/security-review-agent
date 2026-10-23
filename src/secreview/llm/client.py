"""Chat completion access to the local vLLM server."""

from typing import Protocol

import httpx
from pydantic import BaseModel

from secreview.review_settings import REVIEW_SETTINGS


class TokenLogprobs(BaseModel):
    token: str
    logprob: float
    top: dict[str, float]


class LogprobCompletion(BaseModel):
    text: str
    tokens: list[TokenLogprobs]


class RawAlternative(BaseModel):
    token: str
    logprob: float


class RawTokenEntry(BaseModel):
    token: str
    logprob: float
    top_logprobs: list[RawAlternative]


class RawLogprobs(BaseModel):
    content: list[RawTokenEntry]


class RawMessage(BaseModel):
    content: str


class RawChoice(BaseModel):
    message: RawMessage
    logprobs: RawLogprobs | None = None


class ChatClient(Protocol):
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        """Return the model reply, constrained to the given JSON schema."""
        ...


class VllmChatClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self.http_client = http_client

    def build_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> dict[str, object]:
        """Assemble the request body of one deterministic chat completion."""
        settings = REVIEW_SETTINGS.llm
        return {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": REVIEW_SETTINGS.schema_name,
                    "strict": True,
                    "schema": response_schema,
                },
            },
            "model": settings.model,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "chat_template_kwargs": {"enable_thinking": settings.enable_thinking},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        """Send the messages to the server and return the reply text."""
        payload = self.build_payload(system_prompt, user_prompt, response_schema)
        response = self.http_client.post(
            f"{REVIEW_SETTINGS.llm.base_url}/chat/completions",
            json=payload,
            timeout=REVIEW_SETTINGS.llm.timeout_seconds,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])

    def build_logprob_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
        top_logprobs: int,
    ) -> dict[str, object]:
        """Extend the request body with the token log-probabilities."""
        payload = self.build_payload(system_prompt, user_prompt, response_schema)
        payload["logprobs"] = True
        payload["top_logprobs"] = top_logprobs
        return payload

    def complete_with_logprobs(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
        top_logprobs: int,
    ) -> LogprobCompletion:
        """Send the messages and return the reply with the token log-probabilities."""
        payload = self.build_logprob_payload(
            system_prompt,
            user_prompt,
            response_schema,
            top_logprobs,
        )
        response = self.http_client.post(
            f"{REVIEW_SETTINGS.llm.base_url}/chat/completions",
            json=payload,
            timeout=REVIEW_SETTINGS.llm.timeout_seconds,
        )
        response.raise_for_status()
        choice = response.json()["choices"][0]
        return parse_logprob_choice(choice)


def parse_logprob_choice(choice: object) -> LogprobCompletion:
    """Turn one chat completion choice into the text and its token log-probabilities."""
    parsed = RawChoice.model_validate(choice)
    entries = parsed.logprobs.content if parsed.logprobs else []
    tokens: list[TokenLogprobs] = []
    for entry in entries:
        top: dict[str, float] = {}
        for alternative in entry.top_logprobs:
            top[alternative.token] = alternative.logprob
        tokens.append(
            TokenLogprobs(token=entry.token, logprob=entry.logprob, top=top)
        )
    return LogprobCompletion(text=parsed.message.content, tokens=tokens)
