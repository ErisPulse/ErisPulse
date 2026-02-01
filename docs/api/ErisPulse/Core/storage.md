# `ErisPulse.Core.storage` 模块

> 最后更新：2026-02-02 05:58:18

---

## 模块概述


ErisPulse 存储管理模块

提供键值存储和事务支持，用于管理框架运行时数据。
基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 ../data/config.db

用户可通过在 config.toml 中配置以下选项来选择使用全局数据库：
```toml
[ErisPulse.storage]
use_global_db = true
```

> **提示**
> 1. 支持JSON序列化存储复杂数据类型
> 2. 提供事务支持确保数据一致性

---

## 类列表


### `class StorageManager`

存储管理器

单例模式实现，提供键值存储的增删改查和事务管理

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 ../data/config.db

用户可通过在 config.toml 中配置以下选项来选择使用全局数据库：
```toml
[ErisPulse.storage]
use_global_db = true
```

> **提示**
> 1. 使用get/set方法操作存储项
> 2. 使用transaction上下文管理事务


#### 方法列表


##### `_get_connection()`

获取数据库连接（支持事务）

如果在事务中，返回事务的连接
否则创建新连接

---


##### `_ensure_directories()`

确保必要的目录存在

---


##### `_init_db()`

> **内部方法** 
初始化数据库

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


##### `set_multi(items: Dict[str, Any])`

批量设置多个存储项

:param items: 键值对字典
:return: 操作是否成功

**示例**:
```python
>>> storage.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })
```

---


##### `getConfig(key: str, default: Any = None)`

获取模块/适配器配置项（委托给config模块）
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

---


##### `setConfig(key: str, value: Any)`

设置模块/适配器配置（委托给config模块）
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功

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


##### `delete_multi(keys: List[str])`

批量删除多个存储项

:param keys: 键名列表
:return: 操作是否成功

**示例**:
```python
>>> storage.delete_multi(["temp.key1", "temp.key2"])
```

---


##### `get_multi(keys: List[str])`

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
>>>     storage.set("key1", "value1")
>>>     storage.set("key2", "value2")
```

---


##### `clear()`

清空所有存储项

:return: 操作是否成功

**示例**:
```python
>>> storage.clear()  # 清空所有存储
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

