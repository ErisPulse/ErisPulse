"""
WebSocket 共享基类单元测试

覆盖 Core.Bases.websocket：
- WSMessage：类型常量、属性、__repr__
- WebSocketConnectionBase：raw/url/headers 属性代理、iter_* 迭代器在断开时停止、
  on_disconnect/on_error 回调注册（直接调用与装饰器两种形式）
"""

import pytest

from ErisPulse.Core.Bases.errors import WebSocketDisconnect
from ErisPulse.Core.Bases.websocket import WebSocketConnectionBase, WSMessage

# ==================== 测试用的最小实现 ====================


class _FakeRaw:
    """模拟底层 WebSocket 对象"""

    def __init__(self):
        self.url = "ws://example.com/ws"
        self.headers = {"X-Test": "yes"}


class _ControllableWS(WebSocketConnectionBase):
    """可注入 receive 序列的 WS 实现，用于测试 iter_* 行为"""

    def __init__(self, raw, receive_sequence=None, sends=None):
        super().__init__(raw)
        self._receive_sequence = list(receive_sequence or [])
        self._receive_idx = 0
        self.sends = sends if sends is not None else []

    async def send_text(self, data: str) -> None:
        self.sends.append(("text", data))

    async def send_bytes(self, data: bytes) -> None:
        self.sends.append(("bytes", data))

    async def send_json(self, data, mode: str = "text") -> None:
        self.sends.append(("json", data, mode))

    async def receive_text(self) -> str:
        return self._next_or_disconnect()

    async def receive_bytes(self) -> bytes:
        return self._next_or_disconnect()

    async def receive_json(self, mode: str = "text"):
        return self._next_or_disconnect()

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.sends.append(("close", code, reason))

    def _next_or_disconnect(self):
        if self._receive_idx < len(self._receive_sequence):
            item = self._receive_sequence[self._receive_idx]
            self._receive_idx += 1
            if isinstance(item, Exception):
                raise item
            return item
        raise WebSocketDisconnect(1000, "eof")


# ==================== WSMessage ====================


class TestWSMessage:
    def test_type_constants(self):
        assert WSMessage.TEXT == "text"
        assert WSMessage.BINARY == "binary"
        assert WSMessage.CLOSE == "close"
        assert WSMessage.ERROR == "error"

    def test_attributes(self):
        msg = WSMessage(WSMessage.TEXT, "hello")
        assert msg.type == "text"
        assert msg.data == "hello"

    def test_default_data_is_none(self):
        msg = WSMessage(WSMessage.CLOSE)
        assert msg.data is None

    def test_repr_contains_type_and_data(self):
        msg = WSMessage(WSMessage.TEXT, "hello")
        rendered = repr(msg)
        assert "text" in rendered
        assert "hello" in rendered

    def test_slots_prevents_extra_attributes(self):
        msg = WSMessage(WSMessage.TEXT, "x")
        # __slots__ 限制：不能设置未声明的属性
        with pytest.raises(AttributeError):
            msg.extra = 1


# ==================== WebSocketConnectionBase 属性 ====================


class TestProperties:
    def test_raw_proxies_underlying_object(self):
        raw = _FakeRaw()
        ws = _ControllableWS(raw)
        assert ws.raw is raw

    def test_url_proxies_underlying(self):
        raw = _FakeRaw()
        ws = _ControllableWS(raw)
        assert ws.url == "ws://example.com/ws"

    def test_headers_proxies_underlying(self):
        raw = _FakeRaw()
        ws = _ControllableWS(raw)
        assert ws.headers == {"X-Test": "yes"}


# ==================== iter_* 迭代器 ====================


class TestIterators:
    async def test_iter_text_yields_until_disconnect(self):
        ws = _ControllableWS(_FakeRaw(), receive_sequence=["a", "b", "c"])
        collected = [x async for x in ws.iter_text()]
        assert collected == ["a", "b", "c"]

    async def test_iter_text_stops_on_disconnect(self):
        # 序列中插入 WebSocketDisconnect，迭代应停止而不抛出
        ws = _ControllableWS(
            _FakeRaw(),
            receive_sequence=["a", WebSocketDisconnect(1000, "bye"), "never"],
        )
        collected = [x async for x in ws.iter_text()]
        assert collected == ["a"]

    async def test_iter_bytes_stops_on_disconnect(self):
        ws = _ControllableWS(
            _FakeRaw(),
            receive_sequence=[b"x", b"y", WebSocketDisconnect()],
        )
        collected = [x async for x in ws.iter_bytes()]
        assert collected == [b"x", b"y"]

    async def test_iter_json_stops_on_disconnect(self):
        ws = _ControllableWS(
            _FakeRaw(),
            receive_sequence=[{"k": 1}, WebSocketDisconnect()],
        )
        collected = [x async for x in ws.iter_json()]
        assert collected == [{"k": 1}]

    async def test_iter_empty_when_immediately_disconnected(self):
        ws = _ControllableWS(_FakeRaw(), receive_sequence=[WebSocketDisconnect()])
        collected = [x async for x in ws.iter_text()]
        assert collected == []

    async def test_non_disconnect_exception_propagates(self):
        # 非 WebSocketDisconnect 异常应正常向上抛出，不被吞掉
        ws = _ControllableWS(
            _FakeRaw(),
            receive_sequence=[RuntimeError("boom")],
        )
        with pytest.raises(RuntimeError, match="boom"):
            async for _ in ws.iter_text():
                pass


# ==================== 生命周期回调 ====================


class TestLifecycleHooks:
    def test_on_disconnect_direct_call_registers(self):
        ws = _ControllableWS(_FakeRaw())

        def handler(ws, reason=""):
            pass

        ret = ws.on_disconnect(handler)
        assert ret is handler
        assert handler in ws._on_disconnect_handlers

    def test_on_disconnect_as_decorator(self):
        ws = _ControllableWS(_FakeRaw())

        @ws.on_disconnect
        def handler(ws, reason=""):
            pass

        assert handler in ws._on_disconnect_handlers

    def test_on_error_direct_call_registers(self):
        ws = _ControllableWS(_FakeRaw())

        def handler(ws, error=""):
            pass

        ret = ws.on_error(handler)
        assert ret is handler
        assert handler in ws._on_error_handlers

    def test_on_error_as_decorator(self):
        ws = _ControllableWS(_FakeRaw())

        @ws.on_error
        def handler(ws, error=""):
            pass

        assert handler in ws._on_error_handlers

    def test_multiple_handlers_accumulate(self):
        ws = _ControllableWS(_FakeRaw())

        @ws.on_disconnect
        def h1(ws, reason=""):
            pass

        @ws.on_disconnect
        def h2(ws, reason=""):
            pass

        assert len(ws._on_disconnect_handlers) == 2
        assert h1 in ws._on_disconnect_handlers
        assert h2 in ws._on_disconnect_handlers


# ==================== 默认抽象方法 ====================


class TestAbstractDefaults:
    async def test_send_text_not_implemented(self):
        ws = WebSocketConnectionBase(_FakeRaw())
        with pytest.raises(NotImplementedError):
            await ws.send_text("x")

    async def test_close_not_implemented(self):
        ws = WebSocketConnectionBase(_FakeRaw())
        with pytest.raises(NotImplementedError):
            await ws.close()
