"""
ErisPulse 适配器通信模式基类

为最常见的两类平台连接模式提供「半成品」基类，子类只实现拉取/转换钩子，
``start`` / ``shutdown`` 的生命周期编排（后台任务归属、路由注册与按 owner
清理）全部由基类完成：

- :class:`PollingAdapter`——HTTP 轮询型平台（Telegram getUpdates 型）：
  子类实现 ``fetch_events`` / ``convert_one`` 两个钩子即可获得带指数退避的
  常驻轮询循环
- :class:`WebhookAdapter`——HTTP 回调型平台：子类实现 ``convert`` 钩子
  （可选覆写 ``verify_request`` 做签名/Token 校验）即可获得自动注册与
  自动清理的回调接收路由

{!--< tips >!--}
1. 两个基类都不需要子类实现 start / shutdown（基类已管）
2. ``epsdk create adapter --template polling / webhook`` 可直接生成对应骨架
3. 平台协议为 WebSocket 时请直接继承 :class:`BaseAdapter`（见 ws-server 模板）
{!--< /tips >!--}
"""

import asyncio
from abc import abstractmethod
from typing import Any

from ..constants import (
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_FORBIDDEN,
    POLLING_ADAPTER_BACKOFF_BASE_SECS,
    POLLING_ADAPTER_BACKOFF_MAX_SECS,
    WEBHOOK_ADAPTER_PATH_PREFIX,
)
from ..i18n import i18n
from ..logger import logger
from .adapter import BaseAdapter
from .router import HttpRequest


