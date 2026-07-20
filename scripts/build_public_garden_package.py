from __future__ import annotations

from pathlib import Path

import build_public_experiment_package as exporter


ROOT = Path(__file__).resolve().parents[1]
exporter.OUTPUT = ROOT / "experiments" / "public" / "garden_workflow_v1"
exporter.FLOW_RUN = ROOT / "runs" / "agent_garden_demo_v1"
exporter.SELECTED_RUN = exporter.FLOW_RUN
exporter.PACKAGE_NAME = "SkinSmith public garden workflow evidence"


if __name__ == "__main__":
    exporter.main()
