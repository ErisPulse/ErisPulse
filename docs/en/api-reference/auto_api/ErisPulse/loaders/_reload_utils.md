# `ErisPulse.loaders._reload_utils` 模块

---

## 模块概述


热重载共用工具：字节码缓存清理与卸载前语法预检

模块与适配器两条重载管线共用的唯一实现；两侧薄封装只负责收集候选
源文件与提供各自的 i18n 文案键。

---

## 函数列表


### `expand_source_files(file_attrs: Iterable[Any]) -> 'list[Path]'`

把一组 ``__file__`` 候选展开为源文件列表

包入口（``__init__.py``）递归展开为包内全部 ``.py``；单文件仅接受
``.py`` 后缀（C 扩展 / 内存模块天然跳过）。

- **file_attrs**: ``__file__`` 属性值候选（None / 空值自动跳过）

**返回值**: 去重后的源文件路径列表

---


### `clear_source_caches(mods: Iterable[Any]) -> None`

清除模块对象对应源文件的字节码缓存（``__pycache__``/*.pyc）

同秒内且字节数不变的源码改写不会使 pyc 失效（mtime 秒级粒度 +
size 校验），purge ``sys.modules`` 后重导入仍会命中旧字节码——
重载路径必须显式清除，保证「改完代码再 reload 必定读到新代码」。

- **mods**: 模块对象（或 None）的可迭代集合

---


### `module_objects_by_names(names: 'list[str]') -> 'list[Any]'`

按顶层模块名从 ``sys.modules`` 收集现存模块对象

- **names**: 顶层模块名列表

**返回值**: 找到的模块对象（缺失名跳过）

---


### `check_reload_identity(*, new_class: Any, old_class: Any, label: str, i18n_key: str) -> bool`

重载后的类身份核对：新旧类对象是否不同

新旧类均非空时按 ``is`` 比对；身份未变化说明进程内可能仍运行旧代码
（如 C 扩展等清不掉的缓存），告警提示。

- **new_class**: 重载后注册表中的类对象
- **old_class**: 重载前快照中的类对象
- **label**: 组件名（日志用）
- **i18n_key**: 身份未变化告警的文案键（调用方按组件类型提供）

**返回值**: identity_changed（True = 代码确实换新）

---


### `precheck_source_files(label: str, source_files: 'list[Path]', *, i18n_key: str) -> bool`

卸载前语法预检：对源文件列表逐文件 ``ast.parse``

预检失败（语法错误）即拒绝重载——旧实例未卸载、继续服务，语法
错误永远不会把组件推进"半死状态"。超过文件数上限
（``MODULE_RELOAD_PRECHECK_MAX_FILES``）时跳过预检并记 debug，
交由快照回滚兜底。

- **label**: 组件名（日志用）
- **source_files**: 待检源文件列表（空列表直接通过）
- **i18n_key**: 预检失败日志的文案键（调用方按组件类型提供）

**返回值**: 是否通过（True = 允许继续重载流程）

---

