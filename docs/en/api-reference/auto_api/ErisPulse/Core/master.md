# `ErisPulse.Core.master` 模块

---

## 模块概述


框架主人管理系统

提供统一的用户主人身份识别能力，供命令系统（``master`` 参数）
及业务层（``master.is_master()``）使用。

主人配置位于 ``ErisPulse.master.users``，支持两种格式：
1. **dict**（按平台指定）：``{"yunhu": ["123"], "telegram": ["456"]}``
2. **list**（全局主人，所有平台生效）：``["123", "456"]``

除内置身份源（配置 + 运行时增删）外，还支持通过
``master.provider`` 注册自定义身份源，实现可插拔的身份判定
（如对接适配器管理员接口、数据库角色等）。

> **提示**
> 1. 通过 ``from ErisPulse.Core import master`` 导入单例
> 2. ``master.is_master(event)`` 或 ``master.is_master(platform, user_id)`` 检查身份
> 3. 支持运行时 ``master.add()`` / ``master.remove()`` 动态增删（不持久化到配置文件）
> 4. ``@master.provider`` 注册自定义身份源，任一 provider 放行即认定为主人；
> 注销用 ``fn.unregister()``

---

## 类列表


### `class MasterManager`

框架主人管理器（单例）

从配置读取主人列表，并支持运行时增删。
主人检查同时考虑配置中的主人、运行时添加的主人，
以及通过 :meth:`provider` 注册的自定义身份源（provider 链）。

> **提示**
> 1. 默认身份源：``ErisPulse.master.users`` 配置 + 运行时 ``add()`` 记录
> 2. ``@master.provider`` 可注册自定义身份源，
> ``fn(platform, user_id) -> bool``，任一 provider 放行即认定为主人
> 3. provider 异常会被捕获并跳过（不阻断身份判定链）


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

检查范围：配置中的主人 + 运行时添加的主人 + 已注册的 provider 链。
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


##### `_check_providers(platform: str, user_id: str)`

> **内部方法**
依次尝试 provider 链，任一放行即认定为主人

provider 异常被捕获并跳过（记录 warning），不阻断后续判定。

- **platform** (`平台名称`): - **user_id**: 用户 ID
**返回值** (`是否有`): provider 认定该用户为主人

---


##### `provider(fn: MasterProvider)`

注册自定义身份源 provider（装饰器 / 函数调用两用）

签名：``fn(platform: str, user_id: str) -> bool``，返回 True 表示
认定该用户为主人。所有 provider 在内置身份源（配置 + 运行时记录）
未命中时依次尝试，任一放行即认定为主人。

注册后原函数会挂上 ``fn.unregister()``，调用即可撤销该 provider。

provider 归属自动记录：若在模块 owner 上下文（如模块 ``on_load``）
内注册，模块卸载时会被框架自动注销（无需手动 ``unregister``）；
模块级装饰器用法（非加载上下文）为常驻身份源，仅显式注销。

- **fn** (`身份源检查函数（普通函数`): / 模块级函数皆可挂 ``unregister``；
           绑定实例方法请用模块级函数或在注册后自行保存注销句柄）
**返回值** (`原函数（已注册，并尽可能挂载`): ``unregister`` 方法）

**示例**:
```python
>>> from ErisPulse.Core import master
>>>
>>> # 装饰器用法（常驻身份源，推荐）
>>> @master.provider
... def admin_provider(platform, user_id):
...     return user_id in {"999"}  # 自定义判定逻辑
>>>
>>> master.is_master("yunhu", "999")  # True
>>> admin_provider.unregister()  # 不再需要时注销

>>> # 函数式用法（模块加载期注册、卸载期注销）
>>> fn = master.provider(admin_provider)
>>> fn.unregister()
```

---


##### `_drop_provider(fn: MasterProvider)`

> **内部方法**
从 provider 链移除指定函数（幂等）

- **fn** (`已注册的`): provider 函数

---


##### `unregister_by_owner(owner: str)`

注销指定 owner（模块）注册的全部 provider

模块在加载上下文（on_load）内注册的 provider 会由框架在卸载时
自动调用本方法，实现作用域清理——模块开发者无需在 on_unload 手动注销。

- **owner** (`模块名（owner）`): **返回值** (`注销的`): provider 数量

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
>>> master.add("yunhu", "123456")  # 持久化到配置
>>> master.add("yunhu", "999", persist=False)  # 仅本次运行有效
>>> master.add(None, "888")  # 全局主人
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
>>> master.remove("yunhu", "123456")  # 持久化
>>> master.remove("yunhu", "999", persist=False)  # 仅运行时
```

---


##### `reset()`

清空所有运行时主人与已注册的 provider（用于测试或软重启）

注意：不影响配置文件中的主人。
软重启时模块会被重新加载，provider 持有的旧引用一并清空，
由模块在新生命周期中重新注册。

---

