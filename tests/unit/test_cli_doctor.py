"""doctor 命令安全体检项测试"""

import pytest

from ErisPulse.CLI.commands.doctor import DoctorCommand


@pytest.fixture
def doctor() -> DoctorCommand:
    return DoctorCommand()


def test_security_rows_warn_on_default_host(doctor, tmp_path):
    """默认 0.0.0.0 监听 → 两条 WARN（监听 + 文档端点）"""
    cfg = tmp_path / "config.toml"
    cfg.write_text('[ErisPulse.server]\nhost = "0.0.0.0"\n', encoding="utf-8")
    rows = doctor._security_rows(cfg)
    assert len(rows) == 2
    assert all(status == doctor._warn() for status, _, _ in rows)


def test_security_rows_ok_on_local_host(doctor, tmp_path):
    """显式回环地址 → 两条 OK"""
    cfg = tmp_path / "config.toml"
    cfg.write_text('[ErisPulse.server]\nhost = "127.0.0.1"\n', encoding="utf-8")
    rows = doctor._security_rows(cfg)
    assert len(rows) == 2
    assert all(status == doctor._status(True) for status, _, _ in rows)
    assert "127.0.0.1" in rows[0][2]


def test_security_rows_defaults_without_config(doctor, tmp_path):
    """配置文件缺失 → 按框架默认值（0.0.0.0）警示"""
    rows = doctor._security_rows(tmp_path / "missing.toml")
    assert len(rows) == 2
    assert rows[0][0] == doctor._warn()


def test_security_rows_unreadable_config(doctor, tmp_path):
    """配置不可读 → 单条跳过警示，不抛异常"""
    cfg = tmp_path / "config.toml"
    cfg.write_text("not [valid toml", encoding="utf-8")
    rows = doctor._security_rows(cfg)
    assert len(rows) == 1
    assert rows[0][0] == doctor._warn()
