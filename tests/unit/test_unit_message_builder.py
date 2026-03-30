"""
MessageBuilder 单元测试

测试 OneBot12 标准消息段构建器的链式调用、快速构建和工具方法
"""

import sys
import importlib.util
from pathlib import Path

import pytest

# 使用 importlib.util 直接加载 message_builder 模块，完全跳过包 __init__ 链
_src = Path(__file__).parent.parent.parent / "src"
_spec = importlib.util.spec_from_file_location(
    "message_builder", _src / "ErisPulse" / "Core" / "Event" / "message_builder.py"
)
_mb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mb)
MessageBuilder = _mb.MessageBuilder


# ==================== 链式调用测试 ====================

class TestMessageBuilderChain:
    """链式调用风格测试"""

    def test_text_chain(self):
        """测试链式添加文本"""
        result = MessageBuilder().text("Hello").text(" World").build()
        assert len(result) == 2
        assert result[0] == {"type": "text", "data": {"text": "Hello"}}
        assert result[1] == {"type": "text", "data": {"text": " World"}}

    def test_image_chain(self):
        """测试链式添加图片"""
        result = MessageBuilder().image("https://example.com/img.jpg").build()
        assert len(result) == 1
        assert result[0]["type"] == "image"
        assert result[0]["data"]["file"] == "https://example.com/img.jpg"

    def test_image_bytes(self):
        """测试图片支持二进制数据"""
        data = b"\x89PNG\r\n"
        result = MessageBuilder().image(data).build()
        assert result[0]["data"]["file"] is data

    def test_audio_chain(self):
        """测试链式添加音频"""
        result = MessageBuilder().audio("https://example.com/audio.mp3").build()
        assert result[0]["type"] == "audio"
        assert result[0]["data"]["file"] == "https://example.com/audio.mp3"

    def test_video_chain(self):
        """测试链式添加视频"""
        result = MessageBuilder().video("https://example.com/video.mp4").build()
        assert result[0]["type"] == "video"
        assert result[0]["data"]["file"] == "https://example.com/video.mp4"

    def test_file_chain(self):
        """测试链式添加文件"""
        result = MessageBuilder().file("/path/to/doc.pdf").build()
        assert result[0]["type"] == "file"
        assert result[0]["data"]["file"] == "/path/to/doc.pdf"

    def test_file_with_filename(self):
        """测试文件带文件名"""
        result = MessageBuilder().file("data", filename="doc.pdf").build()
        assert result[0]["data"]["filename"] == "doc.pdf"

    def test_file_without_filename(self):
        """测试文件不带文件名时无 filename 键"""
        result = MessageBuilder().file("data").build()
        assert "filename" not in result[0]["data"]

    def test_mention_chain(self):
        """测试链式添加 @用户"""
        result = MessageBuilder().mention("123456").build()
        assert result[0]["type"] == "mention"
        assert result[0]["data"]["user_id"] == "123456"

    def test_mention_with_name(self):
        """测试 @用户带用户名"""
        result = MessageBuilder().mention("123456", user_name="Alice").build()
        assert result[0]["data"]["user_name"] == "Alice"

    def test_mention_without_name(self):
        """测试 @用户不带用户名时无 user_name 键"""
        result = MessageBuilder().mention("123456").build()
        assert "user_name" not in result[0]["data"]

    def test_at_alias(self):
        """测试 at 是 mention 的别名"""
        r1 = MessageBuilder().at("123").build()
        r2 = MessageBuilder().mention("123").build()
        assert r1 == r2

    def test_at_with_name(self):
        """测试 at 带用户名"""
        result = MessageBuilder().at("123", user_name="Bob").build()
        assert result[0]["data"]["user_name"] == "Bob"

    def test_reply_chain(self):
        """测试链式添加回复"""
        result = MessageBuilder().reply("msg_123").build()
        assert result[0]["type"] == "reply"
        assert result[0]["data"]["message_id"] == "msg_123"

    def test_at_all_chain(self):
        """测试链式添加 @全体"""
        result = MessageBuilder().at_all().build()
        assert result[0]["type"] == "mention_all"
        assert result[0]["data"] == {}

    def test_custom_chain(self):
        """测试链式添加自定义消息段"""
        result = MessageBuilder().custom("yunhu_form", {"form_id": "123"}).build()
        assert result[0]["type"] == "yunhu_form"
        assert result[0]["data"]["form_id"] == "123"

    def test_complex_chain(self):
        """测试复杂链式调用"""
        result = (
            MessageBuilder()
            .at_all()
            .mention("123")
            .text("你好")
            .image("url")
            .reply("msg_id")
            .build()
        )
        assert len(result) == 5
        assert result[0]["type"] == "mention_all"
        assert result[1]["type"] == "mention"
        assert result[2]["type"] == "text"
        assert result[3]["type"] == "image"
        assert result[4]["type"] == "reply"


# ==================== 快速构建测试 ====================

