# `ErisPulse.Core.master` 模块

---

## 模块概述


框架主人管理系统

提供统一的用户主人身份识别能力，供命令系统（``master`` 参数）
及业务层（``master.is_master()``）使用。

主人配置位于 ``ErisPulse.master.users``，支持两种格式：
1. **dict**（按平台指定）：``{"yunhu": ["123"], "telegram": ["456"]}``
2. **list**（全局主人，所有平台生效）：``["123", "456"]``

> **提示**
> 1. 通过 ``from ErisPulse.Core import master`` 导入单例
> 2. ``master.is_master(event)`` 或 ``master.is_master(platform, user_id)`` 检查身份
> 3. 支持运行时 ``master.add()`` / ``master.remove()`` 动态增删（不持久化到配置文件）

---

## 类列表


### `class MasterManager`

框架主人管理器（单例）

从配置读取主人列表，并支持运行时增删。
主人检查同时考虑配置中的主人和运行时添加的主人。


#### 方法列表


##### `_load_config_masters()`

从配置加载主人列表

**返回值** (`(platform_masters,`): global_masters)
    - platform_masters: {platform: {user_id, ...}}
    - global_masters: {user_id, ...}

---


##### `is_master(platform_or_event: str | _EventLike, user_id: str | None = None)`

检查是否为框架主人

支持两种调用方式：
- ``master.is_master(event)`` — 从事件对象提取 platform 和 user_id
- ``master.is_master(platform, user_id)`` — 显式指定

检查范围：配置中的主人 + 运行时添加的主人。
全局主人（配置为 list 或运行时添加为 None 平台）对所有平台生效。

- **platform_or_event** (`平台名称`): 或 事件对象
- **user_id** (`用户`): ID（当第一个参数为平台名时使用）
**返回值** (`是否为框架主人`): 
**示例**:
```python
>>> from ErisPulse.Core import master
>>>
>>> # 从事件检查
>>> if master.is_master(event):
...     await event.reply("主人你好")
>>>
>>> # 显式检查
>>> if master.is_master("yunhu", "123456"):
...     print("是主人")
```

---


##### `list()`

获取所有主人列表

**返回值** (`字典，``{"global":`): [...], "<platform>": [...]}``
    global 键包含对所有平台生效的主人

---


##### `add(platform: str | None, user_id: str, persist: bool = True)`

添加主人

- **platform** (`平台名称，None`): 表示全局主人
- **user_id** (`用户`): ID
- **persist** (`是否持久化到配置文件`): (默认: True)
                为 True 时写入 ``ErisPulse.master.users`` 配置，重启后仍然生效；
                为 False 时仅运行时生效，重启后失效。

**示例**:
```python
>>> from ErisPulse.Core import master
>>> master.add("yunhu", "123456")       # 持久化到配置
>>> master.add("yunhu", "999", persist=False)  # 仅本次运行有效
>>> master.add(None, "888")             # 全局主人
```

---


##### `remove(platform: str | None, user_id: str, persist: bool = True)`

移除主人

- **platform** (`平台名称，None`): 表示全局
- **user_id** (`用户`): ID
- **persist** (`是否持久化移除`): (默认: True)
                为 True 时同时从配置文件中移除；
                为 False 时仅移除运行时记录。
**返回值** (`是否成功移除（不存在则返回`): False）

**示例**:
```python
>>> from ErisPulse.Core import master
>>> master.remove("yunhu", "123456")           # 持久化
>>> master.remove("yunhu", "999", persist=False)  # 仅运行时
```

---


##### `reset()`

清空所有运行时主人（用于测试或软重启）

注意：不影响配置文件中的主人。

---

