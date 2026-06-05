#!/usr/bin/env python3
"""Audit unresolved q=1 records from the radius-2 phenomenology frontier."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOW_REPORTS = [
    ("window1", REPORTS / "phenomenology_guided_q1_radius2_pilot.json"),
    ("window2", REPORTS / "phenomenology_guided_q1_radius2_pilot_window2.json"),
    ("window3", REPORTS / "phenomenology_guided_q1_radius2_pilot_window3.json"),
    ("window4", REPORTS / "phenomenology_guided_q1_radius2_pilot_window4.json"),
]
TARGET_DEGREES = {
    "V": ["H1"],
    "V_dual": ["H2"],
    "wedge2_V": ["H1", "H2"],
    "wedge2_V_dual": ["H1", "H2"],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def nonzero_degree_keys(cohomology: list[int]) -> list[str]:
    return [f"H{degree}" for degree, value in enumerate(cohomology) if value]


def missing_character_blocks(record: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    characters = record["character_certificate"]["characters"]
    for sector_label, target_keys in TARGET_DEGREES.items():
        sector = characters[sector_label]
        for cert in sector["line_certificates"]:
            nonzero_keys = nonzero_degree_keys(cert["cohomology"])
            missing_keys = [
                key
                for key in target_keys
                if key in nonzero_keys and key not in cert["actual"]
            ]
            if not missing_keys:
                continue
            source_totals = cert["source_totals"]
            blocks.append(
                {
                    "sector": sector_label,
                    "summand_index": cert.get("summand_index"),
                    "summand_pair": cert.get("summand_pair"),
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "missing_degree_keys": missing_keys,
                    "method": cert["method"],
                    "source_count": cert["source_count"],
                    "source_total_dimensions": {
                        degree: item["dimension"]
                        for degree, item in sorted(source_totals.items())
                    },
                }
            )
    return blocks


def positive_support_obstructions(
    *,
    needed: list[int],
    certified_singlet_charges: list[list[int]],
) -> list[dict[str, Any]]:
    obstructions = []
    for index, value in enumerate(needed):
        if value <= 0:
            continue
        has_positive_generator = any(charge[index] > 0 for charge in certified_singlet_charges)
        if not has_positive_generator:
            obstructions.append(
                {
                    "coordinate": f"e{index}",
                    "needed_value": value,
                    "reason": (
                        "target charge needs a positive coefficient in this coordinate, "
                        "but no certified H1 singlet generator contributes positively there"
                    ),
                }
            )
    return obstructions


def audit_no_triplet_mass_record(record: dict[str, Any]) -> dict[str, Any]:
    singlets = record["singlet_moduli_inventory"]
    singlet_records = singlets["all_nonzero_ext1_line_sectors"]
    certified_labels = set(singlets["certified_h1_singlet_charge_labels"])
    certified = [
        item
        for item in singlet_records
        if item["charge"]["label"] in certified_labels and item["h1_dimension"] > 0
    ]
    certified_charges = [item["charge"]["coefficients"] for item in certified]
    mass_entries = []
    for item in record["mass_operator_table"]:
        needed = item["needed_singlet_charge"]["coefficients"]
        support_obstructions = positive_support_obstructions(
            needed=needed,
            certified_singlet_charges=certified_charges,
        )
        mass_entries.append(
            {
                "fivebar": item["fivebar"],
                "five": item["five"],
                "needed_singlet_charge": item["needed_singlet_charge"],
                "certified_singlet_labels": sorted(certified_labels),
                "degree_le_2_hits": item["certified_singlet_monomial_hits_degree_le_2"],
                "positive_support_obstructions": support_obstructions,
                "certified_singlet_monoid_obstructed": bool(support_obstructions),
            }
        )
    return {
        "kind": "certified_record_without_triplet_mass",
        "mass_entries": mass_entries,
        "all_mass_entries_monoid_obstructed": all(
            entry["certified_singlet_monoid_obstructed"] for entry in mass_entries
        ),
        "recommended_classification": (
            "phenomenologically obstructed"
            if all(entry["certified_singlet_monoid_obstructed"] for entry in mass_entries)
            else "unresolved"
        ),
        "recommended_status": (
            "no_triplet_mass_in_certified_singlet_monoid"
            if all(entry["certified_singlet_monoid_obstructed"] for entry in mass_entries)
            else "no_certified_triplet_mass_operator_found"
        ),
    }


def collect_unresolved() -> list[dict[str, Any]]:
    unresolved = []
    for window_label, path in WINDOW_REPORTS:
        report = load_json(path)
        for index, record in enumerate(report["filtered_candidate_records"]):
            if record["classification"]["category"] != "unresolved":
                continue
            entry = {
                "window": window_label,
                "window_record_index": index,
                "label": record["label"],
                "source_report": str(path),
                "matrix": record["matrix"],
                "cohomology": record["spectrum_certificate"]["cohomology"],
                "vectorlike_prediction": record["spectrum_certificate"][
                    "vectorlike_prediction"
                ],
                "current_classification": record["classification"],
                "character_certified": record["character_certificate"][
                    "character_certified"
                ],
            }
            if not record["character_certificate"]["character_certified"]:
                blocks = missing_character_blocks(record)
                entry["audit"] = {
                    "kind": "missing_character_or_charge_level_data",
                    "missing_character_block_count": len(blocks),
                    "missing_character_blocks": blocks,
                    "recommended_classification": "unresolved",
                    "recommended_status": "character_certificate_backlog",
                }
            else:
                entry["audit"] = audit_no_triplet_mass_record(record)
            unresolved.append(entry)
    return unresolved


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json")
    unresolved = collect_unresolved()
    kinds = Counter(item["audit"]["kind"] for item in unresolved)
    recommended_categories = Counter(
        item["audit"]["recommended_classification"] for item in unresolved
    )
    recommended_statuses = Counter(item["audit"]["recommended_status"] for item in unresolved)
    missing_blocks = sum(
        item["audit"].get("missing_character_block_count", 0) for item in unresolved
    )
    monoid_obstructed = [
        item
        for item in unresolved
        if item["audit"]["kind"] == "certified_record_without_triplet_mass"
        and item["audit"]["all_mass_entries_monoid_obstructed"]
    ]

    gates = {
        "imports_full_radius2_aggregate": gate(
            aggregate["coverage"]["full_radius2_anomaly_frontier_covered"]
            and aggregate["aggregate_categories"]["unresolved"] == 11,
            str(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json"),
            "audit starts from the verified full-current-radius-2 aggregate unresolved frontier",
        ),
        "all_unresolved_records_collected": gate(
            len(unresolved) == aggregate["aggregate_categories"]["unresolved"] == 11,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "all unresolved q=1 records from the four radius-2 windows are included",
        ),
        "missing_character_backlog_identified": gate(
            kinds["missing_character_or_charge_level_data"] == 10
            and missing_blocks > 0,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "ten unresolved records are character-certification backlog with explicit missing blocks",
        ),
        "certified_no_mass_record_strengthened": gate(
            len(monoid_obstructed) == 1
            and recommended_statuses["no_triplet_mass_in_certified_singlet_monoid"] == 1,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "the one character-certified no-mass record is obstructed by certified singlet monoid support",
        ),
    }
    return {
        "scope": "audit of unresolved q=1 records in the radius-2 phenomenology-guided frontier",
        "status": "unresolved_frontier_triaged",
        "summary": {
            "unresolved_records": len(unresolved),
            "kinds": dict(sorted(kinds.items())),
            "recommended_categories": dict(sorted(recommended_categories.items())),
            "recommended_statuses": dict(sorted(recommended_statuses.items())),
            "missing_character_block_count": missing_blocks,
        },
        "records": unresolved,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Unresolved Q1 Frontier Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- unresolved records: `{report['summary']['unresolved_records']}`",
        f"- kinds: `{report['summary']['kinds']}`",
        f"- recommended categories: `{report['summary']['recommended_categories']}`",
        f"- recommended statuses: `{report['summary']['recommended_statuses']}`",
        f"- missing character blocks: `{report['summary']['missing_character_block_count']}`",
        "",
        "## Records",
        "",
    ]
    for item in report["records"]:
        audit = item["audit"]
        lines.append(
            "- "
            f"`{item['window']}/{item['label']}`: "
            f"`{item['current_classification']['status']}` -> "
            f"`{audit['recommended_status']}`"
        )
        if audit["kind"] == "missing_character_or_charge_level_data":
            lines.append(
                f"  missing character blocks: `{audit['missing_character_block_count']}`"
            )
        else:
            entries = audit["mass_entries"]
            lines.append(
                "  certified singlet monoid obstructed: "
                f"`{audit['all_mass_entries_monoid_obstructed']}`; "
                f"needed charge `{entries[0]['needed_singlet_charge']['label']}`"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"unresolved_records={report['summary']['unresolved_records']}")
    print(f"kinds={report['summary']['kinds']}")
    print(f"recommended_statuses={report['summary']['recommended_statuses']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
