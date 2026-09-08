# `ErisPulse.Core.Bases.storage` 模块

---

## 模块概述


ErisPulse 存储基类

提供存储后端和查询构建器的抽象接口，支持不同存储介质的统一访问。

> **提示**
> 1. 异步接口（aget/aset/.../aExecute/...）是原生主接口，所有内置后端基于异步驱动实现
> 2. 同步接口（get/set/.../Execute/...）为兼容层，内部通过 AsyncBridge 桥接到后台事件循环执行
> 3. 具体存储后端（SQLite/MySQL/PostgreSQL/Redis 等）需继承 BaseStorage 并实现异步抽象方法
> 4. 事务：异步代码使用 ``async with storage.atransaction():``，同步代码使用 ``with storage.transaction():``

---

## 函数列表


### `_has_running_loop()`

> **内部方法**
判断当前线程是否有正在运行的事件循环

**返回值**: 是否存在运行中的事件循环

---


## 类列表


### `class AsyncBridge`

同步兼容层的后台事件循环桥接器

以守护线程运行一个常驻事件循环，同步兼容方法通过
:meth:`run` 将协程提交到该循环并阻塞等待结果。
进程级单例，解释器退出时自动停止。

> **提示**
> 1. 所有后端的同步 API 共享同一个桥接循环
> 2. 在桥接线程内禁止再调用同步兼容接口（会自我阻塞）
> 3. 在异步上下文（已有运行中事件循环的线程）调用同步 API 仍可工作，
> 但会短暂阻塞该事件循环，建议改用 a 前缀异步方法


#### 方法列表


##### `_run_loop()`

> **内部方法** 桥接线程入口：启动常驻事件循环

---


##### `run(coro: Any, timeout: float | None = None)`

在桥接事件循环上执行协程并阻塞等待结果

- **coro** (`要执行的协程对象（所有权移交本方法）`): - **timeout**: 可选超时秒数（默认无限等待）
**返回值** (`协程的返回值`): **异常**: `RuntimeError` - 桥接已关闭或在桥接线程内重入调用时

---


##### `close()`

停止桥接事件循环（解释器退出时自动调用）

幂等：循环未启动或已停止时为无操作。

---


### `class _AsyncTransaction`

> **内部方法**
异步事务句柄

由 :meth:`BaseStorage.atransaction` 与同步兼容事务共同驱动，
连接的获取/提交/回滚/释放委托给后端的对应 hook。


#### 方法列表


##### `async start()`

获取专用连接并开启事务

---


##### `async finish(exc: BaseException | None)`

结束事务：无异常时提交，有异常时回滚，最后释放连接

- **exc** (`触发回滚的异常（None`): 表示正常提交）

---


### `class _EmptyTransaction`

> **内部方法** 空事务上下文（存储未就绪时使用）


### `class _NestedTransaction`

> **内部方法** 同步嵌套事务占位（复用外层事务）


### `class _SyncTransaction`

> **内部方法**
同步事务兼容上下文

在桥接事件循环上开启事务，并把事务句柄按调用线程登记，
使事务块内的同步操作路由到事务连接。


### `class BaseQueryBuilder(ABC)`

查询构建器抽象基类

定义链式调用风格的查询构建接口，所有链式方法返回 self，
终止方法返回实际结果。

终止方法以异步原生（aExecute/aExecuteOne/aCount/aExists）为抽象接口，
同步方法（Execute/...）由基类桥接提供兼容实现。

> **提示**
> 使用方式：
> 1. await storage.Table("users").Insert({"name": "Alice"}).aExecute()
> 2. storage.Table("users").Insert({"name": "Alice"}).Execute()  # 同步兼容


#### 方法列表


##### `ToDict()`

将 SELECT 结果以字典形式返回（链式修饰，返回 self）

设置后 ``Execute()`` / ``aExecute()`` 等终止方法的 SELECT 结果
从 tuple 转为 dict（列名 → 值）。未调用本方法的链保持原有
tuple 行为，完全向后兼容。

