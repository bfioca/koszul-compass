#!/usr/bin/env python3
"""Resolve radius-4 unresolved records using previously verified line probes."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
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

BATCH_CONFIGS = {
    "batch1": {
        "aggregate": REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json",
        "windows": [
            ("window1", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout.json"),
            ("window2", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_window2.json"),
            ("window3", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_window3.json"),
            ("window4", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_window4.json"),
            ("window5", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_window5.json"),
            ("window6", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_window6.json"),
        ],
        "expected_categories": {"phenomenologically obstructed": 28, "unresolved": 21},
        "expected_unresolved_records": 21,
    },
    "batch2": {
        "aggregate": REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.json",
        "windows": [
            (
                "window1",
                REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window1.json",
            ),
            (
                "window2",
                REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window2.json",
            ),
            (
                "window3",
                REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window3.json",
            ),
            (
                "window4",
                REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window4.json",
            ),
            (
                "window5",
                REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window5.json",
            ),
            (
                "window6",
                REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window6.json",
            ),
        ],
        "expected_categories": {"phenomenologically obstructed": 18, "unresolved": 24},
        "expected_unresolved_records": 24,
    },
}

PROBE_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.json",
    REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json",
    REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.json",
    REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.json",
    REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.json",
    REPORTS / "phenomenology_guided_q1_radius3_low_repeated_e2_probe.json",
    REPORTS / "phenomenology_guided_q1_radius3_low_remaining_e2_probe.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def normalized_actual(actual: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(actual)


def add_actual(
    actuals: dict[tuple[int, ...], dict[str, Any]],
    sources: dict[tuple[int, ...], list[str]],
    conflicts: list[dict[str, Any]],
    *,
    line_bundle: list[int] | None,
    actual: dict[str, Any] | None,
    source: str,
) -> None:
    if line_bundle is None or actual is None:
        return
    line = tuple(line_bundle)
    actual = normalized_actual(actual)
    if line in actuals and actuals[line] != actual:
        conflicts.append(
            {
                "line_bundle": list(line),
                "existing_sources": sources[line],
                "conflicting_source": source,
            }
        )
        return
    actuals[line] = actual
    sources.setdefault(line, []).append(source)


def serre_dual_actual(actual: dict[str, Any]) -> dict[str, Any]:
    dual = {}
    for degree in range(4):
        source_key = f"H{3 - degree}"
        if source_key in actual:
            dual[f"H{degree}"] = copy.deepcopy(actual[source_key])
    return dual


def add_actual_with_serre_dual(
    actuals: dict[tuple[int, ...], dict[str, Any]],
    sources: dict[tuple[int, ...], list[str]],
    conflicts: list[dict[str, Any]],
    *,
    line_bundle: list[int] | None,
    actual: dict[str, Any] | None,
    source: str,
) -> None:
    add_actual(
        actuals,
        sources,
        conflicts,
        line_bundle=line_bundle,
        actual=actual,
        source=source,
    )
    if line_bundle is None or actual is None:
        return
    dual = [-value for value in line_bundle]
    add_actual(
        actuals,
        sources,
        conflicts,
        line_bundle=dual,
        actual=serre_dual_actual(actual),
        source=f"{source}:serre_dual",
    )


def load_verified_actuals() -> tuple[
    dict[tuple[int, ...], dict[str, Any]],
    dict[tuple[int, ...], list[str]],
    list[dict[str, Any]],
    list[str],
]:
    actuals: dict[tuple[int, ...], dict[str, Any]] = {}
    sources: dict[tuple[int, ...], list[str]] = {}
    conflicts: list[dict[str, Any]] = []
    imported_reports = []
    for path in PROBE_REPORTS:
        report = load_json(path)
        if not report.get("all_gates_pass"):
            continue
        imported_reports.append(str(path))
        if "records" in report:
            for index, record in enumerate(report["records"]):
                add_actual_with_serre_dual(
                    actuals,
                    sources,
                    conflicts,
                    line_bundle=record.get("line_bundle"),
                    actual=record.get("actual") or record.get("resolved_characters"),
                    source=f"{path.name}:records[{index}]",
                )
        add_actual_with_serre_dual(
            actuals,
            sources,
            conflicts,
            line_bundle=report.get("line_bundle"),
            actual=report.get("resolved_characters") or report.get("actual"),
            source=f"{path.name}:line_bundle",
        )
        add_actual(
            actuals,
            sources,
            conflicts,
            line_bundle=report.get("dual_line_bundle"),
            actual=report.get("dual_resolved_characters") or report.get("actual"),
            source=f"{path.name}:dual_line_bundle",
        )
    return actuals, sources, conflicts, imported_reports


def actual_compatible(actual: dict[str, Any], cohomology: list[int]) -> bool:
    for degree, dimension in enumerate(cohomology):
        key = f"H{degree}"
        if dimension == 0:
            if key in actual and actual[key]["dimension"] != 0:
                return False
            continue
        if key not in actual or actual[key]["dimension"] != dimension:
            return False
    return True


def apply_known_line_resolutions(
    characters: dict[str, Any],
    actuals: dict[tuple[int, ...], dict[str, Any]],
    sources: dict[tuple[int, ...], list[str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    unresolved = []
    incompatible = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            line = tuple(cert["line_bundle"])
            actual = actuals.get(line)
            if actual is None:
                unresolved.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "no_verified_known_line_actual",
                    }
                )
                continue
            if not actual_compatible(actual, cert["cohomology"]):
                incompatible.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "actual": actual,
                        "sources": sources[line],
                    }
                )
                unresolved.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "known_line_actual_dimension_mismatch",
                    }
                )
                continue
            cert["actual"] = copy.deepcopy(actual)
            cert["method"] = "radius4_imported_verified_known_line_probe"
            cert["actual_character_computed"] = True
            filled.append(
                {
                    "sector": sector_key,
                    "summand_index": cert.get("summand_index"),
                    "summand_pair": cert.get("summand_pair"),
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "actual": cert["actual"],
                    "sources": sources[line],
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
        "filled_blocks": filled,
        "unresolved_blocks": unresolved,
        "incompatible_known_actuals": incompatible,
        "filled_block_count": len(filled),
        "unresolved_block_count": len(unresolved),
        "incompatible_known_actual_count": len(incompatible),
    }


def load_unresolved_candidates(windows: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    candidates = []
    for window, path in windows:
        report = load_json(path)
        for index, filtered in enumerate(report["filtered_candidate_records"]):
            if filtered["classification"]["category"] != "unresolved":
                continue
            candidates.append(
                {
                    "window": window,
                    "report": str(path),
                    "index": index,
                    "filtered": filtered,
                    "certified": report["certified_records"][index],
                }
            )
    return candidates


def unresolved_priority(item: dict[str, Any]) -> tuple[Any, ...]:
    filtered = item["filtered"]
    prediction = filtered["spectrum_certificate"]["vectorlike_prediction"]
    missing = sum(
        1
        for sector in filtered["character_certificate"]["characters"].values()
        for cert in sector["line_certificates"]
        if not cert["actual_character_computed"] and any(cert["cohomology"])
    )
    return (
        prediction.get("net_families") != 3,
        prediction.get("colored_triplet_vectorlike_pairs") != 1,
        missing,
        item["window"],
        item["index"],
    )


def build_report(batch: str) -> dict[str, Any]:
    config = BATCH_CONFIGS[batch]
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    aggregate_path = config["aggregate"]
    aggregate = load_json(aggregate_path)
    conf = split["full_picard_presentation_7914"]["conf"]
    actuals, sources, conflicts, imported_reports = load_verified_actuals()
    unresolved_items = load_unresolved_candidates(config["windows"])
    unresolved_items.sort(key=unresolved_priority)

    resolved_records = []
    filtered_records = []
    for item in unresolved_items:
        certified = copy.deepcopy(item["certified"])
        characters, resolution = apply_known_line_resolutions(
            certified["characters"], actuals, sources
        )
        certified["characters"] = characters
        certified["radius4_known_line_resolution"] = resolution
        certified["character_certified"] = all(
            sector["all_characters_computed"] for sector in characters.values()
        )
        certified["vectorlike_pair_prediction"] = prediction_from_characters(characters)
        certified["source_window"] = item["window"]
        certified["source_filtered_label"] = item["filtered"]["label"]
        certified["source_filtered_index"] = item["index"]
        resolved_records.append(certified)

        filtered = candidate_certificate_from_5259_record(
            label=f"{item['window']}_{item['filtered']['label']}_known_line_resolved",
            record=certified,
            conf=conf,
        )
        filtered["source_window"] = item["window"]
        filtered["source_filtered_label"] = item["filtered"]["label"]
        filtered["source_filtered_index"] = item["index"]
        filtered["radius4_known_line_resolution"] = resolution
        if not certified["character_certified"]:
            filtered["classification"] = {
                "category": "unresolved",
                "status": "known_line_resolution_still_incomplete",
                "reason": (
                    "verified known-line character probes did not cover every "
                    "missing radius-4 character block"
                ),
            }
        else:
            apply_monoid_obstruction_override(filtered)
        filtered_records.append(filtered)

    categories = Counter(record["classification"]["category"] for record in filtered_records)
    statuses = Counter(record["classification"]["status"] for record in filtered_records)
    desired_q1 = [
        record
        for record in filtered_records
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    viable = [
        record for record in filtered_records if record["classification"]["category"] == "viable"
    ]
    gates = {
        "imports_selected_radius4_aggregate": gate(
            aggregate["all_gates_pass"]
            and aggregate["aggregate_categories"] == config["expected_categories"],
            str(aggregate_path),
            "known-line resolver starts from the verified selected radius-4 unresolved set",
        ),
        "verified_probe_actuals_imported": gate(
            len(imported_reports) == len(PROBE_REPORTS)
            and len(actuals) >= 70,
            ", ".join(imported_reports),
            "known-line actuals are imported only from verified probe reports",
        ),
        "all_unresolved_records_attempted": gate(
            len(unresolved_items)
            == len(filtered_records)
            == config["expected_unresolved_records"],
            "selected radius-4 unresolved records",
            "every selected radius-4 unresolved record was passed through known-line resolution",
        ),
        "some_blocks_filled": gate(
            sum(
                record["radius4_known_line_resolution"]["filled_block_count"]
                for record in resolved_records
            )
            > 0,
            "known-line resolution records",
            "at least one missing character block was filled from verified known-line probes",
        ),
        "per_candidate_sections_emitted": gate(
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
            "known-line-resolved filtered records",
            "every attempted candidate has the required deliverable sections",
        ),
        "viable_count_consistent": gate(
            len(viable)
            == sum(
                1
                for record in filtered_records
                if record["classification"]["category"] == "viable"
            ),
            "known-line-resolved filtered records",
            "summary viable count matches per-record classifications",
        ),
    }
    return {
        "scope": "known-line resolution pass over selected radius-4 unresolved q=1 candidates",
        "batch": batch,
        "status": "viable_candidate_found_after_known_line_resolution"
        if viable
        else "no_viable_candidate_found_after_known_line_resolution",
        "known_line_sources": {
            "imported_reports": imported_reports,
            "unique_actual_line_bundles": len(actuals),
            "conflicts": conflicts,
        },
        "summary": {
            "attempted_unresolved_records": len(filtered_records),
            "filled_blocks": sum(
                record["radius4_known_line_resolution"]["filled_block_count"]
                for record in resolved_records
            ),
            "remaining_unresolved_blocks": sum(
                record["radius4_known_line_resolution"]["unresolved_block_count"]
                for record in resolved_records
            ),
            "incompatible_known_actuals": sum(
                record["radius4_known_line_resolution"]["incompatible_known_actual_count"]
                for record in resolved_records
            ),
            "character_certified_records": sum(
                1 for record in resolved_records if record["character_certified"]
            ),
            "desired_q1_records": len(desired_q1),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "resolved_records": resolved_records,
        "filtered_candidate_records": filtered_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Known-Line Resolution",
        "",
        f"Batch: `{report['batch']}`",
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
            f"`{record['label']}` from "
            f"`{record['source_window']}/{record['source_filtered_label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"filled `{record['radius4_known_line_resolution']['filled_block_count']}`; "
            f"remaining `{record['radius4_known_line_resolution']['unresolved_block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Previously verified line-character probes resolve part of the "
                "selected radius-4 unresolved frontier. Any fully resolved records "
                "are immediately rerun through the 5259-derived mass/proton filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", choices=sorted(BATCH_CONFIGS), default="batch1")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.md"),
    )
    args = parser.parse_args()
    report = build_report(args.batch)
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
