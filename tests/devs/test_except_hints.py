"""
ErisPulse 友好错误提示测试

模拟真实环境：sdk.run() 启动，全局异常 hook 自动处理未捕获异常。
每个测试用例在独立子进程中运行，互不影响。
"""

import subprocess
import sys

# 每个测试用例的代码（独立运行，异常不被 try/except 捕获，直接由全局 hook 处理）
CASES = [
    # === AttributeError ===
    {
        "name": "1. AttributeError — sdk.adaptr",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse import sdk
sdk.adaptr
""",
    },
    {
        "name": "2. AttributeError — sdk.ruter",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse import sdk
sdk.ruter
""",
    },
    # === ImportError ===
    {
        "name": "3. ImportError — from ErisPulse.Core import evnt",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse.Core import evnt
""",
    },
    {
        "name": "4. ImportError — import ErisPulse.Core.eventt",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import ErisPulse.Core.eventt
""",
    },
    # === KeyError ===
    {
        "name": "5. KeyError — config['adapter']",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
config = {"adapters": True, "modules": True, "logger": True}
config["adapter"]
""",
    },
    {
        "name": "6. KeyError — config['loger']",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
config = {"adapters": True, "modules": True, "logger": True}
config["loger"]
""",
    },
    # === NameError ===
    {
        "name": "7. NameError — prnit (→ print?)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
prnit("hello")
""",
    },
    # === RuntimeError (event_loop_closed hint) ===
    {
        "name": "8. RuntimeError — Event loop is closed",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
loop = asyncio.new_event_loop()
loop.close()
loop.run_until_complete(asyncio.sleep(0))
""",
    },
    # === TypeError (invalid_await hint) ===
    {
        "name": "9. TypeError — await 非协程对象 (invalid await)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
async def main():
    await 42
asyncio.run(main())
""",
    },
    # === TypeError (missing_argument hint) ===
    {
        "name": "10. TypeError — 缺少必需位置参数 (missing argument)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
def need_two(a, b):
    return a + b
need_two(1)
""",
    },
    # === TypeError (not_callable hint) ===
    {
        "name": "11. TypeError — int 不可调用 (not callable)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
x = 5
x()  # int 不可调用
""",
    },
    # === TypeError (not_subscriptable hint) ===
    {
        "name": "12. TypeError — None 不可下标 (not subscriptable)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
data = None
data["key"]  # NoneType 不可下标
""",
    },
    # === TypeError (not_iterable hint) ===
    {
        "name": "13. TypeError — int 不可迭代 (not iterable)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
for i in 42:
    pass
""",
    },
    # === RuntimeError (coroutine_never_awaited hint) ===
    {
        "name": "14. RuntimeError — 协程从未 await (coroutine never awaited)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
async def co():
    return 1
# 创建协程但不 await，触发 RuntimeWarning（部分环境包装为 RuntimeError）
co()
import gc
gc.collect()
""",
    },
    # === RuntimeError (no_event_loop hint) ===
    {
        "name": "15. RuntimeError — 没有当前事件循环 (no event loop)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
# 在没有运行中事件循环时调用 get_running_loop
asyncio.get_running_loop()
""",
    },
    # === RuntimeError (asyncio_run_in_loop hint) ===
    {
        "name": "16. RuntimeError — 在运行中的事件循环里调用 asyncio.run (asyncio.run in loop)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
async def outer():
    # 在已有事件循环中嵌套 asyncio.run，会报错
    asyncio.run(asyncio.sleep(0))
asyncio.run(outer())
""",
    },
    # === NameError (name_did_you_mean hint) ===
    {
        "name": "17. NameError — sdk 引用拼写错误 modlue (→ module?)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse import sdk
# modlue 是 module 的拼写错误
sdk.modlue
""",
    },
    # === RecursionError (recursion_error hint) ===
    {
        "name": "19. RecursionError — 无限递归 (recursion error)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import sys
sys.setrecursionlimit(100)
def recurse():
    return recurse()
recurse()
""",
    },
    # === TimeoutError (timeout_error hint) ===
    {
        "name": "20. TimeoutError — 异步超时 (timeout error)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
async def main():
    await asyncio.wait_for(asyncio.sleep(10), timeout=0.01)
asyncio.run(main())
""",
    },
    # === ConnectionError (connection_error hint) ===
    {
        "name": "21. ConnectionError — 连接被拒绝 (connection refused)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
import asyncio
async def main():
    # 连接一个几乎肯定没人监听的端口
    reader, writer = await asyncio.open_connection("127.0.0.1", 1)
asyncio.run(main())
""",
    },
    # === TypeError (not_iterable hint) ===
    {
        "name": "22. TypeError — 对 int 迭代 (not iterable)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
for x in 123:
    pass
""",
    },
    # === ErisPulse HTTPStatusError (http_client_error hint) ===
    {
        "name": "23. HTTPStatusError — 404 客户端错误 (http client error)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse.Core.Bases.errors import HTTPStatusError
raise HTTPStatusError(404, "Not Found")
""",
    },
    # === ErisPulse HTTPStatusError (http_server_error hint) ===
    {
        "name": "24. HTTPStatusError — 500 服务器错误 (http server error)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse.Core.Bases.errors import HTTPStatusError
raise HTTPStatusError(500, "Internal Server Error")
""",
    },
    # === ErisPulse ClientConnectionError (client_connection_error hint) ===
    {
        "name": "25. ClientConnectionError — 客户端连接失败 (client connection error)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse.Core.Bases.errors import ClientConnectionError
raise ClientConnectionError("DNS resolution failed")
""",
    },
    # === ErisPulse WebSocketDisconnect (正常关闭，不附加提示) ===
    {
        "name": "26. WebSocketDisconnect — 正常关闭 code=1000 (无提示，属生命周期事件)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse.Core.Bases.errors import WebSocketDisconnect
raise WebSocketDisconnect(1000, "Normal Closure")
""",
    },
    # === ErisPulse WebSocketDisconnect (异常断开，附加提示) ===
    {
        "name": "27. WebSocketDisconnect — 异常断开 code=1006 (websocket abnormal close)",
        "code": """
from ErisPulse.runtime import setup_exception_handling
setup_exception_handling()
from ErisPulse.Core.Bases.errors import WebSocketDisconnect
raise WebSocketDisconnect(1006, "Abnormal Closure")
""",
    },
]


def run_case(case):
    """在子进程中运行测试用例"""
    # 在子进程中设置 PYTHONIOENCODING=utf-8 确保输出编码一致
    import os

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, "-c", case["code"]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return result


print("=" * 60)
print("  ErisPulse 友好错误提示 — 真实环境测试")
print("=" * 60)

for case in CASES:
    print()
    print("-" * 60)
    print(case["name"])
    print("-" * 60)

    result = run_case(case)

    # 全局 hook 的日志输出可能在 stdout 或 stderr
    output = (result.stderr or "") + (result.stdout or "")
    if output.strip():
        for line in output.strip().splitlines():
            if line.strip():
                print(f"  {line}")
    else:
        print("  (无输出)")

    if result.returncode != 0:
        print(f"  [进程退出码: {result.returncode}]")

print()
print("=" * 60)
print("  测试完成")
print("=" * 60)