**返回值** (`self`): 
**示例**:
```python
>>> rows = await storage.Table("users").Select("name", "age").ToDict().aExecute()
>>> # [{'name': 'Alice', 'age': 30}, ...]
```

---


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


##### `async aExecute()`

执行构建的查询

- SELECT 返回 list[tuple]（调用 ToDict() 后为 list[dict]）
- INSERT/UPDATE/DELETE 返回受影响行数 int

**返回值**: 查询结果或受影响行数

---


##### `async aExecuteOne()`

执行查询并返回单条结果

**返回值** (`单行元组（调用`): ToDict() 后为字典）或 None

---


##### `async aCount()`

执行 COUNT 查询

**返回值**: 匹配的行数

---


##### `async aExists()`

检查是否存在匹配的记录

**返回值**: 是否存在

---


##### `_routed_execute(coro_factory: Any)`

> **内部方法**
同步终止方法执行入口：在调用方线程捕获事务路由连接后桥接执行

- **coro_factory** (`接受可选`): conn 关键字参数、返回协程的工厂
**返回值**: 查询结果

---


##### `Execute()`

执行构建的查询（同步兼容，桥接到 :meth:`aExecute`）

- SELECT 返回 list[tuple]（调用 ToDict() 后为 list[dict]）
- INSERT/UPDATE/DELETE 返回受影响行数 int

**返回值** (`查询结果或受影响行数`): 
**示例**:
```python
>>> rows = storage.Table("users").Select("name", "age").Execute()
```

---


##### `ExecuteOne()`

执行查询并返回单条结果（同步兼容，桥接到 :meth:`aExecuteOne`）

**返回值** (`单行元组（调用`): ToDict() 后为字典）或 None

---


##### `Count()`

执行 COUNT 查询（同步兼容，桥接到 :meth:`aCount`）

**返回值**: 匹配的行数

---


##### `Exists()`

检查是否存在匹配的记录（同步兼容，桥接到 :meth:`aExists`）

**返回值**: 是否存在

---


### `class BaseStorage(ABC)`

存储后端抽象基类（异步原生）

定义键值存储和表管理的统一接口，所有存储后端必须继承并实现此基类。

> **提示**
> 1. 异步方法（aget/aset/aExecute/...）为原生主接口，内置后端基于异步驱动实现
> 2. 同步方法（get/set/Execute/...）为兼容层，通过 AsyncBridge 桥接到后台事件循环
> 3. 异步事务使用 ``async with storage.atransaction():``，
> 同步事务使用 ``with storage.transaction():``（嵌套事务自动复用外层）
> 4. 自定义后端若不接受 ``conn`` 关键字参数（连接路由），请将类属性
> ``_SUPPORTS_CONN_ROUTING`` 设为 False（默认即为 False）


#### 方法列表


##### `_ensure_txn_state()`

> **内部方法**
确保同步事务登记表存在（``__new__`` 绕过 ``__init__`` 的实例兜底）

---


##### `_is_ready()`

> **内部方法**
检查存储后端是否已初始化完成

**返回值**: 是否已初始化完成

---


##### `_bridge_run(coro: Any, timeout: float | None = None)`

> **内部方法**
将协程提交到桥接事件循环并阻塞等待结果（同步兼容层的执行入口）

- **coro** (`要执行的协程对象`): - **timeout**: 可选超时秒数
**返回值**: 协程的返回值

---


##### `_routing_conn()`

> **内部方法**
获取当前调用线程绑定的同步事务连接（无活动事务时为 None）

仅在 ``_SUPPORTS_CONN_ROUTING`` 为 True 的后端上生效。

---


##### `_register_sync_txn(thread_id: int, txn: _AsyncTransaction)`

> **内部方法** 按调用线程登记同步事务句柄

---


##### `_unregister_sync_txn(thread_id: int)`

> **内部方法** 移除调用线程的同步事务登记

---


##### `async _new_async_transaction_and_start()`

