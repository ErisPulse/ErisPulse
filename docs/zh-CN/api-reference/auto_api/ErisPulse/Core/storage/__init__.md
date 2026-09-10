# `ErisPulse.Core.storage.__init__` 模块

---

## 模块概述


ErisPulse 存储管理模块

提供键值存储、通用 SQL 链式查询和事务支持，用于管理框架运行时数据。
内置三种异步原生后端，通过 ``ErisPulse.storage.backend`` 配置项选择：
1. sqlite（默认）：aiosqlite，项目目录 config/config.db
2. mysql：aiomysql，配置见 ``ErisPulse.storage.mysql``
3. postgres：asyncpg，配置见 ``ErisPulse.storage.postgres``

三种后端 API 完全一致，切换后端无需修改调用代码。
mysql / postgres 连接失败时快速失败（冷却后自动重连），不影响框架运行。

> **提示**
> 1. 支持JSON序列化存储复杂数据类型
> 2. 提供事务支持确保数据一致性
> 3. 提供链式调用风格的通用 SQL 查询构建器

---

## 函数列表


### `create_storage()`

根据配置创建存储后端实例

读取 ``ErisPulse.storage.backend`` 配置项，实例化对应后端。
驱动缺失时报错并提示安装命令。

**返回值** (`存储后端实例`): **异常**: `ValueError` - 配置了未知的后端名称时

**示例**:
```python
>>> storage = create_storage()
```

---

