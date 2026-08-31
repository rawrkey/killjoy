"""OpenAI-compatible LLM provider abstraction.

Supports any OpenAI-compatible endpoint (OpenAI, OmniRouter, Ollama, vLLM, etc.).
Falls back gracefully when LLM is unavailable — deterministic pipeline continues.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""
    content: str = ""
    parsed: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    success: bool = False
    error: str = ""


class LLMProvider:
    """OpenAI-compatible LLM provider.

    Works with any endpoint that implements the OpenAI chat completions API:
    - OpenAI (gpt-4o, gpt-4o-mini, etc.)
    - OmniRouter or other routing proxies
    - Ollama (with openai-compatible server)
    - vLLM, LiteLLM, etc.

    The provider is configured via environment variables or explicit arguments.
    When unavailable, all methods return safe fallback responses.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        timeout: int = 15,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._client = None

    def _ensure_client(self) -> Any:
        """Lazy-initialize the OpenAI client."""
        if self._client is not None:
            return self._client

        if not self._api_key:
            logger.warning("No LLM API key configured — LLM agents will use deterministic fallback")
            return None

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=0,  # Don't retry on 429 — fall back to deterministic
            )
            return self._client
        except ImportError:
            logger.warning("openai package not installed — LLM agents will use deterministic fallback")
            return None
        except Exception as e:
            logger.warning("Failed to initialize LLM client: %s", e)
            return None

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Send a chat completion request and return a structured response.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            response_format: Optional {"type": "json_object"} for JSON mode

        Returns:
            LLMResponse with content, parsed dict, and success flag
        """
        client = self._ensure_client()
        if client is None:
            return LLMResponse(error="LLM provider not available")

        try:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self._temperature,
                "max_tokens": max_tokens or self._max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            content = choice.message.content or ""
            usage = {}

            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }

            # Try to parse JSON from content
            parsed = {}
            if content:
                parsed = self._extract_json(content)

            return LLMResponse(
                content=content,
                parsed=parsed,
                model=self._model,
                usage=usage,
                success=True,
            )

        except Exception as e:
            logger.warning("LLM chat failed: %s", e)
            return LLMResponse(error=str(e))

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM text output, trying multiple strategies."""
        import re

        # Strategy 1: Direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 2: Extract from markdown code blocks
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except (json.JSONDecodeError, ValueError):
                pass

        # Strategy 3: Find first { ... } block (greedy to capture nested)
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except (json.JSONDecodeError, ValueError):
                        start = -1  # keep looking

        return {}

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[BaseModel | None, LLMResponse]:
        """Send a chat request and parse the response into a Pydantic model.

        Uses JSON mode to get structured output, then validates against schema.

        Returns:
            Tuple of (parsed model instance or None, raw LLMResponse)
        """
        # Add JSON mode instruction to system message
        json_messages = list(messages)
        if json_messages and json_messages[0]["role"] == "system":
            json_messages[0] = {
                "role": "system",
                "content": json_messages[0]["content"]
                + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation, just JSON.",
            }
        else:
            json_messages.insert(0, {
                "role": "system",
                "content": "Respond with valid JSON only. No markdown, no explanation, just JSON.",
            })

        response = self.chat(
            json_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        # If structured output not supported, retry without response_format
        if not response.success and "structured-outputs" in (response.error or ""):
            logger.info("Model does not support structured outputs, retrying without response_format")
            response = self.chat(
                json_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if not response.success or not response.parsed:
            return None, response

        try:
            parsed_model = schema.model_validate(response.parsed)
            return parsed_model, response
        except Exception as e:
            logger.warning("Failed to parse LLM response into %s: %s", schema.__name__, e)
            return None, response

    @property
    def is_available(self) -> bool:
        """Check if the LLM provider is configured and reachable."""
        return self._api_key != ""


def get_llm_provider(
    api_key: str = "",
    base_url: str = "",
    model: str = "",
) -> LLMProvider:
    """Factory function to create an LLM provider from config values.

    Falls back to environment-based configuration when args are empty.
    """
    import os

    return LLMProvider(
        api_key=api_key or os.getenv("KILLJOY_LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""),
        base_url=base_url or os.getenv("KILLJOY_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=model or os.getenv("KILLJOY_LLM_MODEL", "gpt-4o-mini"),
    )