class PollingAdapter(BaseAdapter):
    """
    HTTP 轮询型适配器基类（抽象）

    适用于"客户端定时拉取事件"的平台（Telegram getUpdates 型）。基类以
    spawn-返回式实现 ``start()``：经 :meth:`BaseAdapter.spawn_client_loop`
    拉起轮询循环后立即返回；循环内拉取失败自动留痕并指数退避（基数
    ``POLLING_ADAPTER_BACKOFF_BASE_SECS`` 秒、上限
    ``POLLING_ADAPTER_BACKOFF_MAX_SECS`` 秒），成功后归零重计。

    子类最小实现面：

    - :meth:`fetch_events`——拉一批平台原生事件
    - :meth:`convert_one`——单条原生事件转 OneBot12（返回 None 跳过）
    - :meth:`call_api`——平台 API 调用（BaseAdapter 既有抽象）

    {!--< tips >!--}
    1. 轮询间隔默认取类属性 ``poll_interval``（5 秒）；声明了含
       ``poll_interval`` 字段的 ConfigClass 时自动改用配置值
    2. ``shutdown()`` 无需子类处理：轮询循环经 owner（平台名）归属，
       适配器停止时框架自动取消
    3. 拉取与转换异常由基类统一捕获退避，循环内无需写 try/except
    {!--< /tips >!--}

    :example:
    >>> class TelegramAdapter(PollingAdapter):
    ...     poll_interval = 3.0
    ...
    ...     async def fetch_events(self):
    ...         resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
    ...         data = await resp.json()
    ...         return data.get("result", [])
    ...
    ...     def convert_one(self, raw):
    ...         return MyConverter().convert(raw)
    """

    # 轮询间隔（秒）。声明了含 poll_interval 字段的 ConfigClass 时，
    # 运行时以配置值为准（见 _resolve_poll_interval）
    poll_interval: float = 5.0

    async def start(self) -> None:
        """
        启动轮询适配器（spawn-返回式）

        拉起归属本平台的轮询循环后立即返回：启动即成功，平台不可达等
        拉取失败由循环内的指数退避处理，不阻塞框架启动链。

        子类通常无需覆写；需要一次性初始化（如登录）时可覆写并在
        ``await super().start()`` 前后补充逻辑。
        """
        self.spawn_client_loop(self._poll_loop(), name="poll_loop")

    async def _poll_loop(self) -> None:
        """
        常驻轮询循环：拉取 → 逐条转换上报 → 休眠

        {!--< internal-use >!--}
        拉取/转换异常统一捕获：WARNING 留痕 + 指数退避后重试；
        asyncio.CancelledError 原样上抛（owner 取消即停止）。
        {!--< /internal-use >!--}
        """
        backoff = POLLING_ADAPTER_BACKOFF_BASE_SECS
        while True:
            try:
                events = await self.fetch_events()
                for raw in events or []:
                    event = self.convert_one(raw)
                    if event is None:
                        continue
                    # 逐条隔离 emit：单条上报异常不丢弃余批（offset 已在
                    # fetch 推进的适配器会真丢事件），记 warning 继续本批
                    try:
                        await self.emit_event(event)
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        logger.warning(
                            i18n.t(
                                "core.adapter.polling_emit_failed",
                                platform=self._platform or self.__class__.__name__,
                                error=e,
                            )
                        )
                backoff = POLLING_ADAPTER_BACKOFF_BASE_SECS
                await asyncio.sleep(self._resolve_poll_interval())
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(
                    i18n.t(
                        "core.adapter.polling_fetch_failed",
                        platform=self._platform or self.__class__.__name__,
                        error=e,
                        backoff=backoff,
                    )
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, POLLING_ADAPTER_BACKOFF_MAX_SECS)

    def _resolve_poll_interval(self) -> float:
        """
        解析生效的轮询间隔

        优先取 ConfigClass 声明的 ``poll_interval`` 配置值（实时读取，
        热更新生效）；未声明或值非法（非正数）时回退类属性默认值。

        :return: 生效的轮询间隔（秒）
        """
        if self.ConfigClass is None:
            return self.poll_interval
        try:
            value = getattr(self.cfg, "poll_interval", None)
        except Exception:
            value = None
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
        return self.poll_interval

    @abstractmethod
    async def fetch_events(self) -> list[Any]:
        """
        拉取一批平台原生事件（抽象，子类必须实现）

        建议实现为一次平台 API 调用（如 getUpdates），返回本轮全部
        原生事件；无新事件时返回空列表。抛出的异常由基类统一退避处理。

        :return: 平台原生事件列表
        """

        raise NotImplementedError(i18n.t("core.adapter.must_implement_fetch_events"))

    @abstractmethod
    def convert_one(self, raw: Any) -> dict[str, Any] | None:
        """
        单条原生事件转 OneBot12 标准格式（抽象，子类必须实现）

        :param raw: fetch_events 返回的单条原生事件
        :return: OneBot12 事件字典；无法识别的事件返回 None（跳过不上报）
        """

        raise NotImplementedError(i18n.t("core.adapter.must_implement_convert_one"))

    async def shutdown(self) -> None:
        """
        关闭轮询适配器（默认空实现）

        轮询循环经 owner（平台名）归属：适配器停止时框架按归属自动取消，
        子类无需管理任务句柄；有平台侧会话需要显式登出时可覆写本方法。
        """


