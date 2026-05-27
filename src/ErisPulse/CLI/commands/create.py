"""
Create 命令实现

脚手架工具，快速创建 Module / Adapter 项目模板
"""

import sys
from argparse import ArgumentParser
from pathlib import Path

from rich.prompt import Prompt, IntPrompt
from rich.text import Text

from ..console import console
from ..base import Command
from ..utils.display import section_header


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
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import logger, config as config_manager, adapter


class {name}(BaseAdapter):
    \"\"\"
    {name}适配器

    继承自BaseAdapter基类，实现了SendDSL风格的链式调用接口
    \"\"\"

    def __init__(self, sdk=None):
        from ErisPulse import sdk as _sdk
        self.sdk = _sdk if sdk is None else sdk
        self.logger = logger.get_child("{name}")
        self.config_manager = config_manager
        self.adapter = adapter

        self.logger.info("{name} 初始化完成")
        self.config = self._load_config()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert

    def _setup_converter(self):
        from .Converter import {converter_name}
        return {converter_name}()

    def _load_config(self):
        if not self.config_manager:
            return {{}}

        config = self.config_manager.getConfig("{name}", {{}})

        if config is None:
            default_config = {{
                "mode": "server",
                "server": {{
                    "path": "/webhook",
                }},
                "client": {{
                    "url": "http://127.0.0.1:8080",
                    "token": ""
                }}
            }}
            self.config_manager.setConfig("{name}", default_config)
            self.logger.info("已创建{name}默认配置")
            return default_config
        return config

    class Send(BaseAdapter.Send):
        \"\"\"
        Send消息发送DSL

        At/AtAll/Reply/Using(也就是使用的账户)/Account/To 由框架基类内置处理
        使用 self._apply_modifiers(message) 合并修饰器到消息段。
        使用 self.send_context 获取发送上下文 (target_type, target_id, account_id)。

        支持链式调用:
        Send.To("group","123").At("456").Reply("789").Text("hi")
        \"\"\"

        def Raw_ob12(self, message, **kwargs):
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs
                )

            return asyncio.create_task(_do_send())

        def Text(self, text: str):
            return self.Raw_ob12([{{"type": "text", "data": {{"text": text}}}}])

        def Image(self, file):
            return self.Raw_ob12([{{"type": "image", "data": {{"file": file}}}}])

    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError(f"需要实现平台特定的API调用: {{endpoint}}")

    async def start(self):
        self.logger.info(f"启动{name}，配置模式: {{self.config.get('mode', 'unknown')}}")
        raise NotImplementedError("需要实现适配器启动逻辑")

    async def shutdown(self):
        self.logger.info("关闭{name}")
        raise NotImplementedError("需要实现适配器关闭逻辑")
"""

_ADAPTER_CONVERTER = """\"\"\"
{name}转换器

用于在平台特定消息格式和ErisPulse标准格式之间进行转换
\"\"\"


class {converter_name}:
    \"\"\"
    {name}转换器类

    负责将平台特定的事件格式转换为ErisPulse标准格式
    \"\"\"

    def __init__(self):
        pass

    def convert(self, data: dict) -> dict:
        \"\"\"
        将平台特定消息格式转换为ErisPulse标准格式

        :param data: 平台原始事件数据
        :return: ErisPulse标准格式的事件数据
        \"\"\"
        return data

    def reverse_convert(self, event: dict) -> dict:
        \"\"\"
        将ErisPulse标准格式转换为平台特定消息格式

        :param event: ErisPulse标准格式的事件数据
        :return: 平台特定格式的事件数据
        \"\"\"
        return event
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
    import re
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name)
    s = re.sub(r'(?<=[A-Z])([A-Z])(?=[a-z])', r'_\1', s)
    return s.lower().lstrip('_')


def _to_converter_name(name: str) -> str:
    return f"{name}Converter"


def _validate_name(name: str) -> bool:
    if not name:
        return False
    if not name[0].isalpha():
        return False
    return all(c.isalnum() or c == '_' for c in name)


