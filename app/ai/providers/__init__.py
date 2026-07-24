"""Phantom Inspiration Studio — AI providers (Ollama, etc.)."""

from app.ai.providers.ollama_client import OllamaClient, get_client

__all__ = ["OllamaClient", "get_client"]
