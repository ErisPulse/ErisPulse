# 存儲後端

> [!TIP]
> **什麼時候需要閱讀這篇**：當切換 sqlite / mysql / postgres 或自定義存儲後端時。不需要則跳過，不會影響其他功能的使用。

ErisPulse 內建三種異步原生存儲後端，透過配置即可一鍵切換，**API 完全一致、切換零程式碼變動**：

| 後端 | 驅動 | 安裝 | 特點 |
|------|------|------|------|
| SQLite（預設） | aiosqlite | 開箱即用 | 零設定、單檔案、WAL 併發 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 適合已有 MySQL 基礎設施、多實例共享 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | 事務能力強、JSONB 生態、高併發 |

{!--< tips >!--}
1. 異步是原生主介面（`aget/aset/atransaction/aExecute`），同步 API 為相容層
2. 框架自身的配置持久化、會話收件箱、對話檢查點等全部走同一存儲後端——切換後端即整體遷移
3. `[mysql]` extra 已包含 `cryptography`——MySQL 8 預設的 `caching_sha2_password` 認證必需，缺失時連接池初始化會失敗
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

## 連接失敗行為

框架啟動與運行**不依賴資料庫可達**——MySQL / PostgreSQL 連接失敗不會導致框架崩潰或無法啟動：

1. 建池瞬時失敗自動指數退避重試（預設 3 次）
2. 重試耗盡 → 記錄 WARNING（含原因與冷卻時長），框架照常啟動 / 繼續運行，僅儲存操作暫不可用
3. 冷卻期（預設 30 秒）內後續儲存操作**快速失敗**（不阻塞、不拖慢其餘功能）
4. 冷卻結束自動重連嘗試——資料庫恢復後儲存隨之恢復，無需重啟

日誌範例：`mysql 連接池建立最終失敗（已重試 3 次），30 秒後自動重連；期間儲存操作將快速失敗，框架其餘功能不受影響`

## 失敗語義（2.12 起）

| 場景 | 行為 |
|------|------|
| 操作執行失敗（寫鎖逾時 / SQL 錯誤 / 約束衝突） | **拋出 `StorageOperationError`**（寫入路徑：aset / adelete / aclear / set_multi 及同步橋同路徑）——不再靜默 `False`，重要寫入失敗必須可見 |
| 連線層級不可達（冷卻期快速失敗） | 回傳 `False` / `None`（規則 26 框架韌性語義，另有 `storage.unreachable` / `storage.recovered` 事件） |
| 交易開啟逾時（>30s） | 拋出 `StorageOperationError`（`STORAGE_TXN_BEGIN_TIMEOUT_SECS`） |

重要寫入請用 try/except 包裹並做補償；交易區塊內只放純 DB 操作。

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
該事件循環，**首次調用會輸出一次性告警**（"建議改用 a 前綴異步方法"），
推薦優先使用 a 前綴異步方法。兩條邊界必須知曉：

- **橋接線程內禁止再調同步介面**：同步介面在橋接線程內執行，此時再調
  同步介面會拋 `RuntimeError`（防重入保護，避免自死鎖）
- **橋接目標循環關閉後調用會失敗**：`uninit()` 之後不要再調用儲存介面

完整方法對照見 [SQL 查詢建構器](sql-builder.md)。

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

## SQLite "database is locked" 排查

框架 SQLite 後端已內建：**WAL 日誌模式**（讀寫不互斥）+ **busy_timeout 5000ms**（寫鎖競爭自動等待）+ autocommit 連線 + 多事件迴圈各持共享連線 + **交易 `BEGIN IMMEDIATE`**（2.12 起——交易開始即取寫鎖，消除 deferred 交易「先讀後寫」升級時的 `SQLITE_BUSY_SNAPSHOT`，該 busy 不重試、`busy_timeout` 無法緩解，是高頻讀寫混合下間歇性 locked 的框架內根因）。

2.12+ 純框架使用（儲存 / ORM / 混合雙路徑交錯寫）不應再出現 locked；仍遇到時按以下順序排查：

| 場景 | 判定 | 處置 |
|------|------|------|
| 交易內慢操作 | `atransaction` 區塊內有慢活（外部 HTTP、大計算），持鎖超過 busy_timeout | 交易區塊內只做庫操作，慢操作移出 |
| 混用第二套 ORM | 同一行程內 sqlmodel / SQLAlchemy / 裸 sqlite3 自開連線寫同一個資料庫檔案 | **同一資料庫檔案只用一套 ORM**（內建本就是非同步原生），不要混用過渡 |
| 多行程同檔案 | 多實例 / Dashboard / 資料庫工具開啟同一 sqlite | 各實例獨立 `config/` 目錄；管理工具以唯讀模式開啟；高頻寫場景切換 mysql / postgres（設定一改零程式碼遷移） |
| 舊版本框架 | `<2.12` 的 deferred 交易升級問題 | 升級框架 |

> `busy_timeout` 目前為類別常數 `_SQLITE_BUSY_TIMEOUT_MS = 5000`（`Core/storage/sqlite.py`）；如需調整屬於原始碼層級修改，不作為執行期設定公開。

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