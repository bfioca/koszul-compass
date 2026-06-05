#!/usr/bin/env python3
"""Summarize the current selected radius-4 frontier after known-line resolution."""

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


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json")
    resolved = load_json(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json")
    original_obstructed = aggregate["aggregate_categories"]["phenomenologically obstructed"]
    newly_obstructed = resolved["summary"]["categories"]["phenomenologically obstructed"]
    remaining_unresolved = resolved["summary"]["categories"]["unresolved"]
    statuses = dict(aggregate["aggregate_statuses"])
    statuses["missing_character_or_charge_level_data"] -= aggregate["aggregate_categories"]["unresolved"]
    if statuses["missing_character_or_charge_level_data"] == 0:
        statuses.pop("missing_character_or_charge_level_data")
    for status, count in resolved["summary"]["statuses"].items():
        statuses[status] = statuses.get(status, 0) + count

    gates = {
        "imports_selected_radius4_aggregate": gate(
            aggregate["all_gates_pass"]
            and aggregate["aggregate_categories"]
            == {"phenomenologically obstructed": 28, "unresolved": 21},
            str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json"),
            "current frontier starts from the verified selected radius-4 aggregate",
        ),
        "imports_known_line_resolution": gate(
            resolved["all_gates_pass"]
            and resolved["summary"]["categories"]
            == {"phenomenologically obstructed": 7, "unresolved": 14},
            str(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"),
            "current frontier imports the verified known-line resolution pass",
        ),
        "counts_are_accounted": gate(
            original_obstructed + newly_obstructed + remaining_unresolved
            == aggregate["aggregate_totals"]["raw_q1_spectrum_survivors"]
            == 49,
            "selected radius-4 current frontier accounting",
            "all selected radius-4 raw q=1 survivors are obstructed or unresolved",
        ),
        "no_viable_candidate_found": gate(
            aggregate["viable_count"] == 0 and resolved["summary"]["viable_count"] == 0,
            "selected radius-4 current frontier classifications",
            "no viable candidate appears after known-line resolution",
        ),
    }
    return {
        "scope": "current selected radius-4 q=1 frontier after known-line resolution",
        "status": "no_viable_candidate_found_selected_radius4_frontier_partly_unresolved",
        "summary": {
            "selected_frontier_size": aggregate["coverage"]["frontier_size"],
            "raw_q1_spectrum_survivors": aggregate["aggregate_totals"][
                "raw_q1_spectrum_survivors"
            ],
            "character_certified_before_resolution": aggregate["aggregate_totals"][
                "character_certified_q1_survivors"
            ],
            "known_line_newly_character_certified": resolved["summary"][
                "character_certified_records"
            ],
            "current_obstructed_count": original_obstructed + newly_obstructed,
            "current_unresolved_count": remaining_unresolved,
            "viable_count": 0,
            "filled_known_line_blocks": resolved["summary"]["filled_blocks"],
            "remaining_unresolved_blocks": resolved["summary"][
                "remaining_unresolved_blocks"
            ],
            "current_statuses": dict(sorted(statuses.items())),
        },
        "remaining_unresolved_records": [
            {
                "label": record["label"],
                "source": f"{record['source_window']}/{record['source_filtered_label']}",
                "status": record["classification"]["status"],
                "vectorlike_prediction": record["spectrum_certificate"][
                    "vectorlike_prediction"
                ],
                "remaining_blocks": record["radius4_known_line_resolution"][
                    "unresolved_block_count"
                ],
            }
            for record in resolved["filtered_candidate_records"]
            if record["classification"]["category"] == "unresolved"
        ],
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Current Selected Radius-4 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Remaining Unresolved", ""])
    for record in report["remaining_unresolved_records"]:
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source']}`: "
            f"`{record['status']}`; remaining blocks `{record['remaining_blocks']}`; "
            f"prediction `{record['vectorlike_prediction']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The selected radius-4 frontier remains viable-free after importing "
                "all matching verified known-line character probes. The remaining "
                "work is character resolution for the 16 records whose missing "
                "blocks are not fully covered by the existing probe library."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_current_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_current_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
