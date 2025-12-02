"""
AI Data Agent using LangGraph.
"""
from typing import Dict, Any, TypedDict, Annotated, List
import operator

from langchain_community.utilities import SQLDatabase
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from app.core.ai_config import get_ai_config
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State for the agent workflow."""
    query: str
    sql_query: str
    sql_result: str
    answer: str
    error: str
    messages: Annotated[List[BaseMessage], operator.add]


class AIAgentService:
    """Service for AI Data Agent."""
    
    def __init__(self):
        self.config = get_ai_config()
        # Use sync connection string for SQLDatabase
        # Convert async sqlite url to sync: sqlite+aiosqlite:///... -> sqlite:///...
        db_url = settings.DATABASE_URL.replace("+aiosqlite", "")
        self.db = SQLDatabase.from_uri(db_url)
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_sql", self._execute_sql)
        workflow.add_node("synthesize_answer", self._synthesize_answer)
        
        # Add edges
        workflow.set_entry_point("generate_sql")
        
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "synthesize_answer")
        workflow.add_edge("synthesize_answer", END)
        
        return workflow.compile()
        
    async def _generate_sql(self, state: AgentState) -> Dict[str, Any]:
        """Generate SQL query from natural language."""
        query = state["query"]
        schema = self.db.get_table_info()
        
        model = self.config.get_chat_model(temperature=0)
        if not model:
            raise ValueError("AI model not available")
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SQL expert. Generate a SQL query to answer the user's question.
            
            Database Schema:
            {schema}
            
            Rules:
            1. Return ONLY the SQL query. No markdown, no explanation.
            2. Use SQLite syntax.
            3. Read-only queries only (SELECT).
            4. Limit results to 10 unless specified otherwise.
            """),
            ("user", "{query}")
        ])
        
        chain = prompt | model | StrOutputParser()
        sql_query = await chain.ainvoke({"schema": schema, "query": query})
        
        # Clean up SQL
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        return {"sql_query": sql_query}
        
    async def _execute_sql(self, state: AgentState) -> Dict[str, Any]:
        """Execute the generated SQL query."""
        sql_query = state["sql_query"]
        
        try:
            # Basic safety check
            if not sql_query.lower().startswith("select"):
                raise ValueError("Only SELECT queries are allowed.")
                
            result = self.db.run(sql_query)
            return {"sql_result": str(result)}
        except Exception as e:
            return {"sql_result": f"Error: {str(e)}", "error": str(e)}
            
    async def _synthesize_answer(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize natural language answer from SQL results."""
        query = state["query"]
        sql_query = state["sql_query"]
        sql_result = state["sql_result"]
        
        model = self.config.get_chat_model()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data analyst. Answer the user's question based on the database query results.
            
            User Question: {query}
            SQL Query: {sql_query}
            SQL Result: {sql_result}
            
            Provide a clear, concise answer. If the result is empty, say so.
            """),
            ("user", "What is the answer?")
        ])
        
        chain = prompt | model | StrOutputParser()
        answer = await chain.ainvoke({
            "query": query,
            "sql_query": sql_query,
            "sql_result": sql_result
        })
        
        return {"answer": answer}
        
    async def query(self, user_query: str) -> Dict[str, Any]:
        """Run the agent workflow."""
        initial_state = {"query": user_query, "messages": []}
        
        result = await self.workflow.ainvoke(initial_state)
        
        return {
            "answer": result["answer"],
            "sql_query": result.get("sql_query"),
            "data": None,  # Could parse sql_result back to json if needed
            "error": result.get("error")
        }


# Global instance
ai_agent_service = AIAgentService()
