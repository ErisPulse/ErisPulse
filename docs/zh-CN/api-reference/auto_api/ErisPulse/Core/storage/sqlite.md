# `ErisPulse.Core.storage.sqlite` 模块

---

## 模块概述


ErisPulse SQLite 存储后端（aiosqlite 异步原生实现）

默认存储后端。数据库文件位于项目目录 ``config/config.db``；
启用 ``use_global_db`` 时使用包内全局数据库 ``data/config.db``。

> **提示**
> 1. 非事务操作复用每事件循环的单个共享连接（autocommit 模式）
> 2. 事务使用专用连接（BEGIN/COMMIT/ROLLBACK），与共享连接互不干扰
> 3. WAL 日志模式 + busy_timeout，支持多事件循环（如同步桥接循环）并发访问

---

## 类列表


### `class SQLiteDialect(SQLDialect)`

SQLite 方言实现


#### 方法列表


##### `autoincrement_column(base_type: str)`

> **内部方法** SQLite 原生支持 AUTOINCREMENT 后缀

---


##### `is_missing_table_error(exc: BaseException)`

> **内部方法** sqlite3.OperationalError: no such table

---


### `class SQLiteStorage(_SingletonMixin, SQLStorageBase)`

SQLite 存储管理器（aiosqlite 异步原生实现）

单例模式实现，提供键值存储的增删改查、通用 SQL 链式查询和事务管理。

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 data/config.db（``use_global_db`` 开启且文件存在时）

> **提示**
> 1. 使用 get/set（或 aget/aset）方法操作键值存储项
> 2. 使用 Table() 链式调用操作自定义表
> 3. 使用 transaction/atransaction 上下文管理事务


#### 方法列表


##### `_check_use_global_db_changed()`

> **内部方法** use_global_db 配置变更检查

---


##### `_ensure_directories()`

> **内部方法** 确保必要的目录存在

---


##### `_init_db()`

> **内部方法**
初始化数据库（创建默认 config 键值表）

**异常**: `sqlite3.OperationalError` - 数据库文件无法创建或打开时

---


##### `async _apply_pragmas(conn: aiosqlite.Connection)`

> **内部方法** 应用标准 PRAGMA（WAL/synchronous/busy_timeout）

---


##### `async _create_loop_resource()`

> **内部方法** 当前事件循环的共享连接（autocommit 模式）

---


##### `async _destroy_loop_resource(resource: aiosqlite.Connection)`

> **内部方法** 关闭共享连接

---


##### `async _acquire_resource_conn(resource: aiosqlite.Connection)`

> **内部方法** 共享连接直接复用（游标级并发安全）

---


##### `async _release_resource_conn(resource: aiosqlite.Connection, conn: Any)`

> **内部方法** 共享连接无需归还

---


##### `async _open_txn_conn()`

> **内部方法** 事务使用专用连接（与共享连接互不干扰）

---


##### `async _close_txn_conn(conn: aiosqlite.Connection)`

> **内部方法** 关闭事务专用连接

---


##### `async _begin_txn(conn: Any)`

> **内部方法** BEGIN TRANSACTION

---


##### `async _commit_txn(conn: Any, handle: Any = None)`

> **内部方法** COMMIT

---


##### `async _rollback_txn(conn: Any, handle: Any = None)`

> **内部方法** ROLLBACK

---


##### `async _exec_query_on(kind: str, sql: str, params: Any, conn: Any)`

> **内部方法**
SQLite 执行漏斗

- **kind** (`"select"`): / "one" / "count" / "dml" / "dml_multi"
**返回值** (`select/one`): 返回 (行, 列名列表或None)；其余返回受影响行数

---

