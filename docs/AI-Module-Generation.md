# 使用 AI 根据文档生成模块

ErisPulse 的完整文档已经为AI提供了所有开发所需的信息。现在，你可以直接将 **你的需求** 告诉 AI，并让它根据 ErisPulse 的规范和文档结构，为你生成符合要求的模块代码。

---

## 你需要做的仅仅是：

1. **阅读并理解我们的文档内容**
   - 尤其是 DEVELOPMENT.md 中关于模块结构、SDK 接口调用方式等内容。
2. **明确你要实现的功能**
   - 包括：模块功能描述、使用的适配器（如 YunhuAdapter）、是否需要依赖其他模块等。
3. **告诉 AI 你的需求**
   - 描述得越清晰，AI 生成的结果越准确！

---

## 如何向 AI 描述你的模块需求？

请按照以下格式组织你的描述，确保包含以下信息：

### 示例模板：
```
我需要一个用于处理用户指令的模块，名为 CommandProcessor。
该模块应该能够：
- 监听 Yunhu 平台的指令事件
- 当用户发送 "/help" 时，回复帮助信息

请根据 ErisPulse 的模块规范和文档，为我生成完整的模块文件结构和代码
```

---

## 需要哪些文档来生成模块？

### 使用 AI 生成模块时，需要以下文档：

| 文档 | 内容说明 |
|------|----------|
| `DEVELOPMENT.md` | 提供模块结构、入口文件、Main 类定义规范 |
| `ADAPTERS.md` | 如果你使用了适配器（如 Yunhu、Telegram），AI 会参考其中的事件监听和消息发送方式 |
| `REFERENCE.md` | SDK 接口调用方式（如 `sdk.env`, `sdk.logger`, `sdk.adapter` 等） |

#### 文档的位置在 ErisPulse 项目的 docs 目录下

> 如果你有git环境，可以直接使用 git clone 命令下载 ErisPulse 项目:

```bash
git clone https://github.com/ErisPulse/ErisPulse.git
```

> 如果你没有git环境，也可以访问我们的github项目直接下载 ErisPulse 项目的压缩包：

https://github.com/ErisPulse/ErisPulse

---

## 示例：生成一个天气查询模块

### 用户输入需求：

> 我需要一个天气查询模块 WeatherBot，当用户在群聊中发送“/weather 上海”时，机器人会调用 OpenWeatherMap API 查询天气，并返回中文格式的天气信息。  
> 要求：
> - 使用 YunhuAdapter 监听指令消息；
> - 使用 sdk.util.cache 缓存结果；
> - 模块结构符合 ErisPulse 规范。

并且将 docs 目录下的 `DEVELOPMENT.md`、`ADAPTERS.md`、`REFERENCE.md` 作为附件发送给 AI。

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
        "requires": [],
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
                if not city:
                    await self.sdk.adapter.Yunhu.Send.To(data.chat).Text("请指定城市名称，例如：/weather 上海")
                    return
                chat_type = data.event.chatType
                sender_type = "group" if chat_type == "group" else "user"
                sender_id = data.chat.chatId if chat_type == "group" else data.event.sender.senderId
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

---

你不再需要从零开始写模块。只需：

- 发送给AI, ErisPulse的文档内容  
- 明确你的需求  
- 向 AI 描述你的想法  
- 运行并测试
