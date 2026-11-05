"""
影子 whl 摄取与「转正并持久化」单元测试

覆盖：whl 校验（扩展名 / PEP 427 文件名 / 大小 / ZipSlip）、原件落盘、
source 推导、persist 路径越界拒绝、promote 失败不安装、后台 pip 任务状态。
"""

import asyncio
import io
import zipfile
from pathlib import Path

import pytest

from ErisPulse.Core.Bases.errors import ShadowSourceError
from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.shadow import shadow_manager


@pytest.fixture(autouse=True)
def _clean_shadow_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shadow_manager._shadows.clear()
    shadow_manager._persist_tasks.clear()
    yield
    shadow_manager._shadows.clear()
    shadow_manager._persist_tasks.clear()


def _make_whl(dist: str = "fakepkg") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{dist}/__init__.py", "VALUE = 1\n")
    return buf.getvalue()


class TestIngestWhl:
    def test_happy_path(self):
        data = _make_whl()
        result = shadow_manager.ingest_whl(
            "MyModule", data, "fakepkg-1.0.0-py3-none-any.whl"
        )
        source = Path(result["source"])
        whl_path = Path(result["whl_path"])
        assert (source / "__init__.py").exists()
        assert whl_path.is_file()
        assert whl_path.read_bytes() == data
        assert whl_path.parent.name == "MyModule"

    def test_rejects_non_whl(self):
        with pytest.raises(ShadowSourceError, match="only .whl"):
            shadow_manager.ingest_whl("MyModule", b"x", "pkg.zip")

    def test_rejects_bad_wheel_name(self):
        with pytest.raises(ShadowSourceError, match="wheel filename"):
            shadow_manager.ingest_whl("MyModule", _make_whl(), "bad.whl")

    def test_rejects_invalid_module_name(self):
        with pytest.raises(ShadowSourceError, match="module name"):
            shadow_manager.ingest_whl("..", _make_whl(), "fakepkg-1.0.0-py3-none-any.whl")

    def test_rejects_oversize(self, monkeypatch):
        monkeypatch.setattr("ErisPulse.Core.shadow.SHADOW_WHL_MAX_BYTES", 4)
        with pytest.raises(ShadowSourceError, match="too large"):
            shadow_manager.ingest_whl(
                "MyModule", _make_whl(), "fakepkg-1.0.0-py3-none-any.whl"
            )

    def test_rejects_zip_slip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.py", "x = 1\n")
        with pytest.raises(ShadowSourceError, match="unsafe entry"):
            shadow_manager.ingest_whl(
                "MyModule", buf.getvalue(), "fakepkg-1.0.0-py3-none-any.whl"
            )

    def test_module_manager_wrapper(self):
        result = ModuleManager().shadow_ingest_whl(
            "MyModule", data=_make_whl(), filename="fakepkg-1.0.0-py3-none-any.whl"
        )
        assert Path(result["whl_path"]).is_file()


class TestValidatePersistWhl:
    def test_rejects_missing_file(self):
        with pytest.raises(ShadowSourceError, match="not found"):
            shadow_manager.validate_persist_whl(
                "MyModule", Path.cwd() / "shadows" / "MyModule" / "ghost.whl"
            )

    def test_rejects_outside_shadows_dir(self, tmp_path):
        outside = Path.cwd() / "evil.whl"
        outside.write_bytes(_make_whl())
        with pytest.raises(ShadowSourceError, match="outside"):
            shadow_manager.validate_persist_whl("MyModule", outside)

    def test_accepts_ingested_whl(self):
        result = shadow_manager.ingest_whl(
            "MyModule", _make_whl(), "fakepkg-1.0.0-py3-none-any.whl"
        )
        validated = shadow_manager.validate_persist_whl("MyModule", result["whl_path"])
        assert validated.is_file()


class TestPromotePersist:
    def test_promote_failure_skips_install(self, monkeypatch):
        manager = ModuleManager()

        async def failing_promote(name):
            return False

        started = []
        monkeypatch.setattr(manager, "promote_shadow", failing_promote)
        monkeypatch.setattr(
            shadow_manager, "start_persist", lambda path: started.append(path) or {}
        )
        result = shadow_manager.ingest_whl(
            "MyModule", _make_whl(), "fakepkg-1.0.0-py3-none-any.whl"
        )
        outcome = asyncio.run(
            manager.shadow_promote_persist("MyModule", whl_path=result["whl_path"])
        )
        assert outcome["promoted"] is False
        assert started == []

    def test_promote_success_starts_persist(self, monkeypatch):
        manager = ModuleManager()

        async def ok_promote(name):
            return True

        monkeypatch.setattr(manager, "promote_shadow", ok_promote)

        class _FakeThread:
            def __init__(self, target, args, daemon=None):
                self.target = target
                self.args = args

            def start(self):
                self.target(*self.args)

        monkeypatch.setattr("ErisPulse.Core.shadow.threading.Thread", _FakeThread)
        result = shadow_manager.ingest_whl(
            "MyModule", _make_whl(), "fakepkg-1.0.0-py3-none-any.whl"
        )
        outcome = asyncio.run(
            manager.shadow_promote_persist("MyModule", whl_path=result["whl_path"])
        )
        assert outcome["promoted"] is True
        assert outcome["task_id"].startswith("sp_")

    def test_persist_status_records_failure(self, monkeypatch):
        monkeypatch.setattr("ErisPulse.Core.shadow.SHADOW_PIP_TIMEOUT_SECS", 5)
        monkeypatch.setattr(
            "ErisPulse.Core.shadow.subprocess.Popen", _FailingPopen
        )
        task = shadow_manager.start_persist(Path("unused.whl"))
        for _ in range(100):
            status = shadow_manager.persist_status(task["task_id"])
            if status and status["status"] == "error":
                break
            import time as _time

            _time.sleep(0.01)
        assert shadow_manager.persist_status(task["task_id"])["status"] == "error"


class _FailingPopen:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("no pip")
