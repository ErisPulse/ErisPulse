"""
Create 命令实现

脚手架工具，快速创建 Module / Adapter 项目模板
"""

import datetime
import sys
from argparse import ArgumentParser
from pathlib import Path

from rich.prompt import IntPrompt, Prompt
from rich.text import Text

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils.display import prompt_validated, section_header

_LICENSE_TEMPLATE = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_MODULE_PYPROJECT = """[project]
name = "ErisPulse-{name}"
version = "1.0.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.10"
license = {{ file = "LICENSE" }}
authors = [ {{ name = "{author}", email = "{email}" }} ]

dependencies = [
]

[project.urls]
"homepage" = "{homepage}"

[project.entry-points]
"erispulse.module" = {{ "{name}" = "{name}:Main" }}
"""

_MODULE_INIT = """from .Core import Main
"""

_MODULE_CORE = """from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command, message, notice


class Main(BaseModule):
    \"\"\"
    {name}模块

    继承自BaseModule基类，实现了标准化的模块生命周期管理和事件处理
    \"\"\"

    def __init__(self, sdk=None):
        from ErisPulse import sdk as _sdk
        self.sdk = _sdk if sdk is None else sdk
        self.logger = self.sdk.logger.get_child("{name}")
        self.storage = self.sdk.storage
        self.adapter = self.sdk.adapter
        self.client = self.sdk.client

        self.logger.info("{name} 初始化完成")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100
        )

    async def on_load(self, event: dict) -> bool:
        \"\"\"
        模块被加载时调用

        :param event: 事件内容
        :return: 处理结果
        \"\"\"
        await self._register_commands()
        await self._register_message_handlers()
        self.logger.info(f"模块已加载: {{event}}")
        return True

    async def on_unload(self, event: dict) -> bool:
        \"\"\"
        模块被卸载时调用

        :param event: 事件内容
        :return: 处理结果
        \"\"\"
        self.logger.info(f"模块已卸载: {{event}}")
        return True

    def _load_config(self):
        config = self.sdk.config.getConfig("{name}")
        if not config:
            default_config = {{
                "enabled": True,
            }}
            self.sdk.config.setConfig("{name}", default_config)
            self.logger.warning("未找到模块配置, 已创建默认配置到config.toml")
            return default_config
        return config

    async def _register_commands(self):
        @command("hello", help="发送问候消息")
        async def hello_command(event):
            await event.reply("Hello from {name}!")

    async def _register_message_handlers(self):
        @message.on_private_message()
        async def private_message_handler(event):
            self.logger.info(f"收到私聊消息: {{event.get_text()}}")

        @message.on_group_message()
        async def group_message_handler(event):
            pass

        @notice.on_friend_add()
        async def friend_add_handler(event):
            self.logger.info(f"新好友添加: {{event.get_user_nickname()}}")
"""

_ADAPTER_PYPROJECT = """[project]
name = "ErisPulse-{name}"
version = "1.0.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.10"
license = {{ file = "LICENSE" }}
authors = [ {{ name = "{author}", email = "{email}" }} ]

dependencies = [
]

[project.urls]
"homepage" = "{homepage}"

[project.entry-points]
"erispulse.adapter" = {{ "{entry_key}" = "{name}:{name}" }}
"""

_ADAPTER_INIT = """from .Core import {name}
from .Converter import {converter_name}

__all__ = [
    "{name}",
    "{converter_name}"
]
"""

