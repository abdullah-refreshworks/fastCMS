"""
AI Configuration and Model Initialization.
"""
from typing import Optional
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIConfig:
    """AI Configuration Manager."""
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = "gpt-4o-mini"  # Default model
        
        if self.provider == "openai":
            self.model_name = "gpt-4o-mini"
        elif self.provider == "anthropic":
            self.model_name = "claude-3-sonnet-20240229"
        elif self.provider == "ollama":
            self.model_name = settings.OLLAMA_MODEL

    def get_chat_model(self, temperature: float = 0.7) -> Optional[BaseChatModel]:
        """Get the configured chat model."""
        if not settings.AI_ENABLED:
            logger.warning("AI features are disabled in settings.")
            return None
            
        try:
            if self.provider == "openai":
                if not settings.OPENAI_API_KEY:
                    logger.error("OpenAI API key not found.")
                    return None
                    
                return ChatOpenAI(
                    model=self.model_name,
                    temperature=temperature,
                    api_key=settings.OPENAI_API_KEY
                )
                
            elif self.provider == "anthropic":
                if not settings.ANTHROPIC_API_KEY:
                    logger.error("Anthropic API key not found.")
                    return None
                    
                # return ChatAnthropic(
                #     model=self.model_name,
                #     temperature=temperature,
                #     api_key=settings.ANTHROPIC_API_KEY
                # )
                logger.warning("Anthropic provider not fully implemented yet.")
                return None
                
            elif self.provider == "ollama":
                return ChatOllama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=self.model_name,
                    temperature=temperature
                )
                
            else:
                logger.error(f"Unsupported AI provider: {self.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing AI model: {e}")
            return None


@lru_cache()
def get_ai_config() -> AIConfig:
    """Get cached AI configuration."""
    return AIConfig()
