"""
examples 示例项目导入冒烟测试

AGENTS 规则 20-22 要求 CLI 脚手架模板与 examples 保持同步——本文件以
"示例可导入 + 关键写法未漂移"作为机器守护：

- example-module / example-adapter 可正常导入（引用的框架 API 全部存在）
- example-adapter 的 Converter 继承 BaseConverter（模板同款写法，防止
  示例回退到手写转换的旧范式）
"""

import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def _import_from(example_dir: str, module_name: str):
    sys.path.insert(0, str(EXAMPLES_DIR / example_dir))
    try:
        __import__(module_name)
        return sys.modules[module_name]
    finally:
        sys.path.pop(0)


def test_example_module_imports():
    mod = _import_from("example-module", "MyModule")
    assert hasattr(mod, "Main")
    assert "Main" in mod.__all__


def test_example_adapter_imports():
    mod = _import_from("example-adapter", "MyAdapter")
    assert hasattr(mod, "MyAdapter")
    assert hasattr(mod, "MyAdapterConverter")
    assert "MyAdapterConverter" in mod.__all__


def test_example_adapter_converter_inherits_base_converter():
    """示例 Converter 必须继承 BaseConverter（与 CLI 模板同一写法，防旧范式回流）"""
    from ErisPulse.Core.Bases import BaseConverter

    mod = _import_from("example-adapter", "MyAdapter")
    assert issubclass(mod.MyAdapterConverter, BaseConverter)

    converter = mod.MyAdapterConverter()
    raw = {
        "type": "message",
        "event_id": "e1",
        "sender_id": "u1",
        "group_id": "g1",
        "content": "hello",
    }
    event = converter.convert(raw)
    assert event["type"] == "message"
    assert event["detail_type"] == "group"
    assert event["user_id"] == "u1"
    assert event["message"][0]["type"] == "text"
    assert event["alt_message"] == "hello"
    assert event["myplatform_raw"] == raw  # 原始数据按扩展命名保留
