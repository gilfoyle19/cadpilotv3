from cadpilotv3.logging import (
    get_logger,
    log_error,
    log_node_end,
    log_node_start,
    log_route_decision,
    setup_logging,
)


def main() -> None:
    setup_logging()
    logger = get_logger("cadpilotv3.smoke")

    run_id = "local-run-001"

    log_node_start(
        logger,
        node_name="intent_spec_agent",
        run_id=run_id,
        attempt=1,
        user_prompt_preview="Build a 2 DOF robotic arm in CadQuery and export as STEP",
    )

    log_route_decision(
        logger,
        node_name="critic_checkpoint_a",
        route="parameter_agent",
        run_id=run_id,
        attempt=1,
    )

    log_node_end(
        logger,
        node_name="intent_spec_agent",
        run_id=run_id,
        status="success",
    )

    try:
        raise ValueError("Mock validation failure")
    except ValueError:
        log_error(
            logger,
            message="Execution validation failed",
            node_name="execution_validation",
            run_id=run_id,
            error_class="runtime_error",
            exc_info=True,
        )


if __name__ == "__main__":
    main()