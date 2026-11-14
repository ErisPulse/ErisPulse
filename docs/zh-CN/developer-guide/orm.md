# 数据模型层（ORM）

> [!TIP]
> **什么时候需要读这篇**：需要数据模型、自动建表或关系映射时。不需要则跳过，不影响其它功能的使用。

> [!NOTE]
> **ORM 是异步原生的**：全部 CRUD 方法（`create` / `get` / `save` / `delete` / `create_table` / QuerySet 终结操作）都是 `async def`，直接在事件循环内 `await` 调用即可——底层驱动为 aiosqlite / aiomysql / asyncpg（随存储后端切换），不存在同步阻塞。KV 存储的同步 `get`/`set` 是兼容层，与 ORM 无关。


2.9.0 起框架内置声明式数据模型层：继承 `Model` 并用 `Field` 声明字段，即可获得自动建表与增删改查能力。模型直接构建在内置存储层之上——SQLite / MySQL / PostgreSQL 由 `ErisPulse.storage.backend` 配置决定，**切换后端无需修改模型代码**。

## 声明模型

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON 列，读写自动序列化
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "简介"})
```

- 表名默认取类名 snake_case（`UserProfile → user_profile`），可用 `__tablename__ = "xxx"` 覆写
- `Field` 的约束词表与声明式配置类一致（`choices` / `ge` / `le` / `max_length`，`description` 同样支持 i18n 字典）；校验器引擎与配置校验同源

## 字段参数

| 参数 | 说明 |
|------|------|
| `default` | 默认值（未提供且非自增 → 必填 NOT NULL） |
| `default_factory` | 可变默认值工厂（如 `list`） |
| `primary_key` | 主键（多个即复合主键，收敛为表级 `PRIMARY KEY (a, b)`） |
| `autoincrement` | 自增主键（隐含主键，`create` 后自动回填；单列主键专用，与复合主键互斥） |
| `max_length` | 字符串最大长度（生成 `VARCHAR(n)`，写入校验） |
| `nullable` | 是否允许 NULL（默认 False） |
| `index` | 生成普通索引 |
| `unique` | 唯一约束 |
| `choices` / `ge` / `le` | 枚举 / 数值范围（写入校验） |
| `description` | 描述（i18n 字典，与配置类同格式） |
| `column_type` | 覆写 SQL 列类型定义 |
| `foreign_key` | 列级外键约束（`"表.列"`，生成 `REFERENCES`） |
| `on_delete` | 外键删除动作：`CASCADE` / `SET NULL` / `RESTRICT` / `NO ACTION` / `SET DEFAULT` |
| `auto_now_add` | 插入时自动写入当前时间戳（浮点纪秒） |
| `auto_now` | 插入与实例 `save()` 更新时均自动写入（`QuerySet.update` 批量路径不触发） |

## 复合主键与联合唯一

多个 `primary_key=True` 字段组成复合主键，`get` / `save` / `delete` 按全部主键列定位；
`__unique_together__` 声明联合唯一分组（可多组）：

```python
class Membership(Model):
    __tablename__ = "memberships"
    __unique_together__ = (("user_id", "group_id"),)

    user_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    role: str = Field(default="member")

m = await Membership.get(user_id=1, group_id=2)
```

- `autoincrement` 与复合主键互斥，共存时模型定义即报错
- `__unique_together__` 以唯一索引实现（`uq_` 前缀索引名）：新建表随建表生成，**已存在的表执行 `create_table()` 自动补建**，无需重建
- 复合主键模型暂不支持关系映射（has-many / belongs-to），实例访问时明确报错

## 建表与 CRUD

```python
await User.create_table()                      # 幂等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 插入（自增主键自动回填）
got = await User.get(id=user.id)               # 等值查询首条

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 按主键更新（先约束校验）；主键缺失时退化为插入（自增主键同样回填到实例）
await user.save(update_fields=["age"])         # 部分列更新（白名单，其余列不写入）
await user.delete()                            # 按主键删除

user, created = await User.get_or_create({"age": 20}, name="Alice")      # 查得即返回；无则创建
user, created = await User.update_or_create({"age": 21}, name="Alice")   # 查得更新 defaults 并保存；无则创建

await User.update_all(User.age > 18, role="adult")  # 批量更新
await User.delete_all(User.age > 100)               # 批量删除
```

> [!NOTE]
> `get_or_create` / `update_or_create` 在并发竞争下两个协程可能同时走到创建分支——唯一约束（主键 / `unique` / `__unique_together__`）会让后到者收到 `StorageOperationError`；需要幂等语义时捕获后重查一次。

查询表达式支持 `> >= < <= == !=`、`in_([...])`，以及 `&`（与）/ `|`（或）组合：

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## 事务

ORM 读写与框架存储层共用同一事务路由：处于 `storage.atransaction()` 环境事务内时，`create` / `save` / `delete` 与查询自动复用事务连接，随事务统一提交或回滚，不会独立提交。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # 块内抛异常时，上面的 INSERT 一并回滚
```

