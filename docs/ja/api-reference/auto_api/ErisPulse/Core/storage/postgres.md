# `ErisPulse.Core.storage.postgres` 模块

---

## 模块概述


ErisPulse PostgreSQL 存储后端（asyncpg 异步原生实现）

通过 ``ErisPulse.storage.backend = "postgres"``（或 "postgresql"）启用，
连接参数来自 ``ErisPulse.storage.postgres`` 配置节。需安装可选依赖：
``pip install ErisPulse[postgres]``

> **提示**
> 1. 连接池按事件循环惰性创建（同步桥接循环与用户异步循环各自独立）
> 2. 事务使用 ``conn.transaction()`` 句柄管理（asyncpg 推荐方式）

---

## 类列表


### `class PostgresDialect(SQLDialect)`

PostgreSQL 方言实现


#### 方法列表


##### `translate_sql(sql: str)`

> **内部方法** ``?`` → ``$1..$n``（asyncpg 序号参数风格）

---


##### `upsert_kv_sql(table: str, key_col: str, value_col: str)`

> **内部方法** ON CONFLICT DO UPDATE 形式的 UPSERT

---


##### `has_table_sql(table_name: str)`

> **内部方法** information_schema 查询当前 schema

---


##### `autoincrement_column(base_type: str)`

> **内部方法** ``SERIAL/BIGSERIAL PRIMARY KEY``

---


##### `is_missing_table_error(exc: BaseException)`

> **内部方法** asyncpg UndefinedTableError（按类名判定，避免强依赖驱动）

---


### `class PostgresStorage(_SingletonMixin, SQLStorageBase)`

PostgreSQL 存储管理器（asyncpg 异步原生实现）

单例模式实现，接口与 SQLite / MySQL 后端完全一致，可通过
``ErisPulse.storage.backend`` 配置项无感切换。

> **提示**
> 1. 连接参数见 ``ErisPulse.storage.postgres`` 配置节
> 2. 缺少驱动时提示安装 ``pip install ErisPulse[postgres]``


#### 方法列表


##### `_check_config_changed()`

> **内部方法** postgres 连接配置变更检查

---


##### `_init_db()`

> **内部方法** 初始化数据库（创建默认 config 键值表）

---


##### `_require_driver()`

> **内部方法** 惰性导入 asyncpg，缺失时给出安装指引

---


##### `async _create_loop_resource()`

> **内部方法** 当前事件循环的连接池

---


##### `async _destroy_loop_resource(resource: Any)`

> **内部方法** 优雅关闭连接池

---


##### `async _acquire_resource_conn(resource: Any)`

> **内部方法** 从池中获取连接

---


##### `async _release_resource_conn(resource: Any, conn: Any)`

> **内部方法** 归还连接到池

---


##### `async _open_txn_conn()`

> **内部方法** 事务使用池内专用连接（获取与释放在同一事件循环上）

---


##### `async _close_txn_conn(conn: Any)`

> **内部方法** 归还事务专用连接

---


##### `async _begin_txn(conn: Any)`

> **内部方法** 开启事务，返回 transaction 句柄

---


##### `async _commit_txn(conn: Any, handle: Any = None)`

> **内部方法** COMMIT

---


##### `async _rollback_txn(conn: Any, handle: Any = None)`

> **内部方法** ROLLBACK

---


##### `async _exec_query_on(kind: str, sql: str, params: Any, conn: Any)`

> **内部方法**
PostgreSQL 执行漏斗

- **kind** (`"select"`): / "one" / "count" / "dml" / "dml_multi"
**返回值** (`select/one`): 返回 (行, 列名列表或None)；其余返回受影响行数

---

