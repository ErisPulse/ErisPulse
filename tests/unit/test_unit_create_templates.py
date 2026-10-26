"""
create --template 三模式适配器模板与通信模式基类验证

AGENTS 规则 9/8：修改 ``CLI/commands/create.py`` 模板后须 ``.format()`` +
``compile()`` 验证，核心模块改动须补 pytest。本文件把三套适配器模板
（ws-server / polling / webhook）的渲染编译、生成的包级干跑（FakeSDK 实例
化 + start/shutdown 不炸）以及 :class:`PollingAdapter` /
:class:`WebhookAdapter` 两个半成品基类的行为契约固化为常驻用例。
"""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from ErisPulse.CLI.commands import create as create_cmd
from ErisPulse.CLI.utils.scaffold_text import ScaffoldText


def _render(template: str, lang: str = "en") -> str:
    """按指定模板与脚手架语言渲染适配器核心代码"""
    text = ScaffoldText(lang).all()
    return create_cmd._ADAPTER_CORE_TEMPLATES[template].format(
        name="MyAdapter",
        converter_name="MyAdapterConverter",
        entry_key="myadapter",
        text=text,
        min_sdk=create_cmd._TEMPLATE_MIN_SDK_VERSION,
    )


def _unregister_myadapter_i18n() -> None:
    """清理模板 I18nClass 注册进 i18n 单例的 MyAdapter 翻译域"""
    try:
        from ErisPulse.Core.i18n import i18n

        i18n.unregister_domain("MyAdapter")
    except Exception:
        pass


# ==================== 模板渲染与编译 ====================


class TestTemplateRenderAndCompile:
    """三套模板在 en / zh-CN 文案下渲染后均可编译（AGENTS 规则 9）"""

    @pytest.mark.parametrize("template", ["ws-server", "polling", "webhook"])
    @pytest.mark.parametrize("lang", ["en", "zh-CN"])
    def test_renders_and_compiles(self, template, lang):
        code = _render(template, lang)
        compile(code, f"<{template}:{lang}>", "exec")

    @pytest.mark.parametrize("template", ["polling", "webhook"])
    def test_root_imports_resolve(self, template):
        """新模板的根导入符号必须真实存在（防 I18nKeys 式拼写漂移）"""
        import ast

        import ErisPulse

        tree = ast.parse(_render(template))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "ErisPulse"
            for alias in node.names
        }
        assert imported, "模板应使用根导入"
        for sym in imported:
            assert hasattr(ErisPulse, sym), f"模板导入了根包不存在的符号: {sym}"

    def test_template_map_covers_choices(self):
        """--template 的 choices 与模板映射表一致"""
        assert set(create_cmd._ADAPTER_CORE_TEMPLATES) == {"ws-server", "polling", "webhook"}
        # ws-server 保持默认模板不动（现行为兼容）
        assert create_cmd._ADAPTER_CORE_TEMPLATES["ws-server"] is create_cmd._ADAPTER_CORE

    def test_polling_template_omits_start_shutdown(self):
        """polling/webhook 模板不生成 start/shutdown（基类已管）"""
        for template in ("polling", "webhook"):
            code = _render(template)
            assert "async def start(" not in code
            assert "async def shutdown(" not in code


# ==================== 生成包干跑（FakeSDK） ====================


class _FakeLogger:
    """FakeSDK 使用的空日志器（避免依赖真实日志单例）"""

    def get_child(self, *args, **kwargs):
        return self

    def _noop(self, *args, **kwargs):
        pass

    info = warning = error = debug = trace = critical = _noop


class _FakeSDK:
    """模板 __init__(sdk=...) 所需的最小 SDK 形状"""

    logger = _FakeLogger()


class _StubResponse:
    """client.get 的桩响应：返回一批占位平台事件"""

    def __init__(self, events: list):
        self._events = events

    async def json(self) -> dict:
        return {"events": self._events}


class _StubClient:
    """替代模板根导入 client 的桩（避免干跑触网）"""

    calls: int = 0

    async def get(self, url: str, **kwargs) -> _StubResponse:
        _StubClient.calls += 1
        return _StubResponse(
            [
                {
                    "type": "message",
                    "event_id": f"e{_StubClient.calls}",
                    "sender_id": "u1",
                    "content": "hello",
                }
            ]
        )


class _FakeRequest:
    """WebhookAdapter 处理器所需的请求桩"""

    def __init__(self, payload: Any = None, bad_json: bool = False, headers: dict | None = None):
        self.headers = headers or {}
        self._payload = payload
        self._bad_json = bad_json

    async def json(self) -> Any:
        if self._bad_json:
            raise ValueError("not json")
        return self._payload


