from __future__ import annotations

from pathlib import Path

from cadpilotv3.config.settings import AppSettings


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_artifacts_dir(settings: AppSettings) -> Path:
    return ensure_dir(Path(settings.cad_artifacts_dir).resolve())


def get_run_dir(settings: AppSettings, run_id: str) -> Path:
    return ensure_dir(get_artifacts_dir(settings) / run_id)


def get_output_dir(settings: AppSettings, run_id: str) -> Path:
    return ensure_dir(get_run_dir(settings, run_id) / "output")


def get_logs_dir(settings: AppSettings, run_id: str) -> Path:
    return ensure_dir(get_run_dir(settings, run_id) / "logs")


def get_temp_dir(settings: AppSettings, run_id: str) -> Path:
    return ensure_dir(get_run_dir(settings, run_id) / "tmp")