"""AI service for LangChain integration and intelligent features."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIService:
    """Service for AI-powered features using LangChain."""

    def __init__(self) -> None:
        """Initialize AI service with configured LLM."""
        self.llm = self._get_llm()

    def _get_llm(self) -> Any:
        """Get LLM based on AI provider configuration."""
        if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                openai_api_key=settings.OPENAI_API_KEY,
                streaming=True,
            )
        elif settings.AI_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                streaming=True,
            )
        elif settings.AI_PROVIDER == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.7,
            )
        else:
            raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")

    async def generate_content(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate content based on prompt and optional context.

        Args:
            prompt: The generation prompt
            context: Optional context data
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text content
        """
        messages = [
            SystemMessage(
                content="You are a helpful AI assistant for a headless CMS. "
                "Generate clear, concise, and accurate content based on the user's request."
            )
        ]

        if context:
            context_str = json.dumps(context, indent=2)
            messages.append(
                SystemMessage(content=f"Context data:\n{context_str}")
            )

        messages.append(HumanMessage(content=prompt))

        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise

    async def generate_content_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream generated content token by token.

        Args:
            prompt: The generation prompt
            context: Optional context data

        Yields:
            Text chunks as they are generated
        """
        messages = [
            SystemMessage(
                content="You are a helpful AI assistant for a headless CMS."
            )
        ]

        if context:
            context_str = json.dumps(context, indent=2)
            messages.append(
                SystemMessage(content=f"Context data:\n{context_str}")
            )

        messages.append(HumanMessage(content=prompt))

        try:
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Content streaming failed: {str(e)}")
            raise

    async def natural_language_to_filter(
        self, query: str, collection_schema: Dict[str, Any]
    ) -> Optional[str]:
        """
        Convert natural language query to API filter syntax.

        Args:
            query: Natural language query
            collection_schema: Schema of the collection being queried

        Returns:
            Filter string in FastCMS syntax or None
        """
        # Build schema description
        fields = collection_schema.get("fields", [])
        field_descriptions = []
        for field in fields:
            field_type = field.get("type", "text")
            field_name = field.get("name", "")
            field_descriptions.append(f"- {field_name} ({field_type})")

        schema_str = "\n".join(field_descriptions)

        prompt = f"""Convert the following natural language query into a FastCMS filter expression.

Collection Schema:
{schema_str}

Filter Syntax:
- Use operators: =, !=, >, <, >=, <=, ~ (contains)
- Combine with && for AND conditions
- Examples:
  * "age>=18&&status=active"
  * "email~gmail.com"
  * "price<100"

Natural Language Query: {query}

Return ONLY the filter expression, no explanation. If the query cannot be converted to a filter, return "null".

Filter Expression:"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            filter_expr = response.content.strip()

            # Validate it's not an explanation
            if len(filter_expr) > 200 or "\n" in filter_expr:
                return None

            if filter_expr.lower() == "null":
                return None

            return filter_expr
        except Exception as e:
            logger.error(f"NL to filter conversion failed: {str(e)}")
            return None

    async def enrich_data(
        self, data: Dict[str, Any], instructions: str
    ) -> Dict[str, Any]:
        """
        Enrich or validate data using AI.

        Args:
            data: Data to enrich
            instructions: Instructions for enrichment

        Returns:
            Enriched data
        """
        data_str = json.dumps(data, indent=2)

        prompt = f"""Given the following data and instructions, enrich or validate the data as requested.

Data:
{data_str}

Instructions: {instructions}

Return the enriched data as valid JSON. Keep the original structure but add or modify fields as instructed.

Enriched Data:"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            enriched = json.loads(content)
            return enriched
        except Exception as e:
            logger.error(f"Data enrichment failed: {str(e)}")
            return data

    async def generate_schema_suggestion(
        self, description: str
    ) -> List[Dict[str, Any]]:
        """
        Generate collection schema based on natural language description.

        Args:
            description: Description of the collection to create

        Returns:
            List of field definitions
        """
        prompt = f"""Generate a FastCMS collection schema based on this description: {description}

Available field types:
- text: Short text (< 255 chars)
- editor: Long text/HTML content
- number: Numeric values
- bool: Boolean true/false
- email: Email address
- url: URL
- date: ISO date string
- select: Dropdown with predefined values
- relation: Reference to another collection
- file: File upload
- json: JSON data

Return a JSON array of field objects with this structure:
[
  {{
    "name": "field_name",
    "type": "field_type",
    "validation": {{
      "required": true/false,
      "min": number (for numbers),
      "max": number (for numbers),
      "values": ["option1", "option2"] (for select)
    }}
  }}
]

Return ONLY the JSON array, no explanation.

Schema:"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            schema = json.loads(content)

            if isinstance(schema, list):
                return schema
            return []
        except Exception as e:
            logger.error(f"Schema generation failed: {str(e)}")
            return []

    async def chat(
        self, message: str, history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        General purpose chat with conversation history.

        Args:
            message: User message
            history: Previous conversation messages

        Returns:
            AI response
        """
        messages = [
            SystemMessage(
                content="You are a helpful AI assistant for FastCMS, "
                "a headless CMS platform. Help users with API usage, "
                "data modeling, and content management."
            )
        ]

        # Add conversation history
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant" and content:
                    from langchain_core.messages import AIMessage

                    messages.append(AIMessage(content=content))

        # Add current message
        messages.append(HumanMessage(content=message))

        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            raise