def _build_template_package(tmp_path: Path, monkeypatch, template: str):
    """把渲染后的模板写成真实包结构并导入（含 Converter 相对导入链）"""
    text = ScaffoldText("en").all()
    core = _render(template)
    converter = create_cmd._ADAPTER_CONVERTER.format(
        name="MyAdapter",
        converter_name="MyAdapterConverter",
        entry_key="myadapter",
        text=text,
    )
    root = tmp_path / template.replace("-", "_")
    pkg = root / "MyAdapter"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(
        create_cmd._ADAPTER_INIT.format(
            name="MyAdapter", converter_name="MyAdapterConverter"
        ),
        encoding="utf-8",
    )
    (pkg / "Core.py").write_text(core, encoding="utf-8")
    (pkg / "Converter.py").write_text(converter, encoding="utf-8")

    monkeypatch.syspath_prepend(str(root))
    sys.modules.pop("MyAdapter", None)
    sys.modules.pop("MyAdapter.Core", None)
    sys.modules.pop("MyAdapter.Converter", None)
    return importlib.import_module("MyAdapter")


@pytest.fixture()
def hermetic_config(monkeypatch):
    """模板实例化期间隔离配置读写（ConfigClass 自动生成模板不落盘）"""
    from ErisPulse.Core.Bases import adapter as bases_adapter

    defaults = {
        "MyAdapter": {
            "endpoint": "https://api.example.com",
            "token": "",
            "poll_interval": 5.0,
        }
    }
    monkeypatch.setattr(
        bases_adapter.config_mgr,
        "getConfig",
        lambda key, *a, **k: defaults.get(key),
    )
    monkeypatch.setattr(bases_adapter.config_mgr, "setConfigTemplate", lambda *a, **k: None)
    monkeypatch.setattr(bases_adapter.config_mgr, "setConfig", lambda *a, **k: None)


class TestTemplatePackageDryRun:
    """渲染产物以真实包结构导入后 FakeSDK 干跑 start/shutdown 不炸"""

    def _purge(self):
        """清理干跑残留：临时包模块与模板注册的 MyAdapter i18n 域"""
        for name in ("MyAdapter", "MyAdapter.Core", "MyAdapter.Converter"):
            sys.modules.pop(name, None)
        _unregister_myadapter_i18n()

    def test_polling_package_dry_run(self, tmp_path, monkeypatch, hermetic_config):
        mod = _build_template_package(tmp_path, monkeypatch, "polling")
        try:
            monkeypatch.setattr(mod.Core, "client", _StubClient())
            emitted: list[dict] = []

            async def _record_emit(_self, event):
                emitted.append(event)

            monkeypatch.setattr(mod.MyAdapter, "emit_event", _record_emit)

            async def scenario():
                adapter = mod.MyAdapter(sdk=_FakeSDK())
                await adapter.start()
                await asyncio.sleep(0.05)
                await adapter.shutdown()

            asyncio.run(scenario())
            assert _StubClient.calls >= 1  # 轮询循环确实拉取过
            assert emitted, "轮询循环应至少转换并上报一条事件"
        finally:
            self._purge()

    def test_webhook_package_dry_run(self, tmp_path, monkeypatch, hermetic_config):
        from ErisPulse.Core.router import router

        mod = _build_template_package(tmp_path, monkeypatch, "webhook")
        registered: list[dict] = []
        monkeypatch.setattr(
            router,
            "register_http_route",
            lambda **kwargs: registered.append(kwargs),
        )
        try:
            emitted: list[dict] = []

            async def _record_emit(_self, event):
                emitted.append(event)

            monkeypatch.setattr(mod.MyAdapter, "emit_event", _record_emit)

            async def scenario():
                adapter = mod.MyAdapter(sdk=_FakeSDK())
                adapter._platform = "myadapter"
                await adapter.start()
                assert registered and registered[0]["module_name"] == "myadapter"
                assert registered[0]["path"] == "/webhook"
                assert registered[0]["methods"] == ["POST"]

                # 处理器契约：合法载荷 → ok 且事件上报
                resp = await adapter._webhook_handler(
                    _FakeRequest({"type": "message", "sender_id": "u1", "content": "hi"})
                )
                assert resp == {"status": "ok"}
                assert emitted and emitted[0]["type"] == "message"

                await adapter.shutdown()

            asyncio.run(scenario())
        finally:
            self._purge()


