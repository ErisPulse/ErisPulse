# SQL 查詢建構器

ErisPulse 的 Storage 模組提供鏈式呼叫風格的通用 SQL 查詢建構器，支援自訂表的建立、查詢、更新與刪除操作。

## 架構設計

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (SQLite concrete impl)  │
│    (ABC)            │             │                          │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` 是抽象基類，定義統一介面，支援未來拓展其他儲存媒體（Redis、MySQL 等）
- `StorageManager` 是目前 SQLite 具體實作，完全向後相容

## 導入

```python
from ErisPulse import sdk
# 或
from ErisPulse.Core import storage

# ABC 基類（用於型別註解或自訂實作）
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## 表管理

### 建立表

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### 檢查表是否存在

```python
if sdk.storage.HasTable("users"):
    print("users 表已存在")
```

### 刪除表

```python
sdk.storage.DropTable("users")
```

### 修改表結構

```python
# 添加欄位
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# 重新命名表
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 串連多個操作
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## 鏈式查詢

### 插入資料

```python
# 單筆插入（傳入字典）
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 批次插入（傳入字典列表）
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### 查詢資料

> **重要**：`Select()` 返回的是 `list[tuple]`（元組列表），不是字典。你需要按欄位順序用索引存取。

```python
# 查詢所有欄位
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# 查詢指定欄位
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# 按索引取值
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### 將元組轉為字典

推薦直接在鏈上呼叫 `ToDict()`，SELECT 結果自動以字典返回（欄位名 → 值）：

```python
# ToDict 鏈：結果為 list[dict]，欄位名自動取自查詢元數據（SELECT * 同樣支援）
rows = sdk.storage.Table("users").Select("name", "age").ToDict().Execute()
# rows: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, ...]

for row in rows:
    print(row["name"], row["age"])

# ExecuteOne 同樣生效
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ToDict() \
    .ExecuteOne()
# row: {"name": "Alice", "age": 30} 或 None
```

> `ToDict()` 是鏈式標記（返回 self）：未呼叫它的鏈保持原有 `list[tuple]` 行為，完全向後相容；`copy()` 會保留該標記。

手動 zip 方式（與 ToDict 等價，適合無法改鏈的場景）：

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# 方式一：循環中 zip
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# 方式二：一次性轉為字典列表
records = [dict(zip(columns, row)) for row in rows]
```

#### 獲取單筆記錄

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row 是 tuple 或 None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### 條件過濾

> `Where(condition, *params)` 支援傳入多個參數，對應多個 `?` 佔位符。

```python
# 單條件（一個佔位符，一個參數）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# 一個 Where 中使用多個佔位符
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# 多次呼叫 Where（AND 連接）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### 排序、分頁

```python
# 升序
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# 降序
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# 分頁
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### 更新資料

```python
# 條件更新
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# 全量更新
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### 刪除資料

```python
# 條件刪除
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# 全量刪除
sdk.storage.Table("users").Delete().Execute()
```

### 計數與存在性檢查

```python
# 計數
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性檢查
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## 複用查詢條件

使用 `copy()` 深拷貝建構器，複用基礎條件：

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# 基於相同條件查詢
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# 基於相同條件計數
count = base.copy().Count()

# 基於相同條件檢查存在性
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## 重設建構器

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# 重新建構查詢
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## 事務中使用

鏈式操作完全支援事務：

```python
# 提交事務
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# 回滾示例
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Alice 的記錄仍然存在
```

## 異步原生 API

2.8.0 起儲存層以異步為原生主介面，所有終止方法都有對應的 a 前綴異步版本，
異步 handler 內推薦使用（避免同步相容層短暫阻塞事件循環）：

```python
# 異步事務
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.aset("key2", {"nested": True})

# 異步鏈式查詢
rows = await sdk.storage.Table("users").Select("name", "age").ToDict().aExecute()
row = await sdk.storage.Table("users").Select("*").Where("id = ?", 1).aExecuteOne()
total = await sdk.storage.Table("users").Where("age > ?", 18).aCount()
exists = await sdk.storage.Table("users").Where("name = ?", "Alice").aExists()

# 異步 KV
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()
```

