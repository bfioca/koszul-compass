#!/usr/bin/env python3
"""Verify the broad radius-6 adjacency scout."""

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


def verify(scout_json: Path, scout_md: Path) -> dict[str, Any]:
    report = load_json(scout_json)
    md_text = scout_md.read_text(encoding="utf-8")
    summary = report["summary"]
    filtered = report["filtered_candidate_records"]
    has_representative_boundary = "representative_grammar_statuses" in summary
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(scout_json),
            "builder-side broad radius6 scout gates passed",
        ),
        "imports_verified_source_frontier": gate(
            report["gates"].get(
                "imports_verified_source_frontier",
                report["gates"].get("imports_verified_radius5_frontier", {"pass": False}),
            )["pass"],
            str(scout_json),
            "broad radius6 scout imports verified q1 source frontier artifacts",
        ),
        "screening_accounting_consistent": gate(
            report["screening_counters"]["frontier_records_screened"] >= 0
            and report["frontier_counters"]["within_charge_bound"]
            >= report["screening_counters"]["frontier_records_screened"],
            str(scout_json),
            "frontier and screening counters are consistent",
        ),
        "certified_records_have_required_sections": gate(
            summary["certified_q1_records"] == len(filtered)
            and all(
                item["spectrum_certificate"] is not None
                and item["character_certificate"] is not None
                and (
                    item["classification"]["category"] == "unresolved"
                    or (
                        item["mass_operator_table"] is not None
                        and item["proton_decay_operator_table"] is not None
                    )
                )
                for item in filtered
            ),
            str(scout_json),
            "every emitted radius6 q1 candidate has the required certificate sections",
        ),
        "classification_counts_match": gate(
            sum(summary["categories"].values()) == summary["certified_q1_records"]
            and sum(summary["statuses"].values()) == summary["certified_q1_records"],
            str(scout_json),
            "classification counts cover all certified q1 records",
        ),
        "representative_grammar_boundary_if_advertised": gate(
            not has_representative_boundary
            or (
                sum(summary["representative_grammar_statuses"].values())
                == summary["certified_q1_records"]
                and "representative_grammar_promoted_count" in summary
                and "cup_product_eligible_count" in summary
                and all(
                    "character_refined_classification" in item
                    and "representative_grammar_gate" in item
                    and "representative_grammar_stage"
                    in item["representative_grammar_gate"]
                    for item in filtered
                )
            ),
            str(scout_json),
            "new scout artifacts expose the representative grammar boundary for every emitted q1 record",
        ),
        "markdown_exposes_scout": gate(
            "Broad Adjacency Scout" in md_text
            and "certified_q1_records" in md_text
            and "viable_count" in md_text,
            str(scout_md),
            "markdown exposes broad radius6 scout totals",
        ),
    }
    return {
        "scope": "verification for broad radius6 adjacency scout",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_broad_adjacency_scout.json"),
    )
    parser.add_argument(
        "--scout-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_broad_adjacency_scout.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius6_broad_adjacency_scout_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(Path(args.scout_json), Path(args.scout_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
