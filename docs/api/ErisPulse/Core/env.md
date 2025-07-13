# `ErisPulse/Core/env` 模块

ErisPulse 环境配置模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

> **提示**：
1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失

## 类

### `EnvManager`

环境配置管理器

单例模式实现，提供配置的增删改查、事务和快照管理

> **提示**：
1. 使用get/set方法操作配置项
2. 使用transaction上下文管理事务
3. 使用snapshot/restore管理数据快照


#### 方法

##### `get`

获取配置项的值

:param key: 配置项键名
:param default: 默认值(当键不存在时返回)
:return: 配置项的值

:example:
>>> timeout = env.get("network.timeout", 30)
>>> user_settings = env.get("user.settings", {})


##### `get_all_keys`

获取所有配置项的键名

:return: 键名列表

:example:
>>> all_keys = env.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个配置项")


##### `set`

设置配置项的值

:param key: 配置项键名
:param value: 配置项的值
:return: 操作是否成功

:example:
>>> env.set("app.name", "MyApp")
>>> env.set("user.settings", {"theme": "dark"})


##### `set_multi`

批量设置多个配置项

:param items: 键值对字典
:return: 操作是否成功

:example:
>>> env.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })


##### `getConfig`

获取模块/适配器配置项
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值


##### `setConfig`

设置模块/适配器配置
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功


##### `delete`

删除配置项

:param key: 配置项键名
:return: 操作是否成功

:example:
>>> env.delete("temp.session")


##### `delete_multi`

批量删除多个配置项

:param keys: 键名列表
:return: 操作是否成功

:example:
>>> env.delete_multi(["temp.key1", "temp.key2"])


##### `get_multi`

批量获取多个配置项的值

:param keys: 键名列表
:return: 键值对字典

:example:
>>> settings = env.get_multi(["app.name", "app.version"])


##### `transaction`

创建事务上下文

:return: 事务上下文管理器

:example:
>>> with env.transaction():
>>>     env.set("key1", "value1")
>>>     env.set("key2", "value2")


##### `set_snapshot_interval`

设置自动快照间隔

:param seconds: 间隔秒数

:example:
>>> # 每30分钟自动快照
>>> env.set_snapshot_interval(1800)


##### `clear`

清空所有配置项

:return: 操作是否成功

:example:
>>> env.clear()  # 清空所有配置


##### `load_env_file`

加载env.py文件中的配置项

:return: 操作是否成功

:example:
>>> env.load_env_file()  # 加载env.py中的配置


##### `__getattr__`

通过属性访问配置项

:param key: 配置项键名
:return: 配置项的值

:raises KeyError: 当配置项不存在时抛出
    
:example:
>>> app_name = env.app_name


##### `__setattr__`

通过属性设置配置项

:param key: 配置项键名
:param value: 配置项的值
    
:example:
>>> env.app_name = "MyApp"


##### `snapshot`

创建数据库快照

:param name: 快照名称(可选)
:return: 快照文件路径

:example:
>>> # 创建命名快照
>>> snapshot_path = env.snapshot("before_update")
>>> # 创建时间戳快照
>>> snapshot_path = env.snapshot()


##### `restore`

从快照恢复数据库

:param snapshot_name: 快照名称或路径
:return: 恢复是否成功

:example:
>>> env.restore("before_update")


##### `list_snapshots`

列出所有可用的快照

:return: 快照信息列表(名称, 创建时间, 大小)

:example:
>>> for name, date, size in env.list_snapshots():
>>>     print(f"{name} - {date} ({size} bytes)")


##### `delete_snapshot`

删除指定的快照

:param snapshot_name: 快照名称
:return: 删除是否成功

:example:
>>> env.delete_snapshot("old_backup")

