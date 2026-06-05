#!/usr/bin/env python3
"""Build the final radius-2 obstruction-filter certificate.

This consolidates the four raw q=1 windows and replaces superseded unresolved
records with the strongest later character/rank-resolved classification.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOW_REPORTS = [
    ("window1", "phenomenology_guided_q1_radius2_pilot.json"),
    ("window2", "phenomenology_guided_q1_radius2_pilot_window2.json"),
    ("window3", "phenomenology_guided_q1_radius2_pilot_window3.json"),
    ("window4", "phenomenology_guided_q1_radius2_pilot_window4.json"),
]

RESOLUTION_REPORTS = [
    "phenomenology_guided_q1_radius2_enhanced_backlog.json",
    "phenomenology_guided_q1_radius2_rank_resolved_backlog.json",
    "phenomenology_guided_q1_radius2_medium_rank_resolved.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def source_key(record: dict[str, Any]) -> tuple[str, str] | None:
    window = record.get("source_window")
    label = record.get("source_filtered_label")
    if not window or not label:
        return None
    return (window, label)


def desired_q1(record: dict[str, Any]) -> bool:
    return bool(
        record["spectrum_certificate"]["desired_q1_three_family_signature"]
    )


def has_required_sections(record: dict[str, Any]) -> bool:
    return {
        "spectrum_certificate",
        "character_certificate",
        "mass_operator_table",
        "proton_decay_operator_table",
        "classification",
    }.issubset(record)


def build_initial_records() -> dict[tuple[str, str], dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for window, filename in WINDOW_REPORTS:
        report = load_json(REPORTS / filename)
        for record in report["filtered_candidate_records"]:
            key = (window, record["label"])
            final = copy.deepcopy(record)
            final["raw_candidate_key"] = f"{window}/{record['label']}"
            final["raw_candidate_window"] = window
            final["raw_candidate_label"] = record["label"]
            final["final_resolution_source"] = filename
            final["final_resolution_label"] = record["label"]
            final["resolution_history"] = [
                {
                    "report": filename,
                    "label": record["label"],
                    "classification": record["classification"],
                }
            ]
            records[key] = final
    return records


def apply_unresolved_audit(records: dict[tuple[str, str], dict[str, Any]]) -> None:
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json")
    for item in audit["records"]:
        key = (item["window"], item["label"])
        if key not in records:
            continue
        recommendation = item["audit"]
        if recommendation["recommended_classification"] != "phenomenologically obstructed":
            continue
        record = records[key]
        record["original_classification_before_audit"] = record["classification"]
        record["classification"] = {
            "category": "phenomenologically obstructed",
            "status": recommendation["recommended_status"],
            "reason": (
                "certified singlet monoid support cannot supply a triplet mass "
                "operator at the audited degree bound"
            ),
        }
        record["obstruction_audit"] = recommendation
        record["final_resolution_source"] = (
            "phenomenology_guided_q1_radius2_unresolved_audit.json"
        )
        record["final_resolution_label"] = item["label"]
        record["resolution_history"].append(
            {
                "report": "phenomenology_guided_q1_radius2_unresolved_audit.json",
                "label": item["label"],
                "classification": record["classification"],
            }
        )


def apply_resolution_reports(records: dict[tuple[str, str], dict[str, Any]]) -> None:
    for filename in RESOLUTION_REPORTS:
        report = load_json(REPORTS / filename)
        for resolved in report.get("filtered_candidate_records", []):
            key = source_key(resolved)
            if key is None or key not in records:
                continue
            classification = resolved["classification"]
            if classification["category"] == "unresolved":
                continue
            final = copy.deepcopy(resolved)
            final["raw_candidate_key"] = f"{key[0]}/{key[1]}"
            final["raw_candidate_window"] = key[0]
            final["raw_candidate_label"] = key[1]
            final["final_resolution_source"] = filename
            final["final_resolution_label"] = resolved["label"]
            history = records[key].get("resolution_history", [])
            final["resolution_history"] = history + [
                {
                    "report": filename,
                    "label": resolved["label"],
                    "classification": classification,
                }
            ]
            records[key] = final


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json")
    current = load_json(REPORTS / "phenomenology_guided_q1_radius2_current_frontier.json")
    negative = load_json(REPORTS / "cicy5259_lead_phenomenology_dossier.json")

    records_by_key = build_initial_records()
    apply_unresolved_audit(records_by_key)
    apply_resolution_reports(records_by_key)
    records = [
        records_by_key[key]
        for key in sorted(records_by_key, key=lambda item: (item[0], item[1]))
    ]

    categories = Counter(record["classification"]["category"] for record in records)
    statuses = Counter(record["classification"]["status"] for record in records)
    desired_records = [record for record in records if desired_q1(record)]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    obstructed_desired = [
        record
        for record in desired_records
        if record["classification"]["category"] == "phenomenologically obstructed"
    ]

    gates = {
        "imports_closed_frontier": gate(
            current["summary"]["raw_q1_spectrum_survivors"] == 29
            and current["summary"]["current_obstructed_count"] == 29
            and current["summary"]["current_unresolved_count"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius2_current_frontier.json"),
            "frontier closure says all 29 radius-2 q=1 attempts are classified",
        ),
        "one_record_per_raw_attempt": gate(
            len(records) == aggregate["aggregate_totals"]["filtered_candidate_records"] == 29,
            str(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json"),
            "certificate emits exactly one final record for each raw q=1 attempt",
        ),
        "all_records_have_required_tables": gate(
            all(has_required_sections(record) for record in records)
            and all(record["mass_operator_table"] is not None for record in records)
            and all(record["proton_decay_operator_table"] is not None for record in records),
            "consolidated candidate records",
            "every final candidate has spectrum, character, mass, proton, and classification sections",
        ),
        "negative_control_pattern_rejected": gate(
            any(
                record["classification"]["status"]
                == "negative_control_doublet_triplet_obstruction"
                for record in records
            )
            and negative["classification"]["category"] == "phenomenologically obstructed",
            str(REPORTS / "cicy5259_lead_phenomenology_dossier.json"),
            "the 5259/7914 obstruction pattern is an active rejection status",
        ),
        "no_viable_radius2_candidate": gate(
            len(viable) == 0
            and categories == {"phenomenologically obstructed": 29},
            "consolidated candidate records",
            "no radius-2 candidate passes the charge-level phenomenology filter",
        ),
        "desired_q1_records_all_obstructed": gate(
            len(desired_records) == len(obstructed_desired) == 28,
            "consolidated candidate records",
            "all final desired-q1 spectrum records are obstructed by charge-level evidence",
        ),
    }

    return {
        "scope": "final radius-2 q=1 obstruction-filter certificate around the CICY 5259/7914 negative control",
        "status": "radius2_filter_closed_no_viable_candidate",
        "filter_requirements": {
            "spectrum": "three families plus exactly one vectorlike 5/5bar pair after Wilson-line projection",
            "mass_terms": "certified singlet/moduli operator can lift colored triplets while forbidding, suppressing, or leaving tunably light the electroweak Higgs doublets",
            "proton_decay": "dangerous 10*5bar*5bar operators are forbidden by certified residual selection rules",
            "negative_control": "reject the CICY 5259/7914 doublet-triplet/proton-decay obstruction pattern even when q=1",
        },
        "negative_control": {
            "source": "cicy5259_lead_phenomenology_dossier.json",
            "classification": negative["classification"],
            "obstruction_status": "phenomenologically_obstructed_by_current_charge_level_evidence",
        },
        "summary": {
            "raw_q1_attempts": len(records),
            "desired_q1_final_records": len(desired_records),
            "phenomenologically_obstructed": categories["phenomenologically obstructed"],
            "unresolved": categories["unresolved"],
            "viable": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "candidate_records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Obstruction-Filter Certificate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Filter",
        "",
    ]
    for key, value in report["filter_requirements"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- raw q=1 attempts: `{report['summary']['raw_q1_attempts']}`",
            f"- desired q=1 final records: `{report['summary']['desired_q1_final_records']}`",
            f"- phenomenologically obstructed: `{report['summary']['phenomenologically_obstructed']}`",
            f"- unresolved: `{report['summary']['unresolved']}`",
            f"- viable: `{report['summary']['viable']}`",
            f"- statuses: `{report['summary']['statuses']}`",
            "",
            "## Candidate Ledger",
            "",
        ]
    )
    for record in report["candidate_records"]:
        lines.append(
            "- "
            f"`{record['raw_candidate_key']}` -> `{record['final_resolution_label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"desired-q1 `{record['spectrum_certificate']['desired_q1_three_family_signature']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The radius-2 q=1 branch is closed under the current move primitives and certification machinery: every raw attempt has a spectrum certificate, character certificate, mass-operator table, proton-decay table, and final classification, and no candidate passes the charge-level filter.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate.md"),
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
