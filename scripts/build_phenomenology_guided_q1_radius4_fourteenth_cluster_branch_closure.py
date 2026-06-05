#!/usr/bin/env python3
"""Fully branch-close the cumulative12 two-orbit candidate cluster."""

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
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)

SOURCE_REPORT = REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"
TARGET_CANDIDATE = "batch1:window3_radius4_adjacency_filtered_3_known_line_resolved"
CLUSTER_ORBITS = (
    (-1, 1, 0, -1, 1, 0, -1),
    (0, 0, -1, 0, 2, 0, -1),
)
TRACE_VALUES = (2, 0, -2)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep(trace: int) -> dict[str, Any]:
    return representation_record(2, trace)


def serre_orbit(line: list[int]) -> tuple[int, ...]:
    tup = tuple(line)
    dual = tuple(-value for value in tup)
    return min(tup, dual)


def actual_for_cohomology(cohomology: list[int], trace: int) -> dict[str, Any]:
    if cohomology == [0, 2, 0, 0]:
        return {"H1": rep(trace)}
    if cohomology == [0, 0, 2, 0]:
        return {"H2": rep(trace)}
    raise ValueError(cohomology)


def apply_branch(
    characters: dict[str, Any],
    *,
    traces_by_orbit: dict[tuple[int, ...], int],
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    still_unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            orbit = serre_orbit(cert["line_bundle"])
            if orbit not in traces_by_orbit:
                still_unresolved.append(
                    {
                        "sector": sector_key,
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "outside_fourteenth_cluster_branch_orbits",
                    }
                )
                continue
            actual = actual_for_cohomology(cert["cohomology"], traces_by_orbit[orbit])
            cert["actual"] = actual
            trace_label = "_".join(
                f"o{index}_{traces_by_orbit[orbit]:+d}"
                for index, orbit in enumerate(CLUSTER_ORBITS)
            )
            cert["method"] = f"fourteenth_cluster_bounded_branch_{trace_label}"
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
        "traces_by_orbit": {
            json.dumps(list(orbit), separators=(",", ":")): trace
            for orbit, trace in traces_by_orbit.items()
        },
        "filled_blocks": filled,
        "filled_block_count": len(filled),
        "remaining_unresolved_blocks": still_unresolved,
        "remaining_unresolved_block_count": len(still_unresolved),
    }


def load_target_record() -> dict[str, Any]:
    report = load_json(SOURCE_REPORT)
    for resolved, filtered in zip(report["resolved_records"], report["filtered_candidate_records"]):
        if f"batch1:{filtered['label']}" == TARGET_CANDIDATE:
            return {"resolved": resolved, "filtered": filtered}
    raise RuntimeError(f"target candidate not found: {TARGET_CANDIDATE}")


