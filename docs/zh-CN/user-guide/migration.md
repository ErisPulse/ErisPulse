# 升级迁移指南

> [!TIP]
> **什么时候需要读这篇**：从旧版本升级前，核对**需要动代码或核对部署**的破坏性变更。按你当前所在版本向下读对应小节即可；小版本补丁（patch）从不含迁移动作。逐版本完整变更见 [CHANGELOG](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)。

版本纪律：**补丁版本（x.y.Z）不含迁移动作**，需要动代码的变更只出现在 minor 版本（x.Y.0）；本页覆盖 **2.0.0 至今**的全部破坏性变更（2.5.0 为首个生产就绪版本，1.x → 2.0.0 的迁移见 CHANGELOG 的 2.0.0 条目）。

---

## 2.0.x → 2.5.0（生产就绪门槛）

- **⚠️ 严格模式默认开启（级别 1）**：未继承 `BaseModule` / `BaseAdapter` 的旧组件默认**拒绝加载**——豁免清单 `[ErisPulse.framework] strict_mode_exceptions.modules/adapters`，或 `strict_mode = 0` 宽松模式
- **首次启动语言确认交互**（i18n 五语言）：自动化部署需预设语言（`ERISPULSE_LANG` 环境变量或配置）
- 移除含 C 扩展的三方依赖（watchdog / packaging）——aarch64/ARM 安装兼容性提升，requirements 有锁定的部署需同步清理

## 2.5.x 系列内的破坏性变更

- **CLI 别名治理（2.5.5）**：`ini` 别名移除（与 install 过近）、`lr` 改为 `lsr`——脚本化的部署命令需同步
- **配置 Schema 重构（2.5.5）**：`BaseConfig` 通用基类（`AdapterConfig` 为兼容别名）、`description` 支持 i18n 格式；**移除 `AccountConfig` 别名**——自定义配置类继承需核对
- **适配器配置访问重构（2.5.5）**：`self.cfg` 实时读取（`self.config` 为兼容别名），移除 `_load_config()` / `_load_accounts()` 缓存方法——直接调用这两个私有方法的适配器需改走 `self.cfg`
- **组件发现默认启用（2.5.5）**：新安装组件默认 `enabled=true`

## 2.6.x

- **移除 `Core/web_status/` 整包**、外部看板娘图片与 `/status-assets` 静态挂载——依赖该路由的部署需迁移到 Dashboard

## 2.7.x

- **端口占用为致命错误（2.7.1）**：启动前同步预检，`sdk.init()` 返回 `False`，不再静默顺延端口——部署脚本需保证端口空闲
- **存储抽象层翻转为异步原生契约（2.7.1）**：异步接口（`aget` / `aset` / `aExecute` / `atransaction`）成为原生主接口，同步 API 成为内置兼容层——**现有同步调用零修改**；**自定义存储后端必须迁移到 a 前缀异步方法**（同步版抽象方法已移除）
- **`Core/storage` 改造为包**：SQLite 迁入 `Core/storage/sqlite.py`，MySQL / PostgreSQL 预置；`StorageManager` 保留兼容别名
- **2.8.0**：`sdk.reload_plugin` 更名 `sdk.reload_module`；独立事件准入系统 `Core/access.py` 并入 `scope.identity`（配置节 `ErisPulse.access` 移除，迁移到 `ErisPulse.scope.identity`）；命令 ACL 独立配置节并入 `event.command.acl`；bind 系作用域 API 收敛为字典式配置
- **移除**：安装脚本的 root/管理员强制确认

## 2.8.0 → 2.9.0

无破坏性变更（全部为声明式增量）；已捕获影子模块 `RuntimeError` / `ValueError` 的代码需按 2.9.0 注意事项调整。

## 2.9.0 → 2.10.0

- 配置写入引擎 tomlkit → **tomlclass**（零依赖无损 TOML 编辑）：注释/键顺序/空行保留语义不变——直接 import tomlkit 操作 `config.toml` 的外部工具链需迁移
- `uvicorn` 锁定 `>=0.35.0,<1.0`（能力探测 `Server._serve()`，缺失时回退公开 `serve()`）
- **2.10.0**：`epsdk init` / `create` 模板移除 `enabled` 配置字段——模块启停由框架统一管理，`ConfigClass` 只承载业务参数

## 2.10.x → 2.11.0

- **`sdk.restart()` 语义升级**为组件级热重载（模块热重载管线 + 适配器代码级重载）；框架自更新与 entry-point 增删场景改用 `hard_restart()`
- 实例锁迁移至 `.erispulse/config.lock`——有清理旧锁脚本（原 `config/config.lock`）的部署需同步路径

## 2.11.0 → 2.11.2

- **声明 `AccountConfigClass` 的适配器不再自动生成 `default` 账户模板**——账户改由用户在 Dashboard 账户向导创建，依赖"启动即有 default 账户"的部署需显式添加
- `reload()` / `restart()` 行为收紧（互斥与合并）对正常使用透明

## 2.11.x → 2.12.0

**① 存储写失败语义收紧（破坏性）**：写操作失败（写锁竞争超时 / SQL 错误 / 约束冲突）改为抛 `StorageOperationError`（`aset` / `adelete` / `aclear` / `set_multi` 及同步桥 `set` / `delete` 同路径），**不再静默返回 `False`**；连接级不可达的冷却期快速失败（`False` / `None`）不变。

```python
# 旧：靠返回值判断写失败
if not storage.set("key", "value"):
    ...

# 新：try/except
try:
    storage.set("key", "value")
except StorageOperationError:
    ...
```

**② `run_main_loop` 无可用主循环时**改为入队并返回 `None`，不再创建临时事件循环——依赖临时循环行为的调用方需改用 `spawn_background`（调度回已注册主循环）。

**③ 容器内 `epsdk restart`** 改为发 `SIGUSR1` 触发进程内软重启，不再终止重拉——容器部署核对 restart 策略（整进程重启交由容器承载）。

**④ 依赖提升**：`tomlclass >=0.4.0,<0.5`。

**⑤ 默认行为变化（2.12.0 / 2.12.1）**：

- 循环连接自愈：命中连接级损坏时自动重建缓存连接（2.12.0）
- 组件发现默认启用、`reload()` / `restart()` 预检收紧（2.11 系列）
- 2.12.1：事件幂等去重键加入平台维度、handler 匹配收口（声明了 `detail_type` 条件的处理器在事件缺失该维度时不再穿透，原生事件路径维持放行）、会话绑定支持 `detail_type:` 前缀键

## 2.12.1（补丁）

无迁移动作。全部为缺陷修复与内部改善。默认行为变化：**日志文件输出默认开启**（`log_dir` 默认 `"logs"`，写 `logs/erispulse.log`，size/date 轮转有界）——不需要文件日志的部署设 `[ErisPulse.logger] log_dir = ""`；显式关闭（从开启切回）会自动清理文件 handler，不会残留写入。

---

## 通用建议

- 升级前读对应版本的 CHANGELOG「注意事项」；补丁版本（x.y.Z）可放心升
- 重要存储写入始终 try/except（语义与版本无关的良好实践）
- 自定义后端 / 深度集成方关注 minor 版本的「变更 / 移除」分类

## 下一步

- 某一变更的行为细节 → [存储后端](../advanced/storage-backends.md) · [配置文件说明](configuration.md)
- 升级后行为不符 → [常见问题](faq.md) · `ep doctor`
- 逐版本完整明细 → [CHANGELOG](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)
