#!/usr/bin/env python3
"""Resolve batch-4 radius-4 character gaps with verified known-line probes."""

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

from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    apply_monoid_obstruction_override,
    prediction_from_characters,
)
from build_phenomenology_guided_q1_radius4_known_line_resolved import (  # noqa: E402
    apply_known_line_resolutions,
    gate,
    load_json,
    load_verified_actuals,
)

WINDOW_REPORTS = {
    f"window{i}": REPORTS / f"phenomenology_guided_q1_radius4_adjacency_scout_batch4_window{i}.json"
    for i in range(1, 7)
}


def character_gap_items(windows: list[str]) -> list[dict[str, Any]]:
    items = []
    for window in windows:
        report = load_json(WINDOW_REPORTS[window])
        for index, filtered in enumerate(report["filtered_candidate_records"]):
            if filtered["classification"]["status"] != "missing_character_or_charge_level_data":
                continue
            items.append(
                {
                    "window": window,
                    "index": index,
                    "filtered": filtered,
                    "certified": report["certified_records"][index],
                }
            )
    return items


def build_report(windows: list[str]) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    source_reports = {window: load_json(WINDOW_REPORTS[window]) for window in windows}
    actuals, sources, conflicts, imported_reports = load_verified_actuals()
    items = character_gap_items(windows)
    resolved_records = []
    filtered_records = []
    for item in items:
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
                "reason": "verified known-line probes did not cover every missing batch-4 character block",
            }
        else:
            apply_monoid_obstruction_override(filtered)
        filtered_records.append(filtered)

    categories = Counter(record["classification"]["category"] for record in filtered_records)
    statuses = Counter(record["classification"]["status"] for record in filtered_records)
    viable = [record for record in filtered_records if record["classification"]["category"] == "viable"]
    expected = sum(
        report["summary"]["statuses"].get("missing_character_or_charge_level_data", 0)
        for report in source_reports.values()
    )
    gates = {
        "source_windows_verified": gate(
            all(report["all_gates_pass"] for report in source_reports.values())
            and expected == len(items),
            ", ".join(str(WINDOW_REPORTS[window]) for window in windows),
            "batch-4 known-line pass starts from verified scout windows",
        ),
        "verified_probe_actuals_imported": gate(
            len(imported_reports) == 7 and len(actuals) >= 70,
            ", ".join(imported_reports),
            "known-line actuals are imported from the verified probe library",
        ),
        "all_character_gap_records_attempted": gate(
            len(items) == len(filtered_records) == expected,
            "batch-4 character-gap records",
            "all selected batch-4 character-gap records were attempted",
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
            "batch-4 known-line filtered records",
            "every attempted candidate has the required deliverable sections",
        ),
        "viable_count_consistent": gate(
            len(viable)
            == sum(1 for record in filtered_records if record["classification"]["category"] == "viable"),
            "batch-4 known-line filtered records",
            "summary viable count matches per-record classifications",
        ),
    }
    return {
        "scope": "known-line resolution pass over batch-4 radius-4 character-gap candidates",
        "batch": "batch4",
        "windows": windows,
        "status": "viable_candidate_found_after_known_line_resolution"
        if viable
        else "no_viable_candidate_found_after_known_line_resolution",
        "known_line_sources": {
            "imported_reports": imported_reports,
            "unique_actual_line_bundles": len(actuals),
            "conflicts": conflicts,
        },
        "summary": {
            "attempted_character_gap_records": len(filtered_records),
            "filled_blocks": sum(r["radius4_known_line_resolution"]["filled_block_count"] for r in resolved_records),
            "remaining_unresolved_blocks": sum(r["radius4_known_line_resolution"]["unresolved_block_count"] for r in resolved_records),
            "incompatible_known_actuals": sum(r["radius4_known_line_resolution"]["incompatible_known_actual_count"] for r in resolved_records),
            "character_certified_records": sum(1 for r in resolved_records if r["character_certified"]),
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
        "# Radius-4 Batch-4 Known-Line Resolution",
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
            f"- `{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"`{record['classification']['category']}` / `{record['classification']['status']}`; "
            f"filled `{record['radius4_known_line_resolution']['filled_block_count']}`; "
            f"remaining `{record['radius4_known_line_resolution']['unresolved_block_count']}`; "
            f"incompatible `{record['radius4_known_line_resolution']['incompatible_known_actual_count']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", nargs="+", choices=sorted(WINDOW_REPORTS), default=sorted(WINDOW_REPORTS))
    parser.add_argument("--json-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved.json"))
    parser.add_argument("--md-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved.md"))
    args = parser.parse_args()
    report = build_report(args.windows)
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
