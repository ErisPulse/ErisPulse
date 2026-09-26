# `ErisPulse.Core.shadow` 模块

---

## 模块概述


ErisPulse 影子模块（方向十一：Shadow Modules & Canary Promote）

影子 = 同一模块的新版本，以**独立 owner**（如 ``roll_shadow``）与线上
旧版并存试运行：它收到真实事件的**副本**、其出站被**拦截记账**而非真正
发出——确认无害后 ``promote`` 一键转正，``dismiss`` 随时放弃。模块代码
零改动，全程 **API 驱动**（运行时操作，与 load / unload / reload 同类；
Dashboard / 自定义管理模块调用这些 API，无需用户手写任何配置）。

- 机制与诚实边界：docs/zh-CN/advanced/shadow.md

> **提示**
> 1. ``sdk.module.shadow_start("roll", source="路径/到/v2")`` 启动影子：
> source 为新版代码的目录或单文件路径（建议放在 plugins 目录之外，
> 避免被普通发现机制装载）；影子 owner 名默认取路径名
> 2. 出站拦截覆盖 Send DSL 与 Api DSL；绕过框架的裸 call_api / aiohttp /
> 线程拦不住；ORM 读写不进存储覆盖层
> 3. 转正永远由人确认：``await sdk.module.promote_shadow("roll")``，失败
> 自动回滚旧实例继续服务；``dismiss_shadow`` 随时放弃

---

## 类列表


### `class ShadowLedger`

影子账本：影子 owner 的意向出站记录（内存环形，按 owner 分桶）

记录来源：出站闸（``Send`` DSL / ``Api`` DSL）在 owner 属影子时写入。
每条含 kind（send/api）/ platform / method / target / trace_id / preview。


#### 方法列表


##### `record(owner: str, entry: 'dict[str, Any]')`

记录一条影子意向出站

- **owner** (`影子`): owner 名
- **entry** (`出站条目（kind/platform/method/target/trace_id/preview`): 等）

---


##### `entries(owner: str)`

读取影子 owner 的全部在账条目（时间序）

- **owner** (`影子`): owner 名
**返回值**: 条目列表（无在账条目时为空列表）

---


##### `clear(owner: str)`

清空影子 owner 的账本

- **owner** (`影子`): owner 名

---


### `class ShadowOverlay`

存储内存覆盖层：影子 owner 的 KV 写隔离

语义：写进覆盖层（不落库）、删为墓碑、读先查覆盖层——命中返回影子值，
命中墓碑视为"已删除"（回退默认值），未命中透传真库。ORM 读写不在
覆盖层语义内（文档声明）。


#### 方法列表


##### `write(key: str, value: Any)`

写入覆盖层

---


##### `delete(key: str)`

写入墓碑（影子视角的删除）

---


##### `read(key: str)`

查询覆盖层

- **key** (`存储键（含嵌套路径原样匹配）`): **返回值** (`(状态,`): 值)；状态 "hit"（影子值）/ "tombstone"（影子已删除，
         不应透传真库）/ "miss"（未命中，透传真库）

---


### `class ShadowManager`

影子模块管理器（单例）

维护 原模块名 → 影子实例 的绑定、影子账本与存储覆盖层，并提供
start（启动影子）/ promote（转正）/ dismiss（放弃）/ diff（对比）。
子系统八道闸只依赖 ``ownership.is_shadow`` 与 :data:`shadow_ledger` /
:func:`shadow_overlay`，不反向依赖本管理器。


#### 方法列表


##### `shadow_owner_of(real_name: str)`

查询原模块当前绑定的影子 owner 名

- **real_name** (`原模块名`): **返回值** (`影子`): owner 名（未绑定为 None）

---


##### `real_name_of(shadow_owner: str)`

查询影子 owner 对应的原模块名

- **shadow_owner** (`影子`): owner 名
**返回值** (`原模块名（非影子为`): None）

---


##### `bind(real_name: str, shadow_owner: str)`

登记 绑定关系（影子启动成功后调用；同时向归属权登记影子状态）

- **real_name** (`原模块名`): - **shadow_owner**: 影子 owner 名

---


##### `unbind(shadow_owner: str)`

解除影子绑定（dismiss / 转正后调用；同步移除归属权影子状态）

- **shadow_owner** (`影子`): owner 名
**返回值** (`对应原模块名（未绑定为`): None）

---


##### `overlay(shadow_owner: str)`

获取影子 owner 的存储覆盖层（惰性创建）

- **shadow_owner** (`影子`): owner 名
**返回值**: 覆盖层实例

---


##### `async start(real_name: str, source: 'str | Path', manager: Any, sdk: Any, owner: 'str | None' = None, loader: 'Any | None' = None)`

启动影子：把新版代码以独立 owner 装载为 ``real_name`` 的影子实例

source 为新版代码的**目录或单 .py 文件路径**（推荐放在 plugins 目录
之外，避免被普通发现机制当作独立模块装载）。影子以独立 owner 运行：
收到真实事件副本、出站被拦截记账、配置继承原模块配置节。

- **real_name** (`被`): shadow 的已加载模块名
- **source** (`新版代码路径（目录含`): ``__init__.py`` 或单 ``.py`` 文件）
- **manager** (`模块管理器实例`): - **sdk**: SDK 实例
- **owner** (`影子`): owner 名（默认取路径名，非法时回退
              ``f"{real_name}_shadow"``）
- **loader** (`模块加载器实例（None`): 时自动取 ``sdk._module_loader``）
**返回值** (`影子`): owner 名
**异常**: `RuntimeError` - 原模块未加载 / 影子已存在 / 源路径无效 /
                      影子装载失败

**示例**:
```python
>>> await sdk.module.shadow_start("roll", source="downloads/roll_v2")
'roll_shadow'
```

---


##### `async promote(real_name: str, manager: Any, sdk: Any, loader: 'Any | None' = None)`

转正：卸载当前版本 → 影子以真名注册加载 → 失败自动回滚继续服务

复用方向 10 的重载快照机制（当前版本与级联依赖者先行快照）。
转正后建议尽快把新版本持久化安装（pip 升级 / 替换插件文件），
使重启后仍然生效——运行时切换不会替你完成包管理。

- **real_name** (`原模块名`): - **manager**: 模块管理器实例
- **sdk** (`SDK`): 实例
- **loader** (`模块加载器实例（None`): 时自动取 ``sdk._module_loader``）
**返回值**: 是否转正成功

---


##### `async dismiss(real_name: str, manager: Any)`

放弃影子：回收影子资源、解除绑定、清空账本与命令目录

- **real_name** (`原模块名`): - **manager**: 模块管理器实例
**返回值**: 是否成功

---


##### `diff(real_name: str, transcript: 'Any | None' = None)`

行为对比：影子意向出站 × 真实发送时间线（按 trace_id 对齐）

内容保真度受 transcript 出站 preview（50 字符截断）限制——逐字段
对比以影子账本为准，transcript 仅作"实际发送发生"的佐证源。

- **real_name** (`原模块名`): - **transcript**: 收件箱单例（None 时惰性导入）
**返回值** (`{"shadow_owner",`): "count", "aligned": [{"shadow", "actual"}]}

---

