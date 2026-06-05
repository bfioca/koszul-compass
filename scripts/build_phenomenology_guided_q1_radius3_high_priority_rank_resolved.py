#!/usr/bin/env python3
"""Apply known rank resolutions to high-priority radius-3 unresolved records."""

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
from build_phenomenology_guided_q1_radius2_rank_resolved_backlog import (  # noqa: E402
    apply_rank_resolutions,
)

WINDOW_REPORTS = {
    "window1": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout.json",
    "window2": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window2.json",
    "window3": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window3.json",
    "window4": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window4.json",
}


def regular_h1_h2() -> dict[str, Any]:
    return {
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def load_candidate(window: str, label: str) -> tuple[dict[str, Any], dict[str, Any], int]:
    report = load_json(WINDOW_REPORTS[window])
    for index, filtered in enumerate(report["filtered_candidate_records"]):
        if filtered["label"] == label:
            return filtered, report["certified_records"][index], index
    raise KeyError(f"candidate {window}/{label} not found")


def apply_small_map_resolution(
    characters: dict[str, Any], resolution: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    small_map = load_json(REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.json")
    large_e2 = load_json(REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.json")
    if not small_map["all_gates_pass"] or not large_e2["all_gates_pass"]:
        return characters, resolution

    extra_resolved = {
        tuple(small_map["line_bundle"]): "radius3_small_map_probe_regular_h1_h2",
        tuple(small_map["dual_line_bundle"]): "serre_dual_radius3_small_map_probe_regular_h1_h2",
        tuple(large_e2["line_bundle"]): "radius3_large_e2_probe_regular_h1_h2",
        tuple(large_e2["dual_line_bundle"]): "serre_dual_radius3_large_e2_probe_regular_h1_h2",
    }
    resolved = copy.deepcopy(characters)
    filled_blocks = copy.deepcopy(resolution["filled_blocks"])
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            line = tuple(cert["line_bundle"])
            if (
                cert["actual_character_computed"]
                or cert["cohomology"] != [0, 2, 2, 0]
                or line not in extra_resolved
            ):
                continue
            method = extra_resolved[line]
            cert["actual"] = regular_h1_h2()
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

    unresolved_blocks = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if not cert["actual_character_computed"] and any(cert["cohomology"]):
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
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json")
    projected_probe = load_json(
        REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"
    )
    small_map_probe = load_json(
        REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.json"
    )
    large_e2_probe = load_json(
        REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]

    rank_resolved_records = []
    filtered_records = []
    high_priority_items = [
        record
        for record in audit["records"]
        if record["audit"].get("priority_bucket")
        == "high_priority_q1_or_adjacent_small_map"
    ]
    for item in high_priority_items:
        source_filtered, certified, source_index = load_candidate(
            item["window"], item["label"]
        )
        characters, resolution = apply_rank_resolutions(certified["characters"])
        characters, resolution = apply_small_map_resolution(characters, resolution)
        resolved = copy.deepcopy(certified)
        resolved["characters"] = characters
        resolved["radius3_high_priority_rank_resolution"] = resolution
        resolved["character_certified"] = all(
            sector["all_characters_computed"] for sector in characters.values()
        )
        resolved["vectorlike_pair_prediction"] = prediction_from_characters(characters)
        resolved["source_window"] = item["window"]
        resolved["source_filtered_label"] = item["label"]
        resolved["source_filtered_index"] = source_index
        resolved["source_radius2_record"] = item["source_radius2_record"]
        rank_resolved_records.append(resolved)

        filtered = candidate_certificate_from_5259_record(
            label=f"{item['window']}_{item['label']}_rank_resolved",
            record=resolved,
            conf=conf,
        )
        filtered["source_window"] = item["window"]
        filtered["source_filtered_label"] = item["label"]
        filtered["source_radius2_record"] = item["source_radius2_record"]
        filtered["radius3_high_priority_rank_resolution"] = resolution
        if not resolved["character_certified"]:
            filtered["classification"] = {
                "category": "unresolved",
                "status": "rank_resolved_character_certificate_still_incomplete",
                "reason": (
                    "known rank resolutions did not cover all high-priority "
                    "radius-3 missing character blocks"
                ),
            }
        else:
            apply_monoid_obstruction_override(filtered)
        filtered_records.append(filtered)

    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for record in filtered_records:
        category = record["classification"]["category"]
        status = record["classification"]["status"]
        categories[category] = categories.get(category, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
    desired_q1 = [
        record
        for record in filtered_records
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    gates = {
        "imports_current_frontier": gate(
            len(high_priority_items) == 4,
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "rank resolver starts from the four audited high-priority radius-3 records",
        ),
        "imports_projected_rank_probe": gate(
            projected_probe["all_gates_pass"]
            and projected_probe["resolved_characters"]["H1"]["regular_multiplicity"] == 1
            and projected_probe["resolved_characters"]["H2"]["regular_multiplicity"] == 1,
            str(REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"),
            "known line-level rank resolutions are backed by the verified projected higher-rank probe",
        ),
        "imports_small_map_probe": gate(
            small_map_probe["all_gates_pass"]
            and small_map_probe["resolved_characters"]["H1"]["regular_multiplicity"] == 1
            and small_map_probe["resolved_characters"]["H2"]["regular_multiplicity"] == 1,
            str(REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.json"),
            "small-map line-level rank resolution is backed by the verified radius-3 probe",
        ),
        "imports_large_e2_probe": gate(
            large_e2_probe["all_gates_pass"]
            and large_e2_probe["resolved_characters"]["H1"]["regular_multiplicity"] == 1
            and large_e2_probe["resolved_characters"]["H2"]["regular_multiplicity"] == 1,
            str(REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.json"),
            "large-line E2 character resolution is backed by the verified radius-3 probe",
        ),
        "all_high_priority_records_attempted": gate(
            len(rank_resolved_records) == 4
            and len(filtered_records) == 4,
            "radius-3 high-priority rank-resolved records",
            "all high-priority unresolved records were passed through known rank resolutions",
        ),
        "known_blocks_filled": gate(
            sum(
                record["radius3_high_priority_rank_resolution"]["filled_block_count"]
                for record in rank_resolved_records
            )
            == 6,
            "known line-level rank resolutions",
            "the verified projected-probe, small-map, and large-E2 lines, plus their Serre duals, were filled",
        ),
        "resolved_records_filtered": gate(
            all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in filtered_records
            )
            and all(record["classification"]["category"] != "viable" for record in filtered_records),
            "rank-resolved high-priority candidate certificates",
            "every attempted record emits the required tables and no viable survivor appears",
        ),
    }
    return {
        "scope": "known-rank resolution pass over high-priority radius-3 unresolved records",
        "status": "no_viable_candidate_found_after_known_rank_resolution",
        "summary": {
            "high_priority_records": len(rank_resolved_records),
            "filled_blocks": sum(
                record["radius3_high_priority_rank_resolution"]["filled_block_count"]
                for record in rank_resolved_records
            ),
            "remaining_unresolved_blocks": sum(
                record["radius3_high_priority_rank_resolution"]["unresolved_block_count"]
                for record in rank_resolved_records
            ),
            "character_certified_records": sum(
                1 for record in rank_resolved_records if record["character_certified"]
            ),
            "desired_q1_records": len(desired_q1),
            "viable_count": sum(
                1
                for record in filtered_records
                if record["classification"]["category"] == "viable"
            ),
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
        "# Radius-3 High-Priority Rank-Resolved Backlog",
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
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"prediction `{record['spectrum_certificate']['vectorlike_prediction']}`; "
            f"filled `{record['radius3_high_priority_rank_resolution']['filled_block_count']}`, "
            f"unresolved `{record['radius3_high_priority_rank_resolution']['unresolved_block_count']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved.md"),
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
