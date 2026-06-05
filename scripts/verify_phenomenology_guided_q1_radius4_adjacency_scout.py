#!/usr/bin/env python3
"""Verify the bounded radius-4 adjacency scout."""

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


def verify(*, report_path: Path, md_path: Path) -> dict[str, Any]:
    path = report_path
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["filtered_candidate_records"]
    raw_records = report["raw_q1_records"]
    certified_records = [
        record
        for record in records
        if record["character_certificate"]["character_certified"]
    ]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    adjacency_total = report["adjacency_counters"]["within_charge_bound"]
    frontier_start = report["search_parameters"]["frontier_start"]
    screened = report["screening_counters"]["frontier_records_screened"]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side scout gates passed",
        ),
        "imports_radius3_filter_frontier": gate(
            report["search_parameters"]["source"]
            == "phenomenology_guided_q1_radius3_obstruction_filter_certificate.json"
            and report["adjacency_counters"]["source_radius3_records"] > 0,
            str(path),
            "radius-4 scout expands selected records from the radius-3 obstruction filter",
        ),
        "adjacency_edge_count": gate(
            report["adjacency_counters"]["primitive_count"] == 560
            and report["adjacency_counters"]["raw_edges"]
            == report["adjacency_counters"]["source_radius3_records"] * 560
            and report["adjacency_counters"]["unique_candidates"] > 0,
            str(path),
            "scout generated one primitive adjacency edge from each selected radius-3 source",
        ),
        "bounded_screening_is_explicit": gate(
            0 <= frontier_start < adjacency_total
            and screened
            == min(
                report["search_parameters"]["max_frontier_to_screen"],
                adjacency_total - frontier_start,
            )
            and report["screening_counters"]["frontier_records_before_window"]
            == frontier_start
            and report["screening_counters"]["frontier_records_after_window"]
            == adjacency_total - frontier_start - screened,
            str(path),
            "report records the bounded screened and unscreened frontier counts",
        ),
        "raw_q1_certification_accounting": gate(
            report["screening_counters"]["raw_q1_certification_attempts"]
            == len(records)
            == min(
                len(raw_records),
                report["search_parameters"]["max_raw_q1_to_certify"],
            ),
            str(path),
            "raw q=1 certification attempts match emitted filtered records",
        ),
        "required_sections_exist": gate(
            all(has_required_sections(record) for record in records)
            and all(
                record["mass_operator_table"] is not None
                and record["proton_decay_operator_table"] is not None
                for record in certified_records
            ),
            str(path),
            "every filtered record has required sections and certified records have mass/proton tables",
        ),
        "viable_count_matches_records": gate(
            report["summary"]["viable_count"] == len(viable),
            str(path),
            "summary viable count matches candidate classifications",
        ),
        "markdown_exposes_scope": gate(
            "Status:" in md_text
            and "bounded one-move expansion window" in md_text
            and "viable count" in md_text,
            str(md_path),
            "markdown exposes bounded scout scope and summary",
        ),
    }
    return {
        "scope": "verification for bounded radius-4 adjacency q=1 scout",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout.json"),
    )
    parser.add_argument(
        "--md",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_verification.json"),
    )
    args = parser.parse_args()
    result = verify(report_path=Path(args.report), md_path=Path(args.md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
