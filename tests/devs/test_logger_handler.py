"""
日志订阅系统手动测试

运行方式：ep r tests/devs/test_logger_handler.py

测试内容：
1. 注册订阅器并接收实时日志
2. 等级筛选（min_level）
3. 历史日志补发
4. 移除订阅器
"""

import asyncio

from ErisPulse import sdk


async def test_log_handler():
    """运行日志订阅系统测试"""

    print("\n=== 日志订阅系统测试 ===\n")

    # ---- 1. 装饰器方式注册全等级订阅器 ----
    logs_received = []

    @sdk.logger.handler("test-all", min_level="TRACE")
    def on_all_logs(log_data: dict):
        logs_received.append(log_data)
        print(
            f"[订阅器-全部] [{log_data['level']:>8}] [{log_data['module']}] {log_data['message']}"
        )

    print("[*] 已注册 'test-all' 订阅器（TRACE，接收全部）")

    # ---- 2. 装饰器方式注册 ERROR 级订阅器 ----
    @sdk.logger.handler("test-error", min_level="ERROR")
    def on_error_only(log_data: dict):
        print(f"[订阅器-错误] [{log_data['module']}] {log_data['message']}")

    print("[*] 已注册 'test-error' 订阅器（ERROR 及以上）")

    # ---- 3. 触发各级别日志 ----
    sdk.logger.trace("这是一条 TRACE 级别日志（最细粒度）")
    sdk.logger.debug("这是一条 DEBUG 级别日志")
    sdk.logger.info("这是一条 INFO 级别日志")
    sdk.logger.warning("这是一条 WARNING 级别日志")
    sdk.logger.error("这是一条 ERROR 级别日志")
    sdk.logger.critical("这是一条 CRITICAL 级别日志")

    await asyncio.sleep(0.1)  # 等推送完成

    # ---- 4. 验证等级筛选 ----
    error_logs = [log for log in logs_received if log["level"] in ("ERROR", "CRITICAL")]
    all_count = len(logs_received)
    error_count = len(error_logs)
    print(f"\n[*] 全部订阅器收到 {all_count} 条日志")
    print(f"[*] 其中 ERROR/CRITICAL 级别 {error_count} 条（应被两个订阅器都收到）")

    # ---- 5. 测试移除 ----
    sdk.logger.remove_handler("test-error")
    print("\n[*] 已移除 'test-error' 订阅器")

    sdk.logger.warning("这条 WARNING 只应被 'test-all' 收到")
    await asyncio.sleep(0.1)
    print(f"[*] 移除后全部订阅器共收到 {len(logs_received)} 条日志")

    # ---- 6. 测试历史补发 ----
    backlog_logs = []

    @sdk.logger.handler("test-backlog", min_level="INFO")
    def on_backlog(log_data: dict):
        backlog_logs.append(log_data)

    print(
        f"\n[*] 注册 'test-backlog' 订阅器（INFO+），补发了 {len(backlog_logs)} 条历史日志"
    )
    assert len(backlog_logs) > 0, "历史补发应收到之前产生的日志"

    # ---- 7. 结构化字段验证 ----
    sample = logs_received[0]
    required_keys = {"timestamp", "level", "level_num", "module", "message"}
    missing = required_keys - sample.keys()
    if missing:
        print(f"[✘] 日志 dict 缺少字段: {missing}")
    else:
        print(f"[✓] 日志 dict 结构正确: {required_keys}")
        print(
            f"    示例: level={sample['level']}, level_num={sample['level_num']}, module={sample['module']}"
        )

    # ---- 8. 清理 ----
    sdk.logger.remove_handler("test-all")
    sdk.logger.remove_handler("test-backlog")
    print("\n[*] 所有订阅器已清理")

    print("\n=== 测试完成 ===\n")
    sdk.logger.info("日志订阅系统测试通过")


# ---- 入口 ----
if __name__ == "__main__":
    asyncio.run(test_log_handler())
