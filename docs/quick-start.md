# 快速开始

## 安装 ErisPulse

使用 pip 安装最新版本：

```bash
pip install ErisPulse
```

> 📌 **提示**：如果你在开发过程中需要调试或修改源码，建议克隆仓库并使用本地安装：
```bash
git clone https://github.com/ErisPulse/ErisPulse.git
cd ErisPulse
pip install -e .
```

---

## 初始化项目

1. 创建项目目录并进入：

```bash
mkdir my_bot && cd my_bot
```

2. 初始化 SDK 并生成配置文件：

```python
from ErisPulse import sdk
sdk.init()
```

这将在当前目录下自动生成 `env.py` 配置模板文件。

---

## 安装模块

你可以通过 CLI 安装所需模块：

```bash
epsdk install YunhuAdapter OneBotAdapter AIChat
```

你也可以手动编写模块逻辑，参考开发者文档进行模块开发。

---

## 运行你的机器人

创建主程序文件 `main.py`：

```python
from ErisPulse import sdk
import asyncio

async def main():
    sdk.init()

    # 启动所有适配器
    await sdk.adapter.startup()
    
    # 示例：发送日志消息
    sdk.logger.info("机器人已启动")

    # 保持运行
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

然后运行：

```bash
epsdk run main.py
```

或者使用热重载模式（开发时推荐）：

```bash
epsdk run main.py --reload
```

---

## 核心功能示例

### 日志记录

```python
sdk.logger.info("机器人已启动")
sdk.logger.error("发生了一个错误")
```

你还可以设置日志输出到文件：

```python
sdk.logger.set_output_file("bot.log")
```

### 环境配置

```python
# 设置配置
sdk.env.set("API_KEY", "your-api-key")

# 获取配置
api_key = sdk.env.get("API_KEY")
```

### 错误处理

```python
# 注册自定义错误
sdk.raiserr.register("MyError", doc="我的自定义错误")

# 抛出错误
sdk.raiserr.MyError("发生了自定义错误")
```

---

## 使用适配器（Adapter）

ErisPulse 支持多平台适配器，例如 Yunhu、OneBot、Telegram 等。以下是一个简单的适配器使用示例：

```python
# 发送文本消息给指定用户
await sdk.adapter.Yunhu.Send.To("user", "U1001").Text("你好！")
```

你可以在项目 `devs` 文件夹下的测试文件中找到完整的官方测试适配器使用案例，如：

- `test_telegram.py`
- `test_mail.py`

---

## 模块管理（CLI）

你可以通过命令行工具管理模块：

| 命令       | 描述                      | 示例                          |
|------------|---------------------------|-------------------------------|
| enable     | 激活指定模块              | epsdk enable chatgpt          |
| disable    | 停用指定模块              | epsdk disable weather         |
| install    | 安装一个或多个模块        | epsdk install translator      |
| list       | 列出模块（可筛选）       | epsdk list --module=payment  |
| update     | 更新模块索引               | epsdk update                  |
| origin add | 添加模块源                 | epsdk origin add https://erisdev.com/map.json |
