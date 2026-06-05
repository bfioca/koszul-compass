#!/usr/bin/env python3
"""Enhanced two-term character certification for radius-2 q=1 backlog records."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    add_rep,
    representation_record,
    sector_record,
    subtract_rep,
)
from build_phenomenology_filter_report import (  # noqa: E402
    candidate_certificate_from_5259_record,
)

WINDOW_REPORTS = {
    "window1": REPORTS / "phenomenology_guided_q1_radius2_pilot.json",
    "window2": REPORTS / "phenomenology_guided_q1_radius2_pilot_window2.json",
    "window3": REPORTS / "phenomenology_guided_q1_radius2_pilot_window3.json",
    "window4": REPORTS / "phenomenology_guided_q1_radius2_pilot_window4.json",
}
SECTOR_TARGET_KEYS = {
    "V": ["H1"],
    "V_dual": ["H2"],
    "wedge2_V": ["H1", "H2"],
    "wedge2_V_dual": ["H1", "H2"],
}
SECTOR_LABELS = {
    "V": "V",
    "V_dual": "V*",
    "wedge2_V": "wedge2 V",
    "wedge2_V_dual": "wedge2 V*",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep_from_source_total(item: dict[str, Any]) -> dict[str, Any]:
    return representation_record(item["dimension"], item["nonidentity_trace"])


def nonzero_degrees(cohomology: list[int]) -> list[int]:
    return [degree for degree, value in enumerate(cohomology) if value]


def forced_two_term_actual(cert: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Infer a character when a two-term equivariant map has forced rank."""

    source_totals = {int(key): value for key, value in cert["source_totals"].items()}
    if len(source_totals) != 2:
        return None, "not_two_term"
    degrees = sorted(source_totals)
    if degrees[1] != degrees[0] + 1:
        return None, "not_adjacent_two_term"
    cohomology = cert["cohomology"]
    nonzero = nonzero_degrees(cohomology)
    if len(nonzero) != 1:
        return None, "not_single_nonzero_cohomology_degree"

    low, high = degrees
    low_rep = rep_from_source_total(source_totals[low])
    high_rep = rep_from_source_total(source_totals[high])
    degree = nonzero[0]
    dimension = cohomology[degree]
    if degree == low and dimension == low_rep["dimension"] - high_rep["dimension"]:
        return (
            {f"H{degree}": subtract_rep(low_rep, high_rep)},
            "two_term_dimension_forced_surjective_map",
        )
    if degree == high and dimension == high_rep["dimension"] - low_rep["dimension"]:
        return (
            {f"H{degree}": subtract_rep(high_rep, low_rep)},
            "two_term_dimension_forced_injective_map",
        )
    return None, "two_term_dimensions_do_not_force_rank"


