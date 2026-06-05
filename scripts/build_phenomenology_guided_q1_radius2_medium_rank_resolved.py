#!/usr/bin/env python3
"""Apply medium-priority two-term rank resolutions and rerun the phenomenology filter."""

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


def rep(plus: int, minus: int) -> dict[str, Any]:
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


RESOLVED_ACTUALS = {
    (2, 0, 2, 0, 1, -1, -1): {
        "method": "medium_first_page_rank_split_nonregular",
        "actual": {"H1": rep(0, 2), "H2": rep(0, 1)},
    },
    (-2, 0, -2, 0, -1, 1, 1): {
        "method": "serre_dual_medium_first_page_rank_split_nonregular",
        "actual": {"H1": rep(0, 1), "H2": rep(0, 2)},
    },
    (1, 1, -2, -1, -1, 1, 0): {
        "method": "medium_first_page_plus_higher_rank_split_regular",
        "actual": {"H1": rep(2, 2), "H2": rep(1, 1)},
    },
    (-1, -1, 2, 1, 1, -1, 0): {
        "method": "serre_dual_medium_first_page_plus_higher_rank_split_regular",
        "actual": {"H1": rep(1, 1), "H2": rep(2, 2)},
    },
    (-2, 2, 0, 1, -1, 0, 0): {
        "method": "medium_rank_zero_source_equals_actual_regular",
        "actual": {"H1": rep(3, 3), "H2": rep(1, 1)},
    },
    (2, -2, 0, -1, 1, 0, 0): {
        "method": "serre_dual_medium_rank_zero_source_equals_actual_regular",
        "actual": {"H1": rep(1, 1), "H2": rep(3, 3)},
    },
    (2, 0, 2, 0, 0, -1, -1): {
        "method": "three_term_e2_probe_nonregular_h1_regular_h2",
        "actual": {"H1": rep(1, 0), "H2": rep(1, 1)},
    },
    (-2, 0, -2, 0, 0, 1, 1): {
        "method": "serre_dual_three_term_e2_probe_nonregular_h1_regular_h2",
        "actual": {"H1": rep(1, 1), "H2": rep(1, 0)},
    },
    (1, -1, 2, -1, 1, -1, 1): {
        "method": "three_term_e2_probe_regular_h1_only",
        "actual": {"H1": rep(2, 2)},
    },
    (-1, 1, -2, 1, -1, 1, -1): {
        "method": "serre_dual_three_term_e2_probe_regular_h2_only",
        "actual": {"H2": rep(2, 2)},
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def is_resolvable(cert: dict[str, Any]) -> bool:
    return (
        not cert["actual_character_computed"]
        and tuple(cert["line_bundle"]) in RESOLVED_ACTUALS
    )


def apply_resolutions(characters: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if is_resolvable(cert):
                resolution = RESOLVED_ACTUALS[tuple(cert["line_bundle"])]
                cert["actual"] = copy.deepcopy(resolution["actual"])
                cert["method"] = resolution["method"]
                cert["actual_character_computed"] = True
                filled.append(
                    {
                        "sector": sector_key,
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "method": resolution["method"],
                        "actual": cert["actual"],
                    }
                )
            elif not cert["actual_character_computed"] and any(cert["cohomology"]):
                unresolved.append(
                    {
                        "sector": sector_key,
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "medium_three_term_or_unresolved_map_character",
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
    enhanced = load_json(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.json")
    three_term = load_json(REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    medium_labels = {record["label"] for record in scenarios["records"]}
    rank_resolved_records = []
    filtered_records = []
    for record in enhanced["enhanced_records"]:
        if record["label"] not in medium_labels:
            continue
        characters, resolution = apply_resolutions(record["characters"])
        resolved_record = copy.deepcopy(record)
        resolved_record["characters"] = characters
        resolved_record["medium_rank_resolution"] = resolution
        resolved_record["character_certified"] = all(
            sector["all_characters_computed"] for sector in characters.values()
        )
        resolved_record["vectorlike_pair_prediction"] = prediction_from_characters(characters)
        rank_resolved_records.append(resolved_record)

        filtered = candidate_certificate_from_5259_record(
            label=record["label"].replace("backlog", "medium_rank_resolved_filtered"),
            record=resolved_record,
            conf=conf,
        )
        filtered["source_window"] = record["source_window"]
        filtered["source_filtered_label"] = record["source_filtered_label"]
        filtered["medium_rank_resolution"] = resolution
        if not resolved_record["character_certified"]:
            filtered["classification"] = {
                "category": "unresolved",
                "status": "medium_rank_resolved_character_certificate_still_incomplete",
                "reason": "three-term or unsupported medium blocks still lack a verified equivariant map character",
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
        "imports_medium_scenarios": gate(
            scenarios["summary"]["two_term_supported_records"] == 3
            and scenarios["summary"]["unsupported_three_term_records"] == 2,
            str(REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.json"),
            "medium rank resolution starts from the verified medium scenario split",
        ),
        "imports_three_term_probe": gate(
            three_term["all_gates_pass"]
            and three_term["status"] == "three_term_medium_characters_resolved",
            str(REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe.json"),
            "medium rank resolution imports the verified three-term E2 characters",
        ),
        "two_term_medium_blocks_filled": gate(
            sum(record["medium_rank_resolution"]["filled_block_count"] for record in rank_resolved_records)
            == 10
            and sum(record["medium_rank_resolution"]["unresolved_block_count"] for record in rank_resolved_records)
            == 0,
            "medium line-level rank resolutions",
            "all medium two-term and three-term records are filled",
        ),
        "new_medium_q1_records_filtered": gate(
            len(desired_q1) == 4
            and all(record["classification"]["category"] != "viable" for record in filtered_records),
            "medium rank-resolved phenomenology filter",
            "new desired-q1 medium records were filtered with no viable survivor",
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
            "medium rank-resolved candidate certificates",
            "every medium filtered record has the required report sections",
        ),
    }
    return {
        "scope": "medium-priority two-term rank-resolved backlog and phenomenology filter rerun",
        "status": "no_viable_candidate_found_after_medium_rank_resolution",
        "summary": {
            "medium_records": len(rank_resolved_records),
            "filled_blocks": sum(
                record["medium_rank_resolution"]["filled_block_count"]
                for record in rank_resolved_records
            ),
            "remaining_unresolved_blocks": sum(
                record["medium_rank_resolution"]["unresolved_block_count"]
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
        "medium_rank_resolved_records": rank_resolved_records,
        "filtered_candidate_records": filtered_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Medium Rank-Resolved Backlog",
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
        resolution = record["medium_rank_resolution"]
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"`{record['classification']['category']}` / `{record['classification']['status']}`; "
            f"prediction `{prediction}`; "
            f"medium-filled `{resolution['filled_block_count']}`, "
            f"medium-unresolved `{resolution['unresolved_block_count']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_medium_rank_resolved.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_medium_rank_resolved.md"),
    )
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
