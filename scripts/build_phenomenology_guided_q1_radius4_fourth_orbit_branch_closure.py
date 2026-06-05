#!/usr/bin/env python3
"""Branch-close the cumulative2 next dimension-3 Serre orbit."""

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

SOURCE_REPORTS = {
    "batch1": REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json",
    "batch2": REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json",
}
FOURTH_ORBIT = (-1, 2, -2, 1, 1, 0, -1)
FOURTH_ORBIT_DUAL = tuple(-value for value in FOURTH_ORBIT)
TARGET_CANDIDATES = [
    "batch2:window5_radius4_adjacency_filtered_6_known_line_resolved",
    "batch2:window6_radius4_adjacency_filtered_0_known_line_resolved",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep(trace: int) -> dict[str, Any]:
    return representation_record(3, trace)


def serre_orbit(line: list[int]) -> tuple[int, ...]:
    tup = tuple(line)
    dual = tuple(-value for value in tup)
    return min(tup, dual)


def actual_for_line(line: list[int], cohomology: list[int], trace: int) -> dict[str, Any]:
    tup = tuple(line)
    if tup == FOURTH_ORBIT:
        if cohomology != [0, 0, 3, 0]:
            raise ValueError((line, cohomology))
        return {"H2": rep(trace)}
    if tup == FOURTH_ORBIT_DUAL:
        if cohomology != [0, 3, 0, 0]:
            raise ValueError((line, cohomology))
        return {"H1": rep(trace)}
    raise ValueError(line)


def apply_branch(characters: dict[str, Any], *, trace: int) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    still_unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            if serre_orbit(cert["line_bundle"]) != FOURTH_ORBIT:
                still_unresolved.append(
                    {
                        "sector": sector_key,
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "outside_fourth_serre_orbit_branch",
                    }
                )
                continue
            actual = actual_for_line(cert["line_bundle"], cert["cohomology"], trace)
            cert["actual"] = actual
            cert["method"] = f"fourth_serre_orbit_bounded_branch_trace_{trace:+d}"
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
        "trace": trace,
        "filled_blocks": filled,
        "filled_block_count": len(filled),
        "remaining_unresolved_blocks": still_unresolved,
        "remaining_unresolved_block_count": len(still_unresolved),
    }


