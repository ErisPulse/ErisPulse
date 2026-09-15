"""
命令声明式参数与选项（args= / options=）单元测试

测试 args= 声明解析（str/int/float/bool/literal/duration/rest 七类型、默认值、
顺序规则）、options= 字典式声明（布尔旗标 / 带值选项 / 类型跟随注解）、
分发期参数绑定与按名注入、解析失败自动回复本地化错误 + 用法、
权限检查先于解析、命令认领语义保持，以及未声明命令的向后兼容。
"""

import asyncio
import importlib
from unittest.mock import AsyncMock, patch

import pytest

from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event.command_args import (
    CommandArgsError,
    bind_command_arguments,
    format_usage,
    parse_args_spec,
    parse_options_spec,
)

# importlib.import_module 返回真实子模块（Core.config 包属性被 ConfigManager 单例遮蔽）
config_module = importlib.import_module("ErisPulse.Core.config")


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers
    from ErisPulse.Core.Event.message import message as message_handler

    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    yield
    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


def _msg(text, platform="onebot11", bot_id="bot_x", user_id="u1", group_id=None):
    data = {
        "id": f"id_{abs(hash(text))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "group" if group_id else "private",
        "platform": platform,
        "self": {"platform": platform, "user_id": bot_id},
        "user_id": user_id,
        "user_nickname": "User1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    if group_id:
        data["group_id"] = group_id
    return data


async def _dispatch(text, **kwargs):
    """以 "/" 命令前缀分发消息事件并等待命令分发完成"""
    from ErisPulse.Core.adapter import adapter

    with patch.object(config_module.config, "getConfig", return_value="/"):
        await adapter.emit(_msg(text, **kwargs))
        await asyncio.sleep(0.05)


class TestArgsSpecParsing:
    """args= 声明解析（注册期，fail-fast）"""

    def test_all_types_and_defaults(self):
        spec = parse_args_spec(
            '<name:str> <count:int> [ratio:float=0.5] [flag:bool=true] '
            "[mode:literal=fast|slow] [timeout:duration=1h30m]"
        )
        assert [(e.name, e.type, e.required) for e in spec] == [
            ("name", "str", True),
            ("count", "int", True),
            ("ratio", "float", False),
            ("flag", "bool", False),
            ("mode", "literal", False),
            ("timeout", "duration", False),
        ]
        assert spec[2].default == 0.5
        assert spec[3].default is True
        assert spec[4].default == "fast"
        assert spec[4].choices == ("fast", "slow")
        assert spec[5].default == 5400.0

    def test_rest_type(self):
        spec = parse_args_spec("<a:int> <text:rest>")
        assert spec[-1].type == "rest"
        assert spec[-1].required is True

    def test_optional_rest_default_empty(self):
        spec = parse_args_spec("[text:rest]")
        assert spec[0].default == ""

    def test_type_defaults_to_str(self):
        spec = parse_args_spec("<word>")
        assert spec[0].type == "str"
        assert spec[0].required is True

    @pytest.mark.parametrize(
        "bad",
        [
            "<x:unknown>",
            "<9bad>",
            "<a:rest> <b:int>",  # rest 必须最后
            "[a:int=1] <b:int>",  # 必填不得出现在可选之后
            "<x:int=5>",  # 必填不得带默认值
            "[m:literal]",  # literal 缺枚举表
            "[m:literal=a|a]",  # 枚举重复
            "junk <a:int>",  # 条目间存在裸文本
            "[x:int=abc]",  # 默认值与类型不匹配
        ],
    )
    def test_invalid_spec_raises(self, bad):
        with pytest.raises(ValueError):
            parse_args_spec(bad)

    def test_empty_spec_ok(self):
        assert parse_args_spec("") == []
        assert parse_args_spec("   ") == []


class TestOptionsSpecParsing:
    """options= 声明解析（注册期，fail-fast）"""

    @staticmethod
    def _handler(event, verbose: bool = False, label: str = "", count: int = 0, extra=None):
        return event, verbose, label, count, extra

    def test_flag_and_value_kinds(self):
        spec = parse_options_spec(
            {"verbose": "-v/--verbose", "label": "--label", "count": "-n/--num"},
            self._handler,
        )
        assert spec["verbose"].kind == "flag"
        assert spec["verbose"].type == "bool"
        assert spec["verbose"].forms == ("-v", "--verbose")
        assert spec["verbose"].default is False
        assert spec["label"].kind == "value"
        assert spec["label"].type == "str"
        assert spec["label"].default == ""
        assert spec["count"].type == "int"
        assert spec["count"].default == 0

    def test_missing_annotation_defaults_to_str(self):
        def handler(event, label):
            return label

        spec = parse_options_spec({"label": "--label"}, handler)
        assert spec["label"].kind == "value"
        assert spec["label"].type == "str"
        assert spec["label"].default is None

    def test_string_annotation_supported(self):
        def handler(event, verbose: "bool" = False):
            return verbose

        spec = parse_options_spec({"verbose": "-v"}, handler)
        assert spec["verbose"].kind == "flag"

    def test_unsupported_annotation_raises(self):
        def handler(event, when: list | None = None):
            return when

        with pytest.raises(ValueError):
            parse_options_spec({"when": "--when"}, handler)

    def test_signature_mismatch_raises(self):
        def handler(event):
            return event

        with pytest.raises(ValueError):
            parse_options_spec({"nope": "--nope"}, handler)

    def test_var_keyword_signature_accepts(self):
        def handler(event, **kwargs):
            return kwargs

        spec = parse_options_spec({"anything": "-a"}, handler)
        assert spec["anything"].type == "str"

    def test_bad_flag_form_raises(self):
        def handler(event, label: str = ""):
            return label

        with pytest.raises(ValueError):
            parse_options_spec({"label": "label"}, handler)


class TestBinding:
    """分发期 token → 关键字参数绑定"""

    def _spec_and_opts(self):
        spec = parse_args_spec("<count:int> [sides:int=6] [mode:literal=fast|slow]")
        opts = parse_options_spec({"verbose": "-v/--verbose", "label": "--label"}, self._handler)
        return spec, opts

    @staticmethod
    def _handler(event, verbose: bool = False, label: str = ""):
        return event, verbose, label

    def test_full_bind_with_options(self):
        spec, opts = self._spec_and_opts()
        kw = bind_command_arguments(["3", "-v", "--label", "hi", "20"], spec, opts)
        assert kw == {"count": 3, "sides": 20, "mode": "fast", "verbose": True, "label": "hi"}

    def test_inline_option_value(self):
        spec, opts = self._spec_and_opts()
        kw = bind_command_arguments(["--label=x", "1"], spec, opts)
        assert kw["label"] == "x"

    def test_flag_inline_bool(self):
        spec, opts = self._spec_and_opts()
        kw = bind_command_arguments(["--verbose=false", "1"], spec, opts)
        assert kw["verbose"] is False

    def test_options_extracted_before_positional(self):
        """选项先剔除，剩余 token 按位置解析；rest 覆盖剔除后的剩余文本"""
        spec = parse_args_spec("<text:rest>")
        opts = parse_options_spec({"verbose": "-v"}, self._handler)
        kw = bind_command_arguments(["hello", "-v", "world"], spec, opts)
        assert kw == {"text": "hello world", "verbose": True}

    def test_bool_tokens_reuse_confirm_lexicons(self):
        """bool 判定复用交互确认词表（zh/en/ja/ru），与 Event.confirm() 同一口径"""
        from ErisPulse.Core.constants import CONFIRM_NO_WORDS, CONFIRM_YES_WORDS

        spec = parse_args_spec("<flag:bool>")
        for token in ["true", "yes", "是", "真的", "确认", "はい", "да", "ok"]:
            assert token.lower() in CONFIRM_YES_WORDS
            assert bind_command_arguments([token], spec, None) == {"flag": True}
        for token in ["false", "no", "否", "不用", "いいえ", "нет", "不"]:
            assert token.lower() in CONFIRM_NO_WORDS
            assert bind_command_arguments([token], spec, None) == {"flag": False}
        # 词表外的输入 → 解析错误
        try:
            bind_command_arguments(["off"], spec, None)
            raise AssertionError("should raise")
        except CommandArgsError as e:
            assert e.key == "core.command.args.invalid"

    def test_duration_combination(self):
        spec = parse_args_spec("<t:duration>")
        assert bind_command_arguments(["1h30m"], spec, None) == {"t": 5400.0}

    def test_negative_number_is_value_not_option(self):
        spec = parse_args_spec("<delta:int>")
        opts = parse_options_spec({"verbose": "-v"}, self._handler)
        kw = bind_command_arguments(["-5"], spec, opts)
        assert kw == {"delta": -5}

    def test_error_paths(self):
        spec, opts = self._spec_and_opts()
        with pytest.raises(CommandArgsError) as ei:
            bind_command_arguments(["abc"], spec, opts)
        assert ei.value.key == "core.command.args.invalid"
        with pytest.raises(CommandArgsError) as em:
            bind_command_arguments([], spec, opts)
        assert em.value.key == "core.command.args.missing"
        with pytest.raises(CommandArgsError) as et:
            bind_command_arguments(["1", "2", "fast", "extra"], spec, opts)
        assert et.value.key == "core.command.args.too_many"
        with pytest.raises(CommandArgsError) as eu:
            bind_command_arguments(["--nope"], spec, opts)
        assert eu.value.key == "core.command.args.unknown_option"
        with pytest.raises(CommandArgsError) as ev:
            bind_command_arguments(["1", "--label"], spec, opts)
        assert ev.value.key == "core.command.args.missing_value"
        with pytest.raises(CommandArgsError) as er:
            bind_command_arguments(["1", "2", "nope"], spec, opts)
        assert er.value.key == "core.command.args.invalid"  # literal 枚举外取值

    def test_error_messages_localized(self):
        """CommandArgsError 文本即本地化提示（当前语言）"""
        spec = parse_args_spec("<count:int>")
        try:
            bind_command_arguments(["abc"], spec, None)
            raise AssertionError("should raise")
        except CommandArgsError as e:
            assert "count" in str(e) and "abc" in str(e)

    def test_bool_error_message_contains_arg_name(self):
        """bool 转换失败的错误提示携带真实参数名（非占位符 ?）"""
        spec = parse_args_spec("<flag:bool>")
        with pytest.raises(CommandArgsError) as ei:
            bind_command_arguments(["maybe"], spec, None)
        assert ei.value.params.get("arg") == "flag"
        assert "flag" in str(ei.value)

    def test_optional_without_default_backfills_handler_default(self):
        """[name:type] 未声明默认值时回填处理器签名默认值，而非注入 None"""

        def handler(event, name: str = "friend", sides: int = 6):
            return name, sides

        spec = parse_args_spec("[name:str] [sides:int]", handler)
        kw = bind_command_arguments([], spec, None)
        assert kw == {"name": "friend", "sides": 6}
        # 显式提供时正常覆盖
        kw2 = bind_command_arguments(["abc", "20"], spec, None)
        assert kw2 == {"name": "abc", "sides": 20}

    def test_optional_without_default_no_handler_default_stays_none(self):
        """处理器签名亦无默认值时，可选条目仍为 None"""

        def handler(event, name):
            return name

        spec = parse_args_spec("[name:str]", handler)
        kw = bind_command_arguments([], spec, None)
        assert kw == {"name": None}

    def test_declared_default_not_overridden_by_handler_default(self):
        """声明了默认值时以声明为准（不回填处理器签名默认值）"""

        def handler(event, sides: int = 20):
            return sides

        spec = parse_args_spec("[sides:int=6]", handler)
        kw = bind_command_arguments([], spec, None)
        assert kw == {"sides": 6}


class TestFormatUsage:
    """usage 尾串自动生成"""

    def test_full_shape(self):
        spec = parse_args_spec("<name:str> <need:int> [sides:int=6] [mode:literal=fast|slow] [text:rest]")
        usage = format_usage(spec, None)
        assert usage == "<name> <need> [sides=6] [mode:fast|slow] [text...]"

    def test_options_shape(self):
        spec = parse_args_spec("<count:int>")
        opts = parse_options_spec({"verbose": "-v/--verbose", "label": "--label"}, TestOptionsSpecParsing._handler)
        usage = format_usage(spec, opts)
        assert usage == "<count> [-v, --verbose] [--label STR]"

    def test_empty(self):
        assert format_usage(None, None) == ""


class TestDispatchInjection:
    """经 adapter.emit 全链路：声明式参数注入与错误回复"""

    @pytest.mark.asyncio
    async def test_args_injected_by_name(self):
        calls = []

        @command_handler("roll", args="<count:int> [sides:int=6]")
        async def roll(event, count: int, sides: int = 6):
            calls.append((count, sides, event.get_command_args()))

        await _dispatch("/roll 3 20")
        assert calls == [(3, 20, ["3", "20"])]  # kwargs 按名注入；get_command_args 保持原始 token

    @pytest.mark.asyncio
    async def test_defaults_apply_when_omitted(self):
        calls = []

        @command_handler("roll2", args="<count:int> [sides:int=6]")
        async def roll(event, count: int, sides: int = 6):
            calls.append((count, sides))

        await _dispatch("/roll2 3")
        assert calls == [(3, 6)]

    @pytest.mark.asyncio
    async def test_options_flag_and_value(self):
        calls = []

        @command_handler(
            "search",
            args="<query:str>",
            options={"verbose": "-v/--verbose", "label": "--label"},
        )
        async def search(event, query: str, verbose: bool = False, label: str = ""):
            calls.append((query, verbose, label))

        await _dispatch("/search hello -v --label world")
        assert calls == [("hello", True, "world")]

        calls.clear()
        await _dispatch("/search hi --label=x")
        assert calls == [("hi", False, "x")]

    @pytest.mark.asyncio
    async def test_all_types_end_to_end(self):
        calls = []

        @command_handler(
            "mix",
            args="<i:int> [f:float=1.5] [b:bool=false] [m:literal=a|b] [rest:rest]",
        )
        async def mix(event, i: int, f: float = 1.5, b: bool = False, m: str = "a", rest: str = ""):
            calls.append((i, f, b, m, rest))

        await _dispatch("/mix 5 2.5 true b x y")
        assert calls == [(5, 2.5, True, "b", "x y")]

    @pytest.mark.asyncio
    async def test_parse_failure_replies_error_with_usage(self):
        """解析失败 → 自动回复本地化错误 + 用法，处理器不执行"""
        calls = []

        @command_handler("roll3", args="<count:int> [sides:int=6]")
        async def roll(event, count: int, sides: int = 6):
            calls.append(count)

        replies = []
        with patch.object(command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))):
            await _dispatch("/roll3 abc")

        assert calls == []
        assert len(replies) == 1
        assert "/roll3" in replies[0] and "\n" in replies[0]  # 错误文本 + 用法行
        assert "<count>" in replies[0]

    @pytest.mark.asyncio
    async def test_missing_required_replies_error(self):
        calls = []

        @command_handler("roll4", args="<count:int>")
        async def roll(event, count: int):
            calls.append(count)

        replies = []
        with patch.object(command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))):
            await _dispatch("/roll4")

        assert calls == []
        assert len(replies) == 1

    @pytest.mark.asyncio
    async def test_parse_failure_keeps_claim_and_fires_hook(self):
        """解析失败 → 命令仍被认领（不漏给消息处理器），executed 钩子标记失败"""
        from ErisPulse.Core.Event.message import message as message_handler
        from ErisPulse.Core.lifecycle import lifecycle

        observed, executed = [], []
        results = []

        @message_handler.on_message()
        async def observer(event):
            observed.append(event.get("alt_message"))

        async def on_executed(data):
            executed.append(data["success"])

        lifecycle.register("command.executed", on_executed)
        try:

            @command_handler("locked", args="<count:int>")
            async def locked(event, count: int):
                results.append(count)

            with patch.object(command_handler, "_send_args_error", new=AsyncMock()):
                await _dispatch("/locked bad")
        finally:
            lifecycle.unregister("command.executed", on_executed)

        assert results == []
        assert observed == []  # 认领保持，不漏给消息处理器
        assert executed == [False]

    @pytest.mark.asyncio
    async def test_permission_checked_before_parsing(self):
        """权限检查先于解析：无权限用户触发解析错误输入 → 不回复参数错误"""
        calls, arg_errors = [], []

        def deny(event):
            return False

        @command_handler("secret", args="<count:int>", permission=deny)
        async def secret(event, count: int):
            calls.append(count)

        with patch.object(command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: arg_errors.append(t))):
            await _dispatch("/secret not_a_number")

        assert calls == []
        assert arg_errors == []  # 权限拒绝短路，未触发解析

    @pytest.mark.asyncio
    async def test_backward_compat_no_declaration(self):
        """未声明 args=/options= → handler(event) 行为完全不变（含额外默认参数）"""
        calls = []

        @command_handler("legacy")
        async def legacy(event, untouched="default"):
            calls.append((event.get_command_args(), untouched))

        await _dispatch("/legacy a b")
        assert calls == [(["a", "b"], "default")]

    @pytest.mark.asyncio
    async def test_options_only_rejects_stray_tokens(self):
        """只声明 options 未声明 args → 剔除选项后的剩余 token 报参数过多"""
        calls = []

        @command_handler("optonly", options={"verbose": "-v"})
        async def optonly(event, verbose: bool = False):
            calls.append(verbose)

        replies = []
        with patch.object(command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))):
            await _dispatch("/optonly -v")
        assert calls == [True] and replies == []

        replies.clear()
        with patch.object(command_handler, "_send_args_error", new=AsyncMock(side_effect=lambda e, t: replies.append(t))):
            await _dispatch("/optonly stray")
        assert calls == [True] and len(replies) == 1


