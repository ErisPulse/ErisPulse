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
