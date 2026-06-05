#!/usr/bin/env python3
"""Build the radius-3 obstruction-filter certificate.

This report recasts the CICY 5259/7914 q=1 target as a negative control and
checks the radius-3 quotient-compatible q=1 frontier against the resulting
charge-level phenomenology filter.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
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


def has_required_tables(record: dict[str, Any]) -> bool:
    return (
        has_required_sections(record)
        and record["mass_operator_table"] is not None
        and record["proton_decay_operator_table"] is not None
    )


def desired_q1(record: dict[str, Any]) -> bool:
    return bool(
        record["spectrum_certificate"]["desired_q1_three_family_signature"]
    )


def raw_key(record: dict[str, Any]) -> str:
    return f"{record.get('source_window')}/{record.get('source_filtered_label')}"


def count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(record["classification"][key] for record in records).items()))


def build_report() -> dict[str, Any]:
    bounded = load_json(
        REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate.json"
    )
    current = load_json(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json")
    branches = load_json(
        REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.json"
    )
    negative = load_json(REPORTS / "cicy5259_lead_phenomenology_dossier.json")

    records = bounded["final_candidate_records"]
    branch_records = branches["branch_certificates"]
    strict_unresolved = [
        record for record in records if record["classification"]["category"] == "unresolved"
    ]
    strict_viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    branch_viable = [
        record
        for record in branch_records
        if record["classification"]["category"] == "viable"
    ]
    desired_records = [record for record in records if desired_q1(record)]
    desired_obstructed = [
        record
        for record in desired_records
        if record["classification"]["category"] == "phenomenologically obstructed"
    ]
    desired_unresolved = [
        record
        for record in desired_records
        if record["classification"]["category"] == "unresolved"
    ]
    table_certified_records = [record for record in records if has_required_tables(record)]
    branch_table_certified = [
        record for record in branch_records if has_required_tables(record)
    ]
    negative_control_records = [
        record
        for record in records + branch_records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    ]
    dangerous_records = [
        record
        for record in records + branch_records
        if record["classification"]["status"]
        == "dangerous_10_5bar_5bar_operator_allowed"
    ]
    no_triplet_mass_records = [
        record
        for record in records + branch_records
        if record["classification"]["status"]
        == "no_triplet_mass_in_certified_singlet_monoid"
    ]

    sign_conflict_key = "window2/radius3_adjacency_filtered_16"
    gates = {
        "imports_radius3_bounded_frontier": gate(
            bounded["all_gates_pass"]
            and bounded["summary"]["raw_q1_spectrum_survivors"] == 64
            and bounded["summary"]["phenomenologically_obstructed"] == 63
            and bounded["summary"]["unresolved"] == 1
            and bounded["summary"]["viable"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate.json"),
            "filter starts from the verified bounded radius-3 candidate ledger",
        ),
        "imports_current_frontier": gate(
            current["all_gates_pass"]
            and current["summary"]["current_obstructed_count"] == 63
            and current["summary"]["current_unresolved_count"] == 1
            and current["summary"]["viable_count"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"),
            "current frontier agrees with the bounded ledger counts",
        ),
        "one_strict_record_per_raw_q1_survivor": gate(
            len(records) == len({raw_key(record) for record in records}) == 64,
            "strict radius-3 candidate records",
            "the strict ledger emits exactly one final record per raw q=1 survivor",
        ),
        "table_certified_records_emit_required_tables": gate(
            len(table_certified_records) == 63
            and all(has_required_sections(record) for record in records),
            "strict radius-3 candidate records",
            "all classified strict records emit spectrum, character, mass, proton, and classification tables",
        ),
        "strict_unresolved_is_sign_conflict": gate(
            len(strict_unresolved) == 1
            and raw_key(strict_unresolved[0]) == sign_conflict_key
            and strict_unresolved[0]["mass_operator_table"] is None
            and strict_unresolved[0]["proton_decay_operator_table"] is None,
            "strict radius-3 unresolved record",
            "the only strict table gap is the known sign-conflict character row",
        ),
        "sign_conflict_branch_tables_close_dimension_cases": gate(
            branches["all_gates_pass"]
            and branches["status"] == "sign_conflict_branches_nonviable_under_current_filter"
            and len(branch_table_certified) == len(branch_records) == 2
            and all(raw_key(record) == sign_conflict_key for record in branch_records)
            and len(branch_viable) == 0,
            str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.json"),
            "both dimension-compatible sign-conflict branches emit tables and are nonviable",
        ),
        "negative_control_pattern_rejected": gate(
            negative["classification"]["category"] == "phenomenologically obstructed"
            and negative["classification"]["status"]
            == "phenomenologically_obstructed_by_current_charge_level_evidence"
            and len(negative_control_records) > 0,
            str(REPORTS / "cicy5259_lead_phenomenology_dossier.json"),
            "the CICY 5259/7914 obstruction pattern is an active rejection status",
        ),
        "no_viable_radius3_candidate_found": gate(
            len(strict_viable) == 0 and len(branch_viable) == 0,
            "strict and branch-certified radius-3 records",
            "no strict record or dimension-compatible sign-conflict branch passes the charge-level filter",
        ),
        "desired_q1_records_are_obstructed_and_branch_exhausted": gate(
            len(desired_records) == 46
            and len(desired_obstructed) == 46
            and len(desired_unresolved) == 0
            and len([record for record in branch_records if desired_q1(record)]) == 1
            and all(
                record["classification"]["category"] == "phenomenologically obstructed"
                for record in branch_records
            ),
            "strict desired-q1 records plus sign-conflict branches",
            "all strict desired-q1 records are obstructed, and the desired-q1 sign-conflict branch is nonviable",
        ),
    }

    return {
        "scope": (
            "radius-3 q=1 obstruction-filter certificate around the CICY 5259/7914 "
            "negative control"
        ),
        "status": "radius3_filter_closed_no_viable_candidate_one_strict_sign_conflict",
        "filter_requirements": {
            "spectrum": (
                "three families plus exactly one vectorlike 5/5bar pair after "
                "Wilson-line projection"
            ),
            "mass_terms": (
                "certified singlet/moduli operator can lift colored triplets while "
                "forbidding, suppressing, or leaving tunably light the electroweak "
                "Higgs doublets"
            ),
            "proton_decay": (
                "dangerous 10*5bar*5bar operators are forbidden by certified "
                "line-bundle, Wilson-line, residual U1, or discrete selection rules"
            ),
            "negative_control": (
                "reject the CICY 5259/7914 doublet-triplet/proton-decay obstruction "
                "pattern even when the spectrum is q=1"
            ),
        },
        "negative_control": {
            "source": "cicy5259_lead_phenomenology_dossier.json",
            "classification": negative["classification"],
            "obstruction_status": (
                "phenomenologically_obstructed_by_current_charge_level_evidence"
            ),
        },
        "summary": {
            "strict_raw_q1_survivors": len(records),
            "strict_desired_q1_records": len(desired_records),
            "strict_table_certified_records": len(table_certified_records),
            "strict_phenomenologically_obstructed": bounded["summary"][
                "phenomenologically_obstructed"
            ],
            "strict_unresolved": len(strict_unresolved),
            "strict_viable": len(strict_viable),
            "sign_conflict_branch_records": len(branch_records),
            "sign_conflict_branch_viable": len(branch_viable),
            "effective_viable": len(strict_viable) + len(branch_viable),
            "negative_control_doublet_triplet_obstructions": len(
                negative_control_records
            ),
            "dangerous_operator_obstructions": len(dangerous_records),
            "no_triplet_mass_obstructions": len(no_triplet_mass_records),
            "strict_categories": count_by(records, "category"),
            "strict_statuses": count_by(records, "status"),
            "branch_categories": count_by(branch_records, "category"),
            "branch_statuses": count_by(branch_records, "status"),
        },
        "strict_candidate_records": records,
        "sign_conflict_branch_records": branch_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Obstruction-Filter Certificate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Filter",
        "",
    ]
    for key, value in report["filter_requirements"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Strict Candidate Ledger", ""])
    for record in report["strict_candidate_records"]:
        lines.append(
            "- "
            f"`{raw_key(record)}` -> `{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"desired-q1 `{desired_q1(record)}`; "
            f"tables `{has_required_tables(record)}`"
        )
    lines.extend(["", "## Sign-Conflict Branch Ledger", ""])
    for record in report["sign_conflict_branch_records"]:
        lines.append(
            "- "
            f"`{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"desired-q1 `{desired_q1(record)}`; "
            f"tables `{has_required_tables(record)}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The radius-3 q=1 frontier has no candidate passing the current "
                "charge-level phenomenology filter. The strict ledger has one "
                "remaining character sign conflict, and both dimension-compatible "
                "branch completions of that conflict are table-certified and "
                "nonviable under the same negative-control filter."
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
            REPORTS
            / "phenomenology_guided_q1_radius3_obstruction_filter_certificate.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius3_obstruction_filter_certificate.md"
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
