#!/usr/bin/env python3
"""Verify the radius-3 medium three-family E2 probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side medium-three-family E2 gates passed",
        ),
        "target_record_recorded": gate(
            report["target_record"]
            == {
                "window": "window3",
                "label": "radius3_adjacency_filtered_2",
                "source_radius2_record": "window4/radius2_pilot_filtered_5",
            },
            str(path),
            "probe records the intended medium-priority three-family record",
        ),
        "four_nonregular_blocks_resolved": gate(
            len(report["records"]) == 4
            and all(any(rep["regular_multiplicity"] is None for rep in record["actual"].values()) for record in report["records"]),
            str(path),
            "all four blocks are resolved and each contains nonregular character content",
        ),
        "markdown_exposes_summary": gate(
            "Status: `medium_three_family_e2_characters_resolved_nonregular`" in md_text
            and "target record" in md_text,
            str(md_path),
            "markdown exposes medium-three-family result",
        ),
    }
    return {
        "scope": "verification for medium-priority radius-3 three-family E2 probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
