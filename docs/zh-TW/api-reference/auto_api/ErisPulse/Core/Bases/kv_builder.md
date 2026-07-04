# `ErisPulse.Core.Bases.kv_builder` 模块

---

## 模块概述


ErisPulse KV 查询构建器

将链式 SQL 操作（Table/Insert/Select/Where 等）映射为 KV 键前缀操作。
任何实现了 BaseStorage KV 接口的后端（Redis、内存字典等）均可使用。

键命名规则：
    _table:{table_name}:schema    — 表结构定义（列名 → 类型）
    _table:{table_name}:next_id   — 自增 ID 计数器
    _table:{table_name}:data:{id} — 行数据（JSON 序列化）

使用方式：
    >>> storage = MyKVStorage()
    >>> qb = KVQueryBuilder(storage, "users")
    >>> qb.Insert({"name": "Alice", "age": 30}).Execute()

> **提示**
> 1. 查询性能取决于 get_all_keys() 的效率
> 2. WHERE 条件在 Python 内存中过滤，不适合百万级数据
> 3. 适合中小规模的结构化数据存储

---

## 类列表


### `class KVQueryBuilder(BaseQueryBuilder)`

基于 KV 存储的查询构建器

将 Insert/Select/Update/Delete/Where/OrderBy/Limit 等链式操作
映射为对 BaseStorage KV 接口的调用。


#### 方法列表


##### `_get_next_id()`

获取并递增自增 ID

---


##### `_scan_rows()`

扫描所有行，返回 [(row_id, row_data), ...]

---


##### `_match_row(row: dict)`

检查行是否满足所有 WHERE 条件

---


##### `_bind_clauses()`

将 WHERE 子句中的 ? 替换为实际参数（只执行一次）

---


##### `_eval_clause(row: dict, clause: str)`

评估单条已绑定的 WHERE 子句

clause 中的占位符 `?` 已在 `_bind_clauses` 中替换为实际值。
支持的操作符: =, !=, >, >=, <, <=, LIKE

---


##### `_coerce_value(expected: Any, actual: Any)`

根据 actual 的类型，将 expected 转换为同类型

---


##### `_safe_cmp(a: Any, b: Any)`

安全比较，处理 None

---


##### `async async _ascan_rows()`

异步扫描所有行

---


##### `async async aExecute()`

异步执行查询

---

