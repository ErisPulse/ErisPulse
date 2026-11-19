# 資料模型層（ORM）

> [!TIP]
> **什麼時候需要讀這篇**：需要資料模型、自動建表或關聯映射時。不需要則可跳過，不影響其它功能的使用。

> [!NOTE]
> **ORM 是非同步原生的**：全部 CRUD 方法（`create` / `get` / `save` / `delete` / `create_table` / QuerySet 終結操作）皆為 `async def`，直接在事件迴圈內 `await` 呼叫即可——底層驅動為 aiosqlite / aiomysql / asyncpg（隨儲存後端切換），不存在同步阻塞。KV 儲存的同步 `get`/`set` 是相容層，與 ORM 無關。


2.9.0 起框架內建宣告式資料模型層：繼承 `Model` 並用 `Field` 宣告欄位，即可獲得自動建表與增刪改查能力。模型直接構建在內建儲存層之上——SQLite / MySQL / PostgreSQL 由 `ErisPulse.storage.backend` 設定決定，**切換後端無需修改模型程式碼**。

## 宣告模型

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON 欄位，讀寫自動序列化
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "簡介"})
```

- 資料表名稱預設取類別名稱的 snake_case（`UserProfile → user_profile`），可用 `__tablename__ = "xxx"` 覆寫
- `Field` 的約束詞表與宣告式設定類別一致（`choices` / `ge` / `le` / `max_length`，`description` 同樣支援 i18n 字典）；驗證器引擎與設定驗證同源

## 欄位參數

| 參數 | 說明 |
|------|------|
| `default` | 預設值（未提供且非自動遞增 → 必填 NOT NULL） |
| `default_factory` | 可變預設值工廠（如 `list`） |
| `primary_key` | 主鍵（多個即複合主鍵，收斂為資料表層級的 `PRIMARY KEY (a, b)`） |
| `autoincrement` | 自動遞增主鍵（隱含主鍵，`create` 後自動回填；單欄主鍵專用，與複合主鍵互斥） |
| `max_length` | 字串最大長度（生成 `VARCHAR(n)`，寫入時驗證） |
| `nullable` | 是否允許 NULL（預設 False） |
| `index` | 生成一般索引 |
| `unique` | 唯一約束 |
| `choices` / `ge` / `le` | 列舉 / 數值範圍（寫入時驗證） |
| `description` | 描述（i18n 字典，與設定類別同格式） |
| `column_type` | 覆寫 SQL 欄位類型定義 |
| `foreign_key` | 欄級外鍵約束（`"表.列"`，生成 `REFERENCES`） |
| `on_delete` | 外鍵刪除動作：`CASCADE` / `SET NULL` / `RESTRICT` / `NO ACTION` / `SET DEFAULT` |
| `auto_now_add` | 插入時自動寫入目前時間戳（浮點紀秒） |
| `auto_now` | 插入與實例 `save()` 更新時均自動寫入（`QuerySet.update` 批次路徑不觸發） |

## 複合主鍵與聯合唯一

多個 `primary_key=True` 欄位組成複合主鍵，`get` / `save` / `delete` 按全部主鍵欄位定位；
`__unique_together__` 宣告聯合唯一分組（可多組）：

```python
class Membership(Model):
    __tablename__ = "memberships"
    __unique_together__ = (("user_id", "group_id"),)

    user_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    role: str = Field(default="member")

m = await Membership.get(user_id=1, group_id=2)
```

- `autoincrement` 與複合主鍵互斥，共存時模型定義即報錯
- `__unique_together__` 以唯一索引實現（索引名稱帶 `uq_` 前綴）：新建資料表隨建表生成，**已存在的資料表執行 `create_table()` 時自動補建**，無需重建
- 複合主鍵模型暫不支援關聯映射（has-many / belongs-to），實例存取時明確報錯

## 建表與 CRUD

```python
await User.create_table()                      # 冪等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 插入（自動遞增主鍵自動回填）
got = await User.get(id=user.id)               # 等值查詢第一筆

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 按主鍵更新（先約束驗證）；主鍵缺失時退化為插入（自動遞增主鍵同樣回填到實例）
await user.save(update_fields=["age"])         # 部分欄位更新（白名單，其餘欄位不寫入）
await user.delete()                            # 按主鍵刪除

user, created = await User.get_or_create({"age": 20}, name="Alice")      # 查到即回傳；無則建立
user, created = await User.update_or_create({"age": 21}, name="Alice")   # 查到則更新 defaults 並儲存；無則建立

await User.update_all(User.age > 18, role="adult")  # 批次更新
await User.delete_all(User.age > 100)               # 批次刪除
```

> [!NOTE]
> `get_or_create` / `update_or_create` 在並行競爭下兩個協程可能同時走到建立分支——唯一約束（主鍵 / `unique` / `__unique_together__`）會讓後到者收到 `StorageOperationError`；需要冪等語義時，捕捉後重查一次即可。

查詢表達式支援 `> >= < <= == !=`，以及 `&`（且）/ `|`（或）組合；IN 條件使用 `where_in`：

```python
await User.where(User.age > 18).all()
await User.where_in("name", ["Alice", "Bob"]).all()                       # IN 條件（對類型檢查友善）
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all() # IN 與其他條件組合（in_ 為執行時期能力）
```

> [!TIP]
> **對類型檢查友善**：欄位按值類型註解（`age: int = Field(...)`）宣告時，類別存取比較（`User.age > 18`）在 mypy / pyright / ty 看來是 `bool`，執行時期實際產物是條件物件——條件入口（`where` / `count` / `delete_all` / `update_all`）已相容該形態，呼叫點無需任何 `ignore` 註解；真正的布林值入參（無法編譯為 SQL）會在執行時期被明確拒絕。查詢回傳值已靜態類型化：`first()` / `all()` / `get()` / `create()` 的結果即為模型實例，欄位存取有完整類型提示。
>
> 條件物件不可做真值判斷（`if User.age > 18:` 會拋出錯誤），多條件組合請用 `&` / `|` 而非 `and` / `or`。條件建構輔助函式的回傳類型建議標註為 `Condition | bool`。

## 交易

ORM 讀寫與框架儲存層共用同一交易路由：處於 `storage.atransaction()` 環境交易內時，`create` / `save` / `delete` 與查詢自動重複使用交易連線，隨交易統一提交或回滾，不會獨立提交。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # 區塊內拋出例外時，上面的 INSERT 一併回滾
```

