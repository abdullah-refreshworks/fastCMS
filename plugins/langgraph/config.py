"""
Configuration for LangGraph plugin.
"""

import os
from typing import Optional

class LangGraphConfig:
    """LangGraph plugin configuration."""

    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 1000

    # Supported Models
    AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ]

    # Node Types
    NODE_TYPES = {
        "llm": "LLM Node",
        "tool": "Tool Node",
        "condition": "Conditional Node",
        "function": "Function Node",
        "start": "Start Node",
        "end": "End Node",
    }

config = LangGraphConfig()
