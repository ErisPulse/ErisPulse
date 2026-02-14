# 配置文件说明
> 这个文档会介绍框架的配置文件，如果有第三方模块需要配置，请参考模块的文档。

ErisPulse 使用 TOML 格式的配置文件 `config/config.toml` 来管理项目配置。

## 配置文件位置

配置文件位于项目根目录的 `config/` 文件夹中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 完整配置示例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true

[ErisPulse.storage]
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false

[ErisPulse.event.message]
ignore_self = true
```

## 服务器配置

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 监听地址，0.0.0.0 表示所有接口 |
| port | integer | 8000 | 监听端口号 |
| ssl_certfile | string | 空 | SSL 证书文件路径 |
| ssl_keyfile | string | 空 | SSL 私钥文件路径 |

## 日志配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| level | string | INFO | 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL |
| log_files | array | 空 | 日志输出文件列表 |
| memory_limit | integer | 1000 | 内存中保存的日志条数 |

## 框架配置

```toml
[ErisPulse.framework]
enable_lazy_loading = true
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否启用模块懒加载 |

## 存储配置

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全局数据库（包内）而非项目数据库 |

## 事件配置

### 命令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| prefix | string | / | 命令前缀 |
| case_sensitive | boolean | false | 是否区分大小写 |
| allow_space_prefix | boolean | false | 是否允许空格作为前缀 |

### 消息配置

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 配置项 | 类型 | 默认值 | 说明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略机器人自己的消息 |

## 模块配置

每个模块可以在配置文件中定义自己的配置：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模块中读取配置：

```python
from ErisPulse import sdk

config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")
```

## 下一步

- [模块管理](modules-management.md) - 了解如何管理已安装的模块
- [开发者指南](../developer-guide/) - 学习开发自定义模块