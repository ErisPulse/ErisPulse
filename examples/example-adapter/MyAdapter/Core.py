import asyncio
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import logger, config as config_manager, adapter

class MyAdapter(BaseAdapter):
    """
    MyAdapter适配器示例
    
    这是一个自定义适配器示例，继承自BaseAdapter基类
    实现了SendDSL风格的链式调用接口
    """
    
    def __init__(self, sdk):    # 这里也可以不接受sdk参数而使用导入的sdk实例 SDK会自动判断这个类是否接收了参数
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
        """
        
        # 可以重写Text方法提供平台特定实现
        def Text(self, text: str):
            """发送文本消息"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,    # 来自To()设置的属性
                    recvType=self._target_type # 来自To(type,id)设置的属性
                )
            )
            
        # 添加新的消息类型
        def Image(self, file: bytes):
            """发送图片消息"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,    # 自动使用To()设置的属性
                    recvType=self._target_type
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