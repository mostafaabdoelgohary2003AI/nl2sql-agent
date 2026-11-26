"""Minimal OpenAI-compatible chat client (Gemini API, NVIDIA NIM, OpenAI, Ollama...).
Key only from the environment (LLM_API_KEY); retries 429/5xx with backoff."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


class OpenAICompatibleLLM:
    def __init__(self, model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, temperature: float = 0.0, timeout: int = 30) -> None:
        self.model = model or os.environ.get("LLM_MODEL", "gemini-3.1-flash-lite")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL")
                         or "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("an API key is required (LLM_API_KEY)")
        self.temperature, self.timeout = temperature, timeout
        self.calls, self.seconds = 0, 0.0

    def complete(self, system: str, user: str) -> str:
        body = json.dumps({"model": self.model, "temperature": self.temperature,
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": user}]}).encode("utf-8")
        for attempt in range(4):
            req = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, method="POST",
                                         headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {self.api_key}"})
            t = time.time()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                self.calls += 1; self.seconds += time.time() - t
                return payload["choices"][0]["message"]["content"].strip()
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise
                time.sleep(2 ** attempt * 2)
            except (TimeoutError, urllib.error.URLError, OSError):
                if attempt == 3:
                    raise
                time.sleep(2)