> **内部方法**
创建并开启事务句柄（同步事务入口，须在桥接循环上执行，
保证事务连接与后续同步路由操作处于同一事件循环）

---


##### `async _acquire_txn_conn()`

> **内部方法**
获取事务专用连接

**返回值**: 后端连接对象

---


##### `async _begin_txn(conn: Any)`

> **内部方法** 开启事务

**返回值** (`方言事务句柄（无需句柄的后端返回`): None）

---


##### `async _commit_txn(conn: Any, handle: Any = None)`

> **内部方法** 提交事务

---


##### `async _rollback_txn(conn: Any, handle: Any = None)`

> **内部方法** 回滚事务

---


##### `async _release_txn_conn(conn: Any)`

> **内部方法** 释放事务专用连接

---


##### `async aget(key: str, default: Any = None)`

异步获取存储项的值

支持嵌套键访问，如 "user.settings.theme" 会从存储的嵌套对象中获取值

- **key** (`存储项键名，支持嵌套路径（如`): "user.settings.theme"）
- **default** (`默认值（当键不存在时返回）`): - **conn**: 内部参数：事务连接路由（``_SUPPORTS_CONN_ROUTING`` 为 True
    的后端须接收；默认 None 表示自行获取连接）
**返回值** (`存储项的值`): 
**示例**:
```python
>>> timeout = await storage.aget("network.timeout", 30)
```

---


##### `async aset(key: str, value: Any)`

异步设置存储项的值

支持嵌套键设置，如 "user.settings.theme" 会更新存储的嵌套对象中的对应字段

- **key** (`存储项键名，支持嵌套路径（如`): "user.settings.theme"）
- **value** (`存储项的值`): - **conn**: 内部参数：事务连接路由
**返回值** (`操作是否成功`): 
**示例**:
```python
>>> await storage.aset("app.name", "MyApp")
```

---


##### `async adelete(key: str)`

异步删除存储项

支持嵌套键删除，如 "user.settings.theme" 会删除嵌套对象中的对应字段

- **key** (`存储项键名，支持嵌套路径`): - **conn**: 内部参数：事务连接路由
**返回值** (`操作是否成功`): 
**示例**:
```python
>>> await storage.adelete("temp.session")
```

---


##### `async aget_all_keys()`

异步获取所有存储项的键名

- **conn** (`内部参数：事务连接路由`): **返回值** (`键名列表`): 
**示例**:
```python
>>> all_keys = await storage.aget_all_keys()
```

---


##### `async aclear()`

异步清空所有存储项

- **conn** (`内部参数：事务连接路由`): **返回值** (`操作是否成功`): 
**示例**:
```python
>>> await storage.aclear()
```

---


##### `Table(table_name: str)`

获取指定表的查询构建器

- **table_name** (`表名`): **返回值** (`查询构建器实例`): 
**示例**:
```python
>>> rows = await storage.Table("users").Select("name").aExecute()
```

---


##### `async aCreateTable(table_name: str, columns: dict[str, str])`

异步创建表

- **table_name** (`表名`): - **columns**: 列名到类型的映射（如 {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}）
**返回值**: 操作是否成功

---


##### `async aDropTable(table_name: str)`

异步删除表

- **table_name** (`表名`): **返回值**: 操作是否成功

---


##### `async aHasTable(table_name: str)`

异步检查表是否存在

- **table_name** (`表名`): **返回值**: 是否存在

---


##### `async atransaction()`

异步事务上下文管理器

事务块内的异步操作路由到事务专用连接，保证原子性。
嵌套调用时复用外层事务（与同步版语义一致）。
异常时自动回滚并向外传播。

**返回值** (`异步上下文管理器，yield`): 事务句柄

**示例**:
```python
>>> async with storage.atransaction():
...     await storage.aset("key1", "value1")
...     await storage.aset("key2", "value2")
```

---


##### `get(key: str, default: Any = None)`

获取存储项的值（同步兼容，桥接到 :meth:`aget`）

