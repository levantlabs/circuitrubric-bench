"""Pluggable LLM backends for the reference runner.

Three backends, all presenting the same ``call()`` interface and normalizing
the response into the same dict shape so the runner stays backend-agnostic:

- ``AnthropicBackend``: official ``anthropic`` SDK, talks to ``/v1/messages``.
- ``OpenAICompatibleBackend``: ``openai`` SDK with a configurable ``base_url``
  and API-key env var. Covers OpenAI itself plus any provider exposing an
  OpenAI-style ``/v1/chat/completions`` endpoint — Ollama, vLLM, TGI, SGLang,
  LM Studio, llama.cpp server, Together, Fireworks, Groq, OpenRouter, and
  self-hosted vLLM/TGI.
- ``OllamaNativeBackend``: native Ollama ``/api/chat``, which (unlike Ollama's
  OpenAI-compat shim) honours a top-level ``think: false`` so reasoning models
  don't spend the whole token budget inside a hidden thinking block.

The SDK packages are optional: each backend imports its SDK lazily and raises a
clear install hint if it's missing. Install what you need, e.g.
``pip install circuitrubric[anthropic]`` / ``[openai]`` / ``[ollama]``.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Uniform interface for an LLM chat completion call.

    Implementations return a dict with keys:

    - ``raw_text``     (str)  concatenated assistant text
    - ``stop_reason``  (str)  backend-native finish reason (kept as-is, not
                              mapped — different vendors use different vocab)
    - ``latency_ms``   (int)  wall-clock around the API call (includes SDK
                              retries)
    - ``usage``        (dict) ``{"input_tokens": int, "output_tokens": int}``
    """

    backend_id: str

    def call(
        self,
        model: str,
        temperature: Optional[float],
        max_tokens: int,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        ...


class AnthropicBackend:
    """Anthropic Messages API backend.

    Constructor reads ``ANTHROPIC_API_KEY`` from the environment. Pass a
    pre-built ``client`` for testing to bypass the SDK construction and the
    env-var check.
    """

    backend_id = "anthropic"

    def __init__(self, client: Any = None, max_retries: int = 2):
        if client is not None:
            self._client = client
            return
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed; run `pip install anthropic`"
            ) from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set; export it before running"
            )
        self._client = anthropic.Anthropic(max_retries=max_retries)

    def call(
        self,
        model: str,
        temperature: Optional[float],
        max_tokens: int,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        # temperature=None must omit the kwarg (some models reject it).
        if temperature is not None:
            kwargs["temperature"] = temperature
        t0 = time.perf_counter()
        msg = self._client.messages.create(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        raw_text = "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        return {
            "raw_text": raw_text,
            "stop_reason": msg.stop_reason,
            "latency_ms": latency_ms,
            "usage": {
                "input_tokens": msg.usage.input_tokens,
                "output_tokens": msg.usage.output_tokens,
            },
        }


class OpenAICompatibleBackend:
    """OpenAI-compatible ``/v1/chat/completions`` backend.

    ``base_url=None`` targets OpenAI's default endpoint. For other providers
    pass the provider's base URL — e.g. ``http://localhost:11434/v1`` for a
    local Ollama, ``http://<host>:8000/v1`` for a self-hosted vLLM, or
    ``https://api.together.xyz/v1`` for Together.

    ``api_key_env`` is the name of the env var holding the API key, so the
    user can switch providers without re-exporting. For local servers that
    don't authenticate (Ollama, vLLM defaults), any non-empty value is fine —
    many SDKs require *some* string. Pass a pre-built ``client`` for testing to
    bypass SDK construction and the env-var check.
    """

    backend_id = "openai"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY",
        client: Any = None,
        max_retries: int = 2,
        reasoning: Any = None,   # OpenRouter unified reasoning control, e.g. {"enabled": False} or {"effort": "low"}
    ):
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.reasoning = reasoning
        if client is not None:
            self._client = client
            return
        try:
            import openai
        except ImportError as e:
            raise RuntimeError(
                "openai package not installed; run `pip install openai`"
            ) from e
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{api_key_env} not set; export it before running "
                f"(for local servers that don't authenticate, set it to any "
                f"non-empty value)"
            )
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
        )

    def call(
        self,
        model: str,
        temperature: Optional[float],
        max_tokens: int,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if self.reasoning is not None:
            kwargs["extra_body"] = {"reasoning": self.reasoning}
        t0 = time.perf_counter()
        resp = self._client.chat.completions.create(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        choice = resp.choices[0]
        raw_text = choice.message.content or ""
        # Some OpenAI-compat servers (older vLLM/Ollama builds) omit usage.
        usage = resp.usage
        if usage is None:
            usage_dict = {"input_tokens": 0, "output_tokens": 0}
        else:
            usage_dict = {
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
            }
        return {
            "raw_text": raw_text,
            "stop_reason": choice.finish_reason,
            "latency_ms": latency_ms,
            "usage": usage_dict,
        }


class OllamaNativeBackend:
    """Native Ollama ``/api/chat`` backend with thinking-mode control.

    Why this exists separately from ``OpenAICompatibleBackend``: Ollama's
    OpenAI-compat shim (``/v1/chat/completions``) on many builds does NOT
    honour any "disable thinking" hint, so a reasoning model (e.g. qwen3,
    deepseek-r1) can burn the entire ``max_tokens`` budget inside a hidden
    ``<think>`` block and return EMPTY content (``finish_reason="length"``).
    The native ``/api/chat`` endpoint accepts a top-level ``think: false`` that
    the OpenAI shim drops.

    ``think`` is tri-state for qwen3-style models: ``False`` forces thinking off
    (a safe default), ``True`` forces it on, ``None`` lets the model decide. NOTE:
    gpt-oss IGNORES the boolean and requires a LEVEL STRING — ``"low"`` /
    ``"medium"`` / ``"high"``; passing ``False`` leaves it at its (runaway)
    default, so use ``think="low"`` for gpt-oss to get a concise, emitted answer.
    """

    backend_id = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        client: Any = None,
        think: Any = False,   # bool (qwen3-style) OR level str "low"/"medium"/"high" (gpt-oss)
        timeout: float = 1800.0,   # generous: large num_predict + reasoning can exceed 300s/call
    ):
        self.base_url = base_url or "http://localhost:11434"
        self.think = think
        if client is not None:
            self._client = client
            return
        try:
            from ollama import Client as _OllamaClient
        except ImportError as e:
            raise RuntimeError(
                "ollama package not installed; run `pip install ollama`"
            ) from e
        self._client = _OllamaClient(host=self.base_url, timeout=timeout)

    def call(
        self,
        model: str,
        temperature: Optional[float],
        max_tokens: int,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        options: dict[str, Any] = {"num_predict": max_tokens}
        if temperature is not None:
            options["temperature"] = temperature
        kwargs: dict[str, Any] = {
            "model": model,
            "stream": False,
            "options": options,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.think is not None:
            kwargs["think"] = self.think
        t0 = time.perf_counter()
        resp = self._client.chat(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        # ollama-python returns a ChatResponse (mapping-like). message.content
        # is the visible answer; message.thinking (when think=True) is the
        # reasoning trace, which we deliberately do NOT feed to the grader.
        msg = resp.get("message", {}) if hasattr(resp, "get") else resp.message
        if hasattr(msg, "get"):
            raw_text = msg.get("content") or ""
        else:
            raw_text = getattr(msg, "content", "") or ""
        done_reason = (
            resp.get("done_reason") if hasattr(resp, "get")
            else getattr(resp, "done_reason", None)
        )
        prompt_eval = (
            resp.get("prompt_eval_count") if hasattr(resp, "get")
            else getattr(resp, "prompt_eval_count", None)
        ) or 0
        eval_count = (
            resp.get("eval_count") if hasattr(resp, "get")
            else getattr(resp, "eval_count", None)
        ) or 0
        return {
            "raw_text": raw_text,
            "stop_reason": done_reason or "stop",
            "latency_ms": latency_ms,
            "usage": {
                "input_tokens": prompt_eval,
                "output_tokens": eval_count,
            },
        }


def make_backend(
    backend_id: str,
    base_url: Optional[str] = None,
    api_key_env: Optional[str] = None,
    max_retries: int = 2,
    think: Any = False,
    reasoning: Any = None,
) -> Backend:
    """Construct a backend by id. Raises ValueError for unknown ids."""
    if backend_id == "anthropic":
        return AnthropicBackend(max_retries=max_retries)
    if backend_id == "openai":
        return OpenAICompatibleBackend(
            base_url=base_url,
            api_key_env=api_key_env or "OPENAI_API_KEY",
            max_retries=max_retries,
            reasoning=reasoning,
        )
    if backend_id == "ollama":
        # base_url accepts the bare host (http://localhost:11434), NOT the
        # /v1 suffix the openai backend wants.
        return OllamaNativeBackend(base_url=base_url, think=think)
    raise ValueError(
        f"Unknown backend: {backend_id!r} (expected 'anthropic', 'openai', "
        f"or 'ollama')"
    )


BACKEND_IDS = ("anthropic", "openai", "ollama")
