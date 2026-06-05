#!/usr/bin/env python3
"""Apply medium-small E2 resolutions and rerun the phenomenology filter."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

import sympy as sp

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


def exact_monoid_solution(
    *, needed: list[int], generators: list[list[int]]
) -> dict[str, Any]:
    coeffs = sp.symbols(f"n0:{len(generators)}", integer=True, nonnegative=True)
    trace_shift = sp.symbols("trace_shift", integer=True)
    equations = [
        sum(coeffs[index] * generators[index][coord] for index in range(len(generators)))
        - trace_shift
        - needed[coord]
        for coord in range(5)
    ]
    solution = sp.linsolve(equations, (*coeffs, trace_shift))
    tuples = []
    has_nonnegative_integer_solution = False
    for item in solution:
        values = [sp.simplify(value) for value in item]
        tuples.append([str(value) for value in values])
        if all(value.is_integer for value in values) and all(value >= 0 for value in values[:-1]):
            has_nonnegative_integer_solution = True
    return {
        "solution_tuples": tuples,
        "has_nonnegative_integer_solution": has_nonnegative_integer_solution,
    }


def apply_exact_monoid_obstruction_override(record: dict[str, Any]) -> None:
    if (
        record["classification"]["status"] != "no_certified_triplet_mass_operator_found"
        or record["singlet_moduli_inventory"] is None
        or record["mass_operator_table"] is None
    ):
        return
    certified_labels = set(
        record["singlet_moduli_inventory"]["certified_h1_singlet_charge_labels"]
    )
    certified = [
        item
        for item in record["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]
        if item["charge"]["label"] in certified_labels and item["h1_dimension"] > 0
    ]
    labels = [item["charge"]["label"] for item in certified]
    generators = [item["charge"]["coefficients"] for item in certified]
    entries = []
    for item in record["mass_operator_table"]:
        solution = exact_monoid_solution(
            needed=item["needed_singlet_charge"]["coefficients"],
            generators=generators,
        )
        entries.append(
            {
                "fivebar": item["fivebar"],
                "five": item["five"],
                "needed_singlet_charge": item["needed_singlet_charge"],
                "certified_singlet_generator_labels": labels,
                "certified_singlet_generator_coefficients": generators,
                "exact_solution": solution,
                "certified_singlet_monoid_obstructed": not solution[
                    "has_nonnegative_integer_solution"
                ],
            }
        )
    audit = {
        "method": "exact_nonnegative_linear_charge_cone_check",
        "mass_entries": entries,
        "all_mass_entries_monoid_obstructed": all(
            item["certified_singlet_monoid_obstructed"] for item in entries
        ),
    }
    record["certified_singlet_monoid_mass_audit"] = audit
    if audit["all_mass_entries_monoid_obstructed"]:
        record["classification"] = {
            "category": "phenomenologically obstructed",
            "status": "no_triplet_mass_in_certified_singlet_monoid",
            "reason": (
                "no certified H1 singlet monomial can neutralize the triplet mass "
                "charges; exact nonnegative charge-cone solutions require negative "
                "certified-singlet generator coefficients"
            ),
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


def apply_e2_resolutions(
    characters: dict[str, Any], actuals: dict[tuple[int, ...], dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            line = tuple(cert["line_bundle"])
            if not cert["actual_character_computed"] and line in actuals:
                cert["actual"] = copy.deepcopy(actuals[line])
                cert["method"] = "radius3_medium_small_e2_probe"
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
                        "reason": "no_medium_small_e2_resolution_for_this_line",
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
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json")
    probe = load_json(REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    actuals = {tuple(record["line_bundle"]): record["actual"] for record in probe["records"]}
    medium_items = [
        record
        for record in audit["records"]
        if record["audit"].get("priority_bucket") == "medium_priority_small_map_backlog"
    ]
    rank_resolved_records = []
    filtered_records = []
    for item in medium_items:
        _, certified, source_index = load_candidate(item["window"], item["label"])
        characters, resolution = apply_e2_resolutions(certified["characters"], actuals)
        resolved = copy.deepcopy(certified)
        resolved["characters"] = characters
        resolved["radius3_medium_small_resolution"] = resolution
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
            label=f"{item['window']}_{item['label']}_medium_small_rank_resolved",
            record=resolved,
            conf=conf,
        )
        filtered["source_window"] = item["window"]
        filtered["source_filtered_label"] = item["label"]
        filtered["source_radius2_record"] = item["source_radius2_record"]
        filtered["radius3_medium_small_resolution"] = resolution
        if resolved["character_certified"]:
            apply_monoid_obstruction_override(filtered)
            apply_exact_monoid_obstruction_override(filtered)
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
        "imports_verified_probe": gate(
            probe["all_gates_pass"],
            str(REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.json"),
            "rank-resolved classifier imports the verified medium-small E2 probe",
        ),
        "all_medium_small_records_attempted": gate(
            len(medium_items) == 6
            and len(rank_resolved_records) == 6
            and len(filtered_records) == 6,
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "all six medium-priority small-map records were attempted",
        ),
        "all_missing_blocks_filled": gate(
            sum(record["radius3_medium_small_resolution"]["filled_block_count"] for record in rank_resolved_records)
            == 12
            and sum(record["radius3_medium_small_resolution"]["unresolved_block_count"] for record in rank_resolved_records)
            == 0
            and all(record["character_certified"] for record in rank_resolved_records),
            "medium-small character resolutions",
            "all twelve missing line blocks were filled and all six records are character-certified",
        ),
        "no_viable_medium_small_survivor": gate(
            all(record["classification"]["category"] != "viable" for record in filtered_records),
            "medium-small phenomenology filter",
            "no medium-small resolved record is currently viable",
        ),
        "required_sections_exist": gate(
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
            "medium-small filtered certificates",
            "every medium-small filtered record emits the required deliverable sections",
        ),
    }
    return {
        "scope": "medium-priority radius-3 small-map rank-resolved filter pass",
        "status": "no_viable_candidate_found_after_medium_small_resolution",
        "summary": {
            "records": len(rank_resolved_records),
            "filled_blocks": sum(
                record["radius3_medium_small_resolution"]["filled_block_count"]
                for record in rank_resolved_records
            ),
            "remaining_unresolved_blocks": sum(
                record["radius3_medium_small_resolution"]["unresolved_block_count"]
                for record in rank_resolved_records
            ),
            "character_certified_records": sum(
                1 for record in rank_resolved_records if record["character_certified"]
            ),
            "desired_q1_records": len(desired_q1),
            "viable_count": sum(
                1 for record in filtered_records if record["classification"]["category"] == "viable"
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
        "# Radius-3 Medium-Small Rank-Resolved Records",
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
            f"`{record['label']}`: `{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; prediction "
            f"`{record['spectrum_certificate']['vectorlike_prediction']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_small_rank_resolved.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_small_rank_resolved.md"),
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
