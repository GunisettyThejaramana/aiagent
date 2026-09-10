"""
Local Ollama AI client.

No OpenAI API.
No cloud LLM.
No external AI service.

Ollama runs locally on the user's machine.
"""

from __future__ import annotations

import json
from typing import Any

import requests


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen3:8b",
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    # ============================================================
    # HEALTH
    # ============================================================

    def is_available(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )

            return response.ok

        except Exception:
            return False

    # ============================================================
    # MODELS
    # ============================================================

    def models(self) -> list[str]:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )

            response.raise_for_status()

            data = response.json()

            return [
                item.get("name")
                for item in data.get("models", [])
                if item.get("name")
            ]

        except Exception:
            return []

    # ============================================================
    # CHAT
    # ============================================================

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if json_mode:
            payload["format"] = "json"

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        message = data.get("message", {})

        content = message.get("content", "")

        return str(content).strip()

    # ============================================================
    # SIMPLE GENERATION
    # ============================================================

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
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
        )

    # ============================================================
    # STRUCTURED JSON
    # ============================================================

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
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
        )

        try:
            result = json.loads(text)

            if isinstance(result, dict):
                return result

        except Exception:
            pass

        return {}


# ================================================================
# GLOBAL CLIENT
# ================================================================

ollama_client = OllamaClient()