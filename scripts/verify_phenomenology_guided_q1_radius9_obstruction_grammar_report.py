#!/usr/bin/env python3
"""Verify the radius-9 obstruction grammar report."""

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


def verify(report_json: Path, report_md: Path, rollup_json: Path, windows: int) -> dict[str, Any]:
    report = load_json(report_json)
    rollup = load_json(rollup_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    rollup_summary = rollup["summary"]
    examples = report["representative_examples"]
    closest = report["closest_to_viable"]
    conclusions = report["structural_conclusions"]
    partition = report["allowed_proton_operator_partition_check"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_json),
            "builder-side obstruction grammar gates passed",
        ),
        "imports_verified_rollup": gate(
            rollup_summary["all_verified"]
            and rollup_summary["windows_closed"] == windows
            and summary["windows_closed"] == windows
            and summary["frontier_records_screened"]
            == rollup_summary["frontier_records_screened"]
            and summary["adjusted_desired_q1_candidates"]
            == rollup_summary["adjusted_desired_q1_candidates"],
            str(rollup_json),
            "grammar report imports the verified cumulative radius-9 rollup",
        ),
        "status_counts_match_rollup": gate(
            summary["adjusted_statuses"] == rollup_summary["adjusted_statuses"]
            and summary["viable_count"] == 0
            and summary["open_mass_monoid_solutions"] == 0,
            str(report_json),
            "obstruction counts match the source rollup and no viable/open case exists",
        ),
        "ranked_obstructions_cover_q1_failures": gate(
            {item["status"] for item in summary["ranked_q1_obstructions"]}
            == {
                key
                for key in rollup_summary["adjusted_statuses"]
                if key != "rejected_spectrum_signature_not_q1_three_family"
            },
            str(report_json),
            "ranked obstruction section covers every q1 obstruction class",
        ),
        "representative_examples_have_tables": gate(
            all(
                example is None
                or (
                    example["mass"]["mass_entry_count"] > 0
                    and example["proton"]["operator_count"] > 0
                )
                for example in examples.values()
            ),
            str(report_json),
            "representative examples carry mass and proton tables",
        ),
        "dangerous_rule_is_complement_partition": gate(
            partition["all_allowed_entries_are_complement_partitions"]
            and partition["weighted_allowed_entries"]
            == partition["weighted_complement_partition_entries"],
            str(report_json),
            "allowed dangerous proton entries are trace-neutral complement partitions",
        ),
        "no_selective_dt_observed": gate(
            report["cross_gate_counts_from_mined_representatives"].get(
                "dt_viability_with_proton_protection", 0
            )
            == 0
            and report["cross_gate_counts_from_mined_representatives"].get(
                "dt_viability_without_proton_protection", 0
            )
            == 0
            and closest["selective_dt_but_proton_unprotected"] is None,
            str(report_json),
            "no mined representative has selective doublet-triplet evidence",
        ),
        "closest_classes_present": gate(
            closest["isolated_doublet_triplet_gate"] is not None
            and closest["isolated_triplet_mass_gate"] is not None
            and closest["proton_failure_with_no_triplet_mass"] is not None,
            str(report_json),
            "report identifies nearest isolated failure classes",
        ),
        "structural_questions_answered": gate(
            "not logically forced by the q=1 spectrum grammar"
            in conclusions["dangerous_operator_genericity"]
            and "structurally forced inside the current charge-only grammar"
            in conclusions["doublet_triplet_charge_rule"]
            and "partition of {0,1,2,3,4}"
            in conclusions["dangerous_operator_charge_rule"],
            str(report_json),
            "report answers forced-vs-correlated obstruction grammar questions",
        ),
        "markdown_exposes_findings": gate(
            "Radius-9 Obstruction Grammar Report" in md_text
            and "dangerous_operator_charge_rule" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text
            and "Closest-To-Viable Classes" in md_text,
            str(report_md),
            "markdown exposes ranked classes and structural conclusions",
        ),
    }
    return {
        "scope": "verification for radius-9 obstruction grammar report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=36)
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_obstruction_grammar_windows1_36.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_obstruction_grammar_windows1_36.md"
        ),
    )
    parser.add_argument(
        "--rollup-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_broad_windows1_36_rollup.json"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_obstruction_grammar_windows1_36_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        Path(args.report_json),
        Path(args.report_md),
        Path(args.rollup_json),
        args.windows,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
