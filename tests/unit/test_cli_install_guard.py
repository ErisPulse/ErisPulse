"""epsdk install 未知包守卫测试"""

import pytest

from ErisPulse.CLI.utils.package_manager import PackageManager


@pytest.fixture
def pm(monkeypatch) -> PackageManager:
    """隔离外部交互的 PackageManager：别名/索引/uv 联动全部置空"""
    pm = PackageManager()

    async def _no_alias(name):
        return None

    async def _no_info(name):
        return None

    monkeypatch.setattr(pm, "_find_package_by_alias", _no_alias)
    monkeypatch.setattr(pm, "_get_package_info", _no_info)
    monkeypatch.setattr(pm, "_uv_project_link_active", lambda: False)
    return pm


def test_unknown_package_requires_confirm_and_cancels(pm, monkeypatch):
    """索引外包名默认拒装：确认框取消 → 不执行 pip"""
    pip_calls = []
    monkeypatch.setattr(
        pm, "_run_pip_command_with_output", lambda cmd, msg: pip_calls.append(cmd) or True
    )
    monkeypatch.setattr(
        "ErisPulse.CLI.utils.package_manager.confirm", lambda msg, **k: False
    )
    assert pm.install_package(["not-in-index-pkg"]) is False
    assert pip_calls == []


def test_unknown_package_installs_after_confirm(pm, monkeypatch):
    """索引外包名确认后照常安装"""
    pip_calls = []
    monkeypatch.setattr(
        pm, "_run_pip_command_with_output", lambda cmd, msg: pip_calls.append(cmd) or True
    )
    monkeypatch.setattr(
        "ErisPulse.CLI.utils.package_manager.confirm", lambda msg, **k: True
    )
    assert pm.install_package(["not-in-index-pkg"]) is True
    assert pip_calls and pip_calls[0][-1] == "not-in-index-pkg"


def test_indexed_verified_package_skips_confirm(pm, monkeypatch):
    """索引内已验证包不触发未知包确认"""

    async def _info(name):
        return {"verified": True}

    monkeypatch.setattr(pm, "_get_package_info", _info)
    confirm_called = []
    monkeypatch.setattr(
        "ErisPulse.CLI.utils.package_manager.confirm",
        lambda msg, **k: confirm_called.append(msg) or True,
    )
    pip_calls = []
    monkeypatch.setattr(
        pm, "_run_pip_command_with_output", lambda cmd, msg: pip_calls.append(cmd) or True
    )
    assert pm.install_package(["known-pkg"]) is True
    assert confirm_called == []
    assert pip_calls
