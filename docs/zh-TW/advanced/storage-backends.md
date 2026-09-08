# 存儲後端

ErisPulse 內建三種異步原生存儲後端，透過配置一鍵切換，**API 完全一致、切換零程式碼修改**：

| 後端 | 驅動 | 安裝 | 特點 |
|------|------|------|------|
| SQLite（預設） | aiosqlite | 開箱即用 | 零設定、單檔案、WAL 併發 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 適合已有 MySQL 基礎設施、多實例共享 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | 事務能力強、JSONB 生態、高併發 |

{!--< tips >!--}
1. 異步是原生主介面（`aget/aset/atransaction/aExecute`），同步 API 為相容層
2. 框架自身的設定持久化、會話收件箱、對話檢查點等全部走同一存儲後端——切換後端即整體遷移
{!--< /tips >!--}

## 後端選擇

在 `config/config.toml` 中配置：

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（預設）/ "mysql" / "postgres"
use_global_db = false     # 僅 SQLite：使用套件內的全域資料庫 data/config.db
```

也支援環境變數覆蓋（Docker / 12-factor）：

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

環境變數命名規則：配置路徑大寫、點號換下劃線  
（`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`）。

## 連接參數

### MySQL（`ErisPulse.storage.mysql`）

```toml
[ErisPulse.storage.mysql]
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
charset = "utf8mb4"
pool_min = 1
pool_max = 10
```

### PostgreSQL（`ErisPulse.storage.postgres`）

```toml
[ErisPulse.storage.postgres]
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
pool_min = 1
pool_max = 10
```

> [!NOTE]
> 連接參數變更後需重啟框架生效（配置熱更新時會輸出重啟提醒日誌）。
> 連接池按事件循環惰性建立，建立瞬時失敗（網路抖動 / 資料庫重啟窗口）會自動指數退避重試。

## 異步原生 API

```python
# KV 操作
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()

# 表操作
await sdk.storage.aCreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})
rows = await sdk.storage.Table("users").Select("name").ToDict().aExecute()

# 異步事務
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

同步 API（`get/set/transaction/Table(...).Execute()`）繼續可用，內部經
`AsyncBridge` 後台事件循環橋接執行——在異步 handler 中調用會短暫阻塞
該事件循環，推薦優先使用 a 前綴異步方法。完整方法對照見
[SQL 查詢建構器](sql-builder.md)。

## 方言行為差異

方言差異全部收斂在框架內部，呼叫程式碼無需感知：

| 差異點 | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| 占位符 | `?` | `%s`（自動翻譯） | `$1..$n`（自動翻譯） |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV 值欄位類型 | `TEXT` | `LONGTEXT` | `TEXT` |
| 自增主鍵 | 原生支援 | `AUTO_INCREMENT`（自動翻譯） | `SERIAL`（自動翻譯） |

建表欄位類型統一使用 SQLite 風格定義（如 `"INTEGER PRIMARY KEY AUTOINCREMENT"`、
`"TEXT NOT NULL"`、`"DOUBLE DEFAULT 0.0"`），由方言自動翻譯為目標後端等價寫法。

## 自訂 SQL 後端

純 SQL 後端可繼承共享基類，只需提供連接管理與方言執行漏斗：

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # 覆寫：占位符翻譯 / 標識符引用 / UPSERT / 類型映射 ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # 連接池
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # 執行漏斗
```

非 SQL 後端（如 Redis）繼承 `BaseStorage` 實現 KV 異步介面後，
可直接使用 `KVQueryBuilder` 獲得鏈式表查詢能力（記憶體過濾，適合中小數據量）。

## 相關文件

- [SQL 查詢建構器](sql-builder.md) - 鏈式查詢語法與非同步 API 對照
- [核心模組 API](../api-reference/core-modules.md) - Storage 模組完整 API
- [儲存基類 API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect 抽象介面