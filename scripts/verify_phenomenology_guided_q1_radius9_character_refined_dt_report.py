#!/usr/bin/env python3
"""Verify the radius-9 character-refined DT report."""

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


def proton_allowed_count(record: dict[str, Any]) -> int:
    return sum(
        1
        for item in record.get("proton_decay_operator_table") or []
        if not item.get("forbidden_by_current_selection_rules")
    )


def has_triplet_only_hit(record: dict[str, Any]) -> bool:
    return any(
        item.get("character_refined_support_class") == "triplet_only_character_mass"
        and item.get("triplet_mass_allowed_by_refined_selection_rules")
        and not item.get("doublet_mass_allowed_by_refined_selection_rules")
        and item.get("invariant_singlet_monomial_hits_degree_le_2")
        for item in record.get("refined_mass_operator_table") or []
    )


def has_doublet_support(record: dict[str, Any]) -> bool:
    return any(
        item.get("doublet_mass_allowed_by_refined_selection_rules")
        for item in record.get("refined_mass_operator_table") or []
    )


def verify(report_json: Path, report_md: Path, rollup_json: Path, windows: int) -> dict[str, Any]:
    report = load_json(report_json)
    rollup = load_json(rollup_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    rollup_summary = rollup["summary"]
    weighted_status_total = sum(summary["weighted_refined_statuses"].values())
    unweighted_status_total = sum(summary["unweighted_refined_statuses"].values())
    viable = report.get("refined_viable_candidate_records") or []
    best = report.get("best_candidate")
    gates = {
        "builder_gates_pass": gate(
            report.get("all_gates_pass")
            and all(item.get("pass") for item in report.get("gates", {}).values()),
            str(report_json),
            "builder-side character-refined DT gates passed",
        ),
        "imports_verified_rollup": gate(
            rollup_summary.get("all_verified")
            and rollup_summary.get("windows_closed") == windows,
            str(rollup_json),
            "source radius-9 rollup is verified for the requested window count",
        ),
        "status_totals_match": gate(
            weighted_status_total == summary["represented_q1_weight"]
            and unweighted_status_total == summary["unweighted_records_scanned"]
            and summary["represented_q1_weight"]
            == rollup_summary["adjusted_desired_q1_candidates"],
            str(report_json),
            "weighted and unweighted refined status totals match the scanned q=1 records",
        ),
        "refined_viable_records_present": gate(
            summary["refined_viable_candidate_weight"] > 0
            and summary["explicit_refined_viable_candidate_count"] > 0
            and len(viable) >= summary["explicit_refined_viable_candidate_count"],
            str(report_json),
            "report emits explicit refined viable candidate records",
        ),
        "old_negative_control_bucket_split": gate(
            summary["old_to_refined_status_transitions"].get(
                "negative_control_doublet_triplet_obstruction -> passes_refined_charge_character_dt_and_proton_filter",
                0,
            )
            == summary["refined_viable_candidate_weight"],
            str(report_json),
            "all refined viable candidates came from the old negative-control DT bucket",
        ),
        "best_candidate_sections_present": gate(
            best is not None
            and best.get("spectrum_certificate") is not None
            and best.get("character_certificate") is not None
            and best.get("refined_mass_operator_table") is not None
            and best.get("proton_decay_operator_table") is not None
            and best.get("classification", {}).get("category") == "viable",
            str(report_json),
            "best candidate includes spectrum, character, refined mass, proton, and viable classification sections",
        ),
        "best_candidate_refined_dt_gate": gate(
            best is not None and has_triplet_only_hit(best) and not has_doublet_support(best),
            str(report_json),
            "best candidate has a triplet-only invariant mass hit and no doublet-support mass hit",
        ),
        "best_candidate_proton_gate": gate(
            best is not None and proton_allowed_count(best) == 0,
            str(report_json),
            "best candidate has no allowed dangerous 10*5bar*5bar operator",
        ),
        "viable_records_have_required_tables": gate(
            all(
                record.get("spectrum_certificate")
                and record.get("character_certificate")
                and record.get("refined_mass_operator_table")
                and record.get("proton_decay_operator_table") is not None
                and record.get("classification", {}).get("category") == "viable"
                and has_triplet_only_hit(record)
                and not has_doublet_support(record)
                and proton_allowed_count(record) == 0
                for record in viable
            ),
            str(report_json),
            "every emitted refined viable candidate carries the required tables and passes refined gates",
        ),
        "markdown_exposes_candidate": gate(
            f"Status: `radius9_character_refined_dt_windows1_{windows}_candidate_found`"
            in md_text
            and "passes_refined_charge_character_dt_and_proton_filter" in md_text
            and "triplet-only mass hits" in md_text,
            str(report_md),
            "markdown exposes the candidate-found status and refined mass evidence",
        ),
    }
    return {
        "scope": "verification for radius-9 character-refined DT report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.md"
        ),
    )
    parser.add_argument(
        "--rollup-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_broad_windows1_45_rollup.json"),
    )
    parser.add_argument("--windows", type=int, default=45)
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        report_json=Path(args.report_json),
        report_md=Path(args.report_md),
        rollup_json=Path(args.rollup_json),
        windows=args.windows,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
