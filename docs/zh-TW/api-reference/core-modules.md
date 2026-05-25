# 核心模組 API

本文檔詳細介紹了 ErisPulse 的核心模組 API。

## Storage 模組

### 基本操作

```python
from ErisPulse import sdk

# 設定值
sdk.storage.set("key", "value")

# 取得值
value = sdk.storage.get("key", default_value)

# 取得所有鍵
keys = sdk.storage.keys()

# 刪除值
sdk.storage.delete("key")
```

### 事務操作

```python
# 使用事務確保資料一致性
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # 如果任何操作失敗，所有變更都會回滾
```

### 批次操作

```python
# 批次設定
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批次取得
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# 批次刪除
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL 鏈式查詢

Storage 模組提供鏈式呼叫風格的通用 SQL 查詢建構器，支援自訂表的 CRUD 操作。

> 詳見 [SQL 查詢建構器](../advanced/sql-builder.md) 取得完整文件。

```python
from ErisPulse import sdk

# 建立自訂表
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# 插入資料
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 批次插入
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# 查詢資料
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# 更新資料
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# 刪除資料
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# 計數
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性檢查
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# 取得單條記錄
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# 修改表結構
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 檢查表是否存在
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# 事務中的鏈式操作
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# 複用查詢條件
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### 存儲後端抽象

`StorageManager` 繼承自 `BaseStorage` 抽象基類，支援未來拓展其他存儲介質（Redis、MySQL 等）。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage 定義了統一介面：get/set/delete/Table/CreateTable/DropTable 等
# BaseQueryBuilder 定義了鏈式查詢介面：Select/Insert/Update/Delete/Where/OrderBy/Limit 等
```

## Config 模組

### 讀取配置

```python
from ErisPulse import sdk

# 取得配置
config = sdk.config.getConfig("MyModule", {})

# 取得巢狀配置
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### 寫入配置

```python
# 設定配置
sdk.config.setConfig("MyModule", {"key": "value"})

# 設定巢狀配置
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### 配置範例

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # 建立預設配置
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # 第三個參數為 True 時，立即儲存配置，是方便使用者可以直接修改設定檔的
        return default_config
    return config
```

### 配置審計

Config 模組內建呼叫方感知和審計功能，可追蹤配置的讀寫來源：

```python
# 啟用審計（預設關閉）
sdk.config.enable_audit(True)

# 監聽配置變更
@sdk.config.on_change("MyModule")
def on_config_change(key, old_value, new_value, caller):
    print(f"配置變更: {key}")
    print(f"  舊值: {old_value} -> 新值: {new_value}")
    print(f"  呼叫方: {caller.file}:{caller.lineno} ({caller.function})")

# 取得審計日誌
log = sdk.config.get_audit_log(limit=10)
for entry in log:
    print(f"[{entry.timestamp}] {entry.operation} {entry.key} by {entry.caller.function}")

# 關閉審計
sdk.config.enable_audit(False)
```

審計日誌中每條記錄包含：
- `operation`: 操作類型（`get` / `set`）
- `key`: 配置鍵路徑
- `caller`: 呼叫方資訊（檔案名、行號、函數名、模組名）
- `timestamp`: 操作時間戳

## Logger 模組

### 基本日誌

```python
from ErisPulse import sdk

# 不同日誌層級
sdk.logger.debug("除錯資訊")
sdk.logger.info("執行資訊")
sdk.logger.warning("警告資訊")
sdk.logger.error("錯誤資訊")
sdk.logger.critical("致命錯誤")
```

### 子日誌記錄器

```python
# 取得子日誌記錄器
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("子模組日誌")

# 子模組還可以有子模組的日誌，這樣可以更精確地控制日誌輸出
child_logger.get_child("utils")
```

### 日誌輸出

```python
# 設定輸出檔案
sdk.logger.set_output_file("app.log")

# 儲存日誌到檔案
sdk.logger.save_logs("log.txt")
```

## Adapter 模組

### 取得適配器

```python
from ErisPulse import sdk

# 取得適配器實例
adapter = sdk.adapter.get("platform_name")

# 透過屬性存取
adapter = sdk.adapter.platform_name
```

### 適配器事件

```python
# 監聽標準事件
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 監聽特定平台的事件
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# 監聽平台原生事件
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### 適配器管理

```python
# 取得所有平台
platforms = sdk.adapter.platforms

# 檢查適配器是否存在
exists = sdk.adapter.exists("platform_name")

# 啟用/停用適配器
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# 啟動/關閉適配器
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1