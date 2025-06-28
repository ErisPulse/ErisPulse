# AI 模块生成指南

使用本指南，你可以通过AI快速生成符合ErisPulse规范的模块代码，无需从零开始编写。

## 快速开始

1. **获取开发文档**  
   下载 `docs/ForAIDocs/ErisPulseDevelop.md` - 它包含了所有AI需要的开发规范、适配器接口和SDK参考。

2. **明确你的需求**  
   确定模块功能、使用的适配器、依赖关系等核心要素。

3. **向AI描述需求**  
   使用下面的标准格式清晰地描述你的模块需求。

## 如何描述你的需求

用简单的话告诉AI你想要什么模块，比如：

"帮我做一个[模块名称]模块，它能[主要功能]"
"这个模块需要：
- [功能点1]
- [功能点2]
- [其他你想要的]

技术方面：
- 用[适配器名称]来连接
- 需要[依赖项]支持
- [其他技术上的说明]"

## 示例：通知提醒模块

### 你可以这样描述

"帮我做个ReminderBot模块，用来管理各种提醒
这个模块需要：
- 能接收用户设置的提醒，比如'/remind 明天10点开会'
- 到时间了能自动发通知
- 支持一次性和重复的提醒

技术方面：
- 用YunhuAdapter来接收用户指令
- 需要sdk.util.scheduler处理定时任务
- 用sdk.storage保存提醒数据"

### AI生成代码示例

```python
# __init__.py
moduleInfo = {
    "meta": {
        "name": "ReminderBot",
        "version": "1.0.0",
        "description": "定时提醒模块",
        "author": "YourName",
        "license": "MIT"
    },
    "dependencies": {
        "requires": [],
        "optional": [],
        "pip": []
    }
}

from .Core import Main
```

```python
# Core.py
from datetime import datetime

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.storage = sdk.storage
        self.scheduler = sdk.util.scheduler
        
        @sdk.adapter.Yunhu.on("command")
        async def handle_reminder(data):
            if data.event.message.commandName == "remind":
                await self.process_reminder(data)

    async def process_reminder(self, data):
        # 实现提醒逻辑
        pass
```

## 常见问题

Q: 如何测试生成的模块？  
A: 将生成的代码放入ErisPulse的modules目录，重启服务即可加载测试。

Q: 生成的代码不符合我的需求怎么办？  
A: 可以调整需求描述后重新生成，或直接在生成代码基础上进行修改。

Q: 需要更复杂的功能怎么办？  
A: 可以将复杂功能拆分为多个简单模块，或分阶段实现。