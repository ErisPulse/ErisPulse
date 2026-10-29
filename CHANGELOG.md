# 更新日志

所有版本更新遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范。

> **如何阅读本日志**
> 每个版本分为不同类型的变更部分。建议开发者在升级前先阅读对应版本的 "移除" 和 "变更" 部分。

> **贡献日志**
> 如需为新版本添加日志，请在对应版本号下补充内容，并注明日期和主要贡献者。若同一主题此前已有条目，请直接更新为最终形态，勿追加过程记录（详见下方「写作规范」）。

---

## 规则

### 必须包含的信息
1. **贡献者信息**：每项变更必须标明贡献者，格式为 `@Github用户名`
2. **变更类型**：明确标识变更类型（详见下方分类说明）
3. **日期信息**：版本发布日期采用 `YYYY/MM/DD` 格式

### 写作规范

日志记录的是**发布状态之间的净差异**，而非开发过程：

1. **只记最终形态**：同一版本内对同一主题的多次修改，直接更新既有条目为最终状态，不追加"后期迭代 / 修正 / 不再…"式过程记录
2. **版内修复不单列**：本版本引入又在本版本内修复的缺陷，并入对应特性条目（描述最终行为即可），不单独记录
3. **回退即无痕**：本版本引入又在发布前被回退 / 撤销的功能，不做记录
4. **琐碎不记**：纯测试补充、仓库地址变更、无用户感知的内部微调不记
5. **同主题合并**：同一文件 / 同一模块的多条文档、测试更新合并为一条
6. **摘要从简**：**版本摘要** 不超过 2 句话，只说清"本版本是什么主题、最重磅的 1–3 项变更"；**升级建议** / **注意事项** 同样只给结论与行动项，不复述正文
7. **条目一行一条**：变更分类条目压缩为一行结论（模块/领域 + 干了什么），同一模块/同主题的多条合并；子弹点嵌套最多一层；不粘贴 API 签名、配置键、参数列表或实现细节（这些属于文档）；dev 条目可比正式条目更简，正式条目是 dev 的净差异总结，两者不重复展开

### 变更类型分类

| 类型 | 英文标签 | 说明 | 示例 |
|------|---------|------|------|
| 新增 | Added | 新功能、新API、新模块等 | 新增命令系统支持 |
| 优化 | Improved | 性能提升、用户体验改进、代码优化 | 优化内存使用效率 |
| 变更 | Changed | 功能行为变更、配置变更、API变更（非破坏性） | 调整默认配置项 |
| 修复 | Fixed | Bug修复 | 修复空指针异常 |
| 移除 | Removed | 删除的功能、API或模块 | 移除废弃的API |
| 废弃 | Deprecated | 标记为弃用的功能（计划未来移除） | 某方法即将废弃 |
| 重构 | Refactored | 内部代码重构（不影响公共API） | 重构加载系统架构 |
| 安全 | Security | 安全修复或增强 | 修复权限漏洞 |

### 示例格式

```markdown
  ## [version] - 2025/08/20
  > 正式发布

  **版本摘要**
  用至多 2 句话概括本版本主题与最重磅变更，不罗列子功能细节（细节写在下方变更分类）。

  **升级建议**
  - 是否建议升级：建议升级 / 可选升级 / 跳过升级
  - 升级原因和理由

  **注意事项**
  - 从低版本升级时需要注意的重要事项
  - 弃用功能说明
  - 兼容性变更说明

  ### 新增

  - @用户名
    - `模块名` 模块新增功能描述（一行一条，结论式；同模块多条合并为一条）

  ### 优化

  - @用户名
    - 优化某模块的性能
```

---

## [2.11.1-dev.1] - 2026/10/27
> 开发版

**版本摘要**
本版本为 2.11.1 正式发布前的加固批次：修复热重载体系四项契约缺陷（相对路径下插件删除事件失效、导入失败误判为删除、restart 预检拒绝未闭环、新插件热装载绕过互斥），完成背压告警折叠、收件箱迁移重试、回滚留痕等全线健壮性收口

**升级建议**
- **是否建议升级**：建议升级
- 相对 dev.0 为纯修复与加固，无 API 破坏性变更

### 新增

- @YingXinche
  - 文档：生态模块新增 ApiMCP MCP 桥专页与 QvQChat 配套插件（Stalker/Memes/Companion）区块；新增「选型指南」目录（vs NoneBot2、vs AstrBot/LangBot 对比与 AstrBot 迁移指南）；README 增补 QvQChat/ApiMCP/Cron/Takumi 生态位、Star 引导与爱发电赞助入口（FUNDING）

### 修复

