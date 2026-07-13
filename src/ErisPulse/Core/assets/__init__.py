"""
ErisPulse 前端资源

提供根路由页面和错误页面的 HTML/CSS 模板渲染。
模板文件在模块加载时一次性读取并缓存，运行时仅做字符串替换。

{!--< internal-use >!--}
由 Core/router.py 导入，提供以下函数：
- render_root_page(): 渲染根路由页面
- render_error_page(): 渲染错误页面
{!--< /internal-use >!--}
"""

import os
from typing import Dict, List, Optional, Union

from typing import TypedDict

_StrDict = Dict[str, str]

class HomeEntry(TypedDict, total=False):
    """主页入口按钮描述
    
    name 可为纯文本 (str) 或 i18n 字典格式 (dict[str, str])
    """
    name: Union[str, _StrDict]
    url: str
    icon_svg: str


_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_file(filename: str) -> str:
    """从包目录加载文件内容"""
    with open(os.path.join(_PACKAGE_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


# 一次性加载并缓存模板和 CSS
_ROOT_TEMPLATE = _load_file("root.html")
_ROOT_CSS = _load_file("root.css")
_ERROR_TEMPLATE = _load_file("error.html")
_ERROR_CSS = _load_file("error.css")


def _render_entry(name: str, url: str, icon_svg: str = "") -> str:
    """将单个入口按钮渲染为 HTML"""
    svg = f'<span class="entry-svg">{icon_svg}</span>' if icon_svg else ""
    return f'<a class="entry" href="{url}">{svg}<span>{name}</span></a>'


def render_root_page(
    version: str,
    sub_text: str,
    docs_link: str,
    community_link: str,
    entries: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    渲染根路由页面 HTML

    :param version: str ErisPulse 版本号
    :param sub_text: str 副标题文本
    :param docs_link: str 文档链接显示文本
    :param community_link: str 社区链接显示文本
    :param entries: 主页入口按钮列表，每项含 name/url/icon_svg，name 必须为已解析的纯文本
    :return: str 完整的 HTML 页面字符串
    """
    entries_html = ""
    if entries:
        for entry in entries:
            entries_html += _render_entry(
                name=entry.get("name", ""),
                url=entry.get("url", "#"),
                icon_svg=entry.get("icon_svg", ""),
            )

    html = _ROOT_TEMPLATE
    html = html.replace("{{ROOT_CSS}}", _ROOT_CSS)
    html = html.replace("{{VERSION}}", version)
    html = html.replace("{{SUB_TEXT}}", sub_text)
    html = html.replace("{{ENTRIES_HTML}}", entries_html)
    html = html.replace("{{DOCS_LINK}}", docs_link)
    html = html.replace("{{COMMUNITY_LINK}}", community_link)
    return html


def render_error_page(
    code: int,
    title: str,
    home_link: str,
    desc: Optional[str] = None,
) -> str:
    """
    渲染错误页面 HTML

    :param code: int HTTP 状态码
    :param title: str 错误标题
    :param home_link: str 返回首页链接显示文本
    :param desc: str 错误描述 (可选)
    :return: str 完整的 HTML 页面字符串
    """
    desc_html = f'<p class="page-desc">{desc}</p>' if desc else ""
    html = _ERROR_TEMPLATE
    html = html.replace("{{ERROR_CSS}}", _ERROR_CSS)
    html = html.replace("{{CODE}}", str(code))
    html = html.replace("{{TITLE}}", title)
    html = html.replace("{{DESC_HTML}}", desc_html)
    html = html.replace("{{HOME_LINK}}", home_link)
    return html
