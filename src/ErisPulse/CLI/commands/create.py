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
from ..utils.scaffold_text import ScaffoldText

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

_MODULE_CORE = """from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey, ModuleMeta
from ErisPulse.Core.Event import command, message, notice
from ErisPulse.Core.i18n import i18n


class Main(BaseModule):
    \"\"\"
    {text[module.doc]}
    \"\"\"

    # {text[module.config_hint]}
    @dataclass
    class ConfigClass(BaseConfig):
        \"\"\"{text[module.config_doc]}\"\"\"

        enabled: bool = field(
            default=True,
            metadata={{
                \"description\": {{\"i18n\": \"module.{name}.enabled\", \"default\": \"Enable module\"}},
            }},
        )

    # {text[module.i18n_hint]}
    class I18nClass(BaseI18n):
        \"\"\"{name} translation keys\"\"\"

        enabled: I18nKey = I18nKey(
            key=\"module.{name}.enabled\",
            default=\"Enable module\",
            zh_CN=\"是否启用模块\",
            en=\"Enable module\",
            ja=\"モジュールを有効にする\",
            ru=\"Включить модуль\",
            zh_TW=\"啟用模組\",
        )
        hello_help: I18nKey = I18nKey(
            key=\"module.{name}.command.hello.help\",
            default=\"Send a greeting message\",
            zh_CN=\"发送问候消息\",
            en=\"Send a greeting message\",
            ja=\"挨拶メッセージを送信\",
            ru=\"Отправить приветствие\",
            zh_TW=\"發送問候訊息\",
        )
        hello_reply: I18nKey = I18nKey(
            key=\"module.{name}.command.hello.reply\",
            default=\"Hello from {name}!\",
            zh_CN=\"来自 {name} 的问候！\",
            en=\"Hello from {name}!\",
            ja=\"{name} からの挨拶です！\",
            ru=\"Привет от {name}!\",
            zh_TW=\"來自 {name} 的問候！\",
        )

    def __init__(self, sdk=None):
        from ErisPulse import sdk as _sdk
        self.sdk = _sdk if sdk is None else sdk
        self.logger = self.sdk.logger.get_child(\"{name}\")
        self.storage = self.sdk.storage
        self.adapter = self.sdk.adapter
        self.client = self.sdk.client

        self.logger.info((\"{text[module.log.init_done]}\").format(name=\"{name}\"))

    @staticmethod
    def get_meta() -> ModuleMeta:
        \"\"\"
        {text[module.meta_doc]}
        \"\"\"
        return ModuleMeta(
            name=\"{name}\",
            description=\"{name} module\",
            version=\"0.1.0\",
            author=\"ErisDev\",
            group=\"default\",
            tags=[\"{name}\"],
        )

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            # 依赖声明（可选）：缺失依赖的模块会被跳过加载；
            # 被依赖模块卸载/热重载时，本模块将级联卸载/重载
            # depends=[],
        )

    async def on_load(self, event: dict) -> bool:
        \"\"\"
        {text[module.on_load_doc]}

        :param event: event data
        :return: processing result
        \"\"\"
        await self._register_commands()
        await self._register_message_handlers()
        self.logger.info((\"{text[module.log.loaded]}\").format(event=event))
        return True

    async def on_unload(self, event: dict) -> bool:
        \"\"\"
        {text[module.on_unload_doc]}

        :param event: event data
        :return: processing result
        \"\"\"
        self.logger.info((\"{text[module.log.unloaded]}\").format(event=event))
        return True

    def on_config_update(self, old_config, new_config):
        \"\"\"{text[module.config_updated_doc]}\"\"\"
        self.logger.info(\"{text[module.log.config_updated]}\")

    async def _register_commands(self):
        @command(\"hello\", help=i18n.t(\"module.{name}.command.hello.help\"))
        async def hello_command(event):
            await event.reply(i18n.t(\"module.{name}.command.hello.reply\"))

    async def _register_message_handlers(self):
        @message.on_private_message()
        async def private_message_handler(event):
            self.logger.info((\"{text[module.log.private_message]}\").format(content=event.get_text()))

        @message.on_group_message()
        async def group_message_handler(event):
            pass

        @notice.on_friend_add()
        async def friend_add_handler(event):
            self.logger.info((\"{text[module.log.friend_add]}\").format(nickname=event.get_user_nickname()))
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
from typing import ClassVar
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey
from ErisPulse.Core import router
from ErisPulse.Core.i18n import i18n


class {name}(BaseAdapter):
    \"\"\"
    {text[adapter.doc]}
    \"\"\"

    # 依赖声明（可选，ErisPulse 2.8.0+）：
    # depends = {{"adapters": [], "modules": []}}   # 硬依赖：缺失时跳过启动
    # optional_modules = []                          # 软依赖：就绪/丢失时收到
    #                                               # on_dependency_ready/lost 回调
    depends: ClassVar[dict] = {{}}
    optional_modules: ClassVar[list] = []

    # {text[adapter.config_hint]}
    @dataclass
    class ConfigClass(BaseConfig):
        \"\"\"{text[adapter.config_doc]}\"\"\"

        endpoint: str = field(
            default="https://api.example.com",
            metadata={{
                "description": {{"i18n": "adapter.{name}.endpoint", "default": "Platform API Endpoint"}},
                "required": False,
                "ui": {{"widget": "text", "group": "connection", "order": 1}},
            }},
        )
        token: str = field(
            default="",
            metadata={{
                "description": {{"i18n": "adapter.{name}.token", "default": "Platform Token"}},
                "required": True,
                "secret": True,
                "ui": {{"widget": "password", "group": "basic", "order": 2}},
            }},
        )

    # {text[adapter.i18n_hint]}
    class I18nClass(BaseI18n):
        \"\"\"{name} translation keys\"\"\"

        endpoint: I18nKey = I18nKey(
            key="adapter.{name}.endpoint",
            default="Platform API Endpoint",
            zh_CN="平台 API 地址",
            en="Platform API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
            zh_TW="API 位址",
        )
        token: I18nKey = I18nKey(
            key="adapter.{name}.token",
            default="Platform Token",
            zh_CN="平台 Token",
            en="Platform Token",
            ja="トークン",
            ru="Токен",
            zh_TW="權杖",
        )

    def __init__(self, sdk=None):
        super().__init__(sdk=sdk)
        self.logger = self._get_logger()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert

    def on_config_update(self, old_config, new_config):
        \"\"\"Called when adapter config hot-reloads\"\"\"
        self.logger.info("{text[adapter.log.config_updated]}")

    def _setup_converter(self):
        from .Converter import {converter_name}
        return {converter_name}()

    class Send(BaseAdapter.Send):
        \"\"\"
        {text[adapter.dsl.send_doc]}
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

        # {text[adapter.dsl.send_std_methods_hint]}
        # {text[adapter.dsl.send_override_hint]}
        # def Text(self, text: str):
        #     return self.Raw_ob12([{{"type": "text", "data": {{"text": text}}}}])

        # {text[adapter.dsl.send_extra_methods_hint]}
        # def Sticker(self, sticker_id: str):
        #     return self.Raw_ob12([{{"type": "sticker", "data": {{"id": sticker_id}}}}])

    class Request(BaseAdapter.Request):
        \"\"\"
        {text[adapter.dsl.request_doc]}
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

    class Api(BaseAdapter.Api):
        \"\"\"
        {text[adapter.dsl.api_doc]}
        \"\"\"

        # {text[adapter.dsl.api_std_methods_hint]}
        # {text[adapter.dsl.api_override_hint]}
        # async def get_user_info(self, user_id: str) -> dict:
        #     raw = await self._adapter._request("GET", f"/users/{{user_id}}")
        #     return self._adapter.make_response(data={{...}}, raw=raw)

    async def start(self):
        \"\"\"Start the adapter\"\"\"
        cfg = self.cfg
        self.logger.info("{text[adapter.log.starting]}")

        router.register_websocket(
            module_name="{entry_key}",
            path="/ws",
            handler=self._ws_handler,
        )
        self.logger.info("{text[adapter.log.ws_registered]}")

    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        await self.emit_meta("connect", bot_id, user_name="{name}")
        self.logger.info("{text[adapter.log.bot_connected]}")

        try:
            while True:
                data = await websocket.receive_text()
                raw = json.loads(data)
                event = self.convert(raw)
                if event:
                    await self.adapter.emit(event)
        except Exception as e:
            self.logger.warning("{text[adapter.log.connection_lost]}")
        finally:
            await self.emit_meta("disconnect", bot_id)
            self.logger.info("{text[adapter.log.bot_disconnected]}")

    async def shutdown(self):
        \"\"\"Shut down the adapter\"\"\"
        router.unregister_websocket("{entry_key}", "/ws")
        self.logger.info("{text[adapter.log.shutdown]}")

    async def call_api(self, endpoint: str, **params):
        \"\"\"Call platform API\"\"\"
        from ErisPulse.Core import client

        cfg = self.cfg
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
            self.logger.error(("{text[adapter.log.api_call_failed]}").format(error=e))
            return self.make_error(message=str(e))
"""

