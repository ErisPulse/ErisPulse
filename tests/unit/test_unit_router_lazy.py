"""
路由 Web 栈懒加载单元测试

验证 FastAPI / Uvicorn / Starlette 不在导入期被加载，仅在路由实际服务时按需加载。
"""

import subprocess
import sys
from pathlib import Path

from ErisPulse.Core.router import RouterManager, _load_web_stack

SRC_DIR = str(Path(__file__).resolve().parents[2] / "src")


def _web_modules_loaded() -> bool:
    """当前进程是否已加载 web 栈任一模块"""
    return any(
        m.split(".")[0] in ("fastapi", "uvicorn", "starlette")
        for m in sys.modules
    )


class TestWebStackLazyLoad:
    """Web 栈懒加载测试"""

    def test_web_stack_not_loaded_on_router_import(self):
        """导入 router 模块时不应拉起 fastapi/uvicorn/starlette（子进程隔离验证）"""
        code = (
            "import sys;"
            f"sys.path.insert(0, r'{SRC_DIR}');"
            "import ErisPulse.Core.router;"
            "loaded = [m for m in sys.modules if m.split('.')[0] "
            "in ('fastapi', 'uvicorn', 'starlette')];"
            "print('LOADED', len(loaded))"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=False,
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )
        assert result.returncode == 0, result.stderr
        assert "LOADED 0" in result.stdout, (
            f"router 导入不应加载 web 栈，实际: {result.stdout!r}"
        )

    def test_router_manager_app_is_lazy(self):
        """RouterManager 实例化时不应创建 FastAPI app"""
        manager = RouterManager()
        assert manager._app is None

    def test_app_property_materializes(self):
        """首次访问 app 属性时才创建 FastAPI 实例"""
        manager = RouterManager()
        assert manager._app is None
        _ = manager.app
        assert manager._app is not None

    def test_load_web_stack_is_idempotent(self):
        """_load_web_stack 幂等：重复调用不重复导入"""
        import sys

        _load_web_stack()
        router_mod = sys.modules["ErisPulse.Core.router"]
        assert router_mod._WEB_STACK_LOADED is True
        # 第二次调用应直接返回，不抛异常
        _load_web_stack()
        assert router_mod._WEB_STACK_LOADED is True

    def test_get_app_returns_materialized_app(self):
        """get_app 返回惰性创建后的 app 实例"""
        manager = RouterManager()
        app = manager.get_app()
        assert app is manager._app
        assert app is not None


class TestServerAutoStartConfig:
    """server.auto_start 配置测试"""

    def test_default_config_has_auto_start_true(self):
        """默认配置应包含 server.auto_start = True（向后兼容）"""
        from ErisPulse.runtime.frame_config import DEFAULT_ERISPULSE_CONFIG

        server_cfg = DEFAULT_ERISPULSE_CONFIG["server"]
        assert "auto_start" in server_cfg
        assert server_cfg["auto_start"] is True
