"""
事件覆写系统（event.overrides）单元测试

按事件类型（message / notice / request / meta）与扩展类别（command / acl）
覆盖 set / get / delete 三件套、condition_for 过滤、判定链、整体替换语义、
配置校验、热更新与持久化。
"""

from unittest.mock import patch

import pytest

from ErisPulse.Core.Event import overrides
from ErisPulse.Core.Event.overrides import acl, command, message, meta, notice, request


@pytest.fixture(autouse=True)
def clean_overrides():
    """隔离覆写内存态，测试后恢复"""
    saved = {
        "sections": {t: dict(v) for t, v in overrides._sections.items()},
        "command": dict(overrides._command),
        "acl": dict(overrides._acl),
        "default": overrides._acl_default_allow,
    }
    overrides.clear()
    yield
    overrides.clear()
    for t, v in saved["sections"].items():
        overrides._sections[t] = v
    overrides._command = saved["command"]
    overrides._acl = saved["acl"]
    overrides._acl_default_allow = saved["default"]


class TestMessageOverrides:
    """message 类型：pattern / regex 文本触发条件"""

    def test_set_get_delete(self):
        message.set("My", pattern="签到*", regex="\\d+")
        assert message.get("My") == {"pattern": "签到*", "regex": "re:\\d+"}
        assert message.delete("My") is True
        assert message.get("My") is None
        assert message.delete("My") is False

    def test_condition(self):
        message.set("My", pattern="签到*")
        cond = overrides.condition_for("message", "My")
        assert cond({"alt_message": "签到成功"}) is True
        assert cond({"alt_message": "打卡"}) is False
        # 未配置该类型 -> 无条件
        assert overrides.condition_for("notice", "My") is None

    def test_unknown_param_raises(self):
        with pytest.raises(ValueError):
            message.set("My", bogus_param="x")


class TestDetailTypesOverrides:
    """notice / request / meta：detail_types 白名单"""

    @pytest.mark.parametrize("ns", [notice, request, meta], ids=["notice", "request", "meta"])
    def test_set_get_delete(self, ns):
        ns.set("My", detail_types=["a", "b"])
        assert ns.get("My") == {"detail_types": ["a", "b"]}
        assert ns.delete("My") is True
        assert ns.get("My") is None

    def test_notice_detail_types_condition(self):
        notice.set("My", detail_types="group_increase")  # str 单条目简写
        cond = overrides.condition_for("notice", "My")
        assert cond({"detail_type": "group_increase"}) is True
        assert cond({"detail_type": "friend_add"}) is False
        # 缺 detail_type 的未知事件放行
        assert cond({}) is True

    def test_meta_detail_types_condition(self):
        meta.set("MetaMod", detail_types=["connect"])
        cond = overrides.condition_for("meta", "MetaMod")
        assert cond({"detail_type": "connect"}) is True
        assert cond({"detail_type": "heartbeat"}) is False

    def test_message_type_also_supports_detail_types(self):
        message.set("My", detail_types=["group"])
        cond = overrides.condition_for("message", "My")
        assert cond({"detail_type": "group"}) is True
        assert cond({"detail_type": "private"}) is False

    def test_combined_detail_and_text(self):
        """detail_types + pattern/regex 同时生效"""
        notice.set("My", detail_types=["group_increase"], pattern="欢迎*")
        cond = overrides.condition_for("notice", "My")
        assert cond({"detail_type": "group_increase", "alt_message": "欢迎新成员"}) is True
        assert cond({"detail_type": "group_increase", "alt_message": "其他"}) is False


class TestCommandOverrides:
    """command 扩展类型：实现参数覆写"""

    def test_command_level(self):
        command.set("MyMod", "roll", master=True, hidden=True)
        assert command.get("MyMod", "roll") == {"master": True, "hidden": True}
        assert command.delete("MyMod", "roll") is True
        assert command.get("MyMod", "roll") == {}

    def test_module_level_scalar(self):
        command.set("MyMod", hidden=False)  # 模块级标量
        assert command.get("MyMod")["hidden"] is False

    def test_command_level_wins_over_module_level(self):
        """命令级优先于模块级同名标量"""
        command._check({})
        overrides._command.clear()
        overrides._command["My"] = {"help": "模块级", "roll": {"help": "命令级"}}
        assert command.get("My", "roll") == {"help": "命令级"}
        overrides._command.clear()

    def test_apply_maps_master(self):
        """apply 将覆写键 master 映射到存储键 must_master"""
        command.set("My", "restart", master=True, hidden=True)
        eff = command.apply("My", "restart", {"must_master": False, "help": "原始"})
        assert eff["must_master"] is True
        assert eff["hidden"] is True
        assert eff["help"] == "原始"

    def test_replace_semantics(self):
        """整体替换：重设不残留旧键"""
        command.set("My", "roll", master=True)
        command.set("My", "roll", hidden=True)
        assert command.get("My", "roll") == {"hidden": True}
        # 全空参数 = 移除
        command.set("My", "roll")
        assert command.get("My", "roll") == {}

    def test_unknown_param_raises(self):
        with pytest.raises(ValueError):
            command.set("My", "roll", bogus=True)


