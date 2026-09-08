# SQL 查询构建器

ErisPulse 的 Storage 模块提供链式调用风格的通用 SQL 查询构建器，支持自定义表的创建、查询、更新和删除操作。

## 架构设计

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

- `BaseStorage` / `BaseQueryBuilder` 是抽象基类，定义统一接口，支持未来拓展其他存储介质（Redis、MySQL 等）
- `StorageManager` 是当前 SQLite 具体实现，完全向后兼容

## 导入

```python
from ErisPulse import sdk
# 或
from ErisPulse.Core import storage

# ABC 基类（用于类型标注或自定义实现）
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## 表管理

### 创建表

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### 检查表是否存在

```python
if sdk.storage.HasTable("users"):
    print("users 表已存在")
```

### 删除表

```python
sdk.storage.DropTable("users")
```

### 修改表结构

```python
# 添加列
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# 重命名表
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 链式多个操作
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## 链式查询

### 插入数据

```python
# 单行插入（传入字典）
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 批量插入（传入字典列表）
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### 查询数据

> **重要**：`Select()` 返回的是 `list[tuple]`（元组列表），不是字典。你需要按列顺序用索引访问。

```python
# 查询所有列
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# 查询指定列
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# 按索引取值
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### 将元组转为字典

推荐直接在链上调用 `ToDict()`，SELECT 结果自动以字典返回（列名 → 值）：

```python
# ToDict 链：结果为 list[dict]，列名自动取自查询元数据（SELECT * 同样支持）
rows = sdk.storage.Table("users").Select("name", "age").ToDict().Execute()
# rows: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, ...]

for row in rows:
    print(row["name"], row["age"])

# ExecuteOne 同样生效
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ToDict() \
    .ExecuteOne()
# row: {"name": "Alice", "age": 30} 或 None
```

> `ToDict()` 是链式标记（返回 self）：未调用它的链保持原有 `list[tuple]` 行为，完全向后兼容；`copy()` 会保留该标志。

手动 zip 方式（与 ToDict 等价，适合无法改链的场景）：

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# 方式一：循环中 zip
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# 方式二：一次性转为字典列表
records = [dict(zip(columns, row)) for row in rows]
```

#### 获取单条记录

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row 是 tuple 或 None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### 条件过滤

> `Where(condition, *params)` 支持传入多个参数，对应多个 `?` 占位符。

```python
# 单条件（一个占位符，一个参数）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# 一个 Where 中使用多个占位符
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# 多次调用 Where（AND 连接）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### 排序、分页

```python
# 升序
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# 降序
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# 分页
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### 更新数据

```python
# 条件更新
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# 全量更新
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### 删除数据

```python
# 条件删除
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# 全量删除
sdk.storage.Table("users").Delete().Execute()
```

### 计数与存在性检查

```python
# 计数
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性检查
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## 复用查询条件

使用 `copy()` 深拷贝构建器，复用基础条件：

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# 基于相同条件查询
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# 基于相同条件计数
count = base.copy().Count()

# 基于相同条件检查存在性
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## 重置构建器

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# 重新构建查询
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## 事务中使用

链式操作完全支持事务：

```python
# 提交事务
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# 回滚示例
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Alice 的记录仍然存在
```

## 异步原生 API

2.8.0 起存储层以异步为原生主接口，所有终止方法都有对应的 a 前缀异步版本，
异步 handler 内推荐使用（避免同步兼容层短暂阻塞事件循环）：

```python
# 异步事务
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.aset("key2", {"nested": True})

# 异步链式查询
rows = await sdk.storage.Table("users").Select("name", "age").ToDict().aExecute()
row = await sdk.storage.Table("users").Select("*").Where("id = ?", 1).aExecuteOne()
total = await sdk.storage.Table("users").Where("age > ?", 18).aCount()
exists = await sdk.storage.Table("users").Where("name = ?", "Alice").aExists()

# 异步 KV
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()
```

| 同步（兼容层） | 异步原生 |
|------|------|
| `get` / `set` / `delete` | `aget` / `aset` / `adelete` |
| `get_all_keys` / `clear` | `aget_all_keys` / `aclear` |
| `get_multi` / `set_multi` / `delete_multi` | `aget_multi` / `aset_multi` / `adelete_multi` |
| `transaction()` | `atransaction()` |
| `CreateTable` / `DropTable` / `HasTable` | `aCreateTable` / `aDropTable` / `aHasTable` |
| `Execute` / `ExecuteOne` / `Count` / `Exists` | `aExecute` / `aExecuteOne` / `aCount` / `aExists` |

## 返回值说明

| 操作 | 返回类型 | 说明 |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | 元组列表，按列顺序排列 |
| `Select().ExecuteOne()` | `tuple \| None` | 单条元组或 None |
| `Insert().Execute()` | `int` | 受影响行数 |
| `InsertMulti().Execute()` | `int` | 插入行数 |
| `Update().Execute()` | `int` | 受影响行数 |
| `Delete().Execute()` | `int` | 受影响行数 |
| `Count()` | `int` | 匹配行数 |
| `Exists()` | `bool` | 是否存在 |

### 返回值处理示例

```python
# Select 返回元组，按索引取值
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # 第一行第一列 name
first_age = rows[0][1]   # 第一行第二列 age

# 推荐：用列名列表 + zip 转为字典，代码更可读
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne 返回单条元组或 None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete 返回受影响行数
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"删除了 {affected} 条记录")
```

## 参数化查询

所有 WHERE 参数使用 `?` 占位符，参数作为 `Where()` 的后续参数传入（**不是**元组或列表）：

```python
# 正确 ✓ — 多个参数逐一传入
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# 正确 ✓ — 多次 Where 调用
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# 错误 ✗ — 不要传入元组
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# 这会把整个元组当成第一个占位符的值

# 错误 ✗ — 存在 SQL 注入风险
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Where 参数传递规则

```python
# Where(condition: str, *params: Any)
# params 是可变参数，逐个传入即可

# 单个参数
.Where("name = ?", "Alice")

# 多个参数
.Where("age > ? AND age < ?", 18, 60)

# LIKE 查询
.Where("name LIKE ?", "A%")

# IN 查询（需要手动构造占位符）
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## 自定义存储后端

2.8.0 起抽象层以**异步方法为原生契约**：继承 `BaseStorage` 实现异步抽象方法，
同步 `get/set/Execute` 等由基类自动桥接提供：

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    async def aExecute(self):
        # 实现具体执行逻辑
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

    # 实现其他异步抽象方法与事务连接 hook ...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

> [!TIP]
> 若不想实现事务连接路由（`conn` 关键字参数），保持类属性
> `_SUPPORTS_CONN_ROUTING = False`（默认）即可，事务功能仍可用（隔离性受限）。
> 纯 SQL 后端可直接继承 `Core/Bases/sql_base.py` 的 `SQLStorageBase` +
> `SQLQueryBuilder`，只需提供连接管理与方言执行漏斗，详见
> [存储后端](storage-backends.md)。

## 相关文档

- [存储后端](storage-backends.md) - sqlite / mysql / postgres 后端选择与配置
- [核心模块 API](../api-reference/core-modules.md) - Storage 模块完整 API
- [存储基类 API](../api-reference/auto_api/ErisPulse/Core/Bases/storage.md) - BaseStorage/BaseQueryBuilder 抽象接口
- [消息构建器](message-builder.md) - MessageBuilder 链式调用风格参考
