#!/usr/bin/env python3
"""Branch-close the cumulative14 next mixed-degree Serre orbit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_phenomenology_guided_q1_radius4_tenth_orbit_branch_closure as base

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

SOURCE_REPORT = REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json"
SIXTEENTH_ORBIT = (0, 0, -2, 0, -2, 1, 1)
SIXTEENTH_ORBIT_DUAL = tuple(-value for value in SIXTEENTH_ORBIT)
TARGET_CANDIDATE = "batch2:window4_radius4_adjacency_filtered_0_known_line_resolved"


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def configure_base() -> None:
    base.SOURCE_REPORT = SOURCE_REPORT
    base.TENTH_ORBIT = SIXTEENTH_ORBIT
    base.TENTH_ORBIT_DUAL = SIXTEENTH_ORBIT_DUAL
    base.TARGET_CANDIDATE = TARGET_CANDIDATE
    base.actual_for_line = actual_for_line


def actual_for_line(
    line: list[int],
    cohomology: list[int],
    *,
    h1_trace: int,
    h2_trace: int,
) -> dict[str, Any]:
    tup = tuple(line)
    if tup == SIXTEENTH_ORBIT:
        if cohomology != [0, 2, 1, 0]:
            raise ValueError((line, cohomology))
        return {"H1": base.rep(2, h2_trace), "H2": base.rep(1, h1_trace)}
    if tup == SIXTEENTH_ORBIT_DUAL:
        if cohomology != [0, 1, 2, 0]:
            raise ValueError((line, cohomology))
        return {"H1": base.rep(1, h1_trace), "H2": base.rep(2, h2_trace)}
    raise ValueError(line)


def build_report() -> dict[str, Any]:
    configure_base()
    cumulative14 = base.load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative14_adjusted_frontier.json"
    )
    cumulative14_verification = base.load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative14_adjusted_frontier_verification.json"
    )
    report = base.build_report()
    branch_records = report["branch_records"]
    categories = report["summary"]["categories"]
    statuses = report["summary"]["statuses"]
    next_orbit = cumulative14["summary"]["next_probe_orbit"]
    gates = {
        "cumulative14_frontier_verified": gate(
            cumulative14["all_gates_pass"]
            and cumulative14_verification["all_gates_pass"]
            and next_orbit["serre_orbit_representative"] == list(SIXTEENTH_ORBIT),
            str(REPORTS / "phenomenology_guided_q1_radius4_cumulative14_adjusted_frontier.json"),
            "sixteenth-orbit branch closure targets the verified cumulative14 bottleneck",
        ),
        "target_candidate_loaded": gate(
            report["tenth_serre_orbit"]["target_candidate"] == TARGET_CANDIDATE,
            str(SOURCE_REPORT),
            "the single candidate touched by the cumulative14 next orbit is loaded",
        ),
        "all_trace_branches_tested": gate(
            report["summary"]["branch_count"] == len(branch_records) == 6
            and report["summary"]["filled_blocks"] == 12
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_branches"] == 6,
            "sixteenth Serre orbit branch records",
            "one candidate times six H1/H2 trace branches are fully certified",
        ),
        "classification_counts_match": gate(
            categories == {"phenomenologically obstructed": 6}
            and statuses
            == {
                "negative_control_doublet_triplet_obstruction": 1,
                "rejected_spectrum_signature_not_q1_three_family": 5,
            },
            "sixteenth Serre orbit branch classifications",
            "all sixteenth-orbit branches are rejected by the q=1/phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == 0,
            "sixteenth Serre orbit branch classifications",
            "no branch of the cumulative14 next orbit produces a viable candidate",
        ),
    }
    return {
        "scope": "bounded branch closure for the cumulative14 next radius-4 Serre orbit",
        "status": "no_viable_candidate_found_in_sixteenth_serre_orbit_branches",
        "sixteenth_serre_orbit": {
            "representative": list(SIXTEENTH_ORBIT),
            "dual": list(SIXTEENTH_ORBIT_DUAL),
            "target_candidate": TARGET_CANDIDATE,
        },
        "summary": report["summary"],
        "branch_records": branch_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Sixteenth Serre Orbit Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- orbit representative: `{report['sixteenth_serre_orbit']['representative']}`",
        f"- dual: `{report['sixteenth_serre_orbit']['dual']}`",
        f"- target candidate: `{report['sixteenth_serre_orbit']['target_candidate']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        res = record["tenth_serre_orbit_branch_resolution"]
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
                "The cumulative14 bottleneck has six mixed-degree trace branches. "
                "Every branch is character-certified and nonviable: five lose the "
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
            REPORTS / "phenomenology_guided_q1_radius4_sixteenth_orbit_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_sixteenth_orbit_branch_closure.md"
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
