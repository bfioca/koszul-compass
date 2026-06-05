#!/usr/bin/env python3
"""Branch-close the cumulative13 next mixed-degree Serre orbit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_phenomenology_guided_q1_radius4_thirteenth_orbit_branch_closure as base

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

SOURCE_REPORT = REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"
FIFTEENTH_ORBIT = (-1, 2, 0, 0, 2, -1, 0)
FIFTEENTH_ORBIT_DUAL = tuple(-value for value in FIFTEENTH_ORBIT)
TARGET_CANDIDATE = "batch1:window3_radius4_adjacency_filtered_5_known_line_resolved"


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def configure_base() -> None:
    base.SOURCE_REPORT = SOURCE_REPORT
    base.THIRTEENTH_ORBIT = FIFTEENTH_ORBIT
    base.THIRTEENTH_ORBIT_DUAL = FIFTEENTH_ORBIT_DUAL
    base.TARGET_CANDIDATE = TARGET_CANDIDATE
    base.load_target_record = load_target_record


def load_target_record() -> dict[str, Any]:
    report = base.load_json(SOURCE_REPORT)
    for resolved, filtered in zip(report["resolved_records"], report["filtered_candidate_records"]):
        if f"batch1:{filtered['label']}" == TARGET_CANDIDATE:
            return {"resolved": resolved, "filtered": filtered}
    raise RuntimeError(f"target candidate not found: {TARGET_CANDIDATE}")


def build_report() -> dict[str, Any]:
    configure_base()
    cumulative13 = base.load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative13_adjusted_frontier.json"
    )
    cumulative13_verification = base.load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative13_adjusted_frontier_verification.json"
    )
    report = base.build_report()
    branch_records = report["branch_records"]
    for record in branch_records:
        record["source_batch"] = "batch1"
    categories = report["summary"]["categories"]
    statuses = report["summary"]["statuses"]
    next_orbit = cumulative13["summary"]["next_probe_orbit"]
    gates = {
        "cumulative13_frontier_verified": gate(
            cumulative13["all_gates_pass"]
            and cumulative13_verification["all_gates_pass"]
            and next_orbit["serre_orbit_representative"] == list(FIFTEENTH_ORBIT),
            str(REPORTS / "phenomenology_guided_q1_radius4_cumulative13_adjusted_frontier.json"),
            "fifteenth-orbit branch closure targets the verified cumulative13 bottleneck",
        ),
        "target_candidate_loaded": gate(
            report["thirteenth_serre_orbit"]["target_candidate"] == TARGET_CANDIDATE,
            str(SOURCE_REPORT),
            "the single candidate touched by the cumulative13 next orbit is loaded",
        ),
        "all_trace_branches_tested": gate(
            report["summary"]["branch_count"] == len(branch_records) == 9
            and report["summary"]["filled_blocks"] == 18
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_branches"] == 9,
            "fifteenth Serre orbit branch records",
            "one candidate times nine H1/H2 trace branches are fully certified",
        ),
        "classification_counts_match": gate(
            categories == {"phenomenologically obstructed": 9}
            and statuses
            == {
                "negative_control_doublet_triplet_obstruction": 1,
                "rejected_spectrum_signature_not_q1_three_family": 8,
            },
            "fifteenth Serre orbit branch classifications",
            "all fifteenth-orbit branches are rejected by the q=1/phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == 0,
            "fifteenth Serre orbit branch classifications",
            "no branch of the cumulative13 next orbit produces a viable candidate",
        ),
    }
    return {
        "scope": "bounded branch closure for the cumulative13 next radius-4 Serre orbit",
        "status": "no_viable_candidate_found_in_fifteenth_serre_orbit_branches",
        "fifteenth_serre_orbit": {
            "representative": list(FIFTEENTH_ORBIT),
            "dual": list(FIFTEENTH_ORBIT_DUAL),
            "target_candidate": TARGET_CANDIDATE,
        },
        "summary": report["summary"],
        "branch_records": branch_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Fifteenth Serre Orbit Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- orbit representative: `{report['fifteenth_serre_orbit']['representative']}`",
        f"- dual: `{report['fifteenth_serre_orbit']['dual']}`",
        f"- target candidate: `{report['fifteenth_serre_orbit']['target_candidate']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        res = record["thirteenth_serre_orbit_branch_resolution"]
        lines.append(
            "- "
            f"`{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"filled `{res['filled_block_count']}`; "
            f"remaining `{res['remaining_unresolved_block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The cumulative13 bottleneck has nine mixed-degree trace branches. "
                "Every branch is character-certified and nonviable: eight lose the "
                "q=1 signature and one reproduces the negative-control "
                "doublet-triplet obstruction."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_fifteenth_orbit_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_fifteenth_orbit_branch_closure.md"
        ),
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