- **key** (`存储项键名，支持嵌套路径（如`): "user.settings.theme"）
- **default** (`默认值（当键不存在时返回）`): **返回值** (`存储项的值`): 
**示例**:
```python
>>> timeout = storage.get("network.timeout", 30)
```

---


##### `set(key: str, value: Any)`

设置存储项的值（同步兼容，桥接到 :meth:`aset`）

- **key** (`存储项键名，支持嵌套路径`): - **value**: 存储项的值
**返回值** (`操作是否成功`): 
**示例**:
```python
>>> storage.set("app.name", "MyApp")
```

---


##### `delete(key: str)`

删除存储项（同步兼容，桥接到 :meth:`adelete`）

- **key** (`存储项键名，支持嵌套路径`): **返回值** (`操作是否成功`): 
**示例**:
```python
>>> storage.delete("temp.session")
```

---


##### `get_all_keys()`

获取所有存储项的键名（同步兼容，桥接到 :meth:`aget_all_keys`）

**返回值** (`键名列表`): 
**示例**:
```python
>>> all_keys = storage.get_all_keys()
```

---


##### `clear()`

清空所有存储项（同步兼容，桥接到 :meth:`aclear`）

**返回值** (`操作是否成功`): 
**示例**:
```python
>>> storage.clear()
```

---


##### `transaction()`

创建同步事务上下文（兼容层）

事务块内的同步操作路由到事务专用连接，保证原子性。
同步嵌套调用时复用外层事务。异常时自动回滚并向外传播。

**返回值** (`事务上下文管理器`): 
**示例**:
```python
>>> with storage.transaction():
...     storage.set("key1", "value1")
...     storage.set("key2", "value2")
```

---


##### `CreateTable(table_name: str, columns: dict[str, str])`

创建表（同步兼容，桥接到 :meth:`aCreateTable`）

- **table_name** (`表名`): - **columns**: 列名到类型的映射
**返回值** (`操作是否成功`): 
**示例**:
```python
>>> storage.CreateTable("users", {
...     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
...     "name": "TEXT NOT NULL"
... })
```

---


##### `DropTable(table_name: str)`

删除表（同步兼容，桥接到 :meth:`aDropTable`）

- **table_name** (`表名`): **返回值** (`操作是否成功`): 
**示例**:
```python
>>> storage.DropTable("users")
```

---


##### `HasTable(table_name: str)`

检查表是否存在（同步兼容，桥接到 :meth:`aHasTable`）

- **table_name** (`表名`): **返回值** (`是否存在`): 
**示例**:
```python
>>> if storage.HasTable("users"):
...     print("users 表已存在")
```

---


##### `get_multi(keys: list[str])`

批量获取多个存储项的值

仅返回存在的键。默认实现逐键调用 :meth:`get`，后端可覆写为单次批量查询。

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


##### `keys()`

获取所有存储项的键名（代理到 get_all_keys）

**返回值**: 键名列表

---


##### `async aclose()`

异步关闭当前事件循环上绑定的后端资源（连接/连接池）

默认无操作，持有连接池的后端应覆写此方法。

**示例**:
```python
>>> await storage.aclose()
```

---


##### `close()`

关闭当前事件循环上绑定的后端资源（同步兼容，桥接到 :meth:`aclose`）

**示例**:
```python
>>> storage.close()
```

---


##### `getConfig(key: str, default: Any = None)`

获取模块/适配器配置项（委托给config模块）

- **key** (`配置项的键(支持点分隔符如"module.sub.key")`): - **default**: 默认值
**返回值** (`配置项的值`): > **已弃用** 请使用 `config.getConfig` 来获取配置项，这个API已弃用

---


##### `setConfig(key: str, value: Any)`

设置模块/适配器配置（委托给config模块）

- **key** (`配置项键名(支持点分隔符如"module.sub.key")`): - **value**: 配置项值
**返回值** (`操作是否成功`): > **已弃用** 请使用 `config.setConfig` 来设置配置项，这个API已弃用

---

