import asyncio
from typing import Optional
from ErisPulse.Core import BaseAdapter, EventDataBase
# 你也可以直接导入对应的模块
# from ErisPulse import sdk
# from ErisPulse.Core import logger, env, raiserr, adapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):    # 这里也可以不接受sdk参数
        self.sdk = sdk
        self.env = self.sdk.env
        self.logger = self.sdk.logger
        
        self.logger.info("MyModule 初始化完成")
        self.load_config()
    # 加载配置方法，你需要在这里进行必要的配置加载逻辑
    def load_config(self):
        self.config = self.env.getConfig("MyAdapter", {})

        if self.config is None:
            self.logger.error("请在env.py中添加MyAdapter配置")
            self.env.setConfig("MyAdapter", {
                "mode": "server",
                "server": {
                    "host": "127.0.0.1",
                    "port": 8080
                },
                "client": {
                    "url": "http://127.0.0.1:8080",
                    "token": ""
                }
            })
    class Send(BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        # 底层SendDSL中提供了To方法，用户调用的时候类会被定义 `self._target_type` 和 `self._target_id`/`self._target_to` 三个属性
        # 当你只需要一个接受的To时，例如 mail 的To只是一个邮箱，那么你可以使用 `self.To(email)`，这时只会有 `self._target_id`/`self._target_to` 两个属性被定义
        # 或者说你不需要用户的To，那么用户也可以直接使用 Send.Func(text) 的方式直接调用这里的方法
        
        # 可以重写Text方法提供平台特定实现
        def Text(self, text: str):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
            
        # 添加新的消息类型
        def Image(self, file: bytes):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )

    # 这里的call_api方法需要被实现, 哪怕他是类似邮箱时一个轮询一个发送stmp无需请求api的实现
    # 因为这是必须继承的方法
    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError()

    # 适配器设定了启动和停止的方法，用户可以直接通过 sdk.adapter.setup() 来启动所有适配器，
    # 当然在底层捕捉到您adapter的错误时我们会尝试停止适配器再进行重启等操作
    # 启动方法，你需要在这里定义你的adapter启动时候的逻辑
    async def start(self):
        raise NotImplementedError()
    # 停止方法，你需要在这里进行必要的释放资源等逻辑
    async def shutdown(self):
        raise NotImplementedError()
    

class MyAdapterEventParser(EventDataBase):
    """
    平台事件解析器
    
    将MyAdapter原始事件数据转换为统一格式
    

    用法示例：
    >>> event = MyAdapterEventParser(raw_event)
    >>> print(f"收到来自 {event.user_id} 的消息: {event.content}")
    >>> if event.is_bot: 
    >>>     print("注意：此消息来自机器人")
    """

    # ----- 核心属性实现 -----
    @property
    def platform(self) -> str:
        """平台标识符"""
        return "my_adapter"
    
    @property
    def type(self) -> str:
        """事件主类型（转换平台特有事件类型为通用类型）"""
        mapping = {
            "msg": "message",
            "msg_edit": "message_update",
            "join": "guild_member_add",
            "cmd": "command"
        }
        return mapping.get(self.event.get("event_type"), "unknown")
    
    @property
    def timestamp(self) -> float:
        """精确到毫秒的时间戳"""
        return self.event["timestamp"] / 1000  # 转换毫秒为秒

    # ----- 消息相关增强实现 -----
    @property
    def content(self) -> Optional[str]:
        """支持嵌套消息结构"""
        if 'message' in self.event:
            return self.event['message'].get('text')
        return None
    
    @property
    def message_id(self) -> Optional[str]:
        """复合型消息ID（平台标识+消息ID）"""
        if 'message' in self.event:
            return f"{self.platform}_{self.event['message']['id']}"
        return None

    # ----- 用户相关增强实现 -----
    @property
    def user_id(self) -> Optional[str]:
        """支持不同事件源的用户字段"""
        if 'user' in self.event:
            return self.event['user']['id']
        elif 'sender' in self.event:
            return self.event['sender']['uid']
        return None
    
    @property
    def is_bot(self) -> bool:
        """检查机器人标识字段"""
        user_flags = self.event.get('user', {}).get('flags', 0)
        return bool(user_flags & 0x1)  # 使用位掩码检查bot标志
    
    # ----- 群组相关增强实现 -----
    @property
    def guild_id(self) -> Optional[str]:
        """转换平台特有的群组标识"""
        return self.event.get('group', {}).get('gid')
    
    @property
    def channel_id(self) -> Optional[str]:
        """转换平台特有的频道标识"""
        return self.event.get('channel', {}).get('cid')

    # ----- 高级特性实现 -----
    @property
    def references(self) -> Optional[Dict]:
        """解析消息引用/回复"""
        if 'reference' in self.event.get('message', {}):
            ref = self.event['message']['reference']
            return {
                "message_id": ref["msg_id"],
                "user_id": ref["author_id"],
                "content_preview": ref.get("preview", "")
            }
        return None
    
    @property
    def attachments(self) -> List[Dict]:
        """统一附件格式"""
        attachments = []
        for attach in self.event.get('message', {}).get('attachments', []):
            attachments.append({
                "type": attach["file_type"],
                "name": attach["file_name"],
                "url": attach["download_url"],
                "base64": attach["base64_content"] if attach["file_type"] == "image" else None,
                "size": attach["file_size"]
            })
        return attachments
    