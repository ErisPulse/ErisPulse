"""
根导入契约冒烟测试（2.10+）

验证根命名空间的公共 API 可达性与一致性：
- 深路径与根导入拿到同一对象（兼容契约）
- __all__ 与实际属性一一对应
"""

import ErisPulse


def test_root_import_new_api():
    """2.10 新增面全部根可达"""
    from ErisPulse import (  # noqa: F401
        BroadcastResult,
        ConnectionManager,
        ConnectionNotFoundError,
        ConnectionPermissionError,
        ConnectionRegistryError,
        connections,
        respond,
        run_main_loop,
        spawn_later,
        spawn_thread,
        transcript,
    )


def test_root_and_deep_path_same_object():
    """根导入与深路径是同一对象（深路径永久兼容）"""
    assert ErisPulse.connections is ErisPulse.Core.connections
    assert ErisPulse.client is ErisPulse.Core.client
    assert ErisPulse.respond is ErisPulse.Core.Bases.respond
    assert ErisPulse.WebSocketConnection is ErisPulse.Core.Bases.WebSocketConnection
    assert ErisPulse.WSMessage is ErisPulse.Core.Bases.WSMessage
    assert ErisPulse.ConnectionRegistryError is ErisPulse.Core.Bases.ConnectionRegistryError
    assert ErisPulse.transcript is ErisPulse.Core.transcript
    assert ErisPulse.run_main_loop is ErisPulse.runtime.run_main_loop
    assert ErisPulse.command is ErisPulse.Core.Event.command
    assert ErisPulse.BaseModel is ErisPulse.Core.Bases.BaseModel


def test_all_matches_namespace():
    """__all__ 无缺失、无未定义符号"""
    missing = [name for name in ErisPulse.__all__ if not hasattr(ErisPulse, name)]
    assert missing == []


def test_lazy_web_stack_not_loaded():
    """根导入不触发 fastapi/uvicorn（懒加载纪律，子进程隔离验证）"""
    import os
    import subprocess
    import sys
    from pathlib import Path

    src = Path(__file__).parents[2] / "src"
    env = {**os.environ, "PYTHONPATH": str(src)}
    code = (
        "import sys; import ErisPulse; "
        "assert 'fastapi' not in sys.modules, 'fastapi loaded'; "
        "assert 'uvicorn' not in sys.modules, 'uvicorn loaded'"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60
    )
    assert result.returncode == 0, result.stderr
