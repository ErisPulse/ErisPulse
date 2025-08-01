# 更新日志

所有版本更新遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范。

> **如何阅读本日志**
> 每个版本分为“新增”、“变更”、“修复” 等部分。建议开发者在升级前先阅读对应版本的 Breaking Change 和修复内容。

> **贡献日志**
> 如需为新版本添加日志，请在对应版本号下补充内容，并注明日期和主要贡献者。

---

## [2.1.14-alpha.1] - 2025/08/02

### 新增
- logger 模块新增 get_child 方法，支持创建子模块日志记录器，便于更好地组织和识别日志来源

---

## [2.1.14dev2] - 2025/08/02
### 新增
- `exceptions` 模块新增 `setup_async_loop` 方法，支持用户为指定事件循环设置异常处理器
- 新增 `erispulse_config` 模块，专门管理框架自身配置，与用户配置分离

### 变更
- `exceptions` 模块优化了异常处理器的工作原理
- 将框架配置从 `config` 模块中分离，提升代码结构清晰度

---

## [2.1.14dev1] - 2025/08/01
### 变更
- 弃用并删除 `util` 核心模块
- 彻底弃用 `raisser` 的错误处理机制

### 新增
- 新增 `exceptions` 模块替代原有的 `raiserr` 模块
- 新增 `router` 模块代替 `server`，功能保持兼容

### 修复
- 修复路由注册时的方法命名问题

---

## [2.1.14dev0] - 2025/07/28
### 变更
- 增强 CLI 交互体验
- 彻底弃用并删除 `env.py` 的功能实现

---

## [2.1.13] - 2025/07/23
### 新增
- `__init__.py` 文件新增 `__version__` 变量，用于获取当前版本号

---

## [2.1.13pre3] - 2025/07/22
### 修复
- 修复 `epsdk init` / `epsdk upgrade` 命令无法正常运行问题
- 修复第三方CLI命令无法被正常加载的问题

---

## [2.1.13pre2] - 2025/07/22

### 新增
- 新增更完善的方法注释，用于生成API文档

### 变更
- 删除无用的logging模块

---

## [2.1.13pre1] - 2025/07/22
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