from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit.components.v1 as components


@lru_cache(maxsize=1)
def _viewer_bundle() -> str:
    bundle_path = Path(__file__).parent / "step_viewer" / "assets" / "o3dv.min.js"
    return bundle_path.read_text(encoding="utf-8")


def render_step_viewer(step_path: str | Path, *, height: int = 640) -> None:
    path = Path(step_path)
    step_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    safe_filename = html.escape(path.name)

    document = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          html, body {{
            margin: 0;
            width: 100%;
            height: 100%;
            background: #f7f7f8;
            font-family: Arial, sans-serif;
          }}
          #viewer {{
            position: absolute;
            inset: 0;
          }}
          #status {{
            position: absolute;
            top: 16px;
            left: 16px;
            z-index: 10;
            padding: 8px 12px;
            border-radius: 999px;
            color: #222;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
            font-size: 13px;
          }}
        </style>
      </head>
      <body>
        <div id="viewer"></div>
        <div id="status">Loading {safe_filename}…</div>
        <script>{_viewer_bundle()}</script>
        <script>
          const viewerElement = document.getElementById("viewer");
          const statusElement = document.getElementById("status");
          const stepBase64 = "{step_b64}";
          const fileName = "{safe_filename}";

          function base64ToBytes(value) {{
            const binary = atob(value);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i += 1) {{
              bytes[i] = binary.charCodeAt(i);
            }}
            return bytes;
          }}

          const viewer = new OV.EmbeddedViewer(viewerElement, {{
            backgroundColor: new OV.RGBAColor(247, 247, 248, 255),
            defaultColor: new OV.RGBColor(190, 198, 210),
            edgeSettings: new OV.EdgeSettings(true, new OV.RGBColor(38, 44, 56), 1),
            onModelLoaded: () => {{
              statusElement.textContent = fileName;
            }},
            onModelLoadFailed: () => {{
              statusElement.textContent = "Could not load STEP model.";
            }},
          }});

          const bytes = base64ToBytes(stepBase64);
          const file = new File([bytes], fileName, {{
            type: "application/octet-stream",
          }});
          viewer.LoadModelFromFileList([file]);

          window.addEventListener("resize", () => viewer.Resize());
        </script>
      </body>
    </html>
    """
    components.html(document, height=height, scrolling=False)
