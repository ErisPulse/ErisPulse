# `ErisPulse.runtime.package_reload` 模块

---

## 模块概述


ErisPulse 已安装发行版热重载监控

监控已加载模块 / 适配器来源发行版的文件变化（pip 升级 / 直接修改包文件），
变化时自动重载对应组件——升级即生效，无需重启或手动调用 reload。

由 ``ErisPulse.SDK`` 的同名私有方法薄委托调用；SDK 上保留方法形态，
以便测试与子类按 ``patch.object(SDK, "_start_package_reload_watcher")`` 方式补丁。

> **提示**
> 1. 经 ``ErisPulse.framework.auto_reload`` 配置节启用（默认关闭）
> 2. 仅监控带发行版信息的组件（entry-points 安装包）；本地插件与运行时注册组件不在监控面
> 3. 监控范围 ACL：allow 白名单（空 = 全部）+ deny 黑名单（优先），元素支持 glob

---

## 函数列表


### `_iter_entry_points(group: str) -> list[Any]`

按组读取 entry-points（3.10 / 3.11+ 两种返回形态兼容）

---


## 类列表


### `class _DistWatch`

单个发行版的监控状态：组件清单与文件签名快照


### `class PackageReloadWatcher(HotReloadWatcherBase)`

已安装发行版热重载监控器

后台守护线程按固定间隔对受监控发行版做两级签名扫描（mtime/size 快扫、
命中后 sha256 确认），变化经主事件循环逐组件调用重载管理器。

监控范围 ACL：deny 优先于 allow；allow 为空表示"除 deny 外全部已加载
组件"。名单元素支持 glob，组件名与发行版名均参与匹配（按 PEP 503 归一）。

- **sdk** (`SDK`): 实例（组件清单与重载编排的来源）
- **interval**: 轮询间隔秒数（缺省读 ``framework.auto_reload.interval``）
- **allow**: 白名单（组件名或发行版名，glob 支持；空 = 全部）
- **deny**: 黑名单（优先于 allow）


#### 方法列表


##### `_prepare() -> bool`

**内部方法** 解析监控对象并建立文件签名；无可监控发行版时返回 False

---


##### `_begin() -> None`

**内部方法** 启动轮询守护线程

---


##### `_shutdown() -> None`

**内部方法** 停止轮询守护线程

---


##### `_resolve_watches() -> dict[str, _DistWatch]`

经 entry-points 反查当前已加载组件的来源发行版

---


##### `_collect_files(watch: _DistWatch) -> None`

登记发行版的 .py 文件签名（mtime/size 与 sha256）

---


##### `_find_dist(dist_name: str) -> Any`

按发行版名查找 Distribution 对象（跨组复用同一份缓存映射）

---


##### `_refresh_watches() -> None`

重解析监控对象并重建全部文件签名

---


##### `_file_hash(path: Path) -> str | None`（staticmethod）

文件 sha256（不可读时为 None）

---


##### `_scan_once() -> list[tuple[_DistWatch, list[tuple[str, str]]]]`

单轮扫描，返回发生实质变化的 (发行版, 组件) 列表

---


##### `_hash_changed(watch: _DistWatch, path: Path) -> bool`

sha256 确认（mtime 抖动不算变化）；新哈希回写快照

文件消失（卸载 / 升级窗口）且快照有记录时视为变化；从未可读的
文件不计入。

---


##### `_poll_once() -> None`

**内部方法** 单轮扫描：冷却过滤 → 刷新签名 → 主循环调度重载

---


##### `async _reload(watch: _DistWatch, components: list[tuple[str, str]]) -> None`

逐组件调用对应管理器的重载（自带快照回滚与依赖级联）

---

