import logging
import sys
from typing import Any

from cadpilotv3.config import get_settings
from cadpilotv3.logging.formatters import JsonFormatter


def setup_logging() -> None:
    settings = get_settings()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.log_json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        if not settings.log_include_timestamps:
            fmt = "%(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt=fmt))

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any,
) -> None:
    logger.log(level, message, extra=context)


def log_node_start(
    logger: logging.Logger,
    node_name: str,
    run_id: str | None = None,
    attempt: int | None = None,
    user_prompt_preview: str | None = None,
) -> None:
    log_with_context(
        logger,
        logging.INFO,
        f"Starting node: {node_name}",
        node_name=node_name,
        run_id=run_id,
        attempt=attempt,
        user_prompt_preview=user_prompt_preview,
    )


def log_node_end(
    logger: logging.Logger,
    node_name: str,
    run_id: str | None = None,
    status: str | None = None,
) -> None:
    log_with_context(
        logger,
        logging.INFO,
        f"Finished node: {node_name}",
        node_name=node_name,
        run_id=run_id,
        status=status,
    )


def log_route_decision(
    logger: logging.Logger,
    node_name: str,
    route: str,
    run_id: str | None = None,
    attempt: int | None = None,
) -> None:
    log_with_context(
        logger,
        logging.INFO,
        f"Routing from {node_name} to {route}",
        node_name=node_name,
        route=route,
        run_id=run_id,
        attempt=attempt,
    )


def log_error(
    logger: logging.Logger,
    message: str,
    node_name: str | None = None,
    run_id: str | None = None,
    error_class: str | None = None,
    exc_info: Any = None,
) -> None:
    logger.error(
        message,
        extra={
            "node_name": node_name,
            "run_id": run_id,
            "error_class": error_class,
        },
        exc_info=exc_info,
    )