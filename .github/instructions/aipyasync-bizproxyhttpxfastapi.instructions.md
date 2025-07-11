# Business Proxy: HTTPX + FastAPI Concrete Implementation

You are implementing the Business Proxy layer that abstracts network communication.

---

## Requirements:

- Use httpx.AsyncClient for outbound async HTTP calls  
- Use FastAPI for inbound server async HTTP endpoints  
- Support async context management for connection lifecycle  
- Support message tagging (optional) for rate-limiting/throttling hooks  
- Raise meaningful exceptions for connection failures, retries exhausted, and signature errors  
- Support extensibility for retry and throttling plugins  
- Keep business logic clean: no direct HTTPX/FastAPI calls outside proxy  
- Follow all async core and error handling locked instructions

---

## Code:

~~~python
import asyncio
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse

from typing import Protocol, Callable


class BusinessProxyException(Exception):
    """Base exception for business proxy errors."""


class ConnectionFailure(BusinessProxyException):
    pass


class RetriesExhausted(BusinessProxyException):
    pass


class SignatureFailure(BusinessProxyException):
    pass


class BusinessProxyInterface(Protocol):
    """Interface for the business proxy layer."""

    async def connect(self) -> None:
        ...

    async def disconnect(self) -> None:
        ...

    async def send(self, message: Dict[str, Any], tag: Optional[str] = None) -> None:
        ...

    async def receive(self) -> AsyncIterator[Dict[str, Any]]:
        ...

    def is_connected(self) -> bool:
        ...


class HTTPXFastAPIProxy(BusinessProxyInterface):
    """Concrete implementation of Business Proxy using HTTPX and FastAPI."""

    def __init__(
        self,
        base_url: str,
        retry_policy: Optional[Callable[[Exception, int], bool]] = None,
        throttler: Optional[Callable[[Optional[str]], bool]] = None,
    ):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._retry_policy = retry_policy
        self._throttler = throttler
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._stop_receive = False
        self._receive_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        if self._connected:
            return
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        self._connected = True
        self._stop_receive = False
        # Start background receive task
        self._receive_task = asyncio.create_task(self._background_receive())

    async def disconnect(self) -> None:
        if not self._connected or self._client is None:
            return
        self._stop_receive = True
        if self._receive_task:
            await self._receive_task
        await self._client.aclose()
        self._client = None
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def send(self, message: Dict[str, Any], tag: Optional[str] = None) -> None:
        if not self._connected or self._client is None:
            raise ConnectionFailure("Not connected")

        # Check throttling if applicable
        if self._throttler and not self._throttler(tag):
            # Backoff silently or raise based on policy; here we silently wait
            await asyncio.sleep(1)
            # Alternatively, raise or loop until allowed
            # raise RetriesExhausted("Throttled: too many messages")

        retry_count = 0
        while True:
            try:
                response = await self._client.post("/send", json=message)
                response.raise_for_status()
                return
            except httpx.HTTPStatusError as e:
                # Handle signature failures or auth failures explicitly
                if e.response.status_code == 401:
                    raise SignatureFailure("Signature or auth failure") from e
                else:
                    raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                retry_count += 1
                if self._retry_policy and not self._retry_policy(e, retry_count):
                    raise RetriesExhausted(f"Retries exhausted after {retry_count} attempts") from e
                await asyncio.sleep(min(2 ** retry_count, 10))

    async def receive(self) -> AsyncIterator[Dict[str, Any]]:
        """Async generator yielding received messages."""
        while self._connected and not self._stop_receive:
            try:
                message = await self._receive_queue.get()
                yield message
            except asyncio.CancelledError:
                break

    async def _background_receive(self) -> None:
        """Background task to poll or wait for incoming messages."""
        # This is an example; replace with actual listening/polling logic.
        while self._connected and not self._stop_receive:
            try:
                # Poll server for messages or use long-polling / websocket in real impl.
                # For demo, simulate incoming message
                await asyncio.sleep(2)
                dummy_msg = {"message": "ping"}
                await self._receive_queue.put(dummy_msg)
            except asyncio.CancelledError:
                break


# FastAPI server setup for inbound messages

app = FastAPI()

proxy_instance: Optional[HTTPXFastAPIProxy] = None  # Should be set externally


@app.post("/send")
async def inbound_send(request: Request) -> Response:
    """
    Endpoint for receiving messages from the business layer or clients.
    In real use, forward to message handlers or queues.
    """
    global proxy_instance
    if proxy_instance is None or not proxy_instance.is_connected():
        raise HTTPException(status_code=503, detail="Proxy not connected")
    message = await request.json()
    # Here, process or forward message to business logic
    # For example, enqueue to proxy receive queue:
    await proxy_instance._receive_queue.put(message)
    return JSONResponse(content={"status": "ok"})

~~~