## 与声明式配置类的关系

模型声明与 `ConfigClass`（`@dataclass + field(metadata=...)`）**共享同一套底层**——约束词表、校验器引擎（`validate_field_constraints`）、类型类别注册表（`python_type_category`）；但类基座有意分立：配置字段是普通值（TOML 往返、一次加载热更新），模型字段是列描述符（类访问 = 查询表达式、逐行实例）。一份声明语法，两个各司其职的基座。

### 两种声明何时用哪个

| 维度 | 配置类 `field(metadata=...)` | 模型字段 `Field()` |
|------|------------------------------|---------------------|
| 适用场景 | 模块行为参数（少量、人工可读、需热更新） | 业务数据记录（多行、程序读写、需查询） |
| 存储形态 | `config.toml`（注释保留、TOML 往返） | 数据库表（自动建表、SQL 方言） |
| 值形态 | 普通值（`dataclass` 属性直读） | 描述符（类访问 = 列表达式，实例访问 = 行值） |
| 约束声明 | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| 共享底层 | 校验器引擎 + 约束词表 + 类型类别注册表（同一套） | 同左 |

经验法则：**"模块怎么运转"用配置类，"用户产生了什么数据"用模型**。

## 边界与注意事项

- 后端由全局存储配置决定；模型可用 `__storage__` 类属性覆写为自定义 `BaseStorage` 实例（测试注入用）
- `list` / `dict` 字段（含参数化泛型如 `list[int]`、`dict[str, int]`）按容器类别以 JSON 文本列存储，读写自动序列化
- 写入（`create` / `save`）前自动执行约束校验，失败抛 `ValueError`（本地化消息）
- 自动迁移已交付**新增列**场景（见下文）；列类型变更与删列需手工处理
- 触发存储连接失败时的行为与存储层一致：不崩溃框架，冷却后自动重连

## 自动迁移（阶段二）

`create_table()` 在表已存在时自动对比现有列与模型字段：**新增字段**自动执行
`ALTER TABLE ADD COLUMN`（迁移列剔除 `NOT NULL` 约束，存量行回填 NULL），
声明了 `index=True` 的新字段同步建索引。无需手工写迁移脚本。

```python
# v1 上线后模型演进：新增 email / bio 字段
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # 新增：下次 create_table() 自动 ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # 幂等：仅迁移新增列
```

**边界**：仅支持新增列；主键变更、列类型变更、删列需手工处理（避免破坏性
ALTER 误操作）。

## 外键（关系映射基础）

`foreign_key="表.列"` 声明列级外键约束，DDL 生成 `REFERENCES` 子句；`on_delete`
声明删除动作（如 `"CASCADE"` 级联删除引用行）：

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id", on_delete="CASCADE")

    content: str = Field(max_length=255)
```

## 关系映射（relationship）

在模型类体中以类属性声明 `relationship()`，**方向按外键列声明在哪张表自动判定**：

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # 外键在对方表 → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # 外键在本表 → belongs-to
```

**has-many**：实例属性返回查询集，`QuerySet` 全部链式能力可用，
`create` 自动回填本表主键到对方外键列：

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # 该用户的全部文章
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # 追加对方表字段条件
await alice.posts.delete()                               # 只删该用户的

new_post = await alice.posts.create(content="hi")        # author 自动 = alice.id
```

**belongs-to**：直接 `await` 得到对方实例（无匹配或外键为 NULL 返回 `None`）：

```python
post = await Post.get(id=1)
writer = await post.writer          # User 实例或 None
await writer.posts.count()          # 双向互通
```

**要点**：

- `related` 传类名字符串（按模型类名注册表惰性解析，两侧定义顺序无关）或直接传模型类
- 关系查询与对方模型使用各自的存储后端（不支持跨后端 JOIN——关系查询是独立的两条 SQL）
- 关系查询不缓存，每次访问都是即时查询；改用 `User.where(...)` 仍可做任意自定义查询

## 下一步

### 需要换数据库或部署到云数据库

- [存储后端](../advanced/storage-backends.md) — SQLite / MySQL / PostgreSQL 的配置与切换，模型代码零改动

### 不需要表结构、只存几个键值

- [模块核心概念 - 存储系统](modules/core-concepts.md#存储系统) — 键值存储的轻量用法，无需声明模型
