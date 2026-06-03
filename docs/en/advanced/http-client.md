# HTTP Client

ErisPulse provides a unified HTTP client. Modules and adapters should prioritize using this client for sending HTTP requests rather than importing third-party libraries like `aiohttp` / `httpx` themselves.

## Overview

Main features of the HTTP client:

- **Unified Interface**: Provides `get` / `post` / `put` / `delete` / `patch` / `request` methods
- **Auto Logging**: Automatically logs all requests and statistics
- **Lifecycle Integration**: Triggers `client.request` lifecycle events for every request
- **Retry Support**: Configurable automatic retry counts and intervals
- **Timeout Control**: Independent connection and request timeouts
- **Connection Pool Reuse**: Connection pool management based on `aiohttp.ClientSession`

## Quick Start

```python
from ErisPulse.Core import client

# GET Request
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST Request
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

## HttpResponse

All request methods return an `HttpResponse` object:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP status code (e.g., 200, 404)
resp.reason       # str | None - Status description (e.g., "OK")
resp.headers      # Response headers (case-insensitive)
resp.content_type # str | None - Content-Type
resp.url          # Final URL (may change due to redirects)
resp.raw          # Underlying native response object (currently `aiohttp.ClientResponse`)

# Read response body
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # Parse JSON
text = await resp.text("gbk")  # Specify encoding
```

## Request Methods

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON request body
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# Form request body
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# Raw data
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Generic request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## Parameters

### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Request URL |
| `params` | `dict[str, str]` | Query parameters (optional) |
| `headers` | `dict[str, str]` | Additional request headers (optional) |
| `data` | `Any` | Request body (form or raw data) (optional) |
| `json` | `Any` | JSON request body (optional) |
| `timeout` | `float` | Timeout for this specific request (seconds) (optional, overrides default) |
| `max_retries` | `int` | Maximum retry attempts for this specific request (optional, overrides default) |

## Timeout and Retry

```python
from ErisPulse.Core import HttpClient

# Create a client with custom timeouts
client = HttpClient(
    timeout=60,           # Total request timeout 60s
    connect_timeout=5,    # Connection timeout 5s
    max_retries=3,        # Auto retry 3 times on failure
    retry_delay=2,        # Retry interval 2s
)

# Override timeout for a single request
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

## Custom Default Headers

```python
client = HttpClient(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## Request Statistics

```python
from ErisPulse.Core import client

# View statistics
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Reset statistics
client.reset_stats()
```

## Lifecycle Events

Triggers the `client.request` event after each request is completed, useful for monitoring:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## Context Management

```python
# Use as a context manager to automatically close sessions
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## Using in Adapters

Adapters can use the global client or create their own client instance to send platform API requests:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return await resp.json()
```

> You can also use `sdk.client` via `from ErisPulse import sdk` for the same effect.

## Best Practices

1. **Prioritize the global client**: Use `from ErisPulse.Core import client` to get the global singleton, facilitating unified framework management and monitoring
2. **Avoid directly importing aiohttp**: Use `client` instead of `aiohttp.ClientSession` so future changes to the underlying implementation require no code modifications
3. **Set timeouts reasonably**: Set reasonable timeout durations based on API response speeds to avoid long-term blocking
4. **Use the retry mechanism**: Enable retries for unstable APIs to improve reliability
5. **Monitor request statistics**: Monitor request status via `sdk.client.stats` or `client.request` lifecycle events

## Related Documentation

- [Router Manager](router.md) - HTTP/WebSocket server routing
- [Adapter Development Guide](../developer-guide/adapters/getting-started.md) - Using the HTTP client in adapters
- [Lifecycle Management](lifecycle.md) - Listening to request events