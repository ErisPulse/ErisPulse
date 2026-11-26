# 常见问题（FAQ）

> [!TIP]
> **什么时候需要读这篇**：运行中出现"机器人没反应 / 消息丢失 / database is locked / 内存持续上涨"等现象时，先在这里对照症状找原因与排查路径；没命中再看对应的专题文档。

## 消息与事件

### 群里 @ 机器人，机器人没反应？

按顺序核对：

1. **多账户部署 + `cross_account_policy = "drop"`**：被 @ 的账户副本有 at 点名优待（必定放行），但请确认目标账户的身份口径——绑定表/归属判定用 `self.user_id` 与 `self.account_id` 双口径（见 [跨账户重复受理](../developer-guide/adapters/core-concepts.md)）
2. **`ignore_self`**：发送者 == 接收账户自身时事件被过滤（默认开启），确认不是自己的回声
3. **处理器条件**：`on()` 注册的 `detail_type` / 文本条件是否匹配事件实际字段；事件缺失 `detail_type` 时声明了条件的处理器不再命中
4. **模块休眠/懒加载**：`activate_on` 未触发的模块不会加载（见 [懒加载与休眠](../advanced/lazy-loading.md)）

### 同一条消息机器人回复了两次？

- 多账户同群：两账户各收到一份副本——开 `cross_account_policy`（内容级去重）或配 `session_accounts`（会话精确归属，见 [配置](configuration.md)）
- 同优先级多处理器命中同一事件：各自独立副本并行执行，处理器的 `mark_processed` 才会阻断后续——核对你的处理器注册条件

## 存储与数据库

### `database is locked` 反复出现？

SQLite 的锁互斥只发生在**写与写**之间（WAL 下读写不互斥）。高频触发时按序排查：

1. **长事务**：框架对持锁超过 1s 的事务输出告警并附开启位置（`事务持锁 x.xx s ...`）——按告警把慢操作移出事务块
2. **同步 API 阻塞**：`存储同步 API 在异步上下文调用` 告警指出的调用点迁移为 a 前缀异步方法（`set` → `aset`）——handler 超时同根因同处置，见本条第 1、2 步
3. **写锁排队耐心**：调大 `ErisPulse.storage.sqlite.busy_timeout`（重启生效）
4. 仍无法解决 → 完整排查矩阵见 [存储后端](../advanced/storage-backends.md)

### 升级后写入报 `StorageOperationError`？

2.12.0 起写失败**抛异常而非静默 `False`**——按 [升级迁移指南](migration.md) 改为 try/except。

## 运行时

### 事件 handler 大量超时 / 机器人间歇性没反应？

典型根因：**handler 内调用了同步存储 API**（每次调用阻塞事件循环直到完成）。特征：`存储同步 API 在异步上下文调用` 的限频告警 + handler 超时集中爆发。处置：按告警调用点迁移 `aset` / `aget` / `aExecute`（见 [升级迁移指南](migration.md)）。

### 内存持续上涨怎么办？

1. 开启 `ErisPulse.framework.memory_tracing = true`（排障时开启，常态关闭）——`/metrics` 与内存快照会输出 traced 内存与 top 分配点
2. 观察 GC 周期日志中的快照趋势（`log_snapshot`）；框架的主动 GC 任务按内存增长自动全量回收
3. 热重载重度使用后内存上涨：2.12.1 起卸载链路会解冻回收（旧版本的 `gc.freeze` 盲区已修）——升级框架
4. 模块自身容器无上限增长属于模块责任——归属资源用 owner 上下文登记（见 [归属权系统](../advanced/ownership.md)）

### 热重载后模块"消失了"？

热重载卸载时会取消归属任务、回收归属资源；模块如果在 `on_unload` 之外自行创建任务/线程且未登记归属，框架无法兜底——统一用 `self.spawn()` / `spawn_background(owner=...)` 创建（见 [归属权系统](../advanced/ownership.md)）。

## 配置与部署

### 改了配置没生效？

- **支持热更新**的键（如 `cross_account_policy`、`event_dedupe`、`memory_tracing`、GC 参数）变更即时生效
- **需重启**的键（`storage.use_global_db`、`storage.sqlite.busy_timeout`、router cors/security）变更时框架会输出"需重启进程后生效"告警——看到告警就重启；`storage.backend` 变更同样需重启（当前无告警提示，改完记得重启）
- 编辑中途语法错误：框架保留上次有效配置并输出诊断（不会广播空配置）

### 容器里 `epsdk restart` 容器退出了？

容器内（PID 1）的 restart 已改为发送 `SIGUSR1` 触发进程内软重启——需要此行为请升级到 2.12.0+；整进程重启交给容器 restart 策略。

## 下一步

- 症状未命中 → [存储后端排查矩阵](../advanced/storage-backends.md) · [性能基准与调优](../advanced/performance.md)
- 怀疑框架缺陷 → [Bug 追踪](../bug-tracker.md) · 提交 issue 前先跑 `ep doctor`
- 版本行为差异核对 → [升级迁移指南](migration.md)