def load_target_records() -> list[dict[str, Any]]:
    targets = []
    for batch, path in SOURCE_REPORTS.items():
        report = load_json(path)
        for resolved, filtered in zip(report["resolved_records"], report["filtered_candidate_records"]):
            cid = f"{batch}:{filtered['label']}"
            if cid in TARGET_CANDIDATES:
                targets.append(
                    {
                        "candidate": cid,
                        "batch": batch,
                        "source_report": str(path),
                        "resolved": resolved,
                        "filtered": filtered,
                    }
                )
    return sorted(targets, key=lambda item: item["candidate"])


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    cumulative2 = load_json(REPORTS / "phenomenology_guided_q1_radius4_cumulative2_adjusted_frontier.json")
    cumulative2_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative2_adjusted_frontier_verification.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]
    targets = load_target_records()
    branch_records = []
    for item in targets:
        for trace in [3, 1, -1, -3]:
            certified = copy.deepcopy(item["resolved"])
            characters, resolution = apply_branch(certified["characters"], trace=trace)
            certified["characters"] = characters
            certified["fourth_serre_orbit_branch_resolution"] = resolution
            certified["character_certified"] = all(
                sector["all_characters_computed"] for sector in characters.values()
            )
            certified["vectorlike_pair_prediction"] = prediction_from_characters(characters)
            filtered = candidate_certificate_from_5259_record(
                label=f"{item['batch']}_{item['filtered']['label']}_fourth_trace_{trace:+d}",
                record=certified,
                conf=conf,
            )
            filtered["source_batch"] = item["batch"]
            filtered["source_window"] = item["filtered"]["source_window"]
            filtered["source_filtered_label"] = item["filtered"]["source_filtered_label"]
            filtered["fourth_serre_orbit_branch_resolution"] = resolution
            if not certified["character_certified"]:
                filtered["classification"] = {
                    "category": "unresolved",
                    "status": "fourth_serre_orbit_branch_still_character_incomplete",
                    "reason": (
                        "the cumulative2 next Serre orbit branch was filled, but "
                        "other missing line-character blocks remain"
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
    next_orbit = cumulative2["summary"]["next_probe_orbit"]
    gates = {
        "cumulative2_frontier_verified": gate(
            cumulative2["all_gates_pass"]
            and cumulative2_verification["all_gates_pass"]
            and next_orbit["serre_orbit_representative"] == list(FOURTH_ORBIT),
            str(REPORTS / "phenomenology_guided_q1_radius4_cumulative2_adjusted_frontier.json"),
            "fourth-orbit branch closure targets the verified cumulative2 bottleneck",
        ),
        "target_candidates_loaded": gate(
            [item["candidate"] for item in targets] == TARGET_CANDIDATES,
            ", ".join(str(path) for path in SOURCE_REPORTS.values()),
            "both candidates touched by the cumulative2 next orbit are loaded",
        ),
        "all_trace_branches_tested": gate(
            len(branch_records) == 8
            and sum(
                record["fourth_serre_orbit_branch_resolution"]["filled_block_count"]
                for record in branch_records
            )
            == 16,
            "fourth Serre orbit branch records",
            "two candidates times four trace branches are tested",
        ),
        "classification_counts_match": gate(
            dict(sorted(categories.items()))
            == {"phenomenologically obstructed": 8}
            and dict(sorted(statuses.items()))
            == {
                "negative_control_doublet_triplet_obstruction": 2,
                "rejected_spectrum_signature_not_q1_three_family": 6,
            },
            "fourth Serre orbit branch classifications",
            "all fourth-orbit branches are rejected by the q=1/phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            len(viable) == 0,
            "fourth Serre orbit branch classifications",
            "no branch of the cumulative2 next orbit produces a viable candidate",
        ),
    }
    return {
        "scope": "bounded branch closure for the cumulative2 next radius-4 Serre orbit",
        "status": "no_viable_candidate_found_in_fourth_serre_orbit_branches"
        if not viable
        else "viable_candidate_found_in_fourth_serre_orbit_branches",
        "fourth_serre_orbit": {
            "representative": list(FOURTH_ORBIT),
            "dual": list(FOURTH_ORBIT_DUAL),
            "target_candidates": TARGET_CANDIDATES,
        },
        "summary": {
            "candidate_count": len(targets),
            "branch_count": len(branch_records),
            "filled_blocks": sum(
                record["fourth_serre_orbit_branch_resolution"]["filled_block_count"]
                for record in branch_records
            ),
            "remaining_unresolved_blocks": sum(
                record["fourth_serre_orbit_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                for record in branch_records
            ),
            "character_certified_branches": sum(
                1
                for record in branch_records
                if record["character_certificate"]["character_certified"]
            ),
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
        "# Radius-4 Fourth Serre Orbit Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- orbit representative: `{report['fourth_serre_orbit']['representative']}`",
        f"- dual: `{report['fourth_serre_orbit']['dual']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        res = record["fourth_serre_orbit_branch_resolution"]
        lines.append(
            "- "
            f"`{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"filled `{res['filled_block_count']}`; "
            f"remaining `{res['remaining_unresolved_block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The cumulative2 bottleneck has four one-degree dimension-three "
                "trace branches per candidate. Every branch is character-certified "
                "and nonviable: most lose the q=1 signature, and the q=1 survivors "
                "reproduce the negative-control doublet-triplet obstruction."
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
            REPORTS / "phenomenology_guided_q1_radius4_fourth_orbit_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_fourth_orbit_branch_closure.md"
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
