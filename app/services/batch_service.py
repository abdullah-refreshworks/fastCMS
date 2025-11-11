"""Batch operations service"""
from typing import List, Dict, Any, Optional
import httpx
from app.core.logging import get_logger

logger = get_logger(__name__)


class BatchService:
    """Service for batch API operations"""

    async def execute_batch(
        self,
        requests: List[Dict[str, Any]],
        base_url: str,
        auth_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple API requests in batch

        Args:
            requests: List of request dicts with method, url, body
            base_url: Base URL for requests
            auth_token: Optional auth token

        Returns:
            List of response dicts with status, body
        """
        results = []

        async with httpx.AsyncClient(base_url=base_url) as client:
            for req in requests:
                method = req.get("method", "GET").upper()
                url = req.get("url", "")
                body = req.get("body")
                headers = req.get("headers", {})

                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"

                try:
                    if method == "GET":
                        response = await client.get(url, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, json=body, headers=headers)
                    elif method == "PATCH":
                        response = await client.patch(url, json=body, headers=headers)
                    elif method == "PUT":
                        response = await client.put(url, json=body, headers=headers)
                    elif method == "DELETE":
                        response = await client.delete(url, headers=headers)
                    else:
                        results.append({
                            "status": 400,
                            "error": f"Unsupported method: {method}"
                        })
                        continue

                    results.append({
                        "status": response.status_code,
                        "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    })
                except Exception as e:
                    logger.error(f"Batch request failed: {str(e)}")
                    results.append({
                        "status": 500,
                        "error": str(e)
                    })

        return results
