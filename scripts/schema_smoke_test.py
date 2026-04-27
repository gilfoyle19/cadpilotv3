from cadpilotv3.graph import build_initial_state
from cadpilotv3.schemas import (
    CoordinateConvention,
    CriticReport,
    GeometryPlan,
    IntentSpec,
    Issue,
    ParameterDefinition,
    ParameterSchema,
    PlannedPart,
    ValidationReport,
)


def main() -> None:
    spec = IntentSpec(
        artifact_type="single_part",
        component="mounting_bracket",
        category="mechanical_support",
        complexity="simple",
        parts=["bracket_body"],
        output_format="STEP",
        units="mm",
        style="minimal_printable",
        manufacturing_process=["3D_printing"],
        constraints=["self_supporting", "M5_mounting_holes"],
    )

    plan = GeometryPlan(
        artifact_type="single_part",
        coordinate_convention=CoordinateConvention(
            x="width direction",
            y="depth direction",
            z="height direction",
            zero_config="base face on XY plane",
        ),
        parts=[
            PlannedPart(
                name="bracket_body",
                role="primary_structure",
                modeling_strategy="sketch_extrude",
                strategy_rationale="simple prismatic part with holes and fillets",
                origin="center of base face at Z=0",
                key_features=["base flange", "vertical flange", "two mounting holes"],
                body_type="solid",
            )
        ],
    )

    parameters = ParameterSchema(
        parameters={
            "WIDTH": ParameterDefinition(
                value=80.0,
                unit="mm",
                description="Overall bracket width",
                min=20,
                max=300,
                group="overall_dimensions",
            )
        }
    )

    validation = ValidationReport(
        status="success",
        geometry_valid=True,
        repair_needed=False,
    )

    critic = CriticReport(
        checkpoint="A",
        verdict="pass",
        fidelity_score=0.97,
        drift_detected=False,
        issues=[],
        routing="proceed",
    )

    state = build_initial_state("Create an L-bracket with two mounting holes")
    state.spec = spec
    state.geometry_plan = plan
    state.parameters = parameters
    state.validation = validation
    state.critic_a_report = critic

    print(state.model_dump())
    print(Issue(dimension="scale", severity="minor", description="Looks acceptable"))


if __name__ == "__main__":
    main()