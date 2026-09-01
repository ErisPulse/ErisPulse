from dataclasses import dataclass, field

from ErisPulse import SDK
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey, ModuleMeta
from ErisPulse.Core.Event import Event, command, message, notice


class Main(BaseModule):
    """
    MyModule模块示例

    这是一个自定义模块示例，继承自BaseModule基类
    使用声明式配置管理（ConfigClass），通过 self.cfg 实时读取配置
    同时演示了通过 I18nClass 声明翻译键的推荐写法
    """

    # 配置类以嵌套类形式声明（需 @dataclass 装饰），框架自动识别 ConfigClass
    @dataclass
    class ConfigClass(BaseConfig):
        """MyModule 模块配置"""

        welcome_message: str = field(
            default="欢迎添加我为好友！",
            metadata={
                "description": "新好友欢迎消息",
                "ui": {"widget": "text", "group": "basic", "order": 1},
            },
        )
        echo_enabled: bool = field(
            default=True,
            metadata={
                "description": "是否启用回显命令",
                "ui": {"widget": "switch", "group": "basic", "order": 2},
            },
        )
        debug_mode: bool = field(
            default=False,
            metadata={
                "description": "调试模式（输出详细日志）",
                "ui": {"widget": "switch", "group": "advanced", "order": 3},
            },
        )

    # 翻译键集合以嵌套类形式声明，框架自动识别 I18nClass 并注册到 i18n 系统
    # 属性名会与模块名拼接为完整键路径（如 MyModule.greeting）
    class I18nClass(BaseI18n):
        """MyModule 翻译键声明"""

        greeting_prompt: I18nKey = I18nKey(
            default="Please enter your name:",
            zh_CN="请输入你的名字:",
            en="Please enter your name:",
            ja="あなたの名前を入力してください:",
            ru="Пожалуйста, введите ваше имя:",
            zh_TW="請輸入你的名字:",
        )
        greeting: I18nKey = I18nKey(
            default="Hello, {name}! Nice to meet you.",
            zh_CN="你好，{name}！很高兴认识你。",
            en="Hello, {name}! Nice to meet you.",
            ja="こんにちは，{name}さん！はじめまして。",
            ru="Привет, {name}! Рад знакомству.",
            zh_TW="你好，{name}！很高興認識你。",
        )
        timeout_hint: I18nKey = I18nKey(
            default="Timeout, please try again.",
            zh_CN="等待超时，请重试。",
            en="Timeout, please try again.",
            ja="タイムアウトしました。もう一度試してください。",
            ru="Время ожидания истекло, попробуйте снова.",
            zh_TW="等待逾時，請重試。",
        )

    def __init__(self, sdk: SDK = None):
        self.sdk = sdk
        self.logger = self.sdk.logger.get_child("MyModule")
        self.storage = self.sdk.storage
        self.adapter = self.sdk.adapter

        self.logger.info("MyModule 初始化完成")

    @staticmethod
    def get_meta() -> ModuleMeta:
        """
        返回模块介绍元信息（推荐返回 ModuleMeta 配置类实例，与 get_load_strategy 对齐）
        """
        return ModuleMeta(
            name="MyModule",
            description="自定义模块示例",
            version="1.0.0",
            author="ErisDev",
            group="示例",
            tags=["示例", "demo"],
        )

    @staticmethod
    def get_load_strategy():
        """
        返回模块加载策略
        """
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            # 依赖声明（可选，2.8.0+）：缺失依赖的模块会被跳过加载；
            # 被依赖模块卸载/热重载时，本模块将级联卸载/重载
            # depends=["OtherModule"],
        )

    async def on_load(self, event: dict) -> bool:
        """
        当模块被加载时调用

        :param event: 事件内容
        :return: 处理结果
        """
        await self._register_commands()
        await self._register_message_handlers()

        # 后台任务推荐使用 self.spawn()（2.8.0+）：
        # 任务自动归属本模块，模块卸载时框架在 on_unload 之后兜底取消，
        # 防止任务持有 self 引用导致模块无法被回收
        self.spawn(self._background_poll())

        self.logger.info(f"模块已加载: {event}")
        return True

    async def _background_poll(self):
        """示例后台任务：模块卸载时会被框架兜底取消"""
        import asyncio

        while True:
            await asyncio.sleep(60)

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
        # 命令权限（可选）：permission 为调用函数，返回 True 才执行命令；
        # master=True 限定框架主人；跨命令的用户黑白名单用控制面命令 ACL
        # （ErisPulse.scope.commands 或 sdk.scope.allow_user()/deny_user()，命令名支持 glob）；
        # 模块级可用性与事件准入均收敛在控制面 scope（用户可控）
        @command("hello", help="发送问候消息")
        async def hello_command(event: Event):
            await event.reply("Hello World!")
            sender = event.get_sender()
            self.logger.info(f"收到来自 {sender['user_id']} 的hello命令")

        @command("help", aliases=["h"], help="显示帮助信息")
        async def help_command(event: Event):
            help_text = command.help()
            await event.reply(help_text)

        @command("echo", help="回显消息", usage="/echo <内容>")
        async def echo_command(event: Event):
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
        async def interactive_command(event: Event):
            from ErisPulse import i18n
            await event.reply(i18n.t("MyModule.greeting_prompt"))

            reply = await event.wait_reply(timeout=30)

            if reply:
                name = reply.get_text()
                await event.reply(i18n.t("MyModule.greeting", name=name))
            else:
                await event.reply(i18n.t("MyModule.timeout_hint"))

    async def _register_message_handlers(self):
        """注册消息和通知处理器"""
        @message.on_private_message()
        async def private_message_handler(event: Event):
            cfg = self.cfg
            if cfg.debug_mode:
                self.logger.info(f"收到私聊消息，发送者: {event.get_user_nickname()}, 内容: {event.get_text()}")

        @message.on_group_message()
        async def group_message_handler(event: Event):
            if event.is_at_message():
                mentions = event.get_mentions()
                self.logger.info(f"收到@消息，被@的用户: {mentions}")
                await event.reply("我收到了你的@消息！")

        # pattern（glob 通配符）/ regex（正则）二选一：不匹配的消息不会触发
        @message.on_message(pattern="签到*")
        async def signin_handler(event: Event):
            await event.reply("签到成功")

        @message.on_message(regex=r"\d+\s*元")
        async def price_handler(event: Event):
            await event.reply(f"收到金额：{event.get_text()}")

        @notice.on_friend_add()
        async def friend_add_handler(event: Event):
            self.logger.info(f"新好友添加: {event.get_user_nickname()}")

            # 实时读取配置
            cfg = self.cfg
            await event.reply(cfg.welcome_message)

    def hello(self):
        """可以被其他模块调用的方法"""
        self.logger.info("Hello World!")
        # 其它模块可以通过 sdk.MyModule.hello() 调用此方法
