"""
Langflow plugin request/response schemas.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FlowExecuteRequest(BaseModel):
    """Request to execute a Langflow flow."""

    input_value: str = Field(..., description="Input value for the flow")
    tweaks: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional tweaks to apply to flow components"
    )


class FlowExecuteResponse(BaseModel):
    """Response from flow execution."""

    outputs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Flow execution outputs"
    )
    session_id: Optional[str] = Field(default=None, description="Session ID for the execution")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Connection status: connected or disconnected")
    langflow_url: Optional[str] = Field(default=None, description="Langflow server URL")
    error: Optional[str] = Field(default=None, description="Error message if disconnected")


class FlowInfo(BaseModel):
    """Basic flow information."""

    id: str = Field(..., description="Flow ID")
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(default=None, description="Flow description")


class FlowListResponse(BaseModel):
    """Response containing list of flows."""

    flows: List[FlowInfo] = Field(default_factory=list, description="List of flows")
    total: int = Field(default=0, description="Total number of flows")
