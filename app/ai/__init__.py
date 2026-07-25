"""Phantom Inspiration Studio — AI module."""

from app.ai.agents.script_writer import ScriptWriter
from app.ai.providers.ollama_client import OllamaClient, get_client
from app.ai.models.script import VideoScript, ContentMetadata, ContentPlan

__all__ = [
    "ScriptWriter",
    "OllamaClient",
    "get_client",
    "VideoScript",
    "ContentMetadata",
    "ContentPlan",
]
