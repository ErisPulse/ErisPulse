# ErisPulse 框架默认配置说明

本文档详细解释了 ErisPulse 框架的默认配置项及其含义。这些配置项控制着框架的核心行为，包括服务器设置、日志系统、存储系统等方面。

## 配置结构总览

ErisPulse 的默认配置结构如下：

```python
DEFAULT_ERISPULSE_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "ssl_certfile": None,
        "ssl_keyfile": None
    },
    "logger": {
        "level": "INFO",
        "log_files": [],
        "memory_limit": 1000
    },
    "storage": {
        "max_snapshot": 20
    },
    "modules": {},
    "adapters": {},
    "framework": {
        "enable_lazy_loading": True
    }
}
```

下面我们将逐一解释每个配置项的作用和意义。

## 服务器配置 (server)

服务器配置控制着 ErisPulse 内置 HTTP 服务器的行为：

- `host`: 服务器监听的主机地址，默认为 `"0.0.0.0"`，表示监听所有网络接口
- `port`: 服务器监听的端口号，默认为 `8000`
- `ssl_certfile`: SSL 证书文件路径，用于 HTTPS 连接，`None` 表示不使用 HTTPS
- `ssl_keyfile`: SSL 私钥文件路径，用于 HTTPS 连接，`None` 表示不使用 HTTPS

配置示例：
```toml
[ErisPulse.server]
host = "127.0.0.1"
port = 8080
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

## 日志配置 (logger)

日志配置控制着框架的日志系统行为：

- `level`: 日志级别，默认为 `"INFO"`，可选值包括 `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
- `log_files`: 日志输出文件列表，默认为空列表，表示只在控制台输出
- `memory_limit`: 内存中保存的日志条数限制，默认为 `1000` 条

配置示例：
```toml
[ErisPulse.logger]
level = "DEBUG"
log_files = ["app.log", "debug.log"]
memory_limit = 2000
```

## 存储配置 (storage)

存储配置控制着框架内置存储系统的行为：

- `max_snapshot`: 最大快照数量，默认为 `20`，用于限制自动创建的快照数量

配置示例：
```toml
[ErisPulse.storage]
max_snapshot = 50
```

## 模块配置 (modules)

模块配置区域用于存放各个模块的特定配置。默认为空字典，模块可以在运行时在此处添加自己的配置项。

配置示例：
```toml
[ErisPulse.modules]
[ErisPulse.modules.MyModule]
setting1 = "value1"
setting2 = 42
```

## 适配器配置 (adapters)

适配器配置区域用于存放各个适配器的特定配置。默认为空字典，适配器可以在运行时在此处添加自己的配置项。

配置示例：
```toml
[ErisPulse.adapters]
[ErisPulse.adapters.Yunhu]
token = "your_token_here"
```

## 框架配置 (framework)

框架配置控制着框架核心功能的行为：

- `enable_lazy_loading`: 是否启用模块懒加载，默认为 `True`。启用后，模块将在首次被访问时才加载，有助于提高启动速度

配置示例：
```toml
[ErisPulse.framework]
enable_lazy_loading = true
```

## 配置补充机制

ErisPulse 框架具有智能配置补充机制。当配置缺失时，框架会自动使用默认值填充缺失的配置项，确保系统正常运行。这个机制通过 _ensure_erispulse_config_structure 函数实现。

无论是在初始化时还是在运行时更新配置，框架都会确保配置结构的完整性。

## 高级配置特性

### 内存缓存机制

配置系统实现了内存缓存机制，提高配置访问性能：

```python
# 配置缓存
self._config_cache: Dict[str, Any] = {}
```

当配置被读取时，首先检查内存缓存，如果缓存中有数据则直接返回，避免频繁的文件I/O操作。

### 延迟写入机制

为提高性能，配置系统实现了延迟写入机制：

```python
# 延迟写入标志
self._pending_save = False

# 设置配置时标记需要保存
def setConfig(self, path: str, value: Any) -> None:
    self._config_cache[path] = value
    self._pending_save = True

# 在适当时机批量保存
def _save_if_needed(self) -> None:
    if self._pending_save:
        self._save_to_file()
        self._pending_save = False
```

这种机制减少了频繁的文件写入操作，特别是在短时间内多次更新配置时。

### 线程安全

配置系统使用线程锁确保多线程环境下的安全访问：

```python
import threading

# 线程锁
self._config_lock = threading.RLock()

# 线程安全的配置访问
with self._config_lock:
    # 配置读写操作
    pass
```

## 自定义配置

用户可以根据需要在项目的 `config.toml` 文件中自定义这些配置项。框架会在启动时读取用户配置并与默认配置合并，优先使用用户配置。

例如，要在本地开发环境中修改服务器端口和日志级别，可以在 `config.toml` 中添加：

```toml
[ErisPulse]
[ErisPulse.server]
port = 3000

[ErisPulse.logger]
level = "DEBUG"
```

这样，服务器将监听 3000 端口，日志级别将设置为 DEBUG，其他配置项仍使用默认值。