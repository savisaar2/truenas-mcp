import json
import asyncio
import uuid
import websockets
import ssl
import sys
from typing import Any, Dict, Optional, List

class TrueNASClient:
    def __init__(self, url: str, api_key: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        self.url = url
        self.api_key = api_key
        self.username = username
        self.password = password
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._requests: Dict[str, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._connected_event = asyncio.Event()

    async def connect(self):
        """Establish connection using strict DDP handshake and Auth."""
        connect_kwargs = {}
        if self.url.startswith("wss://"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_kwargs["ssl"] = ssl_context

        print(f">>> Connecting to {self.url}", file=sys.stderr)
        self.ws = await websockets.connect(self.url, **connect_kwargs)
        self._receive_task = asyncio.create_task(self._listen())

        # 1. DDP Connect
        await self.send({"msg": "connect", "version": "1", "support": ["1"]})
        try:
            await asyncio.wait_for(self._connected_event.wait(), timeout=10.0)
            print("<<< DDP Connected", file=sys.stderr)
        except asyncio.TimeoutError:
            raise ConnectionError("Timeout waiting for DDP 'connected'")

        # 2. Authenticate
        auth_id = "auth_login"
        if self.username and self.password:
            print(f">>> Sending Auth (User: {self.username})", file=sys.stderr)
            response = await self.call("auth.login", [self.username, self.password], request_id=auth_id)
        else:
            print(">>> Sending Auth (API Key)", file=sys.stderr)
            response = await self.call("auth.login_with_api_key", [self.api_key], request_id=auth_id)
        
        if not response or response.get("error") or response.get("result") is not True:
            error = response.get("error", {})
            print(f"!!! Auth Failed: {error}", file=sys.stderr)
            reason = error.get('reason', 'Invalid credentials or API key')
            raise ConnectionError(f"Auth failed: {reason}")
        print("<<< Auth Successful", file=sys.stderr)

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("msg")
                
                if msg_type == "connected":
                    self._connected_event.set()
                elif msg_type == "ping":
                    await self.send({"msg": "pong"})
                elif msg_type in ["result", "error"]:
                    msg_id = data.get("id")
                    if msg_id in self._requests:
                        self._requests[msg_id].set_result(data)
                        del self._requests[msg_id]
        except Exception as e:
            print(f"WS Listener error: {e}", file=sys.stderr)

    async def send(self, data: Dict[str, Any]):
        if self.ws:
            await self.ws.send(json.dumps(data))

    async def call(self, method: str, params: List[Any], request_id: Optional[str] = None) -> Dict[str, Any]:
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
        return await asyncio.wait_for(future, timeout=30.0)

    async def close(self):
        if self._receive_task: self._receive_task.cancel()
        if self.ws: await self.ws.close()
