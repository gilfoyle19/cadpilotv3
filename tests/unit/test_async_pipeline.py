from types import SimpleNamespace

from cadpilotv3.graph.pipeline import build_async_pipeline


class FakeAsyncPipelineNodes:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.calls = settings.calls

    async def aintent_spec_agent(self, state):
        self.calls.append("intent_spec_agent")
        state["spec"] = SimpleNamespace(component="test bracket")
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
        )
        state["final_geometry"] = {
            "workspace_dir": ".sandbox_runs/fake",
            "result_object_name": "model",
        }
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
        "critic_a_report": {},
        "critic_b_report": {},
        "repair_decision": None,
        "repair_count": 0,
        "critic_a_attempts": 0,
        "critic_b_attempts": 0,
        "final_geometry": None,
        "export_files": [],
        "user_facing_warnings": [],
        "assembly_report_markdown": "",
    }


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
        "critic_checkpoint_b",
        "export_summary_agent",
    ]
    assert result["export_files"] == ["part.step"]
    assert result["assembly_report_markdown"] == "done"
