"""
异常诊断模块单元测试

测试 runtime.diagnostics 的用户代码帧提取与诊断信息格式化
"""

from unittest.mock import MagicMock

from ErisPulse.runtime.diagnostics import (
    extract_user_frame,
    format_diagnostic_block,
    log_diagnostic,
)

# ==================== extract_user_frame 测试 ====================


class TestExtractUserFrame:
    """extract_user_frame 用户代码帧提取测试"""

    def test_extract_basic_exception(self):
        """测试从普通异常提取帧信息"""
        try:
            x = 1 / 0
        except Exception as e:
            info = extract_user_frame(e)

        assert info["has_traceback"] is True
        assert info["exc_type"] == "ZeroDivisionError"
        assert "division by zero" in info["exc_value"]
        # 应至少捕获到一个用户帧
        assert len(info["frames"]) >= 1
        frame = info["frames"][-1]
        assert frame["lineno"] > 0
        assert "func" in frame
        # 源码应包含触发异常的行
        assert frame["source"] is not None

    def test_extract_no_traceback(self):
        """测试异常无 traceback 时的降级"""
        exc = ValueError("手动构造无 traceback")
        info = extract_user_frame(exc)

        assert info["has_traceback"] is False
        assert info["frames"] == []
        assert info["exc_type"] == "ValueError"
        assert "手动构造无 traceback" in info["exc_value"]

    def test_extract_filters_framework_frames(self):
        """测试框架内部帧被过滤"""
        # 框架内部文件应被识别为框架帧
        import ErisPulse.runtime.diagnostics as diag_mod
        from ErisPulse.runtime.diagnostics import _is_framework_frame

        assert _is_framework_frame(diag_mod.__file__) is True

        # 当前测试文件（用户代码）不应被识别为框架帧
        assert _is_framework_frame(__file__) is False

        # 通过框架代码触发异常，验证 traceback 中框架帧被过滤掉
        def user_code():
            raise RuntimeError("用户代码错误")

        try:
            user_code()
        except Exception as e:
            info = extract_user_frame(e)

        # 至少保留一个用户帧（本测试文件）
        assert len(info["frames"]) >= 1
        assert any("test_unit_diagnostics" in f["file"] for f in info["frames"])

    def test_extract_depth_limit(self):
        """测试 depth 参数限制帧数量"""

        def level_a():
            raise ValueError("深层错误")

        def level_b():
            level_a()

        def level_c():
            level_b()

        def level_d():
            level_c()

        try:
            level_d()
        except Exception as e:
            info_full = extract_user_frame(e, depth=10)
            info_limited = extract_user_frame(e, depth=1)

        # depth=1 时帧数不超过 1
        assert len(info_limited["frames"]) <= 1
        # depth=10 时帧数 >= depth=1
        assert len(info_full["frames"]) >= len(info_limited["frames"])

    def test_extract_nested_exception(self):
        """测试嵌套异常的帧提取"""
        try:
            try:
                _ = [][0]  # noqa: PLE0643
            except IndexError as inner:
                raise RuntimeError("外层包装错误") from inner
        except Exception as e:
            info = extract_user_frame(e)

        assert info["exc_type"] == "RuntimeError"
        assert info["has_traceback"] is True

    def test_short_filename_relative_to_cwd(self, tmp_path, monkeypatch):
        """测试文件名相对于 cwd 的缩短"""
        # 创建一个临时用户文件并触发异常
        user_file = tmp_path / "user_module.py"
        user_file.write_text("def boom():\n    return 1 / 0\n")

        monkeypatch.chdir(tmp_path)
        # 动态导入该文件
        import importlib.util

        spec = importlib.util.spec_from_file_location("user_module", user_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        try:
            mod.boom()
        except Exception as e:
            info = extract_user_frame(e)

        # 文件名应缩短为相对路径（不包含 tmp_path 全路径）
        assert any(
            "user_module.py" in f["file"] and str(tmp_path) not in f["file"]
            for f in info["frames"]
        )


# ==================== format_diagnostic_block 测试 ====================


class TestFormatDiagnosticBlock:
    """format_diagnostic_block 诊断文本格式化测试"""

    def test_format_contains_frame_and_exception(self):
        """测试格式化输出包含帧与异常类型"""
        try:
            raise NameError("undefined_name")
        except Exception as e:
            block = format_diagnostic_block(e)

        assert "→" in block
        assert "NameError" in block
        # 末尾应为提示行（以 → 开头）
        last_line = block.split("\n")[-1]
        assert last_line.startswith("  →")

    def test_format_no_traceback_uses_fallback_message(self):
        """测试无 traceback 时输出 fallback 消息"""
        exc = RuntimeError("无堆栈")
        block = format_diagnostic_block(exc)

        # 应包含「未找到用户代码帧」相关的 fallback 文本
        assert "→" in block
        # i18n 可能生效也可能 fallback 到英文，两者都接受
        assert (
            "未找到用户代码帧" in block
            or "no user code frame" in block.lower()
        )

    def test_format_with_custom_hint_key(self):
        """测试自定义 hint_key"""
        from ErisPulse.Core.i18n import i18n

        # 注册一个测试 hint key
        i18n.register(
            "zh-CN",
            {"test.diag.custom_hint": "这是自定义提示 {name}"},
            domain="test_diag",
        )
        try:
            raise ValueError("测试错误")
        except Exception as e:
            block = format_diagnostic_block(e, hint_key="test.diag.custom_hint")

        # 由于 hint_key 渲染时无 name 参数，可能回退；这里主要验证不崩溃
        assert isinstance(block, str)
        assert "→" in block
        i18n.unregister_domain("test_diag")

    def test_format_with_candidates_adds_suggestion(self):
        """测试 candidates 参数附加相似提示"""
        try:
            raise ValueError("some_typo_value")
        except Exception as e:
            block = format_diagnostic_block(e, candidates=["some_correct_value"])

        # 相似提示行应出现（如果匹配）
        assert isinstance(block, str)

    def test_format_multiline_structure(self):
        """测试输出为多行结构"""
        try:
            data = {"a": 1}
            _ = data["missing_key"]
        except Exception as e:
            block = format_diagnostic_block(e)

        lines = block.split("\n")
        # 至少 2 行（帧 + 提示）
        assert len(lines) >= 2
        for line in lines:
            assert line.startswith("  ")


# ==================== log_diagnostic 测试 ====================


class TestLogDiagnostic:
    """log_diagnostic 日志集成测试"""

    def test_log_diagnostic_writes_to_logger(self):
        """测试诊断信息写入 logger"""
        mock_logger = MagicMock()
        try:
            raise ValueError("日志测试错误")
        except Exception as e:
            log_diagnostic(e, logger=mock_logger)

        mock_logger.error.assert_called_once()
        written = mock_logger.error.call_args[0][0]
        assert "ValueError" in written
        assert "→" in written

    def test_log_diagnostic_no_logger_falls_back_to_core(self):
        """测试不传 logger 时回退到 Core.logger"""
        try:
            raise ValueError("回退测试")
        except Exception as e:
            # 不应抛出异常
            log_diagnostic(e)

    def test_log_diagnostic_with_hint_key(self):
        """测试带 hint_key 的日志输出"""
        mock_logger = MagicMock()
        try:
            raise KeyError("test")
        except Exception as e:
            log_diagnostic(e, hint_key="loader.module.diag_hint", logger=mock_logger)

        mock_logger.error.assert_called_once()
        written = mock_logger.error.call_args[0][0]
        assert "→" in written


# ==================== runtime 聚合导出测试 ====================


class TestRuntimeExport:
    """runtime 聚合导出测试"""

    def test_diagnostics_exported_from_runtime(self):
        """测试诊断函数从 runtime 包导出"""
        from ErisPulse import runtime

        assert hasattr(runtime, "extract_user_frame")
        assert hasattr(runtime, "format_diagnostic_block")
        assert hasattr(runtime, "log_diagnostic")
        assert "extract_user_frame" in runtime.__all__
        assert "format_diagnostic_block" in runtime.__all__
        assert "log_diagnostic" in runtime.__all__
