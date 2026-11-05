"""
开发模式细粒度热重载监控单元测试

覆盖目标分派、去重、插件忽略与重启分支。
"""

import asyncio

from ErisPulse.runtime import dev_watch
from ErisPulse.runtime.reload_target import ReloadTarget


class _FakeSdk:
    def __init__(self, supervised: bool = True):
        self.calls: list[tuple] = []
        self._supervised = supervised

    def is_supervised(self) -> bool:
        return self._supervised

    async def reload_module(self, name: str) -> bool:
        self.calls.append(("module", name))
        return True

    async def reload_adapter(self, name: str) -> bool:
        self.calls.append(("adapter", name))
        return True

    async def restart(self) -> bool:
        self.calls.append(("restart",))
        return True

    async def hard_restart(self, reason: str = "") -> bool:
        self.calls.append(("hard_restart", reason))
        return True


def _handler(sdk: _FakeSdk) -> dev_watch.DevReloadHandler:
    return dev_watch.DevReloadHandler(None, sdk)  # type: ignore[arg-type]


class TestApply:
    async def test_module(self):
        sdk = _FakeSdk()
        await _handler(sdk)._apply(ReloadTarget("module", "MyMod"))
        assert sdk.calls == [("module", "MyMod")]

    async def test_adapter(self):
        sdk = _FakeSdk()
        await _handler(sdk)._apply(ReloadTarget("adapter", "MyAdapter"))
        assert sdk.calls == [("adapter", "MyAdapter")]

    async def test_restart_supervised(self):
        sdk = _FakeSdk(supervised=True)
        await _handler(sdk)._apply(
            ReloadTarget("restart", reason="framework")
        )
        assert sdk.calls == [("hard_restart", "framework")]

    async def test_restart_unsupervised(self):
        sdk = _FakeSdk(supervised=False)
        await _handler(sdk)._apply(
            ReloadTarget("restart", reason="entry")
        )
        assert sdk.calls == [("restart",)]


class TestDispatch:
    def test_dedup_module_targets(self, monkeypatch):
        sdk = _FakeSdk()
        handler = _handler(sdk)
        monkeypatch.setattr(
            dev_watch,
            "classify_reload_path",
            lambda path, sdk, entry_paths=(): ReloadTarget(
                "module", "MyMod"
            ),
        )
        captured = {}

        def fake_submit(coro, loop):
            captured["coro"] = coro

        monkeypatch.setattr(
            dev_watch.asyncio, "run_coroutine_threadsafe", fake_submit
        )
        handler._dispatch({"a.py", "b.py"})
        asyncio.run(captured["coro"])
        assert sdk.calls == [("module", "MyMod")]

    def test_plugin_targets_ignored(self, monkeypatch):
        sdk = _FakeSdk()
        handler = _handler(sdk)
        monkeypatch.setattr(
            dev_watch,
            "classify_reload_path",
            lambda path, sdk, entry_paths=(): ReloadTarget(
                "plugin", "dice"
            ),
        )
        submitted = []
        monkeypatch.setattr(
            dev_watch.asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: submitted.append(coro),
        )
        handler._dispatch({"plugins/dice.py"})
        assert submitted == []
        assert sdk.calls == []

    def test_mixed_targets(self, monkeypatch):
        sdk = _FakeSdk()
        handler = _handler(sdk)

        def fake_classify(path, sdk, entry_paths=()):
            if path.endswith("a.py"):
                return ReloadTarget("module", "ModA")
            return ReloadTarget("adapter", "AdpB")

        monkeypatch.setattr(
            dev_watch, "classify_reload_path", fake_classify
        )
        captured = {}
        monkeypatch.setattr(
            dev_watch.asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: captured.setdefault("coro", coro),
        )
        handler._dispatch({"a.py", "b.py"})
        asyncio.run(captured["coro"])
        assert ("module", "ModA") in sdk.calls
        assert ("adapter", "AdpB") in sdk.calls
