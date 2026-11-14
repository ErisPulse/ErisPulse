import threading
from dataclasses import dataclass, field

# 推荐根导入（2.10+）：常用符号直接从 ErisPulse 根包导入
from ErisPulse import (
    SDK,
    BaseConfig,
    BaseModule,
    Event,
    ModuleMeta,
    command,
)
from ErisPulse.runtime import (
    bind_owner,
    get_current_owner,
    get_rss_mb,
    log_snapshot,
    snapshot,
    spawn_later,
)


class Main(BaseModule):
    """
    运维治理示例模块

    演示第三方线程任务的归属包装（bind_owner）、归属化延迟任务
    （spawn_later）、内存体检（log_snapshot / get_rss_mb）与运行时
    日志隐私开关（exclude_level / allow_level）
    """

    @dataclass
    class ConfigClass(BaseConfig):
        """OpsModule 模块配置"""

        timer_interval: int = field(
            default=30,
            metadata={
                "description": "演示线程的触发间隔（秒）",
                "ui": {"widget": "number", "group": "basic", "order": 1},
            },
        )

    def __init__(self, sdk: SDK = None):
        self.sdk = sdk
        self.logger = self.sdk.logger.get_child("OpsModule")
        self.storage = self.sdk.storage
        self._timer: threading.Timer | None = None
        self.logger.info("OpsModule 初始化完成")

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="OpsModule",
            description="运维治理示例模块",
            version="1.0.0",
            author="ErisDev",
            group="示例",
            tags=["示例", "运维"],
        )

    async def on_load(self, event: dict) -> bool:
        # 内存体检：加载期快照（同名 label 自动计算与上次快照的增量）
        snapshot("OpsModule.load")
        self._start_timer()
        self._register_commands()
        return True

    async def on_unload(self, event: dict) -> bool:
        log_snapshot("OpsModule.unload")
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        return True

    def _start_timer(self):
        """第三方线程入口示例：threading.Timer 回调经 bind_owner 包装携带归属"""
        interval = max(1, self.cfg.timer_interval)
        # 新线程默认空 owner 上下文——其内创建的任务不进归属表、模块卸载时
        # 取消不掉；bind_owner 在包装瞬间捕获当前 owner（本模块），此后无论
        # 从哪个线程调用都以原 owner 身份执行
        timer = threading.Timer(interval, bind_owner(self._on_timer_fire))
        timer.daemon = True
        timer.start()
        self._timer = timer

    def _on_timer_fire(self):
        # 运行在 Timer 线程：current_owner == "OpsModule"（bind_owner 携带）
        self.logger.debug(f"定时器触发，owner={get_current_owner()}")
        self._start_timer()  # 周期性重排

    def _register_commands(self):
        """注册命令处理器"""

        @command("mem", help="当前进程内存读数（RSS）")
        async def mem_command(event: Event):
            await event.reply(f"RSS: {get_rss_mb():.1f} MB")

        @command("privacy", help="运行时消息内容隐私开关", usage="/privacy <on|off|status>")
        async def privacy_command(event: Event, action: str = "status"):
            logger = self.sdk.logger
            # 消息收发内容以 EVENT 等级（数值 21）记录；
            # exclude_level 与配置项 exclude_levels 语义一致，免写配置即时生效
            if action == "off":
                logger.exclude_level("EVENT")
                await event.reply("已屏蔽 EVENT 等级（消息内容不再进日志）")
            elif action == "on":
                logger.allow_level("EVENT")
                await event.reply("已恢复 EVENT 等级")
            else:
                excluded = logger.list_excluded_levels()
                text = "、".join(map(str, excluded)) if excluded else "无"
                await event.reply(f"当前屏蔽的等级：{text}")

        @command("remind", help="归属化延迟任务：到期写入模块状态并打日志", usage="/remind <秒> <内容>")
        async def remind_command(event: Event, seconds: float, text: str = "到点了"):
            # spawn_later：loop.call_later 的 owner 感知包装；模块卸载时随归属取消
            spawn_later(max(0.1, seconds), self._fire_remind, text)
            await event.reply(f"{seconds:.0f} 秒后会触发：{text}")

        @command("reminds", help="查看已触发的延迟提醒")
        async def reminds_command(event: Event):
            fired = self.state.get("reminds", [])
            if not fired:
                await event.reply("还没有触发过提醒")
                return
            lines = "\n".join(f"- {item}" for item in fired[-10:])
            await event.reply(f"最近触发的提醒：\n{lines}")

    async def _fire_remind(self, text: str):
        # 延迟到期回调（owner 归属本模块）；BaseModule.state 持久化，重启不丢
        fired = self.state.get("reminds", [])
        fired.append(text)
        self.state.set("reminds", fired)
        self.logger.info(f"提醒触发: {text}")
