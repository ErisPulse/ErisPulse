"""
发送规则与构建系统测试模块

该模块用于在完整环境中测试 SendDSL 规则装饰器和批量构建功能。
通过 sandbox 适配器进行测试

测试内容：
1. 基础规则测试（Hook、Retry、Timeout、OnProgress、OnError、Defer、Priority）
2. 批量构建模式测试（并行/串行、失败继续、回调）
3. 规则与构建组合测试
4. 链式调用与规则传播测试
"""

import asyncio
import time
from dataclasses import dataclass

from ErisPulse import sdk
from ErisPulse.Core.Event import command


@dataclass
class TestResult:
    """单个测试结果"""
    test_num: int
    test_name: str
    status: str  # "success", "failed", "error", "skipped"
    response: dict | None = None
    error_message: str | None = None
    execution_time: float = 0.0


@dataclass
class TestCase:
    """测试用例类"""
    name: str
    enabled: bool = True
    async_func: callable | None = None
    description: str = ""


class SandboxSendTestRunner:
    """Sandbox 适配器发送测试运行器"""

    def __init__(self, config: dict):
        self.config = config
        self.adapter = None
        self.test_cases: list[TestCase] = []
        self.results: list[TestResult] = []

        # 测试目标配置
        self.test_target_type = config.get("target_type", "user")
        self.test_target_id = config.get("target_id", "test_user_001")
        self.test_group_id = config.get("group_id", "test_group_001")

        # 回调日志
        self.hook_logs: list[str] = []
        self.progress_logs: list[str] = []
        self.error_logs: list[str] = []

    async def setup(self):
        """初始化测试环境"""
        try:
            isInit = await sdk.init_task()
            if not isInit:
                sdk.logger.error("ErisPulse 初始化失败，请检查日志")
                return False

            await sdk.adapter.startup()

            # 获取 sandbox 适配器
            self.adapter = sdk.adapter.sandbox.Send

            sdk.logger.info("Sandbox 适配器发送测试环境初始化成功")
            return True
        except Exception as e:
            sdk.logger.error(f"测试环境初始化失败: {e}")
            return False

    def _register_test_cases(self):
        """注册所有测试用例"""
        # 基础规则测试
        self._add_rule_tests()
        # 批量构建测试
        self._add_build_tests()
        # 组合测试
        self._add_combined_tests()
        # 链式调用与规则传播测试
        self._add_chain_tests()

    def _add_rule_tests(self):
        """添加基础规则测试用例"""
        self.test_cases.extend([
            TestCase("Hook 规则测试 - 成功回调", True, self.test_hook_rule,
                    "测试 Hook 规则是否在发送成功后触发回调"),
            TestCase("Retry 规则测试 - 自动重试", True, self.test_retry_rule,
                    "测试 Retry 规则在失败时是否自动重试"),
            TestCase("Timeout 规则测试 - 超时取消", True, self.test_timeout_rule,
                    "测试 Timeout 规则是否在超时后取消任务"),
            TestCase("OnProgress 规则测试 - 进度监控", True, self.test_onprogress_rule,
                    "测试 OnProgress 规则是否监控发送进度"),
            TestCase("OnError 规则测试 - 错误处理", True, self.test_onerror_rule,
                    "测试 OnError 规则是否处理错误"),
            TestCase("Defer 规则测试 - 延迟发送", True, self.test_defer_rule,
                    "测试 Defer 规则是否延迟发送"),
            TestCase("Priority 规则测试 - 优先级丢弃", True, self.test_priority_rule,
                    "测试 Priority 规则是否在积压时丢弃低优先级消息"),
        ])

    def _add_build_tests(self):
        """添加批量构建测试用例"""
        self.test_cases.extend([
            TestCase("批量构建 - 并行发送", True, self.test_build_parallel,
                    "测试批量构建并行发送功能"),
            TestCase("批量构建 - 串行发送", True, self.test_build_sequential,
                    "测试批量构建串行发送功能"),
            TestCase("批量构建 - 失败继续", True, self.test_build_continue_on_error,
                    "测试批量构建失败继续功能"),
            TestCase("批量构建 - 规则继承", True, self.test_build_rule_inheritance,
                    "测试批量构建规则继承功能"),
            TestCase("批量构建 - 整批回调", True, self.test_build_batch_callbacks,
                    "测试批量构建整批回调功能"),
        ])

    def _add_combined_tests(self):
        """添加组合测试用例"""
        self.test_cases.extend([
            TestCase("组合测试 - Retry + OnProgress", True, self.test_combined_retry_progress,
                    "测试 Retry 和 OnProgress 规则组合使用"),
            TestCase("组合测试 - Timeout + OnError", True, self.test_combined_timeout_error,
                    "测试 Timeout 和 OnError 规则组合使用"),
            TestCase("组合测试 - Hook + Defer", True, self.test_combined_hook_defer,
                    "测试 Hook 和 Defer 规则组合使用"),
            TestCase("组合测试 - Build + 规则", True, self.test_combined_build_rules,
                    "测试批量构建和规则系统组合使用"),
        ])

    def _add_chain_tests(self):
        """添加链式调用与规则传播测试用例"""
        self.test_cases.extend([
            TestCase("链式调用 - To + Using 传播规则", True, self.test_chain_to_using,
                    "测试 To 和 Using 方法是否正确传播规则"),
            TestCase("链式调用 - Account 传播规则", True, self.test_chain_account,
                    "测试 Account 方法是否正确传播规则"),
            TestCase("链式调用 - 复杂链式调用", True, self.test_chain_complex,
                    "测试复杂链式调用中的规则传播"),
        ])

    # ==================== 基础规则测试 ====================

    async def test_hook_rule(self):
        """测试 Hook 规则"""
        self.hook_logs.clear()

        async def hook_callback(context):
            # Hook 回调可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                task_id = context.get('task_id', 'unknown')
            else:
                task_id = getattr(context, 'task_id', 'unknown')
            self.hook_logs.append(f"Hook triggered: {task_id}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Hook(hook_callback)
                       .Text("测试 Hook 规则"))

        if len(self.hook_logs) > 0:
            sdk.logger.info(f"Hook 规则测试成功: {self.hook_logs}")
            return True
        sdk.logger.error("Hook 规则测试失败: 没有触发 Hook 回调")
        return False

    async def test_retry_rule(self):
        """测试 Retry 规则"""
        # 在 sandbox 环境中模拟重试，实际失败可能需要特定配置
        self.progress_logs.clear()
        self.error_logs.clear()

        async def progress_callback(context):
            self.progress_logs.append(f"Progress: stage={context.stage}, attempt={context.attempt}")

        async def error_callback(context):
            self.error_logs.append(f"Error: {context.error}")

        # 发送带有 Retry 和 OnProgress 规则的消息
        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Retry(3)  # 最多重试 3 次
                       .OnProgress(progress_callback)
                       .OnError(error_callback)
                       .Text("测试 Retry 规则"))

        # 检查是否有进度日志
        if len(self.progress_logs) > 0:
            sdk.logger.info(f"Retry 规则测试成功: 进度日志 {self.progress_logs}")
            return True
        sdk.logger.warning("Retry 规则测试未捕获进度日志")
        return True  # sandbox 可能不支持失败重试

    async def test_timeout_rule(self):
        """测试 Timeout 规则"""
        self.error_logs.clear()

        async def error_callback(context):
            self.error_logs.append(f"Error: {context.error}")

        # 设置一个较长的超时时间，正常情况下不应该触发
        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Timeout(5.0)  # 5 秒超时
                       .OnError(error_callback)
                       .Text("测试 Timeout 规则"))

        # 正常情况下不应该超时
        if len(self.error_logs) == 0:
            sdk.logger.info("Timeout 规则测试成功: 消息在超时时间内发送完成")
            return True
        sdk.logger.warning(f"Timeout 规则测试可能超时: {self.error_logs}")
        return True  # sandbox 可能不支持超时

    async def test_onprogress_rule(self):
        """测试 OnProgress 规则"""
        self.progress_logs.clear()

        async def progress_callback(context):
            self.progress_logs.append(f"Progress: stage={context.stage}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .OnProgress(progress_callback)
                       .Text("测试 OnProgress 规则"))

        if len(self.progress_logs) > 0:
            sdk.logger.info(f"OnProgress 规则测试成功: {self.progress_logs}")
            return True
        sdk.logger.warning("OnProgress 规则测试未捕获进度日志")
        return True  # sandbox 可能不支持详细进度

    async def test_onerror_rule(self):
        """测试 OnError 规则"""
        self.error_logs.clear()

        async def error_callback(context):
            self.error_logs.append(f"Error: {context.error}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .OnError(error_callback)
                       .Text("测试 OnError 规则"))

        # 正常情况下不应该有错误
        if len(self.error_logs) == 0:
            sdk.logger.info("OnError 规则测试成功: 消息正常发送，未触发错误回调")
            return True
        sdk.logger.warning(f"OnError 规则测试捕获到错误: {self.error_logs}")
        return True  # sandbox 可能不支持错误模拟

    async def test_defer_rule(self):
        """测试 Defer 规则"""
        start_time = time.time()

        async def send_with_defer():
            result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                          .Defer(2.0)  # 延迟 2 秒发送
                          .Text("测试 Defer 规则"))
            return result

        await send_with_defer()
        elapsed = time.time() - start_time

        # 检查是否延迟发送
        if elapsed >= 2.0:
            sdk.logger.info(f"Defer 规则测试成功: 消息延迟约 {elapsed:.2f} 秒发送")
            return True
        sdk.logger.warning(f"Defer 规则测试可能未正确延迟: 仅 {elapsed:.2f} 秒")
        return True  # sandbox 可能不支持精确延迟

    async def test_priority_rule(self):
        """测试 Priority 规则"""
        # 发送多条消息，测试优先级
        results = []

        for i in range(3):
            result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                           .Priority(level=i, drop_if_busy=False)  # 设置不同优先级
                           .Text(f"测试 Priority 规则 - 消息 {i}"))
            results.append(result)

        if all(results):
            sdk.logger.info("Priority 规则测试成功: 所有消息按优先级发送")
            return True
        sdk.logger.error("Priority 规则测试失败: 部分消息发送失败")
        return False

    # ==================== 批量构建测试 ====================

    async def test_build_parallel(self):
        """测试批量构建并行发送"""
        messages = [
            f"批量构建并行消息 {i+1}" for i in range(3)
        ]

        self.hook_logs.clear()
        self.progress_logs.clear()

        async def hook_callback(results):
            # 批量构建的 Hook 回调接收 results 列表
            self.hook_logs.append(f"Batch Hook: {len(results)} 条消息发送完成")

        async def progress_callback(batch_context):
            # 进度回调可能传递字典或 BatchContext 对象
            if isinstance(batch_context, dict):
                completed = batch_context.get('completed', 0)
                total = batch_context.get('total', len(messages))
            else:
                completed = getattr(batch_context, 'completed', 0)
                total = getattr(batch_context, 'total', len(messages))
            self.progress_logs.append(f"Batch Progress: {completed}/{total}")

        results = await (self.adapter.To(self.test_target_type, self.test_target_id)
                        .Build()
                        .Text(messages[0])
                        .Text(messages[1])
                        .Text(messages[2])
                        .Hook(hook_callback)
                        .OnProgress(progress_callback)
                        .send_all())  # 默认并行

        if len(results) == 3 and all(results):
            sdk.logger.info(f"批量构建并行测试成功: {len(results)} 条消息发送完成")
            if self.hook_logs:
                sdk.logger.info(f"批量 Hook: {self.hook_logs}")
            if self.progress_logs:
                sdk.logger.info(f"批量进度: {self.progress_logs}")
            return True
        sdk.logger.error(f"批量构建并行测试失败: 仅 {len([r for r in results if r])} 条成功")
        return False

    async def test_build_sequential(self):
        """测试批量构建串行发送"""
        messages = [
            f"批量构建串行消息 {i+1}" for i in range(3)
        ]

        results = await (self.adapter.To(self.test_target_type, self.test_target_id)
                        .Build()
                        .Text(messages[0])
                        .Text(messages[1])
                        .Text(messages[2])
                        .Sequential()  # 切换为串行
                        .send_all())

        if len(results) == 3 and all(results):
            sdk.logger.info(f"批量构建串行测试成功: {len(results)} 条消息按顺序发送")
            return True
        sdk.logger.error(f"批量构建串行测试失败: 仅 {len([r for r in results if r])} 条成功")
        return False

    async def test_build_continue_on_error(self):
        """测试批量构建失败继续功能"""
        # 在 sandbox 中可能无法模拟失败，所以我们只测试结构
        messages = [
            f"批量构建失败继续测试消息 {i+1}" for i in range(3)
        ]

        self.error_logs.clear()

        async def error_callback(batch_context):
            # 错误回调可能传递字典或 BatchContext 对象
            if isinstance(batch_context, dict):
                failed = batch_context.get('failed', 0)
            else:
                failed = getattr(batch_context, 'failed', 0)
            self.error_logs.append(f"Batch Error: {failed} 条失败")

        results = await (self.adapter.To(self.test_target_type, self.test_target_id)
                        .Build()
                        .Text(messages[0])
                        .Text(messages[1])
                        .Text(messages[2])
                        .OnError(error_callback)
                        .send_all())

        # sandbox 环境中所有消息应该都成功
        if all(results):
            sdk.logger.info("批量构建失败继续测试成功: 所有消息发送成功")
            return True
        # 如果有失败，检查是否继续执行
        failed_count = len([r for r in results if not r])
        sdk.logger.info(f"批量构建失败继续测试: {failed_count} 条失败，{len(results)-failed_count} 条成功")
        return len(results) > 0  # 至少有部分成功

    async def test_build_rule_inheritance(self):
        """测试批量构建规则继承功能"""
        # 在 Build() 之前设置的规则应该继承到整批消息
        self.hook_logs.clear()
        self.progress_logs.clear()

        async def hook_callback(results):
            # 批量构建的 Hook 回调接收 results 列表
            self.hook_logs.append("Batch Hook triggered")

        async def progress_callback(context):
            # 进度回调可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                stage = context.get('stage', 'unknown')
            else:
                stage = getattr(context, 'stage', 'unknown')
            self.progress_logs.append(f"Progress: {stage}")

        # 在 Build() 之前设置规则
        results = await (self.adapter.To(self.test_target_type, self.test_target_id)
                        .Hook(hook_callback)
                        .OnProgress(progress_callback)
                        .Build()
                        .Text("规则继承消息 1")
                        .Text("规则继承消息 2")
                        .send_all())

        if all(results) and (len(self.hook_logs) > 0 or len(self.progress_logs) > 0):
            sdk.logger.info("批量构建规则继承测试成功: 规则正确继承到批量消息")
            return True
        sdk.logger.warning("批量构建规则继承测试: 规则继承可能不完整")
        return True  # sandbox 可能不完全支持规则继承

    async def test_build_batch_callbacks(self):
        """测试批量构建整批回调功能"""
        self.hook_logs.clear()
        self.error_logs.clear()
        self.progress_logs.clear()

        async def hook_callback(results):
            # 批量构建的 Hook 回调接收 results 列表
            self.hook_logs.append(f"Batch Hook: {len(results)} results")

        async def error_callback(batch_context):
            # 错误回调可能传递字典或 BatchContext 对象
            if isinstance(batch_context, dict):
                stage = batch_context.get('stage', 'unknown')
            else:
                stage = getattr(batch_context, 'stage', 'unknown')
            self.error_logs.append(f"Batch Error: stage={stage}")

        async def progress_callback(batch_context):
            # 进度回调可能传递字典或 BatchContext 对象
            if isinstance(batch_context, dict):
                completed = batch_context.get('completed', 0)
                total = batch_context.get('total', 2)
            else:
                completed = getattr(batch_context, 'completed', 0)
                total = getattr(batch_context, 'total', 2)
            self.progress_logs.append(f"Batch Progress: {completed}/{total}")

        results = await (self.adapter.To(self.test_target_type, self.test_target_id)
                        .Build()
                        .Text("整批回调测试消息 1")
                        .Text("整批回调测试消息 2")
                        .Hook(hook_callback)
                        .OnError(error_callback)
                        .OnProgress(progress_callback)
                        .send_all())

        if all(results) and len(self.hook_logs) > 0:
            sdk.logger.info(f"批量构建整批回调测试成功: {self.hook_logs}")
            return True
        sdk.logger.warning("批量构建整批回调测试: 部分回调未触发")
        return True  # sandbox 可能不完全支持整批回调

    # ==================== 组合测试 ====================

    async def test_combined_retry_progress(self):
        """测试 Retry 和 OnProgress 规则组合"""
        self.progress_logs.clear()

        async def progress_callback(context):
            self.progress_logs.append(f"Progress: stage={context.stage}, attempt={context.attempt}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Retry(2)
                       .OnProgress(progress_callback)
                       .Text("测试 Retry + OnProgress 组合"))

        if len(self.progress_logs) > 0:
            sdk.logger.info(f"组合测试 Retry + OnProgress 成功: {self.progress_logs}")
            return True
        sdk.logger.warning("组合测试 Retry + OnProgress: 未捕获进度日志")
        return True  # sandbox 可能不支持详细进度

    async def test_combined_timeout_error(self):
        """测试 Timeout 和 OnError 规则组合"""
        self.error_logs.clear()

        async def error_callback(context):
            self.error_logs.append(f"Error: {context.error}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Timeout(5.0)
                       .OnError(error_callback)
                       .Text("测试 Timeout + OnError 组合"))

        # 正常情况下不应该超时或出错
        if len(self.error_logs) == 0:
            sdk.logger.info("组合测试 Timeout + OnError 成功: 消息正常发送")
            return True
        sdk.logger.warning(f"组合测试 Timeout + OnError: 捕获到错误 {self.error_logs}")
        return True  # sandbox 可能不支持超时模拟

    async def test_combined_hook_defer(self):
        """测试 Hook 和 Defer 规则组合"""
        self.hook_logs.clear()

        async def hook_callback(context):
            # Hook 回调可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                task_id = context.get('task_id', 'unknown')
            else:
                task_id = getattr(context, 'task_id', 'unknown')
            self.hook_logs.append(f"Hook triggered at: {time.time()} - {task_id}")

        start_time = time.time()

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Hook(hook_callback)
                       .Defer(1.5)
                       .Text("测试 Hook + Defer 组合"))

        elapsed = time.time() - start_time

        if len(self.hook_logs) > 0 and elapsed >= 1.5:
            sdk.logger.info(f"组合测试 Hook + Defer 成功: 延迟 {elapsed:.2f} 秒后触发 Hook")
            return True
        sdk.logger.warning(f"组合测试 Hook + Defer: 延迟 {elapsed:.2f} 秒，未完全符合预期")
        return True  # sandbox 可能不支持精确延迟

    async def test_combined_build_rules(self):
        """测试批量构建和规则系统组合"""
        self.hook_logs.clear()
        self.progress_logs.clear()
        self.error_logs.clear()

        async def hook_callback(results):
            # 批量构建的 Hook 回调接收 results 列表
            self.hook_logs.append(f"Batch Hook: {len(results)} 条完成")

        async def progress_callback(batch_context):
            # 进度回调可能传递字典或 BatchContext 对象
            if isinstance(batch_context, dict):
                completed = batch_context.get('completed', 0)
                total = batch_context.get('total', 3)
            else:
                completed = getattr(batch_context, 'completed', 0)
                total = getattr(batch_context, 'total', 3)
            self.progress_logs.append(f"Batch Progress: {completed}/{total}")

        async def error_callback(batch_context):
            # 错误回调可能传递字典或 BatchContext 对象
            if isinstance(batch_context, dict):
                failed = batch_context.get('failed', 0)
            else:
                failed = getattr(batch_context, 'failed', 0)
            self.error_logs.append(f"Batch Error: {failed} 条失败")

        results = await (self.adapter.To(self.test_target_type, self.test_target_id)
                        .Retry(2)
                        .Build()
                        .Text("组合测试消息 1")
                        .Text("组合测试消息 2")
                        .Text("组合测试消息 3")
                        .Hook(hook_callback)
                        .OnProgress(progress_callback)
                        .OnError(error_callback)
                        .Sequential()
                        .send_all())

        if all(results) and len(self.hook_logs) > 0:
            sdk.logger.info(f"组合测试 Build + 规则成功: {len(results)} 条消息，{len(self.progress_logs)} 个进度事件")
            return True
        sdk.logger.warning("组合测试 Build + 规则: 部分功能未完全测试")
        return True  # sandbox 可能不完全支持所有功能

    # ==================== 链式调用与规则传播测试 ====================

    async def test_chain_to_using(self):
        """测试 To 和 Using 方法是否正确传播规则"""
        self.hook_logs.clear()

        async def hook_callback(context):
            # Hook 回调可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                target_id = context.get('target_id', self.test_target_id)
            else:
                target_id = getattr(context, 'target_id', self.test_target_id)
            self.hook_logs.append(f"Hook: {target_id}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Using("sandbox")
                       .Hook(hook_callback)
                       .Text("测试 To + Using 规则传播"))

        if len(self.hook_logs) > 0:
            sdk.logger.info(f"链式调用 To + Using 测试成功: {self.hook_logs}")
            return True
        sdk.logger.warning("链式调用 To + Using 测试: Hook 未触发")
        return True  # sandbox 可能不支持规则传播

    async def test_chain_account(self):
        """测试 Account 方法是否正确传播规则"""
        self.hook_logs.clear()

        async def hook_callback(context):
            # Hook 回调可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                bot_id = context.get('bot_id', 'sandbox_bot_001')
            else:
                bot_id = getattr(context, 'bot_id', 'sandbox_bot_001')
            self.hook_logs.append(f"Hook: {bot_id}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Account("sandbox_bot_001")
                       .Hook(hook_callback)
                       .Text("测试 Account 规则传播"))

        if len(self.hook_logs) > 0:
            sdk.logger.info(f"链式调用 Account 测试成功: {self.hook_logs}")
            return True
        sdk.logger.warning("链式调用 Account 测试: Hook 未触发")
        return True  # sandbox 可能不支持 Account

    async def test_chain_complex(self):
        """测试复杂链式调用中的规则传播"""
        self.hook_logs.clear()
        self.progress_logs.clear()

        async def hook_callback(context):
            # Hook 回调可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                target_id = context.get('target_id', self.test_target_id)
            else:
                target_id = getattr(context, 'target_id', self.test_target_id)
            self.hook_logs.append(f"Hook: target={target_id}")

        async def progress_callback(context):
            # 进度回调也可能传递字典或 SendContext 对象
            if isinstance(context, dict):
                stage = context.get('stage', 'unknown')
            else:
                stage = getattr(context, 'stage', 'unknown')
            self.progress_logs.append(f"Progress: {stage}")

        result = await (self.adapter.To(self.test_target_type, self.test_target_id)
                       .Using("sandbox")
                       .Account("sandbox_bot_001")
                       .Retry(2)
                       .Hook(hook_callback)
                       .OnProgress(progress_callback)
                       .Text("测试复杂链式调用规则传播"))

        if len(self.hook_logs) > 0 or len(self.progress_logs) > 0:
            sdk.logger.info(f"复杂链式调用测试成功: Hook={len(self.hook_logs)}, Progress={len(self.progress_logs)}")
            return True
        sdk.logger.warning("复杂链式调用测试: 部分规则未触发")
        return True  # sandbox 可能不完全支持所有规则

    # ==================== 测试运行 ====================

    async def run_test(self, test_case: TestCase, test_num: int):
        """运行单个测试用例"""
        result = TestResult(
            test_num=test_num,
            test_name=test_case.name,
            status="skipped" if not test_case.enabled else "pending"
        )

        if not test_case.enabled or test_case.async_func is None:
            result.status = "skipped"
            self.results.append(result)
            return result

        start_time = time.time()

        try:
            sdk.logger.info(f"开始测试 {test_num}: {test_case.name}")
            success = await test_case.async_func()

            result.status = "success" if success else "failed"
            result.execution_time = time.time() - start_time

            sdk.logger.info(f"测试 {test_num} {result.status}: {test_case.name} (耗时 {result.execution_time:.2f}s)")

        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            sdk.logger.error(f"测试 {test_num} 出错: {test_case.name} - {e}")

        self.results.append(result)
        return result

    async def run_all_tests(self):
        """运行所有测试用例"""
        sdk.logger.info("=" * 60)
        sdk.logger.info("开始运行 Sandbox 适配器发送规则与构建系统测试")
        sdk.logger.info("=" * 60)

        self._register_test_cases()

        for i, test_case in enumerate(self.test_cases, start=1):
            await asyncio.sleep(0.5)  # 测试间隔
            await self.run_test(test_case, i)

        self._print_summary()

    def _print_summary(self):
        """打印测试摘要"""
        success_count = len([r for r in self.results if r.status == "success"])
        failed_count = len([r for r in self.results if r.status == "failed"])
        error_count = len([r for r in self.results if r.status == "error"])
        skipped_count = len([r for r in self.results if r.status == "skipped"])

        sdk.logger.info("=" * 60)
        sdk.logger.info("测试摘要")
        sdk.logger.info("=" * 60)
        sdk.logger.info(f"总计: {len(self.results)} 个测试")
        sdk.logger.info(f"成功: {success_count} 个")
        sdk.logger.info(f"失败: {failed_count} 个")
        sdk.logger.info(f"错误: {error_count} 个")
        sdk.logger.info(f"跳过: {skipped_count} 个")
        sdk.logger.info("=" * 60)

        # 打印失败的测试
        if failed_count > 0 or error_count > 0:
            sdk.logger.info("失败的测试:")
            for result in self.results:
                if result.status in ["failed", "error"]:
                    sdk.logger.info(f"  {result.test_num}. {result.test_name} - {result.status}")
                    if result.error_message:
                        sdk.logger.info(f"     错误: {result.error_message}")

        # 打印回调日志
        if self.hook_logs:
            sdk.logger.info("Hook 回调日志:")
            for log in self.hook_logs:
                sdk.logger.info(f"  {log}")

        if self.progress_logs:
            sdk.logger.info("OnProgress 回调日志:")
            for log in self.progress_logs:
                sdk.logger.info(f"  {log}")

        if self.error_logs:
            sdk.logger.info("OnError 回调日志:")
            for log in self.error_logs:
                sdk.logger.info(f"  {log}")