_ADAPTER_CORE = """import asyncio
import json
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig
from ErisPulse.Core import router


@dataclass
class {name}Config(AdapterConfig):
    \"\"\"{name} 适配器配置\"\"\"
    endpoint: str = field(
        default="https://api.example.com",
        metadata={{"description": "平台 API 地址"}},
    )
    token: str = field(
        default="",
        metadata={{"description": "平台 Token", "required": True, "secret": True}},
    )


class {name}(BaseAdapter):
    \"\"\"
    {name} 适配器

    继承自 BaseAdapter 基类，使用声明式配置管理（ConfigClass），
    实现了 SendDSL 风格的链式调用接口和 Bot 状态追踪。
    \"\"\"

    ConfigClass = {name}Config

    def __init__(self, sdk=None):
        super().__init__()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert

    def _setup_converter(self):
        from .Converter import {converter_name}
        return {converter_name}()

    class Send(BaseAdapter.Send):
        \"\"\"
        Send 消息发送 DSL

        At / AtAll / Reply / Using / To 由框架基类内置处理。
        使用 self._apply_modifiers(message) 合并修饰器到消息段。
        使用 self.send_context 获取发送上下文 (target_type, target_id, account_id)。

        支持链式调用:
        Send.To("group", "123").At("456").Reply("789").Text("hi")
        \"\"\"

        def Raw_ob12(self, message, **kwargs):
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs,
                )
            return asyncio.create_task(_do_send())

        def Text(self, text: str):
            return self.Raw_ob12([{{"type": "text", "data": {{"text": text}}}}])

        def Image(self, file):
            return self.Raw_ob12([{{"type": "image", "data": {{"file": file}}}}])

    class Request(BaseAdapter.Request):
        \"\"\"
        Request 请求操作 DSL

        适配器应重写 accept / reject 实现平台特定的请求处理逻辑。
        如果平台不支持请求操作，可不实现此内部类。
        基类默认返回 retcode=10002（不支持的操作）。
        \"\"\"

        async def _do_accept(self, **kwargs):
            result = await self._adapter.call_api(
                endpoint="/set_request",
                request_id=self._request_id,
                approve=True,
                account_id=self._account_id,
                **kwargs,
            )
            return {{
                "status": "ok" if result.get("code") == 0 else "failed",
                "retcode": result.get("code", 0),
                "data": None,
                "message_id": "",
                "message": result.get("message", ""),
            }}

        async def _do_reject(self, **kwargs):
            result = await self._adapter.call_api(
                endpoint="/set_request",
                request_id=self._request_id,
                approve=False,
                account_id=self._account_id,
                **kwargs,
            )
            return {{
                "status": "ok" if result.get("code") == 0 else "failed",
                "retcode": result.get("code", 0),
                "data": None,
                "message_id": "",
                "message": result.get("message", ""),
            }}

    async def start(self):
        \"\"\"启动适配器\"\"\"
        cfg = self.config
        self.logger.info(f"启动 {{cfg.endpoint}} 适配器")

        router.register_websocket(
            module_name="{entry_key}",
            path="/ws",
            handler=self._ws_handler,
        )
        self.logger.info("WebSocket 路由已注册: /ws")

    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        await self.emit_meta("connect", bot_id, user_name="{name}")
        self.logger.info(f"Bot {{bot_id}} 已连接")

        try:
            while True:
                data = await websocket.receive_text()
                raw = json.loads(data)
                event = self.convert(raw)
                if event:
                    await self.adapter.emit(event)
        except Exception as e:
            self.logger.warning(f"连接断开: {{e}}")
        finally:
            await self.emit_meta("disconnect", bot_id)
            self.logger.info(f"Bot {{bot_id}} 已断开")

    async def shutdown(self):
        \"\"\"关闭适配器\"\"\"
        router.unregister_websocket("{entry_key}", "/ws")
        self.logger.info("适配器已关闭")

    async def call_api(self, endpoint: str, **params):
        \"\"\"调用平台 API\"\"\"
        from ErisPulse.Core import client

        cfg = self.config
        headers = {{"Authorization": "Bearer " + cfg.token}}
        url = cfg.endpoint + endpoint

        try:
            resp = await client.post(
                url,
                json=params,
                headers=headers,
                timeout=30,
                max_retries=2,
            )
            result = await resp.json()
            return self.make_response(
                data=result.get("data"),
                message_id=result.get("data", {{}}).get("message_id", ""),
                raw=result,
            )
        except Exception as e:
            self.logger.error(f"API 调用失败: {{e}}")
            return self.make_error(message=str(e))
"""

