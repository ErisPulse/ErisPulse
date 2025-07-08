# 你也可以直接导入对应的模块
# from ErisPulse import sdk
# from ErisPulse.Core import logger, env, raiserr, adapter

class Main:
    def __init__(self, sdk):    # 这里也可以不接受sdk参数
        self.sdk = sdk
        self.env = self.sdk.env
        self.logger = self.sdk.logger
        
        self.logger.info("MyModule 初始化完成")
        self.load_config()

    def load_config(self):
        self.config = self.env.get("MyModule", {})

        if self.config is None:
            self.logger.error("无法加载配置文件")

            self.env.setConfig("MyModule", {
                "key1": "value1",
                "key2": ["value2", "value3"],
                "key3": {
                    "key4": "value4",
                    "key5": "value5"
                },
                "key6": True
            })
            
    def hello(self):
        self.logger.info("Hello World!")
        # 其它模块可以通过 sdk.MyModule.hello() 调用此方法