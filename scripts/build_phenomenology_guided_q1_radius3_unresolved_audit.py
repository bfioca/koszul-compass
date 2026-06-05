#!/usr/bin/env python3
"""Audit unresolved records in the full radius-3 adjacency frontier."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOW_REPORTS = [
    ("window1", REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout.json"),
    ("window2", REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window2.json"),
    ("window3", REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window3.json"),
    ("window4", REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window4.json"),
]

TARGET_DEGREES = {
    "V": ["H1"],
    "V_dual": ["H2"],
    "wedge2_V": ["H1", "H2"],
    "wedge2_V_dual": ["H1", "H2"],
}

DESIRED_Q1_TARGETS = {
    ("V", "H1"): {"dimension": 6, "regular_multiplicity": 3},
    ("V_dual", "H2"): {"dimension": 6, "regular_multiplicity": 3},
    ("wedge2_V", "H1"): {"dimension": 8, "regular_multiplicity": 4},
    ("wedge2_V", "H2"): {"dimension": 2, "regular_multiplicity": 1},
    ("wedge2_V_dual", "H1"): {"dimension": 2, "regular_multiplicity": 1},
    ("wedge2_V_dual", "H2"): {"dimension": 8, "regular_multiplicity": 4},
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
                        for degree, item in sorted(cert["source_totals"].items())
                    },
                }
            )
    return blocks


def trace_zero_feasible(*, partial_trace: int, missing_dimension: int) -> bool:
    required_trace = -partial_trace
    return (
        missing_dimension >= 0
        and abs(required_trace) <= missing_dimension
        and (missing_dimension + required_trace) % 2 == 0
    )


def desired_q1_trace_feasibility(record: dict[str, Any]) -> dict[str, Any]:
    characters = record["character_certificate"]["characters"]
    targets = {}
    all_feasible = True
    for (sector, key), expected in DESIRED_Q1_TARGETS.items():
        partial = characters[sector]["cohomology_characters"].get(
            key,
            {
                "dimension": 0,
                "nonidentity_trace": 0,
                "multiplicities": {"+": 0, "-": 0},
            },
        )
        missing_dimension = expected["dimension"] - partial["dimension"]
        feasible = trace_zero_feasible(
            partial_trace=partial["nonidentity_trace"],
            missing_dimension=missing_dimension,
        )
        all_feasible = all_feasible and feasible
        targets[f"{sector}.{key}"] = {
            "target_dimension": expected["dimension"],
            "target_regular_multiplicity": expected["regular_multiplicity"],
            "partial_dimension": partial["dimension"],
            "partial_trace": partial["nonidentity_trace"],
            "missing_dimension": missing_dimension,
            "required_missing_trace_for_regular": -partial["nonidentity_trace"],
            "trace_zero_feasible": feasible,
        }
    return {
        "desired_q1_trace_feasible": all_feasible,
        "targets": targets,
    }


def positive_support_obstructions(
    *,
    needed: list[int],
    certified_singlet_charges: list[list[int]],
) -> list[dict[str, Any]]:
    obstructions = []
    for index, value in enumerate(needed):
        if value <= 0:
            continue
        if not any(charge[index] > 0 for charge in certified_singlet_charges):
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
                "degree_le_2_hits": item["certified_singlet_monomial_hits_degree_le_2"],
                "certified_singlet_labels": sorted(certified_labels),
                "positive_support_obstructions": support_obstructions,
                "certified_singlet_monoid_obstructed": bool(support_obstructions),
            }
        )
    all_obstructed = bool(mass_entries) and all(
        entry["certified_singlet_monoid_obstructed"] for entry in mass_entries
    )
    return {
        "kind": "certified_record_without_triplet_mass",
        "mass_entries": mass_entries,
        "all_mass_entries_monoid_obstructed": all_obstructed,
        "recommended_classification": (
            "phenomenologically obstructed" if all_obstructed else "unresolved"
        ),
        "recommended_status": (
            "no_triplet_mass_in_certified_singlet_monoid"
            if all_obstructed
            else "no_certified_triplet_mass_operator_found"
        ),
    }


def priority_bucket(
    *,
    missing_blocks: list[dict[str, Any]],
    feasibility: dict[str, Any],
    prediction: dict[str, Any],
) -> str:
    if not feasibility["desired_q1_trace_feasible"]:
        return "trace_infeasible_low_priority"
    if (
        prediction.get("net_families") == 3
        and prediction.get("colored_triplet_vectorlike_pairs") in {0, 1}
        and len(missing_blocks) <= 2
    ):
        return "high_priority_q1_or_adjacent_small_map"
    if prediction.get("net_families") == 3:
        return "medium_priority_three_family"
    if len(missing_blocks) <= 2:
        return "medium_priority_small_map_backlog"
    return "low_priority_nonq1_or_large_map_backlog"


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
                "source_radius2_record": record.get("radius3_source_raw_candidate_key"),
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
                feasibility = desired_q1_trace_feasibility(record)
                entry["audit"] = {
                    "kind": "missing_character_or_charge_level_data",
                    "missing_character_block_count": len(blocks),
                    "missing_character_blocks": blocks,
                    "desired_q1_trace_feasibility": feasibility,
                    "priority_bucket": priority_bucket(
                        missing_blocks=blocks,
                        feasibility=feasibility,
                        prediction=entry["vectorlike_prediction"],
                    ),
                    "recommended_classification": "unresolved",
                    "recommended_status": "character_certificate_backlog",
                }
            else:
                entry["audit"] = audit_no_triplet_mass_record(record)
            unresolved.append(entry)
    return unresolved


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json")
    unresolved = collect_unresolved()
    kinds = Counter(item["audit"]["kind"] for item in unresolved)
    recommended_categories = Counter(
        item["audit"]["recommended_classification"] for item in unresolved
    )
    recommended_statuses = Counter(item["audit"]["recommended_status"] for item in unresolved)
    priority_buckets = Counter(
        item["audit"].get("priority_bucket", "certified_no_mass_record")
        for item in unresolved
    )
    missing_blocks = sum(
        item["audit"].get("missing_character_block_count", 0) for item in unresolved
    )
    block_patterns = Counter()
    for item in unresolved:
        for block in item["audit"].get("missing_character_blocks", []):
            key = (
                block["sector"],
                tuple(block["line_bundle"]),
                tuple(block["cohomology"]),
                tuple(block["missing_degree_keys"]),
                block["source_count"],
                tuple(sorted(block["source_total_dimensions"].items())),
            )
            block_patterns[key] += 1
    monoid_obstructed = [
        item
        for item in unresolved
        if item["audit"]["kind"] == "certified_record_without_triplet_mass"
        and item["audit"]["all_mass_entries_monoid_obstructed"]
    ]
    trace_feasible = [
        item
        for item in unresolved
        if item["audit"]["kind"] == "missing_character_or_charge_level_data"
        and item["audit"]["desired_q1_trace_feasibility"][
            "desired_q1_trace_feasible"
        ]
    ]
    gates = {
        "imports_full_radius3_aggregate": gate(
            aggregate["coverage"]["covered_records"] == 15595
            and aggregate["coverage"]["remaining_records"] == 0
            and aggregate["aggregate_categories"]["unresolved"] == 34,
            str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json"),
            "audit starts from the verified full radius-3 adjacency aggregate",
        ),
        "all_unresolved_records_collected": gate(
            len(unresolved) == aggregate["aggregate_categories"]["unresolved"] == 34,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "all unresolved q=1 records from the four radius-3 windows are included",
        ),
        "missing_character_backlog_identified": gate(
            kinds["missing_character_or_charge_level_data"] == 32
            and missing_blocks > 0
            and len(block_patterns) > 0,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "missing-character records include explicit missing map blocks",
        ),
        "certified_no_mass_records_strengthened": gate(
            len(monoid_obstructed) == 2
            and recommended_statuses["no_triplet_mass_in_certified_singlet_monoid"] == 2,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "both character-certified no-mass records are obstructed by certified singlet monoid support",
        ),
        "trace_feasibility_prioritized": gate(
            len(trace_feasible) >= 1
            and priority_buckets["high_priority_q1_or_adjacent_small_map"] >= 1,
            ", ".join(str(path) for _, path in WINDOW_REPORTS),
            "audit identifies trace-feasible high-priority character-backlog records",
        ),
    }
    return {
        "scope": "audit of unresolved q=1 records in the full radius-3 adjacency frontier",
        "status": "radius3_unresolved_frontier_triaged",
        "summary": {
            "unresolved_records": len(unresolved),
            "kinds": dict(sorted(kinds.items())),
            "recommended_categories": dict(sorted(recommended_categories.items())),
            "recommended_statuses": dict(sorted(recommended_statuses.items())),
            "priority_buckets": dict(sorted(priority_buckets.items())),
            "missing_character_block_count": missing_blocks,
            "unique_missing_block_patterns": len(block_patterns),
            "trace_feasible_missing_character_records": len(trace_feasible),
        },
        "most_common_missing_block_patterns": [
            {
                "count": count,
                "sector": key[0],
                "line_bundle": list(key[1]),
                "cohomology": list(key[2]),
                "missing_degree_keys": list(key[3]),
                "source_count": key[4],
                "source_total_dimensions": dict(key[5]),
            }
            for key, count in block_patterns.most_common(25)
        ],
        "records": unresolved,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Unresolved Q1 Frontier Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Priority Records", ""])
    for item in report["records"]:
        audit = item["audit"]
        if audit["kind"] == "missing_character_or_charge_level_data":
            lines.append(
                "- "
                f"`{item['window']}/{item['label']}` from `{item['source_radius2_record']}`: "
                f"`{audit['priority_bucket']}`, "
                f"prediction `{item['vectorlike_prediction']}`, "
                f"missing blocks `{audit['missing_character_block_count']}`, "
                f"trace feasible `{audit['desired_q1_trace_feasibility']['desired_q1_trace_feasible']}`"
            )
        else:
            lines.append(
                "- "
                f"`{item['window']}/{item['label']}` from `{item['source_radius2_record']}`: "
                f"`{audit['recommended_status']}`, "
                f"monoid obstructed `{audit['all_mass_entries_monoid_obstructed']}`"
            )
    lines.extend(["", "## Common Missing Blocks", ""])
    for item in report["most_common_missing_block_patterns"][:10]:
        lines.append(
            "- "
            f"count `{item['count']}`: `{item['sector']}` line `{item['line_bundle']}` "
            f"cohomology `{item['cohomology']}` missing `{item['missing_degree_keys']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.md"),
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
