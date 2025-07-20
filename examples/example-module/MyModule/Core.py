# 你也可以直接导入对应的模块
# from ErisPulse import sdk
# from ErisPulse.Core import logger, env, raiserr, adapter

class Main:
    def __init__(self, sdk):    # 这里也可以不接受sdk参数
        self.sdk = sdk
        self.env = self.sdk.env
        self.logger = self.sdk.logger
        
        self.logger.info("MyModule 初始化完成")
        self.config = self._load_config()
    
    # 加载配置方法，你需要在这里进行必要的配置加载逻辑
    def _load_config(self):
        _config = self.env.getConfig("MyModule", {})
        if _config is None:
            default_config = {
                "key": "value",
                "key2": [1, 2, 3],
                "key3": {
                    "key4": "value4"
                }
            }
            self.env.setConfig("MyModule", default_config)
            return default_config
        return _config
            
    def hello(self):
        self.logger.info("Hello World!")
        # 其它模块可以通过 sdk.MyModule.hello() 调用此方法
