#!/usr/bin/env python3
"""Apply verified equivariant rank splits to high-priority residual backlog records."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import sector_record  # noqa: E402
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)

REGULAR_TWO_BY_TWO = {
    "H1": {
        "dimension": 2,
        "nonidentity_trace": 0,
        "multiplicities": {"+": 1, "-": 1},
        "regular_multiplicity": 1,
    },
    "H2": {
        "dimension": 2,
        "nonidentity_trace": 0,
        "multiplicities": {"+": 1, "-": 1},
        "regular_multiplicity": 1,
    },
}

RESOLVED_LINES = {
    (1, 0, -2, -1, -1, 1, 0): "higher_rank_probe_representative",
    (-1, 0, 2, 1, 1, -1, 0): "serre_dual_of_higher_rank_probe_representative",
    (1, 0, -2, 0, -2, 1, 0): "manual_equivariant_rank_jump_probe_dim10_family",
    (-1, 0, 2, 0, 2, -1, 0): "serre_dual_of_dim10_family_probe",
    (1, -2, 0, -2, 0, 1, 0): "projected_higher_rank_probe_dim10_family",
    (-1, 2, 0, 2, 0, -1, 0): "serre_dual_of_projected_higher_rank_probe_dim10_family",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def is_resolvable(cert: dict[str, Any]) -> bool:
    return (
        not cert["actual_character_computed"]
        and cert["cohomology"] == [0, 2, 2, 0]
        and tuple(cert["line_bundle"]) in RESOLVED_LINES
    )


def apply_rank_resolutions(characters: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled_blocks = []
    unresolved_blocks = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if is_resolvable(cert):
                method = RESOLVED_LINES[tuple(cert["line_bundle"])]
                cert["actual"] = copy.deepcopy(REGULAR_TWO_BY_TWO)
                cert["method"] = method
                cert["actual_character_computed"] = True
                filled_blocks.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "method": method,
                        "actual": cert["actual"],
                    }
                )
            elif not cert["actual_character_computed"] and any(cert["cohomology"]):
                unresolved_blocks.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "no_verified_equivariant_rank_split_for_this_line",
                    }
                )

    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = resolved[sector_key]
        resolved[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return resolved, {
        "filled_blocks": filled_blocks,
        "unresolved_blocks": unresolved_blocks,
        "filled_block_count": len(filled_blocks),
        "unresolved_block_count": len(unresolved_blocks),
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    enhanced = load_json(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json")
    higher_probe = load_json(REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.json")
    projected_probe = load_json(
        REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]

    high_labels = {record["label"] for record in scenarios["records"]}
    rank_resolved_records = []
    filtered_records = []
    for record in enhanced["enhanced_records"]:
        if record["label"] not in high_labels:
            continue
        characters, resolution = apply_rank_resolutions(record["characters"])
        resolved_record = copy.deepcopy(record)
        resolved_record["characters"] = characters
        resolved_record["rank_resolution"] = resolution
        resolved_record["character_certified"] = all(
            sector["all_characters_computed"] for sector in characters.values()
        )
        resolved_record["vectorlike_pair_prediction"] = prediction_from_characters(characters)
        rank_resolved_records.append(resolved_record)

        filtered = candidate_certificate_from_5259_record(
            label=record["label"].replace("backlog", "rank_resolved_filtered"),
            record=resolved_record,
            conf=conf,
        )
        filtered["source_window"] = record["source_window"]
        filtered["source_filtered_label"] = record["source_filtered_label"]
        filtered["rank_resolution"] = resolution
        if not resolved_record["character_certified"]:
            filtered["classification"] = {
                "category": "unresolved",
                "status": "rank_resolved_character_certificate_still_incomplete",
                "reason": "at least one high-priority block still lacks a verified equivariant rank split",
            }
        else:
            apply_monoid_obstruction_override(filtered)
        filtered_records.append(filtered)

    desired_q1 = [
        record
        for record in rank_resolved_records
        if record["vectorlike_pair_prediction"]["regular_character_rule_applies"]
        and record["vectorlike_pair_prediction"]["net_families"] == 3
        and record["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"] == 1
    ]
    viable = [
        record for record in filtered_records if record["classification"]["category"] == "viable"
    ]
    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for record in filtered_records:
        category = record["classification"]["category"]
        status = record["classification"]["status"]
        categories[category] = categories.get(category, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1

    gates = {
        "imports_verified_higher_probe": gate(
            higher_probe["all_gates_pass"]
            and higher_probe["resolved_characters"] == REGULAR_TWO_BY_TWO,
            str(REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.json"),
            "rank resolution imports the verified representative regular H1/H2 split",
        ),
        "imports_verified_projected_probe": gate(
            projected_probe["all_gates_pass"]
            and projected_probe["resolved_characters"] == REGULAR_TWO_BY_TWO,
            str(REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"),
            "rank resolution imports the verified projected-higher regular H1/H2 split",
        ),
        "high_priority_records_loaded": gate(
            len(rank_resolved_records) == 4,
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "rank-resolved backlog is restricted to the four high-priority residual records",
        ),
        "conservative_blocks_filled": gate(
            sum(record["rank_resolution"]["filled_block_count"] for record in rank_resolved_records)
            == 8
            and all(
                record["rank_resolution"]["unresolved_block_count"] == 0
                for record in rank_resolved_records
            ),
            "verified line-level rank resolutions",
            "all high-priority blocks with verified or Serre-dual rank splits were promoted",
        ),
        "new_q1_records_filtered": gate(
            len(desired_q1) == 4
            and all(
                record["classification"]["category"] != "viable"
                for record in filtered_records
            ),
            "rank-resolved phenomenology filter",
            "new desired-q1 records were passed through mass/proton classification with no viable survivor",
        ),
        "per_candidate_tables_emitted": gate(
            all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in filtered_records
            ),
            "rank-resolved candidate certificates",
            "every rank-resolved filtered record has the required deliverable sections",
        ),
    }
    return {
        "scope": "rank-resolved high-priority radius-2 backlog and phenomenology filter rerun",
        "status": "no_viable_candidate_found_after_conservative_rank_resolution"
        if not viable
        else "viable_candidate_found_after_rank_resolution",
        "summary": {
            "high_priority_records": len(rank_resolved_records),
            "filled_blocks": sum(
                record["rank_resolution"]["filled_block_count"]
                for record in rank_resolved_records
            ),
            "remaining_unresolved_blocks": sum(
                record["rank_resolution"]["unresolved_block_count"]
                for record in rank_resolved_records
            ),
            "character_certified_records": sum(
                1 for record in rank_resolved_records if record["character_certified"]
            ),
            "desired_q1_records": len(desired_q1),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "rank_resolved_records": rank_resolved_records,
        "filtered_candidate_records": filtered_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Rank-Resolved Backlog",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Candidate Classifications", ""])
    for record in report["filtered_candidate_records"]:
        prediction = record["spectrum_certificate"]["vectorlike_prediction"]
        resolution = record["rank_resolution"]
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"`{record['classification']['category']}` / `{record['classification']['status']}`; "
            f"prediction `{prediction}`; "
            f"rank-filled `{resolution['filled_block_count']}`, "
            f"rank-unresolved `{resolution['unresolved_block_count']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
