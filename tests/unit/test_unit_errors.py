"""
异常体系单元测试

覆盖 ErisPulse 自定义异常层级：
- 基类关系（isinstance / 继承链）
- 异常可被 raise / catch
- HTTPStatusError / WebSocketDisconnect 的属性与消息格式化
- 拼写纠错提示系统（runtime.hints）对 ErisPulse 异常的识别
"""

import pytest

from ErisPulse.Core.Bases.errors import (
    ClientConnectionError,
    ClientError,
    ClientTimeoutError,
    ErisPulseError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)


class TestExceptionHierarchy:
    """异常继承层级"""

    def test_all_inherit_from_erispulse_error(self):
        for exc_cls in (
            ClientError,
            ClientConnectionError,
            ClientTimeoutError,
            HTTPStatusError,
            WebSocketError,
            WebSocketDisconnect,
        ):
            assert issubclass(exc_cls, ErisPulseError)

    def test_client_errors_inherit_from_client_error(self):
        for exc_cls in (ClientConnectionError, ClientTimeoutError, HTTPStatusError):
            assert issubclass(exc_cls, ClientError)

    def test_websocket_disconnect_inherits_from_websocket_error(self):
        assert issubclass(WebSocketDisconnect, WebSocketError)

    def test_erispulse_error_is_exception(self):
        assert issubclass(ErisPulseError, Exception)


class TestCatchableBehavior:
    """异常可被正常抛出与捕获"""

    def test_raise_and_catch_base(self):
        with pytest.raises(ErisPulseError):
            raise ErisPulseError("boom")

    def test_catch_client_error_covers_subclasses(self):
        # 用基类捕获子类
        with pytest.raises(ClientError):
            raise ClientConnectionError("dns failed")

        with pytest.raises(ClientError):
            raise ClientTimeoutError("slow")

        with pytest.raises(ClientError):
            raise HTTPStatusError(500, "server error")

    def test_catch_websocket_error_covers_disconnect(self):
        with pytest.raises(WebSocketError):
            raise WebSocketDisconnect(1000, "bye")


class TestHTTPStatusError:
    """HTTPStatusError 的属性与消息"""

    def test_attributes_stored(self):
        err = HTTPStatusError(404, "Not Found")
        assert err.status == 404
        assert err.message == "Not Found"

    def test_message_includes_status(self):
        err = HTTPStatusError(404, "Not Found")
        assert "404" in str(err)
        assert "Not Found" in str(err)

    def test_empty_message(self):
        err = HTTPStatusError(500)
        assert err.message == ""
        assert "500" in str(err)

    def test_is_exception_instance(self):
        err = HTTPStatusError(403, "forbidden")
        assert isinstance(err, Exception)


class TestWebSocketDisconnect:
    """WebSocketDisconnect 的属性与默认值"""

    def test_defaults(self):
        err = WebSocketDisconnect()
        assert err.code == 1000
        assert err.reason == ""

    def test_custom_code_and_reason(self):
        err = WebSocketDisconnect(1011, "internal error")
        assert err.code == 1011
        assert err.reason == "internal error"

    def test_none_reason_normalized_to_empty(self):
        err = WebSocketDisconnect(1001, None)
        assert err.reason == ""

    def test_message_contains_code_and_reason(self):
        err = WebSocketDisconnect(1000, "normal")
        rendered = str(err)
        assert "1000" in rendered
        assert "normal" in rendered


