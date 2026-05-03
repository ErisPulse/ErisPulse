# `ErisPulse.Core.storage` 模块

---

## 模块概述


ErisPulse 存储管理模块

提供键值存储、通用 SQL 链式查询和事务支持，用于管理框架运行时数据。
基于 SQLite 实现持久化存储，支持复杂数据类型和原子操作。

> **提示**
> 1. 支持JSON序列化存储复杂数据类型
> 2. 提供事务支持确保数据一致性
> 3. 提供链式调用风格的通用 SQL 查询构建器

---

## 类列表


### `class SQLiteQueryBuilder(BaseQueryBuilder)`

SQLite 查询构建器

链式调用风格的 SQL 查询构建器，配合 StorageManager 使用。

> **提示**
> 使用方式：
> 1. storage.Table("users").Insert({"name": "Alice"}).Execute()
> 2. storage.Table("users").Select("name").Where("age > ?", 18).OrderBy("name").Limit(10).Execute()
> 3. 通过 copy() 复用基础查询条件


#### 方法列表


##### `Execute()`

执行构建的查询

- SELECT 返回 list[tuple]
- INSERT/INSERT_MULTI 返回受影响行数 int
- UPDATE/DELETE 返回受影响行数 int

:return: 查询结果列表或受影响行数

**示例**:
```python
>>> rows = storage.Table("users").Select("name", "age").Execute()
>>> affected = storage.Table("users").Delete().Where("age < ?", 18).Execute()
```

---


##### `ExecuteOne()`

执行查询并返回单条结果

:return: 单行元组或 None

**示例**:
```python
>>> row = storage.Table("users").Select("*").Where("id = ?", 1).ExecuteOne()
```

---


##### `Count()`

执行 COUNT 查询

:return: 匹配的行数

**示例**:
```python
>>> total = storage.Table("users").Where("age > ?", 18).Count()
```

---


##### `Exists()`

检查是否存在匹配的记录

:return: 是否存在

**示例**:
```python
>>> if storage.Table("users").Where("name = ?", "Alice").Exists():
>>>     print("Alice exists")
```

---


### `class AlterTableBuilder`

ALTER TABLE 构建器

链式调用风格的表结构修改构建器。

> **提示**
> 使用方式：
> 1. storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
> 2. storage.AlterTable("users").RenameTo("members").Execute()


#### 方法列表


##### `AddColumn(column_name: str, column_type: str)`

添加列

:param column_name: 列名
:param column_type: 列类型（如 "TEXT", "INTEGER DEFAULT 0"）
:return: self

**示例**:
```python
>>> storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
```

---


##### `RenameTo(new_name: str)`

重命名表

:param new_name: 新表名
:return: self

**示例**:
```python
>>> storage.AlterTable("users").RenameTo("members").Execute()
```

---


##### `Execute()`

执行所有已收集的 ALTER TABLE 操作

:return: 操作是否成功

---


### `class StorageManager(BaseStorage)`

存储管理器（SQLite 实现）

单例模式实现，提供键值存储的增删改查、通用 SQL 链式查询和事务管理。

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 data/config.db

> **提示**
> 1. 使用 get/set 方法操作键值存储项
> 2. 使用 Table() 链式调用操作自定义表
> 3. 使用 transaction 上下文管理事务


#### 嵌套类


##### `class _Transaction`

事务上下文管理器

> **内部方法** 
确保多个操作的原子性


###### 方法列表


####### `__enter__()`

进入事务上下文

:return: 事务对象

---


####### `__exit__(exc_type: type[Exception], exc_val: Exception, exc_tb: Any)`

退出事务上下文

:param exc_type: 异常类型
:param exc_val: 异常对象
:param exc_tb: 异常堆栈

:return: None

---


#### 方法列表


##### `_is_ready()`

> **内部方法** 
检查存储管理器是否已初始化完成

:return: bool 反馈是否已初始化完成

---


##### `_auto_commit(conn)`

> **内部方法** 
非事务模式下自动提交更改

:param conn: 数据库连接

---


##### `_get_connection()`

> **内部方法** 
获取数据库连接（支持事务）

如果在事务中，返回事务的连接
否则创建新连接

:return: sqlite3.Connection 数据库连接

---


##### `_ensure_directories()`

> **内部方法** 
确保必要的目录存在

---


##### `_init_db()`

> **内部方法** 
初始化数据库

创建默认 config 键值表

---


##### `get(key: str, default: Any = None)`

