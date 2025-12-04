"""
Langflow HTTP client for API communication.
"""

import logging
from typing import Any, AsyncIterator, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class LangflowClient:
    """HTTP client for Langflow API."""

    def __init__(self, base_url: str, api_key: str = "", timeout: int = 300):
        """
        Initialize Langflow client.

        Args:
            base_url: Langflow server URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional API key."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Langflow server health.

        Returns:
            Dict with status and optional error message
        """
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health", headers=self._get_headers()
                )
                if response.status_code == 200:
                    return {"status": "connected", "langflow_url": self.base_url}
                return {
                    "status": "disconnected",
                    "error": f"Unexpected status code: {response.status_code}",
                }
            except httpx.TimeoutException:
                return {"status": "disconnected", "error": "Connection timeout"}
            except httpx.ConnectError:
                return {"status": "disconnected", "error": "Connection refused"}
            except Exception as e:
                logger.error(f"Langflow health check failed: {e}")
                return {"status": "disconnected", "error": str(e)}

    async def list_flows(self) -> Dict[str, Any]:
        """
        List all flows from Langflow.

        Returns:
            Dict containing flows list
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/flows", headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                # Normalize response
                if isinstance(data, list):
                    return {"flows": data, "total": len(data)}
                return data
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to list flows: {e}")
                raise
            except Exception as e:
                logger.error(f"Error listing flows: {e}")
                raise

    async def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Get flow details by ID.

        Args:
            flow_id: Flow UUID

        Returns:
            Flow details dict
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/flows/{flow_id}",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to get flow {flow_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error getting flow {flow_id}: {e}")
                raise

    async def run_flow(
        self,
        flow_id: str,
        input_value: str,
        tweaks: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a flow.

        Args:
            flow_id: Flow UUID
            input_value: Input value for the flow
            tweaks: Optional component tweaks

        Returns:
            Execution result
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload: Dict[str, Any] = {"input_value": input_value}
                if tweaks:
                    payload["tweaks"] = tweaks

                response = await client.post(
                    f"{self.base_url}/api/v1/run/{flow_id}",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to run flow {flow_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error running flow {flow_id}: {e}")
                raise

    async def run_flow_stream(
        self,
        flow_id: str,
        input_value: str,
        tweaks: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Execute a flow with streaming response.

        Args:
            flow_id: Flow UUID
            input_value: Input value for the flow
            tweaks: Optional component tweaks

        Yields:
            Streaming response lines
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload: Dict[str, Any] = {"input_value": input_value}
                if tweaks:
                    payload["tweaks"] = tweaks

                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/v1/run/{flow_id}?stream=true",
                    headers=self._get_headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            yield line
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to stream flow {flow_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error streaming flow {flow_id}: {e}")
                raise

    async def list_projects(self) -> Dict[str, Any]:
        """
        List all projects from Langflow.

        Returns:
            Dict containing projects list
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/projects", headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to list projects: {e}")
                raise
            except Exception as e:
                logger.error(f"Error listing projects: {e}")
                raise
