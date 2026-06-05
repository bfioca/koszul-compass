#!/usr/bin/env python3
"""Bounded branch analysis for radius-6 DT-targeted missing-character records."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
import itertools
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_lead_phenomenology_dossier import (  # noqa: E402
    charged_matter_inventory,
    singlet_sector_records,
)
from build_cicy5259_quotient_wilson_line_report import sector_record  # noqa: E402
from build_phenomenology_filter_report import (  # noqa: E402
    certified_h1_singlets,
    classify_from_tables,
    enumerate_singlet_monomials,
    find_mass_operator_table,
    find_proton_decay_table,
    is_desired_q1_signature,
)
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)
from build_phenomenology_guided_q1_radius5_branch_analysis import (  # noqa: E402
    branch_space_size,
    complete_characters_with_branch,
    unresolved_certs,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


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
        "source": "radius6_dt_targeted_dimension_compatible_branch_completion",
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


def recompute_sector_records(characters: dict[str, Any]) -> dict[str, Any]:
    completed = copy.deepcopy(characters)
    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = completed[sector_key]
        completed[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return completed


def radius6_source_metadata(filtered: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_label": filtered.get(
            "radius6_source_label",
            filtered.get("radius6_broad_source_id", "unknown_radius6_source"),
        ),
        "source_file": filtered.get(
            "radius6_source_file",
            filtered.get("radius6_broad_source_id", "unknown_radius6_source_file"),
        ),
        "move": filtered.get("radius6_move", filtered.get("radius6_broad_move")),
    }


def build_report(
    *,
    max_branches_per_record: int,
    scout_json: Path,
    scout_verification_json: Path,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scout = load_json(scout_json)
    scout_verification = load_json(scout_verification_json)
    conf = split["full_picard_presentation_7914"]["conf"]

    unresolved_records = []
    for filtered, certified in zip(
        scout["filtered_candidate_records"], scout["certified_records"]
    ):
        if filtered["classification"]["status"] != "missing_character_or_charge_level_data":
            continue
        enriched = copy.deepcopy(certified)
        metadata = radius6_source_metadata(filtered)
        enriched["radius6_filtered_label"] = filtered["label"]
        enriched["radius6_source_label"] = metadata["source_label"]
        enriched["radius6_source_file"] = metadata["source_file"]
        enriched["radius6_move"] = metadata["move"]
        unresolved_records.append(enriched)

    record_reports = []
    skipped_records = []
    branch_summaries = []
    desired_q1_branch_candidate_records = []
    singlet_cache: dict[str, dict[str, Any]] = {}

    for record in unresolved_records:
        blocks = unresolved_certs(record["characters"])
        size = branch_space_size(blocks)
        block_summary = [
            {
                "sector": block["sector_key"],
                "summand_index": block.get("summand_index"),
                "summand_pair": block.get("summand_pair"),
                "line_bundle": block["line_bundle"],
                "cohomology": block["cohomology"],
                "option_count": len(block["actual_options"]),
            }
            for block in blocks
        ]
        label = record["radius6_filtered_label"]
        if size > max_branches_per_record:
            skipped_records.append(
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
            completed_characters = recompute_sector_records(completed_characters)
            completed = copy.deepcopy(record)
            completed["characters"] = completed_characters
            completed["character_certified"] = True
            completed["vectorlike_pair_prediction"] = prediction_from_characters(
                completed_characters
            )
            completed["radius6_unresolved_branch_completion"] = {
                "branch_index": branch_index,
                "filled_blocks": [
                    {
                        "sector": block["sector_key"],
                        "summand_index": block.get("summand_index"),
                        "summand_pair": block.get("summand_pair"),
                        "line_bundle": block["line_bundle"],
                        "actual": actual,
                    }
                    for block, actual in zip(blocks, branch_actuals)
                ],
            }
            branch_label = f"{label}_branch_{branch_index}"
            prediction = completed["vectorlike_pair_prediction"]
            desired_q1 = is_desired_q1_signature(prediction)
            if desired_q1:
                filtered = certificate_from_completed_record(
                    label=branch_label,
                    record=completed,
                    conf=conf,
                    singlet_cache=singlet_cache,
                )
                apply_monoid_obstruction_override(filtered)
                filtered["radius6_source_label"] = record["radius6_source_label"]
                filtered["radius6_source_file"] = record["radius6_source_file"]
                filtered["radius6_filtered_label"] = label
                filtered["radius6_unresolved_branch_completion"] = completed[
                    "radius6_unresolved_branch_completion"
                ]
                classification = filtered["classification"]
                desired_q1_branch_candidate_records.append(filtered)
            else:
                classification = {
                    "category": "phenomenologically obstructed",
                    "status": "rejected_spectrum_signature_not_q1_three_family",
                    "reason": "branch completion does not have the target q=1 Wilson-line spectrum",
                }
            categories[classification["category"]] += 1
            statuses[classification["status"]] += 1
            desired_count += int(desired_q1)
            viable_count += int(classification["category"] == "viable")
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

    aggregate_categories = Counter(
        item["classification"]["category"] for item in branch_summaries
    )
    aggregate_statuses = Counter(
        item["classification"]["status"] for item in branch_summaries
    )
    viable_count = sum(
        1
        for item in branch_summaries
        if item["classification"]["category"] == "viable"
    )
    gates = {
        "imports_verified_radius6_scout": gate(
            scout_verification["all_gates_pass"],
            str(scout_verification_json),
            "branch analysis starts from the verified radius6 targeted scout",
        ),
        "all_missing_character_records_considered": gate(
            len(unresolved_records)
            == scout["summary"]["statuses"].get("missing_character_or_charge_level_data", 0),
            str(scout_json),
            "all radius6 missing-character records are included",
        ),
        "branch_accounting_matches": gate(
            sum(item.get("branches_evaluated", 0) for item in record_reports)
            == len(branch_summaries),
            "radius6 branch summaries",
            "one branch summary is emitted for every evaluated branch",
        ),
        "desired_q1_certificates_have_tables": gate(
            all(
                item["spectrum_certificate"]["desired_q1_three_family_signature"]
                and item["character_certificate"]["character_certified"]
                and item["mass_operator_table"] is not None
                and item["proton_decay_operator_table"] is not None
                for item in desired_q1_branch_candidate_records
            ),
            "radius6 desired-q1 branch certificates",
            "all desired q1 branches carry spectrum, character, mass, and proton tables",
        ),
    }
    return {
        "scope": "bounded branch analysis for radius6 DT-targeted missing-character records",
        "status": (
            "viable_branch_found_in_radius6_dt_branch_analysis"
            if viable_count
            else "no_viable_branch_found_in_radius6_dt_branch_analysis"
        ),
        "parameters": {
            "max_branches_per_record": max_branches_per_record,
            "scout_json": str(scout_json),
        },
        "summary": {
            "unresolved_records": len(unresolved_records),
            "records_evaluated": sum(1 for item in record_reports if not item["skipped"]),
            "records_skipped": len(skipped_records),
            "branches_evaluated": len(branch_summaries),
            "desired_q1_branches": len(desired_q1_branch_candidate_records),
            "viable_branches": viable_count,
            "categories": dict(sorted(aggregate_categories.items())),
            "statuses": dict(sorted(aggregate_statuses.items())),
        },
        "record_branch_reports": record_reports,
        "skipped_records": skipped_records,
        "branch_summaries": branch_summaries,
        "desired_q1_branch_candidate_records": desired_q1_branch_candidate_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-6 DT Branch Analysis",
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
                f"desired-q1 `{item['desired_q1_branches']}`, viable "
                f"`{item['viable_branches']}`, statuses `{item['statuses']}`"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-branches-per-record", type=int, default=5000)
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.json"),
    )
    parser.add_argument(
        "--scout-verification-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout_verification.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_branches_per_record=args.max_branches_per_record,
        scout_json=Path(args.scout_json),
        scout_verification_json=Path(args.scout_verification_json),
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
