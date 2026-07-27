import asyncio
from dataclasses import dataclass, field

from ErisPulse.Core import BaseAdapter, RequestDSL, SendDSL
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig, BaseI18n, I18nKey


class MyAdapter(BaseAdapter):
    """
    MyAdapter适配器示例

    演示了如何使用框架提供的配置管理、Meta 事件和响应标准化功能，
    大幅减少样板代码。

    主要特性：
    - 声明 ConfigClass 即可自动加载/生成配置
    - 声明 I18nClass 即可自动注册翻译键到 i18n 系统
    - At/AtAll/Reply 由框架 SendDSL 基类内置
    - emit_meta() 一行发送 meta 事件
    - make_response() / make_error() 构造标准化响应
    - _resolve_account() 自动解析多账户
    """

    # 全局配置类以嵌套类形式声明（需 @dataclass 装饰），框架自动识别 ConfigClass
    @dataclass
    class ConfigClass(BaseConfig):
        """MyAdapter 全局配置"""

        api_endpoint: str = field(
            default="https://api.example.com",
            metadata={
                "description": {"i18n": "MyAdapter.api_endpoint", "default": "API 地址"},
                "required": False,
                "ui": {"widget": "text", "group": "connection", "order": 1},
            },
        )
        mode: str = field(
            default="server",
            metadata={
                "description": {"i18n": "MyAdapter.mode", "default": "运行模式（server 或 client）"},
                "required": False,
                "ui": {
                    "widget": "select",
                    "group": "connection",
                    "order": 2,
                    "options": [
                        {"label": "服务器模式", "value": "server"},
                        {"label": "客户端模式", "value": "client"},
                    ],
                },
            },
        )
        token: str = field(
            default="",
            metadata={
                "description": {"i18n": "MyAdapter.token", "default": "平台 Token"},
                "required": True,
                "secret": True,
                "ui": {"widget": "password", "group": "basic", "order": 3},
            },
        )

    # 翻译键集合以嵌套类形式声明，框架自动识别 I18nClass 并注册到 i18n 系统
    # 这里集中声明 ConfigClass 中引用的 i18n 键（以及其他业务用到的键）的多语言译文
    class I18nClass(BaseI18n):
        """MyAdapter 翻译键声明"""

        api_endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
            zh_TW="API 位址",
        )
        mode: I18nKey = I18nKey(
            default="Run mode (server or client)",
            zh_CN="运行模式（server 或 client）",
            en="Run mode (server or client)",
            ja="実行モード（server または client）",
            ru="Режим работы (server или client)",
            zh_TW="執行模式（server 或 client）",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
            zh_TW="平台權杖",
        )

    # 多账户配置类同样以嵌套类形式声明（多账户时取消注释）
    # @dataclass
    # class AccountConfigClass(BotAccountConfig):
    #     """MyAdapter 多账户配置（可选）"""
    #     bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True, "ui": {"widget": "text", "group": "basic", "order": 1}})
    #     bot_token: str = field(default="", metadata={"description": "Bot Token", "required": True, "secret": True, "ui": {"widget": "password", "group": "basic", "order": 2}})

    def on_config_update(self, old_config, new_config):
        """配置热更新回调"""
        self.logger.info(f"适配器配置已更新")
        if old_config:
            self.logger.info(f"旧配置: {old_config}")
        self.logger.info(f"新配置: {new_config}")

    class Request(RequestDSL):
        """
        请求操作 DSL 实现

        可用属性：
        - self._request_id: 请求ID
        - self._account_id: Bot 账号
        - self._adapter: 适配器实例（可调用 call_api）
        """

        def accept(self, **kwargs):
            """同意请求"""

            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=True,
                    **kwargs,
                )
                return self._adapter.make_response(
                    data=result,
                    message=result.get("message", ""),
                )

            return self._create_task(_do())

        def reject(self, **kwargs):
            """拒绝请求"""

            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=False,
                    **kwargs,
                )
                return self._adapter.make_response(
                    data=result,
                    message=result.get("message", ""),
                )

            return self._create_task(_do())

    class Send(SendDSL):
        """
        Send消息发送DSL

        At/AtAll/Reply 由框架基类处理，无需手动管理状态。
        标准发送方法（Text/Image/Voice/Video/File）已从 SendDSL 基类继承，
        默认委托给 Raw_ob12，无需重复实现。
        使用 self._apply_modifiers(message) 合并修饰器到消息段。
        使用 self.send_context 获取发送上下文字典。
        """

        def Raw_ob12(self, message, **kwargs):
            """发送 OneBot12 格式消息（必须实现）"""

            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs,
                )

            return asyncio.create_task(_do_send())

        # 标准方法 Text/Image/Voice/Video/File 已从 SendDSL 基类继承，
        # 默认委托给 Raw_ob12，无需重复实现。
        # 如需平台特定逻辑，可覆盖单个方法：
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])

        # 添加平台特有的发送方法（会被 event.supports() / available_methods() 识别）：
        def Sticker(self, sticker_id: str):
            """发送平台特有贴纸（示例：平台特有方法）"""
            return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])

        def Example(self, text: str):
            """发送示例消息（继承自BaseAdapter.Send）"""
            return super().Example(text)

    async def call_api(self, endpoint: str, **params):
        """
        调用平台API

        使用 make_response / make_error 构造标准化响应
        """
        cfg = self.cfg
        try:
            raise NotImplementedError(f"需要实现平台特定的API调用: {endpoint}")
        except Exception as e:
            return self.make_error(message=str(e))

    async def start(self):
        """启动适配器"""
        cfg = self.cfg
        self.logger.info(f"启动MyAdapter，配置模式: {cfg.mode}")

        # Bot 上线示例（使用 emit_meta 一行完成）
        # await self.emit_meta("connect", "bot_id_here", user_name="MyBot")

        raise NotImplementedError("需要实现适配器启动逻辑")

    async def shutdown(self):
        """关闭适配器"""
        self.logger.info("关闭MyAdapter")

        # Bot 下线示例
        # await self.emit_meta("disconnect", "bot_id_here")

        raise NotImplementedError("需要实现适配器关闭逻辑")
