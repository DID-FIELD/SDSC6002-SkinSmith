from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.replay import discover_replay_runs, load_replay_run  # noqa: E402


DEFAULT_RUN = PROJECT_ROOT / "runs" / "agent_dragon_multicandidate_v1"
WEAPONS = {
    "AK-47 - full end-to-end": {
        "asset_id": "cs2_ak47_new_geometry",
        "enabled": True,
        "status": "Full Agent, OBJ/UV, three-view, and 2048 PNG/TGA workflow accepted.",
    },
    "M4A4 - transfer evidence": {
        "asset_id": "cs2_m4a4_new_geometry",
        "enabled": False,
        "status": (
            "GameAssetAdapter transfer evidence is complete; formal client execution "
            "is not yet registered."
        ),
    },
}


def _score(value: Any) -> str:
    return f"{float(value):.4f}" if value is not None else "-"


def _image(path: Path, caption: str) -> None:
    if path.is_file():
        st.image(str(path), caption=caption, width="stretch")
    else:
        st.warning(f"Missing image: {path.name}")


def _download(label: str, path: Path, mime: str) -> None:
    if path.is_file():
        st.download_button(
            label,
            data=path.read_bytes(),
            file_name=path.name,
            mime=mime,
            width="stretch",
        )


def _run_agent(arguments: list[str]) -> bool:
    command = [
        str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"),
        str(PROJECT_ROOT / "scripts" / "run_skinsmith_agent.py"),
        *arguments,
    ]
    with st.status("Agent is working...", expanded=True) as status:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.stdout:
            st.code(completed.stdout[-12000:], language="json")
        if completed.stderr:
            st.code(completed.stderr[-12000:], language="text")
        if completed.returncode:
            status.update(label="Agent execution failed", state="error")
            return False
        status.update(label="Agent stage completed", state="complete")
        return True


def _render_direction(direction: Mapping[str, Any], selected: bool) -> None:
    title = str(direction.get("title", direction.get("direction_id", "Direction")))
    suffix = " - selected" if selected else ""
    with st.container(border=True):
        st.subheader(f"{title}{suffix}")
        st.caption(str(direction.get("direction_id", "")))
        st.write(direction.get("concept", ""))
        palette = direction.get("palette", [])
        if palette:
            st.markdown(
                " ".join(
                    f"<span style='display:inline-block;width:24px;height:24px;"
                    f"border-radius:50%;background:{color};border:1px solid #777' "
                    f"title='{color}'></span>"
                    for color in palette
                ),
                unsafe_allow_html=True,
            )
        st.caption(direction.get("recommendation_reason", ""))


def _render_artwork(run, artwork: Mapping[str, Any]) -> None:
    candidate_id = str(artwork.get("candidate_id", "candidate"))
    selected = candidate_id == run.selected_artwork_id
    metrics = artwork.get("metrics", {})
    with st.container(border=True):
        st.subheader(
            f"{artwork.get('title', candidate_id)}"
            f"{' - human selected' if selected else ''}"
        )
        st.caption(f"{candidate_id} - {artwork.get('variation', '')}")
        source = run.path(str(artwork["source_path"]))
        previews = [run.path(path) for path in artwork.get("preview_paths", [])]
        columns = st.columns(4)
        with columns[0]:
            _image(source, "Original master artwork")
        labels = ("Weapon left view", "Weapon right view", "Weapon top view")
        for column, path, label in zip(columns[1:], previews[:3], labels):
            with column:
                _image(path, label)
        seam = metrics.get("asset_seam", {})
        m1, m2, m3 = st.columns(3)
        m1.metric("Asset seam", _score(seam.get("total_error")))
        m2.metric("Multi-view", _score(metrics.get("multi_view_score")))
        m3.metric("Preview total", _score(metrics.get("total_score")))
        if selected:
            st.success(
                "This candidate was selected by a human. Automated metrics are "
                "comparison aids only."
            )