# ==================== PollingAdapter 行为契约 ====================


class TestPollingAdapterBase:
    """半成品基类：轮询循环 / 退避 / 间隔解析 / 生命周期默认实现"""

    @staticmethod
    def _make_adapter(fetch_impl, convert_impl):
        from ErisPulse.Core.Bases import PollingAdapter

        class _Poll(PollingAdapter):
            _platform = "testpoll"
            poll_interval = 0.01

            async def fetch_events(self):
                return await fetch_impl(self)

            def convert_one(self, raw):
                return convert_impl(self, raw)

            async def call_api(self, endpoint: str, **params):
                return self.make_response()

            async def emit_event(self, event):
                self.emitted.append(event)

        adapter = _Poll()
        adapter.emitted = []
        return adapter

    def test_abstract_hooks_required(self):
        from ErisPulse.Core.Bases import PollingAdapter

        with pytest.raises(TypeError):
            PollingAdapter()  # pyright: ignore[reportAbstractUsage]

    def test_start_spawns_and_loop_emits(self, monkeypatch):
        from ErisPulse.Core.Bases import adapter_patterns

        # 缩短退避，避免失败用例拖慢测试
        monkeypatch.setattr(adapter_patterns, "POLLING_ADAPTER_BACKOFF_BASE_SECS", 0.01)
        monkeypatch.setattr(adapter_patterns, "POLLING_ADAPTER_BACKOFF_MAX_SECS", 0.02)

        state = {"calls": 0}

        async def fetch(_self):
            state["calls"] += 1
            if state["calls"] <= 2:
                raise ConnectionError("platform down")
            return [{"update_id": 1, "text": "hi"}]

        adapter = self._make_adapter(fetch, lambda _s, raw: {"type": "message", "id": str(raw["update_id"])})

        async def scenario():
            await adapter.start()  # spawn-返回式：立即返回
            await asyncio.sleep(0.2)
            await adapter.shutdown()  # 默认空实现不炸

        asyncio.run(scenario())
        # 前 2 次失败走退避，之后成功转换上报；循环始终存活未崩溃
        assert state["calls"] >= 3
        assert adapter.emitted and adapter.emitted[0]["id"] == "1"

    def test_convert_one_none_skips(self):
        async def fetch(_self):
            return [{"update_id": 1}]

        adapter = self._make_adapter(fetch, lambda _s, raw: None)

        async def scenario():
            adapter.spawn_client_loop(adapter._poll_loop(), name="poll")
            await asyncio.sleep(0.05)

        asyncio.run(scenario())
        assert adapter.emitted == []  # None 事件跳过不上报

    def test_resolve_poll_interval(self):
        from dataclasses import dataclass as dc_dataclass

        from ErisPulse.Core.Bases import PollingAdapter
        from ErisPulse.Core.Bases.config_schema import BaseConfig

        class _Plain(PollingAdapter):
            poll_interval = 9.0

            async def fetch_events(self):
                return []

            def convert_one(self, raw):
                return None

            async def call_api(self, endpoint: str, **params):
                return None

        plain = _Plain()
        # 未声明 ConfigClass：直接取类属性
        assert plain._resolve_poll_interval() == 9.0

        @dc_dataclass
        class _Cfg(BaseConfig):
            poll_interval: float = 0.5

        class _WithCfg(_Plain):
            ConfigClass = _Cfg

        with_cfg = _WithCfg()
        from ErisPulse.Core.Bases import adapter as bases_adapter

        with patch.object(bases_adapter.config_mgr, "getConfig", return_value={"poll_interval": 0.5}):
            assert with_cfg._resolve_poll_interval() == 0.5
        # 配置值非法（非正数）时回退类属性
        with patch.object(bases_adapter.config_mgr, "getConfig", return_value={"poll_interval": 0}):
            assert with_cfg._resolve_poll_interval() == 9.0


# ==================== WebhookAdapter 行为契约 ====================