- @YingXinche
  - 任务工厂 `_owner_aware_task_factory` 显式回传 `loop`：修复 Python 3.14 下 `Task(loop=None, eager_start=True)` 触发 `'NoneType' object has no attribute 'is_running'`，导致 `sdk.run()` 启动后所有经 `sdk.client` 的 HTTP/WS 请求失败（aiohttp 3.14.x 请求路径必经此工厂）(#472)
  - 文件监控删除检测的键与前缀统一绝对化归一：相对路径调度（默认 `plugins` / `epsdk run --reload` 的 `.`）下删除/改名插件事件恢复触发
  - 插件导入期失败不再误判为「已删除」（模块/适配器两侧）：按重载失败回滚旧实例并返回失败，不再静默移除后误报成功
  - `restart()` 预检整轮拒绝闭环：适配器层跳过本轮重载（消除无谓断连抖动）、整轮判定失败并留痕，修复后再次 restart 即可
  - 新插件热装载（on_created）进入热重载互斥：消除与进行中 restart/reload 的注册表交叉
  - 单模块重载的意外异常同样触发快照回滚；重载回滚各步骤失败分级留痕（原静默吞异常）
  - restart 请求落在普通重载持锁期间同样合并排队（至多补跑一轮完整 restart）
  - 去抖定时器 start 竞态：并发停止监控时 watcher 线程不再偶发 AttributeError
  - `module.unload()` / `adapter.unload()` 公共入口纳入热重载互斥（限时等待，超时降级直接执行并留痕）：外部卸载不再与进行中的重载交叉导致双重 `on_unload` / 双重 shutdown

### 优化

- @YingXinche
  - 事件背压丢弃告警按窗口折叠（默认 5 秒一条、计数照常累计，兑现 `HANDLER_QUEUE_OVERFLOW_WARN_INTERVAL_SECS` 语义）
  - 单文件插件 mtime 导入缓存：任一插件变更触发的重发现不再重复执行全部无关插件的模块级代码
  - 会话收件箱：列迁移失败自动重试（不再误置就绪后写入静默失败）、建表/落盘失败告警升级 warning、出站 meta 改显式白名单键入库
  - `PollingAdapter` 批内单条上报失败隔离（单条异常不再丢弃余批）
  - `spawn_client_loop` 空 platform 时回退 owner 上下文兜底（空 owner 任务不再无人回收）
  - 文件监控停止 join 改有限超时（不再阻塞事件循环一个轮询周期）；预检与监控日志全面 i18n 化（五语言）
  - 配置 schema 透传满血组件扩展元数据（`min/max/step/rows/show_if/disabled_if/value_type/item`，供 Dashboard 2.4.0+ 组件系统消费；旧面板自动忽略）

### 变更

- @YingXinche
  - CLI：`uv add` 与自更新脚本引导探测补子进程超时兜底（对齐既有标准）；`epsdk doctor --fix` 清理配置前自动备份 `config/config.toml.bak`

---

## [2.11.1-dev.0] - 2026/10/23
> 开发版

**版本摘要**
本版本为热重载体系的收口补丁：编排互斥与风暴合并、预检/字节码清理覆盖全部路径、休眠闭环、插件热发现与适配器装完即用；同期清零 Windows 编码、CLI 子进程挂死、历史配置污染三类老问题，并补齐 Core i18n 未翻译键。

**升级建议**
- **是否建议升级**：建议升级
- 无 API 破坏性变更；`reload()`/`restart()` 行为收紧（互斥与合并）对正常使用透明

**注意事项**
- 热重载/重启/归眠操作全程互斥：连续保存改为「完成中合并、完成后至多补跑一轮」；单模块重载不再强制激活懒加载模块
- `restart()` 前置整体语法预检：任一模块源码有语法错误即整轮拒绝、全部旧实例继续服务
- `epsdk run --reload` 默认忽略 `.venv`/`.git` 等目录（`ErisPulse.framework.watch_ignore_dirs` 可配置）；内联模式改「监督进程 + 重载 worker」，硬重启自动重拉
- 运行中 pip 安装的适配器在 `restart()` 即被发现并拉起；`hard_restart()` 适用场景收窄为「框架自身更新与结构性配置变更」

### 新增

- @YingXinche
  - `runtime/reload_ops.py` 热重载互斥协调器：reload/restart/归眠全程互斥，restart 风暴合并（dirty 补跑）、钩子内重入直通不死锁
  - `restart()` 适配器重发现：运行中新装/卸载适配器即刻生效（装完即用），新平台按启用状态自动拉起
  - 本地插件热发现：新增/删除/改名插件文件自动装载/移除；插件目录中的适配器文件保存即触发 `sdk.adapter.reload`
  - `sdk.hard_restart(reason)` 支持可选原因参数，监督者重拉时展示；`runtime/process_state.py` 提供跨进程硬重启标记契约
  - `epsdk doctor` 历史配置污染体检 + `--fix` 一键清理（影子状态残留 / 游离配置节，tomlclass 无损路径）
  - `ErisPulse.framework.watch_ignore_dirs` / `watch_include_plugin_dirs` 框架配置键（文件监控忽略清单可配置）
  - CLI 子进程超时兜底：pip 探测 / ensurepip / venv 创建全部带超时，超时输出代理/镜像诊断提示
  - epsdk ↔ uv 联动：uv 项目内安装/升级/卸载写入 pyproject + uv.lock（免疫 uv sync 清理）；解释器解析感知 `UV_PROJECT_ENVIRONMENT` / `UV_PYTHON`；doctor 输出环境决策链与 uv 项目面板；`--user` 等 uv 不支持的参数直接走 pip
  - `.erispulse/` 运行状态目录启动时自动生成 `.gitignore`（排除本目录，与配置目录同款）
  - `epsdk install` / `upgrade` 完成后按运行实例状态三态提示生效方式（运行中热重载模式 / 运行中普通模式 / 未运行）
  - 事件洪峰入队背压：待处理处理器任务数上限（`ErisPulse.framework.handler_queue_max_pending`，默认 4096，0 = 不限），超限丢弃并告警——常驻进程内存兜底
  - `BaseAdapter.emit_event()` 事件上报便捷方法（与 `emit_meta` 对称，自动补 platform 字段）
  - 适配器通信模式半成品基类：`PollingAdapter`（HTTP 轮询，指数退避循环基类管理）与 `WebhookAdapter`（HTTP 回调，接收路由 owner 归属自动清理），子类只实现 fetch/convert 钩子
  - `epsdk create adapter --template {ws-server,polling,webhook}` 三模式脚手架（默认 ws-server 保持现行为）
  - `examples/` 新增轮询 / 回调模式适配器示例（`example-adapter-polling` / `example-adapter-webhook`）
  - `BaseModule.state` 模块级持久化状态 KV（自动带 `module.state.<模块名>.` 前缀，卸载重载后仍在）
  - `BaseAdapter.spawn_client_loop()` 客户端连接循环调度（任务按平台归属，shutdown 自动取消）
  - `explain_trace` 链路聚合排查（trace-id 串联的事件处理链路汇总）
  - SendDSL 调用不存在方法时的错误提示附可用方法列表（`list_sends()` 指路牌）
  - 会话收件箱 `recent()` 支持按会话键过滤（服务端过滤，消除多群部署下的全局拉取 + 客户端逐条比对）（#468）
  - 出站消息归属：`message.sent`/`message.sending` 载荷与收件箱出站记录携带发送模块（处理器分发期自动按注册归属注入 owner）（#469）

### 优化

- @YingXinche
  - 内存日志存储换 `__slots__` 记录类（单条约 -70% 占用）；`memory_limit = 0` 可整体关闭内存副本；新增全局总条数上限 `ErisPulse.logger.total_memory_limit`；模块卸载同步清理其内存日志
  - i18n 五语言表懒加载（启动只载当前 + 英文兜底，切换语言时按需加载）；补齐 Core i18n 此前未翻译的 44 键（命令冷却/用法/弃用等用户可见提示 ×4 语言）
  - 日志调用者归因热路径 O(1) 化（`frame.f_globals` 取模块名，替代 `inspect.getmodule` 帧遍历）
  - SendDSL 发送方法包装改实例级缓存（同名方法重复访问不再重建闭包，规则变更自动失效）
  - 命令治理状态表的锁清扫改两轮复核（高并发期漏删的锁不再滞留）

### 变更

- @YingXinche
  - `reload_all()` / `restart()` 前置汇总式语法预检（GBK 等非 UTF-8 源码一并拦截），预检失败整轮拒绝
  - 单模块重载不再强制激活懒加载模块（保持重载前活性）；重载后归眠/唤醒闭环完整，`module.reload` 载荷新增 `was_loaded` / `still_loaded`
  - 插件路径热重载清理 `__pycache__` 字节码缓存，「同秒同字节数假重载」在全路径消灭
  - `epsdk run --reload` 改「监督进程 + 重载 worker」结构：硬重启自动重拉、崩溃退避与 Ctrl+C 收尾与非 reload 模式统一
  - 文件监控去抖由「窗口内丢弃」改为「合并后补发」；`--reload` 默认忽略 `.venv`/`.git` 等目录并把插件目录移交插件 watcher

### 修复

- @YingXinche
  - 并发 restart / restart×reload 交叉导致的注册状态错乱与双重 `on_unload`；清扫器归眠与重载竞态
  - `plugins` / `plugins2` 前缀重叠目录互相误判删除事件；watcher 回调异常杀死轮询线程
  - 无事件循环时启用插件热重载「假成功」（主循环注册表延迟解析）；Windows GBK 控制台偶发 `UnicodeEncodeError`（CLI 入口标准流统一 UTF-8 + 子进程注入 `PYTHONIOENCODING`）
  - `epsdk create adapter` 脚手架模板的适配器在收到首条消息即 AttributeError（模板引用不存在的 `self.adapter.emit`——已改用 `emit_event()`）
  - 会话收件箱查询接口丢失消息归因：`get()` / `get_by_trace()` / `event.history()` 未透传 `sender`，入站记录不归档事件时刻元数据——新增 `meta` 列（白名单：昵称/self_id/子类型/消息 id，旧表自动迁移），三个查询接口统一返回 `sender` + `meta`（#467）
  - 入站 bot 自发消息回声被记为 user 污染收件箱归因（OneBot `report-self-message` 等）：按 `self.user_id == user_id` 识别回声，`ErisPulse.transcript.self_echo` 三模式处理（默认记为 bot 并标记 `meta.self_echo`；非回显平台零影响）（#470）

### 重构

- @YingXinche
  - SDK 版本闸门统一为单一实现（strict_mode 错误面与组件安装来源解耦）
  - Kernel 组合根收尾：`Initializer` 缺省构造委托 `Kernel.build_loaders()`，消除游离 StrictModeManager
  - 删除 `BaseLoader` 死接口（`load()` / `_register_config` / `_get_config_status`，零调用方）
  - `scripts/tools` 包化为统一 CLI（`python -m scripts.tools <check|gen|translate> ...`），CI 调用点同步；AI 提示词与技能库的文档清单集中到 `generators/spec.py` 单一规格源
  - 翻译器自动清理源文档删除后的各语言残留译文与缓存；超出输出预算的大块自动二次拆分（大文档翻译不再截断失败），并修复 auto-translate 统一入口的收尾崩溃；AI 提示词的人设清单精简为接地前导

### 移除

- @YingXinche
  - 文档：《模块排查指南》（`developer-guide/module-troubleshooting.md`）——症状级排查内容并入各功能文档的排障小节，独立指南页不再维护

---

## [2.11.0] - 2026/10/22
> 正式发布

**版本摘要**
本版本交付完整的热重载体系：热重载默认全量语义（卸载前语法预检、代码身份核对、依赖级联重导）、懒加载休眠（`dormant_after`）与适配器代码级热重载（`sdk.adapter.reload`），`.got()` 命令流语法糖与 `epsdk stop` / `restart` 补齐运行时控制；同期完成全库工程治理（公共 API 契约标注清零、失败路径留痕、四道工程棘轮闸门进 CI）与全库文档规范改造，多语言翻译产物改由 `docs-generated` 持久分支发布。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：常规模块零改动即可受益；仅依赖旧「reload() 默认轻量」行为的调用方需显式传 `full=False`；第三方适配器/模块无需为工程治理批次做任何改动

**注意事项**
- `reload()` 默认翻转为全量重载；懒加载失败冷却 30 秒可重试、`dormant_after` 归眠期间不接收事件（`activate_on` 除外）
- `set_sdk_ref` 死接口移除（SDK 引用懒解析根单例）
- 实例锁迁移至 `.erispulse/config.lock`（首次启动自动清旧锁）；配置目录自带 `.gitignore`
- `sdk.restart()` 语义变为组件级热重载；框架自更新与 entry-point 增删场景请使用 `hard_restart()`
- 多语言文档/翻译缓存/AI 提示词等生成产物改由 `docs-generated` 分支 + workflow artifact 发布，开发分支不再提交；`styleguide/` 退出 AI 提示词包


---

## [2.11.0-dev.0] - 2026/10/20
> 开发版

**版本摘要**
本版本交付热重载体系的核心能力：热重载默认全量语义（卸载前语法预检、代码身份核对、依赖级联重导），新增懒加载休眠（`dormant_after` 闲置归眠、访问透明唤醒）与适配器代码级热重载（`sdk.adapter.reload`），加载失败现场可经 `module.last_error()` 直接查询。

**升级建议**
- **是否建议升级**：可选升级
- 升级原因：常规模块零改动即可受益；仅依赖旧「默认轻量重载」行为的调用方需显式传 `reload(name, full=False)`

**注意事项**
- `reload()` / `reload_module()` 默认翻转为全量重载（清理顶层包 import 缓存并级联重导依赖者代码）；`module.reload` 事件 payload 的 `full` 语义变为「本次是否全量」
- 懒加载初始化失败由「永久失效」改为冷却 30 秒后可重试；声明 `dormant_after` 的模块归眠期间不接收事件（`activate_on` 除外），未声明则行为不变
- 下游展示组件（Dashboard 等）可跟进 `get_info()` 新增的 `running_identity` / `stale` 字段与 `module.before_unload` / `module.sleep` 事件

### 变更

- @YingXinche
  - `sdk.restart()` 语义升级为组件级热重载：全部模块走统一热重载管线（预检/快照回滚/身份核对）、适配器逐个代码级重载，框架进程/路由/配置监听保持在线；框架自更新与 entry-point 增删场景用 `hard_restart()`
  - 实例锁迁移至 `.erispulse/config.lock`（与运行状态文件同居，首次启动自动清旧锁）；配置目录自带 `.gitignore`
  - 移除死接口 `set_sdk_ref`：管理器 SDK 引用懒解析根单例（该接口自 2.5 起从未被生产链路调用）
  - 全库公共方法契约标注补齐（约 160 处归零）；`styleguide/` 退出 AI 提示词包；翻译 CI 收敛性修复（缓存 key 唯一化 + 时间预算调整）

### 新增

- @YingXinche
  - 卸载前语法预检：失败即拒绝卸载、旧实例继续服务（语法错误不再进入半死状态，日志给出文件 + 行号）
  - 运行时注册模块纳入热重载（重载快照登记 + `top_level` 推导）；加载失败可观测（`last_error()` 返回异常 + traceback + 时间戳，`get_info()` 新增 `running_identity` / `stale` 字段）
  - 卸载前钩子 `on_before_unload(event)` 与 `module.before_unload` 生命周期事件
  - 懒加载休眠：`dormant_after` 闲置自动归眠（释放运行时资源、保留懒代理与注册存根），访问透明唤醒；`sdk.module.sleep()` 手动归眠，配套 `module.sleep` 事件
  - 命令多轮流控语法糖 `.got()`：流式声明收集步骤、值按参数名注入，检查点续跑、解析失败自动重发
  - 适配器代码级热重载 `sdk.adapter.reload(平台名)`（本地插件与 PyPI 包均支持）：预检 → 清理 → 重导 → 重注册 → 原运行态拉起，失败自动回滚，配套 `adapter.reload` 事件
  - CLI 运行时控制 `epsdk stop` / `epsdk restart`：`runtime.json` 登记监督与框架进程 PID，优雅终止与按原参数重启

### 修复

- @YingXinche
  - `module.disable()` 补发 `module.unload` 事件（依赖者收到 `on_dependency_lost`）；`dump_state()` router 段字段与实现对齐
  - 适配器停止/重启的资源回收统一走归属权管线（五类注册资源不再随 restart 累积残留）
  - 失败路径留痕补齐（会话收件箱写失败、退出前配置刷盘失败、路由安全配置失败等升级为 warning）；散落超时/轮询参数收拢为命名常量

---

## [2.10.2] - 2026/10/18
> 正式发布

**版本摘要**
本版本补齐适配器本地开发回路：适配器可放入 `plugins/` 免打包开发（`epsdk create adapter --local`），`epsdk create pack` 一键转换为可发布项目；配置写入引擎替换为零依赖无损引擎 tomlclass（读写提速约一个数量级、CRLF 首次全链路保真），CLI 交付 `init --adapter` / `doctor --fix` / `run` 启动前自检与分组主帮助。

**升级建议**
- **是否建议升级**：可选升级
- 升级原因：本地适配器开发工作流改进；配置引擎替换对注释/顺序保留语义零变化

**注意事项**
- 本地插件目录适配器与同名 PyPI 包**本地优先**；转换发布后请移除 `plugins/` 原件
- 适配器放入插件目录即自动加载；代码级热重载将在 2.11 提供，当前改代码需重启
- 配置写入引擎切换为 tomlclass（新增依赖、移除 tomlkit 直接依赖）
- 嵌套 dataclass 声明配置的存量错位（BUG-046）不自动迁移，需手动挪回组件节

---

## [2.10.2-dev.0] - 2026/10/14
> 开发版

**版本摘要**
本版本补齐适配器本地开发回路（`plugins/` 免打包 + `epsdk create pack` 转发布），配置写入引擎整体替换为 tomlclass，根路由/错误页更新为亮暗双主题，CLI 交付 `init --adapter` / `doctor --fix` / `run` 启动前自检与分组主帮助。

**升级建议**
- **是否建议升级**：可选升级
- 升级原因：本地适配器开发工作流改进；配置引擎替换对注释/顺序保留语义零变化

**注意事项**
- 本地插件目录适配器与同名 PyPI 包**本地优先**；转换发布后请移除 `plugins/` 原件
- 适配器放入插件目录即自动加载（与 entry-point 同等待遇）；代码级热重载将在 2.11 提供，当前改代码需重启
- 配置写入引擎切换为 tomlclass（新增依赖、移除 tomlkit 直接依赖）；不可序列化键不再残留空表壳
- 嵌套 dataclass 声明配置的存量错位（BUG-046）不自动迁移，需手动挪回组件节

### 新增

- @YingXinche
  - 适配器本地插件目录支持：`plugins/` 自动发现注册（与 entry-point 同等待遇）；`epsdk create adapter --local` 生成、`epsdk create pack` 转换为可发布项目
  - 配置诊断注释回读：`validate_config` 校验失败消息附带字段注释原文，`ep doctor` 同步展示
  - `epsdk init --adapter` 免交互预装适配器；`epsdk doctor --fix` 自动修复（补建 config.toml、拉起配置向导补必填项）
  - `epsdk run` 启动前自检（对接 strict_mode，`--strict` 临时开启）；主帮助按类别分组渲染（Rich 表格）
  - `sdk.module.services()` 服务条目新增 `parameters` 字段（声明 + docstring 按参数合并）

### 修复

- @YingXinche
  - 修复声明式配置嵌套子表锚定漂移（BUG-046，模板与 full.example 两处）；修复服务目录漏懒加载模块（BUG-047）

### 文档

- @YingXinche
  - 适配器「本地开发（免打包）」章节、CLI 参考、uv tool 分离部署指南与示例 README 同步

### 变更

- @YingXinche
  - 配置写入引擎 tomlkit → tomlclass（零依赖无损 TOML 编辑引擎）：注释/键顺序/空行保留语义不变、未触碰内容逐字节保真、读盘字节模式 CRLF 保真，读写性能提升约一个数量级
  - 根路由页与错误页视觉更新（亮暗双主题，跟随系统深色模式）

---

## [2.10.1] - 2026/10/13
> 正式发布

**版本摘要**
本版本为命令与消息处理链路的健壮性维护：集中修复多段消息参数丢失、「先 @ 后命令」不可达、命令被拒重复回复与权限函数副作用双触发、交互等待被命令消息重入消费、`select` 同键多路互踢等深层缺陷；统一 mention 语义并补齐无 `alt_message` 适配器的文本回退。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：纯缺陷修复，无破坏性变更；仅依赖下述旧行为的组件需核对

**注意事项**
- 命令分发文本改为全部 text 段按序拼接（修复性变更，尾部参数不再丢失）；多前缀最长优先、前缀匹配容忍前导空白
- `BaseConverter.at()` 产出修正为 OB12 规范 `mention` 段（依赖旧 `at` 形态的适配器请同步）
- 会话级等待键并入 `detail_type`（进程内等待，无迁移）；`overrides` 对 message 事件空文本改为不命中
- 测试会话配置隔离升级为干净替换（维护者本机历史测试残留可顺手清理）

### 修复

- @YingXinche
  - 退出健壮性：uninit 链与测试收尾显式确定性关停常驻线程（新增 `ConfigManager.stop_all_watchers()`），消除退出期噪音与挂死

### 文档

- @YingXinche
  - 文档站阅读路径翻新：首页「不必全读」声明 + L1 核心五篇最小必读集 + 30 篇「什么时候需要读这篇」判读框

---

## [2.10.1-dev.0] - 2026/10/13
> 开发版（预发布）

### 变更

- @YingXinche
  - `uvicorn` 锁定 `>=0.35.0,<1.0` 并按能力探测使用 `Server._serve()`（缺失时仅告警并回退公开 `serve()`，不硬失败）

### 修复

- @YingXinche
  - 测试基建：会话级配置隔离升级为「备份/干净替换/还原」，历史测试写入不再污染并跨运行自我延续
  - 命令分发链路：多 text 段丢失、畸形段防御、拒绝路径重跑（重复回复 / 权限函数副作用双触发）、交互重入（新 `wait_reply` 不再被触发消息消费）、前缀健壮化（最长匹配 + 前导空白容忍 + user_id 归一）
  - `select()` 改聚合等待（同键多路不再互踢）；交互原语文本统一 `alt_message` 优先 + 段回退口径（无 alt 适配器不再永久超时）
  - 事件条件逐 handler 异常隔离（坏模块条件函数不再拖死分发链）；`at()` 修正为 OB12 `mention` 段
  - `get_text()` 无 `alt_message` 时回退 text 段拼接；`MessageBuilder.build()` 深拷贝等边界加固
  - 退出健壮性：uninit 链显式确定性关停常驻线程（新增 `ConfigManager.stop_all_watchers()`）；文档阅读路径翻新（「不必全读」+ L1 核心五篇）

---

## [2.10.0] - 2026/10/11
> 正式发布

**版本摘要**
本版本把「连接」升级为框架级一等资源：统一连接注册表（`ErisPulse.connections`）自动登记服务端 WS/SSE 与客户端出站连接，支持广播、业务分组、跨模块传递/复用与卸载自动回收；同期交付根导入契约、路由单参注册与 HTTP 元组响应约定、归属权体系补全与会话收件箱保留策略运行时覆盖。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：全部为增量能力，深路径导入永久兼容；受「卸载关闭归属连接」影响的下游组件（如旧版 Dashboard 推送）建议同步适配

**注意事项**
- 模块卸载/适配器停止会关闭并注销其名下全部连接（含日志订阅与对话恢复工厂）——杜绝泄漏的预期行为，依赖旧行为的组件需知悉
- 放开 transcript 保留策略会让表随消息量无限增长，操作前阅读风险专节
- 路由路径（含模块名前缀）大小写敏感
- `epsdk init` / `create` 生成物切换根导入写法，`min_sdk_version` 与依赖下限自本版起为 `2.10.0`；模块模板不再生成模块级 `enabled` 开关（启停由框架统一管理）

---

## [2.10.0-dev.1] - 2026/10/10
> 开发版（预发布）

**版本摘要**
脚手架与文档修正批次：模块模板移除模块级 `enabled` 配置开关（启停由框架统一管理），路由文档补充路径大小写敏感说明。

**升级建议**
- **是否建议升级**：可选升级
- 升级原因：纯模板与文档变更，不影响运行时行为

### 优化

- @YingXinche
  - `docs/advanced/router.md` 补充路由路径（含模块名前缀）大小写敏感说明

### 移除

- @YingXinche
  - `epsdk init` / `create` 模块模板移除 `enabled` 配置字段与配套翻译键：模块启停由框架统一管理，`ConfigClass` 只承载业务参数

---

## [2.10.0-dev.0] - 2026/10/09
> 开发版（预发布）

**版本摘要**
本版本把「连接」升级为框架级一等资源：统一连接注册表（`ErisPulse.connections`）自动登记与回收连接，支持广播、业务分组、跨模块传递/复用；同期交付根导入契约、路由单参注册与 HTTP 元组响应约定、归属权体系补全与 transcript 保留策略运行时覆盖。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：全部为增量能力，深路径导入永久兼容

**注意事项**
- 模块卸载/适配器停止会关闭并注销其名下全部连接（含日志订阅与对话恢复工厂）——杜绝泄漏的预期行为，依赖旧行为的组件需知悉
- 放开 transcript 保留策略会让表随消息量无限增长（磁盘/下游内存风险），操作前阅读 `docs/advanced/transcript.md` 风险专节
- `epsdk init` / `create` 生成物切换根导入写法（`from ErisPulse.Core.*` 深路径不受影响）

### 新增

- @YingXinche
  - `Core/connections` 连接注册表：服务端 WS/SSE 与客户端出站连接自动登记（`track=False` 可退出）、广播（`BroadcastResult` 成败明细）、业务分组（`join_group` / `assign` / `dismiss`）、跨模块传递/复用（`close` 仅 owner 可调）、`list()` / `stats()` 查询与归属审计计数；配套异常族与生命周期事件
  - `runtime` 调度工具：`run_main_loop()` 跨线程安全投递主循环、`spawn_later()` / `spawn_thread()` 归属化延迟调度与线程启动
  - 根导入契约：管理器单例/类、类型、错误全族、ORM、Schema、事件处理器与运行时工具全部可 `from ErisPulse import ...`
  - 路由注册单参形态（`@router.get("/path")` 命名空间自动归属当前模块）；HTTP 元组响应约定与 `respond()` 帮助函数
  - `transcript` 保留策略运行时覆盖（`set_retention` / `get_retention` / `reset_retention`，覆盖优先于配置、重启失效）
  - 归属权补全：日志订阅（`logger.handler`）、对话恢复工厂纳入 owner 治理与卸载注销；`i18n.register` 的 `domain` 缺省自动取当前归属 owner

### 优化

- @YingXinche
  - `ownership.reclaim` 回收链新增归属连接关闭步骤，卸载/停止/半卸载三条路径统一生效

---

## [2.9.0] - 2026/10/08
> 正式发布

**版本摘要**
本版本交付 2.9「模块开发体验」主线（EPRFC-2026-001）全部方向：命令声明式参数与治理、统一依赖注入、中间件否决权、内置 ORM、热重载完备与影子模块灰度转正、排查诊断、配置环境变量绑定等（均为增量能力，现有模块零适配）；同期重造事件分发热路径（吞吐/延迟提升 3~9 倍），正式支持 Python 3.14。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：新能力全部为声明式增量，无破坏性配置/数据变更；高消息量部署的分发吞吐与发送延迟显著受益

**注意事项**
- `scope` 的 `persist=False` 修复为严格不落盘：此前误写入用户 config.toml 的残留值与影子模块状态记录（`ErisPulse.modules.status.<影子owner>=False`）需手工清理
- `epsdk init` / `create` 生成物的 `min_sdk_version` 与依赖下限自本版起为 `2.9.0`
- Python 3.14 正式支持（3.14t free-threaded 保持实验性监测）

### 修复

- @YingXinche
  - 修复包形式插件的导入路径相对条目导致切换工作目录后插件导入静默 `ModuleNotFoundError`（`sys.path` 改绝对路径写入）

---

## [2.9.0-dev.3] - 2026/10/05
> 开发版（预发布）

**版本摘要**
性能与健壮性双主线：事件分发与消息链路吞吐/延迟提升 3~9 倍，transcript 改内存缓冲批量落盘，i18n 解析缓存与热路径日志守卫消除每次调用文件 IO；同期完成发布前健壮性批次（静默吞异常补留痕、影子异常族入层级、CLI 文案 i18n）。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：无破坏性配置/数据变更；高消息量部署的分发吞吐、存储读路径（+41%）与发送延迟（-32%）显著受益。已捕获影子模块 `RuntimeError`/`ValueError` 的代码需按注意事项调整

**注意事项**
- transcript 改「内存缓冲 + 至多 1 秒批量落盘」：正常退出强制刷盘，硬崩溃/强杀时最近约 1 秒会话记录可能丢失（不适合审计级持久化）
- `setConfig` 延迟写入改常驻 watcher 线程统一调度 + 失败退避重试（对外配置语义与事件时序不变）
- 影子模块 API 异常定形：`RuntimeError`/`ValueError` 改为 `ShadowStateError` / `ShadowSourceError` / `ShadowPromoteError`（挂 `ErisPulseError` 层级并聚合导出），针对性 `except` 需同步
- 脚手架生成物文案跟随界面语言；模板 `min_sdk_version` 与依赖下限升至 2.9.0

### 新增

- @YingXinche
  - 影子模块异常族挂入 `ErisPulseError` 层级并聚合导出；`shadow_manager` 等补齐 `Core` 聚合导出

### 优化

- @YingXinche
  - transcript 写入路径重造（内存缓冲 + 批量落盘 + uninit/atexit 刷盘兜底 + 配置节缓存）；i18n 生效语言解析缓存；`should_log()` 热路径日志守卫（级别关闭时跳过格式化与翻译）；事件匹配闭包注册期预编译
  - 配置延迟写入调度重造（常驻线程 + 失败退避重试）；排查诊断与 CLI 残留硬编码文案 i18n 化；行为参数收编 `Core/constants.py`（公共常量 `__all__` 补齐 + 导出完整性守护测试）
  - 脚手架模板同步（`args=` 示例命令、模板收口常量）

### 修复

- @YingXinche
  - 修复会话检查点 GC 周期任务「永生」（裸 `create_task` 无归属无取消路径，uninit 后残留）
  - 修复约 20 处静默吞异常无留痕（配置热更新订阅失败、检查点恢复/GC 失败、归属权 reclaim 单步失败等），按语义记录日志

---

## [2.9.0-dev.2] - 2026/10/03
> 开发版（预发布）

**版本摘要**
2.9 主线健壮性打磨版：模块热重载补全（`reload_module(full=True)` 全量重载 + `reload_all_modules()`），修复 `args=` 回填失效、scope `persist=False` 落盘（BUG-038）、配额并发丢失等缺陷，CLI 体验补齐（`--yes` 接线、doctor 配置健康检查）。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：dev.0 的命令治理/影子模块/归属权审计存在已确认缺陷；存量用户受益于 scope 持久化语义修复（BUG-038）

**注意事项**
- `reload_module()` 新增可选 `full` 参数（默认 `False`，不声明时行为不变）
- `scope` 的 `persist=False` 修复为严格不落盘：此前误写入用户 config.toml 的残留值不会自动清理，请手工删除
- 修复前启动过影子模块的部署可能残留 `ErisPulse.modules.status.<影子owner>=False`（真实插件重名会被误禁用），建议顺手清理

### 新增

- @YingXinche
  - 模块热重载补全：`full=True` 全量重载（叠加旧模块对象顶层包名清理 import 缓存 + PyPI 依赖者级联重导，元数据缺失的「假重载」盲区消除）；`sdk.reload_all_modules()` 按拓扑序一次重载全部（单模块失败隔离）
  - CLI 体验：全局 `--yes/-y` 接线（非 TTY 明确报错）、`doctor` 组件配置健康检查、`run` 连续崩溃排查指引、install/upgrade 后生效方式提示、`list` 适配器启用状态列
  - 配置 CRUD 补齐：`getAllConfig()` 全量快照与 `delConfig()` 点路径键删除（复用 `config.set` 事件，监听方零改动）
  - 适配器元信息公开读取 API（`get_meta` / `get_info`，第三方无需绕道 sys.modules）；路由 `reload()` 运行时热重载 host/port/SSL（失败以旧配置恢复服务）
  - 一键安装脚本新增 uv tool 全局安装方式；Docker 模式时区交互与 compose 持久化挂载优化
  - 媒体发送协议标准（§2.1：URL/路径/bytes 必须支持、平台限制声明义务与降级阶梯）；新增 i18n 一致性 / 文档链接 / MySQL+PostgreSQL 双后端 CI 门禁
  - 发布版本一致性校验；CI 质量门禁正式阻塞（ruff + basedpyright 0 error）、集成测试常驻 job

### 优化

- @YingXinche
  - API 参考文档渲染整体修复（doctest 前缀剥离、类型反引号误标、代码块指令转换、签名补全），CI 文档更新链路恢复生效

### 修复

- @YingXinche
  - 修复 `setConfig` 置 `None` 导致整次 flush 失败无限重试（单键不可序列化仅丢弃该键并告警）；MySQL extra 补 `cryptography` 依赖
  - 修复 `args=` 可选条目缺默认值时注入 `None` 覆盖处理器自身默认值
  - 修复 scope `persist=False` 落盘与 `delete(persist=True)` 语义（持久化基线承接）、`cache_size` 配置不生效
  - 修复 `Depends.module` dict/list 参数缓存键不可哈希抛错；`usage_limit=` 配额并发丢失更新（按键互斥锁）
  - 治理与节流状态表容量上限与机会式清扫（7x24 常驻无界增长）；防抖不再取消正在执行的业务处理器
  - 影子模块事件隔离改深拷贝、影子命令分流失败不再静默转真实注册；影子状态写入收窄与实例属性残留清理
  - ORM 修复一批：子类静默共享父表、PostgreSQL 长索引名建索引失败、默认值列插入后实例不一致、跨循环连接池滞留、INSERT 默认值客户端应用等
  - 修复三处被 `try/except` 吞掉的运行时导入层级错误（归属任务取消、事件覆写热更新订阅、影子路由误挂载——三者此前从未生效）
  - 修复配置整节写与点分写并存的读写不一致（BUG-039，统一特异性优先语义）；配置迁移按文件位置锚定（不再依赖 CWD）
  - 修复 uv 新版安装位置误报失败等一键安装脚本一批问题；`workers/get-erispulse` 分发服务加固（上游故障回落兜底缓存、HEAD 500 等）

## [2.9.0-dev.0] - 2026/09/25
> 开发版（预发布）

**版本摘要**
本版本开启 2.9「模块开发体验」主线（EPRFC-2026-001）：命令声明式参数与选项（`args=` / `options=`）、统一依赖注入（`Depends`）、中间件事件否决权、命令治理声明化（cooldown / rate_limit / usage_limit / deprecated）、节流防抖、内置 ORM、分发决策链追踪与排查诊断、配置环境变量绑定、热重载快照回滚与影子模块灰度转正——均为增量能力，现有模块零适配。

**升级建议**
- **是否建议升级**：建议升级
- 升级原因：纯新增能力（不声明即原行为），零适配成本

**注意事项**
- `args=` 声明语法：`<count:int>` 必填、`[sides:int=6]` 可选，支持 str/int/float/bool/literal/duration/rest 七种类型；声明参数名必须存在于处理器签名（注册期 fail-fast）
- `options=` 为字典式声明：布尔注解为旗标，其余为带值选项，先于位置参数解析；权限检查先于参数解析，解析失败命令仍被认领
- 中间件仅显式返回 `False` 才否决事件；`Depends` 与 `args=`/`options=` 参数重名注册期报错；`emit_sync` 路径不支持异步依赖
- 热重载失败自动回滚旧实例（尽力而为：`on_unload` 副作用不可撤销）；孤儿 owner 资源 WARNING 告警，`sdk.module.audit(name, deep=True)` 定位
- 命令治理 `*_reply=` 为边沿触发（同一窗口至多回复一次，防连击刷屏）

### 新增

- @YingXinche
  - 命令声明式参数与选项：`@command("roll", args="<count:int> [sides:int=6]")` 自动类型转换按名注入；输入错误自动回复本地化提示与用法；`/help` 未声明 `usage=` 时自动生成用法串
  - 统一依赖注入 `Core/di`：`db=Depends(get_session)` 覆盖命令/事件/生命周期/SSE 路由全部注入点，请求级缓存 + `Depends.module` 语法糖
  - 中间件事件否决权：显式返回 `False` 即丢弃事件（配套 `adapter.event.blocked` 钩子审计），现有中间件零影响
  - 命令治理声明化：`cooldown=` / `rate_limit=`（滑动窗口）/ `usage_limit=`（自然周期配额，经存储持久化）/ `deprecated=`，键粒度 user/session/global，命中默认静默
  - 处理器节流与防抖：`throttle=` / `debounce=`（四个 message 装饰器均支持，互斥声明注册期报错）
  - 内置 ORM（`Model` / `Field`）：Active Record CRUD、参数化泛型 JSON 列、三后端方言、事务复用；自动迁移（新增字段 ALTER TABLE）与 `relationship()` 关系映射
  - 分发决策链追踪（`start_dispatch_trace()`，生产路径零开销）与模块排查诊断（`explain_module` / `explain_event` / `format_report`）
  - 声明式配置环境变量绑定：`metadata={"env": ...}`，优先级 环境变量 > config.toml > 默认值（Docker/CI 免改配置文件）
  - 归属权统一门面（`reclaim` / `counts` / `orphans` / `audit`）与模块重载完备性：卸载前快照、失败自动回滚、路由注销精确化、平台事件方法卸载注销、`on_load` 失败半卸载等盲区修复
  - 影子模块与灰度转正：新版本以独立 owner 并存试运行（事件副本、出站拦截记账、KV 覆盖层、路由只登记不挂载），`shadow_start` / `shadow_diff` / `promote_shadow` / `dismiss_shadow` API 驱动、模块代码零改动
  - 正式支持 Python 3.14（3.14t free-threaded 实验性监测）；`scope.blocked` 生命周期事件（作用域拦截可订阅可统计）

### 修复

- @YingXinche
  - 慢事件日志重构为三层业务定位：执行中看门狗直接报告协程停在哪个文件哪一行，处理器名附定义位置与命令标注，标准库帧自动跳过

---

## [2.8.6] - 2026/09/22
> 正式发布

**版本摘要**
Python 3.10 兼容性修复版：移除 CLI 对 `tomllib`（3.11+ 标准库）的直接依赖，改用 tomlkit——修复 3.10 下 `epsdk init` / `install` 回写 pyproject 时报 `No module named 'tomllib'`。

**升级建议**
- **建议升级**：Python 3.10 用户修复 `ModuleNotFoundError`；其余版本行为不变

**注意事项**
- 无破坏性变更；pyproject 回写仍由 tomlkit 保留注释与格式

### 修复
- @YingXinche
  - `append_pyproject_dependencies` 移除 `tomllib` 依赖，改 tomlkit 单次解析直接改写（并省去一次重复解析）

---

## [2.8.5] - 2026/09/21
> 正式发布

**版本摘要**
本版本确立 `uv tool install ErisPulse` 为受支持的全局 CLI 安装方式（`self-update` 自动走 `uv tool upgrade`，Windows 分离进程解决文件占用）；`init` 生成物治理（分组式 `.gitignore`、不预写适配器启停状态），新增 `version` 子命令与 `--no-banner`。

**升级建议**
- **建议升级**：CLI 安装通道与脚手架治理；推荐 uv 用户改用 `uv tool install ErisPulse`

**注意事项**
- `init` 不再预写 `ErisPulse.adapters.status`（未配置即默认启用）；`.gitignore` 整体排除 `config/`（敏感配置不入库，共享骨架用 `config.full.example`）
- uv tool 用户自更新用 `epsdk self-update`；Windows 更新在新窗口完成、当前终端退出属预期；「工具环境 + 无项目环境」下 run/install 会提示先 `epsdk init`

---

## [2.8.5-dev.0] - 2026/09/21
> 开发版

**版本摘要**
本版本确立 `uv tool install ErisPulse` 全局 CLI 安装通道：`self-update` 自动识别工具环境改走 `uv tool upgrade`（Windows 分离进程解决文件占用），`init` 生成物治理与 `version` / `--no-banner` 等 CLI 规范化。

**升级建议**
- 建议升级：CLI 安装通道与脚手架治理，框架运行时行为不变

**注意事项**
- `init` 不再预写适配器启停状态（未配置即默认启用）；`.gitignore` 整体排除 `config/`
- uv tool 用户自更新用 `epsdk self-update`（自动走 uv tool upgrade）；「工具环境 + 无项目环境」下 run/install 会提示先 `epsdk init`

### 新增
- @YingXinche
  - uv tool 环境一等支持：自动识别工具环境（解释器路径特征）、`self-update` 改走 `uv tool upgrade`、Windows 分离进程更新（避免文件占用）、无项目环境提示
  - `epsdk version` 子命令（别名 `ver`）；Banner 静默机制（非交互终端 / `ERISPULSE_NO_BANNER` / `--no-banner`）

### 修复
- @YingXinche
  - `git init` 环节补错误处理（git 未安装/创建失败明确提示）；补上 2.8.4 起缺失的 `cli.uv.isolated_warning` 五语言翻译；CLI 既有类型错误清理至 0

### 优化
- @YingXinche
  - `init` 生成 `.gitignore` 升级为分组式完整模板（整体排除 `config/` 与 `logs/`）；安装/快速开始/CLI 参考文档同步

---

## [2.8.4] - 2026/09/19
> 正式发布

**版本摘要**
本版本聚焦 CLI 脚手架与环境系统：`init` 支持指定任意目录、生成 `pyproject.toml` 依赖清单并可选创建项目 `.venv`，全命令感知项目虚拟环境；新增 uv 隔离环境检测与 git/.gitignore/README 脚手架。

**升级建议**
- **建议升级**：CLI 体验优化，框架运行时行为不变；新项目建议直接 `epsdk init` 建立自包含环境

**注意事项**
- 请使用 `epsdk run`（自动使用项目 `.venv`）运行机器人，不要 `uv run epsdk run`（一次性隔离环境不持久化）
- `epsdk install` 在项目内会同步回写 `pyproject.toml` 依赖清单

---

## [2.8.4-dev.0] - 2026/09/19
> 开发版

**版本摘要**
本版本聚焦 CLI 脚手架与环境系统：`init` 支持任意目录 + `pyproject.toml` 依赖清单 + 可选项目 `.venv`，`run`/`install`/`uninstall`/`upgrade` 全命令感知项目虚拟环境，新增 uv 隔离环境检测与 git 脚手架。

**升级建议**
- 建议升级：CLI 体验优化，框架运行时行为不变

**注意事项**
- 请使用 `epsdk run`（自动使用项目 `.venv`）运行机器人，不要 `uv run epsdk run`（一次性隔离环境不持久化）
- `epsdk install` 在项目内会同步回写 `pyproject.toml` 依赖清单

### 新增

- @YingXinche
  - `epsdk init` 支持任意目录与项目环境自包含（pyproject 清单、可选 `.venv` 创建与依赖安装、git/.gitignore/README 脚手架、`--no-venv`）
  - `epsdk run` 使用项目 `.venv` 解释器（`ERISPULSE_PYTHON` > `.venv` > `VIRTUAL_ENV`）；install/uninstall/upgrade/list 等同步感知项目环境
  - uv 隔离环境检测（`warn_if_uv_isolated`）与统一目标解释器解析基建

### 优化

- @YingXinche
  - `epsdk doctor` 新增项目虚拟环境检测项；CLI 五语言词条补齐

---

## [2.8.3] - 2026/09/18
> 正式发布

**版本摘要**
本版本为 2.8.x 边界收束版：`wait_reply` 等待期间补全命令交互（命中命令放行执行、等待继续挂起），修复 `activate_on` 懒激活失败后彻底失联，新增对话检查点主动清理与归属感知 Task Factory。

**升级建议**
- **建议升级**：修复交互式命令与懒激活边界缺陷；命令交互为默认新行为，旧行为一行配置找回

**注意事项**
- `wait_reply` 等待期间命中已注册命令默认执行命令（旧行为配置 `wait_reply.cmdpass = true`）
- `activate_on` 激活失败后保留触发器，冷却 30s 自动重试
- Task Factory 仅安装于主事件循环；`run_in_executor` 与自建循环不受归属管辖

---

## [2.8.3-dev.0] - 2026/09/17
> 开发版

**版本摘要**
本版本为 2.8.x 边界收束版：`wait_reply` 补全命令交互（`cmdpass`）、修复 `activate_on` 懒激活失败失联、补充对话检查点主动清理与归属感知 Task Factory。

**升级建议**
- 建议升级：修复交互式命令与懒激活边界缺陷；命令交互为默认新行为

**注意事项**
- `wait_reply` 等待期间命中已注册命令默认执行（旧行为配置 `wait_reply.cmdpass = true`）
- `activate_on` 激活失败后保留触发器，冷却 30s 自动重试

### 新增
- @YingXinche
  - `wait_reply(cmdpass=)` 三态参数：等待期间命中命令放行分发器执行、等待继续挂起（补全交互式对话缺失的命令交互）
  - 对话检查点周期 GC（过期存档不再永久驻留）；Owner 感知 Task Factory（`owner_scope` 内任何 `create_task` 自动归属、卸载兜底取消）

### 修复
- @YingXinche
  - 修复 `activate_on` 激活失败即彻底失联（保留触发器 + 冷却重试）

---

## [2.8.2] - 2026/09/16
> 正式发布

**版本摘要**
本版本聚焦命令系统歧义收口：命中已注册命令的消息不再漏给低优先级消息处理器（消除双重响应），命令名与别名同名冲突改为命令名优先（消除别名静默劫持）；落实文档已描述的 `command.block` / `wait_reply.block` 放行阻断配置。

**升级建议**
- **建议升级**：修复双重响应与别名劫持，无任何 API 签名变更

**注意事项**
- ⚠️ **行为变更**：命中命令的消息（含被拒绝的）不再流向低优先级消息处理器；观察者场景配置 `ErisPulse.event.command.block = false`
- ⚠️ **行为变更**：命令名与别名同名冲突时命令名优先（冲突 WARNING）
- `/help` 子命令始终位于父命令之后

---

## [2.8.2-dev.0] - 2026/09/14
> 开发版

**版本摘要**
命令系统歧义收口：命令命中即认领阻断（消除双重响应）、命令名优先于别名（消除静默劫持）、`/help` 子命令挂父命令展示，并落实 `command.block` / `wait_reply.block` 配置。

**升级建议**
- 建议升级：修复双重响应歧义与别名劫持，无 API 签名变更

**注意事项**
- ⚠️ 命中命令的消息不再流向低优先级消息处理器（观察者场景配置 `command.block = false`）
- ⚠️ 命令名与别名同名冲突时命令名优先（冲突 WARNING）

### 新增
- @YingXinche
  - 落实 `ErisPulse.event.command.block` / `wait_reply.block` 配置（此前仅存在于文档、配置无效）；别名冲突注册告警

### 变更
- @YingXinche
  - 命中命令即认领阻断：被作用域/权限拒绝的命令不再漏给低优先级消息处理器
  - 命令解析与查询统一命令名优先于别名

### 优化
- @YingXinche
  - `/help` 子命令挂到可见父命令下先序展示

---

## [2.8.1] - 2026/09/13
> 正式发布

**版本摘要**
本版本聚焦稳定性与命令系统修缮：配置写入重构为原子路径并新增多实例共享配置目录检测（消除写入丢失与空文件隐患），`import ErisPulse` 冷启动提速，新增组件最低 SDK 版本检查，修复空格分隔子命令永不触发。

**升级建议**
- **建议升级**：无任何 API/配置格式变更；多实例用户消除写入失败告警，所有用户获得启动加速

**注意事项**
- 配置目录新增 `.erispulse_config.lock` 锁文件（退出自动释放，勿删/勿入库）；出现共享配置目录告警请为每个实例使用独立配置目录
- 组件可经 `ModuleMeta(min_sdk_version=...)` 声明最低 SDK 版本（未声明不检查，现有组件零改动）
- ⚠️ **行为变更**：父命令与子命令同时注册时 `admin add x` 优先命中子命令；`/help` 子命令缩进展示（解析帮助的下游注意格式）；大小写不敏感模式下命令参数保留原始大小写

### 新增
- @YingXinche
  - 组件加载期最低 SDK 版本检查（`min_sdk_version`，与严格模式协同）；版本解析比较唯一实现（PEP 440 子集，CLI 与加载器共用）
  - `import ErisPulse` 冷启动优化（CLI 包延迟引入、`importlib.metadata` 全线惰性化）；跨模块重名命令注册告警（此前静默覆盖）

### 优化
- @YingXinche
  - README 排版调整；`/help` 子命令挂到可见父命令下缩进展示

### 修复
- @YingXinche
  - 修复多实例共享配置目录写入偶发失败（ENOENT）：唯一临时文件 + fsync + `os.replace` 原子替换，消除强杀/断电空文件风险；新增 advisory lock 共享检测告警
  - 修复诊断提示 `{name}` 占位符未填充
  - 修复空格分隔子命令（如 `admin add`）注册后永不触发：改最长前缀匹配，权限继承父链

---

## [2.8.0] - 2026/09/12
> 正式发布

**版本摘要**
2.8.0 为「用户控制权、生态协作与生产韧性」综合性大版本：新增作用域三维体系（模块绑定/身份准入/出站白黑名单）与统一事件覆写、命令 ACL，落地交互会话基础设施（租约、检查点、定时器、消息事务、trace-id）与多后端异步存储（sqlite/mysql/postgres，连接失败不阻塞框架），并充实生命周期事件、配置体验（注释保留、`epsdk config` 向导）与模块系统（meta、热重载、懒激活）。

**升级建议**
- **建议升级**：权限控制权完全交给用户（无需改模块代码）；配置向导与注释保留显著降低上手成本；多后端存储与连接韧性面向生产
- 从 2.8.0-dev 预发布版升级：dev 阶段 API 直接切换不保留门面，请过一遍注意事项与移除清单；从 2.7.x 升级：各 dev 条目保留完整细节可作变更手册查阅

**注意事项**
- ⚠️ **移除**：`reload_plugin` → `reload_module`；`Core/access.py` 并入 `scope.identity`（配置节 `ErisPulse.access` 移除）；命令 ACL 独立配置节并入 `event.command.acl`；dev.0 绑定 API 收敛为字典式
- ⚠️ **行为变更**：config.toml 不再自动填充默认键（约 60+ 项）、写入保留注释与键顺序；重复等待立即取消；已认领消息仍可命中挂起等待；事件幂等去重默认开启
- ⚠️ 自定义存储后端需按异步契约迁移（实现 a 前缀异步方法与事务 hook；仅使用框架存储 API 的零改动）
- ⚠️ 生命周期处理器并行执行（返回值按优先级回放）；`fire()` 后台发射不保证时机
- 懒加载失败异常改为 `ModuleNotAvailableError`（旧位置保留导入别名）；拓扑树输出默认 `json_safe=True`；存储连接失败快速失败 + 冷却重连（默认 30 秒）

---

## [2.8.0-dev.3] - 2026/09/10
> 开发版本

**版本摘要**
归属权清理链向外部工具模块开放（`on_cleanup` / `get_current_caller`），生命周期事件体系充实（处理器并行执行、`fire()` 后台发射、新增存储/客户端/i18n/启动阶段事件），异常体系补结构化属性并统一归位；修复非主循环线程后台任务被孤立永不执行。

**升级建议**
- 建议升级：纯新增 + 异常归位保留旧别名；依赖生命周期处理器串行顺序或链式传递中间修改的消费方需评估并行执行

**注意事项**
- `on_cleanup` 必须在对方模块调用链内登记（或显式 `owner=`）；工具模块应在自身 `on_unload` 注销钩子
- 后台 `fire` 事件不保证执行时机，进程退出时可能丢失；懒加载失败异常改为 `ModuleNotAvailableError`

### 新增
- @wsu2059q
  - 外部归属清理钩子 `on_cleanup` / `off_cleanup`：工具模块托管资源随对方卸载自动回调（owner 自动解析、回调异常隔离）；`module.call` 注入 `current_caller` 调用来源感知
  - 生命周期事件充实：`emit` 处理器并行执行（返回值按优先级回放）、`fire()` 后台零成本发射并切换热路径事件；新增 `storage.ready/unreachable/recovered`、`client.request.failed`、`module.reload`、`i18n.language.changed`、`core.init.stage` 等事件与启动分阶段耗时统计；事件名常量化收敛 `Core/constants.py`
  - 异常体系：`ClientError` 系补结构化属性（url/method/attempts 等）、`SessionOccupiedError` / `InteractionCancelled` / `StrictModeError` 迁入统一层级并聚合导出、异常消息 i18n 全覆盖、事件处理器异常附用户代码帧定位
  - 拓扑树 `json_safe=True` 默认 JSON 安全输出（运行时对象自动净化，Dashboard 序列化不再失败）
  - 新增生态文档 `ecosystem/cron.md` 与归属权/错误处理文档更新

### 修复
- @wsu2059q
  - 修复 `spawn_background` 在非主循环线程调度的任务被孤立永不执行（投递回已注册主循环）

---

## [2.8.0-dev.2] - 2026/09/10
> 开发版本

**版本摘要**
本版本落地交互会话基础设施（互斥租约、自动检查点、消息事务、trace-id、会话收件箱）与模块间 RPC 协议化（`module.call` / 服务契约 / 定向事件），存储层升级为多后端异步原生架构（sqlite / mysql / postgres，连接失败不阻塞框架）；配置写入完整保留注释与键顺序、默认配置不再落盘。

**升级建议**
- 建议升级：模块卸载/平台关闭后的等待泄漏修复；存储默认仍 SQLite 行为兼容，MySQL/PostgreSQL 配置 `ErisPulse.storage.backend` + 可选驱动即用

**注意事项**
- **行为变更**：同一会话键重复注册等待时旧等待方立即收到取消（不再干等超时）；已认领消息仍可命中挂起等待（对话连续性优先）
- 同步存储 API 在异步上下文经后台桥接执行（推荐异步 handler 用 `await storage.aget/aset`）；自定义后端需按异步契约迁移（实现 a 前缀方法与事务 hook）
- 存储连接失败快速失败（返回 `False`/`None`）+ 冷却期（默认 30 秒）自动重连，框架不阻塞不崩溃
- **行为变更**：config.toml 不再自动填充框架默认键（约 60+ 项，需要时参考 `config.full.example`）；写入不再按字典序重排，用户注释与键顺序完整保留

### 新增
- @wsu2059q
  - 多后端存储引擎：sqlite（默认）/ mysql / postgres 异步原生，配置或环境变量一键切换（可选依赖 `[mysql]` / `[postgres]`）；方言差异收敛 `SQLDialect`；建池失败指数退避 + 冷却期快速失败；异步事务 `atransaction()`；CLI init/create 模板与示例同步
  - 交互会话管理器 `sdk.interaction`：等待表按 会话/owner/平台 三索引管理，模块卸载/适配器关闭精确取消（`InteractionCancelled`）；回复命中权限复查；会话互斥租约（`acquire` / `hold` / TTL / `get_owner_of`）
  - 模块间通信：`module.call()` 协议化调用（类型化异常 + 懒加载唤醒 + 归因 + 超时 + 出站审计）；`ModuleMeta.services` 服务契约与 `sdk.module.services()` 服务目录；`lifecycle.emit(to=)` 定向事件
  - 会话定时器（`remind` 可被回复取消 / `escalate` 到点必达，随卸载自动取消）；会话级等待 `wait_reply(session=True)` 与多路等待 `event.select()`
  - 事件幂等去重（`event_dedupe`，websocket 重推同 id 只分发一次）；冷启动回放 `replay=`（新装模块热插拔进进行中聊天）；Conversation 恢复自动接管租约并带回 `recent_history`
  - Conversation 自动检查点（分支跳转存档、终态清除、TTL、重启自动恢复工厂）；端到端 trace-id（入站生成、出站携带、`_trace_id` 全链路串联）；消息事务 `event.message_tx()`（异常逆序自动撤回）
  - 会话收件箱 `transcript`（`event.history(n)`，每会话条数上限 + TTL 保留策略）；查询构建器 `ToDict()` 链
  - 声明式配置增强：`example` 字段、docstring 自动生成描述、嵌套 dataclass 递归、`setConfigTemplate()` 带注释模板落盘、`config.full.example` 单一生成源（首行标记自维护）

### 修复
- @wsu2059q
  - 修复 `wait_reply` 挂起的回复被高优先级处理器抢先认领后永远收不到（饿死）：回复命中判定提前至消息分发入口，对话连续性优先于命令匹配
  - 修复作用域 `persist=False` 运行时绑定被后续配置写入静默冲掉（#432，覆盖层记录 + 配置重载重放，事件覆写同步修复）
  - 修复事件分发慢日志归属 `<unknown>`（平台兜底上下文 + 命令归属优先）；修复 Docker 镜像升级 pre/rc 后被入口点静默还原为内置正式版；修复配置面板 select/dict 字段 `[object Object]` 渲染

### 变更
- @wsu2059q
  - 配置写入切换 tomlkit（注释与键顺序完整保留）；框架默认配置不再自动落盘（仅内存合并返回）

### 依赖
- @wsu2059q
  - 新增 `tomlkit`，移除不再使用的 `toml` 运行时依赖

---

## [2.8.0-dev.1] - 2026/08/28
> 开发版本

**版本摘要**
本版本重构权限/访问控制为**作用域（scope）三维体系 + 统一事件/命令覆写**，控制权完全交给用户：模块维度（三级绑定 + merge 继承）、身份维度（四级准入，deny 优先）、出站维度（send/api 方法级白黑名单，被拒返回 `retcode=34601`）；旧 `ErisPulse.access` 与命令权限节直接移除。配套新增 CLI `epsdk config` 配置向导与主人自定义身份源 provider 链，并修复配置「写后立读」不一致、翻译管线代码块围栏损坏等一批问题。

### 新增
- @wsu2059q
  - 统一文本/条目匹配工具 `Core/text_match.py`：精确名 / glob / `re:` 正则统一语法（大小写不敏感，LRU 缓存）
  - 作用域三维体系 `Core/scope.py`：模块维度（platforms/bots/sessions 三级绑定 + `merge` 继承 + 静默语义）、身份维度（adapters/bots/sessions/users 四级二元策略，被拒事件入口丢弃）、出站维度（`actions.<module>.<action>` 方法级白黑名单）；维度化 `set/get/delete` 与字典式点路径访问并存，LRU 缓存与配置热更新
  - 统一事件覆写 `Core/Event/overrides.py`：按事件类型覆写任意模块处理器的触发条件（message/notice/request/meta 的 pattern/regex/detail_types）与命令实现参数（master/hidden/aliases/prefix/help/usage 等，用户优先）+ 命令 ACL 用户黑白名单，配置驱动不改模块代码
  - 管线接入：适配器 `on()` 新增 detail_type/pattern/regex 条件；处理器过滤链为 条件 + 作用域 + 覆写 三重 AND；Send/Api/Request DSL 统一经出站授权闸口
  - `wait_reply` 全链路支持 `pattern` / `regex`；`set_erispulse_section()` 整节替换写入（支持删除子键）
  - CLI `epsdk config` 配置向导（schema 驱动、多账户管理、`--json` 状态输出，字段 i18n 与 CLI 语言统一）；install/init 后自动衔接向导
  - 主人系统 provider 链 `master.provider(fn)`（注册自动归属，卸载自动注销）
  - `ApiDSL` 补齐 OneBot12 标准动作（频道 12 个 + 元动作 4 个；文件资源动作透传并降级标注）
  - 命令查询 API 会话感知（传入上下文按作用域过滤）与覆写后生效值统一
  - 模块热重载归一：本地插件与 PyPI 安装包一致；归属权兜底清理扩面（路由中间件/首页入口/适配器处理器/自定义会话类型/运行时覆写等注册型资源随卸载自动回收）

### 优化
- @wsu2059q
  - CI 文档自动更新流程顺序修正；本地插件目录发现失败告警；pyproject 工程化升级（PEP 735/639、pytest 矩阵 3.10–3.13 + uv + pip-audit + Codecov、dependabot）；模板与示例补 build-system

### 移除
- @wsu2059q
  - `sdk.reload_plugin` 更名 `sdk.reload_module`；独立事件准入系统 `Core/access.py` 并入 `scope.identity`（配置节 `ErisPulse.access` 移除）；命令 ACL 独立配置节并入 `event.command.acl`；dev.0 作用域雏形 bind 系 API 收敛为字典式；安装脚本 root/管理员警告与强制确认移除

### 修复
- @wsu2059q
  - 修复配置「写后立读」不一致（待写键叠加读取）；`wait_reply` 回复被高优先级处理器饿死；慢日志归属 `<unknown>`
  - 修复 Docker 镜像升级 pre/rc 后被入口点静默还原为内置正式版（版本感知自愈）；配置面板 select/dict 字段 `[object Object]` 渲染
  - 修复翻译管线丢代码块围栏（约 150 译文损坏，围栏配平判定 + 两级校验 + 缓存清理）；内嵌 AI 评审闭环与提示词泄露四道防线（存量污染全量重译归零）
  - 修复安装脚本 Debian venv 创建失败（ensurepip 预检自动安装）；修复 mock 字符串 patch 被 3.10 单例遮蔽等 Python 3.10 测试兼容问题（四版本全量通过）

---

## [2.8.0-dev.0] - 2026/08/13
> 开发版本

**版本摘要**
本版本聚焦模块作用域与生态协作基础：新增「平台/Bot/会话」三级绑定的模块作用域系统、模块 meta 元信息与命令总览、本地插件文件夹免打包即插即用（含热重载）与 `activate_on` 事件驱动懒激活。

### 新增
- @wsu2059q
  - 模块作用域系统 `Core/scope.py`：三级绑定（会话>Bot>平台）+ modules/blocked 白黑名单 + LRU 缓存，事件/命令分发闸口按 owner 过滤
  - 模块 meta 与命令总览：`get_meta()` 声明式元信息（支持 i18n 字典）、`get_commands_overview()` 按模块聚合、拓扑树 API（`sdk.get_topology()`）
  - 日志等级屏蔽 `exclude_levels`（被屏蔽等级完全丢弃，支持热更新）
  - 本地插件文件夹 `plugins/`：单文件与包形式免打包自动发现，本地优先于 PyPI 同名包；`sdk.enable_plugin_hot_reload()` 文件监控热重载；`epsdk create module --local` 生成插件结构
  - `activate_on` 事件驱动懒激活：命令/事件触发时激活模块，占位命令对 Help 可见（dict 声明镜像用户级参数）
  - 日志目录与自动分段 `set_output_dir()`（size/date 轮转）；多行消息单行化（控制台保留多行布局）；文件日志补时间戳级别

### 优化
- @wsu2059q
  - 组件生命周期强化：`depends` 声明贯通进 meta、级联卸载/重载、后台任务 owner 归属与卸载兜底取消、`unload(purge=True)` 彻底卸载、适配器 `unload()`、优雅收尾超时保护
  - 适配器依赖声明：`depends` 硬依赖缺失跳过启动、`optional_modules` 软依赖就绪/丢失通知
  - `HttpClient` 更名 `Client`（旧名兼容别名）；SDK 类顶层导出、模板纯注入写法与事件回调类型注解
  - 硬重启监督者契约：`ERISPULSE_SUPERVISED` 标记 + `sdk.is_supervised()` + 监督者指南文档
  - SSL 内联 PEM（`ssl_cert`/`ssl_key` 内容优先）与 `config/ssl/` 默认证书目录
  - 常量收敛与 CLI init 完整配置示例补全
  - 文档翻译 CI 超时治理（语言级并行 + 时间预算多轮续译）；文档大规模审查修正、去重、7 张 mermaid 配图与平台特性同步

---

## [2.7.1] - 2026/08/11
> 正式发布

**版本摘要**
2.7.1 为稳定性与内部质量维护版本：修复配置 watcher 竞态丢数据（BUG-030）、端口占用误判重启死循环、SSE 软重启丢失等关键 bug；GC 分阶段门控显著降低内存驻留，`event.done()` / `mark_processed(claim=, stop=)` 事件状态控制更清晰，静默异常治理与源码 i18n 收尾。

**升级建议**
- **建议升级**：配置写入可靠性与运行期稳定性显著提升，无破坏性公共 API 变更

**注意事项**
- ⚠️ 声明式配置导入路径统一至 `Core.Bases`（runtime 保留兼容 shim）
- ⚠️ GC 默认行为调整：`proactive_gc_generation` 0（轻量回收）、`proactive_gc_full_every` 20（周期深度回收）；显式配置旧值仍生效
- `mark_processed(claim=True, stop=True)` 默认行为与旧版一致；日志订阅器可订阅低于全局级别

---

## [2.7.1-dev.4] - 2026/08/10
> 开发版本

**版本摘要**
静默异常治理 + 内部去重 + i18n 收尾：消除 storage/adapter/router 10+ 处 `except: pass`，router 提取工厂方法去重 ~150 行，源码残留硬编码中文全量 i18n；修复 SSE 路由软重启丢失与端口占用误判。

### 修复
- @wsu2059q
  - 修复 SSE 路由软重启后丢失（重复检查误判抛 `ValueError`）
  - 端口占用探测由 bind 改 connect（消除 TIME_WAIT 误判重启死循环）；被占用降级为跳过 HTTP 启动而非进程退出

### 变更
- @wsu2059q
  - 存储抽象层翻转为异步原生契约（同步 API 成为内置兼容层，现有同步调用零修改；自定义后端需迁移到 a 前缀异步方法）
  - `Core/storage` 改造为包（SQLite 迁入 + MySQL/PostgreSQL 预置，`StorageManager` 保留兼容别名）

### 优化
- @wsu2059q
  - 静默异常补诊断日志、router/adapter 内部去重、28 处函数内导入提升至模块顶层、i18n 全量收尾（~90 key × 5 语言）

---

## [2.7.1-dev.3] - 2026/08/09
> 开发版本

**版本摘要**
事件链路解耦 + GC 优化：`mark_processed(claim=, stop=)` 正交化「认领」与「阻断」（`done()` 别名、`is_stopped()` 查询，完全向后兼容）；主动 GC 分阶段门控与 uninit 即时回收，降低空转开销。

### 新增
- @wsu2059q
  - `event.done(claim=, stop=)` 别名与 `is_stopped()` 查询
  - 主动 GC 分阶段门控（空闲/垃圾量/内存增长）与配置变更即时重启；uninit 追加即时回收

### 变更
- @wsu2059q
  - 中断判定改用 `_propagation_stopped`（`mark_processed()` 默认同时设置，行为兼容）；GC 默认参数调整（常规轮次轻量回收 + 周期性深度回收，显式配置旧值仍生效）

### 优化
- @wsu2059q
  - 主动 GC 空转轮次近乎零开销；`Event.to_dict()` 过滤内部键

---

## [2.7.1-dev.2] - 2026/08/07
> 开发版本

**版本摘要**
回退 dev.1 的路由端口自动顺延（对 Docker 固定端口暴露有害）：端口被占用改为致命初始化错误，启动前预检并清晰报错，交由运行器/Docker 重启。

### 移除
- @wsu2059q
  - 移除端口自动顺延机制及配套常量与翻译键

### 变更
- @wsu2059q
  - 端口被占用视为致命错误：启动前同步预检，`sdk.init()` 返回 False，不再静默降级

### 优化
- @wsu2059q
  - `ep run` 退出时终止子进程，防止孤儿进程占用端口

---

## [2.7.1-dev.1] - 2026/08/06
> 开发版本

**版本摘要**
UX/DX 与配置健壮性维护：修复配置整棵覆盖冲掉热更新、后台线程 on_unload 跨循环报错、日志列表显示原始 `%s`；新增日志订阅低级别订阅与 `plain` 纯文本格式。

### 新增
- @wsu2059q
  - 日志订阅器支持订阅低于全局级别的日志（低级别仅推给匹配订阅器，不污染主日志流）
  - `plain` 纯文本日志格式（`set_format("plain")`），适合采集管道

### 修复
- @wsu2059q
  - 修复配置整棵覆盖：`update_erispulse_config` 改按叶子键写入，陈旧快照不再冲掉其它子键热更新
  - 修复日志内存副本/订阅器未应用 `%` 格式化（Dashboard 显示原始 `%s`）；视觉输出统一入日志管道
  - 修复 `enable()/disable()` 不立即持久化（禁用后重启仍启用）与懒加载代理未清理
  - 修复 `spawn_background` 后台线程 "attached to a different loop"；Display 提示未转义 Rich 标记崩溃
  - 修复 uvicorn 绑定失败 `sys.exit(3)` 级联崩溃刷屏（预检端口并顺延）；退出/关停噪音降级折叠

### 优化
- @wsu2059q
  - 严格模式非法值大声告警、启动面板与 doctor/list 输出优化；残留硬编码中文 i18n 化

---

## [2.7.1-dev.0] - 2026/08/06
> 开发版本

**版本摘要**
稳定性维护版本：修复配置 watcher 竞态导致 `setConfig(immediate=False)` 特定时序静默丢数据（BUG-030）；GC 可控化（`gc.freeze()` + 分代回收）、声明式配置导入路径统一至 `Core.Bases`、翻译脚本分块增量。

**升级建议**
- **建议升级**：修复配置写入丢失，使用延迟写入的模块强烈建议升级

### 修复
- @wsu2059q
  - 修复配置 watcher 竞态丢数据（BUG-030）：区分自身写入与外部修改，外部修改保留脏键合并；`wrapper.py` 4 处静默异常补 trace 日志

### 优化
- @wsu2059q
  - GC 可控化：`gc.freeze()` 冻结框架对象 + 分代回收配置项；声明式配置导入路径统一至 `Core.Bases`（runtime 保留 shim）
  - 翻译脚本分块增量（块级哈希缓存，小改动只重译变化块）

---

## [2.7.0] - 2026/08/04
> 正式发布

**版本摘要**
2.7.0 为面向生产部署与开发者体验的综合性版本：OneBot12 标准化（`ApiDSL` / `BaseConverter` / 会话类型推断修复）、配置热更新系统化、异常诊断与 `doctor` 排障、优雅关闭与环境变量配置，Web 栈懒加载使导入期内存减半。

**升级建议**
- **强烈建议升级**：群通知 `event.reply()` 修复、运行时热更新减少重启、导入期内存 ~112MB → ~58MB、容器化部署能力齐备

**注意事项**
- ⚠️ Schema 定义源迁移至 `Core/Bases/`（`runtime/` 保留兼容 shim）；`infer_receive_type` 对 notice/request 改从 ID 字段推断
- ⚠️ 配置加载不再静默回退：TOML/权限错误输出精确行号或原因；CORS/安全头与存储 DB 路径变更需重启（有告警）
- `server.auto_start` 默认 `true` 行为不变；硬重启退出码等跨进程契约统一引用 `Core/constants.py`
- `epsdk create` 模板改嵌套 `ConfigClass`/`I18nClass`，文案跟随脚手架语言；新增导出 `ApiDSL` / `BaseConverter` / `I18nKey` / 诊断与内存工具等符号

---

## [2.7.0-dev.5] - 2026/07/31
> 开发版本

**版本摘要**
功能增强与配置热更新系统化：logger/适配器并发/命令参数/GC 间隔运行时热更新，新增 `sdk.shutdown()` 优雅关闭、配置环境变量覆盖、`X-Request-ID`、`BaseConverter` 基类与 CLI `doctor`；修复限流清理窗口等 bug，完成常量提取与 CLI/主库隔离。

### 修复

- @wsu2059q
  - 修复路由限流清理按固定窗口误删长窗口规则（BUG-027，`100/hour` 退化为 `100/minute`）
  - 修复配置监听广播半成品 TOML（BUG-029）：加载失败保留上次有效缓存，仅成功时发射 `config.updated`

### 新增

- @wsu2059q
  - 配置热更新系统化：logger（级别/文件/内存/格式）、适配器并发上限、命令参数、GC 间隔热更新；CORS/安全头与存储路径变更告警「需重启」
  - `sdk.shutdown()` 优雅关闭 + SIGTERM/SIGHUP 信号处理；硬重启前强制刷盘
  - 配置环境变量覆盖（`ERISPULSE_<SECTION>_<KEY>`，Docker/12-factor）
  - 路由 `X-Request-ID` 请求关联 ID；`secret` 字段脱敏；`validate_config` 强化（类型/枚举/范围）
  - CLI 全局 `--no-color` / `--yes`；`BaseConverter` 事件转换器基类；`epsdk doctor` 诊断命令
  - `lifecycle.once()` / `has_handlers()` 公开 API

### 重构

- @wsu2059q
  - 跨模块契约常量化（`HARD_RESTART_EXIT_CODE` 等）；CLI 与主库常量隔离（`CLI/constants.py` 镜像，回归测试钉死一致）
  - 硬编码中文清扫与 CLI i18n Windows 检测补强；create 模板现代化（嵌套 ConfigClass + 文案多语言化）
  - 版本比较增强（post/local/epoch，纯标准库）

### 优化

- @wsu2059q
  - 日志热路径（deque 环形缓冲 + `_get_caller` 快速路径）、发送热路径短路、拓扑排序反向邻接表、`list --outdated` 单次拉取索引

---

## [2.7.0-dev.4] - 2026/07/30
> 开发版本

**版本摘要**
内存占用优化版本：Web 栈（FastAPI/Uvicorn/Starlette）延迟到路由首次服务时加载（导入期内存 ~112MB → ~58MB），新增 `server.auto_start` 跳过 HTTP 服务器与 `runtime/memory.py` 内存追踪；完全向后兼容。

**升级建议**
- 建议升级：所有进程导入期内存显著下降；无需 HTTP 的 bot 可完全省去 web 栈

**注意事项**
- `server.auto_start` 默认 `true` 行为不变；显式 `false` 跳过服务器启动（Dashboard 等 HTTP 功能不可用）

### 新增

- @wsu2059q
  - `runtime/memory.py` 内存追踪工具（RSS / tracemalloc / 快照），初始化与主动 GC 关键点 TRACE 记录
  - `server.auto_start` 配置项（默认 true）

### 优化

- @wsu2059q
  - Web 栈懒加载（惰性 app 属性 + 守护装饰器）；Windows 自更新脚本文案 i18n；新增贡献指南文档

---

## [2.7.0-dev.3] - 2026/07/29
> 开发版本

**版本摘要**
OneBot12 标准化增强：新增 `ApiDSL` 标准 API 动作基类（信息查询/群管理/消息管理/文件操作），修复 notice/request 事件会话类型推断 bug（群通知 `event.reply()` 误发私聊），`sdk.init()/run()` 新增生命周期回调钩子。

**升级建议**
- 建议升级：群通知事件的 `event.reply()` 现正确发送到群内；信息查询类调用跨平台统一

**注意事项**
- `infer_receive_type` 行为变更：notice/request 事件改从 ID 字段推断会话类型，message 事件不受影响

### 新增

- @wsu2059q
  - `ApiDSL` 基类：OneBot12 标准 API 动作 DSL（用户/群组/消息/文件 + `call()` 逃生舱、`Using()` 多账户），默认委托 `call_api` 零配置可用
  - `sdk.init()` 新增 `before_init` / `after_init`、`sdk.run()` 新增 `on_ready` 回调钩子（同步/异步均可）

### 修复

- @wsu2059q
  - 修复 notice/request 事件的会话类型推断（`infer_receive_type`）

---

## [2.7.0-dev.2] - 2026/07/29
> 开发版本

**版本摘要**
开发者可观测性增强：新增 `runtime.diagnostics` 异常诊断（加载/初始化失败自动输出用户代码帧摘要），配置加载升级为三态可操作诊断（TOML 行号/权限原因）；完全向后兼容。

**升级建议**
- 建议升级：默认 INFO 级即可定位组件加载失败位置；配置写错输出精确行号

### 新增

- @wsu2059q
  - `runtime.diagnostics` 异常诊断引擎（`extract_user_frame` / `format_diagnostic_block` / `log_diagnostic`），模块/适配器加载与初始化失败路径全量接入
  - 配置加载三态诊断（TOML 语法错误行号列号 / 权限原因 / 通用失败，附「已回退默认配置」告警）；flush 阶段配置损坏单独捕获并保留脏键重试（跨进程告警冷却）

---

## [2.7.0-dev.1] - 2026/07/28
> 开发版本

**版本摘要**
Event 包装类平台修饰方法支持：新增 `Event.send_chain()` 与 `reply(via=)`，平台专有修饰方法可在事件处理器中使用；完全向后兼容，适配器无需改动。

**升级建议**
- 建议升级：云湖看板等平台专有修饰方法现可在事件处理器中链式使用

### 新增

- @wsu2059q
  - `Event.send_chain()` 返回可自由追加修饰与发送方法的链；`reply()` 新增 `via` 参数按序应用修饰链

### 优化

- @wsu2059q
  - send-dsl / api-reference 文档与示例、脚手架模板补充平台修饰方法写法

---

## [2.7.0-dev.0] - 2026/07/26
> 开发版本

**版本摘要**
i18n 键声明式注册 + Schema 定义源迁移 + 适配器 EventMixin 自动注册：新增 `I18nClass` 嵌套类集中声明翻译键，Schema 定义从 `runtime/` 迁至 `Core/Bases/`（确立 Bases 为供应方），适配器声明 `EventMixin` 后框架自动注册到自身平台。

**升级建议**
- 建议升级：配置描述引用的 i18n 键由框架自动注册；导入路径更清晰

### 新增

- @wsu2059q
  - `Core/Bases/i18n_schema.py`：`BaseI18n` / `I18nKey` 声明式翻译键 Schema，模块/适配器经 `I18nClass` 嵌套类自动注册（早于配置模板生成）
  - `BaseAdapter.EventMixin` 嵌套类：声明后框架自动注册到适配器自身平台
  - `Core/Bases` 导出 Schema 类型；示例项目与脚手架模板同步推荐写法

### 变更

- @wsu2059q
  - Schema 定义源迁移：`config_schema.py` / `i18n_schema.py` 定义移至 `Core/Bases/`，`runtime/` 保留懒加载 shim

### 优化

- @wsu2059q
  - `advanced/i18n.md` 新增 I18nClass 推荐写法；适配器核心概念文档新增 EventMixin 章节

---

## [2.6.3] - 2026/07/25
> 正式发布

**版本摘要**
2.6.3 为维护增强版本：公共 API 导出规范化（补全 `__all__`），`on_config_update` 回调核心化覆盖全部配置变更路径；移除类型存根以解决解析冲突导致的 Unknown 注解提示。

**升级建议**
- **建议升级**：配置热更新回调覆盖全部变更路径，IDE 补全更准确

**注意事项**
- `on_config_update` 现响应代码与文件编辑全部路径，升级后请验证组件回调逻辑
- 该版本移除了存根（解决存根解析冲突导致导入注解提示 Unknown）

---

## [2.6.3-dev.0] - 2026/07/23
> 开发版本

**版本摘要**
标准化与配置热更新修复版本：公共 API 导出规范化（补全 `__all__`），`on_config_update` 回调核心化（覆盖全部配置变更路径，BUG-021）。

**升级建议**
- 建议升级：配置热更新回调覆盖代码与文件编辑全部路径

### 新增

- @wsu2059
  - `on_config_update` 核心路由：管理器订阅 `config.set` / `config.updated`，按配置键前缀分发回调（此前仅配置面板路径触发）
  - 核心基类单元测试补齐（errors / kv_builder / websocket / 配置变更路由）

### 修复

- @wsu2059
  - 修复 `_flush_config()` 写入后未同步 mtime，框架自身写入被误判外部修改、重复触发 `config.updated`

### 优化

- @wsu2059
  - 补全顶层 / Core / Bases 的 `__all__` 导出声明；示例项目配置类改嵌套类声明

---

## [2.6.2] - 2026/07/21
> 正式发布

**版本摘要**
2.6.2 为代码质量与开发体验版本：SendDSL 内置标准发送方法 + `epsdk types` 类型存根解决 IDE 补全，引入 basedpyright 类型检查（修复 61 个类型 bug），修复跨环境安装错位，配置文件外部编辑自动重载。

**升级建议**
- **建议升级**：IDE 补全体验显著提升；修复「装得上却看不到」的跨环境安装问题

**注意事项**
- ⚠️ SendDSL 标准发送方法由基类默认实现（委托 `Raw_ob12`），`To()` 自动会话类型转换
- 链式方法返回 `Self`；`list_sends` 不再排除基类方法
- 下游启用 basedpyright 可能暴露此前未发现的类型问题（非破坏性）

---

## [2.6.2-dev.2] - 2026/07/22
> 随版本发布

**版本摘要**
开发体验打磨：CLI 与框架提示能力解耦（独立 hints 模块）、CLI 友好提示系统（拼写建议 / 异常 hint / Quick Start 面板）、SDK 门面增强。

### 新增

- @wsu2059
  - `CLI/hints.py` 独立拼写建议模块；CLI 友好提示：统一错误输出格式、四类异常场景化 hint、无子命令时 Quick Start 面板
  - `sdk.version` property（实时查询安装版本）

### 变更

- @wsu2059
  - `sdk.init()` 重复调用保护（已初始化时告警返回 True）；`sdk.__repr__()` 显示版本与组件计数；pyproject readme 指向 `README.pypi.md`

---

## [2.6.2-dev.1] - 2026/07/19
> 随正式版发布
> 开发版本

**版本摘要**
代码质量全面升级：引入 basedpyright 类型检查（修复 61 个类型 bug）、ruff 16 规则集（清除 100+ 问题）、pathlib 迁移 71 处，新增 `spawn_background()` 与配置文件变化监听。

### 新增

- @wsu2059
  - `runtime.tasks.spawn_background()` 统一管理后台任务，避免被 GC 提前回收
  - basedpyright 类型检查系统（standard 模式，真实类型 bug 提级 error）
  - `Core.config` 配置文件变化监听：外部编辑自动重载并广播 `config.updated`，取消待写定时器避免回写覆盖
  - pip 回退前 `ensurepip --upgrade` 自举，解决 uv venv 无 pip 安装失败

### 优化

- @wsu2059
  - ruff 启用 16 个规则集；`os.path.*` → `pathlib` 迁移 71 处；`Core.constants` 7 个未引用常量正式投入使用
  - `SendDSL.To()` 接入自动会话类型转换（接收类型 → 发送类型）

### 修复

- @wsu2059
  - 修复 61 处类型注解错误（返回值 / Optional / override / Python 3.10 兼容等）与 uv `--python` 参数位置错误

---

## [2.6.2-dev.0] - 2026/07/16
> 开发版本

**版本摘要**
本版本聚焦 IDE 补全与跨环境安装修复：SendDSL 基类内置标准发送方法，新增 `epsdk types` 运行时类型存根生成命令，修复 pipx/venv 跨环境安装错位。

### 新增

- @wsu2059
  - `SendDSL` 基类内置 Text/Image/Voice/Video/File 标准发送方法（默认委托 `Raw_ob12`），链式方法返回 `Self` 支持子类补全
  - `epsdk types` 命令：扫描已安装组件生成 `TYPE_CHECKING` 类型存根 `_ep_types.py`（跨环境子进程内省，`--output`/`--force` 等选项）
  - `BaseFinder` 支持 `python_executable` 跨环境 entry-points 查询

### 优化

- @wsu2059
  - `list_sends` 改为排除链式修饰方法（标准发送方法可被 `event.supports()` 识别）；`adapter.get` / `module.get` 泛型 TypeVar
  - 适配器模板移除标准方法样板代码，演示平台特有方法

### 修复

- @wsu2059
  - 修复跨环境安装错位：`PackageManager` 统一目标解释器、uv 调用显式 `--python`，install 与 list 查询同一环境

### 变更

- @wsu2059
  - SendDSL 标准发送方法由基类提供默认实现，适配器子类只需实现 `Raw_ob12`

---

## [2.6.1] - 2026/07/16
> 正式发布

**版本摘要**
2.6.1 为维护增强版本：`LazyModule` 重构消除动态加载副作用、友好错误提示大幅扩展、`choose` 交互式方法重写（尊重发送方法 + 智能样式）。

**升级建议**
- **建议升级**：属性访问开销与 GC 压力降低、`module.get()` 更直观、调试体验提升

**注意事项**
- ⚠️ 管理器参数命名统一为 `name`（旧关键字仍可用，已弃用）；`module.get()` 对已注册未加载模块返回懒代理
- `LazyModule` 使用 `__slots__`，不能给代理动态挂属性；`options_format` 默认值改为 `"auto"`

---

## [2.6.1-dev.1] - 2026/07/16
> 随正式版发布

**版本摘要**
本版本重构 `choose` 交互式方法：尊重用户传入的发送方法、支持占位符插入与方法感知的选项智能样式。

### 优化

- @wsu2059
  - `choose()` / `collect()` 重构：`merge_prompt=True` 尊重用户 method、新增 `placeholder` 占位符参数；`options_format="auto"` 按 method 自动选择 Markdown/Html/纯文本样式

---

## [2.6.1-dev.0] - 2026/07/15
> 开发版本

**版本摘要**
本版本消除动态加载副作用并统一管理器参数命名：`LazyModule` 热路径优化、懒加载透明化（`module.get()` 返回代理）、管理器参数对齐 `ManagerBase` 基类，友好错误提示场景大幅扩展。

**升级建议**
- 建议升级：长期运行属性访问开销与 GC 压力显著降低；`module.get()` 行为更直观

**注意事项**
- ⚠️ 管理器参数命名统一为 `name`（`module_name=` / `platform=` 旧关键字仍可用，已弃用）
- `module.get()` 对已注册未加载模块返回懒加载代理（确认加载状态用 `module.is_loaded()`）
- `LazyModule` 改用 `__slots__`，不能再给代理动态挂属性；初始化失败后短路不再重试（可用 `module.load()` 重触发）

### 新增

- @wsu2059
  - `ModuleManager.register_lazy()` / `unregister_lazy()` 懒加载代理表：`get()` 与 `sdk.xxx` / `module.xxx` 行为一致
  - 管理器旧关键字参数弃用告警（一次去重，i18n 五语言）

### 优化

- @wsu2059
  - `LazyModule` 重构：移除热路径日志、`__slots__`、weakref 打破循环引用、缓存签名分析、初始化失败短路
  - `runtime/hints.py` 友好提示扩展：NameError / 协程忘 await / 缺参数 / 不可调用 / 事件循环 / 递归 / 超时 / 连接错误及 ErisPulse 自定义异常

### 变更

- @wsu2059
  - 管理器参数命名对齐 `ManagerBase`（`name` / `class_type` / `info`），消除 basedpyright 覆写违规，旧关键字保留兼容

---

## [2.6.0] - 2026/07/13
> 正式发布

**版本摘要**
2.6.0 为面向生产环境的增强版本：新增发送规则装饰器系统与批量构建模式、框架主人权限系统，并全面强化资源管理（事件并发背压、生命周期钩子 owner 清理、主动 GC、离线 Bot 回收），完成 Web 前端资源提取重构。

**升级建议**
- **强烈建议升级**：统一的消息发送治理与权限管理；修复多项内存泄漏

**注意事项**
- ⚠️ 钩子存储格式变更为三元组 `(priority, handler, owner)`（不影响公共 API）；事件并发上限 / GC 间隔 / 离线 Bot 过期均可配置
- `Core/web_status/` 已移除，错误页统一纯 CSS 样式；`register_home_entry()` 支持 i18n 字典
- 新增导出符号：`SendContext` / `SendBuilder` / `BatchContext` / `master` / `MasterManager`

---

## [2.6.0-dev.2] - 2026/07/13
> 随正式版发布

**版本摘要**
本版本完成 Web 前端资源重构：内联 HTML/CSS 提取至 `Core/assets/`，新增 `register_home_entry()` 模块快捷入口注册（含 i18n），移除 `web_status/` 与外部图片依赖。

**升级建议**
- 建议升级：基础设施重构为后续前端扩展奠基

**注意事项**
- `Core/web_status/` 已移除，错误页统一纯 CSS 无图样式；模板导入期缓存，运行期零 I/O

### 新增

- @wsu2059q
  - `register_home_entry(name, url, icon_svg)` 根路由入口按钮注册（name 支持 i18n 字典）
  - `Core/assets/` 前端资源包：根页面与错误页模板独立文件管理
  - HttpClient 新增 `files` 参数（multipart 文件上传，无需自行导入 aiohttp）

### 移除

- @wsu2059q
  - 移除 `Core/web_status/` 整包、外部看板娘图片与 `/status-assets` 静态挂载

### 优化

- @wsu2059q
  - `router.py` 精简约 280 行内联 HTML/CSS；CONTRIBUTING 项目结构同步

---

## [2.6.0-dev.1] - 2026/07/12
> 开发版本

**版本摘要**
本版本聚焦性能与资源管理：事件处理器并发背压控制、生命周期钩子 owner 自动清理、主动 GC、离线 Bot 过期回收与限流存储定期清理，修复多项内存泄漏。

**升级建议**
- 建议升级：修复 HttpClient session 泄漏、wait_reply CancelledError 残留、生命周期钩子泄漏

**注意事项**
- 钩子存储格式从二元组改为三元组 `(priority, handler, owner)`，不影响公共 API
- 事件处理器并发上限默认 64（`handler_max_concurrency`）、主动 GC 默认 300 秒（`proactive_gc_interval`）、离线 Bot 默认 3600 秒过期（`offline_bot_expiry`）
- SendDSL `rules` 改为构造后赋值，覆写 `__init__` 的第三方 Send 子类无需修改

### 新增

- @wsu2059q
  - 事件处理器 Task 追踪与并发背压（信号量限流 + shutdown 排空在途任务）
  - 生命周期钩子 owner 追踪与 `unregister_by_owner()` 按归属批量清理，模块卸载/适配器清理自动接入
  - 主动 GC 后台任务、离线 Bot 记录过期清理、路由限流存储定期清理

### 修复

- @wsu2059q
  - 修复软重启泄漏 `aiohttp.ClientSession`（uninit 关闭连接池）与 `LazyModule._module_info` 循环引用残留
  - 修复 `wait_reply` 取消时 `_waiting_replies` 条目残留（`finally` 清理）

---

## [2.6.0-dev.0] - 2026/07/09
> 开发版本

**语义化版本承诺**
从 2.6.0 起，ErisPulse 严格遵守语义化版本控制：2.6.x 仅修复 Bug，2.7.0+ 可引入新功能但保持向后兼容；本次新 API 在 2.6.x 生命周期内保证签名稳定。

**版本摘要**
2.6.0 首个开发版引入两大特性：SendDSL 发送规则装饰器系统（超时/重试/回调/延迟/优先级/进度）与批量构建模式、框架主人（Master）权限系统（`master=True` 自动鉴权）。

**升级建议**
- **建议升级**：发送规则与主人系统提供统一的生产能力；修复委托链路回调重复触发

**注意事项**
- 规则方法返回 self，必须置于发送方法之前；规则随 To/Using/Account 新实例独立传播
- 批量构建模式下 Timeout/Retry 作用于每条发送，Hook/OnError/OnProgress 为整批语义；无规则时行为完全不变
- 主人配置位于 `ErisPulse.master.users`（dict 按平台 / list 全局）；新增导出 `SendContext` / `SendBuilder` / `BatchContext` / `master` / `MasterManager`

### 新增

- @wsu2059q
  - `Core/Bases/send_rules.py` 发送规则系统：`SendContext` 执行上下文 + `apply_send_rules()` 规则引擎
  - SendDSL 新增 7 个链式规则方法：Hook / Retry / Timeout / Defer / Priority / OnProgress / OnError
  - `Core/Bases/send_builder.py` 批量构建模式：`.Build()` 累积发送意图、`.send_all()` 统一执行，支持串行/并行、失败继续与整批规则
  - `Core/master.py` 框架主人系统：`MasterManager` 单例（is_master / add / remove / list，运行时增删持久化），命令装饰器新增 `master=True`

### 修复

- @wsu2059q
  - 修复标准适配器委托链路（Text → Raw_ob12）下规则与回调重复触发；修复规则传播时 hooks 列表浅拷贝共享、有规则时 `message.sent` 提前触发

### 文档

- @wsu2059q
  - send-dsl / platform-guide / common-tasks / README 同步新增发送规则与批量构建说明

### 测试

- @wsu2059q
  - 新增 send_rules / send_builder / master 单元测试共 102 个（含真实适配器模式集成测试）

---

## [2.5.5] - 2026/07/10
> 正式发布

**版本摘要**
2.5.5 修复 Storage 嵌套键路径包含大纯数字段（如 QQ 群号）时误判为数组索引、分配数亿元素导致进程被 OOM Kill 的安全漏洞。

**升级建议**
- **强烈建议升级**：修复 `storage.set()` 写入大数字 ID 键时进程被 OOM Kill（退出码 -9）

**注意事项**
- 点分隔路径的中间层统一按字典键处理；仅已有列表容器且索引 < `STORAGE_MAX_LIST_INDEX`（10000）时按数组索引

### 安全
- @wsu2059q
  - `Core/storage` 修复 `_set_nested_value` OOM：预创建中间层一律用字典、超大索引安全跳过、递归改迭代；新增 `STORAGE_MAX_LIST_INDEX` 常量

---

## [2.5.4] - 2026/07/09
> 正式发布

**版本摘要**
2.5.4 修复修改账户配置后适配器缓存不刷新导致账户解析失败的关键问题与服务器停止时 WebSocket 误报日志；恢复 `_load_accounts()` / `_load_config()` 向后兼容。

**升级建议**
- **强烈建议升级**：修复 Dashboard 改 token 后多账户适配器「未找到可用账户」

### 新增
- @wsu2059q
  - `BaseAdapter` 恢复 `_load_accounts()` / `_load_config()` 覆写点（返回非 None 时优先采用），旧适配器无需修改

### 修复
- @wsu2059q
  - 修复 `_accounts_data` 仅在 `__init__` 读取一次：每次 `adapter.start()` 前刷新，账户配置改动即时生效
  - 修复服务器停止时 WebSocket 关闭竞态误报 ERROR 日志（降为 DEBUG）

---

## [2.5.3] - 2026/07/08
> 正式发布

**版本摘要**
2.5.3 修复 2.5.2 引入的多账户解析回归（`_resolve_account` 恒失败），交互式方法个性化增强，配置 Schema i18n 扩展到 options/placeholder/分组标题。

**升级建议**
- **强烈建议升级**（多账户适配器用户必升）：修复发送消息时的账户解析报错

### 新增
- @wsu2059q
  - 配置 Schema i18n 扩展至 `description` / `options[].label` / `placeholder` / `group_labels` 四维，`_schema_meta` 作为扩展元数据声明入口
  - 交互式方法增强：`choose()` 新增 `options_format` / `merge_prompt`，`confirm()` 新增 `hint`，`collect()` 字段支持选择题

### 修复
- @wsu2059q
  - 修复 2.5.2 引入的 `_resolve_account()` 回归：`__init__` 中恢复 `_accounts_data` 填充，多账户适配器收发消息不再报 `未声明 AccountConfigClass`

---

## [2.5.2] - 2026/07/06
> 正式发布

**版本摘要**
2.5.2 聚焦配置系统升级与 Dashboard 模块管理：配置 Schema 通用化（`BaseConfig`）、模块声明式配置（`ConfigClass` + `self.cfg`）、Dashboard 模块配置视图；同期新增运行时状态快照、全局拼写纠错提示引擎与各子系统 TRACE 链路追踪。

**升级建议**
- **强烈建议升级**：配置系统通用化，调试体验（友好提示 / dump_state / TRACE 追踪）全面增强

**注意事项**
- ⚠️ 适配器推荐以 `self.cfg` 替代 `self.config` 访问配置；`AdapterConfig` 由 `BaseConfig` 替代、metadata `webui` 键统一为 `ui`（旧名均保留兼容）
- 模块声明式配置不提供 `self.config`，统一使用 `self.cfg`；`ConfigClass` 以模块注册名为配置键
- CLI 别名 `ini` 已移除、`lr` 改为 `lsr`
- 存储连接默认 `journal_mode=WAL` + `synchronous=NORMAL`（修复事务外操作不生效问题）

---

## [2.5.2-dev.6] - 2026/07/06
> 随正式版发布

**版本摘要**
本版本为 2.5.2 正式版发布当天的最终整合：配置 Schema 重构为通用 `BaseConfig`，适配器改 `self.cfg` 实时读取，模块新增声明式配置（`ConfigClass`），Dashboard 新增模块配置页面。

### 新增

- @wsu2059q
  - 配置 Schema 系统重构：新增 `BaseConfig` 通用基类（`AdapterConfig` 为兼容别名），`description` 支持 i18n 格式，新增 `register_config_i18n()` / `resolve_config_schema()`；移除 `AccountConfig` 别名
  - 适配器配置访问重构：`self.cfg` 实时读取（`self.config` 为兼容别名，`accounts` 同步实时读取），移除 `_load_config()` / `_load_accounts()` 缓存加载方法
  - 模块声明式配置：`ConfigClass` 类属性 + `self.cfg` + `on_config_update()` 回调（不提供 `self.config`），配置键使用模块注册名
  - Dashboard 新增模块配置页面与 API（`GET/PUT /api/module/{name}/config`），适配器/模块配置描述 i18n 自动解析

### 变更

- @wsu2059q
  - CLI create 适配器/模块模板同步切换 `BaseConfig` + `self.cfg` + 声明式配置写法；新增 `AGENTS.md`，developer-guide / i18n 文档与示例项目同步更新

---

## [2.5.2-dev.5] - 2026/07/05
> 开发版本

**版本摘要**
2.5.2-dev.5 为友好错误提示引擎补齐 Event loop 关闭与非法 await 两类场景的测试覆盖。

### 测试

- @wsu2059q
  - `main.py` 友好错误提示测试新增 2 个真实环境用例（`Event loop is closed` / `invalid await`）

---

## [2.5.2-dev.4] - 2026/07/03
> 开发版本

**版本摘要**
本版本聚焦可观测性与事件系统增强：新增 `sdk.dump_state()` 状态快照、事件/命令/存储/路由 TRACE 链路追踪与全局友好错误提示引擎（拼写纠错）。

### 新增

- @wsu2059q
  - `sdk.dump_state()` 运行时状态快照导出（SDK/适配器/模块/事件/路由）
  - 事件/命令/存储/路由子系统 TRACE 级链路追踪日志与慢 handler 告警（i18n 五语言同步）
  - 全局友好错误提示引擎（`runtime/hints.py`）：AttributeError / ImportError / KeyError 自动给出拼写建议；CLI 无效命令拦截提示
  - `Event` 包装类新增 `get_target_id()` / `get_session_id()` / `supports()` / `available_methods()`，`reply()` 新增 `at_sender` / `quote` 参数；`register_event_method/mixin` 支持 `"*"` 通配符
  - 存储/配置/查询构建器补齐异步接口（`aget/aset`、`agetConfig`、`aExecute` 系）；`epsdk list` 新增模块脚本入口发现

### 变更

- @wsu2059q
  - CLI 别名治理：移除 `ini`（与 install 过于相似）、`lr` 改为 `lsr`

### 优化

- @wsu2059q
  - `Core/constants.py` 常量补齐 `Final` 注解与 `TypedDict`，私有成员移出 `__all__`

---

## [2.5.2-dev.3] - 2026/06/30
> 开发版本

**版本摘要**
本版本修复存储 `synchronous=NORMAL` 对事务外高频操作不生效的问题，模块/适配器发现策略改为默认启用。

### 变更

- @wsu2059q
  - 模块/适配器发现策略改为默认启用：新安装组件默认 `enabled=true`，禁用组件在 `list_items()` / `get_status_summary()` 中可见

### 修复

- @wsu2059q
  - `Core/storage` 修复 `synchronous=NORMAL` 不跨连接生效：连接创建统一走 `_open_connection()`，每个新连接应用 WAL + NORMAL（此前新连接回落 FULL，每次 commit 触发 fsync）

---

## [2.5.2-dev.2] - 2026/06/29
> 开发版本

**版本摘要**
本版本优化 Docker 部署、配置持久化健壮性与日志体验：新增 Docker 健康检查与日志订阅系统，严格模式默认调回宽松，框架内部调试日志大量降为 TRACE。

**升级建议**
- 建议升级：Docker 部署用户（新增健康检查，compose 移除冗余 command）

### 新增

- @wsu2059q
  - `Dockerfile` 新增 HEALTHCHECK（复用 `/ping` 端点）；新增 `.pre-commit-config.yaml`（ruff check + format）
  - `Core/logger` 新增日志订阅系统（`handler` / `remove_handler`，按级别筛选、自动补发历史日志），供 Dashboard 等实时接收结构化日志

### 优化

- @wsu2059q
  - `Core/config` 新增 atexit 钩子：进程异常退出时自动 flush 未持久化的脏配置
  - 日志配色主题重构（INFO 绿色等，致谢 @mmmpipi）；CLI Emoji 替换为纯 ASCII
  - 框架内部大量调试日志降为 TRACE（路由/事件/适配器/懒加载/命令等子系统），并新增关键流程 TRACE 观测点

### 变更

- @wsu2059q
  - 严格模式默认级别由 1（跳过）调回 0（宽松）：未继承基类的组件仅告警加载，显式配置可恢复；提示文案精简（5 语言）
  - Docker/compose 工程文件清理（`.dockerignore`/`.gitignore` 排除 `config/.packages`、移除冗余 VOLUME/command）；pytest 配置迁移至 pyproject；Ruff 检查范围扩展至 tests

### 修复

- @wsu2059q
  - 修复 CLI upgrade 偶发 `'NoneType' object has no attribute 'lower'`
  - `Core/storage` SQL 查询构建器列名校验改黑名单模式（仅拦截注入危险字符），修复 `*` 通配符被误拒（BUG-019，影响 Cron 等模块）
  - `Core/logger` 修复 `set_level()` / `set_module_level()` 无法识别 TRACE 等自定义级别
  - `Core/client` HttpClient 新增代理支持（`proxy` 参数 / 环境变量自动检测），默认重试次数 0 → 1

---

## [2.5.2-dev.1] - 2026/06/27
> 开发版本

**版本摘要**
本版本强化 Docker 容器运行稳定性：entrypoint 不再自动更新框架（交由 Dashboard 热更新），子进程异常退出时主进程自动重试而不退出。

**升级建议**
- 建议升级：所有 Docker 部署用户；容器不再因内部错误反复重启

### 修复

- @wsu2059q
  - `CLI/commands/run.py` 子进程崩溃容错：非硬重启退出码不再退出主进程，记录日志后自动重试；模块内 `sys.exit()` 不再终止子进程

### 移除

- @wsu2059q
  - Docker entrypoint / Dockerfile / compose 移除框架自动更新逻辑与 `ERISPULSE_CHANNEL` 等环境变量，`restart` 策略改为 `on-failure:5`

---

## [2.5.2-dev.0] - 2026/06/27
> 开发版本

**版本摘要**
2.5.2-dev.0 修复非热重载模式下 `ep run <script>` 找不到脚本所在目录子包的问题

### 修复
- @wsu2059q
  - `CLI/commands/run.py` 修复非热重载模式下运行脚本时找不到脚本所在目录子包的问题：

### 优化
- @wsu2059q
  - 将 `Event` cmd和msg的处理逻辑进行合并

---

## [2.5.1] - 2026/06/24
> 正式发布

**版本摘要**
本版本聚焦日志系统与 Storage 增强：新增 `EVENT` 日志级别（可被 WARNING+ 过滤）并统一日志配色，Storage 支持嵌套键访问；Docker 镜像全面国际化。

**升级建议**
- **建议升级**：日志降噪与 Storage 嵌套键访问为常规件收益

**注意事项**
- ⚠️ `Logger.message()` 更名为 `event()`：直接调用的第三方模块需同步更名

### 新增
- Storage 支持嵌套键访问（点号语法，中间层自动创建）
- 新增 `EVENT` 日志级别（等同 INFO），WARNING+ 即可过滤事件日志
- Docker 镜像国际化：entrypoint 五语言、locale 生成、`LANG`/`ERISPULSE_LANG` 自动检测与透传

### 变更
- 日志级别 `MESSAGE`(60) 更名为 `EVENT`(21)，行为改为等同 INFO；`message()` 方法随之更名为 `event()`
- 适配器事件日志按 OneBot12 事件类型分类显示

### 优化
- 日志配色统一至 `constants.py` 并关闭 Rich 自动高亮，降低视觉噪音
- 路由注册/注销日志降为 DEBUG 并新增 INFO 级摘要，批量操作不再刷屏
- Docker entrypoint 文案规范化（ASCII Banner、版本获取去重、失败输出错误日志）

---

## [2.5.0] - 2026/06/19
> 正式发布

**版本摘要**
2.5.0 版本定位为「生产就绪」版本，新增国际化（i18n）系统（5种语言）、严格模式加载策略、结构化日志（JSON 格式）、CLI 全面国际化、健康检查与就绪探针支持；移除含 C 扩展的三方依赖以提升 aarch64/ARM 等平台兼容性；修复 HTTP 客户端连接泄漏、热重载竞态等多个关键问题。这是 ErisPulse 首个面向正式生产环境的全功能大版本。

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 新增完整的国际化系统，SDK 及 CLI 全部内置文本支持 5 种语言（简体中文/繁体中文/英文/日文/俄文），自动检测用户语言环境
  - 新增严格模式加载策略（默认级别 1），拒绝未继承基类的模块/适配器，防止资源泄露
  - 新增 JSON 结构化日志输出，兼容 ELK/Grafana Loki/Datadog 等日志聚合系统，满足生产环境可观测性需求
  - 新增 `sdk.health` 健康检查与就绪探针，满足容器化部署场景的存活性探测
  - 移除含 C 扩展的三方依赖（watchdog/packaging），提升 aarch64/ARM 平台安装兼容性
  - 增强启动摘要输出（懒加载标注、禁用组件列表、严格模式拒绝清单）
  - 新增 CLI 命令别名体系与首次启动语言确认交互，开发者体验全面升级
  - 修复 HTTP 客户端响应体未预读导致的连接泄漏、热重载竞态等多个关键问题

**注意事项**
- ⚠️ **严格模式默认开启（级别 1）**：未继承 `BaseModule`/`BaseAdapter` 的组件默认会被拒绝跳过。如需加载旧组件，请通过配置 `[ErisPulse.framework] strict_mode_exceptions.modules/adapters` 豁免清单，或设置 `strict_mode = 0` 宽松模式

---

## [2.5.0-dev.4] - 2026/06/17
> 开发版本

**版本摘要**
2.5.0-dev.4 增强启动摘要输出（懒加载标注、禁用组件列表、严格模式拒绝清单）；修正 Core i18n 语言优先级链，`set_language()` / `epsdk i18n` 全局持久化对 SDK 运行时生效。

### 新增
- @wsu2059q
  - `Core/logger.py` `print_tree_item` 新增 `tag` / `tag_style` 参数，支持树状项尾部标注样式化标签（如 `[懒加载]`）
  - `loaders/strict.py` `StrictModeManager` 新增与级别无关的 `_rejections` 拒绝追踪列表：
    - `decide()` 返回拒绝时记录（包括 Level 1）
    - `record_failure()` 始终记录拒绝（与致命 `_violations` 分离）
    - `rejections` 属性供摘要阶段展示被拒组件清单
  - `sdk.py` 初始化完成阶段摘要增强：
    - 模块树每项标注 `[懒加载]` / `[立即加载]` 标签
    - 新增「已禁用适配器」/「已禁用模块」显示行
    - 新增「严格模式已拒绝」段，逐项列出被拒组件及原因
  - `Core/i18n/__init__.py` 全局持久化语言能力：
    - `_load_global_language()` 从 `~/.erispulse/cli_state.json` 读取 `epsdk i18n` 设置
    - `set_language()` 默认同时写入全局持久化（不需额外参数），调用后跨项目跨重启生效
    - `_persist_global_language()` 写入全局状态文件，保留已有键（如 `lang_hint_count`）
    - 新优先级链：`set_language()` > `ERISPULSE_LANG` 环境变量 > 全局持久化 > 项目配置
  - 5 个语言文件新增 `core.sdk.init.tag_lazy`、`tag_eager`、`disabled_adapters`、`disabled_modules`、`strict_rejected`、`strict_rejected_reason` 翻译键
  - `tests/unit/test_unit_strict_mode.py` 新增 5 个拒绝追踪测试
  - `tests/unit/test_unit_i18n.py` 新增 4 个语言优先级测试

### 变更
- @wsu2059q
  - Core i18n 语言检测优先级调整：`epsdk i18n` / `set_language()` 的全局持久化选择 > 项目 `ErisPulse.i18n.language` 配置
  - `set_language()` 行为变更：调用即持久化到全局状态文件，不再仅内存生效。临时覆盖请用 `ERISPULSE_LANG` 环境变量

---

## [2.5.0-dev.3] - 2026/06/17
> 开发版本

**版本摘要**
2.5.0-dev.3 引入「严格模式」加载策略，默认拒绝未继承基类的模块/适配器，避免上下文系统与兑底清理的资源泄露；补齐适配器加载器缺失的 `BaseAdapter` 继承检查，并同步更新配置文档。

### 新增
- @wsu2059q
  - `loaders/strict.py` 新增严格模式管理模块：
    - `StrictModeManager` 统一处理加载合规性判定与违规收集，三级策略：
      - `0` 宽松（违规仅警告，未继承基类的组件仍尝试加载）
      - `1` 严格-跳过（默认，拒绝未继承基类的组件并跳过，其余正常启动）
      - `2` 严格-致命（收集所有违规后统一报告并中止整个启动）
    - `StrictModeError` 致命异常、`Violation` 违规记录、`StrictModeLevel` 级别枚举
    - `decide()` 用于「未继承基类」这类可容忍/可拒绝的违规判定
    - `record_failure()` 用于异常类失败的致命记录（调用方已自行跳过）
    - `raise_if_fatal()` 在检查点统一输出违规清单并抛出
  - `loaders/adapter.py` 新增 `BaseAdapter` 继承检查（与模块对称）：
    - 加载阶段校验适配器是否继承 `BaseAdapter`，不合规时按严格模式判定
  - `loaders/bases/loader.py` 新增严格模式管理器注入接口：
    - `set_strict_manager()` 由初始化协调器注入共享实例
    - `_strict()` 访问器，未注入时从配置创建（兼容独立调用/测试）
  - `Core/constants.py` 新增 `DEFAULT_STRICT_MODE = 1` 常量
  - `runtime/frame_config.py` 新增 `[ErisPulse.framework]` 配置项：
    - `strict_mode`（默认 1）
    - `strict_mode_exceptions.modules` / `strict_mode_exceptions.adapters` 豁免清单
  - `sdk.py` 初始化协调器创建共享严格模式管理器并注入两个加载器，确保跨加载器收集违规；在加载阶段与注册阶段后各设一个中止检查点
  - 5 个语言文件（en/zh-CN/zh-TW/ja/ru）新增严格模式相关翻译键
  - `tests/unit/test_unit_strict_mode.py` 新增 15 个单元测试（三级行为/豁免清单/跨加载器收集/检查点报告）

### 变更
- @wsu2059q
  - `loaders/module.py` 未继承 `BaseModule` 的模块不再静默警告后加载，改为交由严格模式判定容忍或拒绝
  - 严格模式默认开启（级别 1）：未继承基类的组件默认会被拒绝跳过，需加载旧组件时通过豁免清单或调为宽松模式
  - 严格模式拒绝日志现给出可操作提示（加入 `strict_mode_exceptions` 豁免清单或设置 `strict_mode = 0`）
  - 加载/注册/初始化阶段的异常处理新增严格模式记录，在致命级别下纳入统一报告

### 修复
- @wsu2059q
  - 适配器加载器此前完全未检查是否继承 `BaseAdapter`，现补齐与模块对称的基类校验

### 文档
- @wsu2059q
  - `docs/zh-CN/user-guide/configuration.md` 同步更新：
    - 框架配置新增「严格模式」小节（级别表、行为差异、豁免清单用法）
    - 补充 `uninit_timeout`、`logger.format`、`i18n.language` 等缺失字段
    - 修正 `case_sensitive` 默认值（由错误的 `false` 改为实际默认 `true`）
    - 新增「国际化配置」整节

---

## [2.5.0-dev.2] - 2026/06/15
> 开发版本

**版本摘要**
2.5.0-dev.2 移除含 C 扩展的三方依赖以提升 aarch64 等平台兼容性，新增语言切换命令与首次启动语言确认提示，完善 CLI 工具层国际化

### 新增
- @wsu2059q
  - `CLI/utils/file_watcher.py` 新增纯 Python 文件变更监控模块：
    - `PollingObserver` 通过定期比较 .py 文件 mtime 检测变更，不依赖任何 C 扩展
    - `FileSystemEventHandler` / `FileChangeEvent` 提供与 watchdog 一致的事件接口
  - `CLI/commands/language.py` 新增 `epsdk i18n` 命令（别名 `language` / `lang`）：
    - 交互式选择语言或直接指定语言代码切换（如 `epsdk i18n en`）
    - 支持 `--list` 列出所有支持的语言
  - `CLI/cli.py` 新增首次启动语言确认提示：
    - 同时展示全部支持语言，确保检测错误时用户仍能看懂
    - 前 5 次启动时提醒，括号内显示倒计时（此提示将在 x 次启动后静默消失）
    - 当前语言行高亮显示
  - `CLI/i18n/__init__.py` 新增：
    - 语言选择持久化（`~/.erispulse/cli_state.json`），跨会话保留用户选择
    - `t_in()` 方法获取指定语言的翻译，用于多语言同时展示
    - 语言提示计数器（`get_lang_hint_shown_count` / `increment_lang_hint`）
    - `LANGUAGE_NAMES` 常量映射语言代码到显示名称
  - `CLI/utils/package_manager.py` 新增 `_version_key()` 内置版本比较：
    - 遵循项目命名规则排序：正式版 > rc > beta > alpha > dev
    - 支持 `2.5.0-dev.1`、`2.5.0a1`、`2.4.5` 等格式

### 变更
- @wsu2059q
  - `CLI/commands/run.py` 热重载改用 `utils/file_watcher.PollingObserver`，不再依赖 watchdog
  - `CLI/cli.py` 帮助文本的「命令」/「选项」标题改为通过 i18n 获取
  - `CLI/utils/display.py` 全部硬编码中文改为通过 i18n 获取（翻页导航、确认提示等）
  - `CLI/utils/package_manager.py` 全部硬编码中文改为通过 i18n 获取
  - `CLI/i18n/locales/` 5 个语言文件新增语言确认提示、display 工具、package_manager 工具相关翻译键
  - `CLI/i18n/__init__.py` 语言优先级调整：显式选择 > `ERISPULSE_LANG` 环境变量 > 持久化选择 > 自动检测
  - `Core/Event/command` 支持设置多个前缀匹配

### 移除
- @wsu2059q
  - 移除 `watchdog` 三方依赖（含 C 扩展，在 aarch64 等平台可能无预编译 wheel 导致安装失败）
  - 移除 `packaging` 三方依赖（仅用于版本比较，已由内置 `_version_key()` 替代）

### 优化
- @wsu2059q
  - 减少第三方依赖数量，提升 aarch64/ARM 等无预编译 wheel 平台的兼容性
  - CLI 工具层完全国际化，所有用户可见文本支持 5 种语言

---

## [2.5.0-dev.1] - 2026/06/15
> 开发版本

**版本摘要**
2.5.0-dev.1 为框架添加完整的国际化（i18n）支持，覆盖所有内置文本

### 新增
- @wsu2059q
  - `Core/i18n/` 新增国际化模块，支持 5 种语言：
    - zh-CN（简体中文）、zh-TW（繁体中文）、en（英文）、ja（日文）、ru（俄文）
    - 内置 271 个翻译键，覆盖 SDK 初始化/反初始化、适配器管理、模块管理、路由服务器、生命周期、
      存储、配置、HTTP 客户端等全部核心模块的运行时消息
    - 自动检测用户语言环境，按就近原则映射：zh-TW/HK/MO → 繁体，其他 zh* → 简体，en* → 英文等
    - 跨平台语言检测：Windows 优先使用 `GetUserDefaultLocaleName` API，
      Unix/macOS 优先使用环境变量 `LANG`/`LC_ALL`
    - 专用环境变量 `ERISPULSE_LANG` 最高优先级，支持测试时快速切换语言：
      `$env:ERISPULSE_LANG="en"`
    - 外部模块可通过 `i18n.register()` 注册自定义翻译，通过 `i18n.unregister_domain()` 卸载
  - `Core/i18n/locales/` 内置翻译数据包，每种语言一个独立文件
  - `CLI/i18n/` 新增 CLI 独立国际化模块，与 Core i18n 完全解耦：
    - 内置 253 个翻译键，覆盖 create/init/install/list/run/self-update/uninstall/upgrade 等全部命令
    - 纯内部使用，外部模块不应直接依赖
  - `runtime/config_schema.py` 新增 `I18nConfig` dataclass，支持 WebUI 配置
  - `runtime/frame_config.py` 新增 `[ErisPulse.i18n] language` 配置项（默认 `auto`）
  - `Core/constants.py` 新增 `DEFAULT_I18N_LANGUAGE` 常量
  - `tests/unit/test_unit_i18n.py` 新增 48 个单元测试（语言检测/就近映射/翻译查找/注册功能/Windows API）

### 变更
- @wsu2059q
  - `sdk.py` 及全部 Core 模块运行时中文文本改为通过 `i18n.t()` 获取翻译
  - `loaders/adapter.py` 及 `loaders/module.py` 运行时中文文本改为通过 `i18n.t()` 获取翻译
  - `CLI/cli.py` 及全部 CLI 命令运行时中文文本改为通过 `CLI.i18n.t()` 获取翻译
  - `Core/__init__.py` 导出 `i18n` / `I18nManager`
  - `sdk.py` 新增 `sdk.i18n` 属性，与 `sdk.logger`、`sdk.config` 同级
  - `tests/unit/test_unit_adapter.py` 4 个测试适配 i18n 输出

### 内部
- @wsu2059q
  - `Core/i18n/__init__.py` 优化跨平台语言检测，Windows 优先系统 API 避免 Git Bash 等工具覆盖 `LANG`
  - 将 `i18n.t()` 的 `key` 参数改为仅位置参数（`/`），解决翻译值含 `{key}` 占位符时的参数冲突

---

## [2.5.0-dev.0] - 2026/06/08
> 开发版本

**版本摘要**
2.5.0 定位为「生产就绪」版本，新增健康检查/就绪探针、结构化日志、优雅关闭超时等

### 新增
- @wsu2059q
  - `Core/logger.py` 新增 JSON 结构化日志支持：
    - 新增 `Logger.set_json_format(enabled)` 方法
    - 新增 `_JsonFormatter` 格式化器，输出 `{"timestamp", "level", "logger", "message"}` JSON
    - 通过 `config.toml` 中 `[ErisPulse.logger] format = "json"` 启用
    - 兼容 ELK / Grafana Loki / Datadog 等日志聚合系统
  - `Core/router.py` 新增 `/robots.txt` 端点，禁止所有主流爬虫/AI 爬虫收录路由
  - `Core/logger.py` 新增 TRACE (5) / MESSAGE (60) 自定义日志等级：
    - TRACE (5)：比 DEBUG (10) 更低，用于最细粒度调试
    - MESSAGE (60)：高于 CRITICAL (50)，用于消息收发日志，不受日志级别过滤影响
  - `Core/constants.py` 新增 `TEXT_BASED_METHODS = frozenset({"Text", "Markdown", "Html"})`
  - `Core/adapter.py` 新增 `[Recv]` 消息接收日志（MESSAGE 级别），显示 `platform/detail_type(user_id): content`
  - `Core/Bases/adapter.py` 新增 `[Send]` 消息发送日志（MESSAGE 级别），显示 `platform/method -> target: content`
    - 文本类方法（Text/Markdown/Html）显示消息内容
    - 非文本方法仅显示方法名和目标
    - Send/Recv 日志统一使用 `[Message]` 子 logger，前缀一致
  - `Core/Bases/adapter.py` 新增 `_wrap_send_method` 钩子注入机制：
    - 自动为 `SendDSL` 非链式发送方法注入 `message.sending` / `message.sent` 生命周期钩子
    - 新增 `SendDSL.__getattribute__`，自动包装返回 `asyncio.Task` 的方法
    - `_CHAIN_MODIFIER_NAMES` frozenset 跳过链式修饰方法（At/AtAll/Reply/To/Using/Account）
  - `Core/Event/wrapper.py` 交互方法新增 `method` 参数：
    - `confirm(prompt, ..., method="Text")` 支持非文本方式发送确认提示
    - `choose(prompt, options, ..., method="Text")` 文本类方法合并选项到一条消息，富媒体方法拆分为两条
    - `collect(fields, ...)` 每个 field 支持 `method` 键指定发送方式
    - `wait_reply(prompt, ..., method="Text")` 支持指定发送方法
  - `Core/Event/wrapper.py` 新增 `Event.__getattribute__`，平台方法优先于内置方法生效
  - `Core/Event/wrapper.py` 新增 `_builtin_wait_reply` / `_builtin_confirm` / `_builtin_choose` / `_builtin_collect` 模块级函数，供覆写方回退调用
  - `CLI` 命令别名体系，支持短命令快速调用：
    - `create`→`c`/`new`、`install`→`i`/`add`、`uninstall`→`rm`/`remove`、`upgrade`→`up`、`self-update`→`su`/`update`、`list`→`l`/`ls`、`list-remote`→`lr`、`run`→`r`、`init`→`ini`
    - `Command` 基类新增 `aliases` 类属性；命令注册表新增 `resolve()`/`list_aliases()` 别名解析与冲突保护（首注册优先）
  - `CLI/utils/package_manager.py` 新增 `--no-uv` 标志（install/uninstall/upgrade/self-update/init），强制使用 pip；同时支持 `ERISPULSE_NO_UV` 环境变量
  - `CLI/commands/init.py` 新增 `--here` 标志与交互提示，支持在当前目录初始化项目
  - `CLI/utils/display.py` 新增 `prompt_validated()` 输入校验循环辅助方法
  - 新增 CLI 单元测试套件（`tests/unit/test_unit_cli.py`，61 个测试），覆盖命令注册/发现、参数解析、命令路由与别名体系

### 优化
- @wsu2059q
  - `CLI/utils/package_manager.py` 安装路由优化：
    - 优先使用独立 uv 二进制（`shutil.which("uv")`），其次回退 `python -m uv`，最后回退 pip
    - `_get_target_python()` 解析 `VIRTUAL_ENV`，确保依赖安装到活动虚拟环境
  - `CLI/commands/{create,init}.py` 校验失败时保留输入重新提示，而非 `sys.exit` 直接退出
  - `CLI` 全系统补充符合文档字符串规范的注释

### 变更
- @wsu2059q
  - `sdk.Uninitializer.uninit()` 重构为异步超时控制：
    - 反初始化主体由 `asyncio.wait_for()` 包装
    - 超时后记录 WARNING 并返回 `False`，允许进程继续退出
    - 0 表示不设超时（保留行为兼容）
  - `Core/logger.py` `_log` / `LoggerChild._log` 改用 `self._logger.log()` 替代 `getattr(self._logger, level_name)`，支持自定义日志等级
  - `Core/Event/wrapper.py` `register_event_mixin` / `register_event_method` 允许覆写所有内置方法名，不再做冲突检测
  - `Core/Event/wrapper.py` `Event.reply()` 中的 `message.sending` / `message.sent` 生命周期钩子下沉至 `SendDSL.__getattribute__`，所有适配器发送操作均触发

### 移除
- @wsu2059q
  - `Core/Event/wrapper.py` 移除命名冲突检测：
    - 移除 `_ALLOW_OVERRIDE_NAMES`、`_get_event_builtin_names()` 
    - 移除相关 `warnings` 导入

### 修复
- @wsu2059q
  - 修复 HTTP 客户端请求后响应体未预读导致的连接泄漏问题
  - `CLI/commands/run.py` 重构热重载机制，修复多个问题：
    - 进程因错误（语法错误/异常）退出时不再终止整个 CLI，改为等待下次文件变更后自动重启
    - 修复正常重载（进程运行中保存文件）时误报「进程异常退出」的竞态：文件监控线程不再直接操作子进程，仅发出重载信号，终止/重启统一由主线程处理
    - 修复重载等待状态下 Ctrl+C 无响应（事件等待无超时阻塞信号处理），改为轮询等待
  - 修复 `tests/unit/test_unit_client.py` 陈旧测试（响应体 `read` 未设为 `AsyncMock`、`close` 行为断言与实现不符）

---

## [2.4.9] - 2026/06/12
> 正式发布

**版本摘要**
2.4.9 修复适配器热重载时路由冲突导致重载失败的关键问题。框架自动管理适配器生命周期资源（路由/事件/命令），与模块卸载对齐颗粒度。

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 修复第三方模块（如 Dashboard）触发适配器热重载时，因旧路由未清理导致 `WebSocket路径 ... 已注册` 冲突、重载失败的问题
  - 修复适配器启动失败重试时，残留路由同样导致冲突的问题
  - 新增框架级 `adapter.restart(platform)` API，第三方模块无需自行管理适配器重载生命周期

**注意事项**
- 适配器热重载现在由框架统一处理资源清理，第三方模块应调用 `sdk.adapter.restart(platform)` 而非直接操作适配器实例
- 需重启进程使本版本生效（旧版本注册的路由无 owner 归属记录）

### 新增

- @wsu2059q
  - `Core/router.py` 新增路由归属者追踪与按 owner 清理机制：
    - 新增 `_owner_namespaces: dict[str, set[str]]` 映射，在路由注册时自动记录 `current_owner → namespace` 归属关系
    - 新增 `_track_owner_namespace(namespace)` 内部方法，读取 `current_owner` ContextVar 建立归属记录
    - HTTP / WebSocket / SSE 路由注册（`register_http_route` / `_register_ws_endpoint` / `_register_sse`）在重复检查后自动调用归属追踪
    - 新增 `unregister_all_by_owner(owner)` 公开方法，按归属者清理其名下所有命名空间的路由（适用于"以平台名为 owner、用细颗粒度命名空间注册"的场景）
  - `Core/adapter.py` 新增 `restart(platform)` 框架级适配器重载 API：
    - 自动执行 shutdown + 资源兜底清理 + owner 注入启动 的完整生命周期
    - 提交 `adapter.status.change` 事件（stopping / starting / started）
    - 启动失败时自动回滚（停止 + 清理本次注册的资源），避免下次冲突
    - 第三方模块的热重载应调用本方法，而非直接操作适配器实例
  - `Core/adapter.py` 新增 `_stop_adapter(platform)` 内部原语（"停止即清理"）：
    - 将"停止适配器"与"回收其注册的资源"绑定在一次调用里
    - 调用适配器自身 `shutdown()` 后立即清理路由/事件/命令（幂等）
    - `restart()` 和启动失败重试均经此入口，保证适配器一旦停止、归属资源必被回收
  - `Core/adapter.py` 新增 `_cleanup_adapter_resources(platform)` 内部方法：
    - 同时清理以平台名为命名空间注册的路由（`unregister_all_by_namespace`）和以平台名为 owner 注册的路由（`unregister_all_by_owner`）
    - 清理 `command` / `message` / `notice` / `request` / `meta` 下按 owner 注册的事件处理器和命令

### 变更

- @wsu2059q
  - `Core/adapter.py` `_run_adapter()` 在调用 `adapter.start()` 期间注入 `current_owner.set(platform)`，使适配器注册的路由/事件处理器自动归属到该平台（与模块加载对齐）
  - `Core/adapter.py` `restart()` / 启动失败重试路径在重新启动前调用 `_stop_adapter(platform)`，保证旧资源已回收
  - `Core/adapter.py` `shutdown()` 新增逐平台 `_cleanup_adapter_resources(platform)` 调用，覆盖以平台名为 owner 注册的细颗粒度命名空间路由
  - `Core/router.py` `unregister_all_by_namespace()` 在清理命名空间后同步从所有 owner 索引中移除该命名空间的归属记录
  - `Core/router.py` `clear()` 重置 `_owner_namespaces`

### 修复

- @wsu2059q
  - 修复适配器热重载时因旧路由（如 `onebot11_default`）未清理导致 `WebSocket路径 ... 已注册` 冲突、重载失败的问题：
    - **根因**：`AdapterManager.shutdown()` 仅以 `unregister_all_by_namespace(platform)` 清理路由，但适配器（如 OneBot11）以 `onebot11_{account_name}` 为命名空间注册 WS 路由，颗粒度不匹配导致清理为空操作
    - **方案**：路由注册时通过 `current_owner` 自动追踪 owner→namespace 归属，停止/重启时同时按 owner 清理，覆盖细颗粒度命名空间
  - 修复适配器启动失败重试时，上次尝试注册的残留路由同样导致冲突的问题（重试路径现经 `_stop_adapter` 清理）

---

## [2.4.8] - 2026/06/12
> 正式发布

**版本摘要**
2.4.8 是一个 HTTP/WS 客户端稳定性和适配器重连可靠性修复版本。

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 修复 WebSocket 客户端并发 `receive()` 导致 `Concurrent call to receive() is not allowed` 崩溃
  - 修复 HTTP 客户端连接错误重试时 session 泄漏（`_drain_sessions` 未关闭旧连接）
  - 修复 HTTP 请求异常处理顺序错误导致连接重试 + session 重建逻辑从未执行（死代码）
  - 修复适配器重连竞态导致 `Cannot write to closing transport`

**注意事项**
- `ClientWebSocket.send_*()` 现在会在连接已关闭时抛出 `WebSocketError` 而非底层 aiohttp 异常

### 修复

- @wsu2059q
  - 修复 `Core/client.py` `ClientWebSocket` 多个协程并发调用 `receive()` 导致 aiohttp 抛出 `Concurrent call to receive() is not allowed` 异常：
    - 新增 `_recv_lock` (asyncio.Lock) 序列化所有 `receive()` / `receive_text()` / `receive_bytes()` 调用
  - 修复 `Core/client.py` `_get_http_session()` / `_get_ws_session()` 并发调用可能创建多个 aiohttp session 导致连接泄漏：
    - 新增 `_session_lock` (asyncio.Lock) 保护 session 创建
  - 修复 `Core/client.py` `_drain_sessions()` 仅置空引用未关闭底层 session 导致连接泄漏：
    - 改为异步方法，先释放锁再安全关闭旧 session
  - 修复 `Core/client.py` `request()` 异常处理顺序错误：
    - `except ClientConnectionError` 捕获 ErisPulse 异常（永不触发），aiohttp 连接错误被通用 `except Exception` 接住
    - 连接重试 + session 重建逻辑（`_drain_sessions`）从未执行
    - 重构为按 `asyncio.TimeoutError` → `aiohttp.ClientConnectionError`（触发 session 重建）→ `aiohttp.ClientError` → `ClientError`（透传）→ `Exception` 顺序捕获
  - 修复 `Core/client.py` `ClientWebSocket.send_json()` 忽略 `mode` 参数，`mode="binary"` 时仍以文本模式发送
  - 修复 `Core/client.py` `_get_ws_session()` 未传入 `self._default_headers`，WS 连接不携带全局默认请求头
  - 修复 `Core/client.py` `close()` 与并发请求/WS 连接的竞态条件，改为锁保护
  - 修复 `Core/client.py` `HttpResponse.__aexit__` 在 `request()` 返回后重复调用 `release()`：
    - 新增 `_released` 标记，`request()` 退出 `async with` 后标记已释放

---

## [2.4.7] - 2026/06/11
> 正式发布

**版本摘要**
2.4.7 是一个在2.5.x系列发布之前进行功能修复的补丁版本

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 修复部分场景下 client 在进行轮询/post时未预读响应体，导致连接泄漏/信息丢失的错误

---

## [2.4.6] - 2026/06/08
> 正式发布

**版本摘要**
2.4.6 版本是一个重大功能更新版本，主要新增了声明式配置管理系统、WebSocket 客户端共享基类、ErisPulse 统一异常体系、SSE 服务端推送支持、路由发现功能；重构了适配器开发体验为声明式配置风格；增强了 SQL 注入防护和模块属性安全校验；修复了服务重启后 WebSocket 连接挂起、存储空值混淆等多个关键问题。

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 适配器开发体验全面升级：声明式配置、一行发送 meta 事件、标准化响应构造
  - 新增 SSE 支持，满足实时推送场景需求
  - 路由发现功能便于动态获取 API 信息
  - 安全增强：SQL 标识符白名单校验、模块属性保护、代理凭证脱敏
  - 修复多个服务重启相关的关键问题

**注意事项**
- ⚠️ **配置迁移**：适配器配置现已迁移至声明式 `ConfigClass` / `AccountConfigClass`，旧版适配器需要更新(不更新也没关系~会兼容的喔)
- ⚠️ **模块命名规范**：模块名称禁止使用 `_` 前缀和与 SDK 保留属性（如 `logger`、`config`）冲突的名称

---

## [2.4.6-dev.6] - 2026/06/07
> 开发版本

### 新增
- @wsu2059q
  - `Core/Bases/websocket.py` 新增 `WebSocketConnectionBase` 共享基类和 `WSMessage` 消息类型：
    - 客户端和服务端 WebSocket 共享 send/receive/iter/close 接口
    - `WSMessage` 统一消息抽象（TEXT / BINARY / CLOSE / ERROR）
    - iter_text/iter_bytes/iter_json 自动在断开时停止迭代
    - on_disconnect/on_error 生命周期回调
  - `Core/Bases/errors.py` 新增 ErisPulse 异常体系：
    - `ErisPulseError` → `ClientError`（`ClientConnectionError` / `ClientTimeoutError` / `HTTPStatusError`）→ `WebSocketError` → `WebSocketDisconnect`
    - 通过 `sdk.client` 发起的请求自动将 aiohttp 异常转换为 ErisPulse 异常
  - `Core/Bases/client.py` 新增 `BaseClientWebSocket` 抽象基类
  - `Core/client.py` 新增 WebSocket 客户端：
    - `ClientWebSocket`：基于 aiohttp 的 WS 客户端连接封装
    - `HttpClient.ws_connect()`：建立 WebSocket 连接，支持 heartbeat 参数
    - 触发 `client.ws.connect` 生命周期事件
  - `runtime/config_schema.py` 新增 dataclass 配置 Schema 系统：
    - `AdapterConfig` / `BotAccountConfig` 配置基类
    - `dataclass_to_toml_with_comments()` 生成带注释的 TOML 模板
    - `dict_to_dataclass()` / `validate_config()` / `get_config_schema()` 工具函数
  - `Core/Bases/adapter.py` BaseAdapter 新增声明式配置管理：
    - `ConfigClass` / `AccountConfigClass` 类属性声明配置类
    - `self.config` / `self.accounts` / `self.enabled_accounts` 属性自动加载
    - `emit_meta()` 便捷方法一行发送 meta 事件
    - `make_response()` / `make_error()` 构造标准化响应
    - `_resolve_account()` 自动解析多账户
    - `on_config_update()` 配置热更新回调
  - `Core/constants.py` 新增 WS 客户端默认常量
  - `Core/router.py` 新增路由发现与 SSE 支持：
    - `get_module_routes(module_name)` 获取命名空间详细路由信息（HTTP 方法、WS 认证、SSE 流式标记）
    - `get_module_urls(module_name)` 获取命名空间完整连接 URL（自动转换 ws:// / wss://）
    - `get_module_urls_matching(prefix)` 按前缀聚合多命名空间路由（兼容多账户适配器）
    - `list_namespaces()` 返回值新增 `"sse"` 键
    - `register_sse()` / `@sse` 装饰器 / `RouteGroup.sse()` 注册 SSE 端点
    - `unregister_sse()` 取消注册 SSE 路由
    - `unregister_all_by_namespace()` 清理统计新增 `"sse_count"`
  - `Core/Bases/router.py` 新增 `SseEmitter` 服务器无关 SSE 协议实现：
    - `send(data, event, id, retry)` 自动格式化 SSE 协议（非 str 数据自动 JSON 序列化）
    - `close()` / `closed` 优雅连接管理
    - `request` 属性访问底层 HTTP 请求
    - 通过 `on_send` / `on_close` 回调与服务器层解耦
  - `Core/adapter.py` 新增 `get_connection_info(platform)` 适配器连接信息查询：
    - 聚合 base_url、HTTP/WS/SSE 路由的完整 URL
    - 精确匹配优先，无结果时自动按前缀聚合

### 变更
- @wsu2059q
  - `WebSocketConnection` 改为继承 `WebSocketConnectionBase`，通用接口移至基类
  - `WebSocketDisconnect` 从 `Bases/router.py` 移至 `Bases/errors.py`（旧导入路径兼容）
  - `HttpClient` / `HttpResponse` / `ClientWebSocket` 继承对应抽象基类
  - `HttpResponse.text()` / `json()` 改为基于 `read()` 缓存实现，不再依赖 aiohttp 原生方法
  - `BaseAdapter.__init__(self, sdk=None)` 接受 sdk 参数，自动初始化 logger / config / accounts
  - 适配器注册时自动注入 `instance._platform`
  - 生命周期事件 `client.request` 更名为 `client.request.success`
  - HTTP 请求异常分类处理：`ClientConnectionError` 重建 session 重试，`TimeoutError` 独立重试
  - `WebSocket` 路由存储元组从 `(handler, auth_handler)` 扩展为 `(handler, auth_handler, auto_accept)`，确保服务重启后 `auto_accept` 标志不丢失
  - `loaders/strategy.py` `ModuleLoadStrategy.__getattr__` 不存在的属性现在抛出 `AttributeError` 而非静默返回 `None`
  - `config/config.toml` 清除所有硬编码凭证，替换为占位符值
  - `.gitignore` 新增 `config/config.toml`、`config/config.db` 等敏感配置文件排除规则

### 安全
- @wsu2059q
  - `Core/storage.py` 新增 SQL 标识符（表名/列名/列类型）白名单校验，防止 SQL 注入：
    - 新增 `_validate_identifier()` 函数，仅允许 `^[a-zA-Z_][a-zA-Z0-9_]*$` 格式
    - 新增 `_validate_column_type()` 函数，拒绝包含分号、注释符等危险字符的类型定义
    - 所有 `Table()`、`CreateTable()`、`DropTable()`、`AlterTable()`、`Select()`、`Insert()`、`Update()`、`OrderBy()` 入口添加校验
  - `CLI/utils/package_manager.py` 移除 SSL 证书验证静默降级逻辑，检测到代理时不再以 `ssl.CERT_NONE` 重试
  - `CLI/utils/package_manager.py` 新增 `_sanitize_proxy_url()` 方法，脱敏代理 URL 中的用户名/密码，防止凭证泄露到控制台
  - `loaders/module.py` 新增 SDK 属性名安全校验：
    - 新增 `_RESERVED_SDK_ATTRS` 保留属性集合，禁止模块覆盖 `logger`、`config`、`__class__` 等关键属性
    - 新增 `_validate_sdk_attr_name()` 函数，拒绝 `_` 前缀、不符合标识符规范、与保留属性冲突的模块名称
    - `initialize_modules()` 在 `setattr(sdk_instance, ...)` 之前强制校验
  - `Core/Bases/storage.py` 修复 `BaseStorage.__setattr__` 静默吞没后端写入失败的问题：移除 `except` fallback，让异常正常传播

### 修复
- @wsu2059q
  - 修复 `BaseStorage.get_multi()` / `__getattr__()` 将存储值 `None` 与键不存在混淆的问题：引入 `_SENTINEL` 哨兵值区分
  - 修复 `loaders/adapter.py` 异常处理捕获 `BaseException` 导致 `KeyboardInterrupt`（Ctrl+C）被静默吞没的问题
  - 修复 `loaders/module.py` `LazyModule._init_failed` 属性未在 `__init__` 中初始化，导致 `hasattr` 检查脆弱的问题
  - 修复 `Core/client.py` `_convert_aiohttp_exception` 中重复 `return` 死代码
  - 修复 `CLI/commands/install.py` 适配器交互安装表格定义 5 列但 `row_builder` 只提供 4 值导致 Rich 报错或显示错乱的问题
  - 修复 `Core/router.py` `_restore_routes_from_records` 中 `auto_accept` 硬编码为 `False`，导致服务重启后所有 WebSocket 路由 `auto_accept` 丢失、连接挂起的问题
  - 修复 `Core/Bases/router.py` `SseEmitter.send()` 数据分割不处理 `\r\n`（Windows 换行符），可能导致部分 SSE 客户端解析异常的问题
  - 修复 `CLI/commands/create.py` LICENSE 模板硬编码年份 `"2026"`，导致后续年份生成错误版权日期的问题

### 文档
- @wsu2059q
  - HTTP 客户端文档 → HTTP/WS 客户端文档，新增 WebSocket 客户端和异常体系章节
  - 适配器开发文档更新为声明式配置风格（ConfigClass / emit_meta / make_response）
  - 示例适配器 `MyAdapter` 全面重构，展示新 API 用法
  - 适配器开发文档新增「连接信息与路由发现」和「SSE 支持」章节
  - `core-concepts.md` WebSocket/WebHook 示例移除 FastAPI 类型注解依赖
  - `best-practices.md` 新增连接信息暴露和 `module_name` 一致性说明

---

## [2.4.6-dev.5] - 2026/06/03
> 开发版本

### 新增
- @wsu2059q
  - `Core/client.py` 新增基于 aiohttp 的 HTTP 客户端模块：
    - `HttpClient` 类：提供 `get`/`post`/`put`/`delete`/`patch`/`request` 异步方法
    - `HttpResponse` 类：封装响应对象，支持 `read()`/`text()`/`json()`，自动缓存响应体
    - 支持自定义 timeout、connect_timeout、max_retries、retry_delay、headers、user_agent
    - 自动记录请求日志和统计信息（`stats` 属性 / `reset_stats()` 方法）
    - 每次请求触发 `client.request` 生命周期事件，可用于监控
    - 支持上下文管理器（`async with HttpClient() as client:`）
  - `Core/__init__.py` 新增全局 HTTP 客户端单例 `client = HttpClient()`
  - `sdk.py` 注册 `client` 为核心属性，支持 `sdk.client` 动态访问
  - `Core/Bases/client.py` 新增抽象基类 `BaseHttpClient` 和 `BaseHttpResponse`，定义统一接口契约
  - `Core/Bases/server.py` 重命名为 `Core/Bases/router.py`，更准确反映路由抽象类型的定位
  - 新增 52 个 HTTP 客户端单元测试（`tests/unit/test_unit_client.py`）：
    - HttpResponse 属性、缓存、编码、上下文管理器
    - HttpClient 初始化默认值、快捷方法委托、统计、会话管理
    - request 核心逻辑：成功/失败/重试/耗尽重试/超时覆盖/参数传递/生命周期事件
  - 新增 48 个路由系统 + HTTP 客户端集成测试（`tests/integration/test_integration_router_client.py`）：
    - 核心端点（/health、/ping、/docs、/openapi.json）
    - HttpRequest 抽象类型自动注入（GET/POST/query_params/headers/url/raw/cookies）
    - FastAPI 原生类型透传、无注解自动注入、非 request 参数名行为
    - 装饰器路由（@http/@get/@post/@put/@delete）及路径参数
    - 路由组（RouteGroup）
    - HTTP 方法组合与 405 响应
    - 路由注册/注销/冲突检测/路径标准化/模块隔离
    - WebSocket 抽象类型注入、FastAPI 注解透传、JSON/bytes 收发、属性代理
    - WebSocket 认证（通过/失败）、装饰器 WS 路由
    - WebSocket 生命周期钩子（on_disconnect/on_error）

### 变更
- @wsu2059q
  - 路由抽象类型文件重命名：`Core/Bases/server.py` → `Core/Bases/router.py`
  - HTTP 客户端从抽象基类分离为独立实现模块：`Core/Bases/client.py`（抽象基类）→ `Core/client.py`（aiohttp 实现）
  - `Core/__init__.py` 从 `Core.client` 导入具体实现，从 `Core.Bases` 导入抽象基类，统一导出
  - `Core/router.py` 导入路径从 `.Bases.server` 更新为 `.Bases.router`
  - 所有文档示例统一使用 `from ErisPulse.Core import client` 作为推荐的 HTTP 客户端使用方式
  - 安装脚本下载方式从 Cloudflare Pages 改为 Worker 分发
  - slow-handler 日志优化：`wait_reply` 等待期间不再误触发 WARNING，改为 DEBUG 级别日志
  - slow-handler 日志现在显示具体业务模块（`owner=...`），而非笼统的 `CommandHandler._handle_message`
  - `runtime/context.py` 新增 `handler_waits` ContextVar（原 `_handler_wait_info` 重命名），去除私有前缀，公开化为跨模块契约
  - `Event/base.py:_invoke_handler` 去掉多余嵌套 try/finally，`_elapsed` 改在单一 finally 块计算
  - `Event/command.py:wait_reply` 去掉防御性创建 ContextVar list 的逻辑，未在 handler 内时直接跳过记录

### 文档
- @wsu2059q
  - 更新 `docs/zh-CN/getting-started/basic-concepts.md`：新增 Client（HTTP 客户端）章节，Router 章节展示抽象类型和 FastAPI 原生类型两种风格
  - 更新 `docs/zh-CN/api-reference/core-modules.md`：新增 HTTP Client 模块完整文档、抽象类型章节
  - 更新 `docs/zh-CN/advanced/http-client.md`：所有示例改为 `from ErisPulse.Core import client` 风格
  - 更新 `docs/zh-CN/advanced/router.md`：所有导入路径从 `ErisPulse.Core.Bases.server` 改为 `ErisPulse.Core`

---

## [2.4.6-dev.4] - 2026/06/01
> 开发版本

### 新增
- @wsu2059q
  - `sdk.py` 新增 `hard_restart()` 硬重启方法：
    - 执行完整 `uninit()` 反初始化后调用 `os._exit(42)` 退出进程
    - 由父进程（`epsdk run`）检测退出码 42 并自动启动新进程
    - 确保资源完全释放，避免热重启可能导致的资源泄漏
  - `CLI/commands/run.py` `_run_internal()` 重构为子进程管理模式：
    - 非 `--reload` 模式下以 `subprocess.Popen` 启动 SDK 子进程
    - 检测子进程退出码 42 时自动重新启动（硬重启循环）
    - `--reload` 热重载模式保持原有行为不变

### 变更
- @wsu2059q
  - 适配器/模块加载系统全面拦截 `SystemExit` 异常，防止第三方代码调用 `sys.exit()` 导致 Docker 容器意外退出

---

## [2.4.6-dev.2] - 2026/05/31
> 开发版本

### 新增
- @wsu2059q
  - `Core/constants.py` 集中管理框架内部硬编码常量（100+），每个常量附带使用位置和修改影响说明
  - `runtime/context.py` 运行时上下文追踪（`current_owner` ContextVar），支持按模块自动标记资源归属
  - `Event/base.py` `Event/command.py` 新增 `owner` 字段和 `unregister_by_owner()` 方法
  - `router.py` 主题化错误页面（4xx/5xx/unknown）和根路由 `/` 页面，Apple 式优雅设计
  - `web_status/` 移入 `src/ErisPulse/` 作为可分发包，`pyproject.toml` 已配置

### 变更
- @wsu2059q
  - `adapter.py` `shutdown()` 仅全量关闭时清空全局事件处理器
  - `module.py` `load()` 使用 `current_owner` 包裹实例创建；`_unload_single_module()` 和 `disable()` 新增按 owner 的事件处理器/命令/SDK属性清理
  - `adapter.py` / `module.py` `_is_base_*_subclass` 内联为 `_is_subclass` 静态方法
  - `sdk.py` 核心模块属性改为动态解析（`__getattr__`），软重启后自动获取最新单例
  - `lifecycle.py` 移除 `emit`/`emit_sync` 中的冗余调试日志
  - `runtime/exceptions.py` 异常处理增加 `AttributeError` 捕获

---

## [2.4.6-dev.3] - 2026/05/31
> 开发版本

### 变更
- @wsu2059q
  - `adapter.py` `emit()` 事件处理器分发从顺序 `await` 改为 `asyncio.create_task()` fire-and-forget 模式：
    - 新增 `_dispatch_handler_task()` 方法，将每个 OB12 handler 和 raw handler 包装为独立 `asyncio.Task`
    - 处理器执行不再阻塞 `emit()` 返回，防止单个慢处理器（如 `wait_reply`）阻塞整个事件分发链路
    - 自动捕获处理器异常并记录日志，`CancelledError` 静默处理
    - Task 创建失败时回退到 `asyncio.ensure_future()`

### 新增
- @wsu2059q
  - `Core/constants.py` 新增 `HANDLER_SLOW_THRESHOLD_SECS = 1.0` 常量（处理器执行耗时告警阈值）
  - `adapter.py` `_dispatch_handler_task()` 内置处理器执行耗时监控，超过阈值记录 WARNING
  - `Event/base.py` `_invoke_handler()` 新增处理器执行耗时监控，超过阈值记录 WARNING
  - `lifecycle.py` `_execute_handlers_async()` 慢处理器告警从硬编码 50ms 改为使用 `HANDLER_SLOW_THRESHOLD_SECS` 常量
  - `Event/command.py` `wait_reply()` 超时时记录 DEBUG 级别日志（包含 wait_key 和 timeout）

### 修复
- @wsu2059q
  - 修复 `adapter.emit()` 中 `_update_bot_status()` 调用括号错误导致离线状态无法正确设置的问题

---

## [2.4.6-dev.1] - 2026/05/26
> 开发版本

### 新增
- @wsu2059q
  - `SendDSL` 框架级 At/AtAll/Reply 修饰器实现：
    - `At(user_id)` / `AtAll()` / `Reply(message_id)` 已由 `SendDSL` 基类内置实现，适配器无需重复编写
    - 新增 `_apply_modifiers(message)` 辅助方法，自动将修饰器状态合并为 OneBot12 消息段列表
    - 新增 `send_context` 属性，显式返回 `{target_type, target_id, account_id}` 字典，替代隐式访问 `_target_type` / `_target_id` / `_account_id` 实例变量
    - 修饰器合并顺序：`mention_all` → `mention` → `reply` → 用户消息段
    - 现有适配器覆盖的 `At`/`AtAll`/`Reply` 方法不受影响（子类优先）
  - `lifecycle` 生命周期管理器全面增强：
    - 新增 `emit(event, data)` 异步触发和 `emit_sync(event, data)` 同步触发 API
    - 新增 `register(event, handler, priority)` 函数调用模式注册
    - 新增 `off(event, handler)` 取消注册、`clear()` 清除所有、`list_hooks()` 查询钩子
    - 支持优先级排序（数值越小越先执行）
    - 处理器返回非 None 值时可传递给后续处理器（数据链）
    - 内部存储从 `_handlers` 重构为 `_hooks`，存储 `(priority, handler)` 元组
  - `RequestDSL` 框架级请求操作 DSL 基类实现：
    - 新增 `RequestDSL` 基类，采用与 `SendDSL` 一致的工厂实例模式：`adapter.Request("req_id").accept()`
    - 新增 `__call__` 工厂方法，`adapter.Request(request_id)` 返回新的 `RequestDSL` 实例
    - 新增 `Using(account_id)` 方法，指定执行操作的 Bot 账号
    - 新增 `accept(**kwargs)` / `reject(**kwargs)` 公开方法，支持平台扩展参数（如 comment 备注）
    - 新增 `_do_accept` / `_do_reject` 内部方法，适配器子类重写实现平台逻辑
    - 基类默认返回 `retcode=10002`（不支持的操作），并记录 warning 级别日志
    - 新增 `request_context` 属性，返回 `{request_id, account_id}` 字典
  - `BaseAdapter.Request` 内部类 + 工厂实例：
    - `BaseAdapter` 新增 `Request` 内部类（继承 `RequestDSL`），与 `Send` 内部类对称
    - `BaseAdapter.__init__` 新增 `self.Request = self.__class__.Request(self)` 工厂初始化
  - `Event` 请求操作便捷方法：
    - 新增 `get_request_id()` 方法，获取请求事件标识
    - 新增 `approve(comment=None)` 异步方法，同意当前请求事件
    - 新增 `reject(comment=None)` 异步方法，拒绝当前请求事件
    - 新增 `_handle_request_action()` 内部方法，校验事件类型、平台适配器、request_id 后委托给 Request DSL
    - 缺少 `request_id` 时抛出 `ValueError`，引导适配器开发者正确设置字段
  - `Core.Bases.__init__` / `Core.__init__` 导出 `RequestDSL` 类
  - 新增 `docs/zh-CN/standards/request-action-spec.md` 请求操作标准文档

### 变更
- @wsu2059q
  - `SendDSL` 基类增强：
    - `__init__` 新增修饰器状态变量（`_at_user_ids`、`_reply_message_id`、`_at_all`），`To()`/`Using()` 创建新实例时自动重置
    - `BaseAdapter.Send.Raw_ob12` 文档字符串更新为推荐使用 `_apply_modifiers(message)` 和 `**self.send_context` 的新模式
  - `config` 配置变更监听从 `on_change` 回调改为统一生命周期钩子 `config.set`：
    - 移除 `on_change()` 回调注册 API
    - 移除 `AuditEntry` 数据类及相关导出
    - 改用 `lifecycle.emit_sync("config.set", {...})` 触发，可通过 `@lifecycle.on("config.set")` 监听
  - `sdk.py` 清理生命周期时使用 `_hooks` 替代旧版 `_handlers`
  - `request.py` 修正误导性文档字符串（「通过返回值控制」→「event.approve()/reject()」）
  - `docs` 更新中文适配器开发文档（getting-started / send-method-spec / event-conversion），展示 Request DSL 用法

### 移除
- @wsu2059q
  - `SendDSL` 移除 `_unimplemented_modifier()` 方法（`At`/`AtAll`/`Reply` 已有实际实现，不再需要 no-op 垫片）
  - `config` 移除配置审计系统：
    - 移除 `AuditEntry` 数据类（`config.py`、`Core/__init__.py`）
    - 移除 `enable_audit()`、`disable_audit()`、`get_audit_log()`、`clear_audit_log()` 方法
    - 移除 `_detect_caller()`、`_resolve_caller()` 调用方感知机制
    - 移除 `on_change()` 变更回调注册
    - 移除 `CLI init` 模板中 `[ErisPulse.config.audit]` 配置段
    - 移除 `test_unit_config.py` 中相关审计/回调测试用例

### 优化
- @wsu2059q
  - `adapter` 简化示例适配器和 CLI 脚手架模板：
    - 移除 `examples/example-adapter/MyAdapter/Core.py` 中 ~40 行 At/AtAll/Reply 样板代码
    - 更新 `CLI/commands/create.py` 的 `_ADAPTER_CORE` 模板，使用 `_apply_modifiers()` 和 `send_context`
  - 更新示例适配器 `examples/example-adapter/MyAdapter/Core.py`：添加 `super().__init__()`、`Request` 内部类
  - `docs` 更新中文适配器开发文档（getting-started / core-concepts / send-dsl / best-practices），展示新辅助方法用法
  - `docs` 核心模块文档：移除配置审计相关内容，更新生命周期文档为完整钩子参考
  - `docs` 事件系统文档：修正优先级方向说明
  - `docs` 架构文档：移除配置审计描述

---

## [2.4.6-dev.0] - 2026/05/24
> 开发版本

### 新增
- @wsu2059q
  - `CLI` 新增未验证模块标识：`list-remote`/`install`交互安装中未验证模块显示「（未验证）」标记，安装时弹出风险警告需确认

### 修复
- @wsu2059q
  - 修复 `adapter`/`module` 加载的启用状态检测在部分场景下可能失效的问题
  - 修复 `sdk.run` 的保持运行变量关闭的情况下，会导致继续运行代码`uninit`的bug

### 优化
- @wsu2059q
  - `docs` SQL 构建器文档：明确元组返回值、新增 `Where` 多参数用法说明
  - `docs` 发布文档：精简为 3 步流程，更新商店提交入口
  - `README` 新增 1Panel 应用商店安装方式
  - 优化 `logger` 的显示样式
  - 优化 `cli` 的显示样式，新增display辅助模块
  - 优化热重启（`sdk.restart()`）的缓存清理机制，确保更新后的模块/适配器/框架代码能正确生效：
    - 新增 `_invalidate_metadata_cache()` 清除 `importlib.metadata` 缓存
    - 新增 `_invalidate_framework_cache()` 清除 `ErisPulse.*` 子模块缓存
    - 增强诊断日志输出
  - 并入 `适配器启动` 到 `sdk.init`

---

## [2.4.5] - 2026/05/17
> 正式发布

**版本摘要**
2.4.5 版本是一个重大功能更新版本，主要新增了 Event 多 Bot 模式优化、配置审计系统、指标监控模块、路由系统全面增强（装饰器注册、路由分组、中间件、限流、CORS）、多轮对话扩展（分支/跳转/持久化）、模块依赖管理；重构了 SDK 生命周期为独立阶段（Router 启动从适配器解耦）；优化了日志调用方检测和 CLI 交互体验；修复了优先级加载、适配器中间件空返回、配置文件路径等多个关键问题。

**升级建议**
- **建议升级**
- 升级原因：
  - Event 多 Bot 模式，提供完整的 Bot 生命周期管理
  - 路由系统全面增强，支持装饰器注册、路由分组、中间件、限流、CORS、安全头等
  - 配置审计和指标监控模块，增强系统可观测性
  - 多轮对话扩展，支持分支跳转和持久化
  - 模块依赖管理，基于拓扑排序确保加载顺序正确
  - SDK 生命周期细化，Router 启动与适配器启动解耦，清理流程更完整

**注意事项**
- ⚠️ **路由中间件路径模式变更**：路径模式为 glob 匹配（如 `"/MyModule/*"`），而非 `(module_name, pattern)` 元组
- ⚠️ **Router 启动解耦**：`adapter.startup()` 不再包含 `router.start()` 调用，Router 由 SDK 生命周期独立启动

**兼容性**
- 对外 API 完全兼容，现有模块和适配器代码无需修改

### 修复
- @wsu2059q
  - 修复在本版本dev版本中反初始化耗时在显示之前就被清理导致显示耗时为0ms的问题

---

## [2.4.5-dev.3] - 2026/05/16
> 开发版本

### 新增

- @wsu2059q
  - `Config` 模块新增调用方感知和配置审计系统：
    - 新增 `_detect_caller()` 方法，使用 `sys._getframe()` 检测配置读写的调用来源
    - 新增 `AuditEntry` 数据类，记录操作类型、配置键、调用方信息和时间戳
    - 新增 `enable_audit(enabled)` 方法，开启/关闭审计日志
    - 新增 `get_audit_log(limit)` 方法，获取最近的审计记录
    - 新增 `on_change(key)` 装饰器，监听指定配置键的变更回调
    - 调用方信息包含文件名、行号、函数名、模块名
  - `Metrics` 新增指标监控模块 (`Core/metrics.py`)：
    - 新增 `MetricsManager` 管理器，提供 `counter()`、`gauge()`、`histogram()` 工厂方法
    - 新增 `Counter` 计数器指标，支持 `inc(n)` 和 `value` 属性
    - 新增 `Gauge` 仪表盘指标，支持 `inc()`、`dec()`、`set(v)` 和 `value` 属性
    - 新增 `Histogram` 直方图指标，支持 `observe(v)` 和 P50/P95/P99 百分位计算
    - 新增 `@timed(metric_name)` 装饰器，自动记录函数执行耗时
    - 新增 `register_builtin_metrics()` 方法，注册 HTTP 请求数、模块加载耗时等内置指标
    - 新增 `get_all_metrics()` 方法，返回所有指标的当前快照
  - `Router` 路由系统全面增强：
    - 新增 `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` 装饰器快捷注册路由
    - 新增 `RouteGroup` 路由分组，支持前缀、版本号和嵌套分组
    - 新增路由中间件系统（`FuncMiddleware`），支持 glob 模式路径匹配和前/后置处理
    - 新增 `@middleware(*paths)` 装饰器，根据函数参数数量自动判断前置/后置
    - 新增 `add_middleware(before, after, *paths)` 函数式中间件注册
    - 新增路由限流功能，滑动窗口算法，支持 `rate_limit` 参数（如 `"10/minute"`）
    - 新增 `setup_cors()` 方法，配置化 CORS 中间件
    - 新增 `setup_security_headers()` 方法，自动添加安全响应头
    - 新增 `disable_docs()` / `set_docs_info()` 方法，控制 API 文档
    - 新增 `_apply_config()` 方法，从配置文件自动应用 CORS 和安全头
    - `register_http_route` 新增 `rate_limit`、`summary`、`description`、`tags`、`response_model`、`deprecated` 参数，与装饰器粒度对齐
  - `Conversation` 多轮对话扩展：
    - 新增 `@conv.branch(name)` 装饰器，注册对话分支
    - 新增 `conv.goto(name)` 方法，在分支间跳转
    - 新增 `conv.start(name=None)` 方法，启动对话（默认从第一个分支开始）
    - 新增 `conv.context` 字典，分支间共享状态
    - 新增 `conv.save()` / `conv.resume()` / `conv.clear_saved()` 方法，支持对话持久化
    - `collect()` 字段新增 `condition` 参数，支持条件字段（动态表单）
  - `Module` 模块加载新增依赖管理：
    - 新增 `_validate_dependencies()` 方法，验证模块声明的 `depends` 依赖是否已注册
    - 新增 `_topological_sort()` 方法，基于 Kahn 算法按依赖关系排序加载顺序
    - 同层级模块按 `priority` 降序排列
    - 缺失依赖的模块自动跳过并记录警告
  - `CLI init` 命令增强：
    - `epsdk init` 现在生成精简的 `config.toml` 和完整的 `config.full.example`
    - 新增 `_get_full_example_config()` 静态方法，生成带注释的完整配置示例
    - 配置示例覆盖：server、logger、storage、event、framework、config.audit、metrics、router.cors、router.security、adapters.status、modules.status

### 变更

- @wsu2059q
  - `Router` 路由中间件路径模式为 glob 匹配（如 `"/MyModule/*"`），而非 `(module_name, pattern)` 元组

### 修复

- @wsu2059q
  - 修复优先级加载策略的相关问题，在 `initialize_modules()` 遍历前，按 `priority` 降序排序模块列表。同 priority 的模块保持原有相对顺序（稳定排序）。
  - 修复 `adapter.emit()` 中间件返回 `None` 时导致后续中间件和事件处理器收到空数据的问题
  - 修复 `config` 配置文件路径为相对路径时依赖 CWD 的问题，启动时自动解析为绝对路径

---

## [2.4.5-dev.2] - 2026/05/13
> 开发版本

### 重构

- @wsu2059q
  - `SDK` 生命周期细化为独立的阶段，Router 启动从 `adapter.startup()` 中解耦：
    - `Initializer.init()` 新增路由服务器启动步骤（模块初始化之后、适配器启动之前）
    - `Uninitializer.uninit()` 重构为 9 步有序清理：适配器关闭 → 模块卸载 → 路由停止 → 事件清理 → 管理器清理 → LazyModule 引用清理 → 单例状态清理 → 属性清理 → 状态重置
    - `adapter.startup()` 不再包含 `router.start()` 调用，仅负责适配器实例启动
    - `adapter.shutdown()` 不再包含 `router.stop()` 调用，适配器关闭后无条件清理事件处理器

### 优化

- @wsu2059q
  - `CLI` 添加了 ASCII Art Banner
  - 数据库创建的 `logger` 被调整为 `logger.debug`
  - `ModuleLoader.register_to_manager()` 复用已加载的 `module_class`，消除重复 `entry_point.load()` 调用
  - `runtime/frame_config` 缓存 `get_erispulse_config()` 结果，避免重复 `deepcopy`
  - `SDK._invalidate_module_cache()` 新增 `importlib.invalidate_caches()` 调用，确保 restart 后重新导入使用最新代码
  - `AdapterManager._update_bot_status()` 中 bot offline 任务完成后自动从 `_adapter_tasks` 中移除，防止无界增长
  - `CLI` 命令交互界面风格简化：
    - 移除 `install` / `self-update` / `uninstall` 命令中的冗余 `Panel` 介绍框
    - 在 `print_banner()` 后统一注入 `[title]{command.description}[/]` 命令标题行
    - Banner 尾部空行从 `\n\n` 缩减为 `\n`，消除 banner 与内容之间的大间距

### 修复

- @wsu2059q

  - 修复 `epsdk run <目录路径>` 导致 CLI 重复实例化和 Banner 重复打印的问题：
    - `RunCommand.execute()` 新增 `os.path.isdir()` 检查，提示用户指定具体脚本文件
  - 修复 `CommandRegistry` 重复注册时抛出 `ValueError` 导致错误信息泄漏的问题（改为幂等跳过）
  - 修复 `print_banner()` 在同一进程中重复打印的问题（添加全局标志）
  - 修复 `Uninitializer.uninit()` 清理不完整导致 restart 后状态残留的问题：
    - 新增 `config.force_save()` 清理待写入定时器
    - 新增 `lifecycle._timers.clear()` 清理残留计时器
    - 新增 `logger._logs.clear()` 和 `logger._module_levels.clear()` 清理日志内存缓存
    - 新增 LazyModule 内部引用清理（`_sdk_ref`、`_instance`、`_manager_instance`、`_module_class`），打破循环引用链

---

## [2.4.5-dev.1] - 2026/05/12
> 开发版本

### 优化
- @wsu2059q
  - `logger` 的 `caller` 检测进行了优化，现在显示的调用方更加智能

---

## [2.4.5-dev.0] - 2026/05/10
> 开发版本

### 新增

- @wsu2059q
  - `Event` 模块新增多Bot模式支持：
    - 新增 `get_self_account_id()` 方法，优先返回 `account_id`（ErisPulse扩展），不存在时回退到 `user_id`（OB12标准）
    - `reply()`、`reply_ob12()` 方法自动使用接收事件的Bot发送消息（通过 `SendDSL.Using(bot_id)`）
    - `wait_reply()` 的等待键新增 `bot_id` 维度，区分不同Bot的同用户同目标会话
    - `_get_adapter_and_target()` 返回值扩展为四元组，新增 `bot_id`
  - `Docker` 新增多版本通道支持和自动更新功能：
    - 新增 `dev` 和 `stable` 两个版本通道，通过 `ERISPULSE_CHANNEL` 环境变量控制
    - 实现启动时自动更新功能，支持 `ERISPULSE_UPDATE_ON_START` 配置
    - Dockerfile 重构为多阶段构建，分离 `production` 和 `dev` 目标
    - 新增 `docker-entrypoint.sh` 入口脚本，集成版本检测和自动升级逻辑
    - `docker-compose.yml` 支持动态构建目标和标签配置
  - 添加花枫咖啡馆（Ideaura）适配器到平台支持列表及特性文档

### 优化

- @wsu2059q
  - 改进 `CLI install` 命令的交互式安装体验
  - 调整 `lifecycle` 和 `router` 中的参数验证逻辑

### 修复

- @wsu2059q
  - 改进适配器管理器的错误处理机制
  - Code Review 修复：涉及 `logger`、`storage`、`module`、`sdk`、`loader`、`finder`、`frame_config`、`exceptions` 等多个模块的参数校验和异常处理改进

---

## [2.4.4] - 2026/05/07
> 正式发布

**版本摘要**
修复版本：简化初始化模板，重构热重载机制为子进程模式，修复 `sdk.run()` 未捕获 `CancelledError` 导致异常日志的问题。

**升级建议**
- **建议升级**
- 升级原因：
  - 初始化模板大幅简化，新项目开箱即用
  - 热重载机制改为子进程模式，更稳定可靠
  - `sdk.run()` 正确处理关闭信号，避免异常日志

**兼容性**
- 对外 API 完全兼容，现有模块和适配器代码无需修改

### 变更

- @wsu2059q
  - `ep init` 生成的 `main.py` 模板简化：移除冗余的手动初始化/启动/循环/关闭代码，改为 `await sdk.run(keep_running=True)` 一行调用
  - `ep run` 热重载机制重构恢复为子进程模式：
    - 使用 `subprocess.Popen` 启动脚本进程，而非在事件循环内运行
    - 文件变更时终止旧进程并重新启动，避免模块缓存和状态残留问题
    - 非重载模式下使用 `runpy.run_path()` 直接运行脚本

### 修复

- @wsu2059q
  - 修复 `sdk.run()` 未捕获 `asyncio.CancelledError` 导致关闭时输出异常日志的问题

---

## [2.4.3] - 2026/05/06
> 正式发布

**版本摘要**
架构优化版本：ASGI 服务器从 Hypercorn 切换为 Uvicorn，新增通用 SQL 链式查询构建器，移除子进程运行模型，修复热重启模块缓存和 Windows CTRL+C 等关键问题。

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 修复热重启后已更新模块代码未生效的关键问题
  - 修复 Windows 下 CTRL+C 无法停止程序的问题
  - ASGI 服务器切换为 Uvicorn，稳定性更好
  - 新增 SQL 链式查询构建器，增强存储模块能力

**注意事项**
- ⚠️ **依赖变更**：`hypercorn>=0.14.0` 已替换为 `uvicorn>=0.30.0`，升级后需重新安装依赖
- ⚠️ **移除子进程模型**：`ep run` 不再通过子进程运行，热重载改为事件循环内调用 `sdk.restart()`
- ⚠️ **移除**：`runtime/cleanup.py` 模块已删除，子进程清理机制不再需要
- ⚠️ **移除**：`sdk._init_progress()` 方法和自动生成 main.py 的逻辑已移除，模板创建请使用 `epsdk init`
- ⚠️ **移除**：`__init__.py` 中 `_prepare_environment`、`_init_progress` 的向后兼容导出已移除
- ⚠️ **行为变更**：`sdk.run()` 的 finally 块改为完整清理（`await sdk.uninit()`），不再需要调用方手动调用 `sdk.uninit()`

**兼容性**
- 对外 API 完全兼容，现有模块和适配器代码无需修改
- 仅移除内部辅助方法（`_prepare_environment`、`_init_progress`），不影响公共 API 使用者

---

## [2.4.3-dev.1] - 2026/05/03
> 开发版本

### 新增
- @wsu2059q
  - `Core.Storage` 存储模块新增通用 SQL 链式查询构建器：
    - 新增 `Bases/storage.py`，定义 `BaseStorage(ABC)` 和 `BaseQueryBuilder(ABC)` 抽象基类，支持未来拓展其他存储介质（Redis、MySQL 等）
    - 新增 `SQLiteQueryBuilder(BaseQueryBuilder)`，链式调用风格的 SQL 查询构建器
    - 新增 `AlterTableBuilder`，链式调用风格的表结构修改构建器（支持 `AddColumn`、`RenameTo`）
    - `StorageManager` 继承 `BaseStorage`，新增 `Table()`、`CreateTable()`、`DropTable()`、`HasTable()`、`AlterTable()` 方法
    - 链式方法：`Select`、`Insert`、`InsertMulti`、`Update`、`Delete`、`Where`、`OrderBy`、`Limit`、`Offset`、`copy`、`clear`
    - 终止方法：`Execute`、`ExecuteOne`、`Count`、`Exists`
    - 所有 WHERE 参数使用 `?` 占位符，防止 SQL 注入
    - 完全支持事务，复用 `_get_connection()` 和 `_auto_commit()`
    - 现有键值 API（`get`/`set`/`delete` 等）完全向后兼容

### 优化
- @wsu2059q
  - 修改加载失败逻辑，某部分模块加载失败时不会影响整体加载

### 修复
- @wsu2059q
  - 修复热重启（`sdk.restart()`）后已更新模块的 Python 代码未生效的问题：
    - **根因**：`_do_restart()` 在重新初始化时，`entry_point.load()` 从 `sys.modules` 返回了旧版本的缓存模块对象，导致新安装/更新的模块逻辑（如新增 API 路由）未生效
    - **方案**：在 `uninit()` 后、`init()` 前清理 `sys.modules` 中已加载模块/适配器包的缓存，使 `entry_point.load()` 从磁盘加载最新代码
    - `BaseFinder` 新增 `get_top_level_modules()` 方法，从 `top_level.txt` 或 entry-point value 推导包的顶层 Python 模块名
    - `ModuleLoader` / `AdapterLoader` 加载时将 `top_level` 信息存入 `moduleInfo["meta"]` / `adapterInfo["meta"]`
    - `SDK._do_restart()` 新增 `_collect_top_level_modules()` 和 `_invalidate_module_cache()` 辅助方法
  - `RouterManager.stop()` 清理时额外重置 `_uvicorn_server = None`，避免重启时残留引用

---

## [2.4.3-dev.0] - 2026/04/28
> 开发版本

**版本摘要**
架构优化版本：ASGI 服务器从 Hypercorn 切换为 Uvicorn，移除子进程运行模型和 cleanup 模块，修复 Windows 下 CTRL+C 无法停止程序的问题。`ep run` 不指定脚本时直接内部运行 SDK，模板创建统一由 `epsdk init` 处理。

**注意事项**
- ⚠️ **依赖变更**：`hypercorn>=0.14.0` 已替换为 `uvicorn>=0.30.0`，升级后需重新安装依赖
- ⚠️ **移除子进程模型**：`ep run` 不再通过子进程运行，热重载改为事件循环内调用 `sdk.restart()`
- ⚠️ **移除**：`runtime/cleanup.py` 模块已删除，子进程清理机制不再需要
- ⚠️ **移除**：`sdk._init_progress()` 方法和自动生成 main.py 的逻辑已移除，模板创建请使用 `epsdk init`
- ⚠️ **移除**：`__init__.py` 中 `_prepare_environment`、`_init_progress` 的向后兼容导出已移除
- ⚠️ **行为变更**：`sdk.run()` 的 finally 块改为完整清理（`await sdk.uninit()`），不再需要调用方手动调用 `sdk.uninit()`

**兼容性**
- 对外 API 完全兼容，现有模块和适配器代码无需修改
- 仅移除内部辅助方法（`_prepare_environment`、`_init_progress`），不应影响公共 API 使用者

### 变更

- @wsu2059q
  - ASGI 服务器从 Hypercorn 切换为 Uvicorn：
    - `pyproject.toml` 依赖 `hypercorn>=0.14.0` → `uvicorn>=0.30.0`
    - `router.py` 使用 `uvicorn.Server._serve()` 直接启动，绕过 `capture_signals()` 避免信号处理冲突
    - `router.stop()` 通过 `should_exit = True` 优雅停止，超时则取消任务
  - `ep run` 行为调整：
    - 不指定脚本时直接内部运行 SDK，不再自动生成 `main.py` 模板
    - 指定不存在的脚本时提示使用 `epsdk init` 创建项目
  - `sdk.run()` finally 块改为完整清理（`await self.uninit()`），替代原来的部分清理（`module.unload()` + `adapter.shutdown()`）
  - main.py 模板简化：移除冗余的 `finally: await sdk.uninit()`（`sdk.run()` 已处理）

### 移除

- @wsu2059q
  - 移除 `runtime/cleanup.py` 清理管理模块及其所有子进程相关代码（`CleanupManager` 类、`send_cleanup_signal()`、`setup_cleanup_subprocess()`）
  - 移除 `sdk._init_progress()` 方法和自动生成 `main.py` 模板的逻辑
  - 移除 `__init__.py` 中 `_prepare_environment`、`_init_progress` 的向后兼容导出
  - 移除 `_prepare_environment()` 的 `script_path` 参数，仅保留配置初始化功能

### 修复

- @wsu2059q
  - 修复 Windows 下 `python main.py` 无法使用 CTRL+C 停止程序的问题：
    - **根因**：Hypercorn 的 `serve()` 函数注册的 SIGINT 处理器覆盖了默认处理器，且 Hypercorn 内部 shutdown 机制在 `asyncio.create_task()` 模式下无法正常触发
    - **方案**：切换为 Uvicorn，使用 `_serve()` 绕过 `capture_signals()` 信号处理上下文管理器，将信号控制权交还给 SDK

---

## [2.4.2] - 2026/04/26
> 正式发布

**版本摘要**
稳定性更新版本，修复了配置系统、模块加载、事件处理等关键问题，提升了系统的稳定性和可维护性。

**升级建议**
- **强烈建议升级**
- 升级原因：
  - 修复配置系统多线程写入数据丢失问题
  - 修复 LazyModule 同步访问初始化问题
  - 修复 Bot 离线事件重复提交问题
  - 增强异常处理和错误提示

**注意事项**
- ⚠️ **弃用方法正式删除**：`AdapterFather`/`adapter_server` 兼容别名已移除
- ⚠️ **重要**：`BaseAdapter.emit()` 现在会抛出 `NotImplementedError`

**兼容性**
- 对外 API 保持兼容（除非使用了已移除的兼容别名）

---

## [2.4.2-dev.2] - 2026/04/24
> 开发版本

### 移除
- @wsu2059q
  - 弃用移除 `AdapterFather`/`adapter_server` 兼容别名

### 修复
- @wsu2059q
  - 修复 `lifecycle.submit_event()` 使用可变默认参数 `data={}` 的隐患
  - 修复 `_migrate_config()` 迁移异常被静默吞掉无任何提示的问题
  - 修复 `BaseAdapter.emit()` 仅记录日志不抛异常，调用方可能忽略废弃方法的问题（改为 `raise NotImplementedError`）
  - 修复 `_update_bot_status()` 使用 `asyncio.ensure_future` 无 task 引用追踪的问题（改为 `create_task` 并保存引用）

### 优化
- @wsu2059q
  - `AdapterManager`/`ModuleManager` 新增 `__repr__()` 方法，便于调试时查看注册和运行状态
  - `list_adapters()`/`list_modules()` 已弃用方法添加 `warnings.warn(DeprecationWarning)` 实际触发弃用警告

---

## [2.4.2-dev.1] - 2026/04/21
> 开发版本

### 修复
- @wsu2059q
  - 修复 LazyModule 同步访问 BaseModule 导致未初始化完成的问题：
    - 在同步上下文中，BaseModule 使用 `asyncio.run()` 确保初始化完成
    - 保持透明代理特性，用户无需感知同步/异步差异
  - 修复配置系统多线程写入导致数据丢失的问题：
    - 添加文件锁机制（`_file_lock`）确保文件操作原子性
    - 使用临时文件写入后原子性重命名（`os.replace`/`os.rename`）
    - 改进 `_schedule_write` 的 Timer 取消和重新调度逻辑
  - 修复 Router 停止时异常未记录的问题：
    - 区分不同类型的异常（CancelledError、TimeoutError、其他异常）
    - 分别记录不同级别的日志，并使用 `exc_info=True` 输出完整堆栈
  - 修复 Bot 离线事件重复提交的问题：
    - 在 `AdapterManager` 中添加 `_is_being_shutdown` 标志
    - `shutdown()` 开始时设置为 True，结束时清除
    - `_update_bot_status()` 检查该标志，避免在关闭过程中重复提交离线事件
  - 修复模块管理器 `exists()` 和 `is_enabled()` 逻辑混乱的问题：
    - `exists()`: 只检查模块类是否已注册（`_module_classes`），语义明确为"是否可加载"
    - `is_enabled()`: 检查配置中是否存在且状态为启用，不存在直接返回 False
  - 修复生命周期事件处理器在事件提交完成前被清理的问题：
    - 在提交事件后添加 `await asyncio.sleep(0.1)` 确保事件处理完成
    - 然后再清理 `lifecycle._handlers`

### 优化
- @wsu2059q
  - 优化 SDK 属性访问的错误提示：
    - 根据属性名称区分不同场景提供准确的错误提示
    - 已注册但未启用：提示模块/适配器未启用
    - 完全不存在：提示检查名称拼写
  - 优化 Uninitializer 的清理逻辑：
    - 简化清理逻辑，只处理已初始化的 LazyModule
    - 跳过未初始化的 LazyModule，不创建临时实例
    - 只为已初始化的模块调用 `on_unload`
  - `restart()` 方法添加详细的设计说明和使用示例：
    - 说明使用 `asyncio.ensure_future()` 的设计意图
    - 解释返回值语义（任务是否成功调度，而非重启是否完成）
    - 提供多个使用场景示例和最佳实践

### 重构
- @wsu2059q
  - 新增 `parse_bool_config()` 工具函数统一处理布尔值配置：
    - 支持 bool、int、str 等多种类型
    - 标准化 "true"/"false"、"yes"/"no"、"on"/"off" 等常见布尔值表示

---

## [2.4.2-dev.0] - 2026/04/13
> 开发版本

### 新增
- @wsu2059q
  - `adapter.shutdown()` 支持指定平台关闭（传入 `platforms` 参数），同时新增逐平台状态变化事件
  - `adapter.startup()` 新增后台任务追踪机制（`_adapter_tasks`），`shutdown()` 时自动取消对应任务
  - `module` 模块新增 `get_status_summary()` 和 `get_info()` 方法

### 优化
- @wsu2059q
  - `adapter.shutdown()` 状态事件与 `startup()` 保持对称
  - `module.exists()` 同时检查内存注册和配置文件
  - `module.enable()` 新增模块存在性验证

### 修复
- @wsu2059q
  - 修复 `Event.confirm()` 确认词集合赋值重复、`MessageBuilder.at` 方法定义被覆盖
  - 修复 `Event.is_friend_add()`/`is_friend_delete()` 的 `detail_type` 值与 OB12 标准不一致
  - 修复 `adapter.clear()` 未清理 `_started_instances` 和 `_adapter_tasks`
  - 修复 `command.wait_reply()` 使用已弃用的 `asyncio.get_event_loop()`
  - 修复 `Event.collect()` 字段缺少 `key` 时静默跳过、`Event.collect()` 缺少 `key` 时无提示

### 移除
- @wsu2059q
  - 移除第三方 CLI 扩展功能：
    - 删除 `CLIFinder` 及其相关代码
    - 删除 CLI 第三方命令加载和执行机制
    - 移除 `CommandRegistry` 中的外部命令管理功能
    - 从包管理器中移除 CLI 扩展的安装、卸载、升级和查询功能
    - 删除 `install`、`list`、`list-remote`、`uninstall` 命令中的 CLI 扩展选项
    - 删除 CLI 扩展示例代码 `examples/example-cli-module/`
    - 删除 CLI 扩展开发文档（所有语言版本）
    - 更新用户指南，移除 CLI 扩展相关说明
  - 移除原因：CLI 扩展功能过于复杂，使用场景有限，简化架构以降低维护成本

---

## [2.4.1] - 2026/04/10
> 正式发布

**版本摘要**
2.4.1 版本是一个重要的功能更新版本，主要新增了 Event 交互方法（confirm/choose/collect/wait_for/conversation）、Bot 状态追踪系统、MessageBuilder 消息构建器、平台事件方法扩展系统；实现了事件处理并行化；标准化了模块/适配器生命周期；全面现代化了类型注解（Python 3.10+）；并修复了重启后多个关键功能问题。

**升级建议**
- **建议升级**
- 升级原因：
  - Event 交互方法大幅简化了多轮对话和用户交互的开发流程
  - Bot 状态追踪系统提供了完整的 Bot 生命周期管理
  - MessageBuilder 支持链式构建 OneBot12 消息段，提升消息构建体验
  - 事件处理并行化解决了 `wait_reply` 阻塞后续处理器的问题
  - 生命周期标准化确保重启/卸载场景下的状态完全可控

**注意事项**
- ⚠️ **BREAKING CHANGE**：`Raw_ob12` 方法现在是适配器**必须实现**的核心方法，未实现时基类默认返回标准错误响应（`status: "failed"`, `retcode: 10002`）并记录 error 级别日志
- 类型注解全面转向 Python 3.10+ 内置类型语法，要求 Python >= 3.10

**兼容性**
- 对外 API 保持兼容，现有代码无需修改
- 适配器开发者需注意 `Raw_ob12` 为必须实现的方法

---
## [2.4.1-dev.0] - 2026/04/11
> 开发版本

### 优化
- @wsu2059q
  - 优化`Event`中优先级并发的处理逻辑

---

## [2.4.0-dev.4] - 2026/04/10
> 开发版本

### 新增
- @wsu2059q
  - **Event 交互方法**：新增 `confirm`、`choose`、`collect`、`wait_for`、`conversation` 方法，提供声明式交互能力
    - `event.confirm(prompt)` - 等待用户确认，识别中英文内置确认词
    - `event.choose(prompt, options)` - 选项选择菜单
    - `event.collect(fields)` - 多步骤表单收集
    - `event.wait_for(event_type, condition)` - 等待任意事件
    - `event.conversation()` - 多轮对话上下文
  - **内置确认词集合**：导出 `CONFIRM_YES_WORDS` (21个) 和 `CONFIRM_NO_WORDS` (19个)
  - **Conversation 类**：多轮对话管理器，支持 `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`

### 优化
- @wsu2059q
  - **事件处理并行化**：同优先级处理器并行执行，不同优先级按顺序执行
    - 解决 `wait_reply` 阻塞后续处理器的问题
    - 使用 Copy-On-Write 优化，无修改时不创建副本
    - 同优先级多处理器修改同一字段时，使用最后修改值并记录警告日志

---

## [2.4.0-dev.3] - 2026/04/09
> 开发版本

### 新增
- @wsu2059q
  - cli的install支持pip参数

### 重构
- @wsu2059q
  - **模块/适配器生命周期标准化**：统一初始化与卸载流程，确保完全可控
    - `BaseEventHandler` 引入 `_linked_to_adapter_bus` 状态，明确追踪与适配器事件总线的连接关系
    - `_clear_handlers()` 断开总线连接后，下次 `register()` 自动重新挂载，适配 shutdown/restart 场景
    - 删除散落的 `_adapter_handler_registered`、`_command_handler_registered` 魔术标记
  - **LazyModule 实例化修正**：BaseModule 子类统一通过 `manager.load()` 完成实例化 + `on_load`，消除双重实例化问题
  - **Uninitializer 卸载流程修正**：先收集模块属性再清理管理器，确保重启后 sdk 状态完全重置

### 修复
- @wsu2059q
  - **修复重启后命令事件失效**：`adapter.shutdown()` 清空事件总线后，`BaseEventHandler` 的 `_linked_to_adapter_bus` 未重置，导致 `_process_event` 无法重新挂载到适配器总线。表现为 `@command` 注册的命令在重启后无法触发
  - **修复重启后懒加载模块未被正常加载**：`uninit()` 在 `module_manager.clear()` 之后遍历已清空的列表，导致 sdk 上的模块属性未被清理，restart 后旧残留影响新实例
  - **修复未初始化的 LazyModule 代理未执行 `on_unload`**：从未被访问过的懒加载模块不在 `_loaded_modules` 中，uninit 时 `on_unload` 不会被调用
  - **修复生命周期事件处理器未清理**：`lifecycle._handlers` 在 uninit 时从未清理，restart 后旧处理器会重复触发
  - **Python 3.10/3.11 兼容性修复**：将 Python 3.12+ 的 `type` 语句改为 `typing.TypeAlias`


---

## [2.4.0-dev.2] - 2026/04/05
> 开发版本

### 重构
- @wsu2059q
  - **类型注解现代化**：全面转向 Python 3.10+ 内置类型语法
  - **collections.abc 替换**：
    - `typing.Callable` → `collections.abc.Callable`
    - `typing.Awaitable` → `collections.abc.Awaitable`
    - `typing.Iterator` → `collections.abc.Iterator`
  - **引入 StrEnum**：在 `session_type.py` 中使用 `enum.StrEnum` 替换字符串常量：
    - 创建 `ReceiveType` 枚举类（PRIVATE, GROUP, CHANNEL, GUILD, THREAD, USER）
    - 创建 `SendType` 枚举类（USER, GROUP, CHANNEL, GUILD, THREAD）
    - 保持向后兼容
  - **引入类型别名**：在 5 个文件中添加 `type` 别名声明：
    - `session_type.py`: ReceiveTypeStr, SendTypeStr, SessionTypeMap, OptionalStr
    - `config.py`: ConfigValue, ConfigKey
    - `storage.py`: StorageKey, StorageValue
    - `router.py`: HTTPHandler, WebSocketHandler, RoutePath
    - `strategy.py`: StrategyData
  - **引入海象运算符**
  - **引入 match/case**

---

## [2.4.0-dev.1] - 2026/04/01
> 开发版本

### 新增
- @wsu2059q
  - `adapter` 模块新增 Bot 状态追踪系统：
    - 新增 `_bots` 内部存储，按平台和 Bot ID 维护状态信息（在线/离线、活跃时间、元信息）
    - `emit()` 方法自动处理 OB12 事件中的 `self` 字段，实现 Bot 自动发现与状态更新
    - 支持处理 `meta` 事件的三种类型：
      - `connect`：自动注册 Bot 并触发 `adapter.bot.online` 生命周期事件
      - `disconnect`：标记 Bot 离线并触发 `adapter.bot.offline` 生命周期事件
      - `heartbeat`：更新 Bot 活跃时间和元信息
    - 普通事件（message/notice/request）中的 `self` 字段也会自动发现并注册 Bot
    - 支持从 `self` 字段提取扩展元信息（`user_name`、`nickname`、`avatar`、`account_id`）
    - 新增 `get_bot_info(platform, bot_id)` 方法，获取 Bot 详细信息
    - 新增 `list_bots(platform=None)` 方法，列出指定平台或所有平台的 Bot
    - 新增 `is_bot_online(platform, bot_id)` 方法，检查 Bot 是否在线
    - 新增 `get_status_summary()` 方法，获取适配器与 Bot 的完整状态摘要（便于 WebUI 展示）
    - `shutdown()` 时自动将所有已注册 Bot 标记为离线
    - `clear()` 时清理所有 Bot 状态

### 重构
- @wsu2059q
  - `logger` 模块提取 `_log` 内部方法：
    - `Logger` 和 `LoggerChild` 各新增 `_log(level_name, level_const, msg)` 方法，统一日志记录流程
    - `debug`/`info`/`warning`/`error`/`critical` 五个公开方法简化为单行委托调用
  - `storage` 模块提取公共逻辑方法：
    - 新增 `_is_ready()` 方法替代 8 处重复的初始化守卫检查
    - 新增 `_auto_commit(conn)` 方法替代 6 处重复的事务提交检查
  - `SendDSL` 提取修饰器未实现方法：
    - 新增 `_unimplemented_modifier(method_name, **kwargs)` 方法
    - `At`/`Reply`/`AtAll` 三个方法简化为委托调用
  - `module` 加载器简化策略获取逻辑：
    - 新增 `_extract_strategy_value()` 统一处理 dict/ModuleLoadStrategy 两种类型
    - 新增 `_get_global_lazy_loading()`、`_resolve_strategy()`、`_apply_global_lazy_loading()` 方法
    - `_get_load_strategy` 由嵌套 try/except 简化为顺序调用

### 修复
- @wsu2059q
  - 修复 `BaseAdapter.Send.Example` 方法中参数 `text: str` 被硬编码字典覆盖的类型矛盾问题（改用 `mock_response` 变量名）

### 测试
- @wsu2059q
  - 新增 Bot 状态追踪单元测试（共 23 个用例）：
    - meta connect 事件：注册 Bot、触发生命周期事件、首次/重复注册
    - meta heartbeat 事件：更新活跃时间、更新元信息、未知 Bot 不崩溃
    - meta disconnect 事件：标记离线、未知 Bot 不崩溃
    - 普通事件自动发现：message/notice 事件发现 Bot、无 self 不崩溃
    - self 字段元信息提取与合并
    - 查询方法：get_bot_info、list_bots、is_bot_online、get_status_summary
    - 生命周期：shutdown 标记离线、clear 清理状态
    - 多平台多 Bot 场景

---

## [2.4.0-dev.0] - 2026/03/30
> 开发版本

> 这个dev版本的 Raw_ob12 之前已经实现，现转为必须实现项

### 新增
- @wsu2059q
  - `Event.wrapper` 新增平台事件方法扩展系统：
    - 新增 `register_event_method(platform)` 装饰器，支持为指定平台注册专有方法
    - 新增 `register_event_mixin(platform, mixin_cls)` 函数，支持批量注册 Mixin 类中的方法
    - 新增 `unregister_event_method(platform, name)` 函数，支持注销单个扩展方法
    - 新增 `unregister_platform_event_methods(platform)` 函数，适配器关闭时清理全部扩展方法
    - 新增 `get_platform_event_methods(platform)` 函数，查询指定平台已注册的扩展方法名列表
    - Event 实例根据 `platform` 字段动态注入对应平台的扩展方法，非当前平台的方法抛出 `AttributeError`
    - `dir(event)` 自动包含当前平台的扩展方法名
    - 注册时自动检测与 Event 内置方法的命名冲突，冲突时发出 `RuntimeWarning` 并跳过
    
  - Event 模块新增 MessageBuilder 消息构建器：
    - 支持链式调用构建 OneBot12 消息段列表
    - 支持快速构建单段消息（静态方法调用）
    - 提供文本、图片、音频、视频、文件、@用户、回复、@全体等基础消息段构建方法
    - 支持自定义消息段和平台扩展消息段
    - 提供 copy()、clear()、__len__() 等工具方法
  - `Event.wrapper` 新增 reply_ob12() 方法：
    - 支持使用 OneBot12 消息段列表进行回复
    - 可配合 MessageBuilder 链式构建消息
  - Core 模块导出 MessageBuilder 类，支持从 `ErisPulse.Core` 直接导入

### 变更
- @wsu2059q
  - **BREAKING CHANGE**: Raw_ob12 方法现在是适配器必须实现的核心方法：
    - 未实现时基类默认实现会记录 **error 级别**日志
    - 返回标准错误响应格式（`status: "failed"`, `retcode: 10002`）
    - 不再返回 `None`，确保调用方可统一处理响应
  - SendDSL 协议方法文档更新：
    - 明确标识 Raw_ob12 为必须实现的方法
    - 标准方法（Text、Image 等）内部应委托给 Raw_ob12
    - 修饰器状态（At/Reply/AtAll）需在 Raw_ob12 内合并为消息段
  - 完善适配器文档：
    - 详细说明反向转换（OneBot12 → 平台）实现规范
    - 更新适配器架构图，展示正向转换与反向转换的对称性
    - 提供 MessageBuilder 完整使用示例

### 文档
- @wsu2059q
  - 更新 send-method-spec.md 标准文档：
    - 新增第 11 章「消息构建器（MessageBuilder）」
    - 明确 Raw_ob12 为必须实现的方法
    - 添加推荐的消息构建器使用示例
  - 更新适配器开发指南：
    - best-practices.md 添加反向转换与消息构建章节
    - core-concepts.md 更新架构图，展示双向转换流程
    - getting-started.md 简化示例代码，强调 Raw_ob12 必须实现
    - send-dsl.md 更新协议方法表格，标注必须实现的方法

### 测试
- @wsu2059q
  - 新增 `SendDSL Raw_ob12` 单元测试：
    - 测试未重写 Raw_ob12 时返回标准错误响应
    - 测试未重写时记录 error 级别日志
    - 测试重写后正常返回 Task 并可 await
    - 测试接受 dict 和 list 两种输入格式
    - 测试配合 MessageBuilder 使用

---

## [2.3.9] - 2026/03/28
> 正式发布

**版本摘要**
2.3.9 版本是一个功能丰富的更新版本，主要增加了会话类型管理系统、运行状态检查API、会话类型管理模块以及完善的类型注解支持。同时增强了CI/CD工作流的质量检查功能，优化了多个核心模块的功能和性能。

**升级建议**
- **建议升级**
- 升级原因：新增了会话类型管理和运行状态检查等实用功能，显著提升了开发体验和类型安全性

## 注意事项
- 新增了会话类型管理模块，提供标准的会话类型定义和转换功能
- 移除了 `/routes` 端点，出于安全考虑删除路由列表查询功能

**兼容性**
- 完全向后兼容

---

## [2.3.9-dev.3] - 2026/03/27

### 新增
- wsu2059q
  - `CI/CD` 工作流新增 Ruff 代码质量检查：
    - 新增 `ruff-check` 任务，自动检查代码质量问题
    - 检查结果会提交到 PR 评论中供开发者参考
    - 检查失败不会阻止合并，仅作为参考

### 优化
- @wsu2059q
  - 为 SDK 核心组件添加完整的类型注解：
    - 为所有 Core 单例添加类型注解
    - 在 sdk.py 中添加了 `__future__` import annotations
    - 为 SDK 类属性提供精确的类型标注，提升 IDE 类型提示准确性

### 文档
- @wsu2059q
  - 更新 `standards/README.md` 索引，移除已删除文档条目并更新描述
  - 更新文档生成脚本（`generate-docs-index.py`、`generate-ai-prompts.py`）中的文档路径引用
  - 重构技术标准文档排版：
    - 扩展命名规范、会话类型扩展、模块开发者指南、扩展注册表 → `event-conversion.md`
    - `Raw_ob12` 规范、反向转换规范、方法发现、发送方法扩展注册表 → `send-method-spec.md`
    - `message_id` 必选字段、`{platform}_raw` 原始响应规范 → `api-response.md`

---
## [2.3.9-dev.2] - 2026/03/23

### 修复
- @LeslieKeys
  - 修复 `ep init` 命令交互式初始化中适配器配置的类型错误：
    - 修正 `_configure_adapters_interactive_sync` 方法的参数类型为 `Path`

### 文档
- @wsu2059q
  - 新增 Bug 修复说明文档（`bug-tracker.md`）
  - 重构发送方法规范文档：
    - 将 `naming-conventions.md` 重命名为 `send-method-spec.md`，更准确反映文档内容
    - 扩展媒体消息参数规范，详细说明 URL、文件路径、二进制数据的使用场景和注意事项
  - 更新文档生成脚本（`generate-docs-index.py`、`generate-ai-prompts.py`）中的文档路径引用

---

## [2.3.9-dev.1] - 2026/03/21
> 开发版本

### 新增
- @wsu2059q
  - `router` 模块新增版本信息和 ping 端点：
    - 新增 `/ping` 端点，提供连通性检查和时间戳返回
    - `/health` 端点增强返回信息，包含 ErisPulse 版本号和 Python 版本信息
  - `router` 模块新增 `_normalize_path` 方法，标准化路径格式
  - `Event` 模块新增会话类型管理模块（`session_type.py`）：
    - 定义标准会话类型：`private`, `group`, `channel`, `guild`, `thread`, `user`
    - 支持接收类型到发送类型的自动转换（如 `private` → `user`）
    - 提供会话类型注册和注销功能（`register_custom_type`, `unregister_custom_type`）
    - 实现自动类型推断功能（`infer_receive_type`）
    - 提供类型转换和 ID 获取工具方法（`convert_to_send_type`, `get_target_id` 等）

### 优化
- @wsu2059q
  - `BaseAdapter.SendDSL.To` 方法增强：
    - 支持自动类型转换：当目标类型为 `private` 时自动转换为 `user`
    - 支持简化形式：只提供 `target_id` 时默认推断为 `user`
  - `Event.wrapper` 模块优化：
    - 使用会话类型管理模块统一处理类型转换和 ID 获取
    - 简化 `_get_adapter_and_target_info` 方法实现
    - 移除冗余的类型映射逻辑
  - `Event.command` 模块优化：
    - 使用 `get_send_type_and_target_id` 替代手动类型判断
    - 使用 `infer_receive_type` 进行类型推断
    - 统一发送逻辑，提高代码可维护性

### 移除
- @wsu2059q
  - 移除 `/routes` 端点，出于安全考虑删除路由列表查询功能

### 文档
- @wsu2059q
  - 新增会话类型标准文档，提供完整的类型定义和使用指南
  - 更新事件转换标准文档，引用会话类型标准
  - 新增会话类型管理单元测试（`tests/unit/test_unit_session_type.py`）
  - 文档生成器添加`会话类型支持`文档

---

## [2.3.8] - 2026/03/18
> 正式发布

**版本摘要**
本版本新增运行状态检查API，优化了适配器和模块的用户体验；改进了配置文件的可读性；优化了SDK初始化流程。

**升级建议**
- **可选升级**
- 升级原因：新增的运行状态检查API让开发更便捷，配置文件更易读

**兼容性**
- 完全向后兼容

---

## [2.3.8-dev.1] - 2026/03/15
> 开发版本

### 新增
- @wsu2059q
  - `adapter` 和 `module` 模块新增运行状态检查API：
    - 新增 `is_running(name)` 方法，检查指定平台/模块是否正在运行
    - 新增 `list_running()` 方法，列出所有正在运行的平台/模块

### 优化
- @wsu2059q
  - `BaseAdapter` 的 `SendDSL` 类新增 `__getattr__` 方法：
    - 实现大小写不敏感的方法调用，支持 `Text()`、`text()`、`TEXT()` 等任意大小写形式
    - 调用不存在的方法时，将完全兼容 `hasattr()` 逻辑
  - `logger` 的 `get_child` 新增属性获取，支持 `__getattr__` 方法：“logger.Module = logger.get_child("Module")” 是对等的
  - `storage` 新增 `keys` 方法,用于代理 `get_all_keys` 作为字典标准的方法获取全部key

---

## [2.3.8-dev.0] - 2026/03/11
> 开发版本

### 变更
- @wsu2059q
  - `router` 模块 WebSocket 路由增强：
    - `register_websocket` 方法新增 `auto_accept` 参数（默认 `True`）
    - `auto_accept=False` 时，handler 必须自行调用 `websocket.accept()` 或 `websocket.close()`

### 修复
- @wsu2059q
  - 修复极端情况下 WebSocket 连接时 ASGI 消息顺序错误："Expected ASGI message 'websocket.send' or 'websocket.close', but got 'websocket.accept'"

### 重构
- @wsu2059q
  - `config` 模块配置文件写入优化：
    - 新增 `_sort_config_dict` 方法，递归排序配置字典
    - 确保配置文件中同一模块的配置项排列在一起，提升可读性

### 文档
- @wsu2059q
  - 更新所有相关文档，说明 `auto_accept` 参数的使用方法和两种模式差异
  - 更新示例代码，展示自动接受和手动控制连接两种用法

---

## [2.3.7] - 2026/03/10
> 正式发布

**版本摘要**
本版本进行了多项代码质量改进和配置优化：统一使用 `inspect` 模块检查协程函数，替代将被弃用的 `asyncio` 方法；修正模块加载事件命名规范；调整项目配置文件路径结构；从构建配置中移除 stubs 目录。

**升级建议**
- **可选升级**

**注意事项**
- 配置文件路径变更：项目配置文件从 `config.toml` 迁移到 `config/config.toml`，使用 `ep init` 创建的新项目将使用新的路径结构

**兼容性**
- 完全向后兼容

### 修复
- @wsu2059q
  - 修正模块加载事件名称为 `module.load`
  - 修改 CLI init 命令生成的配置文件路径为 `config/config.toml`

### 重构
- @wsu2059q
  - 使用 `inspect.iscoroutinefunction` 替代将被弃用的 `asyncio.iscoroutinefunction`：
    - CLI 命令处理函数协程检查
    - 事件处理器协程检查
    - 命令处理器协程检查
    - 生命周期处理器协程检查
    - 模块加载器协程检查

### 移除
- @wsu2059q
  - 从 pyproject.toml 构建配置中移除 stubs 目录打包

---

## [2.3.6] - 2026/03/04
> 正式发布

**版本摘要**
本版本重构了初始化系统架构，将初始化器和反初始化器整合为SDK内部类；
简化项目入口模板，提供更便捷的启动方式；
优化热重载机制，确保资源清理的完全。

**升级建议**
- **可选升级**

**注意事项**
- 内部架构变更：`loaders/initializer.py` 已移除，相关类已整合到 `SDK` 类内部
- 热重载机制变更：现在使用信号文件进行跨进程通信，确保清理操作正确执行

**兼容性**
- 完全向后兼容

### 新增
- @wsu2059q
  - 新增 `runtime/cleanup.py` 清理管理模块，提供跨平台进程清理机制
  - 新增 `SDK.Uninitializer` 内部类，统一管理反初始化流程

### 重构
- @wsu2059q
  - 将 `Initializer` 类重构为 `SDK.Initializer` 内部类，提升代码内聚性
  - 优化热重载机制，使用信号文件进行跨进程通信，确保子进程正确执行清理
  - 简化 `main.py` 入口模板，使用 `sdk.run()` 代替手动初始化

### 修复
- @wsu2059q
  - 修复 CLI run 命令脚本路径默认值和环境初始化逻辑

---

## [2.3.6-dev.1] - 2026/02/27
> 开发版本

### 优化
- @wsu2059q
  - 优化 `loaders/module.py` 模块中检查全局懒加载的判断逻辑

### 修复
- @wsu2059q
  - 修复 `CLI/registry.py` 中 `__new__` 方法的类型注解语法错误

---
## [2.3.5] - 2026/02/26
> 正式发布

**版本摘要**
本版本进行了重要的架构重构和功能增强：重构了异常处理和配置管理模块架构，引入 `runtime` 包统一管理运行时配置；新增发送方法查询功能和 Event wrapper 修饰参数支持；优化了模块加载和命令处理逻辑。

**升级建议**
- **建议升级**
- 升级原因：
  - 架构重构提升了代码的可维护性和模块化程度
  - 新增的发送方法查询功能可帮助开发者更好地了解适配器能力
  - reply 方法的修饰参数支持让消息回复更灵活、更易用
  - SendDSL 修饰方法的默认实现提供了更友好的错误提示

**注意事项**
- 内部架构变更：`Core.exceptions` 模块已迁移至 `runtime.exceptions`，请更新相关导入(此为全局异常处理)
- `_bootstrap` 模块已重构为 `runtime.frame_config`，统一管理运行时配置(ep库内部的配置)

**兼容性**
- 完全向后兼容

---

## [2.3.5-dev.3] - 2026/02/24
> 开发版本

### 新增
- @wsu2059q
  - `adapter` 模块新增发送方法查询功能：
    - 新增 `list_sends(platform)` 方法，列出指定平台支持的所有发送方法
    - 新增 `send_info(platform, method_name)` 方法，获取发送方法的详细信息（参数、返回类型、文档等）
  - `Event.wrapper` 模块的 `reply` 方法新增修饰参数支持：
    - 新增 `at_users` 参数，支持 @多个用户，如 `["user1", "user2"]`
    - 新增 `reply_to` 参数，支持回复指定消息
    - 新增 `at_all` 参数，支持 @全体成员

---

## [2.3.5-dev.2] - 2026/02/19 - 2026/02/24
> 开发版本

### 新增
- @wsu2059q
  - `runtime` 新增 `get_config` 方法
  - `BaseAdapter` 的 `SendDSL` 新增修饰方法的默认实现：
    - 新增 `At()`、`Reply()`、`AtAll()`、`Raw_ob12()`、`Raw_json()` 方法的默认实现
    - 避免适配器未重写时导致模块出现 bug，提供友好的错误提示
  - 为 `AdapterManager` 和 `ModuleManager` 添加 `set_sdk_ref()` 方法，支持设置 SDK 引用

### 重构
- @wsu2059q
  - 重构异常处理和配置管理模块架构：
    - 将 `Core.exceptions` 模块移至 `runtime/exceptions.py`
    - 将 `_bootstrap.py` 重构为 `runtime/frame_config.py`，统一管理运行时配置
    - 新增 `runtime` 包，整合异常处理和配置管理功能
    - 移除 `setup_async_loop` 方法，改用 `setup_exception_handling`
  - 重构 SDK 架构，将核心方法迁移至 `SDK` 类：
    - 将 `__init__.py` 中的 SDK 逻辑方法迁移至 `sdk.py` 的 `SDK` 类
    - `__init__.py` 提供向后兼容性导出，支持现有代码继续使用函数式调用
  - 更新导入路径：
    - 所有引用 `_bootstrap` 的模块改为引用 `runtime`
    - 所有引用 `Core.exceptions` 的模块改为引用 `runtime.exceptions`
  - 将 `runtime/config.py` 重命名为 `runtime/frame_config.py`，优化模块命名
  - 提取配置服务获取逻辑到 `_get_config_service()` 独立函数，减少代码重复
  - 移除 `AdapterManager` 中平台名称大小写属性注册功能，简化适配器管理逻辑

### 移除
- @wsu2059q
  - 移除 `Core.exceptions` 模块导出，异常处理功能已迁移至 runtime 模块
  - 移除 `AdapterManager` 中的 `_register_platform_attributes()` 方法及相关平台属性注册逻辑

---

## [2.3.5-dev.1] - 2026/02/15
> 开发版本

### 新增
- @wsu2059q
  - 新增 `commands.must_at_bot` 配置，用于控制是否需要 @bot 才能执行命令

### 优化
- @wsu2059q
  - 优化 `Event` 模块中包装器wait_reply方法的逻辑，并且为返回值添加Event包装以支持更方便的获取事件内容

### 重构
- @wsu2059q
  - 移动 `Core._self_config` 模块到 `_bootstrap.py` 模块中，以便统一管理
  - 移动 `Core.Event` 模块的配置初始化逻辑到 `_bootstrap.py` 模块中

---
## [2.3.5-dev.0] - 2026/02/10
> 开发版本

### 优化
- @wsu2059q
  - 优化 `loaders/module.py` 模块中检查全局懒加载的判断逻辑

### 修复
- @wsu2059q
  - 修复 `CLI/registry.py` 中 `__new__` 方法的类型注解语法错误

---
## [2.3.4] - 2026/02/10
> 正式发布

**版本摘要**
本版本进行了重大架构重构：引入了统一的模块发现机制（finders）和加载策略系统（strategy），重构了模块和适配器的加载流程；新增测试基础设施，移除了 storage 快照功能和 Core.ux 模块；CLI 实现了命令自动发现机制。

**升级建议**
- **必须升级**（如果计划开发新模块）或 **建议升级**（现有项目）
- 升级原因：新的加载系统提供了更好的扩展性和可维护性，支持更灵活的模块加载策略

**注意事项**
⚠️ **重要：内部API变更与功能移除**
- 从此版本开始，内部结构和实现已发生变化
- 如果您的模块使用了部分内部API，请注意修改
- **移除的功能**：
  - `storage` 模块的快照功能已移除（`snapshot()`, `restore()` 等方法）
  - `Core.ux` 模块已移除
- 主要变更：
  - 模块加载器现在使用 `ModuleFinder` 和 `AdapterFinder` 查找
  - 加载策略支持 "all"、"enabled"、"manual" 三种模式
  - `BaseModule` 基类检查逻辑已调整（旧策略依然保持兼容）

**兼容性**
- 对外API保持兼容，现有代码无需修改

---
## [2.3.4-dev.3] - 2026/02/04
> 开发版本

### 新增
- @wsu2059q
  - 新增 `finders` 模块，实现统一的模块发现机制：
    - 新增 `BaseFinder` 基类，定义统一的 finder 接口
    - 新增 `ModuleFinder`，用于查找 `erispulse.module` entry-points
    - 新增 `AdapterFinder`，用于查找 `erispulse.adapter` entry-points
    - 新增 `CLIFinder`，用于查找 `erispulse.cli` entry-points
    - 提供 `find_all()` 和 `find_by_name()` 方法，支持批量查找和按名称查找

### 重构
- @wsu2059q
  - 重构加载系统使用 `finders` 模块：
    - `loaders/adapter.py` 现在使用 `AdapterFinder` 查找适配器
    - `loaders/module.py` 现在使用 `ModuleFinder` 查找模块
    - `CLI/utils/package_manager.py` 现在使用所有三个 finders 查找已安装包
  - CLI中的reloader直接移动到run命令内部进行定义

### 修复
- @wsu2059q
  - 修复入口直接从ErisPulse导入时发生错误的问题
  - 修复CLI部分命令中的导入错误

---

## [2.3.4-dev.2] - 2026/02/03
> 开发版本

### 新增
- @wsu2059q
  - 添加模块加载策略支持：
    - 新增 `loaders/strategy`，提供可扩展的加载策略系统
    - 支持 "all"（加载全部）、"enabled"（仅加载启用）和 "manual"（手动指定）三种策略
    - 新增 `LoadingStrategy` 抽象基类，定义策略接口
    - 新增 `LoadAllStrategy`、`LoadEnabledStrategy`、`LoadManualStrategy` 具体实现
    - `ModuleInitializer` 现在支持通过策略控制模块加载行为

### 重构
- @wsu2059q
  - 重构模块加载系统架构：
    - 移除 `BaseModule` 基类中的 `should_eager_load` 方法，改使用 `LoadingStrategy` 策略控制（旧策略依然保持兼容）

---

## [2.3.4-dev.1] - 2026/02/02
> 开发版本

### 新增
- @wsu2059q
  - 添加测试基础设施
  - `lifecycle` 模块：添加事件类型验证，防止空值提交

### 重构
- @wsu2059q
  - 重构模块加载系统架构：
    - 引入 `ManagerBase` 基类，统一适配器和模块管理器的配置接口
    - `AdapterManager` 和 `ModuleManager` 现在继承自 `ManagerBase`
    - 新增 `BaseLoader` 加载器抽象基类，定义标准加载接口
    - 引入 `AdapterLoader` 和 `ModuleLoader` 专用加载器
    - 新增 `ModuleInitializer` 初始化协调器，统一管理加载流程
    - 移除 `__init__.py` 中的 `LazyModule` 内部实现，迁移到 `loaders/module_loader.py`

### 优化
- @wsu2059q
  - `adapter` 模块：优化 `exists()` 方法，检查 `_adapters` 而非配置；`enable()`/`disable()` 支持自动注册
  - `module` 模块：增强 `register()` 的类验证和警告机制；`unload()` 改进错误处理
  - `router` 模块：优化 WebSocket 路由注销逻辑和 IPv6 回环地址显示
  - `logger` 模块：改进 `get_child()` 方法，支持非相对路径；`set_output_file()` 改进处理器管理
  - `exceptions` 模块：改进事件循环异常处理器设置，避免 RuntimeError

### 修复
- @wsu2059q
  - `command` 模块：修复 `aliases` 参数中的别名未正确注册的问题
  - 修复 `adapter.shutdown()` 后未清空 `_started_instances` 集合的问题
  - 修复 `logger.set_module_level()` 在模块未启用时的不必要检查

### 移除
- @wsu2059q
  - 移除 `storage` 模块的快照功能：
    - 移除 `snapshot()`, `restore()`, `list_snapshots()`, `delete_snapshot()` 方法
    - 移除 `set_snapshot_interval()` 方法和 `_check_auto_snapshot()` 内部方法
    - 移除 `ErisPulse.storage.max_snapshot` 配置项
    - 移除相关文档和示例代码
  - 移除 `devs/test.py` 交互测试脚本

### 文档
- @wsu2059q
  - 更新核心概念文档，添加 SDK 初始化流程和模块懒加载流程的 Mermaid 图表

---

## [2.3.4-dev.0] - 2026/01/27
> 开发版本

### 新增
- @wsu2059q
  - `cli`中 `epsdk run` ，如果入口不存在，现在会自动创建一个入口文件，而不是打印错误信息
  - `cli` 实现命令自动发现机制：
    - 动态扫描 `commands` 目录，自动加载继承自 `Command` 基类的所有命令
    - 无需手动注册命令，提高扩展性和维护性
  - `cli` 交互式安装支持预加载远程包列表，提升用户体验

### 重构
- @wsu2059q
  - 重构 `cli` 第三方命令执行逻辑，简化处理流程
  - 修正 `run` 命令中未使用的导入路径

### 移除
- @wsu2059q
  - 移除 `Core.ux` 模块及其相关功能
  - 移除 `SDKProtocol` 中 `UXManager` 相关代码和类型定义

---

## [2.3.3] - 2026/01/19
> 正式发布

**版本摘要**
本版本引入了 SDK Protocol 类型定义和 Event 包装类：SDK Protocol 提供完整的类型接口和运行时兼容性检查，显著改进了 IDE 类型提示和自动补全体验；Event 包装类提供便捷的事件访问方法，支持统一的 `reply()` 和 `wait_reply()` 方法。

**升级建议**
- **建议升级**
- 升级原因：大幅改善开发体验，提供更好的类型提示、自动补全支持和便捷的事件处理接口

**注意事项**
- 新增 `ErisPulse.run` 方法的 `keep_running` 参数（默认为 True），可能影响无头模式的行为
- 更新了核心模块导出列表，建议在升级后检查模块导入语句
- Event 对象在事件处理流程中自动创建，替换原有的 dict 对象

**兼容性**
- 完全向后兼容，无需修改现有代码

### 新增
- @wsu2059q
  - 提供 IDE 配置指南（VSCode、PyCharm、Vim/Neovim 等），支持完整的类型提示和自动补全
  - 新增 `sdk_protocol` 模块，提供 SDK Protocol 类型定义：
    - 定义 SDK 对象的完整类型接口，包含所有核心模块和方法
    - 支持运行时兼容性检查功能
    - 改进 IDE 类型提示和自动补全体验

### 变更
- @wsu2059q
  - 更新核心模块导出列表，添加：
    - `Core` 模块导出 Logger、LifecycleManager 等类
    - `lifecycle` 模块导出 LifecycleManager 类和实例
    - 提升模块公共接口的明确性和类型安全性
  - `ErisPulse.run` 方法添加 `keep_running` 参数，控制无头模式是否保持运行，默认值为 True

---

## [2.3.3-dev.1] - 2026/01/19
> 开发版本

### 变更
- @wsu2059q
  - 为 ErisPulse.run 方法添加 keep_running 参数，控制无头模式是否保持运行，默认值为 True

---
## [2.3.3-dev.0] - 2026/01/17
> 开发版本

### 新增
- @wsu2059q
  - `Event` 模块新增 Event 包装类，提供便捷的事件访问方法：
    - Event 类继承 dict，保持完全的字典兼容性，支持点式访问事件字段
    - 提供核心信息获取方法：`get_id()`, `get_time()`, `get_type()`, `get_platform()`, `get_self_info()`
    - 提供消息事件方法：`get_message()`, `get_text()`, `get_user_id()`, `get_group_id()` 及消息类型判断
    - 提供通知和请求事件方法：`is_notice()`, `is_request()`, `get_operator_id()` 等
    - 提供统一的 `reply()` 方法，支持通过 `method` 参数指定适配器的发送方法（Text、Image、Voice、Video、File 等）
    - 提供 `wait_reply()` 方法，支持等待用户回复，可设置超时、验证函数和回调函数
    - 提供命令信息和原始数据访问方法
    - Event 对象在事件处理流程中自动创建，替换原有的 dict 对象

### 优化
- @wsu2059q
  - `Event.command` 模块新增命令判断的兜底机制：
    - 优化命令处理流程，当从 `message` 列表中提取的 text 内容没有触发命令时，会自动检查 `alt_message` 字段是否符合触发命令的逻辑
    - 新增 `_process_text_for_command` 方法，用于统一处理文本内容的命令匹配逻辑
    - 改进 `_handle_message` 方法，确保即使适配器的 `message` 列表有问题，只要 `alt_message` 字段正确，命令仍能正常触发

### 文档
- @wsu2059q
  - 更新模块开发文档，新增 Event 包装类的详细使用说明和示例
  - 更新示例模块，演示 Event 包装类的新功能

---

## [2.3.2] - 2025/01/11
> 正式发布

**版本摘要**
本版本新增了第三方 CLI 模块的异步调用支持，并修复了相关异常处理问题。

**升级建议**
- **可选升级**
- 升级原因：仅在使用第三方 CLI 模块时建议升级

**注意事项**
- 无需代码变更，直接升级即可

**兼容性**
- 完全向后兼容

### 新增
- @wsu2059q
  - 新增第三方cli模块异步的调用支持

### 修复
- @wsu2059q
  - 修复第三方命令调用时可能出现的异常

---

## [2.3.1] - 2025/12/28
> 正式发布

**版本摘要**
本版本修复了 `ep-init` 命令中协程未等待的问题(直接初始化的功能，不包括交互式初始化)，并新增了同步包装器以确保命令行调用的正确性。

**升级建议**
- **建议升级**
- 升级原因：修复了初始化命令的bug，避免潜在问题

**注意事项**
- 无需代码变更，直接升级即可

**兼容性**
- 完全向后兼容

### 修复
- @wsu2059q
  - 修复 `ep-init` 命令使用 `init_task()` 导致协程未等待的问题
  - 新增 `init_sync()` 同步包装器，用于命令行直接调用初始化功能

---
## [2.3.0] - 2025/12/25
> 正式发布

**版本摘要**
本版本进行了重大架构升级：引入 `BaseModule` 基类标准化模块生命周期；新增 `lifecycle` 模块提供完整生命周期事件管理；重构 adapter 事件处理机制支持原始事件类型；优化 CLI 架构和配置系统；新增 UX 管理器和项目初始化功能；修复控制台颜色主题导入问题。

**升级建议**
- **建议升级**
- 升级原因：架构升级带来更好的可维护性和扩展性

**注意事项**
⚠️ **重要：API变更**
- `BaseAdapter` 中移除了原生事件监听方法（`emit`/`on`），统一使用 `adapter.on()` 和 `adapter.emit()`
- 所有适配器需要在事件数据中包含 `{platform}_raw_type` 字段
- 引入 `BaseModule` 基类，建议新模块继承该基类

**兼容性**
- 提供一定的向下兼容性，但建议尽快迁移到新方式

### 修复
- @wsu2059q
  - 修复控制台颜色主题导入报错导致安装中断的问题

---
## [2.3.0-dev.6] - 2025/12/22
> 开发版本

### 新增
- @wsu2059q
  - 新增框架配置解析文档，包括框架的默认配置项及其含义
  - 新增懒加载模块系统、路由管理器和事件系统文档
  - 新增懒加载全局配置支持，允许通过配置文件控制是否使用懒加载

### 变更
- @wsu2059q
  - 优化懒加载模块初始化逻辑，支持同步初始化和异步初始化分离
    - 新增 `_initialize_sync()` 方法，用于在异步上下文中进行同步调用
    - 新增 `_complete_async_init()` 方法，用于完成异步初始化部分
  - 优化CLI资源清理逻辑：
    - 分离适配器和模块清理逻辑

### 修复
- @wsu2059q
  - 修复懒加载模块在异步上下文中初始化可能出现的问题
  - 修复配置系统中的缓存一致性检查问题

---
## [2.3.0-dev.5] - 2025/12/21
> 开发版本

### 新增
- @wsu2059q
  - `utils` 模块新增包管理器和CLI工具：
    - 将 `PackageManager` 从主CLI模块迁移到 `utils/package_manager.py`
    - 将 `ReloadHandler` 从主CLI模块迁移到 `utils/reload_handler.py`
    - 将 `CLI` 从主CLI模块迁移到 `utils/cli.py`

### 变更
- @wsu2059q
  - 重构 CLI 架构：
    - 简化主入口点，将大部分功能移至 `utils` 模块
    - 优化模块导入结构，减少循环依赖
  - 优化 UX 管理器：
    - 改进适配器安装流程，增强错误处理
    - 更新远程包获取机制，提高稳定性
  - 回退 `module` 模块的基类检查机制，现在即使模块未继承基类也会被加载
  - `router` 模块优化：
    - 如果设定的为回环地址，会在日志中末尾处显示一个可访问的地址
  - `storage` 模块优化：
    - 选择默认的存储位置会在项目内，如果您不想使用当前位置，请修改 `config.toml` 文件中的配置：
    ```toml
      [ErisPulse.storage]
      # 设为 true 可使用包内全局数据库，false 或不设置则使用项目数据库
      use_global_db = false
    ```

### 修复
- @wsu2059q
  - 修复适配器安装过程中可能出现的异常处理问题
  - 修复在已有事件循环中调用 asyncio.run 导致的异常

---
## [2.3.0-dev.4] - 2025/12/20
> 开发版本

### 新增
- @wsu2059q
    - 新增 `UXManager` UX管理器，提供友好的界面和操作
    - 添加 `ux` 全局实例和 `ExperienceManager` 类到核心模块
    - 新增 CLI 命令：`init`, `status`, `config-wizard`
    - 为 CLI 添加项目初始化功能，支持指定项目名称和适配器
    - 添加系统状态查看功能，可查看模块和适配器详细信息
    - 新增交互式配置向导，引导用户完成基本配置

### 变更
- @wsu2059q
  - 日志系统优化：
    - 修复 `critical` 方法不再自动抛出异常，仅记录日志
    - 更新文档说明 `critical` 方法的行为变更
  - 适配器系统优化：
    - 简化适配器数据结构，移除冗余的多重映射
    - 重构适配器注册逻辑，提高代码可维护性
    - 优化平台属性注册方法，减少代码重复
  - 模块系统增强：
    - 加强模块验证逻辑，拒绝加载不继承自 `BaseModule` 的模块
    - 添加模块名称验证，确保模块命名规范
  - 配置系统改进：
    - 实现内存缓存机制，减少频繁的文件 I/O 操作
    - 添加延迟写入机制，多个配置操作会合并为单次写入
    - 新增强制保存和重新加载方法，提供更灵活的配置管理
  - CLI 命令优化：
    - 重构 `init` 命令，改为交互式初始化
    - 移除 `config-wizard` 命令，将配置向导集成到 `init` 命令中
    - 添加 `--quick` 选项，支持快速模式初始化项目
    - 新增交互式适配器配置功能

### 文档
- @wsu2059q
  - 添加 `ux-improvements.md` 文档，详细介绍用户体验改进
  - 更新 `quick-start.md`，添加新命令的使用说明
  - 更新 `core/cli.md`，添加新增的 CLI 命令文档
  - 更新 `core/modules.md`，添加用户体验管理器模块的说明

---
## [2.3.0-dev.3] - 2025/09/06
> 开发版本

### 新增
- @wsu2059q
    - 为 `logger` 模块的 `_get_caller` 方法添加空值检查，解决 Pylance 报告的 OptionalMemberAccess 警告
    - 为 `logger` 模块的方法添加显式返回值，解决所有代码路径必须返回布尔值的类型检查问题
    - `exceptions` 模块中 `setup_async_loop` 函数添加对事件循环有效性检查，增强异常处理的健壮性
    - 为 `Logger` 类添加更安全的调用者识别机制，增强日志记录的可靠性

### 变更
- @wsu2059q
  - 重构核心模块并优化日志管理：
    - 优化 `Logger` 类的模块化和异常处理
    - 改进 `Logger` 类中的调用栈分析逻辑，增加空值检查
    - 为所有方法添加明确的返回值，解决类型检查问题
  - 改进数据库操作和快照管理的异常处理
  - 调整模块加载器和初始化器的异常处理逻辑
  - 优化路由管理器中HTTP和WebSocket路由的注销功能
  - 调整模块加载器中模块状态管理逻辑，不再强制退出未继承抽象类的模块 *2025/11/01
  - 调整适配器加载时注解问题导致的无法访问的错误处理逻辑

### 修复
- @wsu2059q
  - 修复 `Logger` 类中部分方法在极端情况下可能不返回布尔值的问题
  - 修复模块卸载功能中参数默认值处理不当的问题
  - 修复路由注销功能中路径处理和路由查找的问题
  - 修复数据库事务处理中连接管理的问题

---
## [2.3.0-dev.2] - 2025/08/26
> 开发版本

### 新增
- @wsu2059q
  - `lifecycle` 模块新增完整的生命周期事件管理功能：
    - 支持标准生命周期事件的提交和监听
    - 实现点式结构事件监听（如 `module.init` 可被 `module` 监听）
    - 添加事件计时器功能，用于测量操作耗时
    - 增加事件数据格式验证机制

### 变更
- @wsu2059q
  - 优化SDK初始化流程：
    - 改进错误处理机制，提供更详细的加载失败信息
    - 优化生命周期事件触发时机和数据结构
  - 更新生命周期事件命名规范：
    - 将 `lifecycle.emit` 方法重命名为 `lifecycle.submit_event`
    - 统一事件数据格式，包含事件名称、时间戳、来源、描述和数据
  - 重构模块和适配器加载逻辑：
    - 使用异步并发方式处理模块注册和初始化
    - 改进适配器状态变化事件的提交机制

### 修复
- @wsu2059q
  - 修复模块加载过程中生命周期事件提交的问题
  - 修复适配器注册和加载时的异常处理机制
  - 修复服务器启动和停止时生命周期事件的正确提交

---

## [2.3.0-dev.1] - 2025/08/24

### 新增
- @wsu2059q
  - `ModuleInitializer` 模块新增并行加载支持

### 变更
- @wsu2059q
  - 优化SDK初始化流程：
    - 改进错误处理机制，提供更详细的加载失败信息
    - 优化生命周期事件触发时机和数据结构

---

## [2.3.0-dev.0] - 2025/08/23
> 由于一些机制的变更，将版本提升至 2.3.x 开发版本
> 虽然提供了一定的向下兼容性，但仍然不建议继续使用旧方式

### 新增
- @wsu2059q
  - `adapter` 模块新增平台原始事件类型字段支持：
    - 所有适配器现在需要在事件数据中包含 `{platform}_raw_type` 字段，用于标识原始事件类型
    - 更新了事件监听器，支持通过 `raw=True` 参数监听原始事件
  - `BaseAdapter` 基类新增对原始事件类型的支持

### 变更
- @wsu2059q
  - 重构 `adapter` 模块事件处理机制：
    - 移除了 `BaseAdapter` 中的原生事件监听方法（`emit`/`on`）
    - 标准化事件监听接口，现在通过 `adapter.on()` 统一处理事件
    - 更新了适配器注册逻辑，支持传递适配器信息参数
  - 优化模块系统：
    - 引入 `BaseModule` 基类，为模块提供标准化的生命周期方法
    - 模块管理器现在支持模块注册、加载和卸载功能

### 修复
- @wsu2059q
  - 修复适配器事件处理中的平台匹配问题
  - 修复模块系统中模块重复加载的问题
  - 修复SDK初始化过程中可能的异步循环问题

---

## [2.2.2-dev.0] - 2025/08/20

### 新增
- @wsu2059q
  - 新增 `lifecycle` 模块，提供生命周期管理功能
  - 新增 `module` 模块，提供模块管理功能

### 变更
- @wsu2059q
  - 使用 `ruff` 作为代码检查工具
  - 删除 `模块注册器模块` 现在由 `config` 直接进行模块状态控制
  - 删除 `BaseAdapter` 基类中的 `emit/on` 等原生事件监听方法，现在需要尽快使用 `adapter.on/emit` 提交OneBot12事件
  - 标准化模块加载逻辑

---

## [2.2.1] - 2025/08/19
> 正式发布

**版本摘要**
本版本新增交互式命令支持，支持命令处理器等待用户回复；增强事件处理器管理功能，支持处理器注销；修复事件处理器重复注册导致事件被多次处理的问题。

**升级建议**
- **建议升级**
- 升级原因：修复了事件处理器重复注册的重要问题，新增交互式命令功能

**注意事项**
- 无需代码变更，直接升级即可

**兼容性**
- 完全向后兼容

---

## [2.2.1-dev.0] - 2025/08/18

### 新增
- @wsu2059q
  - `Event.command` 模块新增交互式命令支持：
    - 添加 `wait_reply` 方法，支持命令处理器等待用户回复并进行交互
    - 支持设置提示消息、超时时间、验证函数和回调函数
    - 提供优雅的多轮对话命令实现机制
  - `Event` 模块增强事件处理器管理功能：
    - 为所有事件子模块（command、message、notice、request、meta）每种装饰器添加对应的处理器注销方法
    - 支持通过装饰器注册的事件处理器可以被取消注册

### 变更
- @wsu2059q
  - 重构 `Event` 模块内部实现：
    - 优化事件处理器的存储和查找机制，提高效率
  - 遵循 ErisPulse 注释风格规范，完善所有事件处理模块的注释

### 修复
- @wsu2059q
  - 修复命令处理器注销时未能清理相关配置的缺陷
  - 修复 `wait_reply` 功能在并发情况下的潜在竞争条件问题
  - 修复事件处理器重复注册导致事件被多次处理的问题：
    - 优化 `BaseEventHandler` 类，确保每个事件类型只向适配器注册一次处理器
    - 防止使用多个 `@message` 等装饰器时事件被重复触发多次的问题
    - 提高事件处理效率，避免不必要的重复处理

---

## [2.2.0] - 2025/08/18
> 正式发布

**版本摘要**
本版本新增 `Event` 核心模块，提供统一的事件处理机制，支持命令、消息、通知、请求、元事件等多种事件类型的装饰器注册；新增 `module` 模块用于模块管理；命令系统支持权限检查、隐藏命令、别名配置等功能。

**升级建议**
- **建议升级**
- 升级原因：Event 模块提供更便捷的事件处理方式，简化开发流程

**注意事项**
- 原 `mods` 模块更名为 `module_registry`，如有使用请修改导入
- 移除了 `event_manager` 模块，统一使用 `adapter` 模块进行事件发送和接收

**兼容性**
- 部分内部模块重命名，核心功能保持兼容

---

## [2.2.0-dev.2] - 2025/08/18

### 新增
- 添加 `Event` 模块更多功能：
  - 命令支持权限检查功能，可通过 `permission` 参数设置权限检查函数
  - 命令支持隐藏功能，可通过 `hidden` 参数控制命令在帮助中是否显示
  - 命令支持更灵活的别名配置，可通过 `aliases` 参数设置额外别名
  - 命令帮助系统增强，支持显示隐藏命令选项
  - 添加命令执行错误和权限拒绝的自动消息反馈机制
- `Event` 模块配置增强：
  - 添加 `allow_space_prefix` 配置项，支持 "/ command" 格式的命令

### 变更
- 重构 `Event` 模块设计：
  - 移除 `event_manager` 模块，避免与 `adapter` 模块功能重复
  - 简化中间件系统，移除全局和局部中间件以避免复杂性
  - 用户应通过 `adapter` 模块进行事件的发送和接收
- 优化 `Event` 模块注释和文档，遵循 ErisPulse 注释风格规范

### 修复
- 修复命令处理中的一些潜在错误处理问题
- 修复命令别名处理逻辑中的边界情况

---

## [2.2.0-dev.1] - 2025/08/17

### 新增
- 添加 `module` 模块，用于快速获取模块实例/信息/管理
- 添加 `module_registry` 模块，用于管理模块注册信息

### 变更
- 原 `mods` 模块更名为 `module_registry`，大多模块未使用 `mods` 模块，故未进行兼容操作，请注意修改
- 优化 版本信息 变量，使用pip包信息

---

## [2.2.0-dev.0] - 2025/08/17
> 开发版本

### 新增
- 新增 `Event` 核心模块，提供统一的事件处理机制
  - `Event.command` 子模块，支持基于装饰器的命令注册和处理
  - `Event.message` 子模块，支持消息事件处理
  - `Event.notice` 子模块，支持通知事件处理
  - `Event.request` 子模块，支持请求事件处理
  - `Event.meta` 子模块，支持元事件处理
  - `Event.event_manager` 子模块，提供全局事件管理功能
  - `Event.exceptions` 子模块，提供事件系统相关异常类型
- `Event` 模块支持优先级控制，允许为事件处理器设置执行优先级
- `Event` 模块支持条件处理器，允许根据条件决定是否执行处理器
- `Event` 模块支持中间件机制，提供全局和局部中间件功能
- `Event` 模块支持自定义事件类型创建和处理

### 变更
- 更新文档，添加 `Event` 模块使用指南
- 更新示例模块，演示 `Event` 模块的使用方法

---

## [2.1.15] - 2025/08/16
> 正式发布

---

## [2.1.15-dev.4] - 2025/08/12

### 变更
- 改进包管理器的进度显示，修复富文本进度条显示不正确的问题

### 修复
- 修复Windows平台上 `self-update` 命令因文件占用导致的更新失败问题
- 修复升级过程中可能因网络或权限问题导致的进程阻塞问题

---

## [2.1.15-dev.3] - 2025/08/12

### 新增
- CLI工具新增 `self-update` 命令，支持交互式更新ErisPulse SDK本身
- `install`、`uninstall` 和 `upgrade` 命令现在支持同时处理多个包
- CLI新增版本兼容性检查，在安装/升级包时会检查 `min_sdk_version` 要求
- 新增 `search` 命令，支持搜索本地和远程包

### 变更
- 优化CLI交互体验，提供更友好的命令行界面
- 改进版本排序算法，确保正确识别最新版本
- 更新CLI文档，添加多包操作和self-update命令说明

### 修复
- 修复版本比较逻辑中的错误，确保正确识别最新稳定版本
- 修复包管理器中的异常处理问题

---

## [2.1.15-dev.2] - 2025/08/12

### 新增
- 添加 `sdk.init_task` 方法，用于在异步模式下初始化 SDK

### 变更
- 重构 `env` 模块为 `storage`，提供更准确的存储管理功能命名
- 保持 `env` 向后兼容性，标记为弃用状态，建议迁移到 `storage` 模块

---

## [2.1.15-dev.1] - 2025/08/10
### 变更
- 更新硬仓库地址

---

## [2.1.14] - 2025/08/03
### 修复
- 加强CLI运行时重载机制，确保适配器正确停止，避免僵尸线程产生

---

## [2.1.14-alpha.1] - 2025/08/02

### 新增
- logger 模块新增 get_child 方法，支持创建子模块日志记录器，便于更好地组织和识别日志来源

---

## [2.1.14-dev.2] - 2025/08/02
### 新增
- `exceptions` 模块新增 `setup_async_loop` 方法，支持用户为指定事件循环设置异常处理器
- 新增 `erispulse_config` 模块，专门管理框架自身配置，与用户配置分离

### 变更
- `exceptions` 模块优化了异常处理器的工作原理
- 将框架配置从 `config` 模块中分离，提升代码结构清晰度

---

## [2.1.14-dev.1] - 2025/08/01
### 变更
- 弃用并删除 `util` 核心模块
- 彻底弃用 `raisser` 的错误处理机制

### 新增
- 新增 `exceptions` 模块替代原有的 `raiserr` 模块
- 新增 `router` 模块代替 `server`，功能保持兼容

### 修复
- 修复路由注册时的方法命名问题

---

## [2.1.14-dev.0] - 2025/07/28
### 变更
- 增强 CLI 交互体验
- 彻底弃用并删除 `env.py` 的功能实现

---

## [2.1.13] - 2025/07/23
### 新增
- `__init__.py` 文件新增 `__version__` 变量，用于获取当前版本号

---

## [2.1.13-pre.3] - 2025/07/22
### 修复
- 修复 `epsdk init` / `epsdk upgrade` 命令无法正常运行问题
- 修复第三方CLI命令无法被正常加载的问题

---

## [2.1.13-pre.2] - 2025/07/22

### 新增
- 新增更完善的方法注释，用于生成API文档

### 变更
- 删除无用的logging模块

---
 
## [2.1.13-pre.1] - 2025/07/22
### 新增
- CLI工具新增UV工具链自动检测功能
- 热重载功能增加对`.env`文件变更的监控支持
- 实现远程包简称到完整包名的自动解析功能

### 变更
- 重构CLI核心架构，拆分为独立的功能模块
- 控制台输出全面升级为Rich库实现
- `install`命令支持自动识别远程模块/适配器简称
- `run --reload`增强文件监控稳定性
- 改进包管理器的进程安全退出机制

### 修复
- 修复Windows平台颜色初始化问题
- 解决第三方CLI命令加载时的类型检查错误
- 修正包版本检查时的缓存一致性问题

---

## [2.1.12] - 2025/07/21
### 新增
- `list` 添加 `cli拓展` 项目
- `list-remote` 添加 `cli拓展` 项目

### 变更
- `logger` 默认关闭markup，避免在控制台输出时出现混淆的情况

---

## [2.1.11] - 2025/07/21
### 变更
- `epsdk run` 命令支持无参数运行，添加自动初始化功能

---

## [2.1.10] - 2025/07/20
### 新增
- 新增 `config` 模块，用于分离 `env` 模块功能，提供更友好的配置管理体验

### 变更
- 标准日志处理器替换为RichHandler，提供更美观的彩色控制台日志输出
- 使用独立的 `Config` 模块处理核心配置，避免与 `env` 模块冲突
- 兼容性性改进：解决情况下部分循环引用问题

### 修复
- 修复设置模块日志等级时，调用错误的问题

---

## [2.1.7] - 2025/07/19
### 新增
- 引入富文本输出支持
- 新增 `enable` / `disable` 命令，用于启用/禁用模块
- 优化CLI交互体验, 新增自动使用 `uv` 工具链（如果存在）
- 添加对于第三方CLI模块的支持，运行注册到 `epsdk` 命令下的自定义命令

### 变更
- 修改 `mods` 模块存储/状态前缀以适配新的模块加载机制
- 调整 `CLI` 中的 run 方法，使其支持监控 `config.toml` 文件变化

### 修复
- 修复windows依赖引入错误
- f-string 语法兼容性修复

---

## [2.1.5] - 2025/07/18
### 新增
- Core 模块新增 `AdapterBase` 类

### 变更
- 标记 `raiserr` 为弃用状态，使用 原生 `raise` 语句代替
- 删除核心部分对于 `raiserr` 的依赖

---

## [2.1.4] - 2025/07/17
### 修复
- 修复 CLI 中的 response.json 强制要求请求体为 json 格式的问题

---

## [2.1.3] - 2025/07/17

### 修复
- 修正 `Send` 对象中 `_account_id` 属性错误，统一使用 `_account` 属性名
- 修复错误处理流程中二次触发相同异常的问题

---

## [2.1.2] - 2025/07/17

### 新增
- `Send` 链式调用新增 `Using` 方法，用于指定账号（该操作会与 `To` 方法类似，设置 `self._account_id` 属性）

### 变更
- 引入独立的 `ErisPulse` toml 配置项，用于集中管理框架相关配置
- 将 `Send` 默认提供的 `Text` 方法更名为 `Example` 方法，避免与某些模块的 `Text` 方法检测逻辑冲突
- 懒加载机制改进：对于定义了 `should_eager_load` 属性的模块，现在统一在代理到懒加载器后执行加载，优化模块初始化流程

---

## [2.1.1] - 2025/07/17

### 变更
- 删除CLI `search` 命令，使用 `list-remote` 命令代替（仅包括收录模块）

### 修复
- 修复懒加载时一些魔术方法无法被调用并初始化的问题
- 修复初始化时被重复赋值None的错误

---

## [2.1.0] - 2025/07/14

### 新增
- 新增统一的底层适配器服务器统一管理，支持 webhook/websocket 模式
- 添加 `server` 核心模块
- 新增 `list-remote` 命令

- 添加了模块懒加载功能
- `sdk.load_modules()` 方法，指定需要直接加载的模块
- 添加模块内的 `should_eager_load` 属性方法检测，用于控制模块是否立即加载（无视懒加载）
- 添加 `env.setConfig`/`env.getConfig` 方法，用于直接在项目 `config.toml` 文件中设置/获取配置项

- 适配器加载支持，新增`AdapterLoader`类处理适配器加载
- 模块加载器现在支持区分普通模块和适配器模块

### 变更
- install 命令添加了对于远程package映射表的安装支持
- `env.py` 已经弃用，启用了项目文件内的 `config.toml` 文件代替配置管理
- BaseAdapter 中继承上的 `emit_onebot12`/`on_onebot12` 方法现在已弃用
- 改为 adapter.emit/on 方法来提交/获取全局OneBot12事件
- 弃用模块的依赖加载及拓扑排列相关方法，使用懒加载进行代替
- 重构模块加载系统，将功能拆分为：
  - `ModuleLoader`: 处理模块加载
  - `AdapterLoader`: 处理适配器加载
- 重构`ModuleInitializer`类，支持适配器和模块的差异化初始化
- 移除了旧版模块管理命令的相关代码

### 修复
- 修复监听时可能无法获取事件的问题

---

## [2.0.0]

### 新增
- Pypi包模块加载机制 | 并重构兼容部分
- Pypi包加载时自动检查包含的模块依赖关系

### 变更
- 优化模块加载逻辑，将模块加载拆分为 主加载逻辑 - 1.包加载逻辑 2.模块加载逻辑
- 添加新的 ModuleInfo 项 -> package; 用来检测包之间的ep模块依赖关系
- 添加贡献指南, 规范底层模块方法注释逻辑
- 删除堆成石的模块注释, 并增加代码注释率

### 修复
- 使用 `send = adapter.<适配器名>.To()` 直接创建发送器, 导致调用旧适配器方法而抛出异常的情况

1.x.x 版本更新日志请查看分支日志
