"""
Local Ollama client.

Uses Ollama running locally.

Default:
    http://127.0.0.1:11434

Default model:
    qwen3:8b

Performance:
    - Reuses one HTTP session
    - Keeps the model loaded
    - Disables Qwen3 thinking by default for faster responses
    - Limits unnecessary token generation
    - Uses local Ollama only
    - Measures Ollama request time
    - Supports normal chat
    - Supports JSON generation
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from app.config import settings


class OllamaClient:

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (
            base_url
            or settings.OLLAMA_BASE_URL
        ).rstrip("/")

        self.model = (
            model
            or settings.OLLAMA_MODEL
        )

        self.timeout = (
            timeout
            or settings.OLLAMA_TIMEOUT
        )

        # Keep model loaded in Ollama.
        self.keep_alive = -1

        # Default maximum generated tokens.
        self.num_predict = 256

        # Qwen3 thinking can make CPU inference much slower.
        # We disable it for normal enterprise assistant usage.
        self.think = False

        # Keep the existing context size.
        self.num_ctx = 8192

        # Reuse HTTP connection.
        self.session = requests.Session()

        self.headers = {
            "Content-Type": "application/json",
        }

    # ---------------------------------------------------------
    # CHECK OLLAMA
    # ---------------------------------------------------------

    def is_available(self) -> bool:
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=3,
            )

            return response.ok

        except Exception:
            return False

    # ---------------------------------------------------------
    # GET MODELS
    # ---------------------------------------------------------

    def models(self) -> list[str]:
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )

            response.raise_for_status()

            data = response.json()

            return [
                item.get("name")
                for item in data.get("models", [])
                if item.get("name")
            ]

        except Exception as exc:
            print("Ollama models error:", exc)
            return []

    # ---------------------------------------------------------
    # CHAT
    # ---------------------------------------------------------

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        json_mode: bool = False,
        num_predict: int | None = None,
        think: bool | None = None,
    ) -> str:

        max_tokens = (
            num_predict
            if num_predict is not None
            else self.num_predict
        )

        thinking_enabled = (
            self.think
            if think is None
            else think
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,

            # Keep model loaded.
            "keep_alive": self.keep_alive,

            # Qwen3 supports this.
            # False gives much faster normal responses.
            "think": thinking_enabled,

            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.num_ctx,
            },
        }

        if json_mode:
            payload["format"] = "json"

        message_chars = sum(
            len(str(message.get("content", "")))
            for message in messages
        )

        print()
        print("========================================")
        print("OLLAMA REQUEST")
        print("========================================")
        print("Model          :", self.model)
        print("Messages       :", len(messages))
        print("Prompt chars   :", message_chars)
        print("Thinking       :", thinking_enabled)
        print("Context        :", self.num_ctx)
        print("Max tokens     :", max_tokens)

        start_time = time.perf_counter()

        try:

            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )

            elapsed = time.perf_counter() - start_time

            print(
                f"Ollama response time: {elapsed:.2f} seconds"
            )

            response.raise_for_status()

            data = response.json()

        except requests.Timeout:

            elapsed = time.perf_counter() - start_time

            print(
                f"Ollama timeout after {elapsed:.2f} seconds"
            )

            raise

        except requests.RequestException as exc:

            elapsed = time.perf_counter() - start_time

            print(
                f"Ollama request failed after "
                f"{elapsed:.2f} seconds:",
                exc,
            )

            raise

        message = data.get("message", {})

        content = message.get(
            "content",
            "",
        )

        result = str(content).strip()

        # -----------------------------------------------------
        # OLLAMA PERFORMANCE INFORMATION
        # -----------------------------------------------------

        total_duration = data.get(
            "total_duration"
        )

        load_duration = data.get(
            "load_duration"
        )

        prompt_eval_duration = data.get(
            "prompt_eval_duration"
        )

        eval_duration = data.get(
            "eval_duration"
        )

        if total_duration:

            print(
                "Ollama total duration : "
                f"{total_duration / 1_000_000_000:.2f} seconds"
            )

        if load_duration:

            print(
                "Model load duration   : "
                f"{load_duration / 1_000_000_000:.2f} seconds"
            )

        if prompt_eval_duration:

            print(
                "Prompt eval duration  : "
                f"{prompt_eval_duration / 1_000_000_000:.2f} seconds"
            )

        if eval_duration:

            print(
                "Generation duration   : "
                f"{eval_duration / 1_000_000_000:.2f} seconds"
            )

        print(
            "Response chars         :",
            len(result),
        )

        print("OLLAMA RESPONSE COMPLETE")
        print("========================================")
        print()

        return result

    # ---------------------------------------------------------
    # GENERATE
    # ---------------------------------------------------------

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        num_predict: int | None = None,
        think: bool | None = None,
    ) -> str:

        return self.chat(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=temperature,
            num_predict=num_predict,
            think=think,
        )

    # ---------------------------------------------------------
    # GENERATE JSON
    # ---------------------------------------------------------

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        think: bool | None = None,
    ) -> dict:

        text = self.chat(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
            json_mode=True,
            num_predict=256,
            think=think,
        )

        # -----------------------------------------------------
        # NORMAL JSON
        # -----------------------------------------------------

        try:

            result = json.loads(text)

            if isinstance(result, dict):
                return result

        except Exception as exc:

            print(
                "Ollama JSON parsing error:",
                exc,
            )

        # -----------------------------------------------------
        # CLEAN MARKDOWN JSON
        # -----------------------------------------------------

        try:

            cleaned = text.strip()

            if cleaned.startswith("```"):

                cleaned = (
                    cleaned
                    .replace(
                        "```json",
                        "",
                    )
                    .replace(
                        "```JSON",
                        "",
                    )
                    .replace(
                        "```",
                        "",
                    )
                    .strip()
                )

                result = json.loads(cleaned)

                if isinstance(result, dict):
                    return result

        except Exception as exc:

            print(
                "Ollama cleaned JSON parsing error:",
                exc,
            )

        return {}


# -------------------------------------------------------------
# SINGLE GLOBAL CLIENT
# -------------------------------------------------------------

ollama_client = OllamaClient()