#!/usr/bin/env python3
"""Verify the cumulative12 fourteenth two-orbit cluster branch closure report."""

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


def has_required_sections(record: dict[str, Any]) -> bool:
    return {
        "spectrum_certificate",
        "character_certificate",
        "mass_operator_table",
        "proton_decay_operator_table",
        "classification",
    }.issubset(record)


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius4_fourteenth_cluster_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_fourteenth_cluster_branch_closure.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["branch_records"]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side two-orbit cluster closure gates passed",
        ),
        "target_cluster_matches_cumulative12_frontier": gate(
            report["target_candidate"]
            == "batch1:window3_radius4_adjacency_filtered_3_known_line_resolved"
            and [row["representative"] for row in report["cluster_serre_orbits"]]
            == [
                [-1, 1, 0, -1, 1, 0, -1],
                [0, 0, -1, 0, 2, 0, -1],
            ],
            str(path),
            "branch closure targets the full two-orbit cumulative12 candidate cluster",
        ),
        "all_cluster_branches_certified": gate(
            report["summary"]["candidate_count"] == 1
            and report["summary"]["branch_count"] == len(records) == 9
            and report["summary"]["filled_blocks"] == 36
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_branches"] == 9
            and all(
                record["character_certificate"]["character_certified"]
                and has_required_sections(record)
                and record["fourteenth_cluster_branch_resolution"]["filled_block_count"] == 4
                and record["fourteenth_cluster_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 0
                for record in records
            ),
            str(path),
            "all nine trace completions have spectrum/character/operator certificates",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 9}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 3,
                "rejected_spectrum_signature_not_q1_three_family": 6,
            },
            str(path),
            "all cluster branches are nonviable with exact obstruction counts",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0
            and report["status"] == "no_viable_candidate_found_in_fourteenth_cluster_branches",
            str(path),
            "no two-orbit completion produces a viable candidate",
        ),
        "markdown_exposes_closure": gate(
            "branch_count: `9`" in md_text
            and "remaining_unresolved_blocks: `0`" in md_text
            and "dangerous_10_5bar_5bar_operator_allowed" in md_text
            and "six branches lose the q=1 signature" in md_text,
            str(md_path),
            "markdown exposes the full cluster closure and exact obstruction split",
        ),
    }
    return {
        "scope": "verification for cumulative12 fourteenth two-orbit cluster branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_fourteenth_cluster_branch_closure_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