def enhance_characters(characters: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    enhanced = copy.deepcopy(characters)
    filled_blocks = []
    unresolved_blocks = []
    for sector_key, sector in enhanced.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            actual, method = forced_two_term_actual(cert)
            if actual is None:
                unresolved_blocks.append(
                    {
                        "sector": sector_key,
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "source_total_dimensions": {
                            key: value["dimension"]
                            for key, value in sorted(cert["source_totals"].items())
                        },
                        "reason": method,
                    }
                )
                continue
            cert["actual"] = actual
            cert["method"] = method
            cert["actual_character_computed"] = True
            filled_blocks.append(
                {
                    "sector": sector_key,
                    "summand_index": cert.get("summand_index"),
                    "summand_pair": cert.get("summand_pair"),
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "filled_degree_keys": sorted(actual),
                    "method": method,
                    "actual": actual,
                }
            )

    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = enhanced[sector_key]
        enhanced[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return enhanced, {
        "filled_blocks": filled_blocks,
        "unresolved_blocks": unresolved_blocks,
        "filled_block_count": len(filled_blocks),
        "unresolved_block_count": len(unresolved_blocks),
    }


def prediction_from_characters(characters: dict[str, Any]) -> dict[str, Any]:
    h1_wedge = characters["wedge2_V"]["cohomology_characters"]["H1"]
    h2_wedge = characters["wedge2_V"]["cohomology_characters"]["H2"]
    h1_regular = h1_wedge["regular_multiplicity"]
    h2_regular = h2_wedge["regular_multiplicity"]
    return {
        "regular_character_rule_applies": h1_regular is not None
        and h2_regular is not None,
        "h1_wedge2_regular_multiplicity": h1_regular,
        "h2_wedge2_regular_multiplicity": h2_regular,
        "colored_triplet_vectorlike_pairs": h2_regular,
        "electroweak_doublet_vectorlike_pairs": h2_regular,
        "net_families": (
            h1_regular - h2_regular
            if h1_regular is not None and h2_regular is not None
            else None
        ),
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


def certified_singlet_monoid_mass_audit(record: dict[str, Any]) -> dict[str, Any] | None:
    if (
        record["classification"]["status"] != "no_certified_triplet_mass_operator_found"
        or record["singlet_moduli_inventory"] is None
        or record["mass_operator_table"] is None
    ):
        return None
    certified_labels = set(
        record["singlet_moduli_inventory"]["certified_h1_singlet_charge_labels"]
    )
    certified_charges = [
        item["charge"]["coefficients"]
        for item in record["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]
        if item["charge"]["label"] in certified_labels and item["h1_dimension"] > 0
    ]
    entries = []
    for item in record["mass_operator_table"]:
        support = positive_support_obstructions(
            needed=item["needed_singlet_charge"]["coefficients"],
            certified_singlet_charges=certified_charges,
        )
        entries.append(
            {
                "fivebar": item["fivebar"],
                "five": item["five"],
                "needed_singlet_charge": item["needed_singlet_charge"],
                "positive_support_obstructions": support,
                "certified_singlet_monoid_obstructed": bool(support),
            }
        )
    return {
        "mass_entries": entries,
        "all_mass_entries_monoid_obstructed": all(
            item["certified_singlet_monoid_obstructed"] for item in entries
        ),
    }


def apply_monoid_obstruction_override(record: dict[str, Any]) -> None:
    audit = certified_singlet_monoid_mass_audit(record)
    if audit is None:
        return
    record["certified_singlet_monoid_mass_audit"] = audit
    if audit["all_mass_entries_monoid_obstructed"]:
        record["classification"] = {
            "category": "phenomenologically obstructed",
            "status": "no_triplet_mass_in_certified_singlet_monoid",
            "reason": (
                "no certified H1 singlet monomial can neutralize the triplet mass "
                "charge because the certified singlet generators lack required "
                "positive charge support"
            ),
        }


def load_backlog_certified_records() -> list[dict[str, Any]]:
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json")
    records = []
    for item in audit["records"]:
        if item["audit"]["kind"] != "missing_character_or_charge_level_data":
            continue
        window_report = load_json(WINDOW_REPORTS[item["window"]])
        certified = copy.deepcopy(window_report["certified_records"][item["window_record_index"]])
        certified["source_window"] = item["window"]
        certified["source_filtered_label"] = item["label"]
        certified["source_report"] = str(WINDOW_REPORTS[item["window"]])
        records.append(certified)
    return records


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    input_records = load_backlog_certified_records()
    enhanced_records = []
    filtered_records = []
    for index, record in enumerate(input_records):
        characters, enhancement = enhance_characters(record["characters"])
        enhanced = copy.deepcopy(record)
        enhanced["label"] = f"radius2_enhanced_backlog_{index}"
        enhanced["characters"] = characters
        enhanced["character_certified"] = all(
            sector["all_characters_computed"] for sector in characters.values()
        )
        enhanced["vectorlike_pair_prediction"] = prediction_from_characters(characters)
        enhanced["enhancement"] = enhancement
        enhanced_records.append(enhanced)

        filtered = candidate_certificate_from_5259_record(
            label=f"radius2_enhanced_filtered_{index}",
            record=enhanced,
            conf=conf,
        )
        filtered["source_window"] = record["source_window"]
        filtered["source_filtered_label"] = record["source_filtered_label"]
        filtered["enhancement"] = enhancement
        if not enhanced["character_certified"]:
            filtered["classification"] = {
                "category": "unresolved",
                "status": "enhanced_character_certificate_still_incomplete",
                "reason": (
                    "two-term dimension-forced enhancement did not resolve all "
                    "nonzero character blocks"
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
    viable = [
        record
        for record in filtered_records
        if record["classification"]["category"] == "viable"
    ]
    newly_certified = [
        record for record in enhanced_records if record["character_certified"]
    ]
    desired_q1 = [
        record
        for record in enhanced_records
        if record["vectorlike_pair_prediction"]["regular_character_rule_applies"]
        and record["vectorlike_pair_prediction"]["net_families"] == 3
        and record["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"] == 1
    ]
    gates = {
        "backlog_records_loaded": gate(
            len(input_records) == 10,
            str(REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json"),
            "enhancement starts from the ten character-backlog records",
        ),
        "two_term_blocks_filled": gate(
            sum(record["enhancement"]["filled_block_count"] for record in enhanced_records)
            > 0,
            "dimension-forced two-term character enhancement",
            "at least one missing character block was filled by the conservative enhancement",
        ),
        "filter_reran_for_every_record": gate(
            len(filtered_records) == len(enhanced_records) == 10,
            "enhanced records",
            "every enhanced backlog record was resubmitted to the phenomenology filter",
        ),
    }
    return {
        "scope": "two-term enhanced character-certification attempt for radius-2 q=1 backlog",
        "status": "viable_candidate_found"
        if viable
        else "no_viable_candidate_found_after_two_term_enhancement",
        "summary": {
            "input_backlog_records": len(input_records),
            "newly_character_certified_records": len(newly_certified),
            "desired_q1_after_enhancement": len(desired_q1),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "filled_block_count": sum(
                record["enhancement"]["filled_block_count"]
                for record in enhanced_records
            ),
            "remaining_unresolved_block_count": sum(
                record["enhancement"]["unresolved_block_count"]
                for record in enhanced_records
            ),
        },
        "enhanced_records": enhanced_records,
        "filtered_candidate_records": filtered_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Enhanced Character Backlog",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- input backlog records: `{report['summary']['input_backlog_records']}`",
        f"- newly character-certified records: `{report['summary']['newly_character_certified_records']}`",
        f"- desired q=1 after enhancement: `{report['summary']['desired_q1_after_enhancement']}`",
        f"- viable count: `{report['summary']['viable_count']}`",
        f"- filled blocks: `{report['summary']['filled_block_count']}`",
        f"- remaining unresolved blocks: `{report['summary']['remaining_unresolved_block_count']}`",
        f"- categories: `{report['summary']['categories']}`",
        f"- statuses: `{report['summary']['statuses']}`",
        "",
        "## Candidate Classifications",
        "",
    ]
    for record in report["filtered_candidate_records"]:
        prediction = record["spectrum_certificate"]["vectorlike_prediction"]
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"prediction `{prediction}`; "
            f"filled `{record['enhancement']['filled_block_count']}`, "
            f"remaining `{record['enhancement']['unresolved_block_count']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"newly_character_certified={report['summary']['newly_character_certified_records']}")
    print(f"desired_q1={report['summary']['desired_q1_after_enhancement']}")
    print(f"viable_count={report['summary']['viable_count']}")
    print(f"filled_blocks={report['summary']['filled_block_count']}")
    print(f"remaining_unresolved_blocks={report['summary']['remaining_unresolved_block_count']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