_ADAPTER_CONVERTER = """\"\"\"
{name} 事件转换器

将平台原生事件转换为 OneBot12 标准格式（正向转换）。
反向转换（发送方向）由适配器的 Send.Raw_ob12() 处理。
\"\"\"

import time
import uuid


class {converter_name}:
    \"\"\"
    {name} 转换器类

    负责将平台特定的事件格式转换为 ErisPulse 标准 OneBot12 格式。
    所有转换后的事件必须包含 platform_raw 字段以保留原始数据。
    \"\"\"

    def convert(self, raw_event: dict) -> dict:
        \"\"\"
        将平台原生事件转换为 OneBot12 标准格式

        :param raw_event: 平台原始事件数据
        :return: OneBot12 标准格式的事件字典，无法识别时返回 None
        \"\"\"
        if not isinstance(raw_event, dict):
            return None

        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        timestamp = raw_event.get("timestamp") or int(time.time())

        event = {{
            "id": str(event_id),
            "time": int(timestamp),
            "type": self._convert_type(raw_event),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "{entry_key}",
            "self": {{
                "platform": "{entry_key}",
                "user_id": str(raw_event.get("self_id", "")),
            }},
            "{entry_key}_raw": raw_event,
            "{entry_key}_raw_type": raw_event.get("type", ""),
        }}

        if event["type"] == "message":
            event["user_id"] = str(raw_event.get("sender_id", ""))
            event["message"] = self._convert_message_segments(raw_event.get("content", ""))
            event["alt_message"] = raw_event.get("content", "")

        return event

    def _convert_type(self, raw_event: dict) -> str:
        event_type = raw_event.get("type", "")
        type_map = {{
            "chat": "message",
        }}
        return type_map.get(event_type, "unknown")

    def _convert_detail_type(self, raw_event: dict) -> str:
        return "private" if raw_event.get("is_private") else "group"

    def _convert_message_segments(self, content) -> list:
        if isinstance(content, str) and content:
            return [{{"type": "text", "data": {{"text": content}}}}]
        return []
"""

_README_MODULE = """# {name}

{description}

## 安装

```bash
epsdk install {name}
```

## 使用

模块会自动加载，你也可以通过 `sdk.{name}` 访问模块实例。

## 配置

在 `config.toml` 中添加:

```toml
[{name}]
enabled = true
```
"""

_README_ADAPTER = """# {name}

{description}

## 安装

```bash
epsdk install {name}
```

## 使用

在 `config.toml` 中启用适配器:

```toml
[ErisPulse.adapters.status]
{name_snake} = true
```

## 配置

```toml
[{name}]
mode = "server"

[{name}.server]
path = "/webhook"

[{name}.client]
url = "http://127.0.0.1:8080"
token = ""
```
"""


def _camel_to_snake(name: str) -> str:
    """
    将 PascalCase/CamelCase 名称转换为 snake_case

    :param name: [str] 原始名称
    :return: [str] 转换后的 snake_case 名称
    """
    import re

    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s = re.sub(r"(?<=[A-Z])([A-Z])(?=[a-z])", r"_\1", s)
    return s.lower().lstrip("_")


def _to_converter_name(name: str) -> str:
    """
    根据适配器名称生成转换器类名

    :param name: [str] 适配器名称
    :return: [str] 转换器类名（名称后追加 Converter）
    """
    return f"{name}Converter"


def _validate_name(name: str) -> bool:
    """
    校验项目/模块/适配器名称是否合法

    名称必须以字母开头，且只能包含字母、数字和下划线。

    :param name: [str] 待校验的名称
    :return: [bool] 合法返回 True，否则 False
    """
    if not name:
        return False
    if not name[0].isalpha():
        return False
    return all(c.isalnum() or c == "_" for c in name)


