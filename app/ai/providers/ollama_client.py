"""Ollama API client — wraps the local Ollama server for LLM inference."""

import json
import time
import requests
from typing import Generator, Optional


class OllamaClient:
    """Client for interacting with a local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def _reset_session(self) -> None:
        """Discard a stale keep-alive socket after a local Ollama reset."""
        try:
            self._session.close()
        finally:
            self._session = requests.Session()

    def _post_generation(self, endpoint: str, payload: dict, *, stream: bool = False):
        """Make a local generation request with narrow, recoverable retries.

        Ollama can briefly reset its HTTP socket while moving a model between
        CPU/GPU memory.  That is not a bad script response and should not end
        an otherwise valid automation run on the first disconnect.
        """
        last_error = None
        for attempt in range(1, 4):
            try:
                response = self._session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    stream=stream,
                    # A separate connect/read timeout gives slow local models
                    # time to write a structured script without an infinite UI
                    # hang.  8k context also keeps the 8B model stable on PCs
                    # with modest VRAM.
                    timeout=(15, 420),
                )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                self._reset_session()
                if attempt < 3:
                    time.sleep(attempt * 2)
                    # Health check is deliberately best-effort; the following
                    # request is the authoritative check and yields the final
                    # actionable error if Ollama is truly unavailable.
                    try:
                        self._session.get(f"{self.base_url}/api/tags", timeout=5)
                    except requests.RequestException:
                        pass
        raise ConnectionError(
            "Ollama disconnected while generating the script after 3 recovery attempts. "
            "Try the stable Llama 3.1 8B model, then check that Ollama is running. "
            f"Last error: {last_error}"
        ) from last_error

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
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": num_predict,
                "num_ctx": 8192,
            },
        }
        if system:
            payload["system"] = system
        if stop:
            payload["options"]["stop"] = stop
        if format:
            payload["format"] = format

        r = self._post_generation("/api/generate", payload)
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
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": 8192,
            },
        }
        if system:
            payload["system"] = system

        r = self._post_generation("/api/generate", payload, stream=True)
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
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": 8192,
            },
        }
        if format:
            payload["format"] = format

        r = self._post_generation("/api/chat", payload)
        return r.json().get("message", {}).get("content", "")


# Module-level singleton for convenience
_client: Optional[OllamaClient] = None


def get_client(base_url: str = "http://localhost:11434") -> OllamaClient:
    """Return (and cache) a shared OllamaClient instance."""
    global _client
    if _client is None:
        _client = OllamaClient(base_url)
    return _client