class WebhookAdapter(BaseAdapter):
    """
    HTTP 回调型适配器基类（抽象）

    适用于"平台主动推送回调"的平台。基类的 ``start()`` 在框架 router 上
    注册接收路由（最终路径 ``/{平台名}/webhook``，与 ws-server 模板的
    ``/{平台名}/ws`` 同一命名空间约定），注册包在 ``owner_scope`` 中使
    适配器卸载时按 owner 自动清理；回调处理器完成「校验 → 解析 → 转换 →
    上报」的固定编排。

    子类最小实现面：

    - :meth:`convert`——回调载荷转 OneBot12（返回 None 跳过）
    - :meth:`call_api`——平台 API 调用（BaseAdapter 既有抽象）
    - 可选覆写 :meth:`verify_request`——请求校验（默认放行）

    {!--< tips >!--}
    1. ``shutdown()`` 无需子类处理：路由经 owner 归属自动清理
    2. 回调地址可经 ``sdk.adapter.get_connection_info(platform)`` 或
       ``sdk.router.get_module_urls(platform)`` 查询后填到平台后台
    3. 校验失败的请求返回 403，载荷解析失败返回 400
    {!--< /tips >!--}

    :example:
    >>> class DiscordAdapter(WebhookAdapter):
    ...     def verify_request(self, request) -> bool:
    ...         return request.headers.get("x-signature") == self._sign()
    ...
    ...     def convert(self, payload):
    ...         return MyConverter().convert(payload)
    """

    async def start(self) -> None:
        """
        启动回调适配器：注册接收路由后返回

        路由注册在 ``owner_scope(平台名)`` 下进行（框架在启动链上本已注入
        owner，此处显式包住以保证脱离管理器直接调用 ``start()`` 时归属
        同样正确），适配器停止/卸载时按 owner 自动清理，无需子类注销。

        子类通常无需覆写；需要同时拉起辅助任务（如心跳）时可覆写并在
        ``await super().start()`` 前后补充逻辑。
        """
        from ...runtime.context import owner_scope
        from ..router import router

        namespace = self._platform or self._get_config_key()
        with owner_scope(namespace):
            router.register_http_route(
                module_name=namespace,
                path=WEBHOOK_ADAPTER_PATH_PREFIX,
                handler=self._webhook_handler,
                methods=["POST"],
            )
        logger.info(
            i18n.t(
                "core.adapter.webhook_route_registered",
                platform=namespace,
                path=f"/{namespace}{WEBHOOK_ADAPTER_PATH_PREFIX}",
            )
        )

    async def _webhook_handler(self, request: HttpRequest) -> Any:
        """
        回调接收处理器：校验 → 解析 → 转换 → 上报

        {!--< internal-use >!--}
        固定编排不允许子类干预顺序；自定义逻辑分别经 verify_request /
        convert 两个钩子注入。校验失败返回 (denied, 403)，载荷非法返回
        (bad request, 400)，正常返回 {"status": "ok"}（转换返回 None 的
        载荷视为已忽略，同样返回 ok）。
        {!--< /internal-use >!--}

        :param request: 框架注入的 HTTP 请求包装
        :return: HTTP 响应（dict 或 (body, status) 元组）
        """
        if not self.verify_request(request):
            logger.warning(
                i18n.t(
                    "core.adapter.webhook_verify_rejected",
                    platform=self._platform or self.__class__.__name__,
                )
            )
            return {"status": "denied"}, HTTP_STATUS_FORBIDDEN

        try:
            payload = await request.json()
        except Exception as e:
            logger.warning(
                i18n.t(
                    "core.adapter.webhook_bad_payload",
                    platform=self._platform or self.__class__.__name__,
                    error=e,
                )
            )
            return {"status": "bad request"}, HTTP_STATUS_BAD_REQUEST

        event = self.convert(payload)
        if event is not None:
            await self.emit_event(event)
        return {"status": "ok"}

    def verify_request(self, request: HttpRequest) -> bool:
        """
        回调请求校验钩子（可选覆写，默认放行）

        用于签名 / Token 校验：返回 False 时基类直接以 403 回绝且不进入
        事件转换。默认实现恒放行（平台无校验要求时无需覆写）。

        :param request: 框架注入的 HTTP 请求包装（headers / query_params 可用）
        :return: 是否放行

        :example:
        >>> def verify_request(self, request) -> bool:
        ...     cfg = self.cfg
        ...     if not cfg.token:
        ...         return True  # 未配置 Token 时放行
        ...     auth = request.headers.get("authorization", "")
        ...     return auth == f"Bearer {cfg.token}"
        """

        return True

    @abstractmethod
    def convert(self, payload: Any) -> dict[str, Any] | None:
        """
        回调载荷转 OneBot12 标准格式（抽象，子类必须实现）

        :param payload: 请求 JSON 载荷
        :return: OneBot12 事件字典；无法识别的载荷返回 None（跳过上报）
        """

        raise NotImplementedError(i18n.t("core.adapter.must_implement_convert"))

    async def shutdown(self) -> None:
        """
        关闭回调适配器（默认空实现）

        接收路由经 owner（平台名）归属：适配器停止/卸载时框架按 owner
        自动清理，子类无需手动注销路由。
        """


__all__ = [
    "PollingAdapter",
    "WebhookAdapter",
]
