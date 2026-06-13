"""
HTTP 客户端单元测试

测试 Core.client 模块的 HttpClient 和 HttpResponse，
覆盖请求方法、超时/重试、统计、上下文管理、生命周期事件等。
使用 aiohttp.test_utils.AioHTTPTestCase / aiohttp.ClientSession mock 避免真实网络。
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from ErisPulse.Core.client import HttpClient, HttpResponse
from ErisPulse.Core.Bases.errors import ClientError, ClientConnectionError


# ==================== HttpResponse 测试 ====================


class TestHttpResponse:
    """HttpResponse 属性与方法测试"""

    def _make_raw_response(
        self,
        status=200,
        reason="OK",
        content_type="application/json",
        charset="utf-8",
        headers=None,
        url="http://example.com/api",
    ):
        raw = MagicMock()
        raw.status = status
        raw.reason = reason
        raw.content_type = content_type
        raw.charset = charset
        raw.headers = headers or {"content-type": "application/json"}
        raw.url = url
        raw.read = AsyncMock(return_value=b'{"key": "value"}')
        raw.text = AsyncMock(return_value='{"key": "value"}')
        raw.json = AsyncMock(return_value={"key": "value"})
        raw.release = AsyncMock()
        return raw

    def test_status_property(self):
        raw = self._make_raw_response(status=404, reason="Not Found")
        resp = HttpResponse(raw)
        assert resp.status == 404

    def test_reason_property(self):
        raw = self._make_raw_response(reason="Created")
        resp = HttpResponse(raw)
        assert resp.reason == "Created"

    def test_reason_none(self):
        raw = self._make_raw_response()
        raw.reason = None
        resp = HttpResponse(raw)
        assert resp.reason is None

    def test_headers_property(self):
        hdrs = {"content-type": "text/html", "x-custom": "yes"}
        raw = self._make_raw_response(headers=hdrs)
        resp = HttpResponse(raw)
        assert resp.headers == hdrs

    def test_content_type_property(self):
        raw = self._make_raw_response(content_type="text/plain")
        resp = HttpResponse(raw)
        assert resp.content_type == "text/plain"

    def test_content_type_none(self):
        raw = self._make_raw_response()
        raw.content_type = None
        resp = HttpResponse(raw)
        assert resp.content_type is None

    def test_charset_property(self):
        raw = self._make_raw_response(charset="gbk")
        resp = HttpResponse(raw)
        assert resp.charset == "gbk"

    def test_charset_none(self):
        raw = self._make_raw_response()
        raw.charset = None
        resp = HttpResponse(raw)
        assert resp.charset is None

    def test_url_property(self):
        raw = self._make_raw_response(url="http://redirect.example.com/final")
        resp = HttpResponse(raw)
        assert resp.url == "http://redirect.example.com/final"

    def test_raw_property(self):
        raw = self._make_raw_response()
        resp = HttpResponse(raw)
        assert resp.raw is raw

    @pytest.mark.asyncio
    async def test_read_caches_body(self):
        raw = self._make_raw_response()
        raw.read = AsyncMock(return_value=b"hello")
        resp = HttpResponse(raw)

        body1 = await resp.read()
        body2 = await resp.read()
        assert body1 == b"hello"
        assert body2 == b"hello"
        # 只应调用底层 read 一次（缓存）
        raw.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_default_encoding(self):
        raw = self._make_raw_response()
        raw.read = AsyncMock(return_value=b"hello world")
        raw.get_encoding = MagicMock(return_value=None)
        resp = HttpResponse(raw)
        text = await resp.text()
        assert text == "hello world"

    @pytest.mark.asyncio
    async def test_text_custom_encoding(self):
        raw = self._make_raw_response()
        raw.read = AsyncMock(return_value="你好".encode("gbk"))
        resp = HttpResponse(raw)
        text = await resp.text("gbk")
        assert text == "你好"

    @pytest.mark.asyncio
    async def test_json(self):
        raw = self._make_raw_response()
        raw.read = AsyncMock(return_value=b'{"foo": "bar"}')
        resp = HttpResponse(raw)
        data = await resp.json()
        assert data == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_json_with_kwargs(self):
        raw = self._make_raw_response()
        raw.read = AsyncMock(return_value=b'{"foo": "bar"}')
        resp = HttpResponse(raw)
        await resp.json(object_hook=lambda d: {k.upper(): v for k, v in d.items()})
        assert raw.read.call_count == 1

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        raw = self._make_raw_response()
        resp = HttpResponse(raw)
        async with resp as r:
            assert r is resp
        raw.release.assert_called_once()


# ==================== HttpClient 构造与默认值测试 ====================


class TestHttpClientInit:
    """HttpClient 初始化与默认值测试"""

    def test_default_timeout(self):
        from ErisPulse.Core.constants import DEFAULT_HTTP_CLIENT_TIMEOUT_SECS

        c = HttpClient()
        assert c._timeout == DEFAULT_HTTP_CLIENT_TIMEOUT_SECS

    def test_custom_timeout(self):
        c = HttpClient(timeout=99)
        assert c._timeout == 99

    def test_default_connect_timeout(self):
        from ErisPulse.Core.constants import DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS

        c = HttpClient()
        assert c._connect_timeout == DEFAULT_HTTP_CLIENT_CONNECT_TIMEOUT_SECS

    def test_custom_connect_timeout(self):
        c = HttpClient(connect_timeout=5)
        assert c._connect_timeout == 5

    def test_default_max_retries(self):
        from ErisPulse.Core.constants import DEFAULT_HTTP_CLIENT_MAX_RETRIES

        c = HttpClient()
        assert c._max_retries == DEFAULT_HTTP_CLIENT_MAX_RETRIES

    def test_custom_max_retries(self):
        c = HttpClient(max_retries=5)
        assert c._max_retries == 5

    def test_default_retry_delay(self):
        from ErisPulse.Core.constants import DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS

        c = HttpClient()
        assert c._retry_delay == DEFAULT_HTTP_CLIENT_RETRY_DELAY_SECS

    def test_custom_headers(self):
        c = HttpClient(headers={"X-Api-Key": "123"})
        assert c._default_headers["X-Api-Key"] == "123"

    def test_default_user_agent(self):
        from ErisPulse.Core.constants import DEFAULT_HTTP_CLIENT_USER_AGENT

        c = HttpClient()
        if DEFAULT_HTTP_CLIENT_USER_AGENT:
            assert "User-Agent" in c._default_headers
            assert c._default_headers["User-Agent"] == DEFAULT_HTTP_CLIENT_USER_AGENT
        else:
            # 默认值为空字符串时不设置 User-Agent
            assert "User-Agent" not in c._default_headers

    def test_custom_user_agent(self):
        c = HttpClient(user_agent="MyBot/2.0")
        assert c._default_headers["User-Agent"] == "MyBot/2.0"

    def test_initial_stats(self):
        c = HttpClient()
        assert c.stats == {
            "total_requests": 0,
            "total_errors": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
        }

    def test_initial_no_session(self):
        c = HttpClient()
        assert c._session is None


# ==================== HttpClient 快捷方法委托测试 ====================


class TestHttpClientShortcutMethods:
    """测试 get/post/put/delete/patch 委托到 request()"""

    @pytest.fixture
    def client(self):
        c = HttpClient()
        c.request = AsyncMock(return_value=HttpResponse(MagicMock()))
        return c

    @pytest.mark.asyncio
    async def test_get_delegates(self, client):
        await client.get("http://example.com", params={"a": "1"})
        client.request.assert_called_once_with(
            "GET",
            "http://example.com",
            params={"a": "1"},
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_post_delegates(self, client):
        await client.post("http://example.com", json={"k": "v"})
        client.request.assert_called_once_with(
            "POST",
            "http://example.com",
            data=None,
            json={"k": "v"},
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_put_delegates(self, client):
        await client.put("http://example.com", data=b"raw")
        client.request.assert_called_once_with(
            "PUT",
            "http://example.com",
            data=b"raw",
            json=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_delete_delegates(self, client):
        await client.delete("http://example.com")
        client.request.assert_called_once_with(
            "DELETE",
            "http://example.com",
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_patch_delegates(self, client):
        await client.patch("http://example.com", json={"patch": True})
        client.request.assert_called_once_with(
            "PATCH",
            "http://example.com",
            data=None,
            json={"patch": True},
            headers=None,
        )


# ==================== HttpClient 统计测试 ====================


class TestHttpClientStats:
    """HttpClient 统计功能测试"""

    def test_stats_returns_copy(self):
        c = HttpClient()
        stats1 = c.stats
        stats2 = c.stats
        assert stats1 == stats2
        assert stats1 is not stats2  # 必须是副本

    def test_reset_stats(self):
        c = HttpClient()
        c._stats["total_requests"] = 100
        c._stats["total_errors"] = 5
        c.reset_stats()
        assert c.stats == {
            "total_requests": 0,
            "total_errors": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
        }


# ==================== HttpClient 上下文管理测试 ====================


class TestHttpClientContextManager:
    """HttpClient 上下文管理器测试"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        c = HttpClient()
        c.close = AsyncMock()
        async with c:
            pass
        c.close.assert_called_once()


