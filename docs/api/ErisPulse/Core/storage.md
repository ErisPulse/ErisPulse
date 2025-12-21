# `ErisPulse.Core.storage` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 存储管理模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架运行时数据。
基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 ../data/config.db

用户可通过在 config.toml 中配置以下选项来选择使用全局数据库：
```toml
[ErisPulse.storage]
use_global_db = true
```

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失</p></div>

---

## 类列表

### `class StorageManager`

    存储管理器

单例模式实现，提供键值存储的增删改查、事务和快照管理

支持两种数据库模式：
1. 项目数据库（默认）：位于项目目录下的 config/config.db
2. 全局数据库：位于包内的 ../data/config.db

用户可通过在 config.toml 中配置以下选项来选择使用全局数据库：
```toml
[ErisPulse.storage]
use_global_db = true
```

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用get/set方法操作存储项
2. 使用transaction上下文管理事务
3. 使用snapshot/restore管理数据快照</p></div>

    
#### 方法列表

##### `_ensure_directories()`

    确保必要的目录存在

    ---
    
##### `_init_db()`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
初始化数据库

    ---
    
##### `get(key: str, default: Any = None)`

    获取存储项的值

:param key: 存储项键名
:param default: 默认值(当键不存在时返回)
:return: 存储项的值

<details class='example'><summary>示例</summary>

```python
>>> timeout = storage.get("network.timeout", 30)
>>> user_settings = storage.get("user.settings", {})
```
</details>

    ---
    
##### `get_all_keys()`

    获取所有存储项的键名

:return: 键名列表

<details class='example'><summary>示例</summary>

```python
>>> all_keys = storage.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个存储项")
```
</details>

    ---
    
##### `set(key: str, value: Any)`

    设置存储项的值

:param key: 存储项键名
:param value: 存储项的值
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.set("app.name", "MyApp")
>>> storage.set("user.settings", {"theme": "dark"})
```
</details>

    ---
    
##### `set_multi(items: Dict[str, Any])`

    批量设置多个存储项

:param items: 键值对字典
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })
```
</details>

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

<details class='example'><summary>示例</summary>

```python
>>> storage.delete("temp.session")
```
</details>

    ---
    
##### `delete_multi(keys: List[str])`

    批量删除多个存储项

:param keys: 键名列表
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.delete_multi(["temp.key1", "temp.key2"])
```
</details>

    ---
    
##### `get_multi(keys: List[str])`

    批量获取多个存储项的值

:param keys: 键名列表
:return: 键值对字典

<details class='example'><summary>示例</summary>

```python
>>> settings = storage.get_multi(["app.name", "app.version"])
```
</details>

    ---
    
##### `transaction()`

    创建事务上下文

:return: 事务上下文管理器

<details class='example'><summary>示例</summary>

```python
>>> with storage.transaction():
>>>     storage.set("key1", "value1")
>>>     storage.set("key2", "value2")
```
</details>

    ---
    
##### `_check_auto_snapshot()`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
检查并执行自动快照

    ---
    
##### `set_snapshot_interval(seconds: int)`

    设置自动快照间隔

:param seconds: 间隔秒数

<details class='example'><summary>示例</summary>

```python
>>> # 每30分钟自动快照
>>> storage.set_snapshot_interval(1800)
```
</details>

    ---
    
##### `clear()`

    清空所有存储项

:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.clear()  # 清空所有存储
```
</details>

    ---
    
##### `__getattr__(key: str)`

    通过属性访问存储项

:param key: 存储项键名
:return: 存储项的值

<dt>异常</dt><dd><code>AttributeError</code> 当存储项不存在时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> app_name = storage.app_name
```
</details>

    ---
    
##### `__setattr__(key: str, value: Any)`

    通过属性设置存储项

:param key: 存储项键名
:param value: 存储项的值
    
<details class='example'><summary>示例</summary>

```python
>>> storage.app_name = "MyApp"
```
</details>

    ---
    
##### `snapshot(name: Optional[str] = None)`

    创建数据库快照

:param name: 快照名称(可选)
:return: 快照文件路径

<details class='example'><summary>示例</summary>

```python
>>> # 创建命名快照
>>> snapshot_path = storage.snapshot("before_update")
>>> # 创建时间戳快照
>>> snapshot_path = storage.snapshot()
```
</details>

    ---
    
##### `restore(snapshot_name: str)`

    从快照恢复数据库

:param snapshot_name: 快照名称或路径
:return: 恢复是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.restore("before_update")
```
</details>

    ---
    
##### `list_snapshots()`

    列出所有可用的快照

:return: 快照信息列表(名称, 创建时间, 大小)

<details class='example'><summary>示例</summary>

```python
>>> for name, date, size in storage.list_snapshots():
>>>     print(f"{name} - {date} ({size} bytes)")
```
</details>

    ---
    
##### `delete_snapshot(snapshot_name: str)`

    删除指定的快照

:param snapshot_name: 快照名称
:return: 删除是否成功

<details class='example'><summary>示例</summary>

```python
>>> storage.delete_snapshot("old_backup")
```
</details>

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>