class TestHelpAndUsage:
    """help 展示自动 usage；显式 usage 优先"""

    def test_help_auto_usage(self):
        @command_handler("roll5", args="<count:int> [sides:int=6]", options={"verbose": "-v/--verbose"}, help="掷骰子")
        async def roll(event, count: int, sides: int = 6, verbose: bool = False):
            pass

        text = command_handler.help("roll5")
        assert "<count> [sides=6] [-v, --verbose]" in text

    def test_explicit_usage_wins(self):
        @command_handler("roll6", args="<count:int>", usage="自定义用法", help="掷骰子")
        async def roll(event, count: int):
            pass

        text = command_handler.help("roll6")
        assert "自定义用法" in text
        assert "<count>" not in text

    def test_registration_signature_mismatch_raises(self):
        with pytest.raises(ValueError):

            @command_handler("broken", args="<nope:int>")
            async def broken(event):
                pass


class TestI18nKeysComplete:
    """五语言词条完整（用户侧 6 键 + 注册侧 4 键 + trace 1 键）"""

    REQUIRED_KEYS = {
        "core.command.args_parse_failed",
        "core.command.args.invalid",
        "core.command.args.missing",
        "core.command.args.too_many",
        "core.command.args.unknown_option",
        "core.command.args.missing_value",
        "core.command.args.usage",
        "core.command.args.bad_spec",
        "core.command.args.bad_option_forms",
        "core.command.args.option_bad_type",
        "core.command.args.param_mismatch",
    }

    @pytest.mark.parametrize("locale", ["zh_cn", "zh_tw", "en", "ja", "ru"])
    def test_locale_has_all_keys(self, locale):
        import importlib as _il

        mod = _il.import_module(f"ErisPulse.Core.i18n.locales.{locale}")
        missing = self.REQUIRED_KEYS - set(mod.TRANSLATIONS.keys())
        assert not missing, f"{locale} 缺少词条: {missing}"
