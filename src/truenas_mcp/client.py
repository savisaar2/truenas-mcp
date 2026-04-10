import json
import asyncio
import uuid
import websockets
from typing import Any, Dict, Optional, List

class TrueNASClient:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._requests: Dict[str, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Establish connection and authenticate."""
        self.ws = await websockets.connect(self.url)
        
        # 1. Send connect message
        await self.send({
            "msg": "connect",
            "version": "1",
            "support": ["1"]
        })

        # Start listening
        self._receive_task = asyncio.create_task(self._listen())

        # Wait for connected message
        # In a real implementation, we should wait for the "connected" msg.
        # For simplicity in this tool-based env, we'll assume it succeeds or wait briefly.
        
        # 2. Authenticate
        auth_id = str(uuid.uuid4())
        response = await self.call("auth.login_with_api_key", [self.api_key], request_id=auth_id)
        
        if not response or response.get("error"):
            error_msg = response.get("error", {}).get("reason", "Unknown error") if response else "No response"
            raise ConnectionError(f"Authentication failed: {error_msg}")

    async def _listen(self):
        """Listen for incoming messages and resolve futures."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_id = data.get("id")
                if msg_id and msg_id in self._requests:
                    self._requests[msg_id].set_result(data)
                    del self._requests[msg_id]
        except Exception as e:
            # Propagate error to all pending requests
            for fut in self._requests.values():
                if not fut.done():
                    fut.set_exception(e)
            self._requests.clear()

    async def send(self, data: Dict[str, Any]):
        """Send a message to the WebSocket."""
        if self.ws:
            await self.ws.send(json.dumps(data))

    async def call(self, method: str, params: List[Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Call a TrueNAS middleware method."""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        future = asyncio.get_running_loop().create_future()
        self._requests[request_id] = future
        
        await self.send({
            "id": request_id,
            "msg": "method",
            "method": method,
            "params": params
        })
        
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            del self._requests[request_id]
            raise TimeoutError(f"Request {request_id} timed out")

    async def close(self):
        """Close the connection."""
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws:
            await self.ws.close()
