# `ErisPulse.Core.assets.__init__` 模块

---

## 模块概述


ErisPulse 前端资源

提供根路由页面和错误页面的 HTML/CSS 模板渲染。
模板文件在模块加载时一次性读取并缓存，运行时仅做字符串替换。

> **内部方法**
由 Core/router.py 导入，提供以下函数：
- render_root_page(): 渲染根路由页面
- render_error_page(): 渲染错误页面

---

## 函数列表


### `_load_file(filename: str)`

从包目录加载文件内容

---


### `_render_entry(name: str, url: str, icon_svg: str = '')`

将单个入口按钮渲染为 HTML

---


### `render_root_page(version: str, sub_text: str, docs_link: str, community_link: str, entries: Optional[List[Dict[str, str]]] = None)`

渲染根路由页面 HTML

- **version** (`str`): ErisPulse 版本号
- **sub_text** (`str`): 副标题文本
- **docs_link** (`str`): 文档链接显示文本
- **community_link** (`str`): 社区链接显示文本
- **entries** (`主页入口按钮列表，每项含`): name/url/icon_svg，name 必须为已解析的纯文本
**返回值** (`str`): 完整的 HTML 页面字符串

---


### `render_error_page(code: int, title: str, home_link: str, desc: Optional[str] = None)`

渲染错误页面 HTML

- **code** (`int`): HTTP 状态码
- **title** (`str`): 错误标题
- **home_link** (`str`): 返回首页链接显示文本
- **desc** (`str`): 错误描述 (可选)
**返回值** (`str`): 完整的 HTML 页面字符串

---


## 类列表


### `class HomeEntry(TypedDict)`

主页入口按钮描述

name 可为纯文本 (str) 或 i18n 字典格式 (dict[str, str])