| 同步（相容層） | 異步原生 |
|------|------|
| `get` / `set` / `delete` | `aget` / `aset` / `adelete` |
| `get_all_keys` / `clear` | `aget_all_keys` / `aclear` |
| `get_multi` / `set_multi` / `delete_multi` | `aget_multi` / `aset_multi` / `adelete_multi` |
| `transaction()` | `atransaction()` |
| `CreateTable` / `DropTable` / `HasTable` | `aCreateTable` / `aDropTable` / `aHasTable` |
| `Execute` / `ExecuteOne` / `Count` / `Exists` | `aExecute` / `aExecuteOne` / `aCount` / `aExists` |

## 回傳值說明

| 操作 | 回傳型別 | 說明 |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | 元組列表，按欄位順序排列 |
| `Select().ExecuteOne()` | `tuple \| None` | 單筆元組或 None |
| `Insert().Execute()` | `int` | 受影響列數 |
| `InsertMulti().Execute()` | `int` | 插入列數 |
| `Update().Execute()` | `int` | 受影響列數 |
| `Delete().Execute()` | `int` | 受影響列數 |
| `Count()` | `int` | 符合條件列數 |
| `Exists()` | `bool` | 是否存在 |

### 回傳值處理示例

```python
# Select 回傳元組，按索引取值
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # 第一列第一欄 name
first_age = rows[0][1]   # 第一列第二欄 age

# 推薦：用欄位名列表 + zip 轉為字典，程式碼更易讀
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne 回傳單筆元組或 None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete 回傳受影響列數
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"刪除了 {affected} 條記錄")
```

## 參數化查詢

所有 WHERE 參數使用 `?` 佔位符，參數作為 `Where()` 的後續參數傳入（**不是**元組或列表）：

```python
# 正確 ✓ — 多個參數逐一傳入
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# 正確 ✓ — 多次 Where 呼叫
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# 錯誤 ✗ — 不要傳入元組
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# 這會把整個元組當成第一個佔位符的值

# 錯誤 ✗ — 存在 SQL 注入風險
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Where 參數傳遞規則

```python
# Where(condition: str, *params: Any)
# params 是可變參數，逐一傳入即可

# 單個參數
.Where("name = ?", "Alice")

# 多個參數
.Where("age > ? AND age < ?", 18, 60)

# LIKE 查詢
.Where("name LIKE ?", "A%")

# IN 查詢（需要手動建構佔位符）
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## 自訂儲存後端

2.8.0 起抽象層以**異步方法為原生契約**：繼承 `BaseStorage` 實作異步抽象方法，
同步 `get/set/Execute` 等由基類自動橋接提供：

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    async def aExecute(self):
        # 實作具體執行邏輯
        ...

    async def aExecuteOne(self):
        ...

    async def aCount(self):
        ...

    async def aExists(self):
        ...


class MyStorage(BaseStorage):
    async def aget(self, key, default=None):
        ...

    async def aset(self, key, value):
        ...

    # 實作其他異步抽象方法與事務連接 hook ...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

> [!TIP]
> 若不想實作事務連接路由（`conn` 關鍵字參數），保持類屬性
> `_SUPPORTS_CONN_ROUTING = False`（預設）即可，事務功能仍可用（隔離性受限）。
> 純 SQL 後端可直接繼承 `Core/Bases/sql_base.py` 的 `SQLStorageBase` +
> `SQLQueryBuilder`，只需提供連接管理與方言執行漏斗，詳見
> [儲存後端](storage-backends.md)。

## 相關文件

- [儲存後端](storage-backends.md) - sqlite / mysql / postgres 後端選擇與配置
- [核心模組 API](../api-reference/core-modules.md) - Storage 模組完整 API
- [儲存基類 API](../api-reference/auto_api/ErisPulse/Core/Bases/storage.md) - BaseStorage/BaseQueryBuilder 抽象介面
- [訊息建構器](message-builder.md) - MessageBuilder 鏈式呼叫風格參考