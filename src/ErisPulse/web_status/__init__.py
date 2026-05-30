"""
ErisPulse 错误页面静态资源

包含 HTTP 错误页面使用的图片资源。
由 Core/router.py 导入并挂载为 /status-assets 静态路由。

{!--< tips >!--}
图片文件:
- 4xx.png    — 4xx 错误（404、403 等）
- 5xx.png    — 5xx 服务器错误
- unknow.png — 未知异常
{!--< /tips >!--}
"""

import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