def _render_readability(readability: Mapping[str, Any] | None) -> None:
    st.header("Mapped-element readability recommendation")
    if not readability:
        st.info("This run has no mapped-element readability report.")
        return
    st.info(
        "recommendation_only: these scores explain and recommend; they never "
        "override human selection."
    )
    columns = st.columns(5)
    columns[0].metric(
        "Source fulfillment", _score(readability.get("source_design_fulfillment"))
    )
    columns[1].metric("Left", _score(readability.get("left_readability")))
    columns[2].metric("Right", _score(readability.get("right_readability")))
    columns[3].metric("Top", _score(readability.get("top_readability")))
    columns[4].metric(
        "Recommendation", _score(readability.get("recommendation_score"))
    )
    st.progress(float(readability.get("visible_element_ratio", 0.0)))
    st.caption(
        f"Elements above the visibility threshold: "
        f"{readability.get('visible_element_count', 0)}/"
        f"{readability.get('element_count', 0)}. The left view has the highest weight."
    )
    rows = []
    for record in readability.get("elements", []):
        element = record.get("element", {})
        match = record.get("match", {})
        rows.append(
            {
                "Element": element.get("label") or element.get("description"),
                "Source": match.get("source_score"),
                "Left": match.get("left_score"),
                "Right": match.get("right_score"),
                "Top": match.get("top_score"),
                "Best view": match.get("best_view"),
                "Visible": bool(record.get("visible_in_any_view")),
                "Explanation": match.get("mapped_evidence"),
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)


def main() -> None:
    st.set_page_config(page_title="SkinSmith", layout="wide")
    st.title("SkinSmith")
    st.caption(
        "Constraint-aware game weapon skin generation Agent and preserved-run client"
    )

    runs = discover_replay_runs(PROJECT_ROOT)
    choices = {str(path.relative_to(PROJECT_ROOT)): path for path in runs}
    default_key = str(DEFAULT_RUN.relative_to(PROJECT_ROOT))
    with st.sidebar:
        st.header("Run")
        mode = st.radio("Mode", ("Replay", "New task"), horizontal=True)
        selected_key = st.selectbox(
            "Preserved run",
            tuple(choices),
            index=tuple(choices).index(default_key) if default_key in choices else 0,
            disabled=mode != "Replay",
        )
        st.caption(
            "Replay does not call a generation model or modify preserved evidence."
        )
        st.divider()
        st.header("New task")
        weapon_label = st.selectbox(
            "Weapon",
            tuple(WEAPONS),
            disabled=mode != "New task",
        )
        weapon = WEAPONS[weapon_label]
        st.caption(weapon["status"])
        brief = st.text_input(
            "Theme keyword",
            disabled=mode != "New task",
            placeholder="For example: dragon",
        )
        style_family = st.selectbox(
            "Style family",
            ("Auto", "Traditional Art", "Material", "Sci-Fi"),
            disabled=mode != "New task",
        )
        if st.button(
            "Expand theme world",
            disabled=(
                mode != "New task"
                or not brief.strip()
                or not bool(weapon["enabled"])
            ),
            width="stretch",
        ):
            output = (
                PROJECT_ROOT
                / "runs"
                / f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            arguments = [
                brief.strip(),
                "--asset-id",
                str(weapon["asset_id"]),
                "--provider",
                "gemini",
                "--output",
                str(output),
            ]
            if style_family != "Auto":
                arguments.extend(["--style-family", style_family])
            if _run_agent(arguments):
                st.session_state["active_run"] = str(output)
                st.rerun()

    active_run = st.session_state.get("active_run")
    if active_run:
        run_path = Path(active_run)
    elif choices:
        run_path = choices[selected_key]
    else:
        st.error("No replayable Agent run was found.")
        return
    run = load_replay_run(PROJECT_ROOT, run_path)
    result = run.result
    if run.phase == "failed":
        st.error(f"Agent execution failed: {result.get('stop_reason') or 'unknown error'}")

    top = st.columns(5)
    top[0].metric("Phase", run.phase)
    top[1].metric("Status", result.get("status", "-"))
    top[2].metric("Direction", run.selected_direction_id or "Awaiting selection")
    top[3].metric("Artwork", run.selected_artwork_id or "Awaiting selection")
    top[4].metric("Selected route", result.get("decision", {}).get("selected_route", "-"))

    request = result.get("request", {})
    st.header("Design task")
    st.write(request.get("brief", ""))
    st.caption(
        f"Asset: {request.get('asset_id', '-')} - "
        f"Style: {request.get('style_family') or 'Auto'}"
    )

    theme = result.get("theme_expansion")
    if theme:
        st.header("Theme-world expansion")
        st.caption(
            "Checkpoint 1 - The Agent expands a short keyword into related visual "
            "elements. Direction planning starts only after confirmation."
        )
        with st.container(border=True):
            st.subheader(str(theme.get("display_name", theme.get("theme_id", "Theme"))))
            st.write(theme.get("concept", ""))
            st.caption(theme.get("narrative", ""))
            palette = theme.get("palette", [])
            if palette:
                st.markdown(
                    " ".join(
                        f"<span style='display:inline-block;width:24px;height:24px;"
                        f"border-radius:50%;background:{color};border:1px solid #777' "
                        f"title='{color}'></span>"
                        for color in palette
                    ),
                    unsafe_allow_html=True,
                )
            st.dataframe(
                [
                    {
                        "Element": item.get("label"),
                        "Role": item.get("semantic_role"),
                        "Generation description": item.get("description"),
                    }
                    for item in theme.get("elements", [])
                ],
                width="stretch",
                hide_index=True,
            )
            with st.expander("More related elements"):
                st.write(" - ".join(theme.get("world_elements", [])))
            st.info(
                "This is controlled semantic theme expansion, not unrestricted web "
                "search. The Agent generates textual art directions only after confirmation."
            )
        if run.phase == "awaiting_theme":
            if st.button("Confirm theme and generate art directions", type="primary"):
                if _run_agent(
                    [
                        "--resume",
                        str(run.run_dir),
                        "--confirm-theme",
                    ]
                ):
                    st.session_state["active_run"] = str(run.run_dir)
                    st.rerun()

    st.header("Textual art directions")
    st.caption("Checkpoint 2 - Select one of three or four textual art directions.")
    directions = result.get("directions", [])
    for row_start in range(0, len(directions), 2):
        columns = st.columns(2)
        for column, direction in zip(columns, directions[row_start : row_start + 2]):
            with column:
                _render_direction(
                    direction,
                    direction.get("direction_id") == run.selected_direction_id,
                )

    if run.phase == "awaiting_direction":
        st.subheader("Select a direction and generate mapped candidates")
        direction_ids = [str(item["direction_id"]) for item in directions]
        chosen_direction = st.selectbox(
            "Direction",
            direction_ids,
            format_func=lambda value: next(
                (
                    f"{item.get('title')} - {value}"
                    for item in directions
                    if item.get("direction_id") == value
                ),
                value,
            ),
        )
        st.warning(
            "The next stage calls the image model, generates three or four master "
            "artworks, and maps each one to low-cost weapon previews."
        )
        if st.button("Lock direction and generate candidates", type="primary"):
            if _run_agent(
                [
                    "--resume",
                    str(run.run_dir),
                    "--execute",
                    "--direction",
                    chosen_direction,
                    "--image-provider",
                    "gemini",
                    "--bake-size",
                    "512",
                ]
            ):
                st.session_state["active_run"] = str(run.run_dir)
                st.rerun()

    st.header("Source + weapon left/right/top candidate cards")
    st.caption(
        "Checkpoint 3 - The four images form one indivisible candidate. The model "
        "may recommend, but the final selection is human."
    )
    for artwork in result.get("artwork_candidates", []):
        _render_artwork(run, artwork)

    if run.phase == "awaiting_artwork":
        st.subheader("Human selection of the final artwork")
        artwork_ids = [
            str(item["candidate_id"]) for item in result.get("artwork_candidates", [])
        ]
        chosen_artwork = st.selectbox("Artwork", artwork_ids)
        st.warning(
            "The selected source will be reused exactly for the formal 2048 UV bake, "
            "bounded Route C feedback, and TGA export."
        )
        if st.button("Lock artwork and run formal export", type="primary"):
            if _run_agent(
                [
                    "--resume",
                    str(run.run_dir),
                    "--execute",
                    "--artwork",
                    chosen_artwork,
                    "--image-provider",
                    "gemini",
                    "--bake-size",
                    "2048",
                    "--export-tga",
                ]
            ):
                st.session_state["active_run"] = str(run.run_dir)
                st.rerun()

    _render_readability(run.readability)

    st.header("Execution and recovery status")
    usage = run.usage
    budget = run.budget
    status_columns = st.columns(3)
    status_columns[0].metric(
        "Image calls",
        f"{usage.get('image_calls_used', 0)}/{budget.get('max_image_calls', '-')}",
    )
    status_columns[1].metric(
        "Role retries",
        f"{usage.get('role_retries_used', 0)}/{budget.get('max_role_retries', '-')}",
    )
    status_columns[2].metric(
        "Refinement rounds",
        f"{usage.get('refinement_rounds_used', 0)}/"
        f"{budget.get('max_refinement_rounds', '-')}",
    )
    route_c = result.get("decision", {}).get("route_c", {})
    if route_c:
        st.warning(
            f"Route C {'accepted' if route_c.get('accepted') else 'rolled back'}: "
            f"{route_c.get('reason', '')}"
        )
    with st.expander("Event timeline"):
        st.dataframe(
            [
                {
                    "#": event.get("sequence"),
                    "Time": event.get("timestamp"),
                    "Phase": event.get("phase"),
                    "Type": event.get("event_type"),
                    "Summary": event.get("summary"),
                    "Tool": event.get("tool"),
                }
                for event in result.get("events", [])
            ],
            width="stretch",
            hide_index=True,
        )

    st.header("Final export")
    artifacts = result.get("artifacts", {})
    previews = [run.path(path) for path in artifacts.get("selected_previews", [])]
    if len(previews) >= 4:
        _image(previews[3], "Final Route B multi-view")
    if artifacts.get("selected_texture_png") and artifacts.get(
        "selected_texture_tga"
    ):
        download_columns = st.columns(2)
        with download_columns[0]:
            _download(
                "Download final PNG",
                run.path(artifacts["selected_texture_png"]),
                "image/png",
            )
        with download_columns[1]:
            _download(
                "Download final TGA",
                run.path(artifacts["selected_texture_tga"]),
                "application/octet-stream",
            )
    else:
        st.caption("PNG and TGA downloads will appear here after completion.")


if __name__ == "__main__":
    main()
