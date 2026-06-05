#!/usr/bin/env python3
"""Bounded branch analysis for radius-5 known-line-incomplete q=1 records."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    representation_record,
    sector_record,
)
from build_phenomenology_filter_report import (  # noqa: E402
    certified_h1_singlets,
    classify_from_tables,
    enumerate_singlet_monomials,
    find_mass_operator_table,
    find_proton_decay_table,
    is_desired_q1_signature,
)
from build_cicy5259_lead_phenomenology_dossier import (  # noqa: E402
    charged_matter_inventory,
    singlet_sector_records,
)
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def possible_actuals_for_cohomology(cohomology: list[int]) -> list[dict[str, Any]]:
    degree_options = []
    for degree, dimension in enumerate(cohomology):
        if dimension == 0:
            continue
        traces = list(range(-dimension, dimension + 1, 2))
        degree_options.append(
            [(f"H{degree}", representation_record(dimension, trace)) for trace in traces]
        )
    return [{key: rep for key, rep in combo} for combo in itertools.product(*degree_options)]


def unresolved_certs(characters: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for sector_key, sector in characters.items():
        for cert_index, cert in enumerate(sector["line_certificates"]):
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            blocks.append(
                {
                    "sector_key": sector_key,
                    "cert_index": cert_index,
                    "summand_index": cert.get("summand_index"),
                    "summand_pair": cert.get("summand_pair"),
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "actual_options": possible_actuals_for_cohomology(cert["cohomology"]),
                }
            )
    return blocks


def complete_characters_with_branch(
    characters: dict[str, Any],
    blocks: list[dict[str, Any]],
    branch_actuals: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    completed = copy.deepcopy(characters)
    for block, actual in zip(blocks, branch_actuals):
        cert = completed[block["sector_key"]]["line_certificates"][block["cert_index"]]
        cert["actual"] = copy.deepcopy(actual)
        cert["method"] = "radius5_dimension_compatible_branch_completion"
        cert["actual_character_computed"] = True
    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = completed[sector_key]
        completed[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return completed


def branch_space_size(blocks: list[dict[str, Any]]) -> int:
    total = 1
    for block in blocks:
        total *= len(block["actual_options"])
    return total


def certificate_from_completed_record(
    *,
    label: str,
    record: dict[str, Any],
    conf: list[list[int]],
    singlet_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    matrix_key = json.dumps(record["matrix"], sort_keys=True)
    if matrix_key not in singlet_cache:
        singlet_records = singlet_sector_records(conf=conf, matrix=record["matrix"])
        h1_singlets = certified_h1_singlets(singlet_records)
        singlet_cache[matrix_key] = {
            "inventory": {
                "all_nonzero_ext1_line_sectors": singlet_records,
                "certified_h1_singlet_charge_labels": sorted(h1_singlets),
            },
            "monomials": enumerate_singlet_monomials(h1_singlets, max_degree=2),
        }
    inventory = charged_matter_inventory(record)
    mass_table = find_mass_operator_table(
        inventory=inventory,
        singlet_monomials=singlet_cache[matrix_key]["monomials"],
    )
    proton_table = find_proton_decay_table(inventory)
    classification = classify_from_tables(
        desired_signature=True,
        character_certified=record["character_certified"],
        mass_table=mass_table,
        proton_table=proton_table,
    )
    return {
        "label": label,
        "source": "radius5_known_line_incomplete_branch_completion",
        "cicy_route": "5259/7914",
        "matrix": record["matrix"],
        "spectrum_certificate": {
            "cohomology": record["cohomology"],
            "vectorlike_prediction": record["vectorlike_pair_prediction"],
            "desired_q1_three_family_signature": True,
        },
        "character_certificate": {
            "character_certified": record["character_certified"],
            "characters": record["characters"],
        },
        "charged_matter_inventory": inventory,
        "singlet_moduli_inventory": singlet_cache[matrix_key]["inventory"],
        "mass_operator_table": mass_table,
        "proton_decay_operator_table": proton_table,
        "classification": classification,
    }


def build_report(*, max_branches_per_record: int, scout_json: Path) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scout = load_json(scout_json)
    conf = split["full_picard_presentation_7914"]["conf"]
    expected_missing = scout["summary"]["statuses"].get(
        "missing_character_or_charge_level_data", 0
    )
    unresolved_records = []
    for filtered, certified in zip(
        scout["filtered_candidate_records"], scout["certified_records"]
    ):
        if filtered["classification"]["status"] != "missing_character_or_charge_level_data":
            continue
        enriched = copy.deepcopy(certified)
        enriched["radius5_filtered_label"] = filtered["label"]
        enriched["radius5_source_id"] = filtered["radius5_source_id"]
        enriched["radius5_source_status"] = filtered["radius5_source_status"]
        enriched["radius5_new_move"] = filtered["radius5_new_move"]
        unresolved_records.append(enriched)

    record_reports = []
    skipped = []
    branch_summaries = []
    desired_q1_certificates = []
    singlet_cache: dict[str, dict[str, Any]] = {}

    for record in unresolved_records:
        blocks = unresolved_certs(record["characters"])
        size = branch_space_size(blocks)
        block_summary = [
            {
                "sector": block["sector_key"],
                "summand_index": block["summand_index"],
                "summand_pair": block["summand_pair"],
                "line_bundle": block["line_bundle"],
                "cohomology": block["cohomology"],
                "option_count": len(block["actual_options"]),
            }
            for block in blocks
        ]
        label = record["radius5_filtered_label"]
        if size > max_branches_per_record:
            skipped.append(
                {
                    "label": label,
                    "branch_space_size": size,
                    "unresolved_blocks": block_summary,
                    "reason": "branch_space_exceeds_configured_bound",
                }
            )
            record_reports.append(
                {
                    "label": label,
                    "branch_space_size": size,
                    "branches_evaluated": 0,
                    "skipped": True,
                    "unresolved_blocks": block_summary,
                }
            )
            continue

        categories: Counter[str] = Counter()
        statuses: Counter[str] = Counter()
        desired_count = 0
        viable_count = 0
        option_lists = [block["actual_options"] for block in blocks]
        for branch_index, branch_actuals in enumerate(itertools.product(*option_lists)):
            completed_characters = complete_characters_with_branch(
                record["characters"], blocks, branch_actuals
            )
            completed = copy.deepcopy(record)
            completed["characters"] = completed_characters
            completed["character_certified"] = True
            completed["vectorlike_pair_prediction"] = prediction_from_characters(
                completed_characters
            )
            completed["radius5_unresolved_branch_completion"] = {
                "branch_index": branch_index,
                "filled_blocks": [
                    {
                        "sector": block["sector_key"],
                        "summand_index": block["summand_index"],
                        "summand_pair": block["summand_pair"],
                        "line_bundle": block["line_bundle"],
                        "actual": actual,
                    }
                    for block, actual in zip(blocks, branch_actuals)
                ],
            }
            branch_label = (
                f"{record['radius5_filtered_label']}_branch_{branch_index}"
            )
            prediction = completed["vectorlike_pair_prediction"]
            desired_q1 = is_desired_q1_signature(prediction)
            if desired_q1:
                filtered = certificate_from_completed_record(
                    label=branch_label,
                    record=completed,
                    conf=conf,
                    singlet_cache=singlet_cache,
                )
                filtered["radius5_source_id"] = record["radius5_source_id"]
                filtered["radius5_source_status"] = record["radius5_source_status"]
                filtered["radius5_filtered_label"] = record["radius5_filtered_label"]
                filtered["radius5_unresolved_branch_completion"] = completed[
                    "radius5_unresolved_branch_completion"
                ]
                apply_monoid_obstruction_override(filtered)
                classification = filtered["classification"]
                desired_q1_certificates.append(filtered)
            else:
                classification = {
                    "category": "phenomenologically obstructed",
                    "status": "rejected_spectrum_signature_not_q1_three_family",
                    "reason": (
                        "candidate does not have three families plus exactly one "
                        "vectorlike 5/5bar pair after Wilson-line projection"
                    ),
                }

            category = classification["category"]
            status = classification["status"]
            categories[category] += 1
            statuses[status] += 1
            if desired_q1:
                desired_count += 1
            if category == "viable":
                viable_count += 1
            branch_summaries.append(
                {
                    "label": branch_label,
                    "source": label,
                    "desired_q1": desired_q1,
                    "prediction": prediction,
                    "classification": classification,
                }
            )

        record_reports.append(
            {
                "label": label,
                "branch_space_size": size,
                "branches_evaluated": size,
                "skipped": False,
                "unresolved_blocks": block_summary,
                "desired_q1_branches": desired_count,
                "viable_branches": viable_count,
                "categories": dict(sorted(categories.items())),
                "statuses": dict(sorted(statuses.items())),
            }
        )

    aggregate_categories = Counter(item["classification"]["category"] for item in branch_summaries)
    aggregate_statuses = Counter(item["classification"]["status"] for item in branch_summaries)
    viable_count = sum(1 for item in branch_summaries if item["classification"]["category"] == "viable")
    status = (
        "viable_branch_found_in_radius5_bounded_branch_analysis"
        if viable_count
        else "no_viable_branch_found_in_radius5_bounded_branch_analysis"
    )
    gates = {
        "imports_radius5_known_line_report": gate(
            scout["all_gates_pass"]
            and expected_missing >= 0,
            str(scout_json),
            "branch analysis starts from the verified radius-5 scout report",
        ),
        "all_radius5_incomplete_records_considered": gate(
            len(unresolved_records) == len(record_reports) == expected_missing,
            str(scout_json),
            "all radius-5 missing-character records are included",
        ),
        "bounded_records_evaluated": gate(
            all(
                item["branch_space_size"] <= max_branches_per_record
                for item in record_reports
                if not item["skipped"]
            ),
            "dimension-compatible radius-5 branch enumeration",
            "every evaluated record respects the configured branch bound",
        ),
        "branch_accounting_matches": gate(
            sum(item.get("branches_evaluated", 0) for item in record_reports)
            == len(branch_summaries),
            "radius-5 branch summaries",
            "one branch summary is emitted for every evaluated branch",
        ),
        "desired_q1_certificates_have_tables": gate(
            all(
                item["spectrum_certificate"]["desired_q1_three_family_signature"]
                and item["character_certificate"]["character_certified"]
                and item["mass_operator_table"] is not None
                and item["proton_decay_operator_table"] is not None
                for item in desired_q1_certificates
            ),
            "radius-5 desired-q1 branch certificates",
            "all desired-q1 branches carry spectrum, character, mass, and proton tables",
        ),
    }
    return {
        "scope": "bounded dimension-compatible branch analysis for radius-5 missing-character records",
        "status": status,
        "parameters": {
            "max_branches_per_record": max_branches_per_record,
            "scout_json": str(scout_json),
        },
        "summary": {
            "unresolved_records": len(unresolved_records),
            "records_evaluated": sum(1 for item in record_reports if not item["skipped"]),
            "records_skipped": len(skipped),
            "branches_evaluated": len(branch_summaries),
            "desired_q1_branches": len(desired_q1_certificates),
            "viable_branches": viable_count,
            "categories": dict(sorted(aggregate_categories.items())),
            "statuses": dict(sorted(aggregate_statuses.items())),
        },
        "record_branch_reports": record_reports,
        "skipped_records": skipped,
        "branch_summaries": branch_summaries,
        "desired_q1_branch_candidate_records": desired_q1_certificates,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-5 Branch Analysis",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Records", ""])
    for item in report["record_branch_reports"]:
        if item["skipped"]:
            lines.append(
                f"- `{item['label']}` skipped; branch space `{item['branch_space_size']}`"
            )
        else:
            lines.append(
                f"- `{item['label']}`: branches `{item['branches_evaluated']}`, "
                f"desired-q1 `{item['desired_q1_branches']}`, "
                f"viable `{item['viable_branches']}`, statuses `{item['statuses']}`"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This radius-5 pass enumerates every dimension-compatible character "
                "completion within the configured bound and emits full candidate "
                "tables for every branch that reaches the target q=1 spectrum. "
                "Non-q1 branches are retained as compact classification summaries."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-branches-per-record", type=int, default=3000)
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_branch_analysis.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_branch_analysis.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_branches_per_record=args.max_branches_per_record,
        scout_json=Path(args.scout_json),
    )
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
