import asyncio
from dataclasses import dataclass, field
from typing import ClassVar

# 推荐根导入（2.10+）：常用符号直接从 ErisPulse 根包导入
from ErisPulse import BaseConfig, BaseI18n, I18nKey, PollingAdapter, SendDSL, client


class ExamplePollingAdapter(PollingAdapter):
    """
    HTTP 轮询模式适配器示例

    演示如何继承 `PollingAdapter` 接入「客户端定时拉取事件」的平台
    （Telegram getUpdates 型）：

    - 轮询循环由基类管理：start() 拉起带指数退避的循环后立即返回，
      shutdown() 时框架按 owner 自动取消——子类不需要实现这两个方法
    - 只需实现 fetch_events（拉一批原生事件）与 convert_one（单条转 OB12）
    - 轮询间隔经 ConfigClass.poll_interval 声明，配置热更新即时生效
    """

    # 依赖声明（可选，2.8.0+）
    depends: ClassVar[dict] = {}
    optional_modules: ClassVar[list] = []

    # 轮询间隔兜底值：ConfigClass 声明了 poll_interval 字段时以配置值为准
    poll_interval = 5.0

    # 全局配置类以嵌套类形式声明（需 @dataclass 装饰），框架自动识别 ConfigClass
    @dataclass
    class ConfigClass(BaseConfig):
        """
        ExamplePollingAdapter 配置

        :ivar poll_interval: 轮询间隔秒数（热更新生效）
        """

        endpoint: str = field(
            default="https://api.example.com",
            metadata={
                "description": {"i18n": "ExamplePollingAdapter.endpoint", "default": "平台 API 地址"},
                "required": False,
                "ui": {"widget": "text", "group": "connection", "order": 1},
            },
        )
        token: str = field(
            default="",
            metadata={
                "description": {"i18n": "ExamplePollingAdapter.token", "default": "平台 Token"},
                "required": True,
                "secret": True,
                "ui": {"widget": "password", "group": "basic", "order": 2},
            },
        )
        poll_interval: float = field(
            default=5.0,
            metadata={
                "description": {"i18n": "ExamplePollingAdapter.poll_interval", "default": "轮询间隔（秒）"},
                "required": False,
                "min": 0.1,
                "ui": {"widget": "number", "group": "connection", "order": 3},
            },
        )

    # 翻译键集合以嵌套类形式声明，框架自动识别 I18nClass 并注册到 i18n 系统
    class I18nClass(BaseI18n):
        """ExamplePollingAdapter 翻译键声明"""

        endpoint: I18nKey = I18nKey(
            default="Platform API Endpoint",
            zh_CN="平台 API 地址",
            en="Platform API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
            zh_TW="API 位址",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
            zh_TW="平台權杖",
        )
        poll_interval: I18nKey = I18nKey(
            default="Polling interval (seconds)",
            zh_CN="轮询间隔（秒）",
            en="Polling interval (seconds)",
            ja="ポーリング間隔（秒）",
            ru="Интервал опроса (сек)",
            zh_TW="輪詢間隔（秒）",
        )

    def __init__(self, sdk=None):
        super().__init__(sdk=sdk)
        self.logger = self._get_logger()
        self.converter = self._setup_converter()

    def _setup_converter(self):
        """实例化事件转换器（见 Converter.py）"""
        from .Converter import ExamplePollingConverter

        return ExamplePollingConverter()

    def on_config_update(self, old_config, new_config):
        """配置热更新回调"""
        self.logger.info("轮询适配器配置已热更新（poll_interval 即时生效）")

    # start() / shutdown() 由 PollingAdapter 基类管理，无需实现

    async def fetch_events(self):
        """
        拉取一批平台原生事件（一次 getUpdates 调用）

        平台不可达等异常无需捕获——基类统一留痕并指数退避重试。
        """
        cfg = self.cfg
        resp = await client.get(
            f"{cfg.endpoint}/getUpdates",
            params={"timeout": 0},
            headers={"Authorization": "Bearer " + cfg.token},
        )
        data = await resp.json()
        # 真实平台通常还需配合 offset 游标去重，这里演示最小形态
        return data.get("events", [])

    def convert_one(self, raw):
        """单条原生事件转 OneBot12（不认识的事件返回 None 跳过）"""
        return self.converter.convert(raw)

    class Send(SendDSL):
        """
        Send 消息发送 DSL

        At/AtAll/Reply 由框架基类处理；标准发送方法（Text/Image 等）默认
        委托 Raw_ob12，这里只需实现 Raw_ob12。
        """

        def Raw_ob12(self, message, **kwargs):
            """发送 OneBot12 格式消息段（必须实现）"""

            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs,
                )

            return asyncio.create_task(_do_send())

    async def call_api(self, endpoint: str, **params):
        """调用平台 API（发送消息等出站动作的统一入口）"""
        cfg = self.cfg
        headers = {"Authorization": "Bearer " + cfg.token}
        url = cfg.endpoint + endpoint

        try:
            resp = await client.post(
                url,
                json=params,
                headers=headers,
                timeout=30,
                max_retries=2,
            )
            result = await resp.json()
            return self.make_response(
                data=result.get("data"),
                message_id=result.get("data", {}).get("message_id", ""),
                raw=result,
            )
        except Exception as e:
            self.logger.error(f"API 调用失败: {e}")
            return self.make_error(message=str(e))
