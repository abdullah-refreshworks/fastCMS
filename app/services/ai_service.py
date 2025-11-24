"""
AI Service for content generation and processing.
"""
from typing import Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.ai_config import get_ai_config
from app.core.logging import get_logger
from app.schemas.ai import AIGenerateRequest, AIGenerateResponse

logger = get_logger(__name__)


class AIService:
    """Service for AI-powered content generation."""
    
    def __init__(self):
        self.config = get_ai_config()
    
    async def generate_content(self, request: AIGenerateRequest) -> AIGenerateResponse:
        """
        Generate content based on the request.
        """
        model = self.config.get_chat_model()
        if not model:
            raise ValueError("AI service is not available or configured.")
            
        # Select prompt template based on task
        if request.task == "summarize":
            system_prompt = "You are a helpful content editor. Summarize the following text concisely."
        elif request.task == "seo":
            system_prompt = "You are an SEO expert. Generate a title tag (max 60 chars) and meta description (max 160 chars) for the following content. Return as JSON."
        elif request.task == "expand":
            system_prompt = "You are a creative writer. Expand the following points into a well-written paragraph."
        elif request.task == "tone":
            tone = request.tone or "professional"
            system_prompt = f"You are a professional editor. Rewrite the following text in a {tone} tone."
        else:
            system_prompt = "You are a helpful AI assistant."
            
        # Build prompt
        messages = [
            ("system", system_prompt),
            ("user", request.prompt)
        ]
        
        if request.context:
            messages.insert(1, ("system", f"Context: {request.context}"))
            
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Execute chain
        chain = prompt | model | StrOutputParser()
        
        try:
            result = await chain.ainvoke({})
            return AIGenerateResponse(result=result)
        except Exception as e:
            logger.error(f"AI Generation failed: {e}")
            raise ValueError(f"AI Generation failed: {str(e)}")


# Global instance
ai_service = AIService()
