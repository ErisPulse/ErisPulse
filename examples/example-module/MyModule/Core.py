from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command, message, notice
from ErisPulse.runtime.config_schema import BaseConfig


@dataclass
class MyModuleConfig(BaseConfig):
    """MyModule 模块配置"""

    welcome_message: str = field(
        default="欢迎添加我为好友！",
        metadata={
            "description": {"i18n": "my_module.welcome_message", "default": "新好友欢迎消息"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )
    echo_enabled: bool = field(
        default=True,
        metadata={
            "description": {"i18n": "my_module.echo_enabled", "default": "是否启用回显命令"},
            "ui": {"widget": "switch", "group": "basic", "order": 2},
        },
    )
    debug_mode: bool = field(
        default=False,
        metadata={
            "description": {"i18n": "my_module.debug_mode", "default": "调试模式（输出详细日志）"},
            "ui": {"widget": "switch", "group": "advanced", "order": 3},
        },
    )


class Main(BaseModule):
    """
    MyModule模块示例

    这是一个自定义模块示例，继承自BaseModule基类
    使用声明式配置管理（ConfigClass），通过 self.cfg 实时读取配置
    """

    ConfigClass = MyModuleConfig

    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = self.sdk.logger.get_child("MyModule")
        self.storage = self.sdk.storage
        self.adapter = self.sdk.adapter

        self.logger.info("MyModule 初始化完成")

    @staticmethod
    def get_load_strategy():
        """
        返回模块加载策略
        """
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100
        )

    async def on_load(self, event: dict) -> bool:
        """
        当模块被加载时调用

        :param event: 事件内容
        :return: 处理结果
        """
        await self._register_commands()
        await self._register_message_handlers()

        self.logger.info(f"模块已加载: {event}")
        return True

    async def on_unload(self, event: dict) -> bool:
        """
        当模块被卸载时调用

        :param event: 事件内容
        :return: 处理结果
        """
        self.logger.info(f"模块已卸载: {event}")
        return True

    def on_config_update(self, old_config, new_config):
        """配置热更新回调"""
        self.logger.info("模块配置已热更新")
        if old_config:
            self.logger.info(f"旧配置: {old_config}")
        self.logger.info(f"新配置: {new_config}")

    async def _register_commands(self):
        """注册命令处理器"""
        @command("hello", help="发送问候消息")
        async def hello_command(event):
            await event.reply("Hello World!")
            sender = event.get_sender()
            self.logger.info(f"收到来自 {sender['user_id']} 的hello命令")

        @command("help", aliases=["h"], help="显示帮助信息")
        async def help_command(event):
            help_text = command.help()
            await event.reply(help_text)

        @command("echo", help="回显消息", usage="/echo <内容>")
        async def echo_command(event):
            # 实时读取配置（每次访问都反映最新值）
            cfg = self.cfg
            if not cfg.echo_enabled:
                return

            args = event.get_command_args()

            if not args:
                await event.reply("请提供要回显的内容")
            else:
                response = " ".join(args)
                await event.reply(response)

        @command("interactive", help="交互式命令示例", usage="/interactive")
        async def interactive_command(event):
            await event.reply("请输入你的名字:")

            reply = await event.wait_reply(timeout=30)

            if reply:
                name = reply.get_text()
                await event.reply(f"你好，{name}！很高兴认识你。")
            else:
                await event.reply("等待超时，请重试。")

    async def _register_message_handlers(self):
        """注册消息和通知处理器"""
        @message.on_private_message()
        async def private_message_handler(event):
            cfg = self.cfg
            if cfg.debug_mode:
                self.logger.info(f"收到私聊消息，发送者: {event.get_user_nickname()}, 内容: {event.get_text()}")

        @message.on_group_message()
        async def group_message_handler(event):
            if event.is_at_message():
                mentions = event.get_mentions()
                self.logger.info(f"收到@消息，被@的用户: {mentions}")
                await event.reply("我收到了你的@消息！")

        @notice.on_friend_add()
        async def friend_add_handler(event):
            self.logger.info(f"新好友添加: {event.get_user_nickname()}")

            # 实时读取配置
            cfg = self.cfg
            await event.reply(cfg.welcome_message)

    def hello(self):
        """可以被其他模块调用的方法"""
        self.logger.info("Hello World!")
        # 其它模块可以通过 sdk.MyModule.hello() 调用此方法