class TestHintsRecognition:
    """异常友好提示系统对 ErisPulse 异常的识别"""

    def test_http_status_error_hint(self):
        from ErisPulse.runtime.hints import suggest_for_erispulse_client_error

        # 4xx -> http_client_error
        assert suggest_for_erispulse_client_error(HTTPStatusError(404, "x")) == "http_client_error"
        # 5xx -> http_server_error
        assert suggest_for_erispulse_client_error(HTTPStatusError(500, "x")) == "http_server_error"
        # 其他状态码 -> http_status_error
        assert suggest_for_erispulse_client_error(HTTPStatusError(302, "x")) == "http_status_error"

    def test_client_connection_error_hint(self):
        from ErisPulse.runtime.hints import suggest_for_erispulse_client_error

        hint = suggest_for_erispulse_client_error(ClientConnectionError("x"))
        assert hint == "client_connection_error"

    def test_client_timeout_error_hint(self):
        from ErisPulse.runtime.hints import suggest_for_erispulse_client_error

        hint = suggest_for_erispulse_client_error(ClientTimeoutError("x"))
        assert hint == "client_timeout_error"

    def test_websocket_disconnect_hint(self):
        from ErisPulse.runtime.hints import suggest_for_websocket_disconnect

        # 异常关闭（非 1000/1001）应给出提示
        hint = suggest_for_websocket_disconnect(WebSocketDisconnect(1011, "abnormal"))
        assert hint == "websocket_abnormal_close"

    def test_websocket_normal_close_no_hint(self):
        from ErisPulse.runtime.hints import suggest_for_websocket_disconnect

        # 正常关闭（1000）不应给出提示
        hint = suggest_for_websocket_disconnect(WebSocketDisconnect(1000))
        assert hint == "websocket_normal_close"


class TestAsyncExceptionHandlerNoiseFiltering:
    """异步异常处理器对退出/关停噪音的降级处理（避免刷屏）"""

    def test_system_exit_is_not_logged_as_error(self):
        from unittest.mock import Mock, patch

        from ErisPulse.runtime.exceptions import async_exception_handler

        with patch("ErisPulse.runtime.exceptions._log_async_noise") as mock_noise, patch(
            "ErisPulse.runtime.exceptions._get_error_logger"
        ) as mock_get_logger:
            err_logger = Mock()
            mock_get_logger.return_value = err_logger

            # uvicorn 端口绑定失败等场景：任务抛出 SystemExit，应降级处理而非 ERROR 刷屏
            async_exception_handler(None, {"exception": SystemExit(3)})

            err_logger.assert_not_called()
            mock_noise.assert_called_once()

    def test_keyboard_interrupt_is_not_logged_as_error(self):
        from unittest.mock import Mock, patch

        from ErisPulse.runtime.exceptions import async_exception_handler

        with patch("ErisPulse.runtime.exceptions._log_async_noise") as mock_noise, patch(
            "ErisPulse.runtime.exceptions._get_error_logger"
        ) as mock_get_logger:
            err_logger = Mock()
            mock_get_logger.return_value = err_logger

            async_exception_handler(None, {"exception": KeyboardInterrupt()})

            err_logger.assert_not_called()
            mock_noise.assert_called_once()

    def test_task_destroyed_noise_is_folded(self):
        from unittest.mock import Mock, patch

        from ErisPulse.runtime.exceptions import (
            _async_noise_state,
            async_exception_handler,
        )

        _async_noise_state.clear()
        try:
            with patch("ErisPulse.runtime.exceptions._log_async_noise") as mock_noise, patch(
                "ErisPulse.runtime.exceptions._get_error_logger"
            ) as mock_get_logger:
                err_logger = Mock()
                mock_get_logger.return_value = err_logger

                ctx = {"message": "Task was destroyed but it is pending!"}
                async_exception_handler(None, ctx)
                async_exception_handler(None, ctx)  # 窗口内重复，应被折叠

                err_logger.assert_not_called()
                # 首次输出 + 折叠（不重复调用），故只调用一次
                assert mock_noise.call_count == 1
        finally:
            _async_noise_state.clear()

    def test_real_async_error_still_logged_as_error(self):
        from unittest.mock import Mock, patch

        from ErisPulse.runtime.exceptions import async_exception_handler

        with patch("ErisPulse.runtime.exceptions._log_async_noise") as mock_noise, patch(
            "ErisPulse.runtime.exceptions._get_error_logger"
        ) as mock_get_logger:
            err_logger = Mock()
            mock_get_logger.return_value = err_logger

            async_exception_handler(None, {"exception": ValueError("boom")})

            # 真实异步错误仍走 ERROR 输出
            err_logger.assert_called_once()
            mock_noise.assert_not_called()
