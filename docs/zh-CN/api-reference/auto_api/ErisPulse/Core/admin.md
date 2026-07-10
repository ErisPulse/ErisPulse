# `ErisPulse.Core.admin` 模块

---

## 模块概述


管理员管理系统

提供统一的用户管理员身份识别能力，供命令系统（``must_admin`` 参数）
及业务层（``admin.is_admin()``）使用。

管理员配置位于 ``ErisPulse.admin.users``，支持两种格式：
1. **dict**（按平台指定）：``{"yunhu": ["123"], "telegram": ["456"]}``
2. **list**（全局管理员，所有平台生效）：``["123", "456"]``

> **提示**
> 1. 通过 ``from ErisPulse.Core import admin`` 导入单例
> 2. ``admin.is_admin(event)`` 或 ``admin.is_admin(platform, user_id)`` 检查身份
> 3. 支持运行时 ``admin.add()`` / ``admin.remove()`` 动态增删（不持久化到配置文件）

---

## 类列表


### `class AdminManager`

管理员管理器（单例）

从配置读取管理员列表，并支持运行时增删。
管理员检查同时考虑配置中的管理员和运行时添加的管理员。


#### 方法列表


##### `_load_config_admins()`

从配置加载管理员列表

:return: (platform_admins, global_admins)
    - platform_admins: {platform: {user_id, ...}}
    - global_admins: {user_id, ...}

---


##### `is_admin(platform_or_event: Union[str, _EventLike], user_id: str | None = None)`

检查是否为管理员

支持两种调用方式：
- ``admin.is_admin(event)`` — 从事件对象提取 platform 和 user_id
- ``admin.is_admin(platform, user_id)`` — 显式指定

检查范围：配置中的管理员 + 运行时添加的管理员。
全局管理员（配置为 list 或运行时添加为 None 平台）对所有平台生效。

:param platform_or_event: 平台名称 或 事件对象
:param user_id: 用户 ID（当第一个参数为平台名时使用）
:return: 是否为管理员

**示例**:
```python
>>> from ErisPulse.Core import admin
>>>
>>> # 从事件检查
>>> if admin.is_admin(event):
...     await event.reply("管理员你好")
>>>
>>> # 显式检查
>>> if admin.is_admin("yunhu", "123456"):
...     print("是管理员")
```

---


##### `list()`

获取所有管理员列表

:return: 字典，``{"global": [...], "<platform>": [...]}`
    global 键包含对所有平台生效的管理员

---


##### `add(platform: str | None, user_id: str)`

运行时添加管理员（不持久化到配置文件，重启后失效）

:param platform: 平台名称，None 表示全局管理员
:param user_id: 用户 ID

**示例**:
```python
>>> from ErisPulse.Core import admin
>>> admin.add("yunhu", "123456")   # 指定平台
>>> admin.add(None, "999")          # 全局
```

---


##### `remove(platform: str | None, user_id: str)`

移除运行时添加的管理员

注意：此方法仅移除运行时添加的管理员，不影响配置文件中的管理员。
要移除配置中的管理员，请修改 ``ErisPulse.admin.users`` 配置。

:param platform: 平台名称，None 表示全局
:param user_id: 用户 ID
:return: 是否成功移除（不存在则返回 False）

---


##### `reset()`

清空所有运行时管理员（用于测试或软重启）

注意：不影响配置文件中的管理员。

---