## 與宣告式設定類別的關係

模型宣告與 `ConfigClass`（`@dataclass + field(metadata=...)`）**共享同一套底層**——約束詞表、驗證器引擎（`validate_field_constraints`）、類型類別註冊表（`python_type_category`）；但類別基座有意分立：設定欄位是普通值（TOML 往返、一次載入熱更新），模型欄位是欄描述符（類別存取 = 查詢表達式、逐列實例）。一份宣告語法，兩個各司其職的基座。

### 兩種宣告何時用哪個

| 維度 | 設定類別 `field(metadata=...)` | 模型欄位 `Field()` |
|------|------------------------------|---------------------|
| 適用情境 | 模組行為參數（少量、人工可讀、需熱更新） | 業務資料記錄（多列、程式讀寫、需查詢） |
| 儲存形態 | `config.toml`（保留註解、TOML 往返） | 資料庫資料表（自動建表、SQL 方言） |
| 值形態 | 普通值（`dataclass` 屬性直接讀取） | 描述符（類別存取 = 欄表達式，實例存取 = 列值） |
| 約束宣告 | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| 共享底層 | 驗證器引擎 + 約束詞表 + 類型類別註冊表（同一套） | 同左 |

經驗法則：**「模組怎麼運轉」用設定類別，「使用者產生了什麼資料」用模型**。

## 邊界與注意事項

- 後端由全域儲存設定決定；模型可用 `__storage__` 類別屬性覆寫為自訂 SQL 儲存後端實例（`SQLStorageBase`，供測試注入用）
- `list` / `dict` 欄位（含參數化泛型如 `list[int]`、`dict[str, int]`）按容器類別以 JSON 文字欄儲存，讀寫自動序列化
- 寫入（`create` / `save`）前自動執行約束驗證，失敗時拋出 `ValueError`（本地化訊息）
- 自動遷移已交付**新增欄位**情境（見下文）；欄位類型變更與刪除欄位需手動處理
- 觸發儲存連線失敗時的行為與儲存層一致：不使框架崩潰，冷卻後自動重新連線

## 自動遷移（階段二）

`create_table()` 在資料表已存在時自動比對現有欄位與模型欄位：**新增欄位**自動執行
`ALTER TABLE ADD COLUMN`（遷移欄位剔除 `NOT NULL` 約束，既有資料列回填 NULL），
宣告了 `index=True` 的新欄位同步建立索引。無需手動撰寫遷移腳本。

```python
# v1 上線後模型演進：新增 email / bio 欄位
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # 新增：下次 create_table() 自動 ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # 冪等：僅遷移新增欄位
```

**邊界**：僅支援新增欄位；主鍵變更、欄位類型變更、刪除欄位需手動處理（避免破壞性
ALTER 誤操作）。

## 外鍵（關聯映射基礎）

`foreign_key="表.列"` 宣告欄級外鍵約束，DDL 生成 `REFERENCES` 子句；`on_delete`
宣告刪除動作（如 `"CASCADE"` 級聯刪除引用資料列）：

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id", on_delete="CASCADE")

    content: str = Field(max_length=255)
```

## 關聯映射（relationship）

在模型類別主體中以類別屬性宣告 `relationship()`，**方向依外鍵欄位宣告在哪張資料表自動判定**：

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # 外鍵在對方資料表 → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # 外鍵在本表 → belongs-to
```

**has-many**：實例屬性回傳查詢集，`QuerySet` 全部鏈式能力皆可用，
`create` 自動將本表主鍵回填到對方的外鍵欄位：

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # 該使用者的全部文章
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # 追加對方資料表欄位條件
await alice.posts.delete()                               # 只刪除該使用者的

new_post = await alice.posts.create(content="hi")        # author 自動 = alice.id
```

**belongs-to**：直接 `await` 即可取得對方實例（無匹配或外鍵為 NULL 時回傳 `None`）：

```python
post = await Post.get(id=1)
writer = await post.writer          # User 實例或 None
await writer.posts.count()          # 雙向互通
```

**要點**：

- `related` 傳入類別名稱字串（按模型類別名稱註冊表惰性解析，兩側定義順序無關）或直接傳入模型類別
- 關聯查詢與對方模型使用各自的儲存後端（不支援跨後端 JOIN——關聯查詢是獨立的兩條 SQL）
- 關聯查詢不快取，每次存取都是即時查詢；改用 `User.where(...)` 仍可進行任意自訂查詢

## 下一步

### 需要更換資料庫或部署到雲端資料庫

- [儲存後端](../advanced/storage-backends.md) — SQLite / MySQL / PostgreSQL 的設定與切換，模型程式碼零修改

### 不需要資料表結構、只儲存幾個鍵值

- [模組核心概念 - 儲存系統](modules/core-concepts.md#儲存系統) — 鍵值儲存的輕量用法，無需宣告模型