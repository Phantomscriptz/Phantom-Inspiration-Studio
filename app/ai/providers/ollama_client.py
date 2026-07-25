"""Ollama API client — wraps the local Ollama server for LLM inference."""

import json
import requests
from typing import Generator, Optional


class OllamaClient:
    """Client for interacting with a local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Health / model management
    # ------------------------------------------------------------------

    def is_alive(self) -> bool:
        """Check whether the Ollama server is reachable."""
        try:
            r = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except requests.ConnectionError:
            return False

    def list_models(self) -> list[dict]:
        """Return a list of locally available models."""
        r = self._session.get(f"{self.base_url}/api/tags", timeout=10)
        r.raise_for_status()
        return r.json().get("models", [])

    def model_exists(self, model_name: str) -> bool:
        """Check whether a specific model is available locally."""
        models = self.list_models()
        return any(m["name"] == model_name for m in models)

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        model: str = "qwen2.5:7b",
        system: Optional[str] = None,
        temperature: float = 0.8,
        top_p: float = 0.9,
        num_predict: int = 2048,
        stop: Optional[list[str]] = None,
        format: Optional[str] = None,  # "json" for structured output
    ) -> str:
        """
        Generate a completion from the model.

        Args:
            prompt: The user prompt.
            model: Model name to use.
            system: Optional system prompt.
            temperature: Sampling temperature (0.0–2.0).
            top_p: Top-p sampling.
            num_predict: Max tokens to generate.
            stop: Optional stop sequences.
            format: "json" to force JSON output.

        Returns:
            The generated text.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": num_predict,
            },
        }
        if system:
            payload["system"] = system
        if stop:
            payload["options"]["stop"] = stop
        if format:
            payload["format"] = format

        r = self._session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=300,
        )
        r.raise_for_status()
        return r.json().get("response", "")

    def generate_json(
        self,
        prompt: str,
        model: str = "qwen2.5:7b",
        system: Optional[str] = None,
        temperature: float = 0.7,
        num_predict: int = 4096,
    ) -> dict:
        """
        Generate and parse a JSON response from the model.

        Returns the parsed dict, or raises ValueError on parse failure.
        """
        raw = self.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            num_predict=num_predict,
            format="json",
        )
        return json.loads(raw)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def generate_stream(
        self,
        prompt: str,
        model: str = "qwen2.5:7b",
        system: Optional[str] = None,
        temperature: float = 0.8,
        num_predict: int = 2048,
    ) -> Generator[str, None, None]:
        """Yield tokens as they are generated (streaming)."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }
        if system:
            payload["system"] = system

        r = self._session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            stream=True,
            timeout=300,
        )
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                yield token
                if chunk.get("done"):
                    break

    # ------------------------------------------------------------------
    # Chat interface (multi-turn)
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        model: str = "qwen2.5:7b",
        temperature: float = 0.7,
        num_predict: int = 4096,
        format: Optional[str] = None,
    ) -> str:
        """
        Multi-turn chat completion.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }
        if format:
            payload["format"] = format

        r = self._session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=300,
        )
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")


# Module-level singleton for convenience
_client: Optional[OllamaClient] = None


def get_client(base_url: str = "http://localhost:11434") -> OllamaClient:
    """Return (and cache) a shared OllamaClient instance."""
    global _client
    if _client is None:
        _client = OllamaClient(base_url)
    return _client
