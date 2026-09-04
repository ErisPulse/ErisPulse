"""
types 命令单元测试

测试类型存根生成命令的核心逻辑：适配器/模块扫描、存根内容生成、文件写入。
"""

import os
import tempfile
from argparse import Namespace
from unittest.mock import patch

import pytest

from ErisPulse.CLI.commands.types import (
    STUB_FILENAME,
    TypesCommand,
    _build_send_class_stub,
    _is_module_method,
    _is_send_method,
)

# ==================== 辅助函数测试 ====================


class TestHelpers:
    """辅助判断函数测试"""

    def test_is_send_method_excludes_underscore(self):
        """下划线开头的方法不应被视为发送方法"""
        assert not _is_send_method("_private", lambda: None)

    def test_is_send_method_excludes_chain_modifiers(self):
        """链式修饰方法不应被视为发送方法"""
        for name in ("At", "To", "Using", "Hook", "Retry", "Build"):
            assert not _is_send_method(name, lambda: None), f"{name} 不应被识别为发送方法"

    def test_is_send_method_excludes_standard_methods(self):
        """标准发送方法不应出现在平台特有方法列表"""
        for name in ("Text", "Image", "Voice", "Video", "File", "Raw_ob12"):
            assert not _is_send_method(name, lambda: None), f"{name} 应被排除"

    def test_is_send_method_accepts_platform_methods(self):
        """平台特有方法应被识别"""
        assert _is_send_method("Sticker", lambda: None)
        assert _is_send_method("Dice", lambda: None)

    def test_is_send_method_rejects_non_callable(self):
        """非可调用对象不应被视为发送方法"""
        assert not _is_send_method("some_attr", "not_callable")

    def test_is_module_method_excludes_dunder(self):
        """下划线开头不应被视为模块方法"""
        assert not _is_module_method("__init__", lambda: None)
        assert not _is_module_method("_private", lambda: None)

    def test_is_module_method_excludes_framework_attrs(self):
        """框架注入的属性不应被视为模块方法"""
        for name in ("sdk", "logger", "cfg", "storage", "on_load", "on_unload"):
            assert not _is_module_method(name, lambda: None)

    def test_is_module_method_accepts_user_methods(self):
        """用户定义的方法应被识别"""
        assert _is_module_method("hello", lambda: None)
        assert _is_module_method("do_something", lambda: None)


class TestBuildSendClassStub:
    """Send 子类存根构造测试"""

    def test_empty_send_class(self):
        """没有平台特有方法的 Send 类应返回空字符串"""
        from ErisPulse.Core.Bases import SendDSL

        class EmptySend(SendDSL):
            pass

        assert _build_send_class_stub(EmptySend) == ""

    def test_send_class_with_platform_methods(self):
        """有平台特有方法的 Send 类应生成方法声明"""
        from ErisPulse.Core.Bases import SendDSL

        class CustomSend(SendDSL):
            def Sticker(self, sticker_id):
                pass

            def Dice(self):
                pass

        stub = _build_send_class_stub(CustomSend)
        assert "def Sticker" in stub
        assert "def Dice" in stub

    def test_send_class_excludes_standard_methods(self):
        """标准方法（Text/Image）不应出现在存根中（基类已有）"""
        from ErisPulse.Core.Bases import SendDSL

        class SendWithOverride(SendDSL):
            def Text(self, text):
                pass

            def Sticker(self, sid):
                pass

        stub = _build_send_class_stub(SendWithOverride)
        assert "Sticker" in stub
        # Text 是标准方法，已在基类声明，存根中不应再出现
        assert "Text" not in stub


# ==================== 命令集成测试 ====================


class TestPascalCaseEpName:
    """入口点名 PascalCase 转换测试"""

    def test_lowercase(self):
        from ErisPulse.CLI.commands.types import _pascal_case_ep_name
        assert _pascal_case_ep_name("yunhu") == "Yunhu"

    def test_already_pascal_case(self):
        from ErisPulse.CLI.commands.types import _pascal_case_ep_name
        assert _pascal_case_ep_name("MyModule") == "MyModule"

    def test_snake_case(self):
        from ErisPulse.CLI.commands.types import _pascal_case_ep_name
        assert _pascal_case_ep_name("my_adapter") == "MyAdapter"

    def test_with_dash(self):
        from ErisPulse.CLI.commands.types import _pascal_case_ep_name
        assert _pascal_case_ep_name("ErisPulse-Dashboard") == "ErisPulseDashboard"

    def test_mixed_camel_and_snake(self):
        from ErisPulse.CLI.commands.types import _pascal_case_ep_name
        assert _pascal_case_ep_name("yunhu_user") == "YunhuUser"

    def test_preserves_internal_camel(self):
        from ErisPulse.CLI.commands.types import _pascal_case_ep_name
        # ErisPulse 拆分为 Eris / Pulse，然后重新组装
        assert _pascal_case_ep_name("ErisPulse") == "ErisPulse"


