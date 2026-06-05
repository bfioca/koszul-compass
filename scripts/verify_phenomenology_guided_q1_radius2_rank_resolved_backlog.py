#!/usr/bin/env python3
"""Verify rank-resolved high-priority backlog report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.md"
    higher_path = REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.json"
    projected_path = REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"
    report = load_json(path)
    higher = load_json(higher_path)
    projected = load_json(projected_path)
    md_text = md_path.read_text(encoding="utf-8")
    filtered = report["filtered_candidate_records"]
    certified_q1 = [
        record
        for record in filtered
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
        and record["character_certificate"]["character_certified"]
    ]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "rank-resolved backlog builder gates pass",
        ),
        "imports_verified_higher_probe": gate(
            higher["all_gates_pass"]
            and higher["status"] == "representative_block_resolves_to_desired_q1_character",
            f"{path}, {higher_path}",
            "rank-resolved backlog imports the verified higher-rank representative result",
        ),
        "imports_verified_projected_probe": gate(
            projected["all_gates_pass"]
            and projected["status"] == "projected_family_resolves_to_desired_q1_character",
            f"{path}, {projected_path}",
            "rank-resolved backlog imports the projected higher-rank family result",
        ),
        "summary_counts_match": gate(
            report["summary"]["high_priority_records"] == 4
            and report["summary"]["filled_blocks"] == 8
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_records"] == 4
            and report["summary"]["desired_q1_records"] == 4
            and report["summary"]["viable_count"] == 0,
            str(path),
            "rank resolution closes the high-priority residual frontier with four q=1 records",
        ),
        "certified_q1_records_have_required_tables": gate(
            len(certified_q1) == 4
            and all(
                record["mass_operator_table"] is not None
                and record["proton_decay_operator_table"] is not None
                and record["classification"]["status"]
                == "negative_control_doublet_triplet_obstruction"
                for record in certified_q1
            ),
            str(path),
            "newly certified q=1 records include mass/proton tables and fail the negative-control filter",
        ),
        "no_high_priority_unresolved_records_remain": gate(
            all(
                record["rank_resolution"]["unresolved_block_count"] == 0
                for record in filtered
            ),
            str(path),
            "all high-priority rank-resolved records have complete character certificates",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_after_conservative_rank_resolution`" in md_text
            and "desired_q1_records: `4`" in md_text
            and "viable_count: `0`" in md_text
            and "remaining_unresolved_blocks: `0`" in md_text,
            str(md_path),
            "markdown exposes rank-resolution counts and filtered classifications",
        ),
    }
    return {
        "scope": "verification for rank-resolved high-priority backlog report",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