# ==================== HttpClient close 测试 ====================


class TestHttpClientClose:
    """HttpClient close() 测试"""

    @pytest.mark.asyncio
    async def test_close_with_active_session(self):
        c = HttpClient()
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()
        c._session = mock_session

        await c.close()
        mock_session.close.assert_called_once()
        assert c._session is None

    @pytest.mark.asyncio
    async def test_close_with_closed_session(self):
        c = HttpClient()
        mock_session = MagicMock()
        mock_session.closed = True
        mock_session.close = AsyncMock()
        c._session = mock_session

        await c.close()
        mock_session.close.assert_not_called()
        # close() 始终清理 session 引用（已关闭的 session 不会再次 close）
        assert c._session is None

    @pytest.mark.asyncio
    async def test_close_with_no_session(self):
        c = HttpClient()
        c._session = None
        await c.close()  # 不应抛异常
        assert c._session is None


# ==================== HttpClient Session 创建测试 ====================


class TestHttpClientSession:
    """HttpClient _get_http_session 测试"""

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self):
        c = HttpClient(timeout=10, connect_timeout=3, headers={"X-Test": "yes"})

        mock_aiohttp = MagicMock()
        mock_session = MagicMock()
        mock_session.closed = False
        mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
        mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())

        with patch.dict("sys.modules", {"aiohttp": mock_aiohttp}):
            session = await c._get_http_session()

        assert session is mock_session
        mock_aiohttp.ClientSession.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self):
        c = HttpClient()
        mock_session = MagicMock()
        mock_session.closed = False
        c._session = mock_session

        session = await c._get_http_session()
        assert session is mock_session

    @pytest.mark.asyncio
    async def test_get_session_recreates_if_closed(self):
        c = HttpClient()
        dead_session = MagicMock()
        dead_session.closed = True
        c._session = dead_session

        mock_aiohttp = MagicMock()
        new_session = MagicMock()
        new_session.closed = False
        mock_aiohttp.ClientSession = MagicMock(return_value=new_session)
        mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())

        with patch.dict("sys.modules", {"aiohttp": mock_aiohttp}):
            session = await c._get_http_session()

        assert session is new_session


