# `ErisPulse.Core.Bases.storage` 模块

---

## 模块概述


ErisPulse 存储基类

提供存储后端和查询构建器的抽象接口，支持不同存储介质的统一访问

> **提示**
> 1. BaseStorage 定义了键值存储和表管理的标准接口
> 2. BaseQueryBuilder 定义了链式查询构建的标准接口
> 3. 具体存储后端（如 SQLite、Redis、MySQL）需继承并实现这些接口

---

## 类列表


### `class BaseQueryBuilder(ABC)`

查询构建器抽象基类

定义链式调用风格的查询构建接口，所有链式方法返回 self，
终止方法（Execute、ExecuteOne、Count、Exists）返回实际结果。

> **提示**
> 使用方式：
> 1. storage.Table("users").Insert({"name": "Alice"}).Execute()
> 2. storage.Table("users").Select("name").Where("age > ?", 18).Limit(10).Execute()


#### 方法列表


##### `Select()`

指定查询列

:param columns: 列名列表，为空时表示 SELECT *
:return: self

**示例**:
```python
>>> storage.Table("users").Select("name", "age").Execute()
```

---


##### `Insert(data: dict[str, Any])`

插入一行数据

:param data: 列名到值的映射
:return: self

**示例**:
```python
>>> storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
```

---


##### `InsertMulti(data: list[dict[str, Any]])`

批量插入多行数据

:param data: 列名到值的映射列表
:return: self

**示例**:
```python
>>> storage.Table("users").InsertMulti([
...     {"name": "Alice", "age": 30},
...     {"name": "Bob", "age": 25}
... ]).Execute()
```

---


##### `Update(data: dict[str, Any])`

更新数据

:param data: 列名到新值的映射
:return: self

**示例**:
```python
>>> storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()
```

---


##### `Delete()`

删除行

:return: self

**示例**:
```python
>>> storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
```

---


##### `Where(condition: str)`

添加 WHERE 条件

多次调用时条件之间以 AND 连接

:param condition: 条件表达式（使用占位符，如 "age > ?"）
:param params: 占位符对应的参数值
:return: self

**示例**:
```python
>>> storage.Table("users").Where("age > ?", 18).Where("name LIKE ?", "A%").Execute()
```

---


##### `OrderBy(column: str, desc: bool = False)`

添加排序规则

多次调用时按添加顺序组合 ORDER BY

:param column: 排序列名
:param desc: 是否降序（默认升序）
:return: self

**示例**:
```python
>>> storage.Table("users").OrderBy("age", desc=True).OrderBy("name").Execute()
```

---


##### `Limit(count: int)`

限制返回条数

:param count: 最大返回条数
:return: self

**示例**:
```python
>>> storage.Table("users").Limit(10).Execute()
```

---


##### `Offset(count: int)`

设置偏移量

:param count: 跳过的条数
:return: self

**示例**:
```python
>>> storage.Table("users").Limit(10).Offset(20).Execute()
```

---


##### `copy()`

深拷贝当前构建器状态

:return: 新的构建器实例

---


##### `clear()`

重置构建器状态

:return: self

---


##### `Execute()`

执行构建的查询

- SELECT 返回 list[tuple]
- INSERT/UPDATE/DELETE 返回受影响行数 int

:return: 查询结果或受影响行数

---


##### `ExecuteOne()`

执行查询并返回单条结果

:return: 单行元组或 None

---


##### `Count()`

执行 COUNT 查询

:return: 匹配的行数

---


##### `Exists()`

检查是否存在匹配的记录

:return: 是否存在

---


### `class BaseStorage(ABC)`

存储后端抽象基类

定义键值存储和表管理的统一接口，所有存储后端必须继承并实现此基类。

> **提示**
> 1. 键值操作（get/set/delete）用于简单数据存取
> 2. Table/CreateTable/DropTable 用于结构化数据操作
> 3. transaction 提供事务支持


#### 方法列表


##### `get(key: str, default: Any = None)`

获取存储项的值

:param key: 存储项键名
:param default: 默认值
:return: 存储项的值

---


##### `set(key: str, value: Any)`

设置存储项的值

:param key: 存储项键名
:param value: 存储项的值
:return: 操作是否成功

---


##### `delete(key: str)`

删除存储项

:param key: 存储项键名
:return: 操作是否成功

---


##### `get_all_keys()`

获取所有存储项的键名

:return: 键名列表

---


##### `clear()`

清空所有存储项

:return: 操作是否成功

---


##### `transaction()`

创建事务上下文

:return: 事务上下文管理器

---


##### `Table(table_name: str)`

获取指定表的查询构建器

:param table_name: 表名
:return: 查询构建器实例

---


##### `CreateTable(table_name: str, columns: dict[str, str])`

创建表

:param table_name: 表名
:param columns: 列名到类型的映射（如 {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}）
:return: 操作是否成功

---


##### `DropTable(table_name: str)`

删除表

:param table_name: 表名
:return: 操作是否成功

---


##### `HasTable(table_name: str)`

检查表是否存在

:param table_name: 表名
:return: 是否存在

---


##### `get_multi(keys: list[str])`

批量获取多个存储项的值

:param keys: 键名列表
:return: 键值对字典

---


##### `set_multi(items: dict[str, Any])`

批量设置多个存储项

:param items: 键值对字典
:return: 操作是否成功

---


##### `delete_multi(keys: list[str])`

批量删除多个存储项

:param keys: 键名列表
:return: 操作是否成功

---


##### `keys()`

获取所有存储项的键名（代理到 get_all_keys）

:return: 键名列表

---

