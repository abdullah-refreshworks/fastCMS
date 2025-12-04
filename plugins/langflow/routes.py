"""
Langflow plugin API routes.

Provides proxy endpoints to Langflow API with FastCMS authentication.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_user
from plugins.langflow.client import LangflowClient
from plugins.langflow.config import LangflowConfig
from plugins.langflow.schemas import FlowExecuteRequest, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_langflow_config() -> LangflowConfig:
    """Get Langflow configuration from environment."""
    return LangflowConfig()


def get_langflow_client(
    config: LangflowConfig = Depends(get_langflow_config),
) -> LangflowClient:
    """Get configured Langflow client."""
    return LangflowClient(
        base_url=config.langflow_url,
        api_key=config.api_key,
        timeout=config.request_timeout,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    client: LangflowClient = Depends(get_langflow_client),
) -> Dict[str, Any]:
    """
    Check Langflow server connection.

    Returns connection status and any error messages.
    """
    return await client.health_check()


@router.get("/flows")
async def list_flows(
    user=Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client),
) -> Dict[str, Any]:
    """
    List all Langflow flows.

    Requires authentication. Returns all flows accessible to the configured API key.
    """
    try:
        return await client.list_flows()
    except Exception as e:
        logger.error(f"Failed to list flows: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to connect to Langflow: {str(e)}")


@router.get("/flows/{flow_id}")
async def get_flow(
    flow_id: str,
    user=Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client),
) -> Dict[str, Any]:
    """
    Get flow details by ID.

    Args:
        flow_id: Langflow flow UUID

    Returns flow configuration and details.
    """
    try:
        return await client.get_flow(flow_id)
    except Exception as e:
        logger.error(f"Failed to get flow {flow_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to get flow: {str(e)}")


@router.post("/flows/{flow_id}/run")
async def run_flow(
    flow_id: str,
    request: FlowExecuteRequest,
    user=Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client),
) -> Dict[str, Any]:
    """
    Execute a Langflow flow.

    Args:
        flow_id: Langflow flow UUID
        request: Execution request with input value and optional tweaks

    Returns flow execution result.
    """
    try:
        return await client.run_flow(flow_id, request.input_value, request.tweaks)
    except Exception as e:
        logger.error(f"Failed to run flow {flow_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to run flow: {str(e)}")


@router.post("/flows/{flow_id}/run/stream")
async def run_flow_stream(
    flow_id: str,
    request: FlowExecuteRequest,
    user=Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client),
) -> StreamingResponse:
    """
    Execute a Langflow flow with streaming response.

    Args:
        flow_id: Langflow flow UUID
        request: Execution request with input value and optional tweaks

    Returns Server-Sent Events stream of flow execution.
    """

    async def generate():
        try:
            async for chunk in client.run_flow_stream(
                flow_id, request.input_value, request.tweaks
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Stream error for flow {flow_id}: {e}")
            yield f'data: {{"error": "{str(e)}"}}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/projects")
async def list_projects(
    user=Depends(get_current_user),
    client: LangflowClient = Depends(get_langflow_client),
) -> Dict[str, Any]:
    """
    List all Langflow projects.

    Returns all projects accessible to the configured API key.
    """
    try:
        return await client.list_projects()
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=502, detail=f"Failed to connect to Langflow: {str(e)}"
        )
