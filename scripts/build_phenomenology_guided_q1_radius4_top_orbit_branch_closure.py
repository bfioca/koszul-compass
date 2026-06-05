#!/usr/bin/env python3
"""Branch-close the highest-demand missing Serre orbit in radius-4 candidates."""

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

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    representation_record,
    sector_record,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)

KNOWN_LINE_REPORTS = [
    ("batch1", REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"),
    ("batch2", REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json"),
]
TOP_ORBIT = (0, 0, -2, 1, -1, 1, -1)
TOP_ORBIT_DUAL = tuple(-value for value in TOP_ORBIT)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep(sign: int) -> dict[str, Any]:
    if sign == 1:
        return representation_record(1, 1)
    if sign == -1:
        return representation_record(1, -1)
    raise ValueError(sign)


def serre_orbit(line: list[int]) -> tuple[int, ...]:
    tup = tuple(line)
    dual = tuple(-value for value in tup)
    return min(tup, dual)


def branch_actual_for_line(line: list[int], cohomology: list[int], sign: int) -> dict[str, Any]:
    if tuple(line) == TOP_ORBIT:
        expected = [0, 0, 1, 0]
        key = "H2"
    elif tuple(line) == TOP_ORBIT_DUAL:
        expected = [0, 1, 0, 0]
        key = "H1"
    else:
        raise ValueError(line)
    if cohomology != expected:
        raise ValueError((line, cohomology, expected))
    return {key: rep(sign)}


def apply_top_orbit_branch(
    characters: dict[str, Any],
    *,
    sign: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    still_unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            if serre_orbit(cert["line_bundle"]) != TOP_ORBIT:
                still_unresolved.append(
                    {
                        "sector": sector_key,
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "outside_top_serre_orbit_branch",
                    }
                )
                continue
            actual = branch_actual_for_line(cert["line_bundle"], cert["cohomology"], sign)
            cert["actual"] = actual
            cert["method"] = f"top_serre_orbit_bounded_branch_sign_{sign:+d}"
            cert["actual_character_computed"] = True
            filled.append(
                {
                    "sector": sector_key,
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "actual": actual,
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
        "branch_sign": sign,
        "filled_blocks": filled,
        "filled_block_count": len(filled),
        "remaining_unresolved_blocks": still_unresolved,
        "remaining_unresolved_block_count": len(still_unresolved),
    }


def candidate_contains_top_orbit(record: dict[str, Any]) -> bool:
    return any(
        serre_orbit(block["line_bundle"]) == TOP_ORBIT
        for block in record["radius4_known_line_resolution"]["unresolved_blocks"]
    )


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    demand = load_json(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    source_reports = [(batch, path, load_json(path)) for batch, path in KNOWN_LINE_REPORTS]

    candidate_items = []
    for batch, path, report in source_reports:
        for resolved, filtered in zip(
            report["resolved_records"], report["filtered_candidate_records"]
        ):
            if not candidate_contains_top_orbit(filtered):
                continue
            candidate_items.append(
                {
                    "batch": batch,
                    "source_report": str(path),
                    "resolved": resolved,
                    "filtered": filtered,
                }
            )

    branch_records = []
    for item in candidate_items:
        for sign in [1, -1]:
            certified = copy.deepcopy(item["resolved"])
            characters, resolution = apply_top_orbit_branch(
                certified["characters"], sign=sign
            )
            certified["characters"] = characters
            certified["top_serre_orbit_branch_resolution"] = resolution
            certified["character_certified"] = all(
                sector["all_characters_computed"] for sector in characters.values()
            )
            certified["vectorlike_pair_prediction"] = prediction_from_characters(characters)
            certified["source_batch"] = item["batch"]

            filtered = candidate_certificate_from_5259_record(
                label=(
                    f"{item['batch']}_{item['filtered']['label']}"
                    f"_top_orbit_{'plus' if sign == 1 else 'minus'}"
                ),
                record=certified,
                conf=conf,
            )
            filtered["source_batch"] = item["batch"]
            filtered["source_window"] = item["filtered"]["source_window"]
            filtered["source_filtered_label"] = item["filtered"]["source_filtered_label"]
            filtered["top_serre_orbit_branch_resolution"] = resolution
            if not certified["character_certified"]:
                filtered["classification"] = {
                    "category": "unresolved",
                    "status": "top_serre_orbit_branch_still_character_incomplete",
                    "reason": (
                        "the top Serre orbit branch was filled, but other missing "
                        "line-character blocks remain"
                    ),
                }
            else:
                apply_monoid_obstruction_override(filtered)
            branch_records.append(filtered)

    categories = Counter(record["classification"]["category"] for record in branch_records)
    statuses = Counter(record["classification"]["status"] for record in branch_records)
    viable = [
        record for record in branch_records if record["classification"]["category"] == "viable"
    ]
    character_certified = [
        record
        for record in branch_records
        if record["character_certificate"]["character_certified"]
    ]
    top_demand = demand["top_missing_serre_orbits"][0]
    gates = {
        "source_reports_pass": gate(
            all(report["all_gates_pass"] for _batch, _path, report in source_reports),
            ", ".join(str(path) for _batch, path, _report in source_reports),
            "branch closure imports only passing known-line reports",
        ),
        "top_orbit_matches_demand_report": gate(
            top_demand["serre_orbit_representative"] == list(TOP_ORBIT)
            and top_demand["candidate_count"] == 5
            and top_demand["block_count"] == 10,
            str(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json"),
            "branch closure targets the highest-demand missing Serre orbit",
        ),
        "all_top_orbit_candidates_branched": gate(
            len(candidate_items) == 5 and len(branch_records) == 10,
            "top Serre orbit candidate records",
            "both one-dimensional Z2 character branches are tested for each top-orbit candidate",
        ),
        "branch_fills_expected_blocks": gate(
            sum(
                record["top_serre_orbit_branch_resolution"]["filled_block_count"]
                for record in branch_records
            )
            == 20,
            "top Serre orbit branch records",
            "each sign branch fills the line and Serre-dual block for each candidate",
        ),
        "branch_classifications_complete": gate(
            dict(sorted(categories.items()))
            == {"phenomenologically obstructed": 8, "unresolved": 2}
            and dict(sorted(statuses.items()))
            == {
                "negative_control_doublet_triplet_obstruction": 4,
                "rejected_spectrum_signature_not_q1_three_family": 4,
                "top_serre_orbit_branch_still_character_incomplete": 2,
            },
            "top Serre orbit branch classifications",
            "top-orbit branches either remain character-incomplete or are classified by the phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            len(viable) == 0,
            "top Serre orbit branch classifications",
            "neither Z2 sign branch produces a viable candidate",
        ),
    }
    return {
        "scope": "bounded branch closure for the highest-demand missing radius-4 Serre orbit",
        "status": "no_viable_candidate_found_in_top_serre_orbit_branches"
        if not viable
        else "viable_candidate_found_in_top_serre_orbit_branches",
        "top_serre_orbit": {
            "representative": list(TOP_ORBIT),
            "dual": list(TOP_ORBIT_DUAL),
            "branch_actuals": {
                "plus": {
                    str(list(TOP_ORBIT)): {"H2": rep(1)},
                    str(list(TOP_ORBIT_DUAL)): {"H1": rep(1)},
                },
                "minus": {
                    str(list(TOP_ORBIT)): {"H2": rep(-1)},
                    str(list(TOP_ORBIT_DUAL)): {"H1": rep(-1)},
                },
            },
        },
        "summary": {
            "candidate_count": len(candidate_items),
            "branch_count": len(branch_records),
            "filled_blocks": sum(
                record["top_serre_orbit_branch_resolution"]["filled_block_count"]
                for record in branch_records
            ),
            "remaining_unresolved_blocks": sum(
                record["top_serre_orbit_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                for record in branch_records
            ),
            "character_certified_branches": len(character_certified),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "branch_records": branch_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Top Serre Orbit Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- orbit representative: `{report['top_serre_orbit']['representative']}`",
        f"- dual: `{report['top_serre_orbit']['dual']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        lines.append(
            "- "
            f"`{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"filled `{record['top_serre_orbit_branch_resolution']['filled_block_count']}`; "
            f"remaining "
            f"`{record['top_serre_orbit_branch_resolution']['remaining_unresolved_block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The highest-demand missing Serre orbit has only two possible "
                "one-dimensional Z2 character assignments. Branching both signs "
                "does not produce a viable candidate; the fully unlocked branches "
                "are rejected by the same charge-level filters used against the "
                "5259/7914 negative control."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.md"
        ),
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