class CreateCommand(Command):
    name = "create"
    description = "创建 Module / Adapter 项目脚手架"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("create_type", nargs="?", choices=["module", "adapter"], help="创建类型: module 或 adapter")
        parser.add_argument("--name", "-n", help="项目/模块/适配器名称 (PascalCase)")
        parser.add_argument("--description", "-d", help="项目描述", default="")
        parser.add_argument("--author", "-a", help="作者名称", default="")
        parser.add_argument("--email", "-e", help="作者邮箱", default="")
        parser.add_argument("--homepage", help="项目主页 URL", default="")
        parser.add_argument("--output", "-o", help="输出目录 (默认当前目录)", default=".")
        parser.add_argument("--force", "-f", action="store_true", help="强制覆盖已存在的目录")

    def execute(self, args):
        create_type = getattr(args, "create_type", None)
        if not create_type:
            create_type = self._interactive_select_type()

        name = args.name
        if not name:
            default_name = "MyModule" if create_type == "module" else "MyAdapter"
            name = Prompt.ask("  名称 (PascalCase)", default=default_name)

        if not _validate_name(name):
            console.print("[error]  名称必须以字母开头，只能包含字母、数字和下划线")
            sys.exit(1)

        if create_type == "module":
            self._create_module(args, name)
        else:
            self._create_adapter(args, name)

    def _interactive_select_type(self) -> str:
        section_header("选择创建类型")
        console.print("    [bold]1.[/] Module   [dim]— 自定义功能模块[/]")
        console.print("    [bold]2.[/] Adapter  [dim]— 平台适配器[/]")
        console.print()
        choice = IntPrompt.ask("  请选择", default=1, choices=["1", "2"])
        console.print()
        return "module" if choice == 1 else "adapter"

    def _ask_missing(self, args, field_name: str, prompt_text: str, default: str = "") -> str:
        val = getattr(args, field_name, None) or ""
        if not val:
            val = Prompt.ask(f"  {prompt_text}", default=default)
        return val

    def _create_module(self, args, name: str):
        description = self._ask_missing(args, "description", "模块描述", f"一个非常哇塞的{name}模块")
        author = self._ask_missing(args, "author", "作者名称", "yourname")
        email = self._ask_missing(args, "email", "作者邮箱", "your@mail.com")
        homepage = self._ask_missing(args, "homepage", "项目主页", f"https://github.com/{author}/{name}")

        output = Path(args.output)
        project_dir = output / name

        if project_dir.exists() and not args.force:
            console.print(f"[error]  目录 {project_dir} 已存在，使用 --force 覆盖")
            sys.exit(1)

        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            pkg_dir = project_dir / name
            pkg_dir.mkdir(exist_ok=True)

            (pkg_dir / "__init__.py").write_text(_MODULE_INIT, encoding="utf-8")
            (pkg_dir / "Core.py").write_text(
                _MODULE_CORE.format(name=name),
                encoding="utf-8"
            )
            (project_dir / "pyproject.toml").write_text(
                _MODULE_PYPROJECT.format(
                    name=name,
                    description=description,
                    author=author,
                    email=email,
                    homepage=homepage,
                ),
                encoding="utf-8"
            )
            (project_dir / "LICENSE").write_text(
                _LICENSE_TEMPLATE.format(year="2026", author=author),
                encoding="utf-8"
            )
            (project_dir / "README.md").write_text(
                _README_MODULE.format(name=name, description=description),
                encoding="utf-8"
            )

            console.print()
            console.print(f"[success]  Module 项目 [{name}] 创建成功[/]")
            console.print()
            console.print(Text("  项目结构:", style="bold"))
            console.print(f"    {name}/")
            console.print(f"    ├── pyproject.toml")
            console.print(f"    ├── LICENSE")
            console.print(f"    ├── README.md")
            console.print(f"    └── {name}/")
            console.print(f"        ├── __init__.py")
            console.print(f"        └── Core.py")
            console.print()
            console.print(Text("  接下来:", style="bold"))
            console.print(f"    · cd {name}")
            console.print(f"    · 编辑 {name}/Core.py 实现模块逻辑")
            console.print(f"    · pip install -e .  (开发模式安装)")
            console.print(f"    · epsdk run  (运行测试)")

        except Exception as e:
            console.print(f"[error]  创建失败: {e}")
            sys.exit(1)

    def _create_adapter(self, args, name: str):
        description = self._ask_missing(args, "description", "适配器描述", f"{name}平台适配器")
        author = self._ask_missing(args, "author", "作者名称", "yourname")
        email = self._ask_missing(args, "email", "作者邮箱", "your@mail.com")
        homepage = self._ask_missing(args, "homepage", "项目主页", f"https://github.com/{author}/{name}")

        converter_name = _to_converter_name(name)
        entry_key = _camel_to_snake(name)
        output = Path(args.output)
        project_dir = output / name

        if project_dir.exists() and not args.force:
            console.print(f"[error]  目录 {project_dir} 已存在，使用 --force 覆盖")
            sys.exit(1)

        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            pkg_dir = project_dir / name
            pkg_dir.mkdir(exist_ok=True)

            (pkg_dir / "__init__.py").write_text(
                _ADAPTER_INIT.format(name=name, converter_name=converter_name),
                encoding="utf-8"
            )
            (pkg_dir / "Core.py").write_text(
                _ADAPTER_CORE.format(name=name, converter_name=converter_name),
                encoding="utf-8"
            )
            (pkg_dir / "Converter.py").write_text(
                _ADAPTER_CONVERTER.format(name=name, converter_name=converter_name),
                encoding="utf-8"
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
                encoding="utf-8"
            )
            (project_dir / "LICENSE").write_text(
                _LICENSE_TEMPLATE.format(year="2026", author=author),
                encoding="utf-8"
            )
            (project_dir / "README.md").write_text(
                _README_ADAPTER.format(name=name, description=description, name_snake=entry_key),
                encoding="utf-8"
            )

            console.print()
            console.print(f"[success]  Adapter 项目 [{name}] 创建成功[/]")
            console.print()
            console.print(Text("  项目结构:", style="bold"))
            console.print(f"    {name}/")
            console.print(f"    ├── pyproject.toml")
            console.print(f"    ├── LICENSE")
            console.print(f"    ├── README.md")
            console.print(f"    └── {name}/")
            console.print(f"        ├── __init__.py")
            console.print(f"        ├── Core.py")
            console.print(f"        └── Converter.py")
            console.print()
            console.print(Text("  接下来:", style="bold"))
            console.print(f"    · cd {name}")
            console.print(f"    · 编辑 {name}/Core.py 实现适配器逻辑")
            console.print(f"    · 编辑 {name}/Converter.py 实现消息格式转换")
            console.print(f"    · pip install -e .  (开发模式安装)")
            console.print(f"    · epsdk run  (运行测试)")

        except Exception as e:
            console.print(f"[error]  创建失败: {e}")
            sys.exit(1)