class TestAcl:
    """acl 类别：命令用户黑白名单"""

    def test_set_get_delete(self):
        acl.set("roll*", deny="onebot11:u_bad")  # str 单条目简写
        assert acl.get("roll_dice") == {"allow": [], "deny": ["onebot11:u_bad"]}
        assert acl.delete("roll*") is True
        assert acl.get("roll_dice") == {"allow": [], "deny": []}
        assert acl.delete("roll*") is False

    def test_is_allowed_judgement_chain(self):
        """判定链：deny 命中 -> allow 白名单未命中 -> 未配置遵循 default_allow"""
        acl.set("roll", deny=["p:bad"], allow=["p:vip"])
        assert acl.is_allowed("roll", "p", "vip") is True
        assert acl.is_allowed("roll", "p", "bad") is False
        assert acl.is_allowed("roll", "p", "other") is False  # 白名单未命中
        # 未配置 ACL：default_allow=true 放行
        assert acl.is_allowed("other", "p", "u") is True

    def test_acl_glob_matches_actual_command(self):
        """glob ACL 键匹配实际命令名（精确键优先）"""
        acl.set("roll*", deny=["p:u1"])
        acl.set("roll", deny=["p:u2"])
        assert acl.is_allowed("roll", "p", "u2") is False  # 精确键
        assert acl.is_allowed("roll_dice", "p", "u1") is False  # glob 键
        assert acl.is_allowed("roll_dice", "p", "u3") is True

    def test_strict_mode(self):
        """acl_default_allow=false：无 ACL 即拒"""
        overrides._acl_default_allow = False
        assert acl.is_allowed("nope", "p", "u") is False
        acl.set("yes", allow=["p:u"])
        assert acl.is_allowed("yes", "p", "u") is True

    def test_default_allow_property(self):
        assert acl.default_allow is True

    def test_empty_command_name_raises(self):
        with pytest.raises(ValueError):
            acl.set("", deny=["p:u"])


class TestOverridesInfra:
    """通用：topology / 持久化 / 热更新 / 配置校验"""

    def test_topology_shape(self):
        overrides.clear()
        message.set("M", pattern="x*")
        command.set("M2", hidden=True)
        acl.set("roll", deny=["p:u"])
        topo = overrides.topology()
        assert set(topo.keys()) == {"message", "notice", "request", "meta", "command", "acl"}
        assert topo["message"]["M"] == {"pattern": "x*"}
        assert topo["command"]["M2"] == {"hidden": True}
        assert topo["acl"]["roll"] == {"deny": ["p:u"]}

    def test_persist_writes_config(self):
        """各命名空间 persist 经 set_erispulse_section 落盘到对应类型节"""
        written = {}

        def fake_set(path, value):
            written[path] = value

        with patch("ErisPulse.Core.Event.overrides.set_erispulse_section", side_effect=fake_set):
            message.set("M", pattern="x*")
            command.set("M2", "roll", master=True)
            acl.set("roll", deny=["p:u"])
        assert written["event.overrides.message"] == {"M": {"pattern": "x*"}}
        assert written["event.overrides.command"] == {"M2": {"roll": {"master": True}}}
        assert written["event.overrides.acl"] == {"roll": {"deny": ["p:u"]}}

    def test_config_hot_reload(self):
        """配置热更新后覆写缓存重建"""
        overrides.clear()
        with patch(
            "ErisPulse.runtime.get_event_config",
            return_value={
                "overrides": {
                    "message": {"M": {"pattern": "签到*"}},
                    "command": {"M2": {"roll": {"master": True}}},
                    "acl": {"roll": {"deny": ["p:u"]}},
                    "acl_default_allow": False,
                }
            },
        ):
            overrides._reload({})
        assert overrides.condition_for("message", "M")({"alt_message": "签到1"}) is True
        assert command.get("M2", "roll") == {"master": True}
        assert acl.is_allowed("roll", "p", "u") is False
        assert acl.default_allow is False

    def test_config_validation_unknown_param(self):
        """未知参数告警并剔除，合法保留"""
        overrides.clear()
        with patch(
            "ErisPulse.runtime.get_event_config",
            return_value={"overrides": {"message": {"M": {"pattern": "x*", "pattren": "y*"}}}},
        ):
            overrides._reload({})
        assert overrides._sections["message"]["M"] == {"pattern": "x*"}

    def test_config_validation_unknown_type_section(self):
        """未知类型节（拼错类型名）告警并忽略"""
        overrides.clear()
        with patch(
            "ErisPulse.runtime.get_event_config",
            return_value={"overrides": {"messgae": {"M": {}}, "message": {"M": {"pattern": "x*"}}}},
        ):
            overrides._reload({})
        assert "messgae" not in overrides._sections
        assert overrides._sections["message"]["M"] == {"pattern": "x*"}

    def test_config_validation_bad_entry(self):
        """非法条目（值非 dict）告警并忽略"""
        overrides.clear()
        with patch(
            "ErisPulse.runtime.get_event_config",
            return_value={"overrides": {"message": {"Bad": "oops"}}},
        ):
            overrides._reload({})
        assert "Bad" not in overrides._sections["message"]
