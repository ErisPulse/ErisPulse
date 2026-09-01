"""
统一文本/条目匹配工具单元测试

测试 compile_entry_matcher（精确 / glob / re: 正则）、compile_entry_list、
compile_text_matcher（pattern + regex AND）、extract_text 与大小写不敏感语义。
"""

import pytest

from ErisPulse.Core.text_match import (
    compile_entry_list,
    compile_entry_matcher,
    compile_text_matcher,
    entry_matches,
    extract_text,
    is_entry_pattern,
)


def _event(text):
    return {
        "type": "message",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }


class TestEntryMatcher:
    """单条目匹配（精确 / glob / re: 正则）"""

    def test_exact_case_insensitive(self):
        m = compile_entry_matcher("Chat")
        assert m("Chat") is True
        assert m("chat") is True
        assert m("CHAT") is True
        assert m("ChatX") is False

    def test_glob_star(self):
        m = compile_entry_matcher("Tool*")
        assert m("Tool") is True
        assert m("ToolBox") is True
        assert m("toolbox_pro") is True
        assert m("MyTool") is False

    def test_glob_question(self):
        m = compile_entry_matcher("bo?")
        assert m("bot") is True
        assert m("bo") is False
        assert m("bots") is False

    def test_glob_bracket(self):
        m = compile_entry_matcher("[Tt]ool")
        assert m("Tool") is True
        assert m("tool") is True
        assert m("Zool") is False

    def test_regex_prefix_search(self):
        m = compile_entry_matcher("re:^Danger.*")
        assert m("DangerBot") is True
        assert m("danger_zone") is True
        assert m("MyDanger") is False

    def test_regex_case_insensitive_by_default(self):
        m = compile_entry_matcher("re:HELLO")
        assert m("hello world") is True
        assert m("world") is False

    def test_invalid_regex_never_matches(self):
        m = compile_entry_matcher("re:[invalid")
        assert m("anything") is False

    def test_is_entry_pattern(self):
        assert is_entry_pattern("Tool*") is True
        assert is_entry_pattern("re:^x") is True
        assert is_entry_pattern("plain") is False


class TestEntryList:
    """条目列表：任一命中即 True"""

    def test_none_or_empty(self):
        assert compile_entry_list(None) is None
        assert compile_entry_list([]) is None

    def test_any_match(self):
        m = compile_entry_list(["Chat", "Tool*", "re:^Danger"])
        assert m("Chat") is True
        assert m("ToolBox") is True
        assert m("dangerbot") is True
        assert m("Other") is False

    def test_string_coerced_to_list(self):
        m = compile_entry_list("Chat")
        assert m("chat") is True


class TestTextMatcher:
    """compile_text_matcher：pattern 与 regex 须都命中"""

    def test_both_none(self):
        assert compile_text_matcher(None, None) is None

    def test_pattern_only(self):
        cond = compile_text_matcher("签到*", None)
        assert cond(_event("签到成功")) is True
        assert cond(_event("打卡失败")) is False

    def test_regex_only(self):
        cond = compile_text_matcher(None, r"\d+\s*元")
        assert cond(_event("优惠 5 元")) is True
        assert cond(_event("没有优惠")) is False

    def test_pattern_and_regex(self):
        cond = compile_text_matcher("*号", r"^[0-9]+号$")
        assert cond(_event("123号")) is True
        # glob 命中但 regex 不命中
        assert cond(_event("abc号")) is False

    def test_invalid_regex_falls_back_to_no_match(self):
        cond = compile_text_matcher(None, "[invalid")
        assert cond(_event("anything")) is False


class TestExtractText:
    """extract_text：alt_message 优先，回退拼接 text 段"""

    def test_alt_message_first(self):
        event = {
            "message": [{"type": "text", "data": {"text": "segments"}}],
            "alt_message": "alt",
        }
        assert extract_text(event) == "alt"

    def test_segments_fallback(self):
        event = {
            "message": [
                {"type": "image", "data": {"file": "x.png"}},
                {"type": "text", "data": {"text": "a"}},
                {"type": "text", "data": {"text": "b"}},
            ],
        }
        assert extract_text(event) == "ab"

    def test_exception_returns_empty(self):
        assert extract_text(None) == ""
        assert extract_text("not-a-dict") == ""


class TestEntryMatches:
    """便捷单次匹配"""

    def test_entry_matches(self):
        assert entry_matches("Tool*", "toolbox") is True
        assert entry_matches("re:^a+", "aaa") is True
        assert entry_matches("chat", "Chat") is True
        assert entry_matches("chat", "chatting") is False