class CreateCommand(Command):
    """
    create 命令

    脚手架工具，快速创建 Module / Adapter 项目模板
    """

    name = "create"
    description = i18n.t("cli.create.description")
    aliases = ["c", "new"]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "create_type",
            nargs="?",
            choices=["module", "adapter"],
            help=i18n.t("cli.create.type_help"),
        )
        parser.add_argument("--name", "-n", help=i18n.t("cli.create.name_help"))
        parser.add_argument(
            "--description", "-d", help=i18n.t("cli.create.desc_help"), default=""
        )
        parser.add_argument(
            "--author", "-a", help=i18n.t("cli.create.author_help"), default=""
        )
        parser.add_argument(
            "--email", "-e", help=i18n.t("cli.create.email_help"), default=""
        )
        parser.add_argument(
            "--homepage", help=i18n.t("cli.create.homepage_help"), default=""
        )
        parser.add_argument(
            "--output", "-o", help=i18n.t("cli.create.output_help"), default="."
        )
        parser.add_argument(
            "--force", "-f", action="store_true", help=i18n.t("cli.create.force_help")
        )

    def execute(self, args):
        create_type = getattr(args, "create_type", None)
        if not create_type:
            create_type = self._interactive_select_type()

        default_name = "MyModule" if create_type == "module" else "MyAdapter"
        name = args.name
        # 名称校验：非法时保留输入并重新提示，而非直接退出
        if not (name and _validate_name(name)):
            name = prompt_validated(
                i18n.t("cli.create.name_prompt"),
                default=name or default_name,
                validate=_validate_name,
                error_msg=i18n.t("cli.create.name_error"),
            )

        if create_type == "module":
            self._create_module(args, name)
        else:
            self._create_adapter(args, name)

    def _interactive_select_type(self) -> str:
        """
        交互式选择创建类型（Module 或 Adapter）

        :return: [str] 返回 "module" 或 "adapter"
        """
        section_header(i18n.t("cli.create.select_type_title"))
        console.print(
            f"    [bold]1.[/] Module   [dim]{i18n.t('cli.create.select_type_module')}[/]"
        )
        console.print(
            f"    [bold]2.[/] Adapter  [dim]{i18n.t('cli.create.select_type_adapter')}[/]"
        )
        console.print()
        choice = IntPrompt.ask(
            i18n.t("cli.create.select_prompt"), default=1, choices=["1", "2"]
        )
        console.print()
        return "module" if choice == 1 else "adapter"

    def _ask_missing(
        self, args, field_name: str, prompt_text: str, default: str = ""
    ) -> str:
        """
        获取参数值，若缺失则交互式提示输入

        :param args: [Any] 解析后的命令参数对象
        :param field_name: [str] 参数字段名
        :param prompt_text: [str] 提示文本
        :param default: [str] 默认值 (默认: "")
        :return: [str] 获取到的参数值
        """
        val = getattr(args, field_name, None) or ""
        if not val:
            val = Prompt.ask(f"  {prompt_text}", default=default)
        return val

    def _create_module(self, args, name: str):
        """
        创建 Module 项目脚手架

        :param args: [Any] 解析后的命令参数对象
        :param name: [str] 模块名称
        :return: [None] 无返回值
        """
        description = self._ask_missing(
            args,
            "description",
            i18n.t("cli.create.module_desc_prompt"),
            i18n.t("cli.create.module_desc_placeholder", name=name),
        )
        author = self._ask_missing(
            args, "author", i18n.t("cli.create.author_prompt"), "yourname"
        )
        email = self._ask_missing(
            args, "email", i18n.t("cli.create.email_prompt"), "your@mail.com"
        )
        homepage = self._ask_missing(
            args,
            "homepage",
            i18n.t("cli.create.homepage_prompt"),
            f"https://github.com/{author}/{name}",
        )

        output = Path(args.output)
        project_dir = output / name

        if project_dir.exists() and not args.force:
            console.print(
                f"[error]  {i18n.t('cli.create.dir_exists', dir=str(project_dir))}"
            )
            sys.exit(1)

        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            pkg_dir = project_dir / name
            pkg_dir.mkdir(exist_ok=True)

            (pkg_dir / "__init__.py").write_text(_MODULE_INIT, encoding="utf-8")
            (pkg_dir / "Core.py").write_text(
                _MODULE_CORE.format(name=name), encoding="utf-8"
            )
            (project_dir / "pyproject.toml").write_text(
                _MODULE_PYPROJECT.format(
                    name=name,
                    description=description,
                    author=author,
                    email=email,
                    homepage=homepage,
                ),
                encoding="utf-8",
            )
            (project_dir / "LICENSE").write_text(
                _LICENSE_TEMPLATE.format(
                    year=str(datetime.datetime.now().year), author=author
                ),
                encoding="utf-8",
            )
            (project_dir / "README.md").write_text(
                _README_MODULE.format(name=name, description=description),
                encoding="utf-8",
            )

            console.print()
            console.print(
                f"[success]  {i18n.t('cli.create.module_created', name=name)}[/]"
            )
            console.print()
            console.print(Text(i18n.t("cli.create.project_structure"), style="bold"))
            console.print(f"    {name}/")
            console.print("    ├── pyproject.toml")
            console.print("    ├── LICENSE")
            console.print("    ├── README.md")
            console.print(f"    └── {name}/")
            console.print("        ├── __init__.py")
            console.print("        └── Core.py")
            console.print()
            console.print(Text(i18n.t("cli.create.next_steps"), style="bold"))
            console.print(f"    · {i18n.t('cli.create.cd_to', dir=name)}")
            console.print(
                f"    · {i18n.t('cli.create.edit_module', file=name + '/Core.py')}"
            )
            console.print(f"    · {i18n.t('cli.create.install_dev')}")
            console.print(f"    · {i18n.t('cli.create.run_test')}")

        except Exception as e:
            console.print(f"[error]  {i18n.t('cli.create.failed', error=e)}")
            sys.exit(1)

    def _create_adapter(self, args, name: str):
        """
        创建 Adapter 项目脚手架

        :param args: [Any] 解析后的命令参数对象
        :param name: [str] 适配器名称
        :return: [None] 无返回值
        """
        description = self._ask_missing(
            args,
            "description",
            i18n.t("cli.create.adapter_desc_prompt"),
            i18n.t("cli.create.adapter_desc_placeholder", name=name),
        )
        author = self._ask_missing(
            args, "author", i18n.t("cli.create.author_prompt"), "yourname"
        )
        email = self._ask_missing(
            args, "email", i18n.t("cli.create.email_prompt"), "your@mail.com"
        )
        homepage = self._ask_missing(
            args,
            "homepage",
            i18n.t("cli.create.homepage_prompt"),
            f"https://github.com/{author}/{name}",
        )

        converter_name = _to_converter_name(name)
        entry_key = _camel_to_snake(name)
        output = Path(args.output)
        project_dir = output / name

        if project_dir.exists() and not args.force:
            console.print(
                f"[error]  {i18n.t('cli.create.dir_exists', dir=str(project_dir))}"
            )
            sys.exit(1)

        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            pkg_dir = project_dir / name
            pkg_dir.mkdir(exist_ok=True)

            (pkg_dir / "__init__.py").write_text(
                _ADAPTER_INIT.format(name=name, converter_name=converter_name),
                encoding="utf-8",
            )
            (pkg_dir / "Core.py").write_text(
                _ADAPTER_CORE.format(
                    name=name, converter_name=converter_name, entry_key=entry_key
                ),
                encoding="utf-8",
            )
            (pkg_dir / "Converter.py").write_text(
                _ADAPTER_CONVERTER.format(
                    name=name, converter_name=converter_name, entry_key=entry_key
                ),
                encoding="utf-8",
            )
            (project_dir / "pyproject.toml").write_text(
                _ADAPTER_PYPROJECT.format(
                    name=name,
                    description=description,
                    author=author,
                    email=email,
                    homepage=homepage,
                    entry_key=entry_key,
                ),
                encoding="utf-8",
            )
            (project_dir / "LICENSE").write_text(
                _LICENSE_TEMPLATE.format(
                    year=str(datetime.datetime.now().year), author=author
                ),
                encoding="utf-8",
            )
            (project_dir / "README.md").write_text(
                _README_ADAPTER.format(
                    name=name, description=description, name_snake=entry_key
                ),
                encoding="utf-8",
            )

            console.print()
            console.print(
                f"[success]  {i18n.t('cli.create.adapter_created', name=name)}[/]"
            )
            console.print()
            console.print(Text(i18n.t("cli.create.project_structure"), style="bold"))
            console.print(f"    {name}/")
            console.print("    ├── pyproject.toml")
            console.print("    ├── LICENSE")
            console.print("    ├── README.md")
            console.print(f"    └── {name}/")
            console.print("        ├── __init__.py")
            console.print("        ├── Core.py")
            console.print("        └── Converter.py")
            console.print()
            console.print(Text(i18n.t("cli.create.next_steps"), style="bold"))
            console.print(f"    · {i18n.t('cli.create.cd_to', dir=name)}")
            console.print(
                f"    · {i18n.t('cli.create.edit_adapter', file=name + '/Core.py')}"
            )
            console.print(
                f"    · {i18n.t('cli.create.edit_converter', file=name + '/Converter.py')}"
            )
            console.print(f"    · {i18n.t('cli.create.install_dev')}")
            console.print(f"    · {i18n.t('cli.create.run_test')}")

        except Exception as e:
            console.print(f"[error]  {i18n.t('cli.create.failed', error=e)}")
            sys.exit(1)