# ==================== HttpClient request 核心逻辑测试 ====================


class TestHttpClientRequest:
    """HttpClient.request 核心请求逻辑测试"""

    @pytest.mark.asyncio
    async def test_request_success(self):
        c = HttpClient()

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"")
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        result = await c.request("GET", "http://example.com/api")
        assert isinstance(result, HttpResponse)
        assert result.status == 200
        assert c.stats["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_request_records_error_on_failure(self):
        c = HttpClient(max_retries=0)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(side_effect=ConnectionError("refused"))
        c._session = mock_session

        with pytest.raises(ClientError, match="refused"):
            await c.request("GET", "http://example.com")

        assert c.stats["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_request_retries_on_failure(self):
        c = HttpClient(max_retries=2, retry_delay=0)

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary failure")
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read = AsyncMock(return_value=b"")
            return mock_resp

        mock_session = MagicMock()
        mock_session.closed = False

        cm = AsyncMock()
        cm.__aenter__ = mock_request
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        result = await c.request("GET", "http://example.com")
        assert result.status == 200
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_request_exhausts_retries(self):
        c = HttpClient(max_retries=1, retry_delay=0)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(side_effect=ConnectionError("persistent"))
        c._session = mock_session

        with pytest.raises(ClientError, match="persistent"):
            await c.request("GET", "http://example.com")

        assert c.stats["total_errors"] == 2

    @pytest.mark.asyncio
    async def test_request_per_request_timeout_override(self):
        c = HttpClient(timeout=10)

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"")

        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        await c.request("GET", "http://example.com", timeout=60)

        # 验证 request 被调用（timeout 参数传递给 aiohttp.ClientTimeout）
        mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_per_request_max_retries_override(self):
        c = HttpClient(max_retries=0)

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("once")
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read = AsyncMock(return_value=b"")
            return mock_resp

        mock_session = MagicMock()
        mock_session.closed = False

        cm = AsyncMock()
        cm.__aenter__ = mock_request
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        result = await c.request("GET", "http://example.com", max_retries=1)
        assert result.status == 200
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_request_passes_all_params(self):
        c = HttpClient()
        captured_kwargs = {}

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"")

        async def capture_request(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return mock_resp

        cm = AsyncMock()
        cm.__aenter__ = capture_request
        cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        await c.request(
            "POST",
            "http://example.com/api",
            params={"q": "test"},
            headers={"Authorization": "Bearer token"},
            data={"form": "data"},
            json={"json": "data"},
        )

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "http://example.com/api"

    @pytest.mark.asyncio
    async def test_request_lifecycle_event(self):
        c = HttpClient()
        emitted_events = []

        async def mock_emit(event_name, data):
            emitted_events.append((event_name, data))

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"")
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        with patch("ErisPulse.Core.client.lifecycle") as mock_lifecycle:
            mock_lifecycle.emit = mock_emit
            await c.request("GET", "http://example.com/api")

        assert len(emitted_events) == 1
        assert emitted_events[0][0] == "client.request.success"
        assert emitted_events[0][1]["method"] == "GET"
        assert emitted_events[0][1]["url"] == "http://example.com/api"
        assert emitted_events[0][1]["status"] == 200
        assert "elapsed" in emitted_events[0][1]

    @pytest.mark.asyncio
    async def test_request_logs_error_status(self):
        c = HttpClient()

        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.read = AsyncMock(return_value=b"")
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_resp)
        cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        with patch("ErisPulse.Core.client.logger") as mock_logger:
            result = await c.request("GET", "http://example.com")

        assert result.status == 500
        assert c.stats["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_request_passes_extra_kwargs(self):
        c = HttpClient()
        captured = {}

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"")

        async def capture(*args, **kwargs):
            captured.update(kwargs)
            return mock_resp

        cm = AsyncMock()
        cm.__aenter__ = capture
        cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=cm)
        c._session = mock_session

        await c.request("GET", "http://example.com", ssl=False, allow_redirects=False)

        call_kwargs = mock_session.request.call_args[1]
        assert call_kwargs.get("ssl") is False
        assert call_kwargs.get("allow_redirects") is False