获取存储项的值

:param key: 存储项键名
:param default: 默认值(当键不存在时返回)
:return: 存储项的值

**示例**:
```python
>>> timeout = storage.get("network.timeout", 30)
>>> user_settings = storage.get("user.settings", {})
```

---


##### `get_all_keys()`

获取所有存储项的键名

:return: 键名列表

**示例**:
```python
>>> all_keys = storage.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个存储项")
```

---


##### `keys()`

标准字典接口方法，返回所有存储项的键名 -> 代理 --> get_all_keys

:return: 键名列表

**示例**:
```python
>>> all_keys = storage.keys()
>>> print(f"共有 {len(all_keys)} 个存储项")
```

---


##### `set(key: str, value: Any)`

设置存储项的值

:param key: 存储项键名
:param value: 存储项的值
:return: 操作是否成功

**示例**:
```python
>>> storage.set("app.name", "MyApp")
>>> storage.set("user.settings", {"theme": "dark"})
```

---


##### `set_multi(items: dict[str, Any])`

批量设置多个存储项

:param items: 键值对字典
:return: 操作是否成功

**示例**:
```python
>>> storage.set_multi({
...     "app.name": "MyApp",
...     "app.version": "1.0.0",
...     "app.debug": True
... })
```

---


##### `getConfig(key: str, default: Any = None)`

获取模块/适配器配置项（委托给config模块）

:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

> **已弃用** 请使用 `config.getConfig` 来获取配置项，这个API已弃用

---


##### `setConfig(key: str, value: Any)`

设置模块/适配器配置（委托给config模块）

:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功

> **已弃用** 请使用 `config.setConfig` 来设置配置项，这个API已弃用

---


##### `delete(key: str)`

删除存储项

:param key: 存储项键名
:return: 操作是否成功

**示例**:
```python
>>> storage.delete("temp.session")
```

---


##### `delete_multi(keys: list[str])`

批量删除多个存储项

:param keys: 键名列表
:return: 操作是否成功

**示例**:
```python
>>> storage.delete_multi(["temp.key1", "temp.key2"])
```

---


##### `get_multi(keys: list[str])`

批量获取多个存储项的值

:param keys: 键名列表
:return: 键值对字典

**示例**:
```python
>>> settings = storage.get_multi(["app.name", "app.version"])
```

---


##### `transaction()`

创建事务上下文

:return: 事务上下文管理器

**示例**:
```python
>>> with storage.transaction():
...     storage.set("key1", "value1")
...     storage.set("key2", "value2")
```

---


##### `clear()`

清空所有存储项

:return: 操作是否成功

**示例**:
```python
>>> storage.clear()
```

---


##### `Table(table_name: str)`

获取指定表的查询构建器

:param table_name: 表名
:return: SQLiteQueryBuilder 实例

**示例**:
```python
>>> rows = storage.Table("users").Select("name", "age").Where("age > ?", 18).Execute()
>>> storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
```

---


##### `CreateTable(table_name: str, columns: dict[str, str])`

创建表

:param table_name: 表名
:param columns: 列定义字典（列名 → SQL 类型定义）
:return: 操作是否成功

**示例**:
```python
>>> storage.CreateTable("users", {
...     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
...     "name": "TEXT NOT NULL",
...     "age": "INTEGER DEFAULT 0"
... })
```

---


##### `DropTable(table_name: str)`

删除表

:param table_name: 表名
:return: 操作是否成功

**示例**:
```python
>>> storage.DropTable("users")
```

---


##### `HasTable(table_name: str)`

检查表是否存在

:param table_name: 表名
:return: 是否存在

**示例**:
```python
>>> if storage.HasTable("users"):
...     print("users 表已存在")
```

---


##### `AlterTable(table_name: str)`

获取 ALTER TABLE 构建器

:param table_name: 表名
:return: AlterTableBuilder 实例

**示例**:
```python
>>> storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
>>> storage.AlterTable("users").RenameTo("members").Execute()
```

---


##### `__getattr__(key: str)`

通过属性访问存储项

:param key: 存储项键名
:return: 存储项的值

**异常**: `AttributeError` - 当存储项不存在时抛出

**示例**:
```python
>>> app_name = storage.app_name
```

---


##### `__setattr__(key: str, value: Any)`

通过属性设置存储项

:param key: 存储项键名
:param value: 存储项的值

**示例**:
```python
>>> storage.app_name = "MyApp"
```

---