_ADAPTER_CONVERTER = """\"\"\"
{text[adapter.converter_doc]}
\"\"\"

from ErisPulse.Core.Bases import BaseConverter


class {converter_name}(BaseConverter):
    \"\"\"
    {converter_name} converter class

    Converts platform-specific event formats to the ErisPulse standard OneBot12 format.
    Inherits BaseConverter to reuse common field construction (build_base_event)
    and message-segment helpers (text/at/image).
    \"\"\"

    def __init__(self):
        super().__init__(platform="{entry_key}")

    def convert(self, raw_event: dict) -> dict | None:
        \"\"\"
        Convert a platform-native event to the OneBot12 standard format

        :param raw_event: raw platform event data
        :return: OneBot12 event dict, or None if unrecognized
        \"\"\"
        if not isinstance(raw_event, dict):
            return None

        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)

        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "private" if raw_event.get("is_private") else "group"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base

        return None
"""

_README_MODULE = """<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="{name}" />

# {name}

**{description}**

<p>
  <a href="https://pypi.org/project/ErisPulse-{name}/"><img src="https://img.shields.io/pypi/v/ErisPulse-{name}?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-{name}/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>

---

## 安装

```bash
epsdk install ErisPulse-{name}
```
"""

_README_ADAPTER = """<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="{name}" />

# {name}

**{description}**

<p>
  <a href="https://pypi.org/project/ErisPulse-{name}/"><img src="https://img.shields.io/pypi/v/ErisPulse-{name}?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-{name}/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>

---

## 安装

```bash
epsdk install ErisPulse-{name}
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


def _copy_erispulse_logo(project_dir: Path) -> None:
    """
    将 ErisPulseLogo.png 拷贝到项目的 .github/assets/ 目录

    :param project_dir: [Path] 项目根目录
    """
    import shutil

    logo_src = Path(__file__).parent.parent / "assets" / "ErisPulseLogo.png"
    if not logo_src.exists():
        return
    dest = project_dir / ".github" / "assets" / "ErisPulseLogo.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(logo_src, dest)


def _scaffold_text(name: str) -> dict:
    """
    构建当前语言的脚手架文案映射，并预填充 {name} 占位符

    :param name: [str] 模块/适配器名称
    :return: [dict] ScaffoldText.all() 的文案字典（含占位符替换）
    """
    st = ScaffoldText()
    return {
        key: (value.replace("{name}", name) if value else value)
        for key, value in st.all().items()
    }


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
        parser.add_argument(
            "--local",
            action="store_true",
            default=False,
            help=i18n.t("cli.create.local_module_help"),
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
        # --local：创建本地插件（plugins/ 目录结构，免打包安装）
        if getattr(args, "local", False):
            self._create_module_local(args, name)
            return

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
                _MODULE_CORE.format(name=name, text=_scaffold_text(name)),
                encoding="utf-8",
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

    def _create_module_local(self, args, name: str):
        """
        创建本地插件（--local）：生成 plugins/ 目录结构，免打包安装

        :param args: [Any] 解析后的命令参数对象
        :param name: [str] 模块名称
        :return: [None] 无返回值
        """
        output = Path(args.output)
        plugins_dir = output / "plugins"
        plugin_dir = plugins_dir / name

        if plugin_dir.exists() and not args.force:
            console.print(
                f"[error]  {i18n.t('cli.create.dir_exists', dir=str(plugin_dir))}"
            )
            sys.exit(1)

        try:
            plugin_dir.mkdir(parents=True, exist_ok=True)

            (plugin_dir / "__init__.py").write_text(_MODULE_INIT, encoding="utf-8")
            (plugin_dir / "Core.py").write_text(
                _MODULE_CORE.format(name=name, text=_scaffold_text(name)),
                encoding="utf-8",
            )

            console.print()
            console.print(
                f"[success]  {i18n.t('cli.create.module_created', name=name)}[/]"
            )
            console.print()
            console.print(Text(i18n.t("cli.create.local_structure"), style="bold"))
            console.print("    plugins/")
            console.print(f"    └── {name}/")
            console.print("        ├── __init__.py")
            console.print("        └── Core.py")
            console.print()
            console.print(Text(i18n.t("cli.create.next_steps"), style="bold"))
            console.print(f"    · {i18n.t('cli.create.cd_to', dir=str(plugin_dir))}")
            console.print(
                f"    · {i18n.t('cli.create.edit_module', file=str(plugin_dir) + '/Core.py')}"
            )
            console.print(f"    · {i18n.t('cli.create.local_tip')}")

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
                    name=name,
                    converter_name=converter_name,
                    entry_key=entry_key,
                    text=_scaffold_text(name),
                ),
                encoding="utf-8",
            )
            (pkg_dir / "Converter.py").write_text(
                _ADAPTER_CONVERTER.format(
                    name=name,
                    converter_name=converter_name,
                    entry_key=entry_key,
                    text=_scaffold_text(name),
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
