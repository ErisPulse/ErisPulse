from ErisPulse.Core.Event import command, message, notice

class Main:
    def __init__(self, sdk=None):    # 这里也可以不接受sdk参数
        self.sdk = sdk or globals().get('sdk', __import__('ErisPulse').sdk)
        self.env = self.sdk.env
        self.logger = self.sdk.logger
        self.adapter = self.sdk.adapter
        
        self.logger.info("MyModule 初始化完成")
        self.config = self._load_config()
        
        # 注册事件处理器
        self._register_event_handlers()
    
    # 加载配置方法，你需要在这里进行必要的配置加载逻辑
    def _load_config(self):
        _config = self.sdk.config.getConfig("MyModule", {})
        if _config is None:
            default_config = {
                "key": "value",
                "key2": [1, 2, 3],
                "key3": {
                    "key4": "value4"
                }
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return _config
    
    def _register_event_handlers(self):
        """注册事件处理器"""
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
        
        # 注册私聊消息处理器
        @message.on_private_message()
        async def private_message_handler(event):
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
                await adapter_instance.Send.To("user", user_id).Text("欢迎添加我为好友！")
    
    def hello(self):
        self.logger.info("Hello World!")
        # 其它模块可以通过 sdk.MyModule.hello() 调用此方法