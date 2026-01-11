"""
PowerHA Copilot API Client.

Thin HTTP client that communicates with the PowerHA Copilot API server.
All business logic runs on the server - this client just sends requests
and displays responses.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
from dataclasses import dataclass

import httpx

from powerha_copilot_cli.config import Config, get_config


@dataclass
class APIError(Exception):
    """API error with status code and message."""
    status_code: int
    message: str
    details: Optional[Dict[str, Any]] = None


class PowerHACopilotClient:
    """
    Async HTTP client for PowerHA Copilot API.

    Usage:
        async with PowerHACopilotClient() as client:
            response = await client.chat("Check cluster health")
            clusters = await client.list_clusters()
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the client."""
        self.config = config or get_config()
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "PowerHACopilotClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=self._get_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"powerha-copilot-cli/{self.config.api_version}",
        }

        api_key = self.config.get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an API request."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        try:
            response = await self._client.request(method, endpoint, **kwargs)

            if response.status_code == 401:
                raise APIError(401, "Authentication required. Run 'powerha-copilot login' first.")

            if response.status_code == 403:
                raise APIError(403, "Access denied. Check your permissions.")

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    response.status_code,
                    error_data.get("message", f"Request failed: {response.status_code}"),
                    error_data.get("details"),
                )

            return response.json() if response.content else {}

        except httpx.ConnectError:
            raise APIError(0, f"Cannot connect to {self.config.api_url}. Is the server running?")
        except httpx.TimeoutException:
            raise APIError(0, "Request timed out. Try again or increase timeout.")

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the API server.

        Returns:
            Dict with api_key and user info
        """
        response = await self._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
        )

        # Store credentials
        if "api_key" in response:
            self.config.set_api_key(response["api_key"])
        if "refresh_token" in response:
            self.config.set_refresh_token(response["refresh_token"])
        if "user" in response:
            self.config.username = response["user"].get("username")
            self.config.organization = response["user"].get("organization")
            self.config.save()

        return response

    async def login_with_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Authenticate using an API key directly.

        Returns:
            Dict with user info
        """
        # Temporarily set the key to make the request
        self.config.set_api_key(api_key)

        # Update client headers
        if self._client:
            self._client.headers.update(self._get_headers())

        # Verify the key
        response = await self._request("GET", "/auth/me")

        if "user" in response:
            self.config.username = response["user"].get("username")
            self.config.organization = response["user"].get("organization")
            self.config.save()

        return response

    async def logout(self) -> None:
        """Log out and clear credentials."""
        try:
            await self._request("POST", "/auth/logout")
        except APIError:
            pass  # Ignore errors during logout

        self.config.clear_credentials()

    async def whoami(self) -> Dict[str, Any]:
        """Get current user info."""
        return await self._request("GET", "/auth/me")

    # -------------------------------------------------------------------------
    # Chat / Conversation
    # -------------------------------------------------------------------------

    async def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a chat message to the copilot.

        Args:
            message: User message
            conversation_id: Optional conversation ID for context

        Returns:
            Response with assistant message and any actions taken
        """
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        return await self._request("POST", "/chat", json=payload)

    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Send a chat message and stream the response.

        Yields:
            Response chunks as they arrive
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        payload = {"message": message, "stream": True}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with self._client.stream("POST", "/chat", json=payload) as response:
            if response.status_code != 200:
                raise APIError(response.status_code, "Stream request failed")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    # -------------------------------------------------------------------------
    # Cluster Operations
    # -------------------------------------------------------------------------

    async def list_clusters(self) -> List[Dict[str, Any]]:
        """List all accessible PowerHA clusters."""
        response = await self._request("GET", "/clusters")
        return response.get("clusters", [])

    async def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Get detailed information about a cluster."""
        return await self._request("GET", f"/clusters/{cluster_id}")

    async def get_cluster_status(self, cluster_id: str) -> Dict[str, Any]:
        """Get current status of a cluster."""
        return await self._request("GET", f"/clusters/{cluster_id}/status")

    async def get_cluster_health(self, cluster_id: str) -> Dict[str, Any]:
        """Get health check results for a cluster."""
        return await self._request("GET", f"/clusters/{cluster_id}/health")

    async def get_cluster_nodes(self, cluster_id: str) -> List[Dict[str, Any]]:
        """Get nodes in a cluster."""
        response = await self._request("GET", f"/clusters/{cluster_id}/nodes")
        return response.get("nodes", [])

    async def get_resource_groups(self, cluster_id: str) -> List[Dict[str, Any]]:
        """Get resource groups in a cluster."""
        response = await self._request("GET", f"/clusters/{cluster_id}/resource-groups")
        return response.get("resource_groups", [])

    # -------------------------------------------------------------------------
    # Operations / Actions
    # -------------------------------------------------------------------------

    async def perform_failover(
        self,
        cluster_id: str,
        target_node: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Initiate a failover operation.

        Args:
            cluster_id: Cluster identifier
            target_node: Optional target node
            force: Force failover even if risky

        Returns:
            Operation result
        """
        payload = {"force": force}
        if target_node:
            payload["target_node"] = target_node

        return await self._request(
            "POST",
            f"/clusters/{cluster_id}/failover",
            json=payload,
        )

    async def manage_resource_group(
        self,
        cluster_id: str,
        resource_group: str,
        action: str,
    ) -> Dict[str, Any]:
        """
        Manage a resource group.

        Args:
            cluster_id: Cluster identifier
            resource_group: Resource group name
            action: Action (start, stop, move)

        Returns:
            Operation result
        """
        return await self._request(
            "POST",
            f"/clusters/{cluster_id}/resource-groups/{resource_group}/{action}",
        )

    # -------------------------------------------------------------------------
    # History / Audit
    # -------------------------------------------------------------------------

    async def get_conversation_history(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get conversation history."""
        response = await self._request(
            "GET",
            "/conversations",
            params={"limit": limit, "offset": offset},
        )
        return response.get("conversations", [])

    async def get_operation_history(
        self,
        cluster_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get operation history."""
        params = {"limit": limit}
        if cluster_id:
            params["cluster_id"] = cluster_id

        response = await self._request("GET", "/operations", params=params)
        return response.get("operations", [])

    # -------------------------------------------------------------------------
    # Server Info
    # -------------------------------------------------------------------------

    async def health_check(self) -> Dict[str, Any]:
        """Check API server health."""
        return await self._request("GET", "/health")

    async def get_version(self) -> Dict[str, Any]:
        """Get API server version."""
        return await self._request("GET", "/version")


# Synchronous wrapper for simple CLI usage
def sync_client() -> PowerHACopilotClient:
    """Create a synchronous client wrapper."""
    return PowerHACopilotClient()


def run_async(coro):
    """Run an async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)