def branch_label(trace_tuple: tuple[int, ...]) -> str:
    return "_".join(f"o{index}_{trace:+d}" for index, trace in enumerate(trace_tuple))


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    cumulative12 = load_json(REPORTS / "phenomenology_guided_q1_radius4_cumulative12_adjusted_frontier.json")
    cumulative12_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative12_adjusted_frontier_verification.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]
    target = load_target_record()
    branch_records = []
    for trace_tuple in itertools.product(TRACE_VALUES, repeat=len(CLUSTER_ORBITS)):
        traces_by_orbit = dict(zip(CLUSTER_ORBITS, trace_tuple))
        certified = copy.deepcopy(target["resolved"])
        characters, resolution = apply_branch(
            certified["characters"],
            traces_by_orbit=traces_by_orbit,
        )
        certified["characters"] = characters
        certified["fourteenth_cluster_branch_resolution"] = resolution
        certified["character_certified"] = all(
            sector["all_characters_computed"] for sector in characters.values()
        )
        certified["vectorlike_pair_prediction"] = prediction_from_characters(characters)
        filtered = candidate_certificate_from_5259_record(
            label=f"batch1_{target['filtered']['label']}_fourteenth_cluster_{branch_label(trace_tuple)}",
            record=certified,
            conf=conf,
        )
        filtered["source_batch"] = "batch1"
        filtered["source_window"] = target["filtered"]["source_window"]
        filtered["source_filtered_label"] = target["filtered"]["source_filtered_label"]
        filtered["fourteenth_cluster_branch_resolution"] = resolution
        if not certified["character_certified"]:
            filtered["classification"] = {
                "category": "unresolved",
                "status": "fourteenth_cluster_branch_still_character_incomplete",
                "reason": (
                    "the two-orbit cluster branch was filled, but other "
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
    next_orbit = cumulative12["summary"]["next_probe_orbit"]
    gates = {
        "cumulative12_frontier_verified": gate(
            cumulative12["all_gates_pass"]
            and cumulative12_verification["all_gates_pass"]
            and next_orbit["serre_orbit_representative"] == list(CLUSTER_ORBITS[0]),
            str(REPORTS / "phenomenology_guided_q1_radius4_cumulative12_adjusted_frontier.json"),
            "cluster closure starts from the verified cumulative12 bottleneck",
        ),
        "target_candidate_loaded": gate(
            f"batch1:{target['filtered']['label']}" == TARGET_CANDIDATE,
            str(SOURCE_REPORT),
            "the two-orbit candidate touched by the cumulative12 next orbit is loaded",
        ),
        "all_trace_branches_tested": gate(
            len(branch_records) == 9
            and sum(
                record["fourteenth_cluster_branch_resolution"]["filled_block_count"]
                for record in branch_records
            )
            == 36
            and all(
                record["fourteenth_cluster_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 0
                for record in branch_records
            )
            and sum(
                1
                for record in branch_records
                if record["character_certificate"]["character_certified"]
            )
            == 9,
            "fourteenth two-orbit cluster branch records",
            "three traces for each of two dimension-two Serre orbits fully certify the candidate",
        ),
        "classification_counts_match": gate(
            dict(sorted(categories.items())) == {"phenomenologically obstructed": 9}
            and dict(sorted(statuses.items()))
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 3,
                "rejected_spectrum_signature_not_q1_three_family": 6,
            },
            "fourteenth two-orbit cluster branch classifications",
            "all cluster branches are rejected by the q=1/phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            len(viable) == 0,
            "fourteenth two-orbit cluster branch classifications",
            "no completion of the two-orbit candidate is viable",
        ),
    }
    return {
        "scope": "bounded branch closure for the cumulative12 two-orbit radius-4 cluster",
        "status": "no_viable_candidate_found_in_fourteenth_cluster_branches"
        if not viable
        else "viable_candidate_found_in_fourteenth_cluster_branches",
        "target_candidate": TARGET_CANDIDATE,
        "cluster_serre_orbits": [
            {"representative": list(orbit), "dual": [-value for value in orbit]}
            for orbit in CLUSTER_ORBITS
        ],
        "summary": {
            "candidate_count": 1,
            "branch_count": len(branch_records),
            "filled_blocks": sum(
                record["fourteenth_cluster_branch_resolution"]["filled_block_count"]
                for record in branch_records
            ),
            "remaining_unresolved_blocks": sum(
                record["fourteenth_cluster_branch_resolution"][
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
        "# Radius-4 Fourteenth Two-Orbit Cluster Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- target candidate: `{report['target_candidate']}`",
        "",
        "## Cluster Orbits",
        "",
    ]
    for orbit in report["cluster_serre_orbits"]:
        lines.append(f"- `{orbit['representative']}` / `{orbit['dual']}`")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        res = record["fourteenth_cluster_branch_resolution"]
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
                "The cumulative12 two-orbit candidate has nine compatible "
                "dimension-two trace completions. This report fills both Serre "
                "orbits: six branches lose the q=1 signature and three allow a "
                "dangerous 10*5bar*5bar operator."
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
            REPORTS
            / "phenomenology_guided_q1_radius4_fourteenth_cluster_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_fourteenth_cluster_branch_closure.md"
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