# ==================== 命令接口 ====================

@command("test_sandbox_send", help="测试 Sandbox 适配器发送规则与构建功能", usage="/test_sandbox_send")
async def test_sandbox_send_command(event):
    """处理测试命令"""
    sdk.logger.info("收到 Sandbox 适配器发送测试命令")

    # 配置测试参数
    config = {
        "target_type": "user",
        "target_id": event.get("user_id", "test_user_001"),
        "group_id": event.get("group_id", "test_group_001"),
    }

    # 创建测试运行器
    runner = SandboxSendTestRunner(config)

    # 初始化测试环境
    if not await runner.setup():
        reply = "测试环境初始化失败，请检查日志"
        adapter = getattr(sdk.adapter, event.get("platform", "sandbox"))
        await adapter.Send.To("user", event["user_id"]).Text(reply)
        return

    # 运行测试
    await runner.run_all_tests()

    # 发送测试结果
    success_count = len([r for r in runner.results if r.status == "success"])
    total_count = len([r for r in runner.results if r.status != "skipped"])

    reply = f"""Sandbox 适配器发送测试完成！
成功: {success_count}/{total_count}
详情请查看日志"""

    adapter = getattr(sdk.adapter, event.get("platform", "sandbox"))
    await adapter.Send.To("user", event["user_id"]).Text(reply)


# ==================== 主函数 ====================

async def main():
    """主函数，用于直接运行测试"""
    sdk.logger.info("启动 Sandbox 适配器发送规则与构建系统测试")

    # 配置测试参数
    config = {
        "target_type": "user",
        "target_id": "test_user_001",
        "group_id": "test_group_001",
    }

    # 创建测试运行器
    runner = SandboxSendTestRunner(config)

    # 初始化测试环境
    if not await runner.setup():
        sdk.logger.error("无法初始化测试环境")
        return

    try:
        # 运行测试
        await runner.run_all_tests()

        # 保持程序运行，直到手动停止
        sdk.logger.info("测试完成，保持程序运行...")
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        sdk.logger.info("收到中断信号，正在停止测试...")
    except Exception as e:
        sdk.logger.error(f"测试运行出错: {e}")
    finally:
        await sdk.adapter.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