class TestWebhookAdapterBase:
    """半成品基类：路由注册（owner 归属）/ 处理器契约 / 生命周期默认实现"""

    @staticmethod
    def _make_adapter(convert_impl, verify_impl=None):
        from ErisPulse.Core.Bases import WebhookAdapter

        class _Hook(WebhookAdapter):
            _platform = "testhook"

            def convert(self, payload):
                return convert_impl(self, payload)

            async def call_api(self, endpoint: str, **params):
                return self.make_response()

            async def emit_event(self, event):
                self.emitted.append(event)

        if verify_impl is not None:
            _Hook.verify_request = verify_impl
        adapter = _Hook()
        adapter.emitted = []
        return adapter

    def test_abstract_convert_required(self):
        from ErisPulse.Core.Bases import WebhookAdapter

        with pytest.raises(TypeError):
            WebhookAdapter()  # pyright: ignore[reportAbstractUsage]

    def test_start_registers_route_under_owner(self, monkeypatch):
        from ErisPulse.Core.router import router
        from ErisPulse.runtime.context import get_current_owner

        registered: list[tuple] = []

        def _recorder(module_name, path, handler, methods=None, **kwargs):
            registered.append((module_name, path, methods, get_current_owner()))
            # 注册期间的 owner 上下文应指向平台（owner_scope 包裹）
            assert get_current_owner() == "testhook"

        monkeypatch.setattr(router, "register_http_route", _recorder)
        adapter = self._make_adapter(lambda _s, p: None)

        asyncio.run(adapter.start())
        assert registered == [("testhook", "/webhook", ["POST"], "testhook")]

    def test_handler_contract(self):
        adapter = self._make_adapter(
            lambda _s, p: {"type": "message", "id": "1"} if p.get("type") == "message" else None
        )

        async def scenario():
            # 合法载荷：转换 + 上报 + ok
            resp = await adapter._webhook_handler(_FakeRequest({"type": "message"}))
            assert resp == {"status": "ok"}
            assert adapter.emitted and adapter.emitted[0]["id"] == "1"

            # convert 返回 None：跳过上报但仍 ok
            resp = await adapter._webhook_handler(_FakeRequest({"type": "unknown"}))
            assert resp == {"status": "ok"}
            assert len(adapter.emitted) == 1

            # 载荷不可解析：400
            resp = await adapter._webhook_handler(_FakeRequest(bad_json=True))
            assert resp == ({"status": "bad request"}, 400)

            await adapter.shutdown()  # 默认空实现不炸

        asyncio.run(scenario())

    def test_handler_verify_rejected_403(self):
        adapter = self._make_adapter(
            lambda _s, p: {"type": "message"},
            verify_impl=lambda self, request: request.headers.get("auth") == "yes",
        )

        async def scenario():
            resp = await adapter._webhook_handler(_FakeRequest({}, headers={"auth": "no"}))
            assert resp == ({"status": "denied"}, 403)
            assert adapter.emitted == []  # 未过校验不进入转换

        asyncio.run(scenario())

    def test_verify_default_accepts(self):
        from ErisPulse.Core.Bases.adapter_patterns import HttpRequest

        adapter = self._make_adapter(lambda _s, p: None)
        assert adapter.verify_request(_FakeRequest()) is True

        # 注解存在且为框架 HttpRequest（路由注入依赖该类型识别）
        import inspect

        sig = inspect.signature(adapter.verify_request)
        assert sig.parameters["request"].annotation is HttpRequest


# ==================== 常量与导出契约 ====================


class TestExportsAndConstants:
    """新增常量 / 聚合导出完整性"""

    def test_constants_defined(self):
        from ErisPulse.Core.constants import (
            POLLING_ADAPTER_BACKOFF_BASE_SECS,
            POLLING_ADAPTER_BACKOFF_MAX_SECS,
            WEBHOOK_ADAPTER_PATH_PREFIX,
        )

        assert POLLING_ADAPTER_BACKOFF_BASE_SECS == 1.0
        assert POLLING_ADAPTER_BACKOFF_MAX_SECS == 60.0
        assert WEBHOOK_ADAPTER_PATH_PREFIX == "/webhook"

    @pytest.mark.parametrize(
        ("pkg", "name"),
        [
            ("ErisPulse.Core.Bases", "PollingAdapter"),
            ("ErisPulse.Core.Bases", "WebhookAdapter"),
        ],
    )
    def test_exported_from_aggregates(self, pkg, name):
        import importlib

        mod = importlib.import_module(pkg)
        assert hasattr(mod, name)
        assert name in mod.__all__

        import ErisPulse

        assert hasattr(ErisPulse, name)
        assert name in ErisPulse.__all__

    def test_base_classes_inherit_base_adapter(self):
        from ErisPulse.Core.Bases import BaseAdapter, PollingAdapter, WebhookAdapter

        assert issubclass(PollingAdapter, BaseAdapter)
        assert issubclass(WebhookAdapter, BaseAdapter)
