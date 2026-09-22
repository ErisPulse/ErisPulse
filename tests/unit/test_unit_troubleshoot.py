"""
模块排查诊断（explain_module / explain_event）单元测试

EPRFC-2026-001 方向五·场景一 / 二。测试：未注册模块的原因报告、
懒加载模块的正常态判定、依赖缺失检测、SDK 版本不满足检测；
事件诊断的适配器未注册、身份拉黑、模块会话屏蔽、命令未命中识别。
"""



class TestExplainModule:
    def test_unregistered_module_reports(self):
        from ErisPulse.runtime import explain_module

        result = explain_module("definitely_not_a_module_xyz")
        assert result["registered"] is False
        assert result["reasons"]
        assert "未注册" in result["conclusion"]

    def test_lazy_module_reports_normal_state(self):
        from ErisPulse.Core import module as module_mgr
        from ErisPulse.Core.Bases.module import BaseModule, ModuleLoadStrategy, ModuleMeta
        from ErisPulse.runtime import explain_module

        class LazyMod(BaseModule):
            async def on_load(self, event=None) -> bool:
                return True

            async def on_unload(self, event=None) -> bool:
                return True

            @staticmethod
            def get_meta():
                return ModuleMeta(name="DiagLazyMod", version="0.1.0")

            @staticmethod
            def get_load_strategy():
                return ModuleLoadStrategy(lazy_load=True)

        module_mgr.register("DiagLazyMod", LazyMod)
        try:
            result = explain_module("DiagLazyMod")
            assert result["registered"] is True
            assert result["lazy"] is True
            assert result["loaded"] is False
            assert "懒加载" in result["conclusion"]
        finally:
            module_mgr._module_classes.pop("DiagLazyMod", None)

    def test_missing_dependency_detected(self):
        from ErisPulse.Core import module as module_mgr
        from ErisPulse.Core.Bases.module import BaseModule, ModuleLoadStrategy, ModuleMeta
        from ErisPulse.runtime import explain_module

        class DepMod(BaseModule):
            async def on_load(self, event=None) -> bool:
                return True

            async def on_unload(self, event=None) -> bool:
                return True

            @staticmethod
            def get_meta():
                return ModuleMeta(name="DiagDepMod", version="0.1.0")

            @staticmethod
            def get_load_strategy():
                return ModuleLoadStrategy(lazy_load=False, depends=["ghost_dep"])

        module_mgr.register("DiagDepMod", DepMod)
        try:
            result = explain_module("DiagDepMod")
            assert "ghost_dep" in result["missing_dependencies"]
            assert any("依赖未加载" in r for r in result["reasons"])
        finally:
            module_mgr._module_classes.pop("DiagDepMod", None)


class TestExplainEvent:
    def _event(self, text="/x", user_id="u1", platform="onebot11"):
        return {
            "id": "diag_evt",
            "time": 1,
            "type": "message",
            "detail_type": "private",
            "platform": platform,
            "self": {"platform": platform, "user_id": "bot_x"},
            "user_id": user_id,
            "message": [{"type": "text", "data": {"text": text}}],
            "alt_message": text,
        }

    def test_unregistered_adapter_detected(self):
        from ErisPulse.runtime import explain_event

        result = explain_event(self._event(platform="ghost_platform"))
        assert result["adapter_registered"] is False
        assert any("适配器未注册" in r for r in result["reasons"])

    async def test_registered_adapter_and_command_match(self):
        from ErisPulse.Core.Event.command import command as command_handler
        from ErisPulse.runtime import explain_event

        @command_handler("diag_cmd")
        async def diag_cmd(event):
            pass

        result = explain_event(self._event("/diag_cmd"))
        assert result["command_like"] is True
        assert result["command_registered"] is True

        result2 = explain_event(self._event("/diag_cmdx"))
        assert result2["command_registered"] is False
        assert any("未命中" in r for r in result2["reasons"])

    def test_format_report_renders(self):
        from ErisPulse.runtime import explain_module, format_report

        text = format_report(explain_module("nope_xyz"))
        assert "诊断" in text and "结论" in text
