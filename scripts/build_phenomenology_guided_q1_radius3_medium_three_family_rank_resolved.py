#!/usr/bin/env python3
"""Apply the medium-three-family E2 resolution and rerun the filter."""

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

WINDOW_REPORTS = {
    "window1": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout.json",
    "window2": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window2.json",
    "window3": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window3.json",
    "window4": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window4.json",
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


def apply_e2_resolution(characters: dict[str, Any], probe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    actuals = {tuple(record["line_bundle"]): record["actual"] for record in probe["records"]}
    resolved = copy.deepcopy(characters)
    filled = []
    unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            line = tuple(cert["line_bundle"])
            if not cert["actual_character_computed"] and line in actuals:
                cert["actual"] = copy.deepcopy(actuals[line])
                cert["method"] = "radius3_medium_three_family_e2_probe"
                cert["actual_character_computed"] = True
                filled.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "actual": cert["actual"],
                    }
                )
            elif not cert["actual_character_computed"] and any(cert["cohomology"]):
                unresolved.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "no_medium_three_family_e2_resolution_for_this_line",
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
        "filled_block_count": len(filled),
        "unresolved_block_count": len(unresolved),
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    probe = load_json(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    target = probe["target_record"]
    _, certified, source_index = load_candidate(target["window"], target["label"])
    characters, resolution = apply_e2_resolution(certified["characters"], probe)
    resolved = copy.deepcopy(certified)
    resolved["characters"] = characters
    resolved["radius3_medium_three_family_resolution"] = resolution
    resolved["character_certified"] = all(
        sector["all_characters_computed"] for sector in characters.values()
    )
    resolved["vectorlike_pair_prediction"] = prediction_from_characters(characters)
    resolved["source_window"] = target["window"]
    resolved["source_filtered_label"] = target["label"]
    resolved["source_filtered_index"] = source_index
    resolved["source_radius2_record"] = target["source_radius2_record"]
    filtered = candidate_certificate_from_5259_record(
        label=f"{target['window']}_{target['label']}_medium_three_family_rank_resolved",
        record=resolved,
        conf=conf,
    )
    filtered["source_window"] = target["window"]
    filtered["source_filtered_label"] = target["label"]
    filtered["source_radius2_record"] = target["source_radius2_record"]
    filtered["radius3_medium_three_family_resolution"] = resolution
    if resolved["character_certified"]:
        apply_monoid_obstruction_override(filtered)
    gates = {
        "imports_verified_probe": gate(
            probe["all_gates_pass"],
            str(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe.json"),
            "rank-resolved classifier imports the verified medium-three-family E2 probe",
        ),
        "all_missing_blocks_filled": gate(
            resolution["filled_block_count"] == 4
            and resolution["unresolved_block_count"] == 0
            and resolved["character_certified"],
            "medium-three-family character resolution",
            "all four missing line blocks were filled and the record is character-certified",
        ),
        "spectrum_rejected_not_q1": gate(
            filtered["classification"]["category"] == "phenomenologically obstructed"
            and filtered["classification"]["status"] == "rejected_spectrum_signature_not_q1_three_family"
            and not filtered["spectrum_certificate"]["desired_q1_three_family_signature"],
            "phenomenology filter classification",
            "resolved nonregular characters reject this three-family near-miss before q=1 mass/proton filtering",
        ),
        "required_sections_exist": gate(
            {
                "spectrum_certificate",
                "character_certificate",
                "mass_operator_table",
                "proton_decay_operator_table",
                "classification",
            }.issubset(filtered),
            "medium-three-family filtered certificate",
            "the filtered candidate emits the required deliverable sections",
        ),
    }
    return {
        "scope": "medium-priority radius-3 three-family rank-resolved filter pass",
        "status": "medium_three_family_record_rejected_after_character_resolution",
        "summary": {
            "records": 1,
            "filled_blocks": resolution["filled_block_count"],
            "remaining_unresolved_blocks": resolution["unresolved_block_count"],
            "character_certified_records": int(resolved["character_certified"]),
            "desired_q1_records": int(
                filtered["spectrum_certificate"]["desired_q1_three_family_signature"]
            ),
            "viable_count": int(filtered["classification"]["category"] == "viable"),
            "categories": {filtered["classification"]["category"]: 1},
            "statuses": {filtered["classification"]["status"]: 1},
        },
        "rank_resolved_records": [resolved],
        "filtered_candidate_records": [filtered],
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    record = report["filtered_candidate_records"][0]
    lines = [
        "# Radius-3 Medium Three-Family Rank-Resolved Record",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Candidate",
            "",
            (
                f"- `{record['label']}`: `{record['classification']['category']}` / "
                f"`{record['classification']['status']}`; prediction "
                f"`{record['spectrum_certificate']['vectorlike_prediction']}`"
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_rank_resolved.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_rank_resolved.md"),
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
