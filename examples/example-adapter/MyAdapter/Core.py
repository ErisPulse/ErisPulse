import asyncio
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import logger, config as config_manager, adapter

class MyAdapter(BaseAdapter):
    """
    MyAdapter适配器示例
    
    这是一个自定义适配器示例，继承自BaseAdapter基类
    实现了SendDSL风格的链式调用接口
    """
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        self.logger.info("MyAdapter 初始化完成")
        self.config = self._load_config()
        self.converter = self._setup_converter()  # 获取转换器实例
        self.convert = self.converter.convert
    
    def _setup_converter(self):
        """
        设置转换器实例
        从Converter.py导入具体的转换器类
        """
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
    
    # 加载配置方法，你需要在这里进行必要的配置加载逻辑
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
            # 这里默认配置会生成到用户的 config.toml 文件中
            self.config_manager.setConfig("MyAdapter", default_config)
            self.logger.info("已创建MyAdapter默认配置")
            return default_config
        return config
    
    class Send(BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        """
        Send消息发送DSL，支持四种调用方式(继承的Send类包含了To和Using方法):
        1. 指定类型和ID: To(type,id).Func() -> 设置_target_type和_target_id/_target_to
           示例: Send.To("group",123).Text("hi")
        2. 指定发送账号: Using(account_id).Func() -> 设置_account_id
           示例: Send.Using("bot1").Text("hi")
        3. 组合使用: Using(account_id).To(type,id).Func()
           示例: Send.Using("bot1").To("user","123").Text("hi")
        4. 直接调用: Func() -> 不设置目标属性
           示例: Send.Text("broadcast")
        
        5. 链式调用（修饰方法返回self以支持链式）:
           示例: Send.To("group","123").At("456").Reply("789").Text("hi")
        """
        
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)
            # 链式调用状态变量
            self._at_user_ids = []       # @的用户列表
            self._reply_message_id = None # 回复的消息ID
            self._at_all = False         # 是否@全体
        
        def At(self, user_id: str) -> 'MyAdapter.Send':
            """
            @用户（可多次调用）
            
            :param user_id: 要@的用户ID
            :return: Send实例自身，支持链式调用
            """
            self._at_user_ids.append(user_id)
            return self
        
        def AtAll(self) -> 'MyAdapter.Send':
            """
            @全体成员
            
            :return: Send实例自身，支持链式调用
            """
            self._at_all = True
            return self
        
        def Reply(self, message_id: str) -> 'MyAdapter.Send':
            """
            设置回复的消息
            
            :param message_id: 要回复的消息ID
            :return: Send实例自身，支持链式调用
            """
            self._reply_message_id = message_id
            return self
        
        def Text(self, text: str):
            """发送文本消息（支持链式调用中的 At、AtAll 和 Reply）"""
            import asyncio
            
            # 构建消息段数组
            message_segments = []
            
            # 添加 @全体
            if self._at_all:
                message_segments.append({
                    "type": "mention_all",
                    "data": {}
                })
            
            # 添加 @用户列表
            for user_id in self._at_user_ids:
                message_segments.append({
                    "type": "mention",
                    "data": {"user_id": user_id}
                })
            
            # 添加回复
            if self._reply_message_id:
                message_segments.append({
                    "type": "reply",
                    "data": {"message_id": self._reply_message_id}
                })
            
            # 添加文本内容
            if self._at_all or self._at_user_ids:
                text = " " + text
            message_segments.append({
                "type": "text",
                "data": {"text": text}
            })
            
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_message",
                    message=message_segments,
                    target_type=self._target_type,
                    target_id=self._target_id,
                    account_id=self._account_id
                )
            )
            
        def Image(self, file: bytes):
            """发送图片消息（支持链式调用中的 At 和 Reply）"""
            import asyncio
            
            message_segments = []
            
            # 添加 @用户
            for user_id in self._at_user_ids:
                message_segments.append({
                    "type": "mention",
                    "data": {"user_id": user_id}
                })
            
            # 添加图片
            message_segments.append({
                "type": "image",
                "data": {"file": file}
            })
            
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_message",
                    message=message_segments,
                    target_type=self._target_type,
                    target_id=self._target_id,
                    account_id=self._account_id
                )
            )
        
        def Raw_ob12(self, message, **kwargs):
            """
            发送原始 OneBot12 格式的消息
            
            注意：此方法为可选实现，适配器可以根据平台特性决定是否重写。
            如果平台支持直接处理 OneBot12 格式的消息，可以实现此方法。
            """
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_raw_ob12",
                    message=message,
                    target_type=self._target_type,
                    target_id=self._target_id,
                    account_id=self._account_id,
                    **kwargs
                )
            )
        
        # 示例消息发送方法，继承自BaseAdapter.Send
        # 可以重写提供平台特定实现
        def Example(self, text: str):
            """发送示例消息"""
            # 在实际实现中，这里应该调用平台特定的API
            # 这里保留BaseAdapter.Send的默认实现
            return super().Example(text)

    # 这里的call_api方法需要被实现, 哪怕他是类似邮箱时一个轮询一个发送stmp无需请求api的实现
    # 因为这是必须继承的方法
    async def call_api(self, endpoint: str, **params):
        """
        调用平台API
        
        :param endpoint: API端点
        :param params: API参数
        :return: API调用结果
        :raises NotImplementedError: 必须由子类实现
        """
        # 这里应该实现实际的平台API调用逻辑
        # 示例中仅抛出未实现异常
        raise NotImplementedError(f"需要实现平台特定的API调用: {endpoint}")

    # 适配器设定了启动和停止的方法，用户可以直接通过 sdk.adapter.setup() 来启动所有适配器，
    # 当然在底层捕捉到您adapter的错误时我们会尝试停止适配器再进行重启等操作
    # 启动方法，你需要在这里定义你的adapter启动时候的逻辑
    async def start(self):
        """
        启动适配器
        
        :raises NotImplementedError: 必须由子类实现
        """
        # 这里应该实现实际的适配器启动逻辑
        # 例如：建立WebSocket连接、启动HTTP服务器等
        self.logger.info(f"启动MyAdapter，配置模式: {self.config.get('mode', 'unknown')}")
        raise NotImplementedError("需要实现适配器启动逻辑")
    
    # 停止方法，你需要在这里进行必要的释放资源等逻辑
    async def shutdown(self):
        """
        关闭适配器
        
        :raises NotImplementedError: 必须由子类实现
        """
        # 这里应该实现实际的适配器关闭逻辑
        # 例如：关闭WebSocket连接、停止HTTP服务器等
        self.logger.info("关闭MyAdapter")
        raise NotImplementedError("需要实现适配器关闭逻辑")
