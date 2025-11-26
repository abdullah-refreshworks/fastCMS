"""
AI Service for content generation and processing.
"""
from typing import Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

from app.core.ai_config import get_ai_config
from app.core.logging import get_logger
from app.schemas.ai import (
    AIGenerateRequest, AIGenerateResponse,
    AITaggingRequest, AITaggingResponse,
    AIExtractionRequest, AIExtractionResponse
)

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

    async def generate_tags(self, request: AITaggingRequest) -> AITaggingResponse:
        """
        Generate tags for content.
        """
        model = self.config.get_chat_model()
        if not model:
            raise ValueError("AI service is not available.")

        system_prompt = "You are a content categorization expert. Analyze the following text and generate a list of relevant tags."
        
        if request.existing_tags:
            system_prompt += f"\nChoose from these existing tags if applicable, or generate new ones if necessary: {', '.join(request.existing_tags)}"
            
        system_prompt += f"\nReturn ONLY a JSON array of strings, max {request.max_tags} tags. Example: [\"tag1\", \"tag2\"]"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", request.content)
        ])

        chain = prompt | model | JsonOutputParser()
        
        try:
            result = await chain.ainvoke({})
            # Ensure result is a list of strings
            if isinstance(result, dict) and "tags" in result:
                tags = result["tags"]
            elif isinstance(result, list):
                tags = result
            else:
                tags = []
            return AITaggingResponse(tags=tags[:request.max_tags])
        except Exception as e:
            logger.error(f"AI Tagging failed: {e}")
            raise ValueError(f"AI Tagging failed: {str(e)}")

    async def extract_content(self, request: AIExtractionRequest) -> AIExtractionResponse:
        """
        Extract structured data from unstructured text.
        """
        model = self.config.get_chat_model()
        if not model:
            raise ValueError("AI service is not available.")

        schema_str = "\n".join([f"- {k}: {v}" for k, v in request.schema_description.items()])
        system_prompt = f"""You are a data extraction specialist. Extract the following fields from the text:
{schema_str}

Return the result as a valid JSON object matching these fields. If a field cannot be found, use null."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", request.text)
        ])

        chain = prompt | model | JsonOutputParser()
        
        try:
            result = await chain.ainvoke({})
            return AIExtractionResponse(data=result)
        except Exception as e:
            logger.error(f"AI Extraction failed: {e}")
            raise ValueError(f"AI Extraction failed: {str(e)}")


# Global instance
ai_service = AIService()
