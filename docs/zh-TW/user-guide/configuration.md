# 配置檔案說明
> 這份文件將介紹框架的配置檔案，如果有第三方模組需要配置，請參考模組的文件。

ErisPulse 使用 TOML 格式的配置檔案 `config/config.toml` 來管理專案配置。

## 配置檔案位置

配置檔案位於專案根目錄的 `config/` 資料夾中：

```
project/
├── config/
│   └── config.toml
├── main.py
```

## 完整配置範例

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
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true
```

## 伺服器配置

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聽位址，0.0.0.0 表示所有介面 |
| port | integer | 8000 | 監聽埠號 |
| ssl_certfile | string | 空 | SSL 憑證檔案路徑 |
| ssl_keyfile | string | 空 | SSL 私鑰檔案路徑 |

## 日誌配置

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| level | string | INFO | 日誌層級：DEBUG, INFO, WARNING, ERROR, CRITICAL |
| log_files | array | 空 | 日誌輸出檔案列表 |
| memory_limit | integer | 1000 | 記憶體中保存的日誌筆數 |

## 框架配置

```toml
[ErisPulse.framework]
enable_lazy_loading = true
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | 是否啟用模組懶加載 |

## 儲存配置

```toml
[ErisPulse.storage]
use_global_db = false
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| use_global_db | boolean | false | 是否使用全域資料庫（套件內）而非專案資料庫 |

## 事件配置

### 指令配置

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| prefix | string | / | 指令前綴 |
| case_sensitive | boolean | false | 是否區分大小寫 |
| allow_space_prefix | boolean | false | 是否允許空格作為前綴 |
| must_at_bot | boolean | false | 是否必須@機器人才能觸發指令（私聊不受限制） |

### 訊息配置

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 配置項 | 類型 | 預設值 | 說明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 是否忽略機器人自己的訊息 |

## 模組配置

每個模組可以在配置檔案中定義自己的配置：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

在模組中讀取配置：

```python
from ErisPulse import sdk

config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")
```

## 下一步

- [模組管理](modules-management.md) - 了解如何管理已安裝的模組
- [開發者指南](../developer-guide/) - 學習開發自定義模組