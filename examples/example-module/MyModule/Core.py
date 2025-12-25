from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command, message, notice

class Main(BaseModule):
    """
    MyModule模块示例
    
    这是一个自定义模块示例，继承自BaseModule基类
    实现了标准化的模块生命周期管理和事件处理
    """
    
    def __init__(self, sdk):    # 这里也可以不接受sdk参数而使用导入的sdk实例 SDK会自动判断这个类是否接收了参数
        self.sdk = sdk
        self.logger = self.sdk.logger.get_child("MyModule")
        self.storage = self.sdk.storage
        self.adapter = self.sdk.adapter
        
        self.logger.info("MyModule 初始化完成")
        self.config = self._load_config()
        
        # 注册HTTP和WebSocket路由（可选）
        self._register_routes()
    
    @staticmethod
    def should_eager_load() -> bool:
        """
        模块是否应该在启动时加载
        默认为False(即懒加载)
        
        :return: 是否应该在启动时加载
        """
        return False
    
    async def on_load(self, event: dict) -> bool:
        """
        当模块被加载时调用
        
        :param event: 事件内容
        :return: 处理结果
        """
        # 注册命令处理器
        await self._register_commands()
        
        # 注册消息和通知处理器
        await self._register_message_handlers()
        
        self.logger.info(f"模块已加载: {event}")
        return True
    
    async def on_unload(self, event: dict) -> bool:
        """
        当模块被卸载时调用
        
        :param event: 事件内容
        :return: 处理结果
        """
        # 在这里可以清理资源或取消注册事件处理器
        self.logger.info(f"模块已卸载: {event}")
        return True
    
    # 加载配置方法，你需要在这里进行必要的配置加载逻辑
    def _load_config(self):
        """
        从配置中加载模块配置
        如果不存在则使用默认值
        """
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "welcome_message": "欢迎添加我为好友！",
                "echo_enabled": True,
                "debug_mode": False
            }
            self.sdk.config.setConfig("MyModule", default_config)
            self.logger.warning("未找到模块配置, 对应模块配置已经创建到config.toml中")
            return default_config
        return config
    
    async def _register_commands(self):
        """注册命令处理器"""
        # 注册命令处理器
        @command("hello", help="发送问候消息")
        async def hello_command(event):
            platform = event["platform"]
            user_id = event["user_id"]
            
            if hasattr(self.adapter, platform):
                adapter_instance = getattr(self.adapter, platform)
                await adapter_instance.Send.To("user", user_id).Text("Hello World!")
        
        # 注册帮助命令
        @command("help", aliases=["h"], help="显示帮助信息")
        async def help_command(event):
            platform = event["platform"]
            user_id = event["user_id"]
            help_text = command.help()
            
            if hasattr(self.adapter, platform):
                adapter_instance = getattr(self.adapter, platform)
                await adapter_instance.Send.To("user", user_id).Text(help_text)
        
        # 注册回显命令
        @command("echo", help="回显消息", usage="/echo <内容>")
        async def echo_command(event):
            if not self.config.get("echo_enabled", True):
                return
                
            platform = event["platform"]
            user_id = event["user_id"]
            args = event["command"]["args"]
            
            if not args:
                response = "请提供要回显的内容"
            else:
                response = " ".join(args)
            
            if hasattr(self.adapter, platform):
                adapter_instance = getattr(self.adapter, platform)
                await adapter_instance.Send.To("user", user_id).Text(response)
    
    async def _register_message_handlers(self):
        """注册消息和通知处理器"""
        # 注册私聊消息处理器
        @message.on_private_message()
        async def private_message_handler(event):
            if self.config.get("debug_mode", False):
                self.logger.info(f"收到私聊消息: {event}")
        
        # 注册好友添加通知处理器
        @notice.on_friend_add()
        async def friend_add_handler(event):
            self.logger.info(f"新好友添加: {event}")
            
            # 发送欢迎消息
            platform = event["platform"]
            user_id = event["user_id"]
            
            if hasattr(self.adapter, platform):
                adapter_instance = getattr(self.adapter, platform)
                welcome_msg = self.config.get("welcome_message", "欢迎添加我为好友！")
                await adapter_instance.Send.To("user", user_id).Text(welcome_msg)
    
    def _register_routes(self):
        """注册HTTP和WebSocket路由（可选）"""
        # 这里可以注册HTTP路由和WebSocket路由
        # 示例：
        # 
        # async def get_info():
        #     return {
        #         "module": "MyModule", 
        #         "version": "1.0.0",
        #         "status": "running"
        #     }
        # 
        # self.sdk.router.register_http_route(
        #     module_name="MyModule",
        #     path="/info",
        #     handler=get_info,
        #     methods=["GET"]
        # )
        pass
    
    def hello(self):
        """可以被其他模块调用的方法"""
        self.logger.info("Hello World!")
        # 其它模块可以通过 sdk.MyModule.hello() 调用此方法