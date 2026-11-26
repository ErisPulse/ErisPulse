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

后端可插拔：外部包经 entry-points 组 ``erispulse.storage.backends`` 注册
（模块导入时调用 :func:`register_storage_backend`，声明自己的驱动依赖与
ConfigClass），``ErisPulse.storage.backend`` 填注册名即启用——驱动自动
安装、报错指引、线程桥接等行为整套继承，框架零改动。
mysql / postgres 连接失败时快速失败（冷却后自动重连），不影响框架运行。

> **提示**
> 1. 支持JSON序列化存储复杂数据类型
> 2. 提供事务支持确保数据一致性
> 3. 提供链式调用风格的通用 SQL 查询构建器

---

## 函数列表


### `register_storage_backend(name: str, storage_cls: 'type[SQLStorageBase]') -> None`

注册存储后端（可插拔机制）

外部包在模块导入时调用本函数自注册；``ErisPulse.storage.backend`` 填
注册名即启用，驱动自动安装（方言声明 ``driver_requires``）、线程桥接
（``_SUPPORTS_THREAD_BRIDGE``）、ConfigClass 表单等行为整套继承。

- **name**: 后端注册名（配置 ``storage.backend`` 用）
- **storage_cls**: 存储类（SQLStorageBase 子类）

---


### `get_registered_backends() -> 'list[str]'`

列出已注册的后端名（交互式配置/向导的枚举来源）

**返回值**: 后端名列表（含内置与外部注册）

---


### `_load_entrypoint_backends() -> None`

**内部方法** 扫描 entry-points 组并加载外部后端包（幂等）

---


### `create_storage() -> SQLStorageBase`

根据配置创建存储后端实例

读取 ``ErisPulse.storage.backend`` 配置项，从注册表实例化对应后端；
创建前扫描 entry-points 装载外部后端包（时序解法：注册发生在首次
创建时，晚于框架启动的模块加载阶段）。驱动缺失时按方言声明自动安装。

**返回值**: 存储后端实例

**异常**: `ValueError` - 配置了未注册的后端名称时（附可用后端列表）

**示例**:

```python
storage = create_storage()
```

---