class TestTypesCommand:
    """TypesCommand 集成测试"""


    @pytest.fixture
    def command(self):
        """创建 TypesCommand 实例"""
        return TypesCommand()

    @pytest.fixture
    def temp_dir(self):
        """提供临时目录作为输出位置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                yield tmpdir
            finally:
                os.chdir(old_cwd)

    def test_command_name_and_aliases(self, command):
        """命令名和别名应正确"""
        assert command.name == "types"
        assert "t" in command.aliases
        assert "stub" in command.aliases

    def test_no_components_found(self, command, temp_dir):
        """没有已安装组件时应输出提示"""
        # 模拟内省返回空列表
        with patch.object(command, "_introspect_remote", return_value=[]):
            args = Namespace(output=None, force=False,
                             adapters_only=False, modules_only=False)
            # 不应抛异常
            command.execute(args)

    def test_file_exists_without_force(self, command, temp_dir):
        """文件已存在且未指定 --force 时应跳过"""
        # 创建已存在的文件
        stub_path = os.path.join(temp_dir, STUB_FILENAME)
        with open(stub_path, "w") as f:
            f.write("# existing")

        with patch.object(command, "_introspect_remote", return_value=[]):
            args = Namespace(output=None, force=False,
                             adapters_only=False, modules_only=False)
            command.execute(args)

            # 文件内容不应被覆盖
            with open(stub_path) as f:
                assert f.read() == "# existing"

    def test_generate_with_mock_adapter(self, command, temp_dir):
        """使用模拟适配器生成存根"""
        # 模拟内省返回适配器信息（send_methods 由目标环境子进程采集）
        fake_adapters = [{
            "name": "test_platform",
            "value": "fake_module:FakeAdapter",
            "module_path": "fake_module",
            "qualname": "FakeAdapter",
            "send_methods": ["CustomMethod", "Sticker"],
        }]

        with patch.object(command, "_introspect_remote", return_value=fake_adapters):
            args = Namespace(output=None, force=True,
                             adapters_only=False, modules_only=False)
            command.execute(args)

            stub_path = os.path.join(temp_dir, STUB_FILENAME)
            assert os.path.exists(stub_path)

            with open(stub_path, encoding="utf-8") as f:
                content = f.read()

            # 新设计仅导出类型，不再生成 overload 与 Send 子类声明
            # 应包含适配器类的导入（别名 = 入口点名的 PascalCase）
            assert "from fake_module import FakeAdapter as TestPlatform" in content
            assert "TestPlatform" in content
            # __all__ 应包含别名
            assert "'TestPlatform'" in content
            # 不应包含旧的访问器类型设计
            assert "_TypedAdapterManager" not in content
            assert "_TypedModuleManager" not in content
            assert "sdk.adapter =" not in content.replace(" ", "")  # 不导出实例
            # 应可编译
            compile(content, stub_path, "exec")

    def test_generate_with_mock_module(self, command, temp_dir):
        """使用模拟模块生成存根"""
        fake_modules = [{
            "name": "test_module",
            "value": "fake_module:FakeModule",
            "module_path": "fake_module",
            "qualname": "FakeModule",
            "methods": ["hello", "do_something"],
        }]

        # _introspect_remote 根据参数返回不同数据，这里需要根据 group 区分
        def fake_introspect(python, group, kind):
            if kind == "module":
                return fake_modules
            return []

        with patch.object(command, "_introspect_remote", side_effect=fake_introspect):
            args = Namespace(output=None, force=True,
                             adapters_only=False, modules_only=False)
            command.execute(args)

            stub_path = os.path.join(temp_dir, STUB_FILENAME)
            with open(stub_path, encoding="utf-8") as f:
                content = f.read()

            # 模块类导入应以 PascalCase 入口点名作为别名
            assert "from fake_module import FakeModule as TestModule" in content
            assert "'TestModule'" in content
            compile(content, stub_path, "exec")

    def test_custom_output_path(self, command, temp_dir):
        """应支持自定义输出路径"""
        custom_path = os.path.join(temp_dir, "custom_stubs.py")

        with patch.object(command, "_introspect_remote", return_value=[]):
            args = Namespace(output=custom_path, force=True,
                             adapters_only=False, modules_only=False)
            command.execute(args)

            # 没组件时提前返回，不写文件
            assert not os.path.exists(custom_path)

    def test_generate_with_actual_introspect(self, command, temp_dir, monkeypatch):
        """端到端测试：使用真实子进程内省（需要 ErisPulse 可导入）"""
        # 此测试不 mock，走真实的子进程内省路径
        # 如果环境里有任何模块/适配器，应能生成有效存根
        args = Namespace(output=None, force=True,
                         adapters_only=False, modules_only=False)
        # 不应抛异常
        try:
            command.execute(args)
        except SystemExit:
            pass

        stub_path = os.path.join(temp_dir, STUB_FILENAME)
        if os.path.exists(stub_path):
            with open(stub_path, encoding="utf-8") as f:
                content = f.read()
            # 至少应能编译
            compile(content, stub_path, "exec")
            # 应包含存根头部注释
            assert "_ep_types" in content or "ErisPulse" in content
