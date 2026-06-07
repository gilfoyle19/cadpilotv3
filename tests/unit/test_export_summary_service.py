from types import SimpleNamespace

from cadpilotv3.schemas.export import ExportSummary
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.services.export_summary_service import ExportSummaryService


def test_execute_uses_deterministic_summary_when_llm_summary_is_disabled(
    tmp_path,
) -> None:
    service = _service(
        tmp_path,
        cad_enable_llm_export_summary=False,
        agent=FailingAgent(),
    )

    result = service.execute(
        geometry_object=object(),
        user_prompt="Make a 40 mm wide bracket.",
        spec=_spec(),
        parameters=_parameters(),
        validation=_validation(),
        critic_b_report=SimpleNamespace(
            user_facing_warnings=["Check M4 hole fit after printing."],
        ),
    )

    assert result.export_files[0].filename == "test_bracket.step"
    assert result.user_facing_warnings == ["Check M4 hole fit after printing."]
    assert "# Test Bracket" in result.assembly_report_markdown
    assert "- Request: Make a 40 mm wide bracket." in result.assembly_report_markdown
    assert "- Bounding box: 40 x 20 x 10 mm" in result.assembly_report_markdown
    assert "| WIDTH | 40 | mm | Overall width |" in result.assembly_report_markdown
    assert "| STEP | test_bracket.step | 12.5 |" in result.assembly_report_markdown
    assert "## Warnings" in result.assembly_report_markdown


async def test_aexecute_uses_deterministic_summary_when_llm_summary_is_disabled(
    tmp_path,
) -> None:
    service = _service(
        tmp_path,
        cad_enable_llm_export_summary=False,
        agent=FailingAgent(),
    )

    result = await service.aexecute(
        geometry_object=object(),
        user_prompt="Make a 40 mm wide bracket.",
        spec=_spec(),
        parameters=_parameters(),
        validation=_validation(),
        critic_b_report=SimpleNamespace(user_facing_warnings=[]),
    )

    assert result.export_files[0].filename == "test_bracket.step"
    assert "# Test Bracket" in result.assembly_report_markdown
    assert "## Export Files" in result.assembly_report_markdown


def test_execute_uses_llm_summary_by_default(tmp_path) -> None:
    agent = RecordingAgent(
        ExportSummary(
            export_files=[],
            assembly_report_markdown="# LLM Report\n",
            user_facing_warnings=[],
        )
    )
    service = _service(
        tmp_path,
        cad_enable_llm_export_summary=True,
        agent=agent,
    )

    result = service.execute(
        geometry_object=object(),
        user_prompt="Make a 40 mm wide bracket.",
        spec=_spec(),
        parameters=_parameters(),
        validation=_validation(),
        critic_b_report=SimpleNamespace(
            user_facing_warnings=["LLM report inherited warning."],
        ),
    )

    assert agent.run_calls == 1
    assert result.assembly_report_markdown == "# LLM Report\n"
    assert result.export_files[0].filename == "test_bracket.step"
    assert result.user_facing_warnings == ["LLM report inherited warning."]


async def test_aexecute_uses_llm_summary_by_default(tmp_path) -> None:
    agent = RecordingAgent(
        ExportSummary(
            export_files=[],
            assembly_report_markdown="# Async LLM Report\n",
            user_facing_warnings=[],
        )
    )
    service = _service(
        tmp_path,
        cad_enable_llm_export_summary=True,
        agent=agent,
    )

    result = await service.aexecute(
        geometry_object=object(),
        user_prompt="Make a 40 mm wide bracket.",
        spec=_spec(),
        parameters=_parameters(),
        validation=_validation(),
        critic_b_report=SimpleNamespace(user_facing_warnings=[]),
    )

    assert agent.arun_calls == 1
    assert result.assembly_report_markdown == "# Async LLM Report\n"
    assert result.export_files[0].filename == "test_bracket.step"


class FakeExporter:
    def __init__(self, output_dir) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir()

    def export(self, **kwargs):
        return [
            SimpleNamespace(
                format="STEP",
                filename="test_bracket.step",
                filepath=str(self.output_dir / "test_bracket.step"),
                size_kb=12.5,
                contents="Generated STEP file",
            )
        ]


class FailingAgent:
    def run(self, **kwargs):
        raise AssertionError("LLM export summary should not run")

    async def arun(self, **kwargs):
        raise AssertionError("Async LLM export summary should not run")


class RecordingAgent:
    def __init__(self, result: ExportSummary) -> None:
        self.result = result
        self.run_calls = 0
        self.arun_calls = 0

    def run(self, **kwargs):
        self.run_calls += 1
        return self.result

    async def arun(self, **kwargs):
        self.arun_calls += 1
        return self.result


def _service(
    tmp_path,
    *,
    cad_enable_llm_export_summary: bool,
    agent,
) -> ExportSummaryService:
    service = object.__new__(ExportSummaryService)
    service.settings = SimpleNamespace(
        cad_enable_llm_export_summary=cad_enable_llm_export_summary,
    )
    service.exporter = FakeExporter(tmp_path / "output")
    service.agent = agent
    return service


def _spec() -> IntentSpec:
    return IntentSpec(
        component="Test Bracket",
        component_type="single_part",
        manufacturing_process="FDM",
        units="mm",
        output_format="STEP",
    )


def _parameters() -> ParameterSchema:
    return ParameterSchema.model_validate(
        {
            "parameters": {
                "WIDTH": {
                    "value": 40,
                    "unit": "mm",
                    "description": "Overall width",
                }
            }
        }
    )


def _validation() -> ValidationReport:
    return ValidationReport.model_validate(
        {
            "status": "success",
            "error_summary": "The script executed successfully.",
            "geometry_valid": True,
            "repair_needed": False,
            "geometry_report": {
                "artifact_type": "single_part",
                "part_count": 1,
                "bounding_box_mm": [40, 20, 10],
                "volume_mm3": 8000,
                "face_count": 6,
                "is_manifold": True,
                "assembly_valid": True,
            },
        }
    )
