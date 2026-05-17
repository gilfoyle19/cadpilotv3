from __future__ import annotations

from pathlib import Path

import streamlit as st

from cadpilotv3.ui.pipeline_adapter import (
    DEFAULT_DEMO_PROMPT,
    format_stream_event,
    run_streaming_pipeline_for_ui,
)
from cadpilotv3.ui.step_viewer import render_step_viewer


def _init_session_state() -> None:
    st.session_state.setdefault(
        "messages",
        [
            {
                "role": "assistant",
                "content": (
                    "Describe the part you want and I’ll generate a validated CAD model for it."
                ),
            }
        ],
    )
    st.session_state.setdefault("latest_step_path", None)
    st.session_state.setdefault("latest_result", None)


def _assistant_message_from_result(result: dict) -> str:
    report = str(result.get("assembly_report_markdown") or "").strip()
    if report:
        return report

    export_files = result.get("export_files") or []
    if export_files:
        return "CAD generation completed and the latest model is ready in the viewer."

    return "CAD generation completed, but no export summary was produced."


def _find_step_path(result: dict) -> str | None:
    for export_file in result.get("export_files") or []:
        if hasattr(export_file, "model_dump"):
            export_file = export_file.model_dump(mode="json")

        if not isinstance(export_file, dict):
            continue

        filename = str(export_file.get("filename") or "")
        filepath = str(export_file.get("filepath") or "")
        file_format = str(export_file.get("format") or "").upper()

        if file_format == "STEP" or filename.lower().endswith((".step", ".stp")):
            if filepath and Path(filepath).exists():
                return filepath

    return None


def _render_chat_panel() -> None:
    st.subheader("Chat")

    if st.button("Use sample prompt", use_container_width=True):
        st.session_state.pending_prompt = DEFAULT_DEMO_PROMPT

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Describe a CAD part…")
    pending_prompt = st.session_state.pop("pending_prompt", None)
    submitted_prompt = prompt or pending_prompt

    if not submitted_prompt:
        return

    st.session_state.messages.append({"role": "user", "content": submitted_prompt})
    with st.chat_message("user"):
        st.markdown(submitted_prompt)

    with st.chat_message("assistant"):
        status = st.status("Running CadPilot…", expanded=True)

        def on_event(event) -> None:
            message = format_stream_event(event)
            if message:
                status.write(message)

        try:
            result = run_streaming_pipeline_for_ui(submitted_prompt, on_event=on_event)
            assistant_message = _assistant_message_from_result(result)
            st.markdown(assistant_message)
            status.update(label="CadPilot finished", state="complete", expanded=False)
        except Exception as exc:
            result = {}
            assistant_message = f"CadPilot failed: `{type(exc).__name__}: {exc}`"
            st.error(assistant_message)
            status.update(label="CadPilot failed", state="error", expanded=True)

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_message}
    )
    st.session_state.latest_result = result
    next_step_path = _find_step_path(result)
    if next_step_path is not None:
        st.session_state.latest_step_path = next_step_path


def _render_viewer_panel() -> None:
    st.subheader("CAD Viewer")
    latest_step_path = st.session_state.latest_step_path

    if latest_step_path:
        step_path = Path(latest_step_path)
        st.caption(step_path.name)
        render_step_viewer(step_path, height=680)
        with step_path.open("rb") as step_file:
            st.download_button(
                "Download STEP",
                data=step_file,
                file_name=step_path.name,
                mime="application/octet-stream",
                use_container_width=True,
            )
        return

    st.info("Generate a model from the chat panel and the latest STEP file will appear here.")


def main() -> None:
    st.set_page_config(
        page_title="CadPilot v3 Demo",
        page_icon="🧭",
        layout="wide",
    )
    _init_session_state()

    st.title("CadPilot v3")
    st.caption("Natural-language CAD generation with live validation and STEP preview.")

    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        _render_chat_panel()
    with right:
        _render_viewer_panel()


if __name__ == "__main__":
    main()
