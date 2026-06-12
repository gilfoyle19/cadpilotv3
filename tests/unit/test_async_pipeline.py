from types import SimpleNamespace

from cadpilotv3.graph import routing
from cadpilotv3.graph.pipeline import build_async_pipeline, build_pipeline


class FakeSyncPipelineNodes:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.calls = settings.calls

    def intent_spec_agent(self, state):
        self.calls.append("intent_spec_agent")
        state["spec"] = SimpleNamespace(component="test bracket")
        return state

    def design_synthesis_agent(self, state):
        self.calls.append("design_synthesis_agent")
        state["spec"] = SimpleNamespace(component="test bracket")
        state["geometry_plan"] = SimpleNamespace(parts=[])
        state["critic_a_report"] = SimpleNamespace(
            verdict=getattr(self.settings, "design_synthesis_verdict", "pass"),
            routing=getattr(self.settings, "design_synthesis_routing", "proceed"),
            issues=[],
        )
        state["parameters"] = SimpleNamespace(parameters={})
        return state

    def geometry_planner_agent(self, state):
        self.calls.append("geometry_planner_agent")
        state["geometry_plan"] = SimpleNamespace(parts=[])
        return state

    def critic_checkpoint_a(self, state):
        self.calls.append("critic_checkpoint_a")
        state["critic_a_report"] = SimpleNamespace(
            verdict="pass",
            routing="proceed",
        )
        return state

    def parameter_agent(self, state):
        self.calls.append("parameter_agent")
        state["parameters"] = SimpleNamespace(parameters={})
        return state

    def code_generation_infill_agent(self, state):
        self.calls.append("code_generation_infill_agent")
        state["script"] = "import cadquery as cq\n"
        return state

    def execution_validation_node(self, state):
        self.calls.append("execution_validation_node")
        state["validation"] = SimpleNamespace(
            status="success",
            repair_needed=False,
            geometry_valid=True,
            geometry_report=SimpleNamespace(
                artifact_type="single_part",
                part_count=1,
            ),
        )
        state["final_geometry"] = {
            "workspace_dir": ".sandbox_runs/fake",
            "result_object_name": "model",
        }
        return state

    def contract_validation_node(self, state):
        self.calls.append("contract_validation_node")
        state["contract_validation"] = SimpleNamespace(
            status="pass",
            passed=True,
            failure_count=0,
            warning_count=0,
            compact_evidence=[],
        )
        return state

    def repair_agent(self, state):
        self.calls.append("repair_agent")
        return state

    def critic_checkpoint_b(self, state):
        self.calls.append("critic_checkpoint_b")
        state["critic_b_report"] = SimpleNamespace(
            routing="export",
            user_facing_warnings=[],
        )
        return state

    def export_summary_agent(self, state):
        self.calls.append("export_summary_agent")
        state["export_files"] = ["part.step"]
        state["assembly_report_markdown"] = "done"
        state["user_facing_warnings"] = []
        return state


class FakeAsyncPipelineNodes:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.calls = settings.calls

    async def aintent_spec_agent(self, state):
        self.calls.append("intent_spec_agent")
        state["spec"] = SimpleNamespace(component="test bracket")
        return state

    async def adesign_synthesis_agent(self, state):
        self.calls.append("design_synthesis_agent")
        state["spec"] = SimpleNamespace(component="test bracket")
        state["geometry_plan"] = SimpleNamespace(parts=[])
        state["critic_a_report"] = SimpleNamespace(
            verdict=getattr(self.settings, "design_synthesis_verdict", "pass"),
            routing=getattr(self.settings, "design_synthesis_routing", "proceed"),
            issues=[],
        )
        state["parameters"] = SimpleNamespace(parameters={})
        return state

    async def ageometry_planner_agent(self, state):
        self.calls.append("geometry_planner_agent")
        state["geometry_plan"] = SimpleNamespace(parts=[])
        return state

    async def acritic_checkpoint_a(self, state):
        self.calls.append("critic_checkpoint_a")
        state["critic_a_report"] = SimpleNamespace(
            verdict="pass",
            routing="proceed",
        )
        return state

    async def aparameter_agent(self, state):
        self.calls.append("parameter_agent")
        state["parameters"] = SimpleNamespace(parameters={})
        return state

    async def acode_generation_infill_agent(self, state):
        self.calls.append("code_generation_infill_agent")
        state["script"] = "import cadquery as cq\n"
        return state

    async def aexecution_validation_node(self, state):
        self.calls.append("execution_validation_node")
        state["validation"] = SimpleNamespace(
            status="success",
            repair_needed=False,
            geometry_valid=True,
            geometry_report=SimpleNamespace(
                artifact_type="single_part",
                part_count=1,
            ),
        )
        state["final_geometry"] = {
            "workspace_dir": ".sandbox_runs/fake",
            "result_object_name": "model",
        }
        return state

    async def acontract_validation_node(self, state):
        self.calls.append("contract_validation_node")
        state["contract_validation"] = SimpleNamespace(
            status="pass",
            passed=True,
            failure_count=0,
            warning_count=0,
            compact_evidence=[],
        )
        return state

    async def arepair_agent(self, state):
        self.calls.append("repair_agent")
        return state

    async def acritic_checkpoint_b(self, state):
        self.calls.append("critic_checkpoint_b")
        state["critic_b_report"] = SimpleNamespace(
            routing="export",
            user_facing_warnings=[],
        )
        return state

    async def aexport_summary_agent(self, state):
        self.calls.append("export_summary_agent")
        state["export_files"] = ["part.step"]
        state["assembly_report_markdown"] = "done"
        state["user_facing_warnings"] = []
        return state


def _initial_state() -> dict:
    return {
        "user_prompt": "Make a bracket.",
        "spec": {},
        "geometry_plan": {},
        "parameters": {},
        "script": "",
        "validation": {},
        "contract_validation": {},
        "critic_a_report": {},
        "critic_b_report": {},
        "repair_decision": None,
        "repair_history": [],
        "repair_count": 0,
        "direct_repair_codegen": False,
        "critic_a_attempts": 0,
        "critic_b_attempts": 0,
        "final_geometry": None,
        "export_files": [],
        "user_facing_warnings": [],
        "assembly_report_markdown": "",
    }


def test_build_pipeline_uses_legacy_front_half_by_default(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeSyncPipelineNodes,
    )

    pipeline = build_pipeline(SimpleNamespace(calls=calls))
    result = pipeline.invoke(_initial_state())

    assert calls == [
        "intent_spec_agent",
        "geometry_planner_agent",
        "critic_checkpoint_a",
        "parameter_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["export_files"] == ["part.step"]
    assert result["assembly_report_markdown"] == "done"


def test_build_pipeline_uses_design_synthesis_when_enabled(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeSyncPipelineNodes,
    )

    pipeline = build_pipeline(
        SimpleNamespace(calls=calls, cad_enable_design_synthesis=True)
    )
    result = pipeline.invoke(_initial_state())

    assert calls == [
        "design_synthesis_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["spec"].component == "test bracket"
    assert result["export_files"] == ["part.step"]


def test_build_pipeline_replans_after_failed_design_synthesis_self_check(
    monkeypatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeSyncPipelineNodes,
    )
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(
            cad_enable_conditional_critic_b=False,
            cad_max_critic_a_attempts=2,
            cad_max_critic_b_attempts=2,
            cad_max_repair_attempts=2,
        ),
    )

    pipeline = build_pipeline(
        SimpleNamespace(
            calls=calls,
            cad_enable_design_synthesis=True,
            design_synthesis_verdict="fail",
            design_synthesis_routing="replan",
        )
    )
    result = pipeline.invoke(_initial_state())

    assert calls == [
        "design_synthesis_agent",
        "geometry_planner_agent",
        "critic_checkpoint_a",
        "parameter_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["critic_a_report"].routing == "proceed"
    assert result["export_files"] == ["part.step"]
    assert "intent_spec_agent" not in calls


async def test_build_async_pipeline_supports_ainvoke(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeAsyncPipelineNodes,
    )

    pipeline = build_async_pipeline(SimpleNamespace(calls=calls))
    result = await pipeline.ainvoke(_initial_state())

    assert calls == [
        "intent_spec_agent",
        "geometry_planner_agent",
        "critic_checkpoint_a",
        "parameter_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["export_files"] == ["part.step"]
    assert result["assembly_report_markdown"] == "done"


async def test_build_async_pipeline_can_skip_critic_b_when_enabled(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeAsyncPipelineNodes,
    )
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(
            cad_enable_conditional_critic_b=True,
            cad_max_critic_a_attempts=2,
            cad_max_critic_b_attempts=2,
            cad_max_repair_attempts=2,
        ),
    )

    pipeline = build_async_pipeline(SimpleNamespace(calls=calls))
    result = await pipeline.ainvoke(_initial_state())

    assert calls == [
        "intent_spec_agent",
        "geometry_planner_agent",
        "critic_checkpoint_a",
        "parameter_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "export_summary_agent",
    ]
    assert result["export_files"] == ["part.step"]


async def test_build_async_pipeline_uses_design_synthesis_when_enabled(
    monkeypatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeAsyncPipelineNodes,
    )

    pipeline = build_async_pipeline(
        SimpleNamespace(calls=calls, cad_enable_design_synthesis=True)
    )
    result = await pipeline.ainvoke(_initial_state())

    assert calls == [
        "design_synthesis_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["spec"].component == "test bracket"
    assert result["export_files"] == ["part.step"]


async def test_build_async_pipeline_replans_after_failed_design_synthesis_self_check(
    monkeypatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "cadpilotv3.graph.pipeline.PipelineNodes",
        FakeAsyncPipelineNodes,
    )
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(
            cad_enable_conditional_critic_b=False,
            cad_max_critic_a_attempts=2,
            cad_max_critic_b_attempts=2,
            cad_max_repair_attempts=2,
        ),
    )

    pipeline = build_async_pipeline(
        SimpleNamespace(
            calls=calls,
            cad_enable_design_synthesis=True,
            design_synthesis_verdict="fail",
            design_synthesis_routing="replan",
        )
    )
    result = await pipeline.ainvoke(_initial_state())

    assert calls == [
        "design_synthesis_agent",
        "geometry_planner_agent",
        "critic_checkpoint_a",
        "parameter_agent",
        "code_generation_infill_agent",
        "execution_validation_node",
        "contract_validation_node",
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["critic_a_report"].routing == "proceed"
    assert result["export_files"] == ["part.step"]
    assert "intent_spec_agent" not in calls
