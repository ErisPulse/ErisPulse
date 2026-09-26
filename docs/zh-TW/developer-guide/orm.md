# 數據模型層（ORM）

自 2.9.0 版本起，框架內建了宣告式數據模型層：繼承 `Model` 並使用 `Field` 聲明欄位，即可獲得自動建表與增刪改查能力。模型直接建構在內建儲存層之上——SQLite / MySQL / PostgreSQL 由 `ErisPulse.storage.backend` 配置決定，**切換後端無需修改模型程式碼**。

## 聲明模型

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON 列，讀寫自動序列化
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "簡介"})
```

- 表名預設取類名 snake_case（`UserProfile → user_profile`），可用 `__tablename__ = "xxx"` 覆蓋
- `Field` 的約束詞表與宣告式配置類一致（`choices` / `ge` / `le` / `max_length`，`description` 同樣支援 i18n 字典）；校驗引擎與配置校驗同源

## 字段參數

| 參數 | 說明 |
|------|------|
| `default` | 預設值（未提供且非自增 → 必填 NOT NULL） |
| `default_factory` | 可變預設值工廠（如 `list`） |
| `primary_key` | 主鍵 |
| `autoincrement` | 自增主鍵（隱含主鍵，`create` 後自動回填） |
| `max_length` | 字串最大長度（生成 `VARCHAR(n)`，寫入驗證） |
| `nullable` | 是否允許 NULL（預設 False） |
| `index` | 生成普通索引 |
| `unique` | 唯一約束 |
| `choices` / `ge` / `le` | 列舉 / 數值範圍（寫入驗證） |
| `description` | 描述（i18n 字典，與配置類同格式） |
| `column_type` | 覆寫 SQL 列類型定義 |

## 建表與 CRUD

```python
await User.create_table()                      # 幂等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 插入（自增主鍵自動回填）
got = await User.get(id=user.id)               # 等值查詢首條

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 按主鍵更新（先約束校驗）；主鍵缺失時退化為插入（自增主鍵同樣回填到實例）
await user.delete()                            # 按主鍵刪除

await User.update_all(User.age > 18, role="adult")  # 批量更新
await User.delete_all(User.age > 100)               # 批量刪除
```

查詢表達式支援 `> >= < <= == !=`、`in_([...])`，以及 `&`（與）/ `|`（或）組合：

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## 事務

ORM 的讀寫與框架儲存層共用同一個事務路由：當處於 `storage.atransaction()` 環境的事務內時，`create` / `save` / `delete` 與查詢會自動複用事務連接，並隨事務統一提交或回滾，不會獨立提交。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # 塊內拋異常時，上面的 INSERT 一併回滾
```

## 與宣告式配置類的關係

模型宣告與 `ConfigClass`（`@dataclass + field(metadata=...)`）**共享同一套底層**——約束詞表、校驗器引擎（`validate_field_constraints`）、類型類別註冊表（`python_type_category`）；但類基座有意分離：配置欄位是普通值（TOML 往返、一次載入熱更新），模型欄位是欄位描述符（類存取 = 查詢表達式、逐行實例）。一份宣告語法，兩個各司其職的基座。

### 兩種宣告何時用哪個

| 維度 | 配置類 `field(metadata=...)` | 模型欄位 `Field()` |
|------|------------------------------|---------------------|
| 適用場景 | 模組行為參數（少量、人工可讀、需熱更新） | 業務資料記錄（多行、程式讀寫、需查詢） |
| 存儲形態 | `config.toml`（註解保留、TOML 往返） | 資料庫表（自動建表、SQL 方言） |
| 值形態 | 普通值（`dataclass` 屬性直讀） | 描述符（類存取 = 欄位表達式，實例存取 = 行值） |
| 約束宣告 | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| 共享底層 | 校驗器引擎 + 約束詞表 + 類型類別註冊表（同一套） | 同左 |

經驗法則：**「模組如何運作」用配置類，「使用者產生了什麼資料」用模型**。

## 邊界與注意事項

- 後端由全域儲存配置決定；模型可用 `__storage__` 類屬性覆寫為自訂 `BaseStorage` 實例（用於測試注入）
- `list` / `dict` 欄位（含參數化泛型如 `list[int]`、`dict[str, int]`）按容器類別以 JSON 文本列儲存，讀寫自動序列化
- 寫入（`create` / `save`）前自動執行約束校驗，失敗拋 `ValueError`（本地化訊息）
- 自動遷移已交付**新增欄位**場景（見下文）；欄位類型變更與刪欄需手動處理
- 觸發儲存連線失敗時的行為與儲存層一致：不崩潰框架，冷卻後自動重連

## 自動遷移（階段二）

`create_table()` 在表已存在時自動對比現有列與模型欄位：**新增欄位**自動執行
`ALTER TABLE ADD COLUMN`（遷移欄位剔除 `NOT NULL` 約束，存量行回填 NULL），
宣告了 `index=True` 的新欄位同步建立索引。無需手動編寫遷移腳本。

```python
# v1 上線後模型演進：新增 email / bio 欄位
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # 新增：下次 create_table() 自動 ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # 幂等：僅遷移新增欄位
```

**邊界**：僅支援新增欄位；主鍵變更、欄位類型變更、刪欄需手動處理（避免破壞性
ALTER 誤操作）。

## 外鍵（關係映射基礎）

`foreign_key="表.列"` 聲明欄位級外鍵約束，DDL 會生成 `REFERENCES` 子句：

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")

    content: str = Field(max_length=255)
```

## 關係映射（relationship）

在模型類體中以類屬性宣告 `relationship()`，**方向依外鍵欄位宣告在哪張表自動判定**：

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # 外鍵在對方表 → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # 外鍵在本表 → belongs-to
```

**has-many**：實例屬性返回查詢集，`QuerySet` 全部鏈式能力可用，  
`create` 自動回填本表主鍵到對方外鍵欄位：

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # 該用戶的全部文章
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # 追加對方表欄位條件
await alice.posts.delete()                               # 只刪該用戶的

new_post = await alice.posts.create(content="hi")        # author 自動 = alice.id
```

**belongs-to**：直接 `await` 得到對方實例（無匹配或外鍵為 NULL 返回 `None`）：

```python
post = await Post.get(id=1)
writer = await post.writer          # User 實例或 None
await writer.posts.count()          # 雙向互通
```

**要點**：

- `related` 傳入類名字串（按模型類名註冊表惰性解析，兩側定義順序無關）或直接傳模型類
- 關係查詢與對方模型使用各自的儲存後端（不支援跨後端 JOIN——關係查詢是獨立的兩條 SQL）
- 關係查詢不快取，每次存取都是即時查詢；改用 `User.where(...)` 仍可做任意自訂查詢