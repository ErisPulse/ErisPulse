# AI 模块生成指南

使用本指南，你可以通过AI快速生成符合ErisPulse规范的模块代码，无需从零开始编写。

## 快速开始

1. **获取开发文档**  
   下载 `docs/ForAIDocs/ErisPulseDevelop.md` - 它包含了所有AI需要的开发规范、适配器接口和SDK参考。

2. **明确你的需求**  
   确定模块功能、使用的适配器、依赖关系等核心要素。

3. **向AI描述需求**  
   使用下面的标准格式清晰地描述你的模块需求。

## 需求描述规范

请按照以下格式描述你的模块需求：

```
我需要一个用于处理用户指令的模块，名为 CommandProcessor。
该模块应该能够：
- 监听 Yunhu 平台的指令事件
- 当用户发送 "/help" 时，回复帮助信息

请根据 ErisPulse 的模块规范和文档，为我生成完整的模块文件结构和代码
```

### AI生成代码示例

## 示例：生成一个天气查询模块

### 用户输入需求：

> 我需要一个天气查询模块 WeatherBot，当用户在群聊中发送“/weather 上海”时，机器人会调用 OpenWeatherMap API 查询天气，并返回中文格式的天气信息。  
> 要求：
> - 使用 YunhuAdapter 监听指令消息；
> - 使用 sdk.util.cache 缓存结果；
> - 模块结构符合 ErisPulse 规范。

并且将刚刚下载的 `ErisPulseDevelop.md` 作为附件发送给 AI。

### AI 输出示例：

```python
# __init__.py
moduleInfo = {
    "meta": {
        "name": "WeatherBot",
        "version": "1.0.0",
        "description": "天气查询模块",
        "author": "YourName",
        "license": "MIT"
    },
    "dependencies": {
        "requires": [
            "YunhuAdapter"
        ],
        "optional": [],
        "pip": ["aiohttp"]
    }
}

from .Core import Main
```

```python
# Core.py
import aiohttp
import time

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env
        self.util = sdk.util

        @sdk.adapter.Yunhu.on("command")
        async def handle_weather(data):
            if data.event.message.commandName.lower() == "weather":
                city = data.event.message.content.text.strip()
                chat_type = data.event.chatType
                sender_type = "group" if chat_type == "group" else "user"
                sender_id = data.chat.chatId if chat_type == "group" else data.event.sender.senderId

                if not city:
                    await self.sdk.adapter.Yunhu.Send.To(sender_type, sender_id).Text("请指定城市名称，例如：/weather 上海")
                    return
                await self.reply_weather(sender_type, sender_id, city)

    @sdk.util.cache
    async def get_weather_data(self, city: str):
        api_key = self.env.get("WEATHER_API_KEY")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception("无法获取天气信息")

    async def reply_weather(self, sender_type, sender_id, city):
        try:
            data = await self.get_weather_data(city)
            temperature = data["main"]["temp"] - 273.15
            await self.sdk.adapter.Yunhu.Send.To(sender_type, sender_id).Text(f"{city} 的温度是 {temperature:.1f}℃")
        except Exception as e:
            self.logger.error(f"获取天气失败: {e}")
            await self.sdk.adapter.Yunhu.Send.To(sender_type, sender_id).Text(f"获取天气失败，请稍后再试。")
```

## 常见问题

Q: 如何测试生成的模块？  
A: 将生成的代码放入ErisPulse项目(初始化过的你自己的项目内会有这个文件夹)的modules目录，重启服务即可加载测试。

Q: 生成的代码不符合我的需求怎么办？  
A: 可以调整需求描述后重新生成，或直接在生成代码基础上进行修改。

Q: 需要更复杂的功能怎么办？  
A: 可以将复杂功能拆分为多个简单模块，或分阶段实现。

Q: 我可以把这个模块发布到ErisPulse吗？
A: 当然可以！但是我们会审查你的代码，确保它符合我们的规范。