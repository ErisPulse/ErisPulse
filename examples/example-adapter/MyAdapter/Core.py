import asyncio
from ErisPulse.Core import BaseAdapter, RequestDSL, SendDSL
from ErisPulse.Core import logger, config as config_manager, adapter

class MyAdapter(BaseAdapter):
    """
    MyAdapter适配器示例
    
    这是一个自定义适配器示例，继承自BaseAdapter基类
    实现了SendDSL风格的链式调用接口
    
    At/AtAll/Reply 已由框架 SendDSL 基类内置实现，
    适配器只需实现 Raw_ob12 方法，使用 _apply_modifiers() 和 send_context 即可。
    
    同时展示了 Request 内部类的实现方式，用于处理好友请求/群邀请等操作。
    """
    
    def __init__(self, sdk):
        super().__init__()  # 必须调用：初始化 Send / Request 工厂实例
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        self.logger.info("MyAdapter 初始化完成")
        self.config = self._load_config()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
    
    def _setup_converter(self):
        """
        设置转换器实例
        从Converter.py导入具体的转换器类
        """
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
    
    def _load_config(self):
        """加载适配器配置"""
        if not self.config_manager:
            return {}
            
        config = self.config_manager.getConfig("MyAdapter", {})

        if config is None:
            default_config = {
                "mode": "server",
                "server": {
                    "path": "/webhook",
                },
                "client": {
                    "url": "http://127.0.0.1:8080",
                    "token": ""
                }
            }
            self.config_manager.setConfig("MyAdapter", default_config)
            self.logger.info("已创建MyAdapter默认配置")
            return default_config
        return config
    
    # ==================== 请求操作实现 ====================
    
    class Request(RequestDSL):
        """
        请求操作 DSL 实现
        
        适配器按需重写 accept/reject 方法以支持平台请求操作。
        基类默认返回 retcode=10002（不支持的操作）。
        
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
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            
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
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            
            return self._create_task(_do())
    
    # ==================== 消息发送实现 ====================
    
    class Send(SendDSL):
        """
        Send消息发送DSL

        继承BaseAdapter.Send即可获得完整的链式调用支持:
        - To(type, id): 设置发送目标
        - Using(account_id) / Account(account_id): 设置发送账号
        - At(user_id): @用户 (可多次调用)
        - AtAll(): @全体成员
        - Reply(message_id): 回复消息
        - Text/Image/...: 实际发送方法

        At/AtAll/Reply 由框架基类处理，无需手动管理状态。
        使用 self._apply_modifiers(message) 合并修饰器到消息段。
        使用 self.send_context 获取发送上下文字典。
        
        示例:
            Send.To("group","123").At("456").Reply("789").Text("hi")
        """
        
        def Raw_ob12(self, message, **kwargs):
            """
            发送 OneBot12 格式消息（必须实现）

            将 OneBot12 消息段列表转换为平台 API 调用。
            标准方法（Text、Image 等）内部委托给此方法。

            :param message: OneBot12 消息段列表或单个消息段
            :param kwargs: 其他参数
            :return: asyncio.Task
            """
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs
                )
            
            return asyncio.create_task(_do_send())
        
        def Text(self, text: str):
            """发送文本消息（委托给 Raw_ob12）"""
            return self.Raw_ob12([
                {"type": "text", "data": {"text": text}}
            ])
            
        def Image(self, file):
            """发送图片消息（委托给 Raw_ob12）"""
            return self.Raw_ob12([
                {"type": "image", "data": {"file": file}}
            ])
        
        def Example(self, text: str):
            """发送示例消息（继承自BaseAdapter.Send）"""
            return super().Example(text)

    async def call_api(self, endpoint: str, **params):
        """
        调用平台API
        
        :param endpoint: API端点
        :param params: API参数（包含 message, target_type, target_id, account_id 等）
        :return: API调用结果
        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError(f"需要实现平台特定的API调用: {endpoint}")

    async def start(self):
        """
        启动适配器
        
        :raises NotImplementedError: 必须由子类实现
        """
        self.logger.info(f"启动MyAdapter，配置模式: {self.config.get('mode', 'unknown')}")
        raise NotImplementedError("需要实现适配器启动逻辑")
    
    async def shutdown(self):
        """
        关闭适配器
        
        :raises NotImplementedError: 必须由子类实现
        """
        self.logger.info("关闭MyAdapter")
        raise NotImplementedError("需要实现适配器关闭逻辑")
