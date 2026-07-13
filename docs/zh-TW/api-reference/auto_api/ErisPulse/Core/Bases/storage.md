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

- **columns** (`列名列表，为空时表示`): SELECT *
**返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Select("name", "age").Execute()
```

---


##### `Insert(data: dict[str, Any])`

插入一行数据

- **data** (`列名到值的映射`): **返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
```

---


##### `InsertMulti(data: list[dict[str, Any]])`

批量插入多行数据

- **data** (`列名到值的映射列表`): **返回值** (`self`): 
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

- **data** (`列名到新值的映射`): **返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()
```

---


##### `Delete()`

删除行

**返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
```

---


##### `Where(condition: str)`

添加 WHERE 条件

多次调用时条件之间以 AND 连接

- **condition** (`条件表达式（使用占位符，如`): "age > ?"）
- **params** (`占位符对应的参数值`): **返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Where("age > ?", 18).Where("name LIKE ?", "A%").Execute()
```

---


##### `OrderBy(column: str, desc: bool = False)`

添加排序规则

多次调用时按添加顺序组合 ORDER BY

- **column** (`排序列名`): - **desc**: 是否降序（默认升序）
**返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").OrderBy("age", desc=True).OrderBy("name").Execute()
```

---


##### `Limit(count: int)`

限制返回条数

- **count** (`最大返回条数`): **返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Limit(10).Execute()
```

---


##### `Offset(count: int)`

设置偏移量

- **count** (`跳过的条数`): **返回值** (`self`): 
**示例**:
```python
>>> storage.Table("users").Limit(10).Offset(20).Execute()
```

---


##### `copy()`

深拷贝当前构建器状态

**返回值**: 新的构建器实例

---


##### `clear()`

重置构建器状态

**返回值**: self

---


##### `Execute()`

执行构建的查询

- SELECT 返回 list[tuple]
- INSERT/UPDATE/DELETE 返回受影响行数 int

**返回值**: 查询结果或受影响行数

---


##### `ExecuteOne()`

执行查询并返回单条结果

**返回值** (`单行元组或`): None

---


##### `Count()`

执行 COUNT 查询

**返回值**: 匹配的行数

---


##### `Exists()`

检查是否存在匹配的记录

**返回值**: 是否存在

---


### `class BaseStorage(ABC)`

存储后端抽象基类

定义键值存储和表管理的统一接口，所有存储后端必须继承并实现此基类。

> **提示**
> 1. 键值操作（get/set/delete）用于简单数据存取
> 2. Table/CreateTable/DropTable 用于结构化数据操作
> 3. transaction 提供事务支持
> 4. 异步方法（aget/aset/...）默认桥接到同步方法，异步后端可覆写


#### 方法列表


##### `get(key: str, default: Any = None)`

获取存储项的值

- **key** (`存储项键名`): - **default**: 默认值
**返回值**: 存储项的值

---


##### `set(key: str, value: Any)`

设置存储项的值

- **key** (`存储项键名`): - **value**: 存储项的值
**返回值**: 操作是否成功

---


##### `delete(key: str)`

删除存储项

- **key** (`存储项键名`): **返回值**: 操作是否成功

---


##### `get_all_keys()`

获取所有存储项的键名

**返回值**: 键名列表

---


##### `clear()`

清空所有存储项

**返回值**: 操作是否成功

---


##### `transaction()`

创建事务上下文

**返回值**: 事务上下文管理器

---


##### `Table(table_name: str)`

获取指定表的查询构建器

- **table_name** (`表名`): **返回值**: 查询构建器实例

---


##### `CreateTable(table_name: str, columns: dict[str, str])`

创建表

- **table_name** (`表名`): - **columns**: 列名到类型的映射（如 {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}）
**返回值**: 操作是否成功

---


##### `DropTable(table_name: str)`

删除表

- **table_name** (`表名`): **返回值**: 操作是否成功

---


##### `HasTable(table_name: str)`

检查表是否存在

- **table_name** (`表名`): **返回值**: 是否存在

---


##### `get_multi(keys: list[str])`

批量获取多个存储项的值

- **keys** (`键名列表`): **返回值**: 键值对字典

---


##### `set_multi(items: dict[str, Any])`

批量设置多个存储项

- **items** (`键值对字典`): **返回值**: 操作是否成功

---


##### `delete_multi(keys: list[str])`

批量删除多个存储项

- **keys** (`键名列表`): **返回值**: 操作是否成功

---


##### `keys()`

获取所有存储项的键名（代理到 get_all_keys）

**返回值**: 键名列表

---


##### `async aget(key: str, default: Any = None)`

异步获取存储项的值

默认实现通过线程池执行同步 ``get()``，避免阻塞事件循环。
异步后端（如 Redis）应覆写此方法为原生异步实现。

- **key** (`存储项键名`): - **default**: 默认值
**返回值**: 存储项的值

---


##### `async aset(key: str, value: Any)`

异步设置存储项的值

- **key** (`存储项键名`): - **value**: 存储项的值
**返回值**: 操作是否成功

---


##### `async adelete(key: str)`

异步删除存储项

- **key** (`存储项键名`): **返回值**: 操作是否成功

---


##### `async aget_all_keys()`

异步获取所有存储项的键名

**返回值**: 键名列表

---


##### `async aclear()`

异步清空所有存储项

**返回值**: 操作是否成功

---


##### `async aget_multi(keys: list[str])`

异步批量获取多个存储项的值

- **keys** (`键名列表`): **返回值**: 键值对字典

---


##### `async aset_multi(items: dict[str, Any])`

异步批量设置多个存储项

- **items** (`键值对字典`): **返回值**: 操作是否成功

---


##### `async adelete_multi(keys: list[str])`

异步批量删除多个存储项

- **keys** (`键名列表`): **返回值**: 操作是否成功

---