class TestMessageBuilderStatic:
    """快速构建（静态方法）测试"""

    def test_static_text(self):
        """测试快速构建文本"""
        result = MessageBuilder.text("Hello")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result == [{"type": "text", "data": {"text": "Hello"}}]

    def test_static_image(self):
        """测试快速构建图片"""
        result = MessageBuilder.image("url")
        assert result == [{"type": "image", "data": {"file": "url"}}]

    def test_static_audio(self):
        """测试快速构建音频"""
        result = MessageBuilder.audio("url")
        assert result == [{"type": "audio", "data": {"file": "url"}}]

    def test_static_video(self):
        """测试快速构建视频"""
        result = MessageBuilder.video("url")
        assert result == [{"type": "video", "data": {"file": "url"}}]

    def test_static_file(self):
        """测试快速构建文件"""
        result = MessageBuilder.file("data")
        assert result == [{"type": "file", "data": {"file": "data"}}]

    def test_static_file_with_filename(self):
        """测试快速构建文件带文件名"""
        result = MessageBuilder.file("data", filename="doc.pdf")
        assert result[0]["data"]["filename"] == "doc.pdf"

    def test_static_mention(self):
        """测试快速构建 @用户"""
        result = MessageBuilder.mention("123")
        assert result == [{"type": "mention", "data": {"user_id": "123"}}]

    def test_static_mention_with_name(self):
        """测试快速构建 @用户带用户名"""
        result = MessageBuilder.mention("123", user_name="Alice")
        assert result[0]["data"]["user_name"] == "Alice"

    def test_static_at_alias(self):
        """测试静态 at 是 mention 的别名"""
        assert MessageBuilder.at("123") == MessageBuilder.mention("123")

    def test_static_reply(self):
        """测试快速构建回复"""
        result = MessageBuilder.reply("msg_id")
        assert result == [{"type": "reply", "data": {"message_id": "msg_id"}}]

    def test_static_at_all(self):
        """测试快速构建 @全体"""
        result = MessageBuilder.at_all()
        assert result == [{"type": "mention_all", "data": {}}]


# ==================== 工具方法测试 ====================

class TestMessageBuilderUtils:
    """工具方法测试"""

    def test_build_returns_list(self):
        """测试 build 返回列表"""
        result = MessageBuilder().text("Hi").build()
        assert isinstance(result, list)

    def test_build_returns_copy(self):
        """测试 build 返回的是副本（非引用）"""
        builder = MessageBuilder().text("Hi")
        result1 = builder.build()
        builder.text("World")
        result2 = builder.build()
        assert len(result1) == 1
        assert len(result2) == 2

    def test_copy_independent(self):
        """测试 copy 产生独立副本"""
        base = MessageBuilder().text("Base")
        copy1 = base.copy().text("Copy1")
        copy2 = base.copy().text("Copy2")
        assert len(base.build()) == 1
        assert len(copy1.build()) == 2
        assert len(copy2.build()) == 2
        assert copy1.build()[1]["data"]["text"] == "Copy1"
        assert copy2.build()[1]["data"]["text"] == "Copy2"

    def test_copy_deep(self):
        """测试 copy 是深拷贝"""
        base = MessageBuilder().custom("type", {"key": "value"})
        copy = base.copy()
        copy._segments[0]["data"]["key"] = "modified"
        assert base.build()[0]["data"]["key"] == "value"

    def test_clear(self):
        """测试 clear 清空消息段"""
        builder = MessageBuilder().text("Hi").image("url")
        result = builder.clear()
        assert len(builder.build()) == 0
        assert result is builder  # 返回 self

    def test_clear_chain(self):
        """测试 clear 后继续链式调用"""
        result = MessageBuilder().text("old").clear().text("new").build()
        assert len(result) == 1
        assert result[0]["data"]["text"] == "new"

    def test_len_empty(self):
        """测试空构建器长度"""
        assert len(MessageBuilder()) == 0

    def test_len_nonempty(self):
        """测试非空构建器长度"""
        assert len(MessageBuilder().text("a").text("b")) == 2

    def test_bool_empty(self):
        """测试空构建器布尔值为 False"""
        assert not MessageBuilder()

    def test_bool_nonempty(self):
        """测试非空构建器布尔值为 True"""
        assert MessageBuilder().text("Hi")

    def test_repr_empty(self):
        """测试空构建器 repr"""
        assert "MessageBuilder(segments=0)" == repr(MessageBuilder())

    def test_repr_nonempty(self):
        """测试非空构建器 repr"""
        assert "MessageBuilder(segments=3)" == repr(
            MessageBuilder().text("a").image("b").reply("c")
        )


# ==================== 边界情况测试 ====================

class TestMessageBuilderEdge:
    """边界情况测试"""

    def test_empty_text(self):
        """测试空字符串文本"""
        result = MessageBuilder().text("").build()
        assert result[0]["data"]["text"] == ""

    def test_empty_build(self):
        """测试空构建器的 build"""
        assert MessageBuilder().build() == []

    def test_multiple_same_type(self):
        """测试多次添加同类型消息段"""
        result = MessageBuilder().text("a").text("b").text("c").build()
        assert len(result) == 3
        assert all(seg["type"] == "text" for seg in result)

    def test_chain_returns_self(self):
        """测试链式方法返回 self"""
        builder = MessageBuilder()
        assert builder.text("x") is builder
        assert builder.image("y") is builder
        assert builder.audio("y") is builder
        assert builder.video("y") is builder
        assert builder.file("y") is builder
        assert builder.mention("y") is builder
        assert builder.at("y") is builder
        assert builder.reply("y") is builder
        assert builder.at_all() is builder
        assert builder.custom("y", {}) is builder