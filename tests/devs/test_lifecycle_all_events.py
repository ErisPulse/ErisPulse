"""
生命周期事件数据验证测试

在真实 ErisPulse 环境中捕获全部 28 个标准事件，
输出每个事件的 data 内容，与文档定义进行对比验证。

使用方式：
    python tests/devs/test_lifecycle_all_events.py
"""

import asyncio
import signal

from ErisPulse import sdk

ALL_STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["register", "load", "init", "unload"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set"],
}

FULL_NAMES = []
for prefix, suffixes in ALL_STANDARD_EVENTS.items():
    for suffix in suffixes:
        FULL_NAMES.append(f"{prefix}.{suffix}")

captured: dict[str, list] = {name: [] for name in FULL_NAMES}


def make_handler(event_name):
    def handler(data):
        captured[event_name].append(data)
        count = len(captured[event_name])
        print(f"  [caught] {event_name} (x{count})")
        if count == 1:
            print(f"    data: {_truncate(data)}")
    return handler


def _truncate(obj, max_len=200):
    s = str(obj)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


for _name in FULL_NAMES:
    sdk.lifecycle.on(_name)(make_handler(_name))


@sdk.lifecycle.on("*", priority=-1000)
def wildcard(data):
    if not isinstance(data, dict):
        return
    event_name = data.get("event", "")
    if event_name and event_name in captured and not captured[event_name]:
        captured[event_name].append(data)
        print(f"  [caught via *] {event_name} (x1)")
        print(f"    data: {_truncate(data)}")


def print_event_report():
    print("\n" + "=" * 60)
    print("  事件数据验证报告")
    print("=" * 60)

    DOC = {
        "core.init.start": "空或无特殊字段",
        "core.init.complete": "duration, success, adapters{enabled,disabled}, modules{enabled,disabled}",
        "core.uninit.complete": "duration, success, adapters_closed, modules_unloaded, module_properties_cleared",
        "module.register": "module_name, success",
        "module.load": "module_name, success",
        "module.init": "module_name, success",
        "module.unload": "module_name, success",
        "adapter.load": "platform, success",
        "adapter.start": "platforms",
        "adapter.status.change": "platform, status, retry_count?",
        "adapter.stop": "platforms",
        "adapter.stopped": "platforms",
        "adapter.event.receive": "platform, event_type, raw_event_type",
        "adapter.event.dispatched": "platform, event_type, raw_event_type, onebot_handlers_count",
        "adapter.bot.online": "platform, bot_id, info, status",
        "adapter.bot.offline": "platform, bot_id, status",
        "server.start": "base_url, host, port",
        "server.stop": "无特殊字段",
        "server.request": "method, path, client_ip",
        "server.response": "method, path, status_code, client_ip",
        "server.websocket.connect": "path, module_name, client_ip",
        "server.websocket.disconnect": "path, module_name, reason, error?",
        "event.pre_process": "event_type, platform, detail_type",
        "message.sending": "platform, method, detail_type, target_id, bot_id",
        "message.sent": "platform, method, detail_type, target_id, bot_id",
        "command.matched": "command, args, platform, user_id",
        "command.executed": "command, args, platform, user_id, success, error?",
        "config.set": "key, old_value, new_value",
    }

    total = len(FULL_NAMES)
    ok = 0
    for name in FULL_NAMES:
        items = captured[name]
        count = len(items)
        if count:
            ok += 1

        status = f"OK (x{count})" if count else "MISS"
        print(f"\n  [{status:>10}] {name}")
        print(f"    文档字段: {DOC.get(name, '?')}")

        if items:
            sample = items[0]
            if isinstance(sample, dict) and "data" in sample and isinstance(sample["data"], dict):
                data = sample["data"]
            elif isinstance(sample, dict):
                data = sample
            else:
                data = sample
            print(f"    实际数据: {_truncate(data, 300)}")

    miss = total - ok
    print(f"\n{'=' * 60}")
    print(f"  总计: {total} 个, 已触发: {ok}, 未触发: {miss}")
    if miss:
        missed = [n for n in FULL_NAMES if not captured[n]]
        print(f"  未触发: {', '.join(missed)}")
    else:
        print("\n  所有事件均已成功触发!")
    print("=" * 60)


def print_guide():
    print("\n" + "=" * 60)
    print("  请手动触发以下事件")
    print("=" * 60)
    print("""
  1. 通过适配器平台发送一条私聊消息
     -> adapter.event.receive, adapter.event.dispatched
     -> event.pre_process, adapter.bot.online

  2. 让 Bot 回复消息 或 发送带命令前缀的消息 (如 /echo xxx)
     -> message.sending, message.sent
     -> command.matched, command.executed

  3. 访问 Dashboard 页面 (HTTP 请求)
     -> server.request, server.response

  4. 连接/断开 WebSocket
     -> server.websocket.connect, server.websocket.disconnect

  完成后按 Ctrl+C 停止。
""")


async def auto_trigger():
    print("\n--- 自动触发: config.set ---")
    sdk.config.setConfig("_test.lifecycle", "auto_trigger")

    print("\n--- 自动触发: server.request + server.response ---")
    try:
        import urllib.request

        from ErisPulse.runtime import get_server_config
        sc = get_server_config()
        url = f"http://{sc['host']}:{sc['port']}/health"
        try:
            with urllib.request.urlopen(url, timeout=3):
                pass
        except Exception:
            pass
    except Exception:
        pass

    await asyncio.sleep(0.3)


_keep_running = True


def _signal_handler(sig, frame):
    global _keep_running
    _keep_running = False
    raise KeyboardInterrupt


async def main():
    global _keep_running

    print("=" * 60)
    print("  生命周期事件数据验证测试")
    print("=" * 60)

    success = await sdk.init()
    if not success:
        print("SDK 初始化失败，退出")
        return

    await auto_trigger()
    print_guide()

    try:
        while _keep_running:
            await asyncio.sleep(0.5)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    print("\n  正在反初始化...")
    try:
        await sdk.uninit()
    except Exception as e:
        print(f"  uninit 异常: {e}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print_event_report()
