import asyncio
from dataclasses import dataclass, field
from typing import ClassVar

# 推荐根导入（2.10+）：常用符号直接从 ErisPulse 根包导入
from ErisPulse import BaseConfig, BaseI18n, I18nKey, SendDSL, WebhookAdapter, client


class ExampleWebhookAdapter(WebhookAdapter):
    """
    HTTP 回调模式适配器示例

    演示如何继承 `WebhookAdapter` 接入「平台主动推送回调」的平台：

    - 接收路由由基类注册：start() 在框架 router 上挂 POST
      /example_webhook/webhook（owner 归属，卸载自动清理）——子类不需要
      实现 start / shutdown
    - 只需实现 convert（回调载荷转 OB12）；verify_request 覆写做 Token
      校验示范（未配置 token 时放行）
    - 回调地址经 sdk.adapter.get_connection_info("example_webhook") 查询后
      填到平台后台
    """

    # 依赖声明（可选，2.8.0+）
    depends: ClassVar[dict] = {}
    optional_modules: ClassVar[list] = []

    # 全局配置类以嵌套类形式声明（需 @dataclass 装饰），框架自动识别 ConfigClass
    @dataclass
    class ConfigClass(BaseConfig):
        """
        ExampleWebhookAdapter 配置

        :ivar token: 回调校验 Token（留空放行全部请求）
        """

        endpoint: str = field(
            default="https://api.example.com",
            metadata={
                "description": {"i18n": "ExampleWebhookAdapter.endpoint", "default": "平台 API 地址"},
                "required": False,
                "ui": {"widget": "text", "group": "connection", "order": 1},
            },
        )
        token: str = field(
            default="",
            metadata={
                "description": {"i18n": "ExampleWebhookAdapter.token", "default": "校验 Token（留空放行）"},
                "required": False,
                "secret": True,
                "ui": {"widget": "password", "group": "basic", "order": 2},
            },
        )

    # 翻译键集合以嵌套类形式声明，框架自动识别 I18nClass 并注册到 i18n 系统
    class I18nClass(BaseI18n):
        """ExampleWebhookAdapter 翻译键声明"""

        endpoint: I18nKey = I18nKey(
            default="Platform API Endpoint",
            zh_CN="平台 API 地址",
            en="Platform API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
            zh_TW="API 位址",
        )
        token: I18nKey = I18nKey(
            default="Verify Token (empty = accept all)",
            zh_CN="校验 Token（留空放行）",
            en="Verify Token (empty = accept all)",
            ja="検証トークン（空なら全許可）",
            ru="Токен проверки (пусто = разрешить все)",
            zh_TW="校驗權杖（留空放行）",
        )

    def __init__(self, sdk=None):
        super().__init__(sdk=sdk)
        self.logger = self._get_logger()
        self.converter = self._setup_converter()

    def _setup_converter(self):
        """实例化事件转换器（见 Converter.py）"""
        from .Converter import ExampleWebhookConverter

        return ExampleWebhookConverter()

    def on_config_update(self, old_config, new_config):
        """配置热更新回调"""
        self.logger.info("回调适配器配置已热更新")

    # start() / shutdown() 由 WebhookAdapter 基类管理，无需实现

    def verify_request(self, request) -> bool:
        """
        回调校验钩子示范：Bearer Token 校验

        未配置 token 时放行（便于本地联调）；配置后仅放行携带
        Authorization: Bearer <token> 的请求，其余由基类以 403 回绝。
        """
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """单条回调载荷转 OneBot12（不认识的载荷返回 None 跳过）"""
        return self.converter.convert(payload)

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
