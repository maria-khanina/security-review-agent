"""Chat completion access to the local vLLM server."""

from typing import Protocol

import httpx

from secreview.review_settings import REVIEW_SETTINGS


